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
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON returned by MiroFish graph model: {cleaned}") from exc
