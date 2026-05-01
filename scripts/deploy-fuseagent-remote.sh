#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

if [[ ! -f .env ]]; then
  cp envs/env.remote.template .env
fi

set -a
source .env
set +a

if [[ -n "${FUSEAGENT_ACCEPTANCE_CELERY_WORKER_CONCURRENCY:-}" ]]; then
  export CELERY_WORKER_CONCURRENCY="${FUSEAGENT_ACCEPTANCE_CELERY_WORKER_CONCURRENCY}"
  if [[ -z "${FUSEAGENT_ACCEPTANCE_CELERY_GRAPH_WORKER_CONCURRENCY:-}" ]]; then
    export CELERY_GRAPH_WORKER_CONCURRENCY="${FUSEAGENT_ACCEPTANCE_CELERY_WORKER_CONCURRENCY}"
  fi
fi

if [[ -n "${FUSEAGENT_ACCEPTANCE_CELERY_GRAPH_WORKER_CONCURRENCY:-}" ]]; then
  export CELERY_GRAPH_WORKER_CONCURRENCY="${FUSEAGENT_ACCEPTANCE_CELERY_GRAPH_WORKER_CONCURRENCY}"
fi

if [[ -n "${FUSEAGENT_ACCEPTANCE_CHUNK_SIZE:-}" ]]; then
  export CHUNK_SIZE="${FUSEAGENT_ACCEPTANCE_CHUNK_SIZE}"
fi

if [[ -n "${FUSEAGENT_ACCEPTANCE_CHUNK_OVERLAP_SIZE:-}" ]]; then
  export CHUNK_OVERLAP_SIZE="${FUSEAGENT_ACCEPTANCE_CHUNK_OVERLAP_SIZE}"
fi

if [[ -n "${FUSEAGENT_ACCEPTANCE_EMBEDDING_BATCH_SIZE:-}" ]]; then
  export EMBEDDING_MAX_CHUNKS_IN_BATCH="${FUSEAGENT_ACCEPTANCE_EMBEDDING_BATCH_SIZE}"
fi

if [[ -n "${FUSEAGENT_ACCEPTANCE_GRAPH_EXTRACTION_CONCURRENCY:-}" ]]; then
  export GRAPH_EXTRACTION_CONCURRENCY="${FUSEAGENT_ACCEPTANCE_GRAPH_EXTRACTION_CONCURRENCY}"
fi

if [[ -n "${FUSEAGENT_ACCEPTANCE_GRAPH_EXTRACTION_MAX_TOKENS:-}" ]]; then
  export GRAPH_EXTRACTION_MAX_TOKENS="${FUSEAGENT_ACCEPTANCE_GRAPH_EXTRACTION_MAX_TOKENS}"
fi

if [[ -n "${FUSEAGENT_ACCEPTANCE_GRAPH_DEFAULT_CHUNK_SIZE:-}" ]]; then
  export GRAPH_DEFAULT_CHUNK_SIZE="${FUSEAGENT_ACCEPTANCE_GRAPH_DEFAULT_CHUNK_SIZE}"
fi

if [[ -n "${FUSEAGENT_ACCEPTANCE_GRAPH_DEFAULT_CHUNK_OVERLAP:-}" ]]; then
  export GRAPH_DEFAULT_CHUNK_OVERLAP="${FUSEAGENT_ACCEPTANCE_GRAPH_DEFAULT_CHUNK_OVERLAP}"
fi

profiles=()

if [[ "${WITH_DOCRAY_GPU:-0}" == "1" ]]; then
  profiles+=(--profile docray-gpu)
  export DOCRAY_HOST="${DOCRAY_HOST:-http://aperag-docray-gpu:8639}"
elif [[ "${WITH_DOCRAY:-0}" == "1" ]]; then
  profiles+=(--profile docray)
  export DOCRAY_HOST="${DOCRAY_HOST:-http://aperag-docray:8639}"
fi

if [[ "${WITH_NEO4J:-0}" == "1" ]]; then
  profiles+=(--profile neo4j)
fi

if [[ -n "${FUSEAGENT_GPU_DEVICE:-}" ]]; then
  export CUDA_VISIBLE_DEVICES="${FUSEAGENT_GPU_DEVICE}"
  export NVIDIA_VISIBLE_DEVICES="${FUSEAGENT_GPU_DEVICE}"
fi

docker compose -f docker-compose.deploy.remote.yml "${profiles[@]}" up -d --build --remove-orphans

completion_provider_name="${BOOTSTRAP_COMPLETION_PROVIDER_NAME:-${BOOTSTRAP_PROVIDER_NAME:-}}"
completion_provider_base_url="${BOOTSTRAP_COMPLETION_PROVIDER_BASE_URL:-${BOOTSTRAP_PROVIDER_BASE_URL:-}}"
completion_provider_api_key="${BOOTSTRAP_COMPLETION_PROVIDER_API_KEY:-${BOOTSTRAP_PROVIDER_API_KEY:-}}"

embedding_provider_name="${BOOTSTRAP_EMBEDDING_PROVIDER_NAME:-${BOOTSTRAP_PROVIDER_NAME:-}}"
embedding_provider_base_url="${BOOTSTRAP_EMBEDDING_PROVIDER_BASE_URL:-${BOOTSTRAP_PROVIDER_BASE_URL:-}}"
embedding_provider_api_key="${BOOTSTRAP_EMBEDDING_PROVIDER_API_KEY:-${BOOTSTRAP_PROVIDER_API_KEY:-}}"

if [[ -n "${completion_provider_name}" || -n "${embedding_provider_name}" ]]; then
  exec_env_flags=(
    -e "BOOTSTRAP_PROVIDER_NAME=${BOOTSTRAP_PROVIDER_NAME:-}"
    -e "BOOTSTRAP_PROVIDER_BASE_URL=${BOOTSTRAP_PROVIDER_BASE_URL:-}"
    -e "BOOTSTRAP_PROVIDER_API_KEY=${BOOTSTRAP_PROVIDER_API_KEY:-}"
    -e "BOOTSTRAP_COMPLETION_PROVIDER_NAME=${completion_provider_name:-}"
    -e "BOOTSTRAP_COMPLETION_PROVIDER_BASE_URL=${completion_provider_base_url:-}"
    -e "BOOTSTRAP_COMPLETION_PROVIDER_API_KEY=${completion_provider_api_key:-}"
    -e "BOOTSTRAP_COMPLETION_MODEL=${BOOTSTRAP_COMPLETION_MODEL:-}"
    -e "BOOTSTRAP_COMPLETION_CUSTOM_PROVIDER=${BOOTSTRAP_COMPLETION_CUSTOM_PROVIDER:-}"
    -e "BOOTSTRAP_EMBEDDING_PROVIDER_NAME=${embedding_provider_name:-}"
    -e "BOOTSTRAP_EMBEDDING_PROVIDER_BASE_URL=${embedding_provider_base_url:-}"
    -e "BOOTSTRAP_EMBEDDING_PROVIDER_API_KEY=${embedding_provider_api_key:-}"
    -e "BOOTSTRAP_EMBEDDING_MODEL=${BOOTSTRAP_EMBEDDING_MODEL:-}"
    -e "BOOTSTRAP_EMBEDDING_CUSTOM_PROVIDER=${BOOTSTRAP_EMBEDDING_CUSTOM_PROVIDER:-}"
  )

  docker compose -f docker-compose.deploy.remote.yml exec -T \
    "${exec_env_flags[@]}" \
    api python - <<'PY'
import asyncio
import os

from aperag.db.ops import async_db_ops


def merge_tags(*groups):
    merged = []
    for group in groups:
        for tag in group or []:
            if tag not in merged:
                merged.append(tag)
    return merged


def titleize_provider(name):
    return name.replace("-", " ").replace("_", " ").title()


def resolve_custom_provider(api, provider_name):
    env_key = f"BOOTSTRAP_{api.upper()}_CUSTOM_PROVIDER"
    explicit = os.environ.get(env_key, "").strip()
    if explicit:
        return explicit
    return provider_name if api == "completion" else "openai"


def resolve_provider_config(api):
    legacy_provider_name = os.environ.get("BOOTSTRAP_PROVIDER_NAME", "").strip()
    legacy_provider_base_url = os.environ.get("BOOTSTRAP_PROVIDER_BASE_URL", "").strip()
    legacy_provider_api_key = os.environ.get("BOOTSTRAP_PROVIDER_API_KEY", "").strip()

    provider_name = os.environ.get(f"BOOTSTRAP_{api.upper()}_PROVIDER_NAME", "").strip() or legacy_provider_name
    model_name = os.environ.get(f"BOOTSTRAP_{api.upper()}_MODEL", "").strip()
    if not provider_name or not model_name:
        return None

    return {
        "api": api,
        "provider_name": provider_name,
        "base_url": os.environ.get(f"BOOTSTRAP_{api.upper()}_PROVIDER_BASE_URL", "").strip() or legacy_provider_base_url,
        "api_key": os.environ.get(f"BOOTSTRAP_{api.upper()}_PROVIDER_API_KEY", "").strip() or legacy_provider_api_key,
        "model_name": model_name,
        "custom_provider": resolve_custom_provider(api, provider_name),
        "tags": (
            [
                "enable_for_collection",
                "enable_for_agent",
                "default_for_collection_completion",
                "default_for_agent_completion",
                "default_for_background_task",
            ]
            if api == "completion"
            else [
                "enable_for_collection",
                "default_for_embedding",
            ]
        ),
    }


async def ensure_provider(config):
    provider_name = config["provider_name"]
    provider = await async_db_ops.query_llm_provider_by_name(provider_name)

    if provider is None and not config["base_url"]:
        raise SystemExit(
            f"Provider '{provider_name}' is missing and no base URL was supplied for bootstrap."
        )

    completion_dialect = getattr(provider, "completion_dialect", None) or "openai"
    embedding_dialect = getattr(provider, "embedding_dialect", None) or "openai"
    rerank_dialect = getattr(provider, "rerank_dialect", None) or "jina_ai"

    if config["api"] == "completion":
        completion_dialect = config["custom_provider"] or completion_dialect
    else:
        embedding_dialect = config["custom_provider"] or embedding_dialect

    if provider is None:
        await async_db_ops.create_llm_provider(
            name=provider_name,
            user_id="public",
            label=titleize_provider(provider_name),
            completion_dialect=completion_dialect,
            embedding_dialect=embedding_dialect,
            rerank_dialect=rerank_dialect,
            allow_custom_base_url=False,
            base_url=config["base_url"],
        )
    else:
        update_kwargs = {
            "name": provider_name,
            "label": getattr(provider, "label", None) or titleize_provider(provider_name),
            "completion_dialect": completion_dialect,
            "embedding_dialect": embedding_dialect,
            "rerank_dialect": rerank_dialect,
        }
        if config["base_url"]:
            update_kwargs["base_url"] = config["base_url"]
        await async_db_ops.update_llm_provider(**update_kwargs)

    if config["api_key"]:
        await async_db_ops.upsert_msp(name=provider_name, api_key=config["api_key"])


async def upsert_model(config):
    existing = await async_db_ops.query_llm_provider_model(
        config["provider_name"],
        config["api"],
        config["model_name"],
    )
    tags = merge_tags(getattr(existing, "tags", []), config["tags"])

    if existing:
        await async_db_ops.update_llm_provider_model(
            provider_name=config["provider_name"],
            api=config["api"],
            model=config["model_name"],
            custom_llm_provider=config["custom_provider"],
            tags=tags,
        )
        return

    await async_db_ops.create_llm_provider_model(
        provider_name=config["provider_name"],
        api=config["api"],
        model=config["model_name"],
        custom_llm_provider=config["custom_provider"],
        tags=tags,
    )


async def main():
    bootstrap_configs = [
        config
        for config in (
            resolve_provider_config("completion"),
            resolve_provider_config("embedding"),
        )
        if config is not None
    ]

    for config in bootstrap_configs:
        await ensure_provider(config)
        await upsert_model(config)


asyncio.run(main())
PY
fi

docker compose -f docker-compose.deploy.remote.yml ps
