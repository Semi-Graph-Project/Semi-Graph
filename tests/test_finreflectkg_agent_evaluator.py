"""Unit tests for the FinReflectKG Agent evaluator."""

import json
import pytest

import yaml

from scripts import evaluate_finreflectkg_agent as evaluator
from scripts.evaluate_finreflectkg_agent import (
    MODES,
    agent_state_errors,
    aggregate_results,
    build_evaluation_agent,
    evidence_groups,
    load_checkpoint,
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
from semigraph.agent.state import AgentState


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


def test_evaluation_modes_share_production_builder_with_only_tool_lock(monkeypatch):
    calls = []

    def fake_build_agent(**kwargs):
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(evaluator, "build_agent", fake_build_agent)

    for mode in ("agent_vector", "agent_graph", "full_agent"):
        build_evaluation_agent(mode, top_k=7)

    assert calls == [
        {"locked_tool": "vector", "top_k": 7},
        {"locked_tool": "graph", "top_k": 7},
        {"locked_tool": None, "top_k": 7},
    ]


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
        "stop_reason": "assessment_error",
        "tasks": [{"task_id": "T1"}, {"task_id": "T2"}],
        "completed_tasks": [
            {
                "task_id": "T1",
                "sufficient": True,
                "stop_reason": "sufficient",
            },
            {
                "task_id": "T2",
                "sufficient": False,
                "stop_reason": "assessment_error",
            },
        ],
        "attempts": [
            {
                "attempt_id": "T1-A1",
                "task_id": "T1",
                "action": {
                    "tool": "vector",
                    "query": item["query"],
                    "top_k_chunks": 5,
                },
                "retrieval_status": "ok",
                "chunks": [
                    {"chunk_id": "gold_1", "text": "First context."},
                    {"chunk_id": "noise", "text": "Rejected context."},
                ],
                "retrieval_trace": {
                    "status": "ok",
                    "technical_tries": [{"latency_sec": 0.2}],
                },
                "assessment": {
                    "status": "valid",
                    "output": {
                        "accepted_chunk_ids": ["gold_1"],
                        "covered_requirement_ids": ["R1"],
                        "decision": "accept",
                    },
                    "controller": {"decision": "accept"},
                    "trace": {"llm_calls": 1, "latency_sec": 0.3},
                },
            },
            {
                "attempt_id": "T2-A1",
                "task_id": "T2",
                "action": {
                    "tool": "graph",
                    "query": "second evidence query",
                    "top_k_chunks": 5,
                },
                "retrieval_status": "ok",
                "chunks": [{
                    "chunk_id": "gold_2",
                    "text": "Second context.",
                }],
                "retrieval_trace": {
                    "status": "ok",
                    "technical_tries": [{"latency_sec": 0.4}],
                },
                "assessment": {
                    "status": "fail_open",
                    "output": None,
                    "controller": {"decision": "stop"},
                    "trace": {"llm_calls": 2, "latency_sec": 0.5},
                },
            },
        ],
        "plan_trace": {"status": "ok", "llm_calls": 1, "latency_sec": 0.1},
        "synthesis_trace": {
            "status": "ok",
            "llm_calls": 1,
            "latency_sec": 0.6,
        },
        "final_answer": "Grounded answer [1].",
        "citation_map": [{"citation_index": 1, "chunk_id": "gold_1"}],
    }

    detail, ragas = result_from_state(item, "agent_vector", state, 2.5, 5)

    assert detail["final_answer"] == "Grounded answer [1]."
    assert detail["metrics_all_retrieved"]["recall"] == 1.0
    assert detail["metrics_all_retrieved"]["answerable"] == 1
    assert detail["returned_chunk_ids"] == ["gold_1", "noise", "gold_2"]
    assert detail["evidence_pool_chunk_ids"] == ["gold_1", "noise", "gold_2"]
    assert detail["synthesis_chunk_ids"] == ["gold_1", "noise", "gold_2"]
    assert detail["stop_reason"] == "assessment_error"
    assert detail["completed_tasks"][-1]["stop_reason"] == "assessment_error"
    assert detail["retrieval_trace_history"][1]["attempt_id"] == "T2-A1"
    assert detail["assessment_trace_history"][1]["status"] == "fail_open"
    assert detail["orchestration_llm_calls"] == 5
    assert detail["stage_summary"] == {
        "llm_calls": {
            "plan_route": 1,
            "assess": 3,
            "synthesize": 1,
            "orchestration_total": 5,
        },
        "latency_sec": {
            "plan_route": 0.1,
            "retrieval": 0.6,
            "assess": 0.8,
            "synthesize": 0.6,
            "recorded_total": 2.1,
            "unattributed": 0.4,
        },
    }
    assert ragas["user_input"] == item["query"]
    assert ragas["response"] == detail["final_answer"]
    assert ragas["retrieved_contexts"] == [
        "First context.",
        "Rejected context.",
        "Second context.",
    ]
    assert ragas["reference"] == "Reference answer."
    assert set(ragas) == {
        "id",
        "mode",
        "user_input",
        "response",
        "retrieved_contexts",
        "reference",
        "retrieved_context_ids",
        "reference_context_ids",
        "status",
    }


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
            "orchestration_llm_calls": 3,
            "unique_retrieved_count": 5,
            "metrics_at_k": metrics,
            "metrics_all_retrieved": metrics,
            "metrics_synthesis_context": metrics,
        })

    summary = aggregate_results(rows, ["agent_vector", "agent_graph"])

    assert summary["agent_vector"]["chunk_hit_at_k"] == 0.0
    assert summary["agent_graph"]["chunk_hit_at_k"] == 1.0
    assert summary["agent_graph"]["avg_orchestration_llm_calls"] == 3.0


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


def test_resume_config_requires_four_node_harness_identity():
    with pytest.raises(ValueError, match="agent_harness"):
        validate_resume_config(
            {"dataset": "/tmp/questions.yaml"},
            {
                "agent_harness": "four_node_v1",
                "dataset": "/tmp/questions.yaml",
            },
        )


def test_agent_state_errors_marks_retrieval_and_synthesis_failures():
    state = {
        "attempts": [{
            "action": {"tool": "graph"},
            "retrieval_status": "tool_error",
            "retrieval_trace": {"error_type": "ConnectionError"},
        }],
        "synthesis_trace": {"status": "provider_error"},
        "final_answer": (
            "I could not synthesize a grounded final answer from the current evidence."
        ),
    }

    assert agent_state_errors(state) == [
        "graph: ConnectionError",
        "synthesis failed",
    ]


def _successful_state(query: str) -> dict:
    return {
        "original_query": query,
        "stop_reason": "sufficient",
        "tasks": [{"task_id": "T1"}],
        "completed_tasks": [{
            "task_id": "T1",
            "sufficient": True,
            "stop_reason": "sufficient",
        }],
        "attempts": [{
            "attempt_id": "T1-A1",
            "task_id": "T1",
            "action": {"tool": "vector", "query": query, "top_k_chunks": 5},
            "retrieval_status": "ok",
            "chunks": [{"chunk_id": "gold_1", "text": "Evidence."}],
            "retrieval_trace": {},
            "assessment": {
                "status": "valid",
                "output": {
                    "accepted_chunk_ids": ["gold_1"],
                    "covered_requirement_ids": ["R1"],
                    "decision": "accept",
                },
            },
        }],
        "plan_trace": {"status": "ok"},
        "synthesis_trace": {"status": "ok"},
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

@pytest.mark.parametrize("mode", MODES)
def test_all_evaluation_modes_compile_without_running_external_services(mode):
    graph = build_evaluation_agent(mode, top_k=5)

    assert graph is not None


def test_agent_state_declares_plan_route_fields():
    expected_fields = {
        "tasks",
        "current_task_index",
        "current_action",
        "plan_trace",
    }

    assert expected_fields <= set(AgentState.__annotations__)
