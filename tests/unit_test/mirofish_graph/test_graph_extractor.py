import sys
import types

config_stub = types.ModuleType("aperag.config")
config_stub.settings = types.SimpleNamespace(
    mirofish_graph_extraction_max_retries=1,
    mirofish_graph_extraction_max_tokens=1024,
)
sys.modules.setdefault("aperag.config", config_stub)

from aperag.mirofish_graph.graph_extractor import ChunkGraphExtractor


class _FakeLLMClient:
    def __init__(self, result):
        self.result = result

    def chat_json(self, **kwargs):  # noqa: ARG002
        return self.result


def test_graph_extractor_preserves_supported_trace_attributes_only():
    extractor = ChunkGraphExtractor(
        _FakeLLMClient(
            {
                "entities": [
                    {
                        "name": "阿布扎比",
                        "aliases": ["阿布扎比", "Abu Dhabi"],
                        "type": "Location",
                        "summary": "地点",
                        "attributes": {
                            "place_normalized": "Abu Dhabi",
                            "place_aliases": ["Abu Dhabi", "Abu Dhabi"],
                            "noise": {"bad": "value"},
                        },
                    }
                ],
                "relations": [
                    {
                        "source_name": "联合演训",
                        "source_type": "Activity",
                        "target_name": "阿布扎比",
                        "target_type": "Location",
                        "type": "OCCURS_IN",
                        "fact": "联合演训在阿布扎比举行",
                        "evidence": "2026年3月，阿布扎比举行联合演训。",
                        "confidence": 0.92,
                        "attributes": {
                            "time": "2026年3月",
                            "place": "阿布扎比",
                            "unsupported": {"nested": True},
                        },
                    }
                ],
            }
        )
    )

    result = extractor.extract(
        chunk_text="2026年3月，阿布扎比举行联合演训。",
        ontology={
            "entity_types": [{"name": "Location"}, {"name": "Activity"}],
            "edge_types": [{"name": "OCCURS_IN"}],
        },
        document_name="briefing.md",
        chunk_index=0,
    )

    assert result["entities"][0]["attributes"]["place_normalized"] == "Abu Dhabi"
    assert result["entities"][0]["attributes"]["place_aliases"] == ["Abu Dhabi"]
    assert "noise" not in result["entities"][0]["attributes"]
    assert result["relations"][0]["attributes"]["time"] == "2026年3月"
    assert result["relations"][0]["attributes"]["place"] == "阿布扎比"
    assert "unsupported" not in result["relations"][0]["attributes"]
