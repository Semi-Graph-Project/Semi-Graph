from __future__ import annotations

from typing import Callable, TypedDict

from semigraph.online.financial_search import financial_search
from semigraph.online.graph_search import trace_graph_search
from semigraph.online.hybrid_search import hybrid_search
from semigraph.online.news_search import news_search
from semigraph.online.vector_search import trace_vector_search


DEFAULT_TOP_K = 5


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


def _compact_vector_trace(trace: dict, top_k_chunks: int) -> dict:
    candidates = list(trace.get("raw_chunk_candidates") or [])
    reranked = list(trace.get("reranked_chunks") or [])
    chunks = list(trace.get("chunks") or [])
    return {
        "retriever": "vector",
        "profile": "phase_t",
        "parameters": {
            "top_k_chunks": top_k_chunks,
            "candidate_pool_k": trace.get("candidate_pool_k"),
            "final_rerank": trace.get("final_rerank"),
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
            "rerank_mode": trace.get("rerank_mode"),
            "candidate_pool_k": trace.get("candidate_pool_k"),
            "final_rerank": trace.get("final_rerank"),
            "ppr_seed_weight_mode": trace.get("ppr_seed_weight_mode"),
            "ppr_graph_mode": trace.get("ppr_graph_mode"),
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


def agent_vector_search(query: str, top_k_chunks: int, cfg) -> RetrieverResult:
    """Run vector retrieval with the Phase T profile used by the agent."""
    profile = _profile(cfg, "vector")
    trace = trace_vector_search(
        query=query,
        top_k_chunks=top_k_chunks,
        candidate_pool_k=int(profile["candidate_pool_k"]),
        final_rerank=str(profile["final_rerank"]),
        cfg=cfg,
    )
    return {
        "chunks": trace["chunks"],
        "trace": _compact_vector_trace(trace, top_k_chunks=top_k_chunks),
    }


def agent_graph_search(query: str, top_k_chunks: int, cfg) -> RetrieverResult:
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
        rerank_mode=str(profile["rerank_mode"]),
        candidate_pool_k=int(profile["candidate_pool_k"]),
        final_rerank=str(profile["final_rerank"]),
        ppr_seed_weight_mode=str(profile["ppr_seed_weight_mode"]),
        ppr_graph_mode=str(profile["ppr_graph_mode"]),
        graph_triple_filter=str(profile["triple_filter"]),
        cfg=cfg,
    )
    return {"chunks": trace["chunks"], "trace": _compact_graph_trace(trace)}


def _compact_financial_trace(
    trace: dict,
    chunks: list[dict],
    *,
    top_k_chunks: int,
) -> dict:
    """Keep financial lineage useful for evaluation without copying chunks."""

    compact = {
        "retriever": "financial",
        "profile": trace.get("profile", "postgresql_typed_v1"),
        "parameters": {
            "top_k_chunks": top_k_chunks,
            "template_id": trace.get("template_id"),
            "bound_params": dict(trace.get("bound_params") or {}),
        },
        "query_spec": dict(trace.get("query_spec") or {}),
        "backend_latency_sec": trace.get("latency_sec"),
        "missing_count": trace.get("missing_count", 0),
        "returned_chunk_ids": _chunk_ids(chunks),
    }
    for key in (
        "status",
        "reason",
        "unsupported_reason",
        "stage",
        "error_type",
        "error",
    ):
        if trace.get(key) is not None:
            compact[key] = trace[key]
    return compact


def agent_financial_search(
    query: str,
    top_k_chunks: int,
    cfg,
) -> RetrieverResult:
    """Let the Financial Tool own ticker/spec parsing; compact only its trace."""

    result = financial_search(
        query=query,
        top_k_chunks=top_k_chunks,
        cfg=cfg,
    )
    chunks = list(result.get("chunks") or [])
    trace = dict(result.get("trace") or {})
    return {
        "chunks": chunks,
        "trace": _compact_financial_trace(
            trace,
            chunks,
            top_k_chunks=top_k_chunks,
        ),
    }


# Graph, vector, and financial use agent-specific adapters so retrieval traces
# stay compact and evaluation-ready. Other tools keep their existing contract.
RETRIEVERS: dict[str, Callable] = {
    "vector": agent_vector_search,
    "graph": agent_graph_search,
    "hybrid": hybrid_search,
    "financial": agent_financial_search,
    "news": news_search,
}


TOOL_SCHEMAS: list[dict] = [
    {
        "type" : "function",
        "function": {
            "name": "graph",
            "description": "Relational reasoning across entities — supplier chains, customer relationships, subsidiaries, competitive positioning (X → Y → Z multi-hop paths in a knowledge graph)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural language question to query the knowledge graph.",
                    }
                },
                "required": ["query"],
            }
        }
    },

    {
        "type" : "function",
        "function": {
            "name": "vector",
            "description": "semantic similarity search over SEC filing narrative — business strategy, product descriptions, risk factors, management commentary. Use when the question asks what a company SAYS or DESCRIBES about a topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The input text to retrieve vector embeddings for.",
                    }
                },
                "required": ["query"],
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "financial",
            "description": (
                "Query structured financial facts and deterministic metrics "
                "from local PostgreSQL. Use for revenue, profit, margins, "
                "growth, ratios, cash flow, valuation snapshots, and comparisons."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Natural-language financial question. The Financial "
                            "Tool resolves ticker, metric, period, and operation."
                        ),
                    },
                },
                "required": ["query"],
            },
        },
    },

    {
        "type" : "function",
        "function": {
            "name": "news",
            "description": "Retrieve the latest news articles and updates based on a natural language query. This tool can access news databases and APIs to provide relevant information such as recent events, market news, company announcements, and other newsworthy topics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural language question to retrieve the latest news articles and updates.",
                    }
                },
                "required": ["query"],
            }
        }
    }


]
