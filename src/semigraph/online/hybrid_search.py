"""
Phase C2-quater — hybrid_search: Reciprocal Rank Fusion of graph + vector.

Why fusion instead of routing:
  Held-out N=10 result (Phase C2-ter) showed graph and vector tie on
  Hit@5 (7/10 each) but **cover different chunks** — union reaches 9/10.
  RRF is a deterministic, training-free way to capture that union without
  an agentic router or LLM re-ranker.

RRF formula (Cormack et al., SIGIR '09 — the standard IR baseline):
    rrf_score(d) = Σ_i 1 / (k + rank_i(d))
  where i iterates over rankers (vector, graph), rank_i(d) is the
  1-indexed rank of d in ranker i, and k=60 (TREC convention).

Properties relevant to our thesis:
  - **Score-scale invariant**: graph PPR scores (~2-3) and vector cosine
    (0.7-0.9) live on different scales; RRF uses only rank, not score.
  - **Floor guarantee**: a chunk that ranks #1 in either tool scores
    1/(60+1) = 0.0164, which beats any chunk ranked #11+ in the other —
    so high-confidence single-tool hits survive.
  - **Bonus for agreement**: a chunk in BOTH top-5 gets summed score
    (e.g. 1/61 + 1/61 = 0.0328) — beats single-tool top-1.
"""
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
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Reciprocal Rank Fusion of vector_search and graph_search.

    Pure RRF (w_vec = w_gph = 1.0) is the TREC-standard default. We tested
    vector-biased weights (0.6/0.4) on the dev set to mitigate 3 held-out
    losses where graph chunks crowded vector's high-recall hits out of
    top-5 — but the vector bias degraded dev Hit@5 from 20/20 → 17/20 and
    recall 0.607 → 0.492. Conclusion: no weight-tuning sweet spot — the
    coverage-vs-pairwise-stability trade-off is fundamental to RRF. We
    keep the pure RRF default and document the limitation.

    Args:
        query:         Natural-language question.
        top_k_chunks:  Final result size.
        top_k_each:    Top-k pulled from each underlying tool before fusion.
                       Larger = wider candidate pool, more chance to surface
                       cross-tool agreement; 10 is standard.
        k_rrf:         RRF damping constant. 60 = TREC convention; lower
                       amplifies top-rank dominance.
        w_vector:      Weight on vector's RRF contribution (default 1.0).
                       Available as escape hatch — empirically no
                       non-symmetric value tested improves dev metrics.
        w_graph:       Weight on graph's RRF contribution (default 1.0).
        cfg:           Optional Config; defaults to cached singleton.

    Returns:
        `[{chunk_id, text, ticker, fiscal_year, section, score}, ...]` where
        `score` is the fused (weighted) RRF value. Output shape matches
        graph_search and vector_search exactly so call sites are
        interchangeable.
    """
    if not query.strip():
        return []

    vec_results = vector_search(query, top_k_chunks=top_k_each, cfg=cfg)
    gph_results = graph_search(query, top_k_chunks=top_k_each, cfg=cfg)

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
