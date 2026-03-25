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

if [[ -n "${BOOTSTRAP_PROVIDER_NAME:-}" ]]; then
  exec_env_flags=(
    -e "BOOTSTRAP_PROVIDER_NAME=${BOOTSTRAP_PROVIDER_NAME:-}"
    -e "BOOTSTRAP_PROVIDER_BASE_URL=${BOOTSTRAP_PROVIDER_BASE_URL:-}"
    -e "BOOTSTRAP_PROVIDER_API_KEY=${BOOTSTRAP_PROVIDER_API_KEY:-}"
    -e "BOOTSTRAP_COMPLETION_MODEL=${BOOTSTRAP_COMPLETION_MODEL:-}"
    -e "BOOTSTRAP_COMPLETION_CUSTOM_PROVIDER=${BOOTSTRAP_COMPLETION_CUSTOM_PROVIDER:-}"
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


async def upsert_model(provider_name, api, model_name, custom_provider, default_tag):
    if not model_name:
        return

    existing = await async_db_ops.query_llm_provider_model(provider_name, api, model_name)
    tags = merge_tags(
        getattr(existing, "tags", []),
        ["enable_for_collection", default_tag],
    )

    if existing:
        await async_db_ops.update_llm_provider_model(
            provider_name=provider_name,
            api=api,
            model=model_name,
            custom_llm_provider=custom_provider,
            tags=tags,
        )
        return

    await async_db_ops.create_llm_provider_model(
        provider_name=provider_name,
        api=api,
        model=model_name,
        custom_llm_provider=custom_provider,
        tags=tags,
    )


async def main():
    provider_name = os.environ.get("BOOTSTRAP_PROVIDER_NAME", "").strip()
    if not provider_name:
        return

    provider = await async_db_ops.query_llm_provider_by_name(provider_name)
    if provider is None:
        raise SystemExit(f"Provider '{provider_name}' was not found in seeded configs.")

    base_url = os.environ.get("BOOTSTRAP_PROVIDER_BASE_URL", "").strip()
    if base_url:
        await async_db_ops.update_llm_provider(
            name=provider_name,
            base_url=base_url,
        )

    api_key = os.environ.get("BOOTSTRAP_PROVIDER_API_KEY", "").strip()
    if api_key:
        await async_db_ops.upsert_msp(name=provider_name, api_key=api_key)

    await upsert_model(
        provider_name=provider_name,
        api="completion",
        model_name=os.environ.get("BOOTSTRAP_COMPLETION_MODEL", "").strip(),
        custom_provider=os.environ.get("BOOTSTRAP_COMPLETION_CUSTOM_PROVIDER", "").strip() or provider_name,
        default_tag="default_for_collection_completion",
    )
    await upsert_model(
        provider_name=provider_name,
        api="embedding",
        model_name=os.environ.get("BOOTSTRAP_EMBEDDING_MODEL", "").strip(),
        custom_provider=os.environ.get("BOOTSTRAP_EMBEDDING_CUSTOM_PROVIDER", "").strip() or "openai",
        default_tag="default_for_embedding",
    )


asyncio.run(main())
PY
fi

docker compose -f docker-compose.deploy.remote.yml ps
