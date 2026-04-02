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
        return "Upload documents to start building the knowledge graph."
    if status == GRAPH_STATUS_BUILDING:
        return "Building the first knowledge graph from the documents in this knowledge base."
    if status == GRAPH_STATUS_UPDATING:
        if has_active_graph:
            return "Updating the graph with the latest documents added to this knowledge base."
        return "Building the first knowledge graph with the latest documents added to this knowledge base."
    if status == GRAPH_STATUS_READY:
        return "Knowledge graph is ready."
    if status == GRAPH_STATUS_FAILED:
        if has_active_graph:
            return "Graph update failed. Existing graph remains available."
        return "Initial graph build failed."
    return ""
