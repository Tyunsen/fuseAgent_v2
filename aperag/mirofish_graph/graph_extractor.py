from __future__ import annotations

import logging
from typing import Any

from aperag.config import settings

from .helpers import sanitize_graph_attributes
from .llm_client import MiroFishLLMClient

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You extract a compact knowledge graph from a text chunk.

Rules:
- Return valid JSON only.
- Use only entity types from the provided ontology.
- Use only relation types from the provided ontology.
- Keep entity names in the source-language form used by the chunk when possible.
- Keep evidence short and grounded in the source text.
- Do not invent unsupported facts.
- Favor recall over excessive summarization: when the chunk supports multiple distinct entities or relations, extract all materially distinct ones that are evidenced in the chunk.
- Preserve concrete actors, places, activities, statements, and their supported links whenever they add graph coverage.
- Preserve time/place attributes only when the chunk explicitly supports them.
- For trace attributes, only use: time, time_start, time_end, time_label, place, place_normalized, place_aliases.
- If the chunk has no useful entities or relations, return empty arrays.
"""


class ChunkGraphExtractor:
    def __init__(self, llm_client: MiroFishLLMClient) -> None:
        self.llm_client = llm_client

    def extract(
        self,
        *,
        chunk_text: str,
        ontology: dict[str, Any],
        document_name: str,
        chunk_index: int,
    ) -> dict[str, list[dict[str, Any]]]:
        entity_types = ontology.get("entity_types", [])
        edge_types = ontology.get("edge_types", [])

        entity_guide = [
            {
                "name": entity.get("name"),
                "description": entity.get("description", ""),
                "attributes": [attr.get("name") for attr in entity.get("attributes", [])],
            }
            for entity in entity_types
        ]
        relation_guide = [
            {
                "name": edge.get("name"),
                "description": edge.get("description", ""),
                "source_targets": edge.get("source_targets", []),
            }
            for edge in edge_types
        ]

        prompt = f"""
Document: {document_name}
Chunk index: {chunk_index}

Ontology entity types:
{entity_guide}

Ontology relation types:
{relation_guide}

Return this JSON structure:
{{
  "entities": [
    {{
      "name": "entity name",
      "aliases": ["alias"],
      "type": "ontology entity type",
      "summary": "short summary",
      "attributes": {{"attribute_name": "value"}}
    }}
  ],
  "relations": [
    {{
      "source_name": "source entity name",
      "source_type": "ontology entity type",
      "target_name": "target entity name",
      "target_type": "ontology entity type",
      "type": "ontology relation type",
      "fact": "fact sentence",
      "evidence": "short quote",
      "confidence": 0.0,
      "attributes": {{}}
    }}
  ]
}}

Trace attribute guidance:
- If the chunk explicitly states when an entity exists, acts, appears, or is relevant, put that evidence-backed value into entity.attributes using the trace keys above.
- If the chunk explicitly states where an entity exists, acts, appears, or is relevant, put that evidence-backed value into entity.attributes using the trace keys above.
- If the chunk explicitly states when or where a relation/fact holds, put that evidence-backed value into relation.attributes using the trace keys above.
- Never infer missing time/place values from background knowledge.
- Prefer more supported graph facts to fewer summarized facts. If one chunk contains several supported relations, extract each distinct relation instead of collapsing them into one broad statement.

Text chunk:
\"\"\"
{chunk_text}
\"\"\"
"""

        last_error: Exception | None = None
        for attempt in range(settings.mirofish_graph_extraction_max_retries):
            try:
                response = self.llm_client.chat_json(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=max(0.1, 0.2 + attempt * 0.1),
                    max_tokens=settings.mirofish_graph_extraction_max_tokens,
                )
                return self._sanitize_response(response, ontology)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Chunk extraction failed for %s[%s] attempt %s: %s",
                    document_name,
                    chunk_index,
                    attempt + 1,
                    exc,
                )

        logger.warning(
            "Falling back to empty extraction for %s[%s]: %s",
            document_name,
            chunk_index,
            last_error,
        )
        return {"entities": [], "relations": []}

    def _sanitize_response(self, response: dict[str, Any], ontology: dict[str, Any]) -> dict[str, Any]:
        allowed_entity_types = {item.get("name") for item in ontology.get("entity_types", []) if item.get("name")}
        allowed_relation_types = {item.get("name") for item in ontology.get("edge_types", []) if item.get("name")}

        entities: list[dict[str, Any]] = []
        for entity in response.get("entities", []) or []:
            entity_type = entity.get("type")
            name = str(entity.get("name", "") or "").strip()
            if not name or entity_type not in allowed_entity_types:
                continue
            attributes = sanitize_graph_attributes(entity.get("attributes"))
            aliases = self._sanitize_aliases(entity.get("aliases"))
            entities.append(
                {
                    "name": name,
                    "aliases": aliases,
                    "type": entity_type,
                    "summary": str(entity.get("summary", "") or "").strip(),
                    "attributes": attributes,
                }
            )

        relations: list[dict[str, Any]] = []
        for relation in response.get("relations", []) or []:
            relation_type = relation.get("type")
            if relation_type not in allowed_relation_types:
                continue
            source_name = str(relation.get("source_name", "") or "").strip()
            target_name = str(relation.get("target_name", "") or "").strip()
            source_type = relation.get("source_type")
            target_type = relation.get("target_type")
            if not source_name or not target_name:
                continue
            if source_type not in allowed_entity_types or target_type not in allowed_entity_types:
                continue
            confidence = relation.get("confidence", 0.5)
            if not isinstance(confidence, (int, float)):
                confidence = 0.5
            relations.append(
                {
                    "source_name": source_name,
                    "source_type": source_type,
                    "target_name": target_name,
                    "target_type": target_type,
                    "type": relation_type,
                    "fact": str(relation.get("fact", "") or "").strip(),
                    "evidence": str(relation.get("evidence", "") or "").strip(),
                    "confidence": max(0.0, min(float(confidence), 1.0)),
                    "attributes": sanitize_graph_attributes(relation.get("attributes")),
                }
            )

        return {"entities": entities, "relations": relations}

    @staticmethod
    def _sanitize_aliases(raw_aliases: Any) -> list[str]:
        if isinstance(raw_aliases, str):
            candidates = [raw_aliases]
        elif isinstance(raw_aliases, (list, tuple, set)):
            candidates = list(raw_aliases)
        else:
            candidates = []

        aliases: list[str] = []
        seen: set[str] = set()
        for value in candidates:
            alias = "" if value is None else str(value).strip()
            if not alias:
                continue
            normalized = alias.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            aliases.append(alias)
        return aliases
