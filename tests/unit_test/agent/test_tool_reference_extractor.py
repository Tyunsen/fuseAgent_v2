import json
import sys
import types
from pathlib import Path

agent_pkg = types.ModuleType("aperag.agent")
agent_pkg.__path__ = [str(Path(__file__).resolve().parents[3] / "aperag" / "agent")]
sys.modules.setdefault("aperag.agent", agent_pkg)

from aperag.agent.tool_reference_extractor import extract_tool_call_references


class _FakeMemory:
    def __init__(self, messages):
        self._messages = messages

    def get(self):
        return self._messages


def test_extract_tool_call_references_emits_one_row_per_search_item():
    tool_result = {
        "items": [
            {
                "score": 0.91,
                "content": "Ali Khamenei died in the opening phase of the war.",
                "source": "iran-leadership.pdf",
                "recall_type": "vector_search",
                "metadata": {
                    "source": "iran-leadership.pdf",
                    "document_id": "doc_001",
                    "collection_id": "col_001",
                    "page_idx": 2,
                    "md_source_map": [10, 20],
                    "pdf_source_map": [{"page_idx": 2, "bbox": [0, 0, 100, 120]}],
                    "titles": ["Leadership changes"],
                    "source_id": "chunk_1<SEP>chunk_2",
                },
            },
            {
                "score": 0.73,
                "content": "Mojtaba Khamenei became the new supreme leader.",
                "source": "iran-leadership.pdf",
                "recall_type": "graph_search",
                "metadata": {
                    "source": "iran-leadership.pdf",
                    "document_id": "doc_001",
                    "collection_id": "col_001",
                    "pdf_source_map": [{"page_idx": 4, "bbox": [0, 0, 100, 120]}],
                },
            },
        ]
    }
    memory = _FakeMemory(
        [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "aperag_search_collection",
                            "arguments": json.dumps(
                                {
                                    "collection_id": "col_001",
                                    "query": "Who leads Iran?",
                                }
                            ),
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": [{"text": json.dumps(tool_result, ensure_ascii=False)}],
            },
        ]
    )

    references = extract_tool_call_references(memory)

    assert len(references) == 2
    assert references[0]["score"] == 0.91
    assert references[0]["metadata"]["collection_id"] == "col_001"
    assert references[0]["metadata"]["document_name"] == "iran-leadership.pdf"
    assert references[0]["metadata"]["chunk_ids"] == ["chunk_1", "chunk_2"]
    assert references[0]["metadata"]["md_source_map"] == [10, 20]
    assert references[0]["metadata"]["pdf_source_map"] == [{"page_idx": 2, "bbox": [0, 0, 100, 120]}]
    assert references[0]["metadata"]["titles"] == ["Leadership changes"]
    assert references[0]["metadata"]["paragraph_precise"] is True
    assert references[0]["metadata"]["preview_title"].endswith("p.3")
    assert references[1]["metadata"]["paragraph_precise"] is False
    assert references[1]["metadata"]["page_idx"] == 4
    assert references[1]["metadata"]["preview_title"].endswith("p.5")
    assert references[1]["metadata"]["source_row_id"].startswith("search_collection:")
