import pytest

from semigraph.config import get_config
from semigraph import demo
from semigraph.agent import nodes
from semigraph.agent.graph import build_agent
from semigraph.demo import (
    ComparisonResult,
    get_backend_config,
    get_backend_corpus,
    get_backend_corpora,
    run_comparison,
)
from semigraph.trace import TRACE_STORE


def test_backend_corpora_expose_the_two_demo_targets():
    corpora = get_backend_corpora()

    assert [corpus.key for corpus in corpora] == ["benchmark", "production"]
    assert [corpus.neo4j_uri for corpus in corpora] == [
        "bolt://localhost:7690",
        "bolt://localhost:7687",
    ]
    assert [corpus.vector_index for corpus in corpora] == [
        "gold_chunk_embedding",
        "chunk_embedding",
    ]


def test_get_backend_config_isolated_from_cached_config():
    base_config = get_config()
    base_uri = base_config.neo4j_uri

    benchmark_config = get_backend_config("benchmark", base_config=base_config)

    assert benchmark_config is not base_config
    assert benchmark_config.neo4j_uri == "bolt://localhost:7690"
    assert benchmark_config.agent_retrieval["vector"]["vector_index"] == (
        "gold_chunk_embedding"
    )
    assert benchmark_config.agent_retrieval["graph"][
        "chunk_seed_vector_index"
    ] == "gold_chunk_embedding"
    assert base_config.neo4j_uri == base_uri
    assert base_config.agent_retrieval["vector"].get("vector_index") is None


def test_backend_corpus_accepts_descriptor_and_rejects_unknown_key():
    production = get_backend_corpora()[1]

    assert get_backend_corpus(production) is production

    try:
        get_backend_corpus("missing")
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("Unknown corpus key should fail")


def test_comparison_result_has_a_shared_serializable_shape():
    result = ComparisonResult(
        status="complete",
        answer="Grounded answer",
        citations=[{"chunk_id": "c1"}],
        trace=[{"event": "vector_search", "status": "ok"}],
        latency_sec=1.25,
    )

    assert result.to_dict() == {
        "status": "complete",
        "answer": "Grounded answer",
        "citations": [{"chunk_id": "c1"}],
        "trace": [{"event": "vector_search", "status": "ok"}],
        "latency_sec": 1.25,
        "error": None,
    }


def test_run_comparison_direct_vector_uses_selected_config_and_shared_synthesis(
    monkeypatch,
):
    captured = {}
    chunks = [{"chunk_id": "c1", "text": "Evidence"}]

    def fake_vector_search(query, top_k, cfg, trace_callback=None):
        captured["retrieval"] = (query, top_k, cfg.neo4j_uri)
        return {"chunks": chunks, "trace": {"retriever": "vector"}}

    def fake_synthesis(state, cfg=None):
        captured["synthesis"] = (state, cfg.neo4j_uri)
        return {
            "final_answer": "Answer [1]",
            "citation_map": [{"citation_index": 1, "chunk_id": "c1"}],
            "synthesis_trace": {"status": "ok", "llm_calls": 1},
        }

    monkeypatch.setattr(demo.agent_tools, "agent_vector_search", fake_vector_search)
    monkeypatch.setattr(demo.nodes, "synthesize_attempts_node", fake_synthesis)

    result = run_comparison("vector", "Question", "benchmark", top_k=3)

    assert result.status == "complete"
    assert result.answer == "Answer [1]"
    assert result.citations == [{"citation_index": 1, "chunk_id": "c1"}]
    assert captured["retrieval"] == (
        "Question",
        3,
        "bolt://localhost:7690",
    )
    assert captured["synthesis"][1] == "bolt://localhost:7690"
    assert [event["stage"] for event in result.trace] == [
        "config",
        "retrieval",
        "retrieval_summary",
        "synthesis",
        "synthesis",
    ]


@pytest.mark.parametrize("mode", ["vector", "graph"])
def test_run_comparison_uses_configured_synthesis_budget_when_top_k_omitted(
    monkeypatch,
    mode,
):
    captured = {}
    chunks = [{"chunk_id": "c1", "text": "Evidence"}]

    def fake_retrieval(query, top_k, cfg, trace_callback=None):
        captured["retrieval"] = (query, top_k, cfg.neo4j_uri)
        return {"chunks": chunks, "trace": {"retriever": mode}}

    def fake_synthesis(state, cfg=None):
        return {
            "final_answer": "Answer [1]",
            "citation_map": [{"citation_index": 1, "chunk_id": "c1"}],
            "synthesis_trace": {"status": "ok", "llm_calls": 1},
        }

    retriever_name = (
        "agent_vector_search" if mode == "vector" else "agent_graph_search"
    )
    monkeypatch.setattr(demo.agent_tools, retriever_name, fake_retrieval)
    monkeypatch.setattr(demo.nodes, "synthesize_attempts_node", fake_synthesis)

    selected_config = get_backend_config("production")
    result = run_comparison(mode, "Question", "production")

    assert result.status == "complete"
    assert captured["retrieval"] == (
        "Question",
        selected_config.agent_max_synthesis_chunks,
        "bolt://localhost:7687",
    )


def test_run_comparison_direct_graph_uses_selected_config_and_shared_synthesis(
    monkeypatch,
):
    captured = {}
    chunks = [{"chunk_id": "graph-c1", "text": "Graph evidence"}]

    def fake_graph_search(query, top_k, cfg, trace_callback=None):
        captured["retrieval"] = (query, top_k, cfg.neo4j_uri)
        return {"chunks": chunks, "trace": {"retriever": "graph"}}

    def fake_synthesis(state, cfg=None):
        captured["synthesis"] = (state, cfg.neo4j_uri)
        return {
            "final_answer": "Graph answer [1]",
            "citation_map": [{"citation_index": 1, "chunk_id": "graph-c1"}],
            "synthesis_trace": {"status": "ok", "llm_calls": 1},
        }

    monkeypatch.setattr(
        demo.agent_tools,
        "agent_graph_search",
        fake_graph_search,
    )
    monkeypatch.setattr(demo.nodes, "synthesize_attempts_node", fake_synthesis)

    result = run_comparison("graph", "Question", "production", top_k=3)

    assert result.status == "complete"
    assert result.answer == "Graph answer [1]"
    assert result.citations == [
        {"citation_index": 1, "chunk_id": "graph-c1"}
    ]
    assert captured["retrieval"] == (
        "Question",
        3,
        "bolt://localhost:7687",
    )
    assert captured["synthesis"][1] == "bolt://localhost:7687"
    assert [event["stage"] for event in result.trace] == [
        "config",
        "retrieval",
        "retrieval_summary",
        "synthesis",
        "synthesis",
    ]


def test_run_comparison_emits_live_trace_events_without_changing_result(
    monkeypatch,
):
    chunks = [{"chunk_id": "c1", "text": "Evidence"}]

    def fake_vector_search(query, top_k, cfg, trace_callback=None):
        return {"chunks": chunks, "trace": {"retriever": "vector"}}

    def fake_synthesis(state, cfg=None):
        return {
            "final_answer": "Answer [1]",
            "citation_map": [{"citation_index": 1, "chunk_id": "c1"}],
            "synthesis_trace": {"status": "ok", "llm_calls": 1},
        }

    monkeypatch.setattr(demo.agent_tools, "agent_vector_search", fake_vector_search)
    monkeypatch.setattr(demo.nodes, "synthesize_attempts_node", fake_synthesis)
    events = []

    result = run_comparison(
        "vector",
        "Question",
        "benchmark",
        trace_callback=events.append,
        run_id="test-live-vector-trace",
    )

    assert result.status == "complete"
    assert [event["stage"] for event in events] == [
        "config",
        "retrieval",
        "retrieval_summary",
        "synthesis",
        "synthesis",
    ]
    assert events[1]["status"] == "running"
    assert events[1]["message"] == "Searching evidence with vector retrieval"
    assert events[3]["status"] == "running"
    assert events[4]["message"] == "Finished answer synthesis"
    assert [event["seq"] for event in events] == [1, 2, 3, 4, 5]
    trace_document = TRACE_STORE.read("test-live-vector-trace")
    assert trace_document["status"] == "complete"
    assert trace_document["events"] == events


@pytest.mark.parametrize(
    ("mode", "locked_tool"),
    [
        ("agent_vector", "vector"),
        ("agent_graph", "graph"),
    ],
)
def test_run_comparison_agent_modes_pass_selected_config(
    monkeypatch,
    mode,
    locked_tool,
):
    captured = {}

    class FakeAgent:
        def invoke(self, state, config):
            captured["invoke"] = (state, config)
            return {
                "final_answer": "Agent answer [1]",
                "citation_map": [{"citation_index": 1, "chunk_id": "c1"}],
                "plan_trace": {"status": "ok"},
                "attempts": [{
                    "attempt_id": "T1-A1",
                    "task_id": "T1",
                    "action": {"tool": locked_tool, "query": "Question"},
                    "retrieval_status": "ok",
                    "chunks": [{"chunk_id": "c1"}],
                    "retrieval_trace": {"retriever": locked_tool},
                }],
                "synthesis_trace": {"status": "ok", "llm_calls": 1},
            }

    def fake_build_agent(**kwargs):
        captured["build"] = kwargs
        return FakeAgent()

    monkeypatch.setattr(demo, "build_agent", fake_build_agent)

    result = run_comparison(mode, "Question", "production", top_k=4)

    assert result.status == "complete"
    assert captured["build"]["locked_tool"] == locked_tool
    assert captured["build"]["top_k"] == 4
    assert captured["build"]["cfg"].neo4j_uri == "bolt://localhost:7687"
    assert captured["invoke"] == (
        {"original_query": "Question"},
        {"recursion_limit": 50},
    )
    assert [event["stage"] for event in result.trace] == [
        "config",
        "plan",
        "plan",
        "retrieval",
        "synthesis",
    ]


def test_run_comparison_returns_panel_error_for_invalid_mode():
    result = run_comparison("unknown", "Question", "benchmark")

    assert result.status == "error"
    assert result.trace[0]["stage"] == "runner"
    assert "Unknown comparison mode" in (result.error or "")


def test_build_agent_passes_explicit_config_to_agent_nodes(monkeypatch):
    selected_config = get_backend_config("benchmark")
    captured = {}

    def fake_plan_route(state, locked_tool=None, cfg=None):
        captured["plan"] = cfg
        return {"tasks": []}

    def fake_synthesis(state, cfg=None):
        captured["synthesis"] = cfg
        return {
            "final_answer": "No evidence",
            "citation_map": [],
            "synthesis_trace": {"status": "no_evidence"},
        }

    monkeypatch.setattr(nodes, "plan_route_node", fake_plan_route)
    monkeypatch.setattr(nodes, "synthesize_attempts_node", fake_synthesis)

    build_agent(cfg=selected_config).invoke({"original_query": "Question"})

    assert captured["plan"] is selected_config
    assert captured["synthesis"] is selected_config
