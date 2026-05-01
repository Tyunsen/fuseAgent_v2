import sys
import types
from pathlib import Path

agent_pkg = types.ModuleType("aperag.agent")
agent_pkg.__path__ = [str(Path(__file__).resolve().parents[3] / "aperag" / "agent")]
sys.modules.setdefault("aperag.agent", agent_pkg)

db_ops_stub = types.ModuleType("aperag.db.ops")
db_ops_stub.async_db_ops = object()
sys.modules.setdefault("aperag.db.ops", db_ops_stub)

from aperag.agent.stream_formatters import (
    format_stream_content,
    format_stream_end,
    format_stream_start,
)
from aperag.schema import view_models
from aperag.service.prompt_template_service import build_agent_query_prompt
from aperag.service.trace_answer_service import trace_answer_service


def test_build_agent_query_prompt_appends_time_trace_guidance():
    agent_message = view_models.AgentMessage(
        query="3月发生了什么？",
        collections=[],
        language="zh-CN",
        trace_mode="time",
    )
    context = trace_answer_service.build_prompt_context(
        trace_mode="time",
        query=agent_message.query,
        query_keywords=["3月", "发生"],
        channels=["vector_search", "fulltext_search", "graph_search"],
    )

    prompt = build_agent_query_prompt(
        chat_id="chat_1",
        agent_message=agent_message,
        user="user_1",
        template="Question: {{ query }}",
        prompt_appendix=trace_answer_service.build_prompt_appendix(context),
    )

    assert "Question: 3月发生了什么？" in prompt
    assert "Trace mode: time." in prompt
    assert "full-text keywords aligned with the time focus" in prompt


def test_trace_mode_stream_formatters_keep_mode_metadata():
    start = format_stream_start("msg_1", trace_mode="entity")
    chunk = format_stream_content("msg_1", "content", trace_mode="entity")
    end = format_stream_end("msg_1", references=[], urls=[], trace_mode="entity")

    assert start["trace_mode"] == "entity"
    assert chunk["trace_mode"] == "entity"
    assert end["trace_mode"] == "entity"


def test_trace_answer_service_defaults_to_default_mode():
    context = trace_answer_service.build_prompt_context(
        trace_mode=None,
        query="伊朗相关情况",
        query_keywords=["伊朗"],
        channels=["vector_search", "fulltext_search", "graph_search"],
    )

    assert context.trace_mode == "default"
    assert "Trace mode: default." in trace_answer_service.build_prompt_appendix(context)


def test_space_trace_prompt_uses_default_topology_not_gantt():
    context = trace_answer_service.build_prompt_context(
        trace_mode="space",
        query="阿布扎比发生了什么？",
        query_keywords=["阿布扎比"],
        channels=["vector_search", "fulltext_search", "graph_search"],
    )

    appendix = trace_answer_service.build_prompt_appendix(context)

    assert "Trace mode: space." in appendix
    assert "graph TD" in appendix
    assert "Do not include a gantt chart for space mode." in appendix


def test_entity_trace_prompt_avoids_mermaid_subgraph_output():
    context = trace_answer_service.build_prompt_context(
        trace_mode="entity",
        query="伊朗相关的关键参与方和关系",
        query_keywords=["伊朗"],
        channels=["vector_search", "fulltext_search", "graph_search"],
    )

    appendix = trace_answer_service.build_prompt_appendix(context)

    assert "Trace mode: entity." in appendix
    assert "Do not include a Mermaid knowledge subgraph" in appendix
