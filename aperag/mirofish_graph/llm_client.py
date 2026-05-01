from __future__ import annotations

import json
import re
import threading
from typing import Any

from openai import OpenAI


class MiroFishLLMClient:
    _thread_local = threading.local()

    def __init__(self, *, api_key: str, base_url: str | None, model: str) -> None:
        if not api_key:
            raise ValueError("LLM API key is required for MiroFish graph generation")
        if not model:
            raise ValueError("LLM model is required for MiroFish graph generation")

        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client_key = (self.api_key, self.base_url)

    @property
    def client(self) -> OpenAI:
        cache = getattr(self._thread_local, "client_cache", None)
        if cache and cache.get("key") == self._client_key:
            return cache["client"]

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self._thread_local.client_cache = {"key": self._client_key, "client": client}
        return client

    def chat(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        return re.sub(r"<think>[\s\S]*?</think>", "", content).strip()

    def chat_json(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", response, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()
        decoder = json.JSONDecoder()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            try:
                parsed, _ = decoder.raw_decode(cleaned)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

            repaired = self._repair_graph_json(cleaned)
            if repaired is not None:
                return repaired
            raise ValueError(f"Invalid JSON returned by MiroFish graph model: {cleaned}") from exc

    @staticmethod
    def _repair_graph_json(cleaned: str) -> dict[str, Any] | None:
        if '"entities"' not in cleaned and '"relations"' not in cleaned:
            return None

        entities = [
            item
            for item in MiroFishLLMClient._extract_completed_array_objects(cleaned, "entities")
            if item.get("name") and item.get("type")
        ]
        relations = [
            item
            for item in MiroFishLLMClient._extract_completed_array_objects(cleaned, "relations")
            if item.get("source_name") and item.get("target_name") and item.get("type")
        ]

        if not entities and not relations:
            return None

        return {
            "entities": entities,
            "relations": relations,
        }

    @staticmethod
    def _extract_completed_array_objects(cleaned: str, field_name: str) -> list[dict[str, Any]]:
        match = re.search(rf'"{re.escape(field_name)}"\s*:\s*\[', cleaned)
        if not match:
            return []

        objects: list[dict[str, Any]] = []
        index = match.end()
        depth = 0
        start: int | None = None
        in_string = False
        escaped = False

        while index < len(cleaned):
            char = cleaned[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                index += 1
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                if depth == 0:
                    start = index
                depth += 1
            elif char == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start is not None:
                        candidate = cleaned[start : index + 1]
                        try:
                            parsed = json.loads(candidate)
                        except json.JSONDecodeError:
                            parsed = None
                        if isinstance(parsed, dict):
                            objects.append(parsed)
                        start = None
            elif char == "]" and depth == 0:
                break

            index += 1

        return objects
