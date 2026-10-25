"""Friendly Engine.query facade: readiness, retrieval, Agents, and one synthesis."""

from __future__ import annotations

import re
from time import perf_counter
from threading import Lock
from typing import Any

from ..agents.runtime import AgentConfig, AgentRuntime
from ..config import SDKConfig
from .encoder import QueryEncoder
from .graph import graph_retrieve
from .models import (
    CorpusChangedError,
    CorpusNotReadyError,
    InvalidQueryError,
    LLMExecutionError,
    LLMNotConfiguredError,
    OptionalDependencyError,
    RetrievalBackendError,
    RetrievalConfigError,
    RetrievalMatch,
    RetrievalResult,
    RetrievedChunk,
    RetrievalStatus,
)
from .triple_cache import TripleVectorCache
from .vector import vector_retrieve


_MODES = {
    "tool": {"vector", "graph"},
    "agent": {"none", "task_specific", "deepagent"},
    "output": {"chunks", "answer"},
}
_CITATION = re.compile(r"\[([^\[\]]+)\]")


def validate_query(
    config: SDKConfig,
    question: str,
    *,
    tool: str,
    agent: str,
    output: str,
    top_k: int,
) -> None:
    if not isinstance(question, str) or not question.strip():
        raise InvalidQueryError("question must be a non-empty string")
    for name, value in (("tool", tool), ("agent", agent), ("output", output)):
        if not isinstance(value, str) or value not in _MODES[name]:
            raise InvalidQueryError(
                f"{name} must be one of {sorted(_MODES[name])}"
            )
    if isinstance(top_k, bool) or not isinstance(top_k, int):
        raise InvalidQueryError("top_k must be an integer")
    if not 1 <= top_k <= config.retrieval.max_top_k:
        raise InvalidQueryError(
            f"top_k must be between 1 and {config.retrieval.max_top_k}"
        )
    if agent != "none" and top_k < config.retrieval.agent.max_planned_tasks:
        raise RetrievalConfigError(
            "top_k must allow at least one final chunk per planned Agent task; "
            "lower retrieval.agent.max_planned_tasks or increase top_k"
        )


def query_engine(
    engine,
    question: str,
    *,
    tool: str = "vector",
    agent: str = "none",
    output: str = "chunks",
    top_k: int = 10,
) -> RetrievalResult:
    config: SDKConfig = engine.config
    validate_query(config, question, tool=tool, agent=agent, output=output, top_k=top_k)
    question = question.strip()
    llm = _build_llm(config) if agent != "none" else None
    if agent == "deepagent":
        _check_deepagent_dependency()

    try:
        engine.setup()
    except Exception as exc:
        raise RetrievalBackendError(
            "setup", type(exc).__name__, "database setup or index validation failed"
        ) from exc
    driver = engine._driver
    if driver is None:
        raise RetrievalBackendError(
            "setup", "DriverUnavailable", "the SDK database driver is unavailable"
        )

    revision = _read_ready_revision(driver, config)
    encoder: QueryEncoder = engine._get_query_encoder()
    if agent == "none":
        selected, retrieval_trace = _direct_retrieve(
            driver,
            engine,
            config,
            encoder,
            question,
            tool,
            top_k,
            revision,
        )
        evidence = selected
        trace: dict[str, Any] = {"retrieval": retrieval_trace}
    else:
        evidence, trace = _agent_retrieve(
            driver,
            engine,
            config,
            encoder,
            llm,
            question,
            tool,
            agent,
            top_k,
            revision,
        )

    answer = None
    if output == "answer":
        if not evidence:
            answer = "Do not Answer"
            trace["synthesis"] = {"status": "no_evidence", "llm_calls": 0}
        else:
            if llm is None:
                llm = _build_llm(config)
            answer, synthesis_trace = _synthesize(llm, question, evidence)
            answer, synthesis_trace = _filter_citations(answer, synthesis_trace, evidence)
            trace["synthesis"] = synthesis_trace

    _assert_same_revision(driver, config, revision)
    final_chunks = [
        RetrievedChunk(
            chunk_id=chunk["chunk_id"],
            text=chunk["text"],
            rank=index,
            matches=chunk.get("matches", []),
            entities=chunk.get("entities", []),
            assertions=chunk.get("assertions", []),
        )
        for index, chunk in enumerate(evidence[:top_k], start=1)
    ]
    status = RetrievalStatus.OK if final_chunks else RetrievalStatus.NO_EVIDENCE
    if not final_chunks:
        trace.setdefault("abort_reason", "no_chunks")
    return RetrievalResult(
        status=status,
        question=question,
        tool=tool,
        agent=agent,
        output=output,
        chunks=final_chunks,
        answer=answer,
        corpus_revision=revision,
        trace=trace,
    )


def _read_ready_revision(driver, config: SDKConfig) -> int:
    try:
        with driver.session(database=config.database.name) as session:
            row = session.run(
                "MATCH (m:SDKMeta {key: 'root'}) "
                "RETURN m.owner AS owner, m.search_ready AS search_ready, "
                "m.corpus_revision AS corpus_revision, "
                "m.embedding_fingerprint AS embedding_fingerprint"
            ).single()
    except Exception as exc:
        raise RetrievalBackendError(
            "readiness", type(exc).__name__, "cannot read SDK corpus metadata"
        ) from exc
    if row is None:
        raise CorpusNotReadyError("Run Engine.setup() and ingest text before querying")
    if row["owner"] != config.workspace_id:
        raise CorpusNotReadyError("The selected database belongs to another SDK workspace")
    if row["embedding_fingerprint"] != config.embedding.fingerprint:
        raise CorpusNotReadyError("The configured embedding identity differs from the corpus")
    revision = int(row["corpus_revision"] or 0)
    if not row["search_ready"] or revision < 1:
        raise CorpusNotReadyError(
            "No finalized searchable corpus exists; call Engine.ingest() first"
        )
    return revision


def _assert_same_revision(driver, config: SDKConfig, starting_revision: int) -> None:
    try:
        with driver.session(database=config.database.name) as session:
            row = session.run(
                "MATCH (m:SDKMeta {key: 'root'}) "
                "RETURN m.search_ready AS search_ready, "
                "m.corpus_revision AS corpus_revision"
            ).single()
    except Exception as exc:
        raise RetrievalBackendError(
            "consistency", type(exc).__name__, "cannot recheck corpus metadata"
        ) from exc
    if row is None or not row["search_ready"]:
        raise CorpusChangedError("The corpus became unready during this query")
    if int(row["corpus_revision"] or 0) != starting_revision:
        raise CorpusChangedError("The corpus revision changed during this query")


def _direct_retrieve(
    driver,
    engine,
    config: SDKConfig,
    encoder: QueryEncoder,
    question: str,
    tool: str,
    top_k: int,
    revision: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    started = perf_counter()
    try:
        with driver.session(database=config.database.name) as session:
            if tool == "vector":
                rows, trace = vector_retrieve(
                    session,
                    config,
                    query=question,
                    top_k=top_k,
                    encode=encoder.encode,
                )
            else:
                rows, trace = graph_retrieve(
                    session,
                    config,
                    query=question,
                    top_k=top_k,
                    corpus_revision=revision,
                    encode=encoder.encode,
                    triple_cache=engine._triple_cache,
                    projection_lock=engine._projection_lock,
                )
    except (CorpusChangedError, RetrievalBackendError, OptionalDependencyError):
        raise
    except Exception as exc:
        raise RetrievalBackendError(
            f"{tool}_retrieval", type(exc).__name__, "retrieval query failed"
        ) from exc

    matches = _matches(question, tool, rows)
    trace["latency_ms"] = (perf_counter() - started) * 1000
    trace["matched_chunk_ids"] = [row["chunk_id"] for row in rows]
    for row, match in zip(rows, matches, strict=True):
        row["matches"] = [match.model_dump(mode="python")]
    return rows, trace


def _agent_retrieve(
    driver,
    engine,
    config: SDKConfig,
    encoder: QueryEncoder,
    llm,
    question: str,
    tool: str,
    agent: str,
    top_k: int,
    revision: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    relation_hints = _load_relation_hints(driver, config)
    agent_config = AgentConfig(
        max_planned_tasks=config.retrieval.agent.max_planned_tasks,
        max_attempts_per_task=config.retrieval.agent.max_attempts_per_task,
        max_parallel_tasks=config.retrieval.agent.max_parallel_tasks,
        top_k_chunks=config.retrieval.per_search_k,
        max_synthesis_chunks=top_k,
        max_num_relations=max(1, config.retrieval.agent.max_relation_hints),
    )
    matches_by_id: dict[str, list[RetrievalMatch]] = {}
    evidence_by_id: dict[str, dict[str, Any]] = {}
    searches: list[dict[str, Any]] = []
    failed_retrieval: list[Exception] = []
    capture_lock = Lock()

    def retrieve(*, query: str, top_k_chunks: int) -> list[dict[str, Any]]:
        started = perf_counter()
        search: dict[str, Any] = {
            "query": query,
            "tool": tool,
            "status": "running",
        }
        with capture_lock:
            searches.append(search)
        try:
            with driver.session(database=config.database.name) as session:
                if tool == "vector":
                    rows, _ = vector_retrieve(
                        session,
                        config,
                        query=query,
                        top_k=min(top_k_chunks, config.retrieval.max_top_k),
                        encode=encoder.encode,
                    )
                else:
                    rows, _ = graph_retrieve(
                        session,
                        config,
                        query=query,
                        top_k=min(top_k_chunks, config.retrieval.max_top_k),
                        corpus_revision=revision,
                        encode=encoder.encode,
                        triple_cache=engine._triple_cache,
                        projection_lock=engine._projection_lock,
                    )
            match_models = _matches(query, tool, rows)
            with capture_lock:
                for row, match in zip(rows, match_models, strict=True):
                    row["matches"] = [match.model_dump(mode="python")]
                    evidence_by_id.setdefault(row["chunk_id"], row)
                    matches_by_id.setdefault(row["chunk_id"], []).append(match)
                search.update(
                    status="ok",
                    chunk_ids=[row["chunk_id"] for row in rows],
                    scores=[
                        {"rank": item.rank, "score": item.score, "score_kind": item.score_kind}
                        for item in match_models
                    ],
                )
            return rows
        except Exception as exc:
            error = (
                exc
                if isinstance(exc, (RetrievalBackendError, OptionalDependencyError))
                else RetrievalBackendError(
                    f"{tool}_retrieval", type(exc).__name__, "retrieval query failed"
                )
            )
            with capture_lock:
                failed_retrieval.append(error)
                search.update(status="error", error_type=type(error).__name__)
            if error is exc:
                raise
            raise error from exc
        finally:
            search["latency_ms"] = (perf_counter() - started) * 1000

    runtime = AgentRuntime(
        llm=llm,
        retrievers={tool: retrieve},
        config=agent_config,
        relations=relation_hints,
    )
    try:
        if agent == "task_specific":
            from ..agents.graph import run_agent

            state = run_agent(
                {"original_query": question},
                tool,
                runtime=runtime,
                generate_answer=False,
            )
            selected = state["synthesis_input"]["accepted_chunks"]
            selected_ids = [item["chunk_id"] for item in selected]
            agent_trace = _task_trace(state)
        else:
            from ..agents.deepagent import Deepagent

            state = Deepagent(question, tool, FullAnswer=False, runtime=runtime)
            selected_ids = [item["chunk_id"] for item in state["chunks"]]
            agent_trace = state["retrieval_trace"]
    except Exception as exc:
        if failed_retrieval:
            raise failed_retrieval[-1]
        if isinstance(exc, (OptionalDependencyError, RetrievalBackendError)):
            raise
        raise LLMExecutionError(
            f"{agent} Agent failed ({type(exc).__name__}); inspect the chained exception"
        ) from exc

    final_rows = []
    for chunk_id in dict.fromkeys(selected_ids):
        row = evidence_by_id.get(chunk_id)
        if row is None:
            continue
        final_rows.append(
            {
                **row,
                "matches": [
                    match.model_dump(mode="python")
                    for match in matches_by_id.get(chunk_id, [])
                ],
            }
        )
        if len(final_rows) >= top_k:
            break
    return final_rows, {
        "agent": agent,
        "tool": tool,
        "searches": searches,
        "selected_chunk_ids": [row["chunk_id"] for row in final_rows],
        "controller": agent_trace,
    }


def _load_relation_hints(driver, config: SDKConfig) -> dict[str, str]:
    limit = config.retrieval.agent.max_relation_hints
    if limit == 0:
        return {}
    try:
        with driver.session(database=config.database.name) as session:
            rows = session.run(
                "MATCH (relation:ObservedRelation) "
                "WHERE relation.assertion_count > 0 "
                "RETURN relation.id AS id, relation.description AS description "
                "ORDER BY relation.assertion_count DESC, relation.id LIMIT $limit",
                limit=limit,
            )
            return {row["id"]: row["description"] or row["id"] for row in rows}
    except Exception as exc:
        raise RetrievalBackendError(
            "relation_hints", type(exc).__name__, "cannot read observed relation hints"
        ) from exc


def _build_llm(config: SDKConfig):
    if config.llm is None:
        raise LLMNotConfiguredError(
            "Add an llm section to semigraph.yaml before using an Agent or answer output"
        )
    provider = config.llm.provider.strip().lower().replace("_", "-")
    if provider not in {"openai", "openai-compatible", "openrouter"}:
        raise LLMNotConfiguredError(
            "Use llm.provider='openai', 'openai-compatible', or 'openrouter'"
        )
    if provider in {"openai-compatible", "openrouter"} and not config.llm.base_url:
        raise LLMNotConfiguredError(
            f"LLM provider {provider!r} requires llm.base_url in semigraph.yaml"
        )
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise OptionalDependencyError(
            "Install the ingestion extra to use configured LLM calls: "
            "python -m pip install 'semigraph-sdk[ingestion]'"
        ) from exc
    try:
        return ChatOpenAI(
            model=config.llm.model,
            api_key=config.llm_api_key(),
            base_url=config.llm.base_url,
            temperature=0,
        )
    except Exception as exc:
        raise LLMNotConfiguredError(
            f"Cannot configure the selected LLM ({type(exc).__name__})"
        ) from exc


def _check_deepagent_dependency() -> None:
    try:
        import deepagents  # noqa: F401
    except ImportError as exc:
        raise OptionalDependencyError(
            "Install DeepAgent support with: "
            "python -m pip install 'semigraph-sdk[deepagents]'"
        ) from exc


def _matches(
    query: str, tool: str, rows: list[dict[str, Any]]
) -> list[RetrievalMatch]:
    score_kind = "cosine" if tool == "vector" else "ppr"
    return [
        RetrievalMatch(
            query=query,
            tool=tool,
            rank=int(row["rank"]),
            score=float(row["score"]),
            score_kind=score_kind,
        )
        for row in rows
    ]


def _task_trace(state: dict[str, Any]) -> dict[str, Any]:
    workers = []
    for result in sorted(state.get("worker_results", []), key=lambda row: row["task_index"]):
        attempts = []
        for attempt in result.get("attempts", []):
            item = attempt.model_dump(mode="python") if hasattr(attempt, "model_dump") else dict(attempt)
            attempts.append(
                {
                    key: value
                    for key, value in item.items()
                    if key not in {"chunks", "accepted_chunks", "evidence"}
                }
            )
        workers.append(
            {
                "task_index": result["task_index"],
                "selected_chunk_ids": [
                    item["chunk_id"] for item in result.get("accepted_chunks", [])
                ],
                "attempts": attempts,
                "stop_reason": result.get("stop_reason"),
            }
        )
    return {"workers": workers}


def _synthesize(llm, question: str, evidence: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    from ..agents.nodes import synthesize_node

    runtime = AgentRuntime(
        llm=llm,
        retrievers={"vector": lambda **_: [], "graph": lambda **_: []},
        config=AgentConfig(
            max_planned_tasks=1,
            max_synthesis_chunks=max(1, len(evidence)),
            top_k_chunks=max(1, len(evidence)),
        ),
    )
    try:
        result = synthesize_node(
            {"synthesis_input": {"original_query": question, "accepted_chunks": evidence}},
            runtime=runtime,
        )
    except Exception as exc:
        raise LLMExecutionError(
            f"Answer synthesis failed ({type(exc).__name__}); inspect the chained exception"
        ) from exc

    return result["final_answer"], result["synthesis_trace"]


def _filter_citations(
    answer: str,
    trace: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    """Enforce the public citation contract at the query boundary."""
    valid_ids = {item["chunk_id"] for item in evidence}
    invalid_ids = list(trace.get("invalid_citation_ids", []))

    def keep_valid(match: re.Match[str]) -> str:
        chunk_id = match.group(1)
        if chunk_id in valid_ids:
            return match.group(0)
        invalid_ids.append(chunk_id)
        return ""

    answer = _CITATION.sub(
        keep_valid,
        answer,
    ).strip()
    trace = dict(trace)
    trace["invalid_citation_ids"] = list(dict.fromkeys(invalid_ids))
    trace["cited_chunk_ids"] = [
        item for item in trace.get("cited_chunk_ids", []) if item in valid_ids
    ]
    if invalid_ids:
        trace["citation_status"] = "invalid_removed"
    elif trace["cited_chunk_ids"]:
        trace["citation_status"] = "valid"
    else:
        trace["citation_status"] = "missing" if answer else "not_applicable"
    return answer, trace
