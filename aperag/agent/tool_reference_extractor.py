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

"""Tool call reference extractor for agent conversations."""

import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional

from .exceptions import (
    JSONParsingError,
    ToolReferenceExtractionError,
    handle_agent_error,
    safe_json_parse,
)

logger = logging.getLogger(__name__)


SOURCE_ID_SPLIT_PATTERN = re.compile(r"(?:<SEP>|\|)")


@handle_agent_error("tool_call_reference_extraction", default_return=[], reraise=False)
def extract_tool_call_references(memory) -> List[Dict[str, Any]]:
    """
    Extract tool call results from MCP agent history and format as references.

    Args:
        memory: SimpleMemory instance containing agent history

    Returns:
        List of reference dictionaries in the format expected by llm.py
    """
    references = []

    # Get history from memory
    history_messages = memory.get() if hasattr(memory, "get") else []
    if not history_messages:
        logger.debug("No history messages found in memory")
        return references

    for message in history_messages:
        # Check if message has tool calls (message is a dict)
        if isinstance(message, dict) and message.get("role") == "assistant" and message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                try:
                    # Debug: log the actual structure
                    logger.debug(f"Tool call structure: {tool_call}, type: {type(tool_call)}")

                    # Process tool call information
                    # Handle different tool call structures (dict vs object)
                    tool_name = "unknown_tool"
                    tool_args = "{}"
                    tool_call_id = ""

                    # Handle OpenAI ChatCompletionMessageToolCall objects
                    if hasattr(tool_call, "id"):
                        tool_call_id = tool_call.id
                        if hasattr(tool_call, "function"):
                            tool_name = (
                                tool_call.function.name if hasattr(tool_call.function, "name") else "unknown_tool"
                            )
                            tool_args = (
                                tool_call.function.arguments if hasattr(tool_call.function, "arguments") else "{}"
                            )
                    # Handle dictionary format
                    elif isinstance(tool_call, dict):
                        tool_call_id = tool_call.get("id", "")
                        if "function" in tool_call:
                            tool_name = tool_call["function"].get("name", "unknown_tool")
                            tool_args = tool_call["function"].get("arguments", "{}")
                        elif "name" in tool_call:
                            tool_name = tool_call.get("name", "unknown_tool")
                            tool_args = tool_call.get("arguments", "{}")
                        elif "type" in tool_call and tool_call["type"] == "function":
                            tool_name = tool_call.get("function", {}).get("name", "unknown_tool")
                            tool_args = tool_call.get("function", {}).get("arguments", "{}")

                    logger.debug(
                        f"Extracted tool_name: {tool_name}, tool_args: {tool_args}, tool_call_id: {tool_call_id}"
                    )

                    # Parse tool arguments using safe parsing
                    try:
                        args_dict = (
                            safe_json_parse(tool_args, f"tool_args_{tool_name}")
                            if isinstance(tool_args, str)
                            else tool_args
                        )
                    except JSONParsingError:
                        logger.warning(f"Failed to parse tool arguments for {tool_name}, using raw args")
                        args_dict = {"raw_args": tool_args}

                    # Find corresponding tool result message
                    tool_result = _find_tool_result(history_messages, tool_call_id)

                    if tool_result:
                        # Format reference based on tool type
                        ref = None
                        try:
                            if tool_name == "aperag_search_collection":
                                ref = _format_search_reference(tool_result, args_dict)
                            elif tool_name == "aperag_search_chat_files":
                                ref = _format_search_chat_files_reference(tool_result, args_dict)
                            elif tool_name == "aperag_list_collections":
                                ref = _format_list_reference(tool_result, args_dict)
                            elif tool_name == "aperag_web_search":
                                ref = _format_web_search_reference(tool_result, args_dict)
                            elif tool_name == "aperag_web_read":
                                ref = _format_web_read_reference(tool_result, args_dict)
                            else:
                                # Generic tool result reference
                                ref = _format_generic_reference(tool_name, tool_result, args_dict)

                            if isinstance(ref, list):
                                references.extend([item for item in ref if item])
                            elif ref:
                                references.append(ref)

                        except (JSONParsingError, ToolReferenceExtractionError) as e:
                            logger.warning(f"Failed to format reference for tool {tool_name}: {e}")
                            continue

                except Exception as e:
                    logger.warning(f"Error processing individual tool call: {e}")
                    continue

    return references


def _find_tool_result(messages, tool_call_id: str) -> Optional[str]:
    """Find the tool result message for a given tool call ID"""
    for message in messages:
        if isinstance(message, dict) and message.get("role") == "tool" and message.get("tool_call_id") == tool_call_id:
            content = message.get("content", "")
            logger.debug(f"Found tool result for {tool_call_id}: {type(content)} - {content}")

            # Handle both string and list content
            if isinstance(content, list):
                return json.dumps(content)
            return content
    return None


def _parse_tool_result_payload(tool_result: str) -> Any:
    """Parse tool result - handle both string and already parsed data."""
    if isinstance(tool_result, str):
        try:
            result_data = json.loads(tool_result)
        except json.JSONDecodeError:
            result_data = {"raw_result": tool_result}
    else:
        result_data = tool_result

    # Handle array format where data is in first element's text field
    if isinstance(result_data, list) and len(result_data) > 0:
        first_item = result_data[0]
        if isinstance(first_item, dict) and "text" in first_item:
            try:
                result_data = json.loads(first_item["text"])
            except json.JSONDecodeError as exc:
                raise ToolReferenceExtractionError(f"Failed to parse text field as JSON: {first_item['text']}") from exc

    return result_data


def _split_source_ids(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        result: List[str] = []
        for item in value:
            result.extend(_split_source_ids(item))
        return result

    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in SOURCE_ID_SPLIT_PATTERN.split(text) if part.strip()]


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _extract_document_id(metadata: Dict[str, Any]) -> str:
    return str(
        metadata.get("document_id")
        or metadata.get("doc_id")
        or metadata.get("full_doc_id")
        or ""
    ).strip()


def _extract_chunk_ids(metadata: Dict[str, Any]) -> List[str]:
    chunk_ids = []
    chunk_ids.extend(_split_source_ids(metadata.get("chunk_ids")))
    chunk_ids.extend(_split_source_ids(metadata.get("chunk_id")))
    chunk_ids.extend(_split_source_ids(metadata.get("source_chunk_id")))
    chunk_ids.extend(_split_source_ids(metadata.get("source_id")))
    return _dedupe_preserve_order(chunk_ids)


def _to_optional_int(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _normalize_md_source_map(value: Any) -> Optional[List[int]]:
    if not isinstance(value, list) or len(value) < 2:
        return None

    start = _to_optional_int(value[0])
    end = _to_optional_int(value[1])
    if start is None or end is None:
        return None

    if end < start:
        start, end = end, start
    return [start, end]


def _normalize_pdf_source_map(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []

    normalized: List[Dict[str, Any]] = []
    seen = set()
    for item in value:
        if not isinstance(item, dict):
            continue

        page_idx = _to_optional_int(item.get("page_idx"))
        bbox = item.get("bbox")
        para_type = item.get("para_type")
        normalized_item: Dict[str, Any] = {}

        if page_idx is not None:
            normalized_item["page_idx"] = page_idx
        if isinstance(bbox, list):
            normalized_item["bbox"] = bbox
        if para_type is not None:
            normalized_item["para_type"] = str(para_type)

        if not normalized_item:
            continue

        dedupe_key = json.dumps(normalized_item, ensure_ascii=False, sort_keys=True)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(normalized_item)

    return normalized


def _extract_titles(metadata: Dict[str, Any]) -> List[str]:
    titles = metadata.get("titles")
    if not isinstance(titles, list):
        return []
    return [str(item).strip() for item in titles if str(item).strip()]


def _resolve_page_idx(metadata: Dict[str, Any], pdf_source_map: List[Dict[str, Any]]) -> Optional[int]:
    page_idx = _to_optional_int(metadata.get("page_idx"))
    if page_idx is not None:
        return page_idx
    for item in pdf_source_map:
        candidate = _to_optional_int(item.get("page_idx"))
        if candidate is not None:
            return candidate
    return None


def _build_preview_title(document_name: str, page_idx: Any) -> str:
    if page_idx is None:
        return document_name or "Untitled"
    try:
        page_number = int(page_idx) + 1
    except (TypeError, ValueError):
        return document_name or "Untitled"
    if document_name:
        return f"{document_name} - p.{page_number}"
    return f"Page {page_number}"


def _make_source_row_id(scope_type: str, scope_id: str, document_id: str, page_idx: Any, index: int, text: str) -> str:
    digest_input = "|".join(
        [
            scope_type,
            scope_id or "unknown",
            document_id or "unknown",
            str(page_idx if page_idx is not None else "na"),
            str(index),
            (text or "")[:160],
        ]
    )
    digest = hashlib.md5(digest_input.encode("utf-8")).hexdigest()[:12]
    return f"{scope_type}:{digest}"


def _build_search_item_reference(
    *,
    item: Dict[str, Any],
    query: str,
    scope_type: str,
    scope_key: str,
    scope_value: str,
    index: int,
) -> Dict[str, Any]:
    metadata = dict(item.get("metadata") or {})
    content = str(item.get("content") or "").strip()
    recall_type = str(item.get("recall_type") or metadata.get("recall_type") or "").strip()
    md_source_map = _normalize_md_source_map(metadata.get("md_source_map"))
    pdf_source_map = _normalize_pdf_source_map(metadata.get("pdf_source_map"))
    titles = _extract_titles(metadata)
    document_name = (
        str(
            item.get("source")
            or metadata.get("source")
            or metadata.get("document_name")
            or metadata.get("file_path")
            or "Untitled"
        ).strip()
        or "Untitled"
    )
    document_id = _extract_document_id(metadata)
    page_idx = _resolve_page_idx(metadata, pdf_source_map)
    chunk_ids = _extract_chunk_ids(metadata)
    paragraph_precise = bool(content) and recall_type not in {"graph_search"}
    source_row_id = _make_source_row_id(scope_type, scope_value, document_id, page_idx, index, content)
    preview_title = _build_preview_title(document_name, page_idx)

    reference_metadata = {
        **metadata,
        "type": scope_type,
        scope_key: scope_value,
        "query": query,
        "document_id": document_id or None,
        "document_name": document_name,
        "page_idx": page_idx,
        "recall_type": recall_type,
        "chunk_ids": chunk_ids,
        "md_source_map": md_source_map,
        "pdf_source_map": pdf_source_map,
        "titles": titles,
        "paragraph_precise": paragraph_precise,
        "source_row_id": source_row_id,
        "preview_title": preview_title,
    }

    return {
        "text": content,
        "metadata": reference_metadata,
        "score": item.get("score") or 1.0,
    }


def _format_search_item_references(
    *,
    tool_result: str,
    args: Dict[str, Any],
    scope_type: str,
    scope_key: str,
    scope_value: str,
) -> List[Dict[str, Any]]:
    result_data = _parse_tool_result_payload(tool_result)
    logger.debug("%s reference result_data: %s", scope_type, result_data)
    query = str(args.get("query", "") or "")
    items = result_data.get("items") if isinstance(result_data, dict) else None
    if not items:
        return []

    return [
        _build_search_item_reference(
            item=item,
            query=query,
            scope_type=scope_type,
            scope_key=scope_key,
            scope_value=scope_value,
            index=index,
        )
        for index, item in enumerate(items)
        if isinstance(item, dict)
    ]


def _format_search_reference(tool_result: str, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format search_collection tool result as reference"""
    try:
        collection_id = args.get("collection_id", "unknown")
        return _format_search_item_references(
            tool_result=tool_result,
            args=args,
            scope_type="search_collection",
            scope_key="collection_id",
            scope_value=str(collection_id),
        )

    except Exception as e:
        logger.error(f"Error formatting search reference: {e}")
        return []


def _format_search_chat_files_reference(tool_result: str, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format search_chat_files tool result as reference"""
    try:
        chat_id = args.get("chat_id", "unknown")
        return _format_search_item_references(
            tool_result=tool_result,
            args=args,
            scope_type="search_chat_files",
            scope_key="chat_id",
            scope_value=str(chat_id),
        )

    except Exception as e:
        logger.error(f"Error formatting search chat files reference: {e}")
        return []


def _format_list_reference(tool_result: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Format list_collections tool result as reference"""
    try:
        # Parse tool result - handle both string and already parsed data
        if isinstance(tool_result, str):
            try:
                result_data = json.loads(tool_result)
            except json.JSONDecodeError:
                result_data = {"raw_result": tool_result}
        else:
            result_data = tool_result

        logger.debug(f"List reference result_data: {result_data}")

        # Handle array format where data is in first element's text field
        if isinstance(result_data, list) and len(result_data) > 0:
            first_item = result_data[0]
            if isinstance(first_item, dict) and "text" in first_item:
                try:
                    # Parse the text field as JSON
                    text_data = json.loads(first_item["text"])
                    result_data = text_data
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse text field as JSON: {first_item['text']}")
                    return None

        # Look for items field (which contains collections)
        if "items" in result_data:
            collections = result_data["items"]
            text = "Available Collections:\n"
            for collection in collections:
                title = collection.get("title", collection.get("name", "Unknown"))
                description = collection.get("description", "No description")
                collection_id = collection.get("id", "Unknown ID")
                status = collection.get("status", "Unknown")

                text += f"- {title} (ID: {collection_id})\n"
                text += f"  Status: {status}\n"
                if description:
                    text += f"  Description: {description}\n"
                text += "\n"

            return {
                "text": text.strip(),
                "metadata": {"type": "list_collections", "collection_count": len(collections)},
                "score": 1.0,
            }

        return None

    except Exception as e:
        logger.error(f"Error formatting list reference: {e}")
        return None


def _format_web_search_reference(tool_result: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Format web_search tool result as reference"""
    try:
        # Parse tool result - handle both string and already parsed data
        if isinstance(tool_result, str):
            try:
                result_data = json.loads(tool_result)
            except json.JSONDecodeError:
                result_data = {"raw_result": tool_result}
        else:
            result_data = tool_result

        logger.debug(f"Web search reference result_data: {result_data}")

        # Handle array format where data is in first element's text field
        if isinstance(result_data, list) and len(result_data) > 0:
            first_item = result_data[0]
            if isinstance(first_item, dict) and "text" in first_item:
                try:
                    # Parse the text field as JSON
                    text_data = json.loads(first_item["text"])
                    result_data = text_data
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse text field as JSON: {first_item['text']}")
                    return None

        query = args.get("query", "")

        if "results" in result_data:
            results = result_data["results"]
            if results:
                combined_text = f"Web Search Results for: {query}\n\n"

                for result in results:
                    title = result.get("title", "No title")
                    url = result.get("url", "No URL")
                    snippet = result.get("snippet", "")

                    combined_text += f"Title: {title}\n"
                    combined_text += f"URL: {url}\n"
                    combined_text += f"Snippet: {snippet}\n\n"

                return {
                    "text": combined_text.strip(),
                    "metadata": {"type": "web_search", "query": query, "result_count": len(results)},
                    "score": 1.0,
                }

        return None

    except Exception as e:
        logger.error(f"Error formatting web search reference: {e}")
        return None


def _format_web_read_reference(tool_result: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Format web_read tool result as reference"""
    try:
        # Parse tool result - handle both string and already parsed data
        if isinstance(tool_result, str):
            try:
                result_data = json.loads(tool_result)
            except json.JSONDecodeError:
                result_data = {"raw_result": tool_result}
        else:
            result_data = tool_result

        logger.debug(f"Web read reference result_data: {result_data}")

        # Handle array format where data is in first element's text field
        if isinstance(result_data, list) and len(result_data) > 0:
            first_item = result_data[0]
            if isinstance(first_item, dict) and "text" in first_item:
                try:
                    # Parse the text field as JSON
                    text_data = json.loads(first_item["text"])
                    result_data = text_data
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse text field as JSON: {first_item['text']}")
                    return None

        urls = args.get("url_list", [])

        if "results" in result_data:
            results = result_data["results"]
            if results:
                combined_text = "Web Page Content:\n\n"

                for result in results:
                    url = result.get("url", "No URL")
                    title = result.get("title", "No title")
                    content = result.get("content", "")

                    combined_text += f"URL: {url}\n"
                    combined_text += f"Title: {title}\n"
                    combined_text += f"Content: {content}\n\n"

                return {
                    "text": combined_text.strip(),
                    "metadata": {"type": "web_read", "urls": urls, "result_count": len(results)},
                    "score": 1.0,
                }

        return None

    except Exception as e:
        logger.error(f"Error formatting web read reference: {e}")
        return None


def _format_generic_reference(tool_name: str, tool_result: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Format generic tool result as reference"""
    try:
        # Parse the tool result to handle array format
        parsed_result = tool_result
        if isinstance(tool_result, str):
            try:
                parsed_result = json.loads(tool_result)
            except json.JSONDecodeError:
                parsed_result = tool_result

        # Handle array format where data is in first element's text field
        if isinstance(parsed_result, list) and len(parsed_result) > 0:
            first_item = parsed_result[0]
            if isinstance(first_item, dict) and "text" in first_item:
                try:
                    # Parse the text field as JSON
                    text_data = json.loads(first_item["text"])
                    parsed_result = text_data
                except json.JSONDecodeError:
                    # If parsing fails, use the original text
                    parsed_result = first_item["text"]

        # For generic tools, create a simple reference
        text = f"Tool: {tool_name}\n"
        if args:
            text += f"Arguments: {json.dumps(args, indent=2)}\n"

        # Handle both string and non-string results
        if isinstance(parsed_result, str):
            text += f"Result: {parsed_result}"
        else:
            text += f"Result: {json.dumps(parsed_result, indent=2)}"

        return {
            "text": text,
            "metadata": {"type": "tool_result", "tool_name": tool_name, "args": args},
            "score": 1.0,
        }

    except Exception as e:
        logger.error(f"Error formatting generic reference: {e}")
        return None
