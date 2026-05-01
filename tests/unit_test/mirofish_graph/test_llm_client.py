from aperag.mirofish_graph.llm_client import MiroFishLLMClient


class _StubLLMClient(MiroFishLLMClient):
    def __init__(self, response_text: str):
        super().__init__(api_key="test-key", base_url="http://example.com", model="test-model")
        self._response_text = response_text

    def chat(self, **kwargs):  # noqa: ARG002
        return self._response_text


def test_chat_json_repairs_truncated_graph_payload():
    client = _StubLLMClient(
        """
        {
          "entities": [
            {"name": "伊朗", "type": "Location", "summary": "国家", "attributes": {}},
            {"name": "阿布扎比", "type": "Location", "summary": "城市", "attributes": {}}
          ],
          "relations": [
            {
              "source_name": "联合演训",
              "source_type": "Activity",
              "target_name": "阿布扎比",
              "target_type": "Location",
              "type": "OCCURS_IN",
              "fact": "联合演训发生在阿布扎比",
              "evidence": "3月，阿布扎比举行联合演训",
              "confidence": 0.9,
              "attributes": {}
            },
            {
              "source_name": "未完成"
        }
        """.strip()
    )

    result = client.chat_json(messages=[{"role": "user", "content": "extract"}])

    assert [entity["name"] for entity in result["entities"]] == ["伊朗", "阿布扎比"]
    assert len(result["relations"]) == 1
    assert result["relations"][0]["type"] == "OCCURS_IN"
