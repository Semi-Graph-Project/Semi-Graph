"""
Phase C2 — vector_search: vanilla chunk vector retrieval (Homogeneous RAG baseline).

Output shape matches `graph_search()` exactly so Phase E ablation A/B works
without format conversion. No similarity threshold — top-k always returns k.
"""
from __future__ import annotations

from typing import Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.embeddings import get_embedding_model
from semigraph.online.rerank import rerank_chunks
from semigraph.trace import TraceCallback, notify_trace


DEFAULT_VECTOR_INDEX = "chunk_embedding"

_CYPHER_VECTOR_SEARCH = """
CALL db.index.vector.queryNodes($index_name, $top_k, $vec)
YIELD node, score
RETURN node.chunk_id    AS chunk_id,
       node.text        AS text,
       node.ticker      AS ticker,
       node.fiscal_year AS fiscal_year,
       node.section     AS section,
       score
ORDER BY score DESC, chunk_id ASC
"""


def _retrieve_chunks(
    query: str,
    top_k_chunks: int,
    cfg: Optional[Config] = None,
    vector_index: str = DEFAULT_VECTOR_INDEX,
) -> list[dict]:
    """Retrieve a vector-ranked candidate pool from Neo4j."""
    if not query.strip() or top_k_chunks <= 0:
        return []

    cfg = cfg or get_config()
    model = get_embedding_model()
    vec = model.encode([query])[0].tolist()

    driver: Driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            result = session.run(
                _CYPHER_VECTOR_SEARCH,
                index_name=vector_index,
                top_k=top_k_chunks,
                vec=vec,
            )
            return result.data()
    finally:
        driver.close()


def trace_vector_search(
    query: str,
    top_k_chunks: int = 5,
    candidate_pool_k: int = 100,
    final_rerank: str = "none",
    cfg: Optional[Config] = None,
    vector_index: str = DEFAULT_VECTOR_INDEX,
    trace_callback: TraceCallback | None = None,
) -> dict:
    """Run vector retrieval and keep raw/reranked results for evaluation."""
    if not query.strip() or top_k_chunks <= 0:
        return {
            "query": query,
            "candidate_pool_k": candidate_pool_k,
            "final_rerank": final_rerank,
            "chunk_candidates": [],
            "raw_chunk_candidates": [],
            "reranked_chunks": [],
            "reranker_trace": {"enabled": False, "fallback": False, "status": "skipped"},
            "chunks": [],
        }

    cfg = cfg or get_config()
    notify_trace(trace_callback, {
        "stage": "vector_candidates",
        "status": "running",
        "message": "Encoding the query and searching the vector index",
        "details": {
            "vector_index": vector_index,
            "candidate_pool_k": candidate_pool_k,
        },
    })
    if vector_index == DEFAULT_VECTOR_INDEX:
        candidates = _retrieve_chunks(query, candidate_pool_k, cfg=cfg)
    else:
        # Benchmark against a non-default vector index (e.g., gold_chunk_embedding)
        candidates = _retrieve_chunks(
            query,
            candidate_pool_k,
            cfg=cfg,
            vector_index=vector_index,
        )
    notify_trace(trace_callback, {
        "stage": "vector_candidates",
        "status": "complete",
        "message": f"Retrieved {len(candidates)} vector candidates",
        "details": {
            "candidate_count": len(candidates),
            "candidate_chunk_ids": [
                str(chunk["chunk_id"])
                for chunk in candidates[:20]
                if chunk.get("chunk_id")
            ],
        },
    })
    notify_trace(trace_callback, {
        "stage": "reranking",
        "status": "running",
        "message": f"Applying {final_rerank} reranking",
        "details": {
            "mode": final_rerank,
            "candidate_count": len(candidates),
        },
    })
    if final_rerank == "none":
        reranked = candidates[:top_k_chunks]
        reranker_trace = {
            "enabled": False,
            "fallback": False,
            "status": "disabled",
            "candidate_count": len(candidates),
            "returned_count": len(reranked),
        }
    elif final_rerank == "cohere":
        reranked, reranker_trace = rerank_chunks(
            query=query,
            chunks=candidates[:20],
            top_n=top_k_chunks,
            cfg=cfg,
            fail_open=True,
        )
        reranker_trace = {
            "enabled": True,
            "fallback": reranker_trace.get("status") == "fallback",
            **reranker_trace,
        }
    else:
        raise ValueError(f"Unknown final_rerank: {final_rerank}")

    returned_chunk_ids = [
        str(chunk["chunk_id"])
        for chunk in reranked
        if chunk.get("chunk_id")
    ]
    notify_trace(trace_callback, {
        "stage": "reranking",
        "status": "complete",
        "message": f"Selected {len(reranked)} final chunks",
        "details": {
            "mode": final_rerank,
            "returned_chunk_ids": returned_chunk_ids,
            "reranker": reranker_trace,
        },
    })
    notify_trace(trace_callback, {
        "stage": "retrieval_complete",
        "status": "complete",
        "message": "Vector retrieval completed",
        "details": {"returned_chunk_ids": returned_chunk_ids},
    })

    return {
        "query": query,
        "candidate_pool_k": candidate_pool_k,
        "final_rerank": final_rerank,
        "chunk_candidates": candidates,
        "raw_chunk_candidates": candidates,
        "reranked_chunks": reranked,
        "reranker_trace": reranker_trace,
        "chunks": reranked,
    }


def vector_search(
    query: str,
    top_k_chunks: int = 5,
    cfg: Optional[Config] = None,
    candidate_pool_k: Optional[int] = None,
    final_rerank: str = "none",
    vector_index: str = DEFAULT_VECTOR_INDEX,
) -> list[dict]:
    """Return top-k vector chunks, optionally after external reranking.

    Args:
        query: Natural-language question.
        top_k_chunks: Number of chunks to return.
        candidate_pool_k: Number of vector candidates before reranking.
        final_rerank: `none` or `cohere`.
        vector_index: Neo4j vector index name; defaults to the production index.
        cfg: Optional Config; defaults to cached singleton.

    Returns:
        `[{chunk_id, text, ticker, fiscal_year, section, score}, ...]` —
        shape identical to `graph_search()`. Empty list if query is blank.
    """
    trace = trace_vector_search(
        query,
        top_k_chunks=top_k_chunks,
        candidate_pool_k=candidate_pool_k or top_k_chunks,
        final_rerank=final_rerank,
        cfg=cfg,
        vector_index=vector_index,
    )
    return trace["chunks"]


if __name__ == "__main__":
    for q in [
        "AMD",
        "TSMC supply chain",
        "china semiconductor ban",
        "Hopper data center segment revenue",
        "qwerty zzz random nonsense",
    ]:
        print(f"\n--- Query: {q!r} ---")
        for i, ch in enumerate(vector_search(q, top_k_chunks=3), start=1):
            preview = ch["text"][:120].replace("\n", " ")
            print(f"  #{i}  score={ch['score']:.3f}  "
                  f"[{ch['ticker']} FY{ch['fiscal_year']} {ch['section']}]")
            print(f"      └─ {preview}...")

        print("RAW:", vector_search(q, top_k_chunks=5))
