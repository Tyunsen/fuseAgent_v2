from __future__ import annotations

from typing import Any


def normalize_ontology(ontology: dict[str, Any] | None) -> dict[str, Any] | None:
    if not ontology:
        return ontology

    normalized = dict(ontology)
    normalized["entity_types"] = _normalize_items(
        ontology.get("entity_types", []) or [],
        extra_fields=("attributes", "examples"),
    )
    normalized["edge_types"] = _normalize_items(
        ontology.get("edge_types", []) or [],
        extra_fields=("source_targets", "attributes"),
    )
    normalized["analysis_summary"] = str(ontology.get("analysis_summary", "") or "").strip()
    return normalized


def _normalize_items(items: list[Any], *, extra_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    normalized_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "") or "").strip()
        if not name:
            continue

        normalized_item = dict(item)
        normalized_item["name"] = name
        normalized_item["display_name"] = str(item.get("display_name") or name).strip() or name
        for field_name in extra_fields:
            value = item.get(field_name)
            normalized_item[field_name] = value if value is not None else []
        normalized_items.append(normalized_item)
    return normalized_items
