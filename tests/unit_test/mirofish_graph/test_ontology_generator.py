from aperag.mirofish_graph.ontology_generator import OntologyGenerator


class _FakeLLMClient:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def chat_json(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


def test_ontology_generator_keeps_base_types_and_caps_supplemental_types():
    extra_entities = [
        {
            "name": f"special type {index}",
            "description": "supplemental entity",
            "attributes": [],
            "examples": [],
        }
        for index in range(20)
    ]
    extra_edges = [
        {
            "name": f"supports relation {index}",
            "description": "supplemental relation",
            "source_targets": [],
            "attributes": [],
        }
        for index in range(20)
    ]
    llm_client = _FakeLLMClient(
        {
            "supplemental_entity_types": [
                {"name": "military unit", "description": "unit", "attributes": [], "examples": []},
                *extra_entities,
            ],
            "supplemental_edge_types": [
                {
                    "name": "occurs at",
                    "description": "happens in a context",
                    "source_targets": [{"source": "Activity", "target": "Location"}],
                    "attributes": [],
                },
                *extra_edges,
            ],
            "analysis_summary": "broad military collection",
        }
    )

    generator = OntologyGenerator(llm_client)
    ontology = generator.generate(
        document_texts=["Alpha document"],
        simulation_requirement="Track operational activity",
        additional_context=None,
    )

    entity_names = [item["name"] for item in ontology["entity_types"]]
    edge_names = [item["name"] for item in ontology["edge_types"]]

    assert "Person" in entity_names
    assert "Organization" in entity_names
    assert "Location" in entity_names
    assert "MilitaryUnit" in entity_names
    assert len(entity_names) <= 16
    assert "RELATED_TO" in edge_names
    assert "LOCATED_IN" in edge_names
    assert "OCCURS_AT" in edge_names
    assert len(edge_names) <= 16


def test_ontology_generator_prompt_includes_fixed_base_catalogs():
    llm_client = _FakeLLMClient({"entity_types": [], "edge_types": [], "analysis_summary": ""})
    generator = OntologyGenerator(llm_client)

    generator.generate(
        document_texts=["Alpha document"],
        simulation_requirement="Track operational activity",
        additional_context="Collection title: demo",
    )

    user_message = llm_client.calls[0]["messages"][1]["content"]

    assert "Fixed base entity types" in user_message
    assert "Fixed base relation types" in user_message
    assert "supplemental_entity_types" in user_message
    assert "supplemental_edge_types" in user_message
    assert '"name": "Person"' in user_message
    assert '"name": "RELATED_TO"' in user_message
