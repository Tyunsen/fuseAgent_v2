from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from .constants import (
    BASE_EDGE_TYPES,
    BASE_ENTITY_TYPES,
    MIROFISH_ONTOLOGY_EDGE_CAP,
    MIROFISH_ONTOLOGY_ENTITY_CAP,
)
from .llm_client import MiroFishLLMClient
from .ontology_display import normalize_ontology


ONTOLOGY_SYSTEM_PROMPT = """You design a compact but broad ontology for knowledge graph extraction.

Rules:
- Return valid JSON only.
- Keep the provided base types stable. You may add supplemental types when they materially improve recall.
- Return supplemental types only; the system will merge them with the fixed base catalog.
- Supplemental output should stay compact. Prefer at most 4 to 8 extra entity types and 4 to 8 extra relation types.
- Final merged ontology may contain up to 16 entity types and up to 16 relation types in total.
- Keep entity type names as English identifiers in PascalCase.
- Keep relation type names as English identifiers in UPPER_SNAKE_CASE.
- Prefer broad reusable categories over narrow one-off labels.
- Avoid synonyms, near-duplicates, and types that are too specific to a single document.
- Make sure the ontology can preserve evidence-backed time/place attributes when the source explicitly states them.
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
            temperature=0.2,
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
{simulation_requirement or "No explicit intent provided."}

Fixed base entity types (must remain in the final ontology):
{json.dumps(self._catalog_outline(BASE_ENTITY_TYPES, relation=False), ensure_ascii=False, indent=2)}

Fixed base relation types (must remain in the final ontology):
{json.dumps(self._catalog_outline(BASE_EDGE_TYPES, relation=True), ensure_ascii=False, indent=2)}

Document content sample:
{combined_text}

Instructions:
- Return only the supplemental types you want to add on top of the fixed base catalog.
- Keep supplemental types lightweight and broad. Add only the missing types needed to improve coverage for this knowledge base.
- Do not exceed {MIROFISH_ONTOLOGY_ENTITY_CAP} total entity types or {MIROFISH_ONTOLOGY_EDGE_CAP} total relation types.
- When helpful, include trace-oriented attribute names such as time, time_start, time_end, time_label, place, place_normalized, place_aliases.

Return JSON in this shape:
{{
  "supplemental_entity_types": [
    {{
      "name": "MilitaryUnit",
      "display_name": "Military Unit",
      "description": "short description",
      "attributes": [{{"name": "role", "type": "text", "description": "short description"}}],
      "examples": ["example"]
    }}
  ],
  "supplemental_edge_types": [
    {{
      "name": "COORDINATES_WITH",
      "display_name": "Coordinates With",
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

        message += "\nKeep type names stable and reuse the same canonical labels consistently.\n"
        return message

    def _validate_and_process(self, result: dict[str, Any]) -> dict[str, Any]:
        result = result or {}
        entity_types = self._merge_catalogs(
            BASE_ENTITY_TYPES,
            result.get("supplemental_entity_types", result.get("entity_types", [])) or [],
            relation=False,
            cap=MIROFISH_ONTOLOGY_ENTITY_CAP,
        )
        edge_types = self._merge_catalogs(
            BASE_EDGE_TYPES,
            result.get("supplemental_edge_types", result.get("edge_types", [])) or [],
            relation=True,
            cap=MIROFISH_ONTOLOGY_EDGE_CAP,
        )
        normalized = normalize_ontology(
            {
                "entity_types": entity_types,
                "edge_types": edge_types,
                "analysis_summary": str(result.get("analysis_summary", "") or "").strip()[:240],
            }
        )
        return normalized or {
            "entity_types": entity_types,
            "edge_types": edge_types,
            "analysis_summary": str(result.get("analysis_summary", "") or "").strip()[:240],
        }

    def _merge_catalogs(
        self,
        base_items: list[dict[str, Any]],
        generated_items: list[Any],
        *,
        relation: bool,
        cap: int,
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = [deepcopy(item) for item in base_items]
        index_by_name = {
            str(item["name"]).casefold(): position for position, item in enumerate(merged)
        }

        for raw_item in generated_items:
            normalized_item = self._normalize_catalog_item(raw_item, relation=relation)
            if not normalized_item:
                continue

            normalized_name = normalized_item["name"].casefold()
            if normalized_name in index_by_name:
                existing = merged[index_by_name[normalized_name]]
                if not existing.get("description") and normalized_item.get("description"):
                    existing["description"] = normalized_item["description"]
                if relation:
                    existing["source_targets"] = self._merge_list_of_dicts(
                        existing.get("source_targets", []),
                        normalized_item.get("source_targets", []),
                    )
                else:
                    existing["examples"] = self._merge_string_lists(
                        existing.get("examples", []),
                        normalized_item.get("examples", []),
                    )
                existing["attributes"] = self._merge_list_of_dicts(
                    existing.get("attributes", []),
                    normalized_item.get("attributes", []),
                )
                continue

            merged.append(normalized_item)
            index_by_name[normalized_name] = len(merged) - 1
            if len(merged) >= cap:
                break

        return merged[:cap]

    def _normalize_catalog_item(self, item: Any, *, relation: bool) -> dict[str, Any] | None:
        if not isinstance(item, dict):
            return None

        raw_name = str(item.get("name", "") or "").strip()
        name = self._normalize_type_name(raw_name, relation=relation)
        if not name:
            return None

        normalized = {
            "name": name,
            "display_name": str(item.get("display_name") or self._to_display_name(name, relation=relation)).strip()
            or self._to_display_name(name, relation=relation),
            "description": str(item.get("description", "") or "").strip()[:120],
            "attributes": self._normalize_attributes(item.get("attributes")),
        }
        if relation:
            normalized["source_targets"] = self._normalize_source_targets(item.get("source_targets"))
        else:
            normalized["examples"] = self._merge_string_lists([], item.get("examples", []))
        return normalized

    @staticmethod
    def _catalog_outline(items: list[dict[str, Any]], *, relation: bool) -> list[dict[str, Any]]:
        if relation:
            return [
                {
                    "name": item["name"],
                    "description": item.get("description", ""),
                }
                for item in items
            ]
        return [
            {
                "name": item["name"],
                "description": item.get("description", ""),
                "example_attributes": [attr.get("name") for attr in item.get("attributes", [])[:4]],
            }
            for item in items
        ]

    @staticmethod
    def _normalize_type_name(name: str, *, relation: bool) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_ -]+", " ", name or "").strip()
        if not cleaned:
            return ""
        parts = [part for part in re.split(r"[_\-\s]+", cleaned) if part]
        if not parts:
            return ""
        if relation:
            return "_".join(part.upper() for part in parts)
        return "".join(part[:1].upper() + part[1:] for part in parts)

    @staticmethod
    def _to_display_name(name: str, *, relation: bool) -> str:
        if relation:
            return name.replace("_", " ").title()
        return re.sub(r"(?<!^)([A-Z])", r" \1", name).strip() or name

    def _normalize_attributes(self, attributes: Any) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for attribute in attributes or []:
            if not isinstance(attribute, dict):
                continue
            name = str(attribute.get("name", "") or "").strip()
            if not name:
                continue
            normalized.append(
                {
                    "name": name,
                    "type": str(attribute.get("type", "text") or "text").strip(),
                    "description": str(attribute.get("description", "") or "").strip()[:120],
                }
            )
        return self._merge_list_of_dicts([], normalized)

    def _normalize_source_targets(self, source_targets: Any) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for item in source_targets or []:
            if not isinstance(item, dict):
                continue
            source = self._normalize_type_name(str(item.get("source", "") or "").strip(), relation=False)
            target = self._normalize_type_name(str(item.get("target", "") or "").strip(), relation=False)
            if source and target:
                normalized.append({"source": source, "target": target})
        return self._merge_list_of_dicts([], normalized)

    @staticmethod
    def _merge_string_lists(existing: Any, incoming: Any) -> list[str]:
        values: list[str] = []
        seen: set[str] = set()
        for group in (existing or [], incoming or []):
            if isinstance(group, str):
                candidates = [group]
            else:
                candidates = list(group) if isinstance(group, (list, tuple, set)) else []
            for candidate in candidates:
                value = str(candidate or "").strip()
                if not value:
                    continue
                normalized = value.casefold()
                if normalized in seen:
                    continue
                seen.add(normalized)
                values.append(value)
        return values

    @staticmethod
    def _merge_list_of_dicts(existing: Any, incoming: Any) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()
        for collection in (existing or [], incoming or []):
            candidates = list(collection) if isinstance(collection, list) else []
            for item in candidates:
                if not isinstance(item, dict):
                    continue
                key = json.dumps(item, ensure_ascii=False, sort_keys=True)
                if key in seen:
                    continue
                seen.add(key)
                merged.append(item)
        return merged
