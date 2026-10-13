from __future__ import annotations

from typing import Callable, TypedDict

from semigraph.online.graph_search import trace_graph_search
from semigraph.online.vector_search import trace_vector_search
from semigraph.trace import TraceCallback


class RetrieverResult(TypedDict):
    """Chunks plus a compact, JSON-serializable retrieval trace."""

    chunks: list[dict]
    trace: dict


def _profile(cfg, tool_name: str) -> dict:
    profiles = getattr(cfg, "agent_retrieval", {}) or {}
    profile = dict(profiles.get(tool_name, {}))
    if not profile:
        raise ValueError(f"Missing agent_retrieval.{tool_name} configuration")
    return profile


def _chunk_ids(chunks: list[dict], limit: int = 20) -> list[str]:
    return [
        str(chunk["chunk_id"])
        for chunk in chunks[:limit]
        if chunk.get("chunk_id")
    ]


def _compact_items(
    items: list[dict],
    keys: tuple[str, ...],
    limit: int = 20,
) -> list[dict]:
    return [
        {key: item.get(key) for key in keys if item.get(key) is not None}
        for item in items[:limit]
        if isinstance(item, dict)
    ]


def _compact_chunk_ranking(chunks: list[dict], limit: int = 20) -> list[dict]:
    return _compact_items(
        chunks,
        (
            "chunk_id",
            "ticker",
            "fiscal_year",
            "section",
            "score",
            "original_rank",
            "rerank_score",
        ),
        limit=limit,
    )


def _compact_vector_trace(
    trace: dict,
    top_k_chunks: int,
    vector_index: str = "chunk_embedding",
) -> dict:
    candidates = list(trace.get("raw_chunk_candidates") or [])
    reranked = list(trace.get("reranked_chunks") or [])
    chunks = list(trace.get("chunks") or [])
    return {
        "retriever": "vector",
        "profile": "phase_t",
        "parameters": {
            "top_k_chunks": top_k_chunks,
            "candidate_pool_k": trace.get("candidate_pool_k"),
            "vector_index": vector_index,
        },
        "candidate_count": len(candidates),
        "candidate_ranking": _compact_chunk_ranking(candidates),
        "reranked_ranking": _compact_chunk_ranking(reranked),
        "returned_chunk_ids": _chunk_ids(chunks),
        "reranker": dict(trace.get("reranker_trace") or {}),
    }


def _compact_graph_trace(trace: dict) -> dict:
    seeds = list(trace.get("seeds") or [])
    ppr_entities = list(trace.get("ppr_entities") or [])
    candidates = list(trace.get("raw_chunk_candidates") or [])
    reranked = list(trace.get("reranked_chunks") or [])
    chunks = list(trace.get("chunks") or [])
    triple_filter = dict(trace.get("triple_filter_trace") or {})

    return {
        "retriever": "graph",
        "profile": "phase_t",
        "parameters": {
            "top_k_chunks": trace.get("top_k_chunks"),
            "top_k_entities": trace.get("top_k_entities"),
            "top_k_triples": trace.get("top_k_triples"),
            "top_k_chunk_seeds": trace.get("top_k_chunk_seeds"),
            "chunk_seed_vector_index": trace.get("chunk_seed_vector_index"),
            "damping": trace.get("damping"),
            "use_expansion": trace.get("use_expansion"),
            "seed_mode": trace.get("seed_mode"),
            "candidate_pool_k": trace.get("candidate_pool_k"),
            "ppr_seed_weight_mode": trace.get("ppr_seed_weight_mode"),
            "triple_filter": trace.get("graph_triple_filter"),
        },
        "effective_query": trace.get("effective_query"),
        "abort_reason": trace.get("abort_reason"),
        "seed_count": len(seeds),
        "seeds": _compact_items(
            seeds,
            ("chunk_id", "name", "type", "similarity", "specificity"),
        ),
        "triple_filter": {
            "reason": triple_filter.get("reason"),
            "fallback": triple_filter.get("fallback"),
            "attempts": triple_filter.get("attempts"),
            "parse_error": triple_filter.get("parse_error"),
            "filter_latency_sec": triple_filter.get("filter_latency_sec"),
            "selected_candidate_ids": triple_filter.get(
                "selected_candidate_ids", []
            ),
            "rejected_candidate_ids": triple_filter.get(
                "rejected_candidate_ids", []
            ),
            "selected_triples": _compact_items(
                list(triple_filter.get("candidates_after_filter") or []),
                ("candidate_id", "head", "relation", "tail", "similarity"),
            ),
        },
        "triple_candidates": _compact_items(
            list(
                triple_filter.get("candidates_before_filter")
                or triple_filter.get("candidates_after_filter")
                or []
            ),
            ("candidate_id", "head", "relation", "tail", "similarity"),
        ),
        "ppr_entity_count": len(ppr_entities),
        "ppr_entities": _compact_items(
            ppr_entities,
            ("name", "type", "score"),
        ),
        "projection": dict(trace.get("projection") or {}),
        "candidate_count": len(candidates),
        "candidate_ranking": _compact_chunk_ranking(candidates),
        "reranked_ranking": _compact_chunk_ranking(reranked),
        "returned_chunk_ids": _chunk_ids(chunks),
        "reranker": dict(trace.get("reranker_trace") or {}),
    }


def agent_vector_search(
    query: str,
    top_k_chunks: int,
    cfg,
    trace_callback: TraceCallback | None = None,
) -> RetrieverResult:
    """Run vector retrieval with the Phase T profile used by the agent."""
    profile = _profile(cfg, "vector")
    vector_index = str(profile.get("vector_index", "chunk_embedding"))
    trace = trace_vector_search(
        query=query,
        top_k_chunks=top_k_chunks,
        candidate_pool_k=int(profile["candidate_pool_k"]),
        cfg=cfg,
        vector_index=vector_index,
        trace_callback=trace_callback,
    )
    return {
        "chunks": trace["chunks"],
        "trace": _compact_vector_trace(
            trace,
            top_k_chunks=top_k_chunks,
            vector_index=vector_index,
        ),
    }


def agent_graph_search(
    query: str,
    top_k_chunks: int,
    cfg,
    trace_callback: TraceCallback | None = None,
) -> RetrieverResult:
    """Run graph retrieval with the winning Phase T profile used by the agent."""
    profile = _profile(cfg, "graph")
    trace = trace_graph_search(
        query=query,
        top_k_chunks=top_k_chunks,
        top_k_entities=int(profile["top_k_entities"]),
        top_k_triples=int(profile["top_k_triples"]),
        top_k_chunk_seeds=int(profile.get("top_k_chunk_seeds", 5)),
        chunk_seed_vector_index=str(
            profile.get("chunk_seed_vector_index", "chunk_embedding")
        ),
        damping=float(profile["damping"]),
        use_expansion=bool(profile["use_expansion"]),
        seed_mode=str(profile["seed_mode"]),
        candidate_pool_k=int(profile["candidate_pool_k"]),
        ppr_seed_weight_mode=str(profile["ppr_seed_weight_mode"]),
        graph_triple_filter=str(profile["triple_filter"]),
        cfg=cfg,
        trace_callback=trace_callback,
    )
    return {"chunks": trace["chunks"], "trace": _compact_graph_trace(trace)}


# Every Agent Retriever returns the same chunks-plus-trace envelope.
RETRIEVERS: dict[str, Callable[..., RetrieverResult]] = {
    "vector": agent_vector_search,
    "graph": agent_graph_search,
}
