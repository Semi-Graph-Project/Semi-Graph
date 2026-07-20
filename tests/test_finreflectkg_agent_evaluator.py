"""Unit tests for the FinReflectKG Agent evaluator."""

import json

import yaml

from scripts import evaluate_finreflectkg_agent as evaluator
from scripts.evaluate_finreflectkg_agent import (
    agent_state_errors,
    aggregate_results,
    build_evaluation_agent,
    evidence_groups,
    load_checkpoint,
    locked_tool_selector,
    result_from_state,
    score_chunks,
    score_groups,
    validate_resume_config,
    write_checkpoint,
)
from scripts.evaluate_retrieval_quality import (
    _score_group_result as phase_t_score_groups,
)
from scripts.evaluate_retrieval_quality import _score_result as phase_t_score_chunks


def test_chunk_scoring_matches_phase_t_evaluator():
    returned = ["noise", "gold_b", "gold_a", "gold_b"]
    gold = ["gold_a", "gold_b", "gold_c"]

    assert score_chunks(returned, gold) == phase_t_score_chunks(returned, gold)


def test_group_scoring_matches_phase_t_evaluator():
    returned = ["hop_1_alt", "hop_2"]
    groups = {
        "hop_1": ["hop_1", "hop_1_alt"],
        "hop_2": ["hop_2"],
        "hop_3": ["hop_3"],
    }

    assert score_groups(returned, groups) == phase_t_score_groups(returned, groups)


def test_evidence_groups_uses_legacy_fallback():
    assert evidence_groups({}, ["gold_a", "gold_b"]) == {
        "gold_chunks": ["gold_a", "gold_b"]
    }


def test_locked_selector_preserves_retry_query_and_budget():
    selector = locked_tool_selector("graph", top_k=7)

    update = selector({
        "original_query": "original",
        "subqueries": ["planned"],
        "current_subquery_idx": 0,
        "retry_query": "targeted retry",
    })

    assert update == {
        "next_tool": {
            "name": "graph",
            "args": {"query": "targeted retry", "top_k_chunks": 7},
        }
    }


def test_all_evaluation_modes_compile_without_running_external_services():
    for mode in ("agent_vector", "agent_graph", "full_agent"):
        assert build_evaluation_agent(mode, top_k=5) is not None


def test_result_keeps_final_answer_and_ragas_contract():
    item = {
        "id": "Q1",
        "query": "What happened?",
        "gold_tools": ["vector", "graph"],
        "gold_chunks": ["gold_1", "gold_2"],
        "gold_evidence_groups": {
            "hop_1": ["gold_1"],
            "hop_2": ["gold_2"],
        },
        "answer_points": ["Reference answer."],
    }
    state = {
        "original_query": item["query"],
        "subqueries": [item["query"]],
        "current_subquery_idx": 0,
        "round": 1,
        "stop_reason": "sufficient",
        "reflection_reason": "enough",
        "chunks_history": [
            {"chunk_id": "gold_1", "text": "First context."},
            {"chunk_id": "gold_2", "text": "Second context."},
        ],
        "tool_call_log": [{
            "round": 0,
            "subquery": item["query"],
            "tool": "vector",
            "query": item["query"],
            "top_k_chunks": 5,
            "n_chunks": 2,
            "status": "ok",
        }],
        "retrieval_trace_history": [],
        "observation_history": [],
        "reflection_history": [{
            "round": 1,
            "subquery": item["query"],
            "sufficient": True,
            "reason": "enough",
            "feedback": "",
            "retry_query": "",
            "stop_reason": "sufficient",
        }],
        "completed_subqueries": [{
            "subquery_idx": 0,
            "subquery": item["query"],
            "stop_reason": "sufficient",
            "reflection_reason": "enough",
            "round": 1,
        }],
        "final_answer": "Grounded answer [1].",
        "citation_map": [{"citation_index": 1, "chunk_id": "gold_1"}],
    }

    detail, ragas = result_from_state(item, "agent_vector", state, 1.25, 5)

    assert detail["final_answer"] == "Grounded answer [1]."
    assert detail["metrics_all_retrieved"]["recall"] == 1.0
    assert detail["metrics_all_retrieved"]["answerable"] == 1
    assert ragas["user_input"] == item["query"]
    assert ragas["response"] == detail["final_answer"]
    assert ragas["retrieved_contexts"] == ["First context.", "Second context."]
    assert ragas["reference"] == "Reference answer."


def test_aggregate_reports_each_mode_independently():
    rows = []
    for mode, hit in (("agent_vector", 0), ("agent_graph", 1)):
        metrics = {
            "hit": hit,
            "recall": float(hit),
            "group_recall": float(hit),
            "answerable": hit,
        }
        rows.append({
            "mode": mode,
            "status": "ok",
            "latency_sec": 1.0,
            "tool_call_count": 1,
            "unique_retrieved_count": 5,
            "metrics_at_k": metrics,
            "metrics_all_retrieved": metrics,
            "metrics_synthesis_context": metrics,
        })

    summary = aggregate_results(rows, ["agent_vector", "agent_graph"])

    assert summary["agent_vector"]["chunk_hit_at_k"] == 0.0
    assert summary["agent_graph"]["chunk_hit_at_k"] == 1.0


def test_checkpoint_round_trip_is_atomic_and_keyed(tmp_path):
    detail = {
        "id": "Q1",
        "mode": "agent_vector",
        "status": "ok",
        "latency_sec": 1.0,
        "tool_call_count": 1,
        "unique_retrieved_count": 1,
        "metrics_at_k": {},
        "metrics_all_retrieved": {},
        "metrics_synthesis_context": {},
    }
    ragas = {
        "id": "Q1",
        "mode": "agent_vector",
        "status": "ok",
    }
    records = {("Q1", "agent_vector"): (detail, ragas)}

    write_checkpoint(
        tmp_path,
        records,
        [("Q1", "agent_vector")],
        ["agent_vector"],
        score_k=5,
    )

    assert load_checkpoint(tmp_path) == records
    assert (tmp_path / "checkpoint.jsonl").exists()
    assert (tmp_path / "progress.json").exists()
    assert list(tmp_path.glob("*.tmp")) == []


def test_legacy_checkpoint_requires_matching_detail_and_ragas(tmp_path):
    (tmp_path / "details.jsonl").write_text(
        json.dumps({"id": "Q1", "mode": "agent_graph", "status": "ok"}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "ragas.jsonl").write_text(
        json.dumps({"id": "Q1", "mode": "agent_graph", "status": "ok"}) + "\n",
        encoding="utf-8",
    )

    records = load_checkpoint(tmp_path)

    assert set(records) == {("Q1", "agent_graph")}


def test_resume_config_rejects_parameter_drift():
    existing = {
        "dataset": "/tmp/questions.yaml",
        "modes": ["agent_graph"],
        "top_k_per_tool_call": 5,
    }
    expected = {
        "dataset": "/tmp/questions.yaml",
        "modes": ["agent_graph"],
        "top_k_per_tool_call": 10,
    }

    try:
        validate_resume_config(existing, expected)
    except ValueError as exc:
        assert "top_k_per_tool_call" in str(exc)
    else:
        raise AssertionError("Resume accepted incompatible parameters")


def test_agent_state_errors_marks_retrieval_and_synthesis_failures():
    state = {
        "retrieval_trace_history": [{
            "tool": "graph",
            "status": "error",
            "error": "network disconnected",
        }],
        "final_answer": (
            "I could not synthesize a grounded final answer from the current evidence."
        ),
    }

    assert agent_state_errors(state) == [
        "graph: network disconnected",
        "synthesis failed",
    ]


def _successful_state(query: str) -> dict:
    return {
        "original_query": query,
        "subqueries": [query],
        "current_subquery_idx": 0,
        "round": 1,
        "stop_reason": "sufficient",
        "reflection_reason": "enough",
        "chunks_history": [{"chunk_id": "gold_1", "text": "Evidence."}],
        "tool_call_log": [{
            "round": 0,
            "subquery": query,
            "tool": "vector",
            "query": query,
            "top_k_chunks": 5,
            "n_chunks": 1,
            "status": "ok",
        }],
        "retrieval_trace_history": [],
        "observation_history": [],
        "reflection_history": [],
        "completed_subqueries": [],
        "final_answer": "Answer [1].",
        "citation_map": [{"citation_index": 1, "chunk_id": "gold_1"}],
    }


def _write_tiny_dataset(path):
    path.write_text(
        yaml.safe_dump({
            "metadata": {"name": "tiny"},
            "queries": [{
                "id": "Q1",
                "query": "Question?",
                "gold_tools": ["vector"],
                "gold_chunks": ["gold_1"],
                "gold_evidence_groups": {"hop_1": ["gold_1"]},
                "answer_points": ["Answer."],
            }],
        }),
        encoding="utf-8",
    )


def test_resume_skips_successful_unit_idempotently(tmp_path, monkeypatch):
    dataset = tmp_path / "dataset.yaml"
    output_root = tmp_path / "results"
    _write_tiny_dataset(dataset)
    calls = []

    monkeypatch.setattr(evaluator, "build_evaluation_agent", lambda mode, top_k: object())
    monkeypatch.setattr(
        evaluator,
        "run_agent",
        lambda graph, query, recursion_limit, verbose_agent: (
            calls.append(query) or _successful_state(query)
        ),
    )
    base_args = [
        "evaluate_finreflectkg_agent.py",
        "--dataset", str(dataset),
        "--output-root", str(output_root),
        "--modes", "agent_vector",
        "--run-name", "resume-test",
    ]

    monkeypatch.setattr(evaluator.sys, "argv", base_args)
    evaluator.main()
    monkeypatch.setattr(evaluator.sys, "argv", [*base_args, "--resume"])
    evaluator.main()

    assert calls == ["Question?"]
    records = load_checkpoint(output_root / "resume-test")
    assert len(records) == 1
    assert records[("Q1", "agent_vector")][0]["status"] == "ok"


def test_resume_retries_error_and_replaces_same_unit(tmp_path, monkeypatch):
    dataset = tmp_path / "dataset.yaml"
    output_root = tmp_path / "results"
    _write_tiny_dataset(dataset)
    attempts = 0

    def flaky_run(graph, query, recursion_limit, verbose_agent):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionError("network disconnected")
        return _successful_state(query)

    monkeypatch.setattr(evaluator, "build_evaluation_agent", lambda mode, top_k: object())
    monkeypatch.setattr(evaluator, "run_agent", flaky_run)
    base_args = [
        "evaluate_finreflectkg_agent.py",
        "--dataset", str(dataset),
        "--output-root", str(output_root),
        "--modes", "agent_vector",
        "--run-name", "retry-test",
    ]

    monkeypatch.setattr(evaluator.sys, "argv", base_args)
    evaluator.main()
    monkeypatch.setattr(evaluator.sys, "argv", [*base_args, "--resume"])
    evaluator.main()

    records = load_checkpoint(output_root / "retry-test")
    assert attempts == 2
    assert len(records) == 1
    assert records[("Q1", "agent_vector")][0]["status"] == "ok"
