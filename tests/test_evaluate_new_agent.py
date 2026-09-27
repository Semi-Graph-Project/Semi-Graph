from types import SimpleNamespace

import pytest
import yaml
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from eval_scripts import evaluate_new_agent as evaluation


@pytest.fixture
def benchmark(monkeypatch, tmp_path):
    clock = [0.0]
    calls = []
    llm = FakeMessagesListChatModel(responses=[AIMessage(content="answer")])
    cfg = SimpleNamespace(
        llm_api_key="test-only",
        eval_answer_audit_enabled=True,
        agent_retrieval={"graph": {"triple_filter": "none"}},
    )
    monkeypatch.setattr(evaluation, "get_config", lambda: cfg)
    monkeypatch.setattr(evaluation, "get_llm", lambda cfg: llm)
    monkeypatch.setattr(evaluation.time, "perf_counter", lambda: clock[0])
    monkeypatch.setattr(evaluation, "load_sox_queries", lambda: [{
        "id": "Q1", "query": "Question", "gold_chunks": ["C1"],
    }])
    monkeypatch.setattr(evaluation, "TRACE_OUTPUT_TEMPLATE", tmp_path / "{tool}.jsonl")
    monkeypatch.setattr(evaluation, "YAML_TRACE_OUTPUT_TEMPLATE", tmp_path / "{tool}.yaml")

    def search(tool):
        def retrieve(question, top_k):
            calls.append(tool)
            clock[0] += 0.4
            if tool == "graph":
                llm.invoke("Triple filter")
            return [{"chunk_id": "C1", "text": "Evidence"}]
        return retrieve

    def answer(llm, question, chunks, *, audit_enabled, synthesis_trace):
        clock[0] += 1.2
        llm.invoke("draft")
        llm.invoke("audit")
        synthesis_trace.update({
            "parts": [],
            "citation_status": "missing",
        })
        return "Grounded answer"

    def text_to_cypher(question, top_k):
        calls.append("text_to_cypher")
        clock[0] += 0.4
        llm.invoke("Generate Cypher")
        return {
            "chunks": [{"chunk_id": "C1", "text": "Evidence"}],
            "generated_cypher": "MATCH (c:Chunk) RETURN c LIMIT 10",
        }

    def agent(question, tool, generate_answer):
        clock[0] += 0.4
        llm.invoke("plan")
        llm.invoke("assess")
        if generate_answer:
            clock[0] += 1.2
            llm.invoke("synthesize")
        return {
            "chunks": [{"chunk_id": "C1", "text": "Evidence"}],
            "final_answer": "Agent answer",
            "answer_latency_ms": 1200.0 if generate_answer else 0.0,
            "synthesis_trace": {
                "parts": [],
                "citation_status": "missing",
            } if generate_answer else None,
        }

    monkeypatch.setattr(evaluation, "vector_search", search("vector"))
    monkeypatch.setattr(evaluation, "graph_search", search("graph"))
    monkeypatch.setattr(evaluation, "text_to_cypher_search", text_to_cypher)
    monkeypatch.setattr(evaluation, "generate_final_answer", answer)
    monkeypatch.setattr(evaluation, "_run_agent", agent)
    return SimpleNamespace(clock=clock, calls=calls, path=tmp_path, llm=llm, cfg=cfg)


@pytest.mark.parametrize(
    "tool",
    ["vector", "graph", "text_to_cypher", "agent_vector", "agent_graph"],
)
@pytest.mark.parametrize("mode", ["retrieve_only", "full_answer"])
def test_latency_boundaries_and_selected_warmup(benchmark, tool, mode):
    result, = evaluation.evaluate_sox_queries(tool=tool, mode=mode, workers=1, limit=1)
    answering = mode == "full_answer"
    assert result["latency_ms"] == pytest.approx(400.0)
    assert result["answer_latency_ms"] == pytest.approx(1200.0 if answering else 0.0)
    assert result["total_latency_ms"] == pytest.approx(1600.0 if answering else 400.0)
    warmup_tool = evaluation.AGENT_TOOLS.get(tool, tool)
    assert benchmark.calls[0] == warmup_tool

    trace = yaml.safe_load((benchmark.path / f"{tool}.yaml").read_text())
    assert trace["summary"]["average_latency_ms"] == 400.0
    assert trace["summary"]["average_total_latency_ms"] == (1600.0 if answering else 400.0)
    assert trace["measurement"]["workers"] == 1
    assert trace["measurement"]["warmup"]["tool"] == warmup_tool
    # Retrieval warm-up calls are reported separately, never attributed to Q1.
    assert trace["measurement"]["warmup"]["token_usage"]["llm_calls"] == (
        1 if warmup_tool in {"graph", "text_to_cypher"} else 0
    )
    expected_calls = (
        2 + int(answering) if tool in evaluation.AGENT_TOOLS
        else int(tool in {"graph", "text_to_cypher"}) + 2 * int(answering)
    )
    assert result["token_usage"]["llm_calls"] == expected_calls
    assert result["token_usage"]["status"] == ("unavailable" if expected_calls else "no_calls")
    if answering:
        assert "synthesis_trace" in result
    if tool == "text_to_cypher":
        assert result["generated_cypher"].startswith("MATCH")


def test_range_uses_only_selected_queries_for_metrics(benchmark, monkeypatch):
    monkeypatch.setattr(evaluation, "load_sox_queries", lambda: [
        {"id": "Q1", "query": "Question 1", "gold_chunks": ["C1"]},
        {"id": "Q2", "query": "Question 2", "gold_chunks": ["C1"]},
        {"id": "Q3", "query": "Question 3", "gold_chunks": ["C1"]},
    ])

    def retrieve(question, top_k):
        benchmark.calls.append(question)
        return ([{"chunk_id": "C1", "text": "Evidence"}]
                if question == "Question 2" else [])

    monkeypatch.setattr(evaluation, "vector_search", retrieve)
    results = evaluation.evaluate_sox_queries(
        tool="vector",
        mode="retrieve_only",
        workers=1,
        start=2,
        end=3,
    )

    assert [row["id"] for row in results] == ["Q2", "Q3"]
    trace = yaml.safe_load((benchmark.path / "vector.yaml").read_text())
    assert trace["summary"]["query_count"] == 2
    assert trace["summary"]["hit"] == 0.5
    assert trace["summary"]["recall"] == 0.5
    assert trace["measurement"]["selection"] == {
        "start": 2,
        "end": 3,
        "query_count": 2,
    }


def test_generation_failure_keeps_elapsed_time_and_observed_calls(benchmark, monkeypatch):
    def fail(llm, question, chunks, *, audit_enabled, synthesis_trace):
        benchmark.clock[0] += 1.2
        llm.invoke("failed generation")
        raise TimeoutError("provider timed out")

    monkeypatch.setattr(evaluation, "generate_final_answer", fail)
    result, = evaluation.evaluate_sox_queries(tool="vector", mode="full_answer", workers=1)
    assert result["latency_ms"] == pytest.approx(400.0)
    assert result["answer_latency_ms"] == pytest.approx(1200.0)
    assert result["total_latency_ms"] == pytest.approx(1600.0)
    assert result["answer_error"] == "TimeoutError"
    assert result["token_usage"]["llm_calls"] == 1


def test_invalid_agent_synthesis_duration_is_not_silently_clipped(benchmark, monkeypatch):
    monkeypatch.setattr(evaluation, "_run_agent", lambda *args, **kwargs: {
        "chunks": [], "final_answer": "answer", "answer_latency_ms": 1000.0,
    })
    with pytest.raises(RuntimeError, match="within total"):
        evaluation.evaluate_sox_queries(tool="agent_graph", mode="full_answer", workers=1)


def test_trace_io_is_excluded_from_query_latency(benchmark, monkeypatch):
    original = evaluation.write_yaml_trace

    def slow_write(*args):
        benchmark.clock[0] += 10.0
        original(*args)

    monkeypatch.setattr(evaluation, "write_yaml_trace", slow_write)
    result, = evaluation.evaluate_sox_queries(tool="vector", mode="full_answer", workers=1)
    assert result["total_latency_ms"] == pytest.approx(1600.0)


def test_provider_tokens_are_saved_per_query_and_summed_with_warmup(benchmark):
    benchmark.llm.responses = [AIMessage(content="answer", usage_metadata={
        "input_tokens": 10, "output_tokens": 4, "total_tokens": 14,
    })]
    result, = evaluation.evaluate_sox_queries(tool="graph", mode="full_answer", workers=1)
    assert result["token_usage"]["prompt_tokens"] == 30
    assert result["token_usage"]["completion_tokens"] == 12
    assert result["token_usage"]["total_tokens"] == 42
    assert result["token_usage"]["status"] == "complete"
    trace = yaml.safe_load((benchmark.path / "graph.yaml").read_text())
    assert trace["summary"]["token_usage"]["total_tokens"] == 42
    assert trace["summary"]["token_usage_including_warmup"]["total_tokens"] == 56


@pytest.mark.parametrize("audit_enabled,expected_calls", [(True, 2), (False, 1)])
def test_real_answer_generator_obeys_audit_config_and_records_tokens(
    benchmark, monkeypatch, audit_enabled, expected_calls,
):
    from eval_scripts.eval_agent import generate_final_answer

    benchmark.cfg.eval_answer_audit_enabled = audit_enabled
    benchmark.llm.responses = [AIMessage(content="answer", usage_metadata={
        "input_tokens": 10, "output_tokens": 4, "total_tokens": 14,
    })]
    monkeypatch.setattr(evaluation, "generate_final_answer", generate_final_answer)
    result, = evaluation.evaluate_sox_queries(tool="vector", mode="full_answer", workers=1)
    assert result["answer_audit_enabled"] is audit_enabled
    assert result["token_usage"]["llm_calls"] == expected_calls
    assert result["token_usage"]["total_tokens"] == 14 * expected_calls
    trace = yaml.safe_load((benchmark.path / "vector.yaml").read_text())
    assert trace["measurement"]["answer_audit_enabled"] is audit_enabled
