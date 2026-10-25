"""Run the actual DeepAgent tool loop against an injected non-financial corpus."""

import json
from unittest.mock import Mock

import pytest

pytest.importorskip("deepagents")

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from semigraph_sdk.agents import AgentConfig, AgentRuntime
from semigraph_sdk.agents.deepagent import Deepagent


CHUNK = {"chunk_id": "pump-1", "text": "Pump P7 uses a ceramic seal.", "score": 0.8}


class ScriptedModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def call(name, **args):
    return AIMessage(content="", tool_calls=[{
        "name": name, "args": args, "id": f"call-{name}", "type": "tool_call",
    }])


def make_runtime(tool, retrieve, *, full_answer=False, selected=None):
    responses = [
        call(f"search_{tool}", query="Pump P7 seal material"),
        call("EvidenceSelection", chunk_ids=["pump-1"] if selected is None else selected),
    ]
    if full_answer:
        responses.append(AIMessage(content=json.dumps({
            "parts": [{"answer": "A ceramic seal.", "supported_facts": [
                {"claim": "The seal is ceramic.", "evidence_ids": ["pump-1"]},
            ]}],
            "final_answer": "A ceramic seal. [pump-1]",
        })))
    return AgentRuntime(
        llm=ScriptedModel(responses=responses), retrievers={tool: retrieve},
        config=AgentConfig(max_planned_tasks=1, max_parallel_tasks=1),
    )


@pytest.mark.parametrize("tool", ["vector", "graph"])
@pytest.mark.parametrize("full_answer", [False, True])
def test_real_tool_loop_and_optional_synthesis(tool, full_answer):
    retrieve = Mock(return_value=[CHUNK])
    result = Deepagent(
        "What material does P7 use?", tool, full_answer,
        runtime=make_runtime(tool, retrieve, full_answer=full_answer),
    )
    assert result["chunks"] == [CHUNK]
    retrieve.assert_called_once_with(query="Pump P7 seal material", top_k_chunks=10)
    assert result["retrieval_trace"]["searches"][0]["tool"] == tool
    if full_answer:
        assert "[pump-1]" in result["final_answer"]
        assert result["synthesis_trace"]["llm_calls"] == 1
    else:
        assert result["final_answer"] == ""
        assert result["synthesis_trace"] is None


def test_selected_ids_cannot_leak_from_previous_run():
    first = Deepagent(
        "First query", FullAnswer=False,
        runtime=make_runtime("vector", Mock(return_value=[CHUNK])),
    )
    assert first["chunks"] == [CHUNK]
    second = Deepagent(
        "Second query", FullAnswer=False,
        runtime=make_runtime("vector", Mock(return_value=[])),
    )
    assert second["chunks"] == []
    assert second["retrieval_trace"]["rejected_chunk_ids"] == ["pump-1"]


def test_database_error_propagates():
    with pytest.raises(RuntimeError):
        Deepagent(
            "What material does P7 use?", FullAnswer=False,
            runtime=make_runtime("vector", Mock(side_effect=RuntimeError("Database unavailable"))),
        )
