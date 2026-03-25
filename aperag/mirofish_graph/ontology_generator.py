from __future__ import annotations

from typing import Any

from .llm_client import MiroFishLLMClient
from .ontology_display import normalize_ontology


ONTOLOGY_SYSTEM_PROMPT = """You design a compact ontology for knowledge graph extraction.

Rules:
- Return valid JSON only.
- Produce 6 to 10 entity types and 4 to 10 relation types.
- Keep type names in English identifiers.
- Prefer concrete real-world actors and organizations over abstract concepts.
- Include `Person` and `Organization` as fallbacks when they are missing.
- Keep descriptions short and practical.
"""


class OntologyGenerator:
    MAX_TEXT_LENGTH_FOR_LLM = 50000

    def __init__(self, llm_client: MiroFishLLMClient) -> None:
        self.llm_client = llm_client

    def generate(
        self,
        *,
        document_texts: list[str],
        simulation_requirement: str,
        additional_context: str | None = None,
    ) -> dict[str, Any]:
        user_message = self._build_user_message(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context,
        )
        result = self.llm_client.chat_json(
            messages=[
                {"role": "system", "content": ONTOLOGY_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        return self._validate_and_process(result)

    def _build_user_message(
        self,
        *,
        document_texts: list[str],
        simulation_requirement: str,
        additional_context: str | None,
    ) -> str:
        combined_text = "\n\n---\n\n".join(text.strip() for text in document_texts if text.strip())
        if len(combined_text) > self.MAX_TEXT_LENGTH_FOR_LLM:
            combined_text = combined_text[: self.MAX_TEXT_LENGTH_FOR_LLM]

        message = f"""Knowledge-base intent:
{simulation_requirement}

Document content:
{combined_text}

Return JSON in this shape:
{{
  "entity_types": [
    {{
      "name": "Person",
      "display_name": "Person",
      "description": "short description",
      "attributes": [{{"name": "role", "type": "text", "description": "short description"}}],
      "examples": ["example"]
    }}
  ],
  "edge_types": [
    {{
      "name": "RELATED_TO",
      "display_name": "Related To",
      "description": "short description",
      "source_targets": [{{"source": "Person", "target": "Organization"}}],
      "attributes": []
    }}
  ],
  "analysis_summary": "short summary"
}}
"""

        if additional_context:
            message += f"\nAdditional context:\n{additional_context}\n"

        message += "\nKeep entity and relation names stable and reuse the same type names consistently.\n"
        return message

    def _validate_and_process(self, result: dict[str, Any]) -> dict[str, Any]:
        result.setdefault("entity_types", [])
        result.setdefault("edge_types", [])
        result.setdefault("analysis_summary", "")

        for entity in result["entity_types"]:
            entity.setdefault("attributes", [])
            entity.setdefault("examples", [])
            entity["description"] = str(entity.get("description", "") or "")[:100]

        for edge in result["edge_types"]:
            edge.setdefault("source_targets", [])
            edge.setdefault("attributes", [])
            edge["description"] = str(edge.get("description", "") or "")[:100]

        entity_names = {item.get("name") for item in result["entity_types"] if item.get("name")}
        if "Person" not in entity_names:
            result["entity_types"].append(
                {
                    "name": "Person",
                    "display_name": "Person",
                    "description": "Fallback type for individual people.",
                    "attributes": [{"name": "role", "type": "text", "description": "Primary role"}],
                    "examples": ["Expert", "Citizen"],
                }
            )
        if "Organization" not in entity_names:
            result["entity_types"].append(
                {
                    "name": "Organization",
                    "display_name": "Organization",
                    "description": "Fallback type for groups and institutions.",
                    "attributes": [{"name": "org_type", "type": "text", "description": "Organization type"}],
                    "examples": ["Company", "Agency"],
                }
            )

        result["entity_types"] = result["entity_types"][:10]
        result["edge_types"] = result["edge_types"][:10]
        return normalize_ontology(result) or result
