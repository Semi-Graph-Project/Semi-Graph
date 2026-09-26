from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult, LLMResult
from langchain_openai import ChatOpenAI

from eval_scripts.token_usage import (
    TokenUsageCollector,
    collect_token_usage,
    summarize_token_usage,
)
import semigraph.agents.graph as agent_graph


class UsageLLM(BaseChatModel):
    """Emit real LangChain callbacks without contacting a provider."""

    input_tokens: int = 7
    report_usage: bool = True
    fail: bool = False

    @property
    def _llm_type(self):
        return "test-usage"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        if self.fail:
            raise TimeoutError("provider timed out")
        usage = {
            "input_tokens": self.input_tokens,
            "output_tokens": 3,
            "total_tokens": self.input_tokens + 3,
        } if self.report_usage else None
        return ChatResult(generations=[ChatGeneration(message=AIMessage(
            content="ok",
            usage_metadata=usage,
        ))])


def test_usage_context_captures_tokens_without_model_name_and_resets():
    llm = UsageLLM()
    with collect_token_usage() as usage:
        llm.invoke("draft")
        llm.invoke("audit")

    assert usage.snapshot() == {
        "prompt_tokens": 14,
        "completion_tokens": 6,
        "total_tokens": 20,
        "llm_calls": 2,
        "calls_with_usage": 2,
        "status": "complete",
    }
    llm.invoke("outside evaluation")
    assert usage.snapshot()["llm_calls"] == 2


@pytest.mark.parametrize("source", ["message_metadata", "llm_output"])
def test_openai_usage_fallback_does_not_double_count(source):
    tokens = {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14}
    message = AIMessage(
        content="ok",
        response_metadata={"token_usage": tokens} if source == "message_metadata" else {},
    )
    response = LLMResult(
        generations=[[ChatGeneration(message=message)]],
        llm_output={"token_usage": tokens},
    )
    collector = TokenUsageCollector()
    collector.on_chat_model_start({}, [[]])
    collector.on_llm_end(response)
    assert collector.snapshot()["total_tokens"] == 14
    assert collector.snapshot()["calls_with_usage"] == 1


def test_missing_usage_is_unknown_and_partial_sums_are_labeled():
    with collect_token_usage() as unknown:
        UsageLLM(report_usage=False).invoke("usage unavailable")
    assert unknown.snapshot()["total_tokens"] is None
    assert unknown.snapshot()["status"] == "unavailable"

    with collect_token_usage() as partial:
        UsageLLM().invoke("usage available")
        UsageLLM(report_usage=False).invoke("usage unavailable")
    assert partial.snapshot()["total_tokens"] == 10
    assert partial.snapshot()["status"] == "partial"
    total = summarize_token_usage([unknown.snapshot(), partial.snapshot()])
    assert total["llm_calls"] == 3
    assert total["calls_with_usage"] == 1
    assert total["total_tokens"] == 10
    assert total["status"] == "partial"


def test_no_llm_calls_are_zero_and_exception_resets_context():
    with pytest.raises(RuntimeError):
        with collect_token_usage() as usage:
            raise RuntimeError("failed query")
    UsageLLM().invoke("outside failed context")
    assert usage.snapshot()["total_tokens"] == 0
    assert usage.snapshot()["status"] == "no_calls"


def test_failed_provider_call_is_counted_as_missing_usage():
    with collect_token_usage() as usage:
        with pytest.raises(TimeoutError):
            UsageLLM(fail=True).invoke("timeout")
    assert usage.snapshot()["llm_calls"] == 1
    assert usage.snapshot()["calls_with_usage"] == 0
    assert usage.snapshot()["total_tokens"] is None
    assert usage.snapshot()["status"] == "unavailable"


def test_chatopenai_adapter_preserves_provider_usage_without_network():
    def respond(request):
        return httpx.Response(200, json={
            "id": "test-response",
            "object": "chat.completion",
            "created": 0,
            "model": "test-model",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "ok"},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
                "completion_tokens_details": {"reasoning_tokens": 12},
            },
        })

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        llm = ChatOpenAI(model="test-model", api_key="test-only", http_client=client)
        with collect_token_usage() as usage:
            llm.invoke("question")
    assert usage.snapshot()["prompt_tokens"] == 100
    assert usage.snapshot()["completion_tokens"] == 20
    assert usage.snapshot()["total_tokens"] == 120
    assert usage.snapshot()["status"] == "complete"


def test_parallel_queries_capture_nested_agent_llm_calls_independently(monkeypatch):
    """Exercise the actual root graph, fan-out, nested workers and synthesis."""
    cfg = SimpleNamespace(
        agent_max_parallel_tasks=2,
        agent_max_attempts_per_task=1,
        agent_max_synthesis_chunks=10,
        agent_top_k_chunks=5,
    )

    def call_llm(state):
        UsageLLM(input_tokens=7 if state["original_query"] == "Q1" else 17).invoke("call")

    def plan(state, **kwargs):
        call_llm(state)
        return {"tasks": [{"query": "a"}, {"query": "b"}]}

    def execute(state, **kwargs):
        call_llm(state)  # Stand-in for Graph's Triple filter LLM.
        return {"chunks": [{"chunk_id": f"C{state['task_index']}", "text": "evidence"}]}

    def assess(state, **kwargs):
        call_llm(state)
        return {"assessment": {"is_covered": True}, "accepted_chunks": state["chunks"]}

    def synthesize(state, **kwargs):
        call_llm(state)
        return {"final_answer": "ok"}

    monkeypatch.setattr(agent_graph, "plan_route_node", plan)
    monkeypatch.setattr(agent_graph, "execute_node", execute)
    monkeypatch.setattr(agent_graph, "assess_node", assess)
    monkeypatch.setattr(agent_graph, "synthesize_node", synthesize)

    def evaluate(question):
        with collect_token_usage() as usage:
            agent_graph.run_agent({"original_query": question}, cfg=cfg)
        return usage.snapshot()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = list(executor.map(evaluate, ["Q1", "Q2"]))

    assert first["llm_calls"] == second["llm_calls"] == 6
    assert first["total_tokens"] == 60
    assert second["total_tokens"] == 120
    assert first["status"] == second["status"] == "complete"
