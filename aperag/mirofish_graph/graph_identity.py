from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any


_ALIAS_HINT_KEYS = {
    "alias",
    "aliases",
    "aka",
    "country name",
    "full name",
    "official name",
    "organization name",
    "org name",
    "display name",
    "native name",
    "name zh",
    "name cn",
}


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKC", text)
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_name(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-_]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_cjk(value: Any) -> bool:
    text = "" if value is None else str(value)
    return bool(re.search(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text))


def _iter_alias_values(attributes: Any):
    if isinstance(attributes, dict):
        for key, value in attributes.items():
            normalized_key = normalize_name(key)
            if normalized_key in _ALIAS_HINT_KEYS:
                if isinstance(value, (list, tuple, set)):
                    for item in value:
                        yield from _iter_alias_values(item)
                elif isinstance(value, dict):
                    yield from _iter_alias_values(value)
                elif value is not None:
                    yield str(value)
    elif isinstance(attributes, (list, tuple, set)):
        for item in attributes:
            yield from _iter_alias_values(item)
    elif attributes is not None:
        yield str(attributes)


def unique_names(values: list[Any]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = "" if value is None else str(value).strip()
        if not text:
            continue
        normalized = normalize_name(text)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(text)
    return deduped


def collect_entity_aliases(name: str, attributes: Any = None) -> list[str]:
    aliases = [name]
    aliases.extend(_iter_alias_values(attributes))
    return unique_names(aliases)


def choose_preferred_name(*candidates: Any) -> str:
    values = unique_names(list(candidates))
    if not values:
        return ""
    for value in values:
        if contains_cjk(value):
            return value
    return values[0]


def prefer_entity_name(name: str, attributes: Any = None) -> str:
    aliases = collect_entity_aliases(name, attributes)
    return choose_preferred_name(*aliases)


def canonical_json(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(*parts: Any, length: int = 24) -> str:
    normalized = "\u241f".join(normalize_text(part) for part in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:length]


def graph_key(project_id: str) -> str:
    return f"graph_{stable_digest(project_id, 'graph')}"


def document_key(project_id: str, filename: str) -> str:
    return f"doc_{stable_digest(project_id, filename)}"


def chunk_key(project_id: str, document_id: str, chunk_index: int, chunk_text: str) -> str:
    return f"chunk_{stable_digest(project_id, document_id, chunk_index, chunk_text)}"


def entity_key(graph_id: str, entity_type: str, entity_name: str) -> str:
    return f"entity_{stable_digest(graph_id, entity_type, normalize_name(entity_name))}"


def relation_key(
    graph_id: str,
    source_entity_id: str,
    relation_type: str,
    target_entity_id: str,
    fact: str,
) -> str:
    return f"rel_{stable_digest(graph_id, source_entity_id, relation_type, target_entity_id, fact)}"
