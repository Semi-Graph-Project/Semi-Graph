"""Shared contracts and backend selection for the Streamlit comparison demo."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

import yaml

from semigraph.agent import nodes
from semigraph.agent import tools as agent_tools
from semigraph.agent.graph import build_agent
from semigraph.agent.ledger import retrieval_traces, select_synthesis_chunks
from semigraph.config import Config, get_config
from semigraph.trace import TRACE_STORE, TraceCallback, notify_trace


ComparisonStatus = Literal[
    "waiting",
    "running",
    "complete",
    "error",
    "timeout",
]
ComparisonSource = Literal["live", "replay"]


class ComparisonMode(str, Enum):
    VECTOR = "vector"
    GRAPH = "graph"
    AGENT_VECTOR = "agent_vector"
    AGENT_GRAPH = "agent_graph"


COMPARISON_MODES: tuple[str, ...] = tuple(mode.value for mode in ComparisonMode)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HUMAN_VERIFY_ROOT = PROJECT_ROOT / "benchmark" / "human_verify_2"
FROZEN_REPLAY_FILES = {
    ComparisonMode.VECTOR.value: HUMAN_VERIFY_ROOT
    / "controlled_vector_sox_smoke50_vector_first50_full_answer.yaml",
    ComparisonMode.GRAPH.value: HUMAN_VERIFY_ROOT
    / "controlled_graph_sox_smoke50_cross_enc_llm_full_answer.yaml",
    ComparisonMode.AGENT_VECTOR.value: HUMAN_VERIFY_ROOT
    / "controlled_agent_vector_sox_smoke50_v1_full_answer.yaml",
    ComparisonMode.AGENT_GRAPH.value: HUMAN_VERIFY_ROOT
    / "controlled_agent_graph_sox_smoke50_v1_full_answer.yaml",
}


@dataclass(frozen=True, slots=True)
class BackendCorpus:
    """A user-selectable Neo4j corpus without exposing credentials."""

    key: str
    label: str
    description: str
    neo4j_uri: str
    port: int
    vector_index: str


BACKEND_CORPORA: tuple[BackendCorpus, ...] = (
    BackendCorpus(
        key="benchmark",
        label="Benchmark (7690)",
        description="Controlled retrieval benchmark backend",
        neo4j_uri="bolt://localhost:7690",
        port=7690,
        vector_index="gold_chunk_embedding",
    ),
    BackendCorpus(
        key="production",
        label="Production (7687)",
        description="Main production Neo4j backend",
        neo4j_uri="bolt://localhost:7687",
        port=7687,
        vector_index="chunk_embedding",
    ),
)


@dataclass(slots=True)
class ComparisonResult:
    """One normalized result that any comparison panel can render."""

    status: ComparisonStatus = "waiting"
    answer: str = ""
    citations: list[dict[str, Any]] = field(default_factory=list)
    synthesis_chunks: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    latency_sec: float | None = None
    error: str | None = None
    source: ComparisonSource = "live"

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable result for Streamlit and tests."""
        return asdict(self)


def get_backend_corpora() -> tuple[BackendCorpus, ...]:
    """Return the immutable corpus choices shown by the UI."""
    return BACKEND_CORPORA


@lru_cache(maxsize=1)
def _frozen_replay_rows() -> dict[str, dict[str, dict[str, Any]]]:
    """Load the four frozen Human Verify runs once per process."""
    runs = {}
    for mode, path in FROZEN_REPLAY_FILES.items():
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        runs[mode] = {
            str(row["id"]): row
            for row in payload.get("results", [])
            if isinstance(row, dict) and row.get("id")
        }
    return runs


def get_frozen_replay_queries() -> tuple[tuple[str, str], ...]:
    """Return query IDs and text shared by all four frozen runs."""
    rows = _frozen_replay_rows()
    shared_ids = set.intersection(
        *(set(mode_rows) for mode_rows in rows.values())
    )
    reference = rows[ComparisonMode.AGENT_GRAPH.value]
    return tuple(
        (query_id, str(reference[query_id].get("query") or ""))
        for query_id in reference
        if query_id in shared_ids
    )


def load_frozen_replay(
    query_id: str,
) -> tuple[str, dict[str, ComparisonResult]]:
    """Load one frozen four-way comparison without calling a backend."""
    rows = _frozen_replay_rows()
    if not all(query_id in mode_rows for mode_rows in rows.values()):
        raise ValueError(f"Unknown frozen replay query: {query_id}")

    query = str(rows[ComparisonMode.AGENT_GRAPH.value][query_id]["query"])
    results = {}
    for mode, mode_rows in rows.items():
        row = mode_rows[query_id]
        synthesis_trace = dict(row.get("synthesis_trace") or {})
        cited_ids = synthesis_trace.get("cited_chunk_ids") or []
        selected_ids = synthesis_trace.get("selected_chunk_ids") or []
        if not selected_ids:
            selected_ids = [
                chunk_id
                for chunk_ids in (
                    synthesis_trace.get("selected_chunk_ids_by_task") or {}
                ).values()
                for chunk_id in chunk_ids
            ]
        selection_recorded = bool(selected_ids)
        if not selected_ids:
            selected_ids = row.get("top_chunk_ids") or []
        if isinstance(selected_ids, str):
            selected_ids = [selected_ids]
        elif not isinstance(selected_ids, list):
            selected_ids = []
        trace = [{
            "stage": "replay",
            "status": "complete",
            "message": "Loaded a frozen Human Verify result",
            "details": {
                "query_id": query_id,
                "retrieval_hit": row.get("hit"),
                "retrieval_recall": row.get("recall"),
                "reciprocal_rank": row.get("reciprocal_rank"),
            },
        }]
        if synthesis_trace:
            trace.append({"stage": "synthesis", **synthesis_trace})

        results[mode] = ComparisonResult(
            status="complete",
            answer=str(row.get("final_answer") or "No answer returned."),
            citations=[{"chunk_id": chunk_id} for chunk_id in cited_ids],
            synthesis_chunks=[
                {
                    "chunk_id": chunk_id,
                    "text": None,
                    "selection_recorded": selection_recorded,
                }
                for chunk_id in selected_ids
                if chunk_id
            ],
            trace=trace,
            latency_sec=round(
                float(row.get("total_latency_ms") or 0) / 1000,
                3,
            ),
            source="replay",
        )
    return query, results


def get_backend_corpus(corpus: str | BackendCorpus) -> BackendCorpus:
    """Resolve a corpus key or descriptor and reject unknown choices."""
    if isinstance(corpus, BackendCorpus):
        return corpus

    for candidate in BACKEND_CORPORA:
        if candidate.key == corpus:
            return candidate
    valid = ", ".join(candidate.key for candidate in BACKEND_CORPORA)
    raise ValueError(f"Unknown backend corpus {corpus!r}; expected one of: {valid}")


def get_backend_config(
    corpus: str | BackendCorpus,
    base_config: Config | None = None,
) -> Config:
    """Return an isolated Config pointed at the selected Neo4j corpus.

    A deep copy keeps mutable retrieval settings isolated between comparison
    panels. The cached process-wide Config and environment variables are never
    mutated, so switching the dropdown cannot redirect another in-flight run.
    """
    selected = get_backend_corpus(corpus)
    config = deepcopy(base_config if base_config is not None else get_config())
    config.neo4j_uri = {
        "benchmark": config.controlled_neo4j_uri,
        "production": config.production_neo4j_uri,
    }[selected.key]
    # The two Neo4j corpora expose the same retrieval contract with different
    # physical index names. Keep the mapping at the corpus boundary so every
    # runner (Vector and Graph seed retrieval) uses the selected backend's
    # index without mutating the process-wide cached config.
    config.agent_retrieval.setdefault("vector", {})[
        "vector_index"
    ] = selected.vector_index
    config.agent_retrieval.setdefault("graph", {})[
        "chunk_seed_vector_index"
    ] = selected.vector_index
    return config


def _direct_synthesis_state(
    query: str,
    tool: str,
    chunks: list[dict],
    retrieval_trace: dict,
) -> dict:
    """Adapt one direct retrieval into the Agent synthesis contract."""
    task_id = "T1"
    chunk_ids = [
        str(chunk["chunk_id"])
        for chunk in chunks
        if chunk.get("chunk_id")
    ]
    action = {
        "tool": tool,
        "query": query,
        "top_k_chunks": len(chunks),
    }
    return {
        "original_query": query,
        "tasks": [{
            "task_id": task_id,
            "query": query,
            "requirement": {
                "requirement_id": f"{task_id}-R1",
                "description": query,
            },
            "initial_action": action,
        }],
        "attempts": [{
            "attempt_id": f"{task_id}-A1",
            "task_id": task_id,
            "action": action,
            "retrieval_status": "ok",
            "chunks": chunks,
            "retrieval_trace": retrieval_trace,
            "assessment": {
                "status": "valid",
                "output": {
                    "accepted_chunk_ids": chunk_ids,
                    "requirement_covered": bool(chunk_ids),
                },
            },
        }],
        "completed_tasks": [{
            "task_id": task_id,
            "sufficient": True,
            "stop_reason": "direct_retrieval",
        }],
    }


def _synthesis_result(
    synthesis: dict,
    trace: list[dict[str, Any]],
    latency_sec: float,
    synthesis_chunks: list[dict[str, Any]],
) -> ComparisonResult:
    synthesis_trace = dict(synthesis.get("synthesis_trace") or {})
    status = synthesis_trace.get("status")
    result_status: ComparisonStatus = (
        "complete" if status in {"ok", "no_evidence"} else "error"
    )
    error_type = synthesis_trace.get("error_type")
    trace.append({
        "stage": "synthesis",
        **synthesis_trace,
    })
    return ComparisonResult(
        status=result_status,
        answer=str(synthesis.get("final_answer") or ""),
        citations=list(synthesis.get("citation_map") or []),
        synthesis_chunks=synthesis_chunks,
        trace=trace,
        latency_sec=round(latency_sec, 3),
        error=str(error_type) if error_type else None,
    )


def _agent_result(
    result: dict,
    trace: list[dict[str, Any]],
    latency_sec: float,
    max_synthesis_chunks: int,
) -> ComparisonResult:
    attempts = list(result.get("attempts") or [])
    synthesis_chunks = select_synthesis_chunks(
        attempts,
        max_total=max_synthesis_chunks,
    )
    plan_trace = result.get("plan_trace") or {}
    synthesis_trace = result.get("synthesis_trace") or {}
    if plan_trace:
        trace.append({"stage": "plan", **plan_trace})
    trace.extend(
        {"stage": "retrieval", **retrieval_trace}
        for retrieval_trace in retrieval_traces(attempts)
    )
    if synthesis_trace:
        trace.append({"stage": "synthesis", **synthesis_trace})

    plan_error = plan_trace.get("status") == "error"
    synthesis_status = synthesis_trace.get("status")
    has_error = plan_error or synthesis_status == "provider_error"
    error_type = synthesis_trace.get("error_type")
    if plan_error and not error_type:
        error_type = plan_trace.get("fallback_source") or "plan_error"
    return ComparisonResult(
        status="error" if has_error else "complete",
        answer=str(result.get("final_answer") or ""),
        citations=list(result.get("citation_map") or []),
        synthesis_chunks=synthesis_chunks,
        trace=trace,
        latency_sec=round(latency_sec, 3),
        error=str(error_type) if error_type else None,
    )


def run_comparison(
    mode: ComparisonMode | str,
    query: str,
    corpus: str | BackendCorpus,
    top_k: int | None = None,
    recursion_limit: int = 50,
    trace_callback: TraceCallback | None = None,
    run_id: str | None = None,
) -> ComparisonResult:
    """Run one of the four controlled comparison configurations."""
    started_at = perf_counter()
    active_run_id = run_id or uuid4().hex
    trace_started = False
    mode_value = mode.value if isinstance(mode, ComparisonMode) else str(mode)

    def emit(event: dict[str, Any], message: str | None = None) -> None:
        payload = dict(event)
        if message:
            payload["message"] = message
        stored_event = TRACE_STORE.emit(active_run_id, payload)
        notify_trace(trace_callback, stored_event)

    def finish(result: ComparisonResult) -> ComparisonResult:
        document = TRACE_STORE.finish(active_run_id, result.status)
        result.trace = list(document["events"])
        return result

    try:
        try:
            selected_mode = ComparisonMode(mode)
        except (TypeError, ValueError):
            raise ValueError(f"Unknown comparison mode: {mode!r}") from None
        mode_value = selected_mode.value
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must not be empty")
        if top_k is not None and top_k < 1:
            raise ValueError("top_k must be positive")
        if recursion_limit < 1:
            raise ValueError("recursion_limit must be positive")

        selected = get_backend_corpus(corpus)
        cfg = get_backend_config(selected)
        effective_top_k = (
            top_k
            if top_k is not None
            else cfg.agent_max_synthesis_chunks
        )
        TRACE_STORE.start(
            active_run_id,
            mode=mode_value,
            query=query.strip(),
            corpus=selected.key,
        )
        trace_started = True
        trace: list[dict[str, Any]] = [{
            "stage": "config",
            "corpus": selected.key,
        }]
        emit(
            trace[-1],
            "Loaded the selected corpus configuration",
        )
        clean_query = query.strip()

        if selected_mode in {ComparisonMode.VECTOR, ComparisonMode.GRAPH}:
            retriever = (
                agent_tools.agent_vector_search
                if selected_mode is ComparisonMode.VECTOR
                else agent_tools.agent_graph_search
            )
            emit(
                {
                    "stage": "retrieval",
                    "status": "running",
                    "retriever": mode_value,
                },
                f"Searching evidence with {mode_value} retrieval",
            )
            retrieved = retriever(
                clean_query,
                effective_top_k,
                cfg,
                trace_callback=emit,
            )
            retrieval_event = {
                "stage": "retrieval",
                **dict(retrieved.get("trace") or {}),
            }
            trace.append(retrieval_event)
            emit(
                {
                    "stage": "retrieval_summary",
                    "status": "complete",
                    "retriever": mode,
                    "details": dict(retrieved.get("trace") or {}),
                },
                f"Retrieved {len(retrieved.get('chunks') or [])} evidence chunks",
            )
            emit(
                {
                    "stage": "synthesis",
                    "status": "running",
                },
                "Synthesizing a grounded answer from the evidence",
            )
            synthesis_state = _direct_synthesis_state(
                clean_query,
                mode_value,
                list(retrieved.get("chunks") or []),
                dict(retrieved.get("trace") or {}),
            )
            synthesis = nodes.synthesize_attempts_node(
                synthesis_state,
                cfg=cfg,
            )
            synthesis_chunks = select_synthesis_chunks(
                synthesis_state["attempts"],
                max_total=cfg.agent_max_synthesis_chunks,
            )
            result = _synthesis_result(
                synthesis,
                trace,
                perf_counter() - started_at,
                synthesis_chunks,
            )
            synthesis_event = trace[-1]
            emit(
                {
                    **synthesis_event,
                    "details": {
                        key: value
                        for key, value in synthesis_event.items()
                        if key != "stage"
                    },
                },
                "Finished answer synthesis",
            )
            return finish(result)

        tool = (
            "vector"
            if selected_mode is ComparisonMode.AGENT_VECTOR
            else "graph"
        )
        agent = build_agent(
            tool=tool,
            cfg=cfg,
            trace_callback=emit,
        )
        result = agent.invoke(
            {"original_query": clean_query},
            config={"recursion_limit": recursion_limit},
        )
        normalized_result = _agent_result(
            result,
            trace,
            perf_counter() - started_at,
            cfg.agent_max_synthesis_chunks,
        )
        return finish(normalized_result)
    except Exception as exc:
        if not trace_started:
            TRACE_STORE.start(
                active_run_id,
                mode=mode_value,
                query=str(query),
                corpus=(
                    corpus.key
                    if isinstance(corpus, BackendCorpus)
                    else str(corpus)
                ),
            )
            trace_started = True
        error_event = {
            "stage": "runner",
            "status": "error",
            "error_type": type(exc).__name__,
        }
        emit(error_event, "Runner stopped with an error")
        return finish(ComparisonResult(
            status="error",
            latency_sec=round(perf_counter() - started_at, 3),
            error=f"{type(exc).__name__}: {exc}",
        ))
