"""Graph retrieval: query → seeds → passage PPR → ranked chunks."""
from __future__ import annotations

from typing import Optional

from semigraph.config import Config, get_config
from semigraph.online.ppr import run_passage_ppr
from semigraph.online.query_expand import expand_query
from semigraph.online.rerank import company_rerank, fiscal_year_rerank
from semigraph.online.seed import (
    query_to_chunk_seeds,
    query_to_triple_candidates,
    query_to_seeds,
    triple_candidates_to_seeds,
)
from semigraph.online.triple_filter import filter_triple_candidates
from semigraph.online.vector_search import DEFAULT_VECTOR_INDEX
from semigraph.trace import TraceCallback, notify_trace


def _select_seeds(
    query: str,
    seed_mode: str,
    top_k_triples: int,
    top_k_chunk_seeds: int = 5,
    chunk_seed_vector_index: str = DEFAULT_VECTOR_INDEX,
    triple_filter_mode: str = "none",
    cfg: Optional[Config] = None,
) -> tuple[list[dict], dict]:
    """Select one homogeneous seed set for graph retrieval."""
    if seed_mode == "chunk_only":
        return query_to_chunk_seeds(
            query,
            top_k=top_k_chunk_seeds,
            vector_index=chunk_seed_vector_index,
            cfg=cfg,
        ), {
            "mode": "none",
            "applied": False,
            "reason": "chunk_only_mode",
        }

    if triple_filter_mode not in {"none", "llm"}:
        raise ValueError(f"Unknown triple filter mode: {triple_filter_mode}")

    if seed_mode == "triple":
        if triple_filter_mode == "none":
            candidates = query_to_triple_candidates(
                query,
                top_k_candidates=top_k_triples,
                cfg=cfg,
            )
            return triple_candidates_to_seeds(candidates), {
                "mode": "none",
                "applied": False,
                "reason": "embedding_ranked",
                "candidates_before_filter": candidates,
                "candidates_after_filter": candidates,
                "selected_candidate_ids": [
                    candidate["candidate_id"] for candidate in candidates
                ],
            }

        candidates = query_to_triple_candidates(
            query,
            top_k_candidates=top_k_triples,
            cfg=cfg,
        )
        selected, filter_trace = filter_triple_candidates(
            query,
            candidates,
            cfg=cfg,
        )
        return triple_candidates_to_seeds(selected), {
            "mode": "llm",
            "applied": True,
            **filter_trace,
        }
    if seed_mode == "node":
        return query_to_seeds(
            query,
            top_k=top_k_triples,
            cfg=cfg,
        ), {"mode": triple_filter_mode, "applied": False, "reason": "node_mode"}
    raise ValueError(f"Unknown graph seed_mode: {seed_mode}")


def trace_graph_search(
    query: str,
    top_k_chunks: int = 5,
    top_k_entities: int = 20,
    damping: float = 0.5,
    top_k_triples: int = 10,
    top_k_chunk_seeds: int = 5,
    chunk_seed_vector_index: str = DEFAULT_VECTOR_INDEX,
    use_expansion: bool = True,
    seed_mode: str = "triple",
    candidate_pool_k: int = 100,
    ppr_seed_weight_mode: str = "uniform",
    graph_triple_filter: str = "none",
    cfg: Optional[Config] = None,
    trace_callback: TraceCallback | None = None,
) -> dict:
    """Run graph retrieval and return both chunks and stage-level trace.

    query expansion -> seeds -> passage PPR -> metadata reranking -> chunks.
    """
    print(f"[graph_search] query={query!r} "
          f"top_k_chunks={top_k_chunks} top_k_entities={top_k_entities}")

    notify_trace(trace_callback, {
        "stage": "query_expansion",
        "status": "running" if use_expansion else "skipped",
        "message": (
            "Expanding the graph search query"
            if use_expansion
            else "Query expansion is disabled"
        ),
        "details": {"original_query": query},
    })
    effective_query = expand_query(query, cfg=cfg) if use_expansion else query
    notify_trace(trace_callback, {
        "stage": "query_expansion",
        "status": "complete" if use_expansion else "skipped",
        "message": "Prepared the effective graph query",
        "details": {"effective_query": effective_query},
    })
    trace = {
        "query": query,
        "effective_query": effective_query,
        "use_expansion": use_expansion,
        "seed_mode": seed_mode,
        "candidate_pool_k": candidate_pool_k,
        "metadata_rerank": "company+fiscal_year",
        "top_k_chunks": top_k_chunks,
        "top_k_entities": top_k_entities,
        "top_k_triples": top_k_triples,
        "top_k_chunk_seeds": top_k_chunk_seeds,
        "chunk_seed_vector_index": chunk_seed_vector_index,
        "damping": damping,
        "seeds": [],
        "ppr_entities": [],
        "chunk_candidates": [],
        "raw_chunk_candidates": [],
        "reranked_chunks": [],
        "reranker_trace": {"mode": "company+fiscal_year", "status": "not_run"},
        "chunks": [],
        "abort_reason": None,
        "ppr_seed_weight_mode": ppr_seed_weight_mode,
        "graph_triple_filter": graph_triple_filter,
    }

    notify_trace(trace_callback, {
        "stage": "seed_selection",
        "status": "running",
        "message": f"Selecting graph seeds with {seed_mode} mode",
        "details": {
            "seed_mode": seed_mode,
            "triple_filter": graph_triple_filter,
            "top_k_triples": top_k_triples,
            "top_k_chunk_seeds": top_k_chunk_seeds,
        },
    })
    seeds, triple_filter_trace = _select_seeds(
        effective_query,
        seed_mode=seed_mode,
        top_k_triples=top_k_triples,
        top_k_chunk_seeds=top_k_chunk_seeds,
        chunk_seed_vector_index=chunk_seed_vector_index,
        triple_filter_mode=graph_triple_filter,
        cfg=cfg,
    )
    trace["seeds"] = seeds
    trace["triple_filter_trace"] = triple_filter_trace
    notify_trace(trace_callback, {
        "stage": "seed_selection",
        "status": "complete",
        "message": f"Selected {len(seeds)} graph seeds",
        "details": {
            "seed_count": len(seeds),
            "top_k_triples": top_k_triples,
            "seeds": [
                {
                    key: seed[key]
                    for key in ("chunk_id", "name", "type", "similarity", "specificity")
                    if seed.get(key) is not None
                }
                for seed in seeds[:20]
            ],
            "triple_candidates": list(
                triple_filter_trace.get("candidates_before_filter")
                or triple_filter_trace.get("candidates_after_filter")
                or []
            ),
            "triple_filter": triple_filter_trace,
        },
    })
    if not seeds:
        trace["abort_reason"] = "no_seeds"
        notify_trace(trace_callback, {
            "stage": "retrieval_complete",
            "status": "complete",
            "message": "Graph retrieval stopped because no seeds were found",
            "details": {"abort_reason": "no_seeds"},
        })
        print("[graph_search] no seeds — aborting")
        return trace

    notify_trace(trace_callback, {
        "stage": "personalized_pagerank",
        "status": "running",
        "message": "Running Personalized PageRank",
        "details": {
            "graph_mode": "entity_chunk",
            "damping": damping,
            "seed_weight_mode": ppr_seed_weight_mode,
            "seed_count": len(seeds),
        },
    })
    passage_result = run_passage_ppr(
        seeds,
        top_k_chunks=candidate_pool_k,
        top_k_entities=top_k_entities,
        damping=damping,
        seed_weight_mode=ppr_seed_weight_mode,
        cfg=cfg,
    )

    trace["seeds"] = passage_result["seeds"]
    trace["ppr_entities"] = passage_result["ppr_entities"]
    trace["chunk_candidates"] = passage_result["chunks"]
    trace["raw_chunk_candidates"] = trace["chunk_candidates"]
    trace["reranked_chunks"] = fiscal_year_rerank(
        query,
        company_rerank(query, trace["chunk_candidates"], cfg=cfg),
    )
    trace["chunks"] = trace["reranked_chunks"][:top_k_chunks]
    trace["reranker_trace"] = {
        "mode": "company+fiscal_year",
        "status": "complete",
        "candidate_count": len(trace["reranked_chunks"]),
        "returned_count": len(trace["chunks"]),
    }
    trace["projection"] = passage_result["projection"]
    trace["direct_chunk_ppr"] = True
    notify_trace(trace_callback, {
        "stage": "personalized_pagerank",
        "status": "complete",
        "message": "Ranked entities and chunks with Personalized PageRank",
        "details": {
            "entity_count": len(trace["ppr_entities"]),
            "candidate_count": len(trace["raw_chunk_candidates"]),
            "projection": trace["projection"],
        },
    })
    notify_trace(trace_callback, {
        "stage": "reranking",
        "status": "running",
        "message": "Applying company and fiscal-year reranking",
        "details": {
            "mode": "company+fiscal_year",
            "candidate_count": len(trace["raw_chunk_candidates"]),
        },
    })
    _emit_graph_retrieval_events(
        trace_callback,
        trace["raw_chunk_candidates"],
        trace["chunks"],
    )
    return trace


def _emit_graph_retrieval_events(
    trace_callback: TraceCallback | None,
    candidates: list[dict],
    chunks: list[dict],
) -> None:
    """Publish final Graph retrieval details without changing ranking logic."""
    returned_chunk_ids = [
        str(chunk["chunk_id"])
        for chunk in chunks
        if chunk.get("chunk_id")
    ]
    notify_trace(trace_callback, {
        "stage": "reranking",
        "status": "complete",
        "message": f"Selected {len(chunks)} final graph chunks",
        "details": {
            "mode": "company+fiscal_year",
            "candidate_count": len(candidates),
            "returned_chunk_ids": returned_chunk_ids,
        },
    })
    notify_trace(trace_callback, {
        "stage": "retrieval_complete",
        "status": "complete",
        "message": "Graph retrieval completed",
        "details": {"returned_chunk_ids": returned_chunk_ids},
    })


def graph_search(
    query: str,
    top_k_chunks: int = 5,
    top_k_entities: int = 20,
    damping: float = 0.5,
    top_k_triples: int = 8,
    top_k_chunk_seeds: int = 5,
    chunk_seed_vector_index: str = DEFAULT_VECTOR_INDEX,
    use_expansion: bool = True,
    seed_mode: str = "triple",
    candidate_pool_k: int = 100,
    ppr_seed_weight_mode: str = "uniform",
    graph_triple_filter: str = "none",
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Full graph_search pipeline: query → top-k chunks ranked by PPR mass.

    """
    trace = trace_graph_search(
        query,
        top_k_chunks=top_k_chunks,
        top_k_entities=top_k_entities,
        damping=damping,
        top_k_triples=top_k_triples,
        top_k_chunk_seeds=top_k_chunk_seeds,
        chunk_seed_vector_index=chunk_seed_vector_index,
        use_expansion=use_expansion,
        seed_mode=seed_mode,
        candidate_pool_k=candidate_pool_k,
        ppr_seed_weight_mode=ppr_seed_weight_mode,
        graph_triple_filter=graph_triple_filter,
        cfg=cfg,
    )
    return trace["chunks"]
