
from __future__ import annotations

from typing import Optional

from semigraph.config import Config, get_config
from semigraph.online.graph_search import graph_search
from semigraph.online.vector_search import vector_search


def hybrid_search(
    query: str,
    top_k_chunks: int = 5,
    top_k_each: int = 10,
    k_rrf: int = 60,
    w_vector: float = 1.0,
    w_graph: float = 1.0,
    graph_use_expansion: bool = True,
    graph_seed_mode: str = "triple",
    cfg: Optional[Config] = None,
    candidate_pool_k: int = 100,
    graph_top_k_entities: int = 20,
    graph_top_k_triples: int = 8,
    graph_damping: float = 0.7,
    graph_triple_filter: str = "none",
) -> list[dict]:
    """Reciprocal Rank Fusion of vector_search and graph_search.

    """
    if not query.strip():
        return []

    vec_results = vector_search(query, top_k_chunks=top_k_each, cfg=cfg)
    gph_results = graph_search(
        query,
        top_k_chunks=top_k_each,
        use_expansion=graph_use_expansion,
        seed_mode=graph_seed_mode,
        top_k_entities=graph_top_k_entities,
        top_k_triples=graph_top_k_triples,
        damping=graph_damping,
        graph_triple_filter=graph_triple_filter,
        cfg=cfg,
        candidate_pool_k=candidate_pool_k,
    )

    # Accumulate per-chunk weighted RRF score.
    fused: dict[str, dict] = {}

    for rank, chunk in enumerate(vec_results, start=1):
        cid = chunk["chunk_id"]
        fused[cid] = {
            **{k: chunk[k] for k in
               ("chunk_id", "text", "ticker", "fiscal_year", "section")},
            "score": w_vector / (k_rrf + rank),
            "_vec_rank": rank,
            "_gph_rank": None,
        }

    for rank, chunk in enumerate(gph_results, start=1):
        cid = chunk["chunk_id"]
        contribution = w_graph / (k_rrf + rank)
        if cid in fused:
            fused[cid]["score"] += contribution
            fused[cid]["_gph_rank"] = rank
        else:
            fused[cid] = {
                **{k: chunk[k] for k in
                   ("chunk_id", "text", "ticker", "fiscal_year", "section")},
                "score": contribution,
                "_vec_rank": None,
                "_gph_rank": rank,
            }

    # Sort by fused score desc, then chunk_id ASC for determinism
    ranked = sorted(
        fused.values(),
        key=lambda d: (-d["score"], d["chunk_id"]),
    )[:top_k_chunks]

    n_both = sum(1 for d in ranked if d["_vec_rank"] and d["_gph_rank"])
    print(f"[hybrid] vec={len(vec_results)} gph={len(gph_results)} "
          f"unique={len(fused)} → top-{top_k_chunks} (both-tool: {n_both})")

    # Strip internal debug keys before returning — caller sees same shape
    # as graph_search / vector_search.
    return [
        {k: d[k] for k in
         ("chunk_id", "text", "ticker", "fiscal_year", "section", "score")}
        for d in ranked
    ]


if __name__ == "__main__":
    for q in [
        "What political risks affect the home country of the leading pure-play semiconductor foundry?",
        "Which generative AI research lab partners with the maker of EPYC processors?",
        "AMD",
        "qwerty zzz nonsense",
    ]:
        print(f"\n--- Query: {q!r}")
        results = hybrid_search(q, top_k_chunks=5)
        for i, ch in enumerate(results, start=1):
            preview = ch["text"][:90].replace("\n", " ")
            print(f"  #{i}  rrf={ch['score']:.4f}  "
                  f"[{ch['ticker']} FY{ch['fiscal_year']} {ch['section']}] {ch['chunk_id']}")
            print(f"      └─ {preview}...")
