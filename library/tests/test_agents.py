"""Exercise the copied Agent loops with arbitrary text and no external services."""

import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from semigraph_sdk.agents import AgentConfig, AgentRuntime, run_agent
from semigraph_sdk.agents.nodes import plan_route_node


CHUNK = {"chunk_id": "text-001", "text": "ปั๊ม P7 ใช้ซีลเซรามิก", "score": 0.8}
TASK = {"query": "วัสดุซีลของปั๊ม P7", "requirement": "หลักฐานวัสดุที่ใช้ทำซีลของปั๊ม P7"}
PLAN = {"tasks": [TASK]}
ACCEPT = {
    "accepted_chunk_ids": [CHUNK["chunk_id"]], "is_covered": True,
    "retry_query": None, "retry_strategy": None,
}
ANSWER = {
    "parts": [{"answer": "ปั๊ม P7 ใช้ซีลเซรามิก", "supported_facts": [
        {"claim": "ซีลทำจากเซรามิก", "evidence_ids": [CHUNK["chunk_id"]]},
    ]}],
    "final_answer": "ปั๊ม P7 ใช้ซีลเซรามิก [text-001]",
}


class SequenceLLM:
    def __init__(self, payloads):
        self.payloads = iter(payloads)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        payload = next(self.payloads)
        content = payload if isinstance(payload, list) else json.dumps(payload)
        return SimpleNamespace(content=content)


def runtime(llm, retriever, tool="graph", relations=None, **config):
    return AgentRuntime(
        llm=llm,
        retrievers={tool: retriever},
        relations={} if relations is None else relations,
        config=AgentConfig(max_planned_tasks=1, max_parallel_tasks=1, **config),
    )


@pytest.mark.parametrize("tool", ["vector", "graph"])
@pytest.mark.parametrize("full_answer", [False, True])
@pytest.mark.parametrize("relations", [{}, {"USES_MATERIAL": "วัสดุที่อุปกรณ์ใช้"}])
def test_task_specific_accepts_arbitrary_or_empty_relations(tool, full_answer, relations):
    llm = SequenceLLM([PLAN, ACCEPT, *([ANSWER] if full_answer else [])])
    retrieve = Mock(return_value=[CHUNK])
    result = run_agent(
        {"original_query": "ปั๊ม P7 ใช้ซีลวัสดุอะไร"}, tool,
        runtime=runtime(llm, retrieve, tool, relations), generate_answer=full_answer,
    )
    assert result["synthesis_input"]["accepted_chunks"] == [CHUNK]
    assert len(llm.calls) == (3 if full_answer else 2)
    assert f"`{tool}`" in llm.calls[0][0]["content"]
    assess_input = json.loads(llm.calls[1][1]["content"])
    assert assess_input["observed_relations"] == relations
    retrieve.assert_called_once_with(query=TASK["query"], top_k_chunks=10)
    if full_answer:
        assert "[text-001]" in result["final_answer"]
        assert result["synthesis_trace"]["selected_chunk_ids"] == ["text-001"]
    else:
        assert "final_answer" not in result


def test_task_specific_retries_using_missing_evidence():
    retry = {
        "accepted_chunk_ids": [], "is_covered": False,
        "retry_query": "P7 ceramic seal material", "retry_strategy": "focus_missing",
    }
    llm = SequenceLLM([PLAN, retry, ACCEPT])
    retrieve = Mock(side_effect=[[], [CHUNK]])
    result = run_agent(
        {"original_query": "วัสดุซีล P7"},
        runtime=runtime(llm, retrieve), generate_answer=False,
    )
    worker = result["worker_results"][0]
    assert len(worker["attempts"]) == 2
    assert retrieve.call_args_list[1].kwargs["query"] == retry["retry_query"]
    assert result["synthesis_input"]["accepted_chunks"] == [CHUNK]


def test_unknown_evidence_ids_are_rejected_without_synthesis():
    llm = SequenceLLM([PLAN, {**ACCEPT, "accepted_chunk_ids": ["invented"]}])
    result = run_agent(
        {"original_query": "วัสดุซีล P7"},
        runtime=runtime(llm, Mock(return_value=[CHUNK])), generate_answer=True,
    )
    assert result["worker_results"][0]["stop_reason"] == "unknown_chunk_ids"
    assert result["synthesis_input"]["accepted_chunks"] == []
    assert result["final_answer"] == "Do not Answer"
    assert result["synthesis_trace"]["llm_calls"] == 0
    assert len(llm.calls) == 2


def test_plan_accepts_content_blocks_and_repairs_excess_tasks():
    llm = SequenceLLM([
        {"tasks": [TASK, TASK]},
        [{"type": "text", "text": json.dumps(PLAN)}],
    ])
    result = plan_route_node(
        {"original_query": "วัสดุซีล P7"}, "graph",
        runtime(llm, Mock()),
    )
    assert result == PLAN
    assert "Plan exceeds 1 tasks" in llm.calls[1][1]["content"]


def test_missing_tool_fails_before_llm_call():
    llm = Mock()
    with pytest.raises(ValueError, match="No retriever configured"):
        run_agent({"original_query": "question"}, "graph", runtime=runtime(llm, Mock(), "vector"))
    llm.invoke.assert_not_called()


def test_database_errors_are_not_empty_results():
    llm = SequenceLLM([PLAN])
    with pytest.raises(RuntimeError, match="Database unavailable"):
        run_agent(
            {"original_query": "วัสดุซีล P7"},
            runtime=runtime(llm, Mock(side_effect=RuntimeError("Database unavailable"))),
            generate_answer=False,
        )


def test_parallel_tasks_share_dependencies_but_collect_unique_evidence():
    class ParallelLLM:
        def invoke(self, messages):
            if "You plan evidence retrieval" in messages[0]["content"]:
                return SimpleNamespace(content=json.dumps({"tasks": [
                    TASK, {"query": "P7 seal", "requirement": "Identify the seal"},
                ]}))
            return SimpleNamespace(content=json.dumps(ACCEPT))

    retrieve = Mock(return_value=[CHUNK])
    context = AgentRuntime(
        llm=ParallelLLM(), retrievers={"graph": retrieve},
        config=AgentConfig(max_planned_tasks=2, max_parallel_tasks=2),
    )
    result = run_agent(
        {"original_query": "Identify P7's seal and its material"},
        runtime=context, generate_answer=False,
    )
    assert retrieve.call_count == 2
    assert len(result["worker_results"]) == 2
    assert result["synthesis_input"]["accepted_chunks"] == [CHUNK]


def test_library_import_does_not_load_original_package_or_env():
    library_src = str(Path(__file__).resolve().parents[1] / "src")
    env = {k: v for k, v in os.environ.items() if k not in {
        "NEO4J_URI", "NEO4J_PASSWORD", "OPENROUTER_API_KEY", "OPENAI_API_KEY",
    }}
    env["PYTHONPATH"] = library_src
    script = '''
import os, sys
import semigraph_sdk.agents
assert not any(m == "semigraph" or m.startswith("semigraph.") for m in sys.modules)
assert not any(k in os.environ for k in (
    "NEO4J_URI", "NEO4J_PASSWORD", "OPENROUTER_API_KEY", "OPENAI_API_KEY",
))
'''
    subprocess.run([sys.executable, "-B", "-c", script], env=env, check=True)
