from __future__ import annotations

import json
import logging
import re
import threading
from typing import Any

from openai import APIConnectionError, OpenAI

logger = logging.getLogger(__name__)


class LLMConnectionError(Exception):
    """Raised when LLM connection fails with helpful instructions."""

    def __init__(self, base_url: str | None, model: str, original_error: Exception | None = None) -> None:
        self.base_url = base_url
        self.model = model
        self.original_error = original_error
        url_info = f" (URL: {base_url})" if base_url else ""
        message = (
            f"无法连接到 LLM 服务{url_info}，模型: {model}\n\n"
            "图索引构建需要可用的 LLM 服务。可能原因及解决方案:\n"
            "1. 如果使用的是 Ollama: 请确保 Ollama 服务已启动 (ollama serve)\n"
            "2. 检查 base_url 配置是否正确\n"
            "3. 检查网络连接和 API Key\n"
            "4. 检查模型名称是否正确\n\n"
            f"原始错误: {original_error}"
        )
        super().__init__(message)


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

        try:
            response = self.client.chat.completions.create(**kwargs)
        except APIConnectionError as e:
            logger.error("LLM connection failed: %s", e)
            raise LLMConnectionError(self.base_url, self.model, e) from e
        except Exception as e:
            logger.error("LLM request failed: %s", e)
            raise LLMConnectionError(self.base_url, self.model, e) from e

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
