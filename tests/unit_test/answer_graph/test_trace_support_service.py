import sys
import types

import pytest

from aperag.schema import view_models

answer_graph_stub = types.ModuleType("aperag.service.answer_graph_service")
answer_graph_stub.answer_graph_service = object()
sys.modules["aperag.service.answer_graph_service"] = answer_graph_stub

from aperag.service.trace_support_service import TraceSupportService


class _FakeAnswerGraphService:
    async def get_trace_graph(self, **kwargs):  # noqa: ARG002
        return view_models.AnswerGraphResponse(
            nodes=[],
            edges=[],
            linked_row_ids=["row_1"],
            is_empty=False,
            trace_mode="time",
            layout="timeline",
            focus_label="2026-03",
            groups=[
                view_models.TraceGraphGroup(
                    id="time-1",
                    label="2026-03",
                    kind="time",
                    node_ids=[],
                    row_ids=["row_1"],
                )
            ],
        )


@pytest.mark.asyncio
async def test_trace_support_service_binds_conclusions_to_existing_rows(trace_reference_rows):
    service = TraceSupportService()
    service.answer_graph_service = _FakeAnswerGraphService()

    request = view_models.TraceSupportRequest(
        trace_mode="time",
        question="what happened in march?",
        answer="2026-03 Abu Dhabi held a joint exercise.",
        references=[view_models.TraceSupportReferenceInput(**row) for row in trace_reference_rows],
    )

    response = await service.build_trace_support(
        user_id="user_1",
        collection_id="col_1",
        request=request,
    )

    assert response.trace_mode == "time"
    assert response.conclusions
    assert "row_1" in response.conclusions[0].source_row_ids
    assert response.graph.layout == "timeline"
    assert response.graph.groups[0].label == "2026-03"
    assert response.evidence_summary


@pytest.mark.asyncio
async def test_trace_support_service_prefers_row_specific_time_labels_for_time_mode():
    service = TraceSupportService()
    service.answer_graph_service = _FakeAnswerGraphService()

    request = view_models.TraceSupportRequest(
        trace_mode="time",
        question="what happened in march?",
        answer="2026-03-12 Abu Dhabi held a joint exercise. 2026-03-15 Tehran held a follow-up meeting.",
        references=[
            view_models.TraceSupportReferenceInput(
                source_row_id="row_1",
                text="2026-03-12 Abu Dhabi held a joint exercise.",
                snippet="2026-03-12 Abu Dhabi held a joint exercise.",
                document_id="doc_1",
                document_name="briefing-1.md",
                preview_title="Abu Dhabi joint exercise",
                chunk_ids=["chunk_1"],
                paragraph_precise=True,
            ),
            view_models.TraceSupportReferenceInput(
                source_row_id="row_2",
                text="2026-03-15 Tehran held a follow-up meeting.",
                snippet="2026-03-15 Tehran held a follow-up meeting.",
                document_id="doc_2",
                document_name="briefing-2.md",
                preview_title="Tehran follow-up meeting",
                chunk_ids=["chunk_2"],
                paragraph_precise=True,
            ),
        ],
    )

    response = await service.build_trace_support(
        user_id="user_1",
        collection_id="col_1",
        request=request,
    )

    assert response.conclusions
    assert any(conclusion.time_label == "2026-03-12" for conclusion in response.conclusions)
    assert any(conclusion.time_label == "2026-03-15" for conclusion in response.conclusions)
    assert all("conclusion" not in conclusion.title.lower() for conclusion in response.conclusions)
