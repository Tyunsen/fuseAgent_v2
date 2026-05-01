#!/usr/bin/env python3
# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# -*- coding: utf-8 -*-
import ipaddress
import logging
from threading import Lock
from urllib.parse import urlparse

from aperag.config import settings
from aperag.db.models import APIType
from aperag.db.ops import db_ops
from aperag.llm.embed.embedding_service import EmbeddingService
from aperag.llm.llm_error_types import (
    EmbeddingError,
    InvalidConfigurationError,
    ProviderNotFoundError,
)
from aperag.schema.utils import parseCollectionConfig

logger = logging.getLogger(__name__)

mutex = Lock()

_dimension_cache: dict[tuple[str, str], int] = {}
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "host.docker.internal"}


def synchronized(func):
    def wrapper(*args, **kwargs):
        with mutex:
            return func(*args, **kwargs)

    return wrapper


def _normalize_hostname(service_url: str | None) -> str | None:
    if not service_url:
        return None

    parsed = urlparse(service_url if "://" in service_url else f"http://{service_url}")
    if not parsed.hostname:
        return None
    return parsed.hostname.lower()


def _is_loopback_or_private_host(hostname: str | None) -> bool:
    if not hostname:
        return False

    if hostname in _LOCAL_HOSTS or hostname.endswith(".local"):
        return True

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return False

    return ip.is_loopback or ip.is_private or ip.is_link_local


def _is_local_embedding_provider(
    embedding_provider_name: str,
    custom_llm_provider: str,
    embedding_service_url: str,
) -> bool:
    provider_hints = [embedding_provider_name, custom_llm_provider]
    if any(hint and "ollama" in hint.lower() for hint in provider_hints):
        return True

    return _is_loopback_or_private_host(_normalize_hostname(embedding_service_url))


def _build_placeholder_api_key(embedding_provider_name: str, custom_llm_provider: str) -> str:
    provider_hints = [embedding_provider_name, custom_llm_provider]
    if any(hint and "ollama" in hint.lower() for hint in provider_hints):
        return "ollama"
    return "local"


def _resolve_embedding_api_key(
    embedding_provider_name: str,
    custom_llm_provider: str,
    embedding_service_url: str,
    stored_api_key: str | None,
) -> str:
    if stored_api_key:
        return stored_api_key

    if _is_local_embedding_provider(embedding_provider_name, custom_llm_provider, embedding_service_url):
        placeholder_key = _build_placeholder_api_key(embedding_provider_name, custom_llm_provider)
        logger.info(
            "Using placeholder API key for local/self-hosted embedding provider %s at %s",
            embedding_provider_name,
            embedding_service_url,
        )
        return placeholder_key

    error_msg = (
        f"LLM Provider '{embedding_provider_name}' 未配置 API Key。\n\n"
        f"配置信息:\n"
        f"- Provider: {embedding_provider_name}\n"
        f"- Base URL: {embedding_service_url or 'unknown'}\n\n"
        f"处理建议:\n"
        f"1. 云端 Embedding 服务需要先在 Settings > Models > API Keys 中配置真实 API Key\n"
        f"2. 如果这其实是本地或自托管服务，请确认 Base URL 指向 localhost、内网地址或 Ollama 服务\n"
    )
    raise InvalidConfigurationError("api_key", None, error_msg)


def _get_embedding_dimension(
    embedding_svc: EmbeddingService,
    embedding_provider: str,
    embedding_model: str,
    embedding_service_url: str,
) -> int:
    """
    Get embedding dimension by probing the embedding service.

    Args:
        embedding_svc: The embedding service instance
        embedding_provider: Provider name for caching
        embedding_model: Model name for caching
        embedding_service_url: The API base URL

    Returns:
        int: The embedding dimension

    Raises:
        EmbeddingError: If dimension probing fails
    """
    cache_key = (embedding_provider, embedding_model)
    if cache_key in _dimension_cache:
        return _dimension_cache[cache_key]

    try:
        vec = embedding_svc.embed_query("dimension_probe")
        if not vec:
            raise EmbeddingError(
                "Failed to obtain embedding vector while probing dimension",
                {
                    "provider": embedding_provider,
                    "model": embedding_model,
                    "api_base": embedding_service_url,
                },
            )
        if isinstance(vec[0], (list, tuple)):
            vec = vec[0]
        dim = len(vec)
        _dimension_cache[cache_key] = dim
        logger.info("Cached embedding dimension for %s/%s: %s", embedding_provider, embedding_model, dim)
        return dim
    except Exception as e:
        logger.error("Failed to probe embedding dimension for %s/%s: %s", embedding_provider, embedding_model, e)
        error_msg = (
            f"无法连接 Embedding 服务 ({embedding_provider}/{embedding_model})。\n\n"
            f"配置信息:\n"
            f"- Base URL: {embedding_service_url or 'unknown'}\n\n"
            f"可能原因及解决方案:\n"
            f"1. 如果使用的是本地服务，请确认服务已启动且地址可达\n"
            f"2. 如果使用的是云端服务，请检查网络连接和 API Key 配置\n"
            f"3. 请检查集合中的 provider 与 model 配置是否正确\n\n"
            f"原始错误: {str(e)}"
        )
        raise EmbeddingError(
            error_msg,
            {
                "provider": embedding_provider,
                "model": embedding_model,
                "api_base": embedding_service_url,
                "original_error": str(e),
            },
        ) from e


@synchronized
def _get_embedding_model(
    embedding_provider: str,
    embedding_model: str,
    embedding_service_url: str,
    embedding_service_api_key: str,
    embedding_max_chunks_in_batch: int = settings.embedding_max_chunks_in_batch,
    multimodal: bool = False,
) -> tuple[EmbeddingService | None, int]:
    """
    Create and configure an embedding model instance.

    Args:
        embedding_provider: The embedding provider name
        embedding_model: The embedding model name
        embedding_service_url: The API base URL
        embedding_service_api_key: The API key
        embedding_max_chunks_in_batch: Maximum chunks per batch

    Returns:
        tuple: (EmbeddingService instance, embedding dimension)

    Raises:
        EmbeddingError: If model creation or dimension probing fails
    """
    try:
        embedding_svc = EmbeddingService(
            embedding_provider,
            embedding_model,
            embedding_service_url,
            embedding_service_api_key,
            embedding_max_chunks_in_batch,
            multimodal=multimodal,
        )
        embedding_dim = _get_embedding_dimension(
            embedding_svc=embedding_svc,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            embedding_service_url=embedding_service_url,
        )
        return embedding_svc, embedding_dim
    except EmbeddingError:
        raise
    except Exception as e:
        logger.error("Failed to create embedding model %s/%s: %s", embedding_provider, embedding_model, e)
        error_msg = (
            f"无法创建 Embedding 模型实例 ({embedding_provider}/{embedding_model})。\n\n"
            f"配置信息:\n"
            f"- Base URL: {embedding_service_url or 'unknown'}\n\n"
            f"可能原因及解决方案:\n"
            f"1. 如果使用的是本地服务，请确认服务已启动且地址可达\n"
            f"2. 请检查当前 API 地址是否正确\n"
            f"3. 请检查模型名称 '{embedding_model}' 是否在该 provider 中存在\n"
            f"4. 如使用云端服务，请确认 API Key 是否正确配置\n\n"
            f"原始错误: {str(e)}"
        )
        raise EmbeddingError(
            error_msg,
            {
                "provider": embedding_provider,
                "model": embedding_model,
                "api_base": embedding_service_url,
                "original_error": str(e),
            },
        ) from e


def get_collection_embedding_service_sync(collection) -> tuple[EmbeddingService, int]:
    """
    Get embedding service for a collection synchronously.

    Args:
        collection: The collection object with configuration

    Returns:
        tuple: (Embeddings instance, embedding dimension)

    Raises:
        ProviderNotFoundError: If the embedding provider is not found
        InvalidConfigurationError: If configuration is invalid
        EmbeddingError: If embedding service creation fails
    """
    try:
        config = parseCollectionConfig(collection.config)
    except Exception as e:
        logger.error("Failed to parse collection config: %s", e)
        raise InvalidConfigurationError(
            "collection.config", collection.config, f"Invalid collection configuration: {str(e)}"
        ) from e

    embedding_msp = config.embedding.model_service_provider
    embedding_model_name = config.embedding.model
    custom_llm_provider = config.embedding.custom_llm_provider

    logger.info("get_collection_embedding_model_sync %s %s", embedding_msp, embedding_model_name)

    if not embedding_msp:
        raise InvalidConfigurationError(
            "embedding.model_service_provider",
            embedding_msp,
            "Model service provider cannot be empty",
        )

    if not embedding_model_name:
        raise InvalidConfigurationError("embedding.model", embedding_model_name, "Model name cannot be empty")

    if not custom_llm_provider:
        raise InvalidConfigurationError(
            "embedding.custom_llm_provider",
            custom_llm_provider,
            "Custom LLM provider cannot be empty",
        )

    try:
        llm_provider = db_ops.query_llm_provider_by_name(embedding_msp)
    except Exception as e:
        logger.error("Failed to query LLM provider '%s': %s", embedding_msp, e)
        raise ProviderNotFoundError(embedding_msp, "Embedding") from e

    if not llm_provider:
        raise ProviderNotFoundError(embedding_msp, "Embedding")

    embedding_service_url = llm_provider.base_url
    if not embedding_service_url:
        raise InvalidConfigurationError(
            "base_url",
            embedding_service_url,
            f"Base URL not configured for provider '{embedding_msp}'",
        )

    try:
        multimodal = False
        model = db_ops.query_llm_provider_model(embedding_msp, APIType.EMBEDDING.value, embedding_model_name)
        if model:
            multimodal = model.has_tag("multimodal")
    except Exception:
        logger.error("Failed to query embedding model '%s/%s'", embedding_msp, embedding_model_name, exc_info=True)
        raise

    stored_api_key = db_ops.query_provider_api_key(embedding_msp, collection.user)
    embedding_service_api_key = _resolve_embedding_api_key(
        embedding_provider_name=embedding_msp,
        custom_llm_provider=custom_llm_provider,
        embedding_service_url=embedding_service_url,
        stored_api_key=stored_api_key,
    )

    logger.info("get_collection_embedding_model %s", embedding_service_url)

    try:
        return _get_embedding_model(
            embedding_provider=custom_llm_provider,
            embedding_model=embedding_model_name,
            embedding_service_url=embedding_service_url,
            embedding_service_api_key=embedding_service_api_key,
            multimodal=multimodal,
        )
    except EmbeddingError as e:
        if e.details.get("api_base"):
            raise

        raise EmbeddingError(
            e.message,
            {
                **e.details,
                "collection_id": getattr(collection, "id", "unknown"),
                "provider": embedding_msp,
                "model": embedding_model_name,
                "api_base": embedding_service_url,
            },
        ) from e
    except Exception as e:
        logger.error("Failed to get embedding model for collection: %s", e)
        error_msg = (
            f"无法为集合获取 Embedding 模型。\n\n"
            f"配置信息:\n"
            f"- 集合 ID: {getattr(collection, 'id', 'unknown')}\n"
            f"- Provider: {embedding_msp}\n"
            f"- 模型: {embedding_model_name}\n"
            f"- Base URL: {embedding_service_url or 'unknown'}\n\n"
            f"可能原因:\n"
            f"1. Embedding 服务不可达\n"
            f"2. 云端 API Key 未配置或无效\n"
            f"3. 模型配置错误\n\n"
            f"原始错误: {str(e)}"
        )
        raise EmbeddingError(
            error_msg,
            {
                "collection_id": getattr(collection, "id", "unknown"),
                "provider": embedding_msp,
                "model": embedding_model_name,
                "api_base": embedding_service_url,
                "original_error": str(e),
            },
        ) from e
