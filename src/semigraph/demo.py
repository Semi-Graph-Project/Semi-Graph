"""Shared contracts and backend selection for the Streamlit comparison demo."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from semigraph.agent import nodes
from semigraph.agent import tools as agent_tools
from semigraph.agent.graph import build_agent
from semigraph.agent.ledger import retrieval_traces
from semigraph.config import Config, get_config
from semigraph.trace import TRACE_STORE, TraceCallback, notify_trace


ComparisonStatus = Literal["waiting", "running", "complete", "error"]


class ComparisonMode(str, Enum):
    VECTOR = "vector"
    GRAPH = "graph"
    AGENT_VECTOR = "agent_vector"
    AGENT_GRAPH = "agent_graph"


COMPARISON_MODES: tuple[str, ...] = tuple(mode.value for mode in ComparisonMode)


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
    trace: list[dict[str, Any]] = field(default_factory=list)
    latency_sec: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable result for Streamlit and tests."""
        return asdict(self)


def get_backend_corpora() -> tuple[BackendCorpus, ...]:
    """Return the immutable corpus choices shown by the UI."""
    return BACKEND_CORPORA


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
    config.neo4j_uri = selected.neo4j_uri
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
            "requirements": [{
                "requirement_id": f"{task_id}-R1",
                "description": query,
            }],
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
                "output": {"accepted_chunk_ids": chunk_ids},
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
        trace=trace,
        latency_sec=round(latency_sec, 3),
        error=str(error_type) if error_type else None,
    )


def _agent_result(
    result: dict,
    trace: list[dict[str, Any]],
    latency_sec: float,
) -> ComparisonResult:
    attempts = list(result.get("attempts") or [])
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
            synthesis = nodes.synthesize_attempts_node(
                _direct_synthesis_state(
                    clean_query,
                    mode_value,
                    list(retrieved.get("chunks") or []),
                    dict(retrieved.get("trace") or {}),
                ),
                cfg=cfg,
            )
            result = _synthesis_result(
                synthesis,
                trace,
                perf_counter() - started_at,
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

        locked_tool = (
            "vector"
            if selected_mode is ComparisonMode.AGENT_VECTOR
            else "graph"
        )
        agent = build_agent(
            locked_tool=locked_tool,
            top_k=effective_top_k,
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
