from __future__ import annotations

import argparse
import asyncio
import csv
import json
import mimetypes
import os
import re
import socket
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import paramiko
import websockets
from pypdf import PdfReader

from tunnel_remote_fuseagent import (
    REMOTE_HOST,
    REMOTE_USERNAME,
    connect_client,
    find_free_port,
    start_forward_server,
)


IW_DOCS_DIR = Path(r"E:\codes\fuseAgent_v2\iw_docs")
REMOTE_PROJECT_DIR = "/home/common/jyzhu/ucml/fuseAgent-current"
REMOTE_DEPLOY_COMMAND = "bash scripts/deploy-fuseagent-remote.sh"
DEFAULT_REMOTE_WEB_PORT = 36130
DEFAULT_REMOTE_API_PORT = 36180
INDEX_BUDGET_SECONDS = 240
MIN_GRAPH_NODES = 81
MIN_GRAPH_EDGES = 101
REQUEST_RETRY_COUNT = 3
ACCEPTANCE_CELERY_WORKER_CONCURRENCY = 24
ACCEPTANCE_CELERY_GRAPH_WORKER_CONCURRENCY = 1
ACCEPTANCE_CHUNK_SIZE = 1800
ACCEPTANCE_CHUNK_OVERLAP_SIZE = 60
ACCEPTANCE_EMBEDDING_BATCH_SIZE = 64
ACCEPTANCE_GRAPH_EXTRACTION_CONCURRENCY = 12
ACCEPTANCE_GRAPH_EXTRACTION_MAX_TOKENS = 1600
ACCEPTANCE_GRAPH_DEFAULT_CHUNK_SIZE = 2400
ACCEPTANCE_GRAPH_DEFAULT_CHUNK_OVERLAP = 120
ACCEPTANCE_MAX_SOURCE_ITEMS = 15


@dataclass
class ModeResult:
    mode: str
    query: str
    answer: str
    references: list[dict[str, Any]]
    trace_support: dict[str, Any] | None
    passed: bool
    notes: list[str]


def run_remote_command(
    client: paramiko.SSHClient,
    command: str,
    *,
    timeout: int = 1800,
) -> tuple[str, str]:
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return out, err


def ensure_remote_stack() -> None:
    password = os.environ.get("FUSEAGENT_REMOTE_SSH_PASSWORD", "")
    if not password:
        raise RuntimeError("FUSEAGENT_REMOTE_SSH_PASSWORD is required")

    client = connect_client(password)
    try:
        command = (
            f"cd {REMOTE_PROJECT_DIR} && "
            f"FUSEAGENT_ACCEPTANCE_CELERY_WORKER_CONCURRENCY={ACCEPTANCE_CELERY_WORKER_CONCURRENCY} "
            f"FUSEAGENT_ACCEPTANCE_CELERY_GRAPH_WORKER_CONCURRENCY={ACCEPTANCE_CELERY_GRAPH_WORKER_CONCURRENCY} "
            f"FUSEAGENT_ACCEPTANCE_CHUNK_SIZE={ACCEPTANCE_CHUNK_SIZE} "
            f"FUSEAGENT_ACCEPTANCE_CHUNK_OVERLAP_SIZE={ACCEPTANCE_CHUNK_OVERLAP_SIZE} "
            f"FUSEAGENT_ACCEPTANCE_EMBEDDING_BATCH_SIZE={ACCEPTANCE_EMBEDDING_BATCH_SIZE} "
            f"FUSEAGENT_ACCEPTANCE_GRAPH_EXTRACTION_CONCURRENCY={ACCEPTANCE_GRAPH_EXTRACTION_CONCURRENCY} "
            f"FUSEAGENT_ACCEPTANCE_GRAPH_EXTRACTION_MAX_TOKENS={ACCEPTANCE_GRAPH_EXTRACTION_MAX_TOKENS} "
            f"FUSEAGENT_ACCEPTANCE_GRAPH_DEFAULT_CHUNK_SIZE={ACCEPTANCE_GRAPH_DEFAULT_CHUNK_SIZE} "
            f"FUSEAGENT_ACCEPTANCE_GRAPH_DEFAULT_CHUNK_OVERLAP={ACCEPTANCE_GRAPH_DEFAULT_CHUNK_OVERLAP} "
            f"{REMOTE_DEPLOY_COMMAND}"
        )
        out, err = run_remote_command(client, command)
        if err.strip():
            print(err[-4000:])
        if out.strip():
            print(out[-4000:])
    finally:
        client.close()


@contextmanager
def tunnel_context():
    password = os.environ.get("FUSEAGENT_REMOTE_SSH_PASSWORD", "")
    if not password:
        raise RuntimeError("FUSEAGENT_REMOTE_SSH_PASSWORD is required")

    local_web_port = find_free_port(46130)
    local_api_port = find_free_port(46180)

    client = connect_client(password)
    transport = client.get_transport()
    if transport is None or not transport.is_active():
        client.close()
        raise RuntimeError("SSH transport is not active")

    web_server = start_forward_server(transport, local_web_port, DEFAULT_REMOTE_WEB_PORT)
    api_server = start_forward_server(transport, local_api_port, DEFAULT_REMOTE_API_PORT)
    try:
        yield local_web_port, local_api_port
    finally:
        web_server.shutdown()
        web_server.server_close()
        api_server.shutdown()
        api_server.server_close()
        client.close()


def register_and_login(base_url: str) -> tuple[httpx.Client, dict[str, Any]]:
    username = f"trace_accept_{int(time.time())}"
    email = f"{username}@example.com"
    password = "TraceAccept!2026"

    register_payload = {"username": username, "email": email, "password": password}
    register_resp = httpx.post(
        f"{base_url}/api/v1/register",
        json=register_payload,
        timeout=30,
    )
    if register_resp.status_code == 404:
        register_resp = httpx.post(
            f"{base_url}/api/v1/test/register_admin",
            json=register_payload,
            timeout=30,
        )
    register_resp.raise_for_status()

    client = httpx.Client(base_url=base_url, timeout=60)
    login_resp = client.post("/api/v1/login", json={"username": username, "password": password})
    login_resp.raise_for_status()
    user = login_resp.json()
    return client, user


def wait_for_api_ready(base_url: str, timeout_seconds: int = 90) -> None:
    started = time.time()
    while True:
        try:
            response = httpx.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                return
        except Exception:
            pass
        if time.time() - started > timeout_seconds:
            raise TimeoutError("API did not become ready within the expected startup window")
        time.sleep(3)


def create_collection(client: httpx.Client) -> dict[str, Any]:
    response = client.post(
        "/api/v1/collections",
        json={
            "title": f"Triple Trace Acceptance {int(time.time())}",
            "description": "Recurring acceptance knowledge base built from iw_docs",
            "type": "document",
        },
    )
    response.raise_for_status()
    return response.json()


def upload_all_documents(client: httpx.Client, collection_id: str) -> list[str]:
    files_to_upload = [
        path for path in sorted(IW_DOCS_DIR.iterdir()) if path.is_file()
    ]
    request_files: list[tuple[str, tuple[str, bytes, str]]] = []
    for path in files_to_upload:
        upload_name, upload_bytes, content_type = build_upload_payload(path)
        request_files.append(("files", (upload_name, upload_bytes, content_type)))

    create_resp = client.post(
        f"/api/v1/collections/{collection_id}/documents",
        files=request_files,
    )
    create_resp.raise_for_status()
    return [item["id"] for item in create_resp.json()["items"]]


def build_upload_payload(path: Path) -> tuple[str, bytes, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        compact = _compact_pdf_source(path)
        if compact:
            return (f"{path.stem}.md", compact.encode("utf-8"), "text/markdown")

    if suffix in {".md", ".txt", ".json", ".csv"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        compact = _compact_source_document(path, text)
        return (f"{path.stem}.md", compact.encode("utf-8"), "text/markdown")
    if suffix == ".pdf":
        compact = _compact_pdf_source(path)
        if compact:
            return (f"{path.stem}.md", compact.encode("utf-8"), "text/markdown")

    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return (path.name, path.read_bytes(), content_type)


def _compact_source_document(path: Path, raw_text: str) -> str:
    heading = f"# Imported from {path.name}\n\n"
    suffix = path.suffix.lower()

    if suffix == ".json":
        compact = _compact_json_source(path.name, raw_text)
        if compact:
            return heading + compact + "\n"
        try:
            formatted = "\n".join(_flatten_json_lines(json.loads(raw_text)))
        except json.JSONDecodeError:
            formatted = _clean_excerpt(raw_text, limit=12000)
        return f"{heading}{formatted}\n"

    if suffix == ".csv":
        compact = _compact_csv_source(path.name, raw_text)
        if compact:
            return heading + compact + "\n"
        return heading + "\n".join(_flatten_csv_lines(raw_text)) + "\n"

    compact = _compact_feed_text_source(path.name, raw_text)
    if compact:
        return heading + compact + "\n"
    return heading + _clean_excerpt(raw_text, limit=12000) + "\n"


def _compact_pdf_source(path: Path) -> str | None:
    try:
        reader = PdfReader(str(path))
    except Exception:
        return None

    pages: list[str] = []
    for page in reader.pages[: min(len(reader.pages), 12)]:
        try:
            extracted = page.extract_text() or ""
        except Exception:
            extracted = ""
        cleaned = _clean_excerpt(extracted, limit=1800)
        if cleaned:
            pages.append(cleaned)

    if not pages:
        return None

    raw_text = "\n\n".join(pages)
    heading = f"# Imported from {path.name}\n\n"
    compact = _compact_feed_text_source(path.name, raw_text)
    if compact:
        return heading + compact + "\n"
    return heading + _clean_excerpt(raw_text, limit=12000) + "\n"


def _compact_json_source(file_name: str, raw_text: str) -> str | None:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return _compact_json_entries_from_text(file_name, raw_text)

    if not isinstance(payload, dict):
        return None

    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        sections = payload.get("sections")
        if isinstance(sections, list) and sections:
            source = str(payload.get("source") or file_name).strip()
            lines = [f"Source: {source}"]
            if payload.get("url"):
                lines.append(f"URL: {payload['url']}")
            if payload.get("fetched_at"):
                lines.append(f"Fetched At: {payload['fetched_at']}")
            lines.append(f"Section Count: {len(sections)}")
            lines.append("")
            for index, section in enumerate(sections[:ACCEPTANCE_MAX_SOURCE_ITEMS], start=1):
                excerpt = _clean_excerpt(str(section), limit=220)
                if not excerpt:
                    continue
                lines.append(f"## Section {index}")
                lines.append(excerpt)
                lines.append("")
            return "\n".join(lines).strip()
        return None

    source = str(payload.get("source") or file_name).strip()
    lines = [f"Source: {source}"]
    if payload.get("url"):
        lines.append(f"URL: {payload['url']}")
    if payload.get("fetched_at"):
        lines.append(f"Fetched At: {payload['fetched_at']}")
    lines.append(f"Entry Count: {len(entries)}")
    lines.append("")

    rendered_count = 0
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            continue
        title = _clean_excerpt(str(entry.get("title") or "").strip(), limit=160)
        link = str(entry.get("link") or entry.get("url") or "").strip()
        published = str(entry.get("published") or entry.get("time") or "").strip()
        summary = _clean_excerpt(
            str(entry.get("summary") or entry.get("content") or entry.get("snippet") or "").strip(),
            limit=320,
        )
        if not title and not summary:
            continue
        lines.extend(_render_entry(index, title=title, link=link, published=published, summary=summary))
        rendered_count += 1
        if rendered_count >= ACCEPTANCE_MAX_SOURCE_ITEMS:
            break

    return "\n".join(lines).strip() if rendered_count else None


def _compact_json_entries_from_text(file_name: str, raw_text: str) -> str | None:
    pattern = re.compile(
        r'"title"\s*:\s*"(?P<title>[^"]+)"[\s\S]*?'
        r'"link"\s*:\s*"(?P<link>[^"]+)"[\s\S]*?'
        r'"published"\s*:\s*"(?P<published>[^"]+)"[\s\S]*?'
        r'"summary"\s*:\s*"(?P<summary>[^"]+)"',
        re.MULTILINE,
    )
    entries: list[dict[str, str]] = []
    for match in pattern.finditer(raw_text):
        entries.append(match.groupdict())
        if len(entries) >= ACCEPTANCE_MAX_SOURCE_ITEMS:
            break
    if not entries:
        return None

    lines = [f"Source: {file_name}", f"Entry Count: {len(entries)}", ""]
    for index, entry in enumerate(entries, start=1):
        lines.extend(
            _render_entry(
                index,
                title=_clean_excerpt(entry["title"], limit=160),
                link=entry["link"],
                published=entry["published"],
                summary=_clean_excerpt(bytes(entry["summary"], "utf-8").decode("unicode_escape"), limit=320),
            )
        )
    return "\n".join(lines).strip()


def _compact_csv_source(file_name: str, raw_csv: str) -> str | None:
    reader = csv.DictReader(raw_csv.splitlines())
    entries: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    source = file_name
    fetched_at = ""

    for row in reader:
        if not row:
            continue
        source = str(row.get("source") or source).strip() or source
        fetched_at = str(row.get("fetched_at") or fetched_at).strip() or fetched_at
        title = _clean_excerpt(str(row.get("title") or "").strip(), limit=160)
        link = str(row.get("url") or "").strip()
        published = str(row.get("published") or "").strip()
        summary = _clean_excerpt(str(row.get("content") or "").strip(), limit=280)
        key = (title, link)
        if key in seen or (not title and not summary):
            continue
        seen.add(key)
        entries.append((title, link, published, summary))
        if len(entries) >= ACCEPTANCE_MAX_SOURCE_ITEMS:
            break

    if not entries:
        return None

    lines = [f"Source: {source}"]
    if fetched_at:
        lines.append(f"Fetched At: {fetched_at}")
    lines.append(f"Entry Count: {len(entries)}")
    lines.append("")
    for index, (title, link, published, summary) in enumerate(entries, start=1):
        lines.extend(_render_entry(index, title=title, link=link, published=published, summary=summary))
    return "\n".join(lines).strip()


def _compact_feed_text_source(file_name: str, raw_text: str) -> str | None:
    if raw_text.count("RateLimitTriggeredError") >= 3 or raw_text.count('"status":42903') >= 3:
        return (
            f"Source: {file_name}\n"
            "Status: source crawl rate-limited during collection.\n"
            "Summary: the captured file mostly contains repeated 429 rate-limit responses rather than stable article body content."
        )

    source = file_name
    address = ""
    fetched_at = ""
    for line in raw_text.splitlines()[:20]:
        stripped = line.strip()
        if not stripped:
            continue
        if not source and stripped:
            source = stripped
        if stripped.startswith(("地址:", "URL:", "URL Source:")):
            address = stripped.split(":", 1)[-1].strip()
        elif stripped.startswith(("抓取时间:", "Fetched At:")):
            fetched_at = stripped.split(":", 1)[-1].strip()
        elif stripped.startswith("# "):
            source = stripped[2:].strip() or source

    entries = _extract_numbered_entries(raw_text)
    if not entries:
        return None

    lines = [f"Source: {source}"]
    if address:
        lines.append(f"URL: {address}")
    if fetched_at:
        lines.append(f"Fetched At: {fetched_at}")
    lines.append(f"Entry Count: {len(entries)}")
    lines.append("")
    for index, entry in enumerate(entries, start=1):
        lines.extend(
            _render_entry(
                index,
                title=_clean_excerpt(entry.get("title", ""), limit=160),
                link=entry.get("link", ""),
                published=entry.get("published", ""),
                summary=_clean_excerpt(entry.get("summary", ""), limit=320),
            )
        )
    return "\n".join(lines).strip()


def _compact_pdf_source(path: Path) -> str | None:
    try:
        from pypdf import PdfReader
    except Exception:
        return None

    try:
        reader = PdfReader(str(path))
    except Exception:
        return None

    lines = [f"Source: {path.name}", f"Page Count: {len(reader.pages)}", ""]
    rendered_pages = 0

    for index, page in enumerate(reader.pages[:8], start=1):
        text = _clean_excerpt(page.extract_text() or "", limit=1800)
        if not text:
            continue
        lines.append(f"## Page {index}")
        lines.append(text)
        lines.append("")
        rendered_pages += 1

    if not rendered_pages:
        return None

    return "\n".join(lines).strip()


def _extract_numbered_entries(raw_text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    patterns = [
        re.compile(
            r"(?ms)^###\s*\d+\.\s*(?P<title>.+?)\n- 发布时间:\s*(?P<published>.+?)\n- 链接:\s*(?P<link>.+?)\n\n(?P<summary>.+?)(?=\n###\s*\d+\.|\Z)"
        ),
        re.compile(
            r"(?ms)^\d+\.\s*(?P<title>.+?)\n发布时间:\s*(?P<published>.+?)\n链接:\s*(?P<link>.+?)\n摘要:\s*(?P<summary>.+?)(?=\n\d+\.\s|\n正文快照|\Z)"
        ),
    ]

    for pattern in patterns:
        for match in pattern.finditer(raw_text):
            title = match.group("title").strip()
            link = match.group("link").strip()
            published = match.group("published").strip()
            summary = match.group("summary").strip()
            key = (title, link)
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                {
                    "title": title,
                    "link": link,
                    "published": published,
                    "summary": summary,
                }
            )
            if len(entries) >= ACCEPTANCE_MAX_SOURCE_ITEMS:
                return entries
        if entries:
            return entries
    return entries


def _render_entry(index: int, *, title: str, link: str, published: str, summary: str) -> list[str]:
    lines = [f"## {index}. {title or 'Untitled'}"]
    if published:
        lines.append(f"- Published: {published}")
    if link:
        lines.append(f"- URL: {link}")
    if summary:
        lines.append("")
        lines.append(summary)
    lines.append("")
    return lines


def _clean_excerpt(text: str, *, limit: int) -> str:
    cleaned = text.replace("\r", "\n")
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", cleaned)
    cleaned = re.sub(r"\[[^\]]+\]\(([^)]+)\)", r"\1", cleaned)
    cleaned = re.sub(r"(?m)^\s*(Menu|登录|注册|订阅|搜索)\s*$", " ", cleaned)
    cleaned = re.sub(r"(?m)^={3,}\s*$", " ", cleaned)
    cleaned = re.sub(r"(?m)^-{3,}\s*$", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > limit:
        cleaned = cleaned[: limit - 1].rstrip() + "…"
    return cleaned


def _flatten_json_lines(value: Any, prefix: str = "") -> list[str]:
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            lines.extend(_flatten_json_lines(item, next_prefix))
    elif isinstance(value, list):
        for index, item in enumerate(value, start=1):
            next_prefix = f"{prefix}[{index}]"
            lines.extend(_flatten_json_lines(item, next_prefix))
    else:
        rendered = str(value).strip()
        if rendered:
            lines.append(f"- {prefix}: {rendered}")
    return lines or [json.dumps(value, ensure_ascii=False)]


def _flatten_csv_lines(raw_csv: str) -> list[str]:
    reader = csv.DictReader(raw_csv.splitlines())
    lines: list[str] = []
    for index, row in enumerate(reader, start=1):
        fields = [f"{key}={str(value).strip()}" for key, value in row.items() if str(value).strip()]
        if fields:
            lines.append(f"- Row {index}: " + "; ".join(fields))
    return lines or [raw_csv]


def wait_for_indexes_ready(client: httpx.Client, collection_id: str, document_ids: list[str]) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    started = time.time()
    last_debug_snapshot: dict[str, Any] = {}
    while True:
        collection = request_json_with_retry(
            client,
            "GET",
            f"/api/v1/collections/{collection_id}",
        )
        docs_payload = request_json_with_retry(
            client,
            "GET",
            f"/api/v1/collections/{collection_id}/documents",
            params={"page": 1, "page_size": 100, "sort_by": "created", "sort_order": "desc"},
        )
        docs = docs_payload["items"]

        docs_by_id = {item["id"]: item for item in docs}
        ready_docs = [
            docs_by_id[document_id]
            for document_id in document_ids
            if document_id in docs_by_id
        ]
        missing_document_ids = [
            document_id for document_id in document_ids if document_id not in docs_by_id
        ]
        pending_documents = [
            {
                "id": item["id"],
                "name": item.get("name"),
                "status": item.get("status"),
                "vector_index_status": item.get("vector_index_status"),
                "fulltext_index_status": item.get("fulltext_index_status"),
            }
            for item in ready_docs
            if not (
                item.get("vector_index_status") == "ACTIVE"
                and item.get("fulltext_index_status") == "ACTIVE"
            )
        ]
        documents_ready = all(
            item.get("vector_index_status") == "ACTIVE"
            and item.get("fulltext_index_status") == "ACTIVE"
            for item in ready_docs
        ) and not missing_document_ids
        graph_ready = collection.get("config", {}).get("graph_status") == "ready"

        last_debug_snapshot = {
            "graph_status": collection.get("config", {}).get("graph_status"),
            "missing_document_ids": missing_document_ids,
            "pending_documents": pending_documents[:8],
            "ready_doc_count": len(ready_docs),
            "expected_doc_count": len(document_ids),
        }

        if documents_ready and graph_ready:
            return collection, ready_docs, time.time() - started

        if time.time() - started > INDEX_BUDGET_SECONDS:
            raise TimeoutError(
                "Indexing exceeded the 4-minute acceptance budget "
                f"(graph_status={last_debug_snapshot.get('graph_status')}, "
                f"ready_docs={last_debug_snapshot.get('ready_doc_count')}/{last_debug_snapshot.get('expected_doc_count')}, "
                f"missing_docs={last_debug_snapshot.get('missing_document_ids')}, "
                f"pending_docs={last_debug_snapshot.get('pending_documents')})"
            )

        time.sleep(0.2)


def get_graph_counts(client: httpx.Client, collection_id: str) -> tuple[int, int]:
    graph = request_json_with_retry(
        client,
        "GET",
        f"/api/v1/collections/{collection_id}/graphs",
        params={"label": "*", "max_nodes": 5000, "max_depth": 3},
    )
    return len(graph.get("nodes") or []), len(graph.get("edges") or [])


def request_json_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    **kwargs,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(REQUEST_RETRY_COUNT):
        try:
            response = client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except (httpx.ReadError, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
            last_error = exc
            if attempt == REQUEST_RETRY_COUNT - 1:
                raise
            time.sleep(2)
    if last_error:
        raise last_error
    raise RuntimeError(f"Request failed without a concrete error: {method} {url}")


def ensure_default_agent_bot(client: httpx.Client, collection: dict[str, Any]) -> dict[str, Any]:
    bots_resp = client.get("/api/v1/bots")
    bots_resp.raise_for_status()
    bots = bots_resp.json()["items"]
    bot = next((item for item in bots if item.get("title") == "Default Agent Bot"), None)
    if not bot:
        raise RuntimeError("Default Agent Bot not found")

    update_resp = client.put(
        f"/api/v1/bots/{bot['id']}",
        json={
            "title": bot["title"],
            "description": bot.get("description"),
            "config": {
                "agent": {
                    "collections": [
                        {
                            "id": collection["id"],
                            "title": collection["title"],
                            "description": collection.get("description"),
                            "type": collection.get("type"),
                            "status": collection.get("status"),
                        }
                    ]
                },
                "flow": None,
            },
        },
    )
    update_resp.raise_for_status()
    return update_resp.json()


def create_chat(client: httpx.Client, bot_id: str) -> dict[str, Any]:
    response = client.post(f"/api/v1/bots/{bot_id}/chats")
    response.raise_for_status()
    return response.json()


async def send_agent_message(
    *,
    ws_url: str,
    cookie_header: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    headers = {"Cookie": cookie_header} if cookie_header else {}
    messages: list[dict[str, Any]] = []
    async with websockets.connect(ws_url, additional_headers=headers) as websocket:
        await websocket.send(json.dumps(payload, ensure_ascii=False))
        while True:
            raw = await asyncio.wait_for(websocket.recv(), timeout=120)
            message = json.loads(raw)
            messages.append(message)
            if message.get("type") == "stop":
                break
    return messages


def fetch_chat_history(client: httpx.Client, bot_id: str, chat_id: str) -> list[list[dict[str, Any]]]:
    response = client.get(f"/api/v1/bots/{bot_id}/chats/{chat_id}")
    response.raise_for_status()
    return response.json().get("history") or []


def get_last_ai_turn(history: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    for turn in reversed(history):
        if any(part.get("role") == "ai" for part in turn):
            return turn
    return []


def build_trace_rows(references: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def split_source_ids(value: Any) -> list[str]:
        if isinstance(value, list):
            result: list[str] = []
            for item in value:
                result.extend(split_source_ids(item))
            return result
        if not isinstance(value, str):
            return []
        return [item.strip() for item in value.replace("<SEP>", "|").split("|") if item.strip()]

    rows: list[dict[str, Any]] = []
    for index, reference in enumerate(references):
        metadata = reference.get("metadata") or {}
        recall_type = metadata.get("recall_type") or metadata.get("type")
        text = reference.get("text") or ""
        if (
            recall_type == "graph_search"
            and not metadata.get("document_id")
            and not metadata.get("md_source_map")
            and not metadata.get("pdf_source_map")
            and text.strip().startswith("Entities(KG):")
        ):
            continue
        rows.append(
            {
                "source_row_id": metadata.get("source_row_id") or f"row_{index}",
                "text": text,
                "snippet": text[:180],
                "document_id": metadata.get("document_id") or metadata.get("doc_id"),
                "document_name": metadata.get("document_name") or metadata.get("source"),
                "preview_title": metadata.get("preview_title") or metadata.get("document_name") or metadata.get("source"),
                "page_idx": metadata.get("page_idx"),
                "section_label": (metadata.get("titles") or [None])[0],
                "chunk_ids": [
                    *split_source_ids(metadata.get("chunk_ids")),
                    *split_source_ids(metadata.get("chunk_id")),
                    *split_source_ids(metadata.get("source_chunk_id")),
                    *split_source_ids(metadata.get("source_id")),
                ],
                "paragraph_precise": bool(metadata.get("paragraph_precise")),
                "md_source_map": metadata.get("md_source_map"),
                "pdf_source_map": metadata.get("pdf_source_map") or [],
            }
        )
    return rows


def validate_mode_output(
    *,
    mode: str,
    answer: str,
    references: list[dict[str, Any]],
    trace_support: dict[str, Any] | None,
) -> ModeResult:
    notes: list[str] = []
    passed = True
    answer_lower = answer.lower()

    if not answer.strip():
        passed = False
        notes.append("answer is empty")
    if not references:
        passed = False
        notes.append("references missing")

    if mode == "default":
        if "```mermaid" not in answer_lower:
            passed = False
            notes.append("default mode missing mermaid topology/process graph")
    elif mode == "time":
        if "gantt" not in answer_lower:
            passed = False
            notes.append("time mode missing gantt chart")
    elif mode == "space":
        if "```mermaid" not in answer_lower or "graph td" not in answer_lower:
            passed = False
            notes.append("space mode missing default-style graph TD topology graph")
    elif mode == "entity":
        if not trace_support or trace_support.get("graph", {}).get("is_empty"):
            passed = False
            notes.append("entity mode missing answer-scoped knowledge subgraph")

    if trace_support and mode == "entity":
        graph = trace_support.get("graph", {})
        if graph.get("is_empty"):
            passed = False
            notes.append("trace-support graph is empty")

    return ModeResult(
        mode=mode,
        query="",
        answer=answer,
        references=references,
        trace_support=trace_support,
        passed=passed,
        notes=notes,
    )


def run_mode_validation(
    client: httpx.Client,
    *,
    local_web_port: int,
    local_api_port: int,
    bot: dict[str, Any],
    collection: dict[str, Any],
    mode: str,
    query: str,
) -> ModeResult:
    chat = create_chat(client, bot["id"])
    ws_url = f"ws://127.0.0.1:{local_api_port}/api/v1/bots/{bot['id']}/chats/{chat['id']}/connect"
    cookie_header = "; ".join([f"{k}={v}" for k, v in client.cookies.items()])
    payload = {
        "query": query,
        "collections": [
            {
                "id": collection["id"],
                "title": collection["title"],
                "description": collection.get("description"),
                "type": collection.get("type"),
                "status": collection.get("status"),
            }
        ],
        "completion": collection["config"]["completion"],
        "web_search_enabled": False,
        "language": "zh-CN",
        "files": [],
        "trace_mode": mode,
    }
    asyncio.run(send_agent_message(ws_url=ws_url, cookie_header=cookie_header, payload=payload))

    history = fetch_chat_history(client, bot["id"], chat["id"])
    last_ai_turn = get_last_ai_turn(history)
    answer_parts = [
        part.get("data") or ""
        for part in last_ai_turn
        if part.get("role") == "ai" and part.get("type") in {"message", "error"}
    ]
    refs_part = next(
        (
            part
            for part in reversed(last_ai_turn)
            if isinstance(part.get("references"), list) and part.get("references")
        ),
        None,
    )
    answer = "\n\n".join(answer_parts).strip()
    references = refs_part.get("references") if refs_part else []
    rows = build_trace_rows(references)
    trace_support = None
    if rows:
        trace_resp = client.post(
            f"/api/v1/collections/{collection['id']}/trace-support",
            json={
                "trace_mode": mode,
                "question": query,
                "answer": answer,
                "references": rows,
                "max_conclusions": 4,
                "max_nodes": 18,
            },
        )
        trace_resp.raise_for_status()
        trace_support = trace_resp.json()

    result = validate_mode_output(
        mode=mode,
        answer=answer,
        references=references,
        trace_support=trace_support,
    )
    result.query = query
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run recurring triple-trace acceptance checks.")
    parser.add_argument("--skip-remote-deploy", action="store_true")
    args = parser.parse_args()

    if not IW_DOCS_DIR.exists():
        raise FileNotFoundError(f"Acceptance dataset not found: {IW_DOCS_DIR}")

    if not args.skip_remote_deploy:
        ensure_remote_stack()

    with tunnel_context() as (local_web_port, local_api_port):
        base_url = f"http://127.0.0.1:{local_api_port}"
        wait_for_api_ready(base_url)
        client, user = register_and_login(base_url)
        acceptance_started = time.time()
        collection: dict[str, Any] | None = None
        collection_ready: dict[str, Any] | None = None
        document_ids: list[str] = []
        ready_docs: list[dict[str, Any]] = []
        duration = 0.0
        node_count = 0
        edge_count = 0
        mode_results: list[ModeResult] = []
        failures: list[str] = []
        try:
            collection = create_collection(client)
            document_ids = upload_all_documents(client, collection["id"])
            collection_ready, ready_docs, duration = wait_for_indexes_ready(
                client,
                collection["id"],
                document_ids,
            )

            node_count, edge_count = get_graph_counts(client, collection["id"])

            bot = ensure_default_agent_bot(client, collection)
            mode_results = [
                run_mode_validation(
                    client,
                    local_web_port=local_web_port,
                    local_api_port=local_api_port,
                    bot=bot,
                    collection=collection_ready,
                    mode="default",
                    query="请概括该知识库中的主要事件，并给出流程拓扑图。",
                ),
                run_mode_validation(
                    client,
                    local_web_port=local_web_port,
                    local_api_port=local_api_port,
                    bot=bot,
                    collection=collection_ready,
                    mode="time",
                    query="3月发生了什么？",
                ),
                run_mode_validation(
                    client,
                    local_web_port=local_web_port,
                    local_api_port=local_api_port,
                    bot=bot,
                    collection=collection_ready,
                    mode="space",
                    query="阿布扎比发生了什么？",
                ),
                run_mode_validation(
                    client,
                    local_web_port=local_web_port,
                    local_api_port=local_api_port,
                    bot=bot,
                    collection=collection_ready,
                    mode="entity",
                    query="请基于当前知识库列出伊朗相关的关键参与方和关系，并给出 Mermaid 知识图谱子图和引用。",
                ),
            ]
        except Exception as exc:
            duration = time.time() - acceptance_started
            failures.append(str(exc))
            if collection:
                try:
                    collection_ready = request_json_with_retry(
                        client,
                        "GET",
                        f"/api/v1/collections/{collection['id']}",
                    )
                except Exception:
                    collection_ready = None
                try:
                    docs_payload = request_json_with_retry(
                        client,
                        "GET",
                        f"/api/v1/collections/{collection['id']}/documents",
                        params={"page": 1, "page_size": 100, "sort_by": "created", "sort_order": "desc"},
                    )
                    ready_docs = docs_payload.get("items") or []
                except Exception:
                    ready_docs = []
                try:
                    node_count, edge_count = get_graph_counts(client, collection["id"])
                except Exception:
                    node_count, edge_count = 0, 0
        finally:
            if duration > INDEX_BUDGET_SECONDS:
                failures.append(f"index budget exceeded: {duration:.1f}s")
            if node_count and node_count < MIN_GRAPH_NODES:
                failures.append(f"graph node count too low: {node_count}")
            if edge_count and edge_count < MIN_GRAPH_EDGES:
                failures.append(f"graph edge count too low: {edge_count}")
            for result in mode_results:
                if not result.passed:
                    failures.append(f"{result.mode} mode failed: {'; '.join(result.notes)}")

            report = {
                "user": user,
                "local_urls": {
                    "web": f"http://127.0.0.1:{local_web_port}/",
                    "api": f"http://127.0.0.1:{local_api_port}/docs",
                },
                "collection": {
                    "id": (collection_ready or collection or {}).get("id") if (collection_ready or collection) else None,
                    "graph_status": (collection_ready or {}).get("config", {}).get("graph_status") if collection_ready else None,
                    "active_graph_id": (collection_ready or {}).get("config", {}).get("active_graph_id") if collection_ready else None,
                },
                "documents": {
                    "requested_count": len(document_ids),
                    "observed_count": len(ready_docs),
                    "duration_seconds": round(duration, 2),
                },
                "graph_counts": {
                    "nodes": node_count,
                    "edges": edge_count,
                },
                "mode_results": [
                    {
                        "mode": result.mode,
                        "query": result.query,
                        "passed": result.passed,
                        "notes": result.notes,
                    }
                    for result in mode_results
                ],
                "passed": not failures,
                "failures": failures,
            }
            print(json.dumps(report, ensure_ascii=False, indent=2))
            client.close()
            return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
