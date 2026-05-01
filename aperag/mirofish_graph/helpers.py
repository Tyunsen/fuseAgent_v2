from __future__ import annotations

from typing import Any

from aperag.schema.view_models import CollectionConfig

from .constants import (
    GRAPH_STATUS_BUILDING,
    GRAPH_STATUS_FAILED,
    GRAPH_STATUS_READY,
    GRAPH_STATUS_UPDATING,
    GRAPH_STATUS_WAITING_FOR_DOCUMENTS,
    MIROFISH_CREATION_MODE,
    MIROFISH_GRAPH_ENGINE,
)


def is_mirofish_collection_config(config: CollectionConfig | dict[str, Any] | None) -> bool:
    if config is None:
        return False

    if isinstance(config, dict):
        creation_mode = config.get("creation_mode")
        graph_engine = config.get("graph_engine")
    else:
        creation_mode = config.creation_mode
        graph_engine = config.graph_engine

    return creation_mode == MIROFISH_CREATION_MODE or graph_engine == MIROFISH_GRAPH_ENGINE


def build_graph_status_message(status: str, *, has_active_graph: bool = False) -> str:
    if status == GRAPH_STATUS_WAITING_FOR_DOCUMENTS:
        return "Waiting for the first document upload."
    if status == GRAPH_STATUS_BUILDING:
        return "Building the initial knowledge graph from confirmed documents."
    if status == GRAPH_STATUS_UPDATING:
        if has_active_graph:
            return "Updating the graph with the latest confirmed documents."
        return "Rebuilding the initial graph with the latest confirmed documents."
    if status == GRAPH_STATUS_READY:
        return "Knowledge graph is ready."
    if status == GRAPH_STATUS_FAILED:
        if has_active_graph:
            return "Graph update failed. Existing graph remains available."
        return "Initial graph build failed."
    return ""


def sanitize_graph_attributes(attributes: Any) -> dict[str, Any]:
    if not isinstance(attributes, dict):
        return {}

    sanitized: dict[str, Any] = {}
    for raw_key, raw_value in attributes.items():
        key = str(raw_key or "").strip()
        if not key or raw_value is None:
            continue

        if key == "place_aliases":
            values = raw_value if isinstance(raw_value, (list, tuple, set)) else [raw_value]
            aliases = []
            seen: set[str] = set()
            for value in values:
                alias = str(value or "").strip()
                if not alias:
                    continue
                normalized = alias.casefold()
                if normalized in seen:
                    continue
                seen.add(normalized)
                aliases.append(alias)
            if aliases:
                sanitized[key] = aliases
            continue

        if isinstance(raw_value, (str, int, float, bool)):
            value = str(raw_value).strip()
            if value:
                sanitized[key] = value
            continue

        if isinstance(raw_value, (list, tuple, set)):
            values = [str(item).strip() for item in raw_value if str(item).strip()]
            if values:
                sanitized[key] = values

    return sanitized
