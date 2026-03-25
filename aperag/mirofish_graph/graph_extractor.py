from __future__ import annotations

import logging
from typing import Any

from aperag.config import settings

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
            attributes = entity.get("attributes") if isinstance(entity.get("attributes"), dict) else {}
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
                    "attributes": relation.get("attributes") if isinstance(relation.get("attributes"), dict) else {},
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
