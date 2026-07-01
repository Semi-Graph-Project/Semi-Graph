"""
Phase C1c — graph_search tool: closes the retrieval loop (query → chunks).

Composes Phase A-B offline outputs with C1a/C1b/C1b+ online steps:

    query
      → seeds              (seed.query_to_triple_seeds — Phase C1b+)
      → ranked entities    (ppr.run_ppr — Phase C1b)
      → alias clusters     (_cluster_aliases — this file, sub-step C1)
      → ranked chunks      (_map_chunks — TODO, sub-step C2)
      → top-k chunks       (graph_search — TODO, sub-step C3)

SYNONYM_OF semantics: Phase B2 synonymy writes edges from validated pairs
(composite rules — legal_suffix, acronym, plural, digit-match embeddings).
Beyond 2 hops in the synonym graph, transitivity quality degrades — chains
like `a → b → c → d` may include false positives that were never directly
validated. Traversal is capped at 2.

Downstream aggregate (sub-step C2): SUM(PPR score) over the cluster's
mentioning chunks. SUM rewards chunks reached by multiple high-PPR
entities — the multi-hop reasoning signal we want PPR to surface.
"""
from __future__ import annotations

import re
from typing import Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.online.ppr import run_ppr
from semigraph.online.query_expand import expand_query
from semigraph.online.seed import (
    query_to_hybrid_seeds,
    query_to_seeds,
    query_to_triple_seeds,
)


_RISK_TERMS = {
    "affect",
    "constraint",
    "constraints",
    "control",
    "controls",
    "depend",
    "dependency",
    "dependencies",
    "dependent",
    "exposed",
    "exposure",
    "geopolitical",
    "impact",
    "political",
    "risk",
    "risks",
    "shortage",
    "supply",
    "taiwan",
    "tariff",
    "uncertainty",
    "yield",
}
_BUSINESS_TERMS = {
    "architecture",
    "business",
    "compete",
    "competitor",
    "customer",
    "foundry",
    "manufacture",
    "manufactures",
    "partner",
    "partners",
    "product",
    "products",
    "segment",
    "segments",
    "supplier",
    "supplies",
    "wafer",
    "wafers",
}
_FINANCIAL_TERMS = {
    "annual",
    "depreciation",
    "eps",
    "fy",
    "fy2023",
    "fy2024",
    "fy2025",
    "gross",
    "margin",
    "revenue",
    "sales",
}
_CONTENT_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "between",
    "by",
    "did",
    "does",
    "do",
    "from",
    "has",
    "have",
    "how",
    "in",
    "is",
    "it",
    "its",
    "main",
    "of",
    "on",
    "offer",
    "offers",
    "or",
    "product",
    "products",
    "that",
    "the",
    "their",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
}


def _query_terms(query: str) -> set[str]:
    """Lowercase token set used by lightweight retrieval intent heuristics."""
    return set(re.findall(r"[a-z0-9]+", query.lower()))


def _section_boosts_for_query(query: str) -> dict[str, float]:
    """Infer section preference from the user's wording.

    First-principle version: graph/PPR ranks *entities*. A chunk still needs a
    second decision: which filing section is the right evidence container?
    Risk wording should prefer Item_1A, business/product wording should prefer
    Item_1, and exact financial wording should prefer Item_7 when graph is
    called directly.
    """
    terms = _query_terms(query)
    boosts: dict[str, float] = {}

    if terms & _RISK_TERMS:
        boosts["Item_1A"] = 1.35
    if terms & _BUSINESS_TERMS:
        boosts["Item_1"] = 1.18
    if terms & _FINANCIAL_TERMS:
        boosts["Item_7"] = 1.28

    return boosts


def _ticker_boosts_for_query(query: str, cfg: Optional[Config] = None) -> set[str]:
    """Return explicit ticker mentions in the query for provenance-aware rerank."""
    cfg = cfg or get_config()
    known_tickers = {ticker.upper() for ticker in cfg.tickers if ticker}
    terms = {t.upper() for t in _query_terms(query)}
    return terms & known_tickers


def _content_terms_for_query(query: str) -> set[str]:
    """Query terms worth checking literally inside candidate chunk text."""
    terms = _query_terms(query)
    return {
        term
        for term in terms
        if term not in _CONTENT_STOPWORDS and len(term) >= 3
    }


def _lexical_boost_for_chunk(query_terms: set[str], chunk: dict) -> float:
    """Small boost when graph candidates contain answer-bearing query terms."""
    if not query_terms:
        return 1.0

    haystack = " ".join(
        str(chunk.get(key) or "")
        for key in ("chunk_id", "ticker", "section", "text")
    ).lower()
    matches = sum(1 for term in query_terms if term in haystack)

    return 1.0 + min(0.40, matches * 0.08)


def _rerank_chunks_by_query_intent(
    query: str,
    chunks: list[dict],
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Apply lightweight provenance intent reranking to graph chunk candidates.

    The original PPR-derived score remains the base signal. We only multiply it
    by small, explainable boosts from query intent:
      - section match, e.g. risk wording → Item_1A
      - explicit ticker match, e.g. "AMD" → AMD chunks

    """
    if not chunks:
        return []

    section_boosts = _section_boosts_for_query(query)
    ticker_boosts = _ticker_boosts_for_query(query, cfg=cfg)
    content_terms = _content_terms_for_query(query)

    reranked: list[dict] = []
    for idx, chunk in enumerate(chunks):
        base_score = float(chunk.get("score") or 0.0)
        boost = 1.0

        section = str(chunk.get("section") or "")
        boost *= section_boosts.get(section, 1.0)

        ticker = str(chunk.get("ticker") or "").upper()
        if ticker in ticker_boosts:
            boost *= 1.25

        boost *= _lexical_boost_for_chunk(content_terms, chunk)

        enriched = dict(chunk)
        enriched["score"] = base_score * boost
        enriched["_graph_base_score"] = base_score
        enriched["_intent_boost"] = boost
        enriched["_original_rank"] = idx
        reranked.append(enriched)

    reranked.sort(
        key=lambda d: (
            -float(d.get("score") or 0.0),
            int(d.get("_original_rank") or 0),
            str(d.get("chunk_id") or ""),
        )
    )

    return [
        {k: v for k, v in chunk.items() if not k.startswith("_")}
        for chunk in reranked
    ]


# UNWIND iterates one row per requested name. MATCH binds `e` to that name's
# Entity node (missing names produce no row — caller must default). OPTIONAL
# MATCH walks SYNONYM_OF in either direction (undirected) for 1-2 hops. Self
# is appended explicitly because `*1..2` excludes length-0; using `*0..2`
# mixes self-row and alias-rows in collect() in version-dependent ways.
_CYPHER_CLUSTER_ALIASES = """
UNWIND $names AS seed_name
MATCH (e:Entity {name: seed_name})
OPTIONAL MATCH (e)-[:SYNONYM_OF*1..2]-(a:Entity)
WITH seed_name, e.name AS self_name, collect(DISTINCT a.name) AS aliases
RETURN seed_name AS seed, [self_name] + aliases AS cluster
"""


def _cluster_aliases(
    names: list[str],
    cfg: Optional[Config] = None,
) -> dict[str, list[str]]:
    """Resolve each input entity name to its SYNONYM_OF cluster (≤ 2 hops).

    Args:
        names: Entity names to cluster (typically `run_ppr()` top-k output).
        cfg:   Optional Config; defaults to cached singleton.

    Returns:
        `{seed_name: [alias_1, alias_2, ...]}` — alias list always contains
        `seed_name` itself, is deduplicated, and sorted for determinism.
        Entities without SYNONYM_OF edges map to `[seed_name]`.
        Names not present in the graph are absent from the dict — callers
        should fall back via `.get(name, [name])`.
    """
    if not names:
        return {}

    cfg = cfg or get_config()
    driver: Driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            rows = list(session.run(_CYPHER_CLUSTER_ALIASES, names=names))
    finally:
        driver.close()

    return {row["seed"]: sorted(set(row["cluster"])) for row in rows}


# UNWIND yields one row per cluster. The inner MATCH finds every Chunk that
# mentions any alias in the cluster; EXISTS{} guarantees the (cluster, chunk)
# pair appears AT MOST ONCE regardless of how many aliases in the cluster the
# chunk mentions — without EXISTS, a chunk mentioning 3 aliases of AMD would
# contribute 3 × cluster.score, defeating the alias-collapse from C1.
# Outer aggregation then SUMs `contribution` across all clusters mentioning
# the chunk — this is the multi-hop reasoning signal we want at chunk level.
# Secondary sort on chunk_id keeps results deterministic across runs when
# scores tie (without it, Neo4j storage order surfaces nondeterminism).
_CYPHER_MAP_CHUNKS = """
UNWIND $clusters AS cluster
MATCH (c:Chunk)
WHERE EXISTS {
  MATCH (c)-[:MENTIONS]->(e:Entity)
  WHERE e.name IN cluster.aliases
}
WITH c, cluster.score AS contribution
WITH c, sum(contribution) AS score
RETURN c.chunk_id AS chunk_id,
       c.text     AS text,
       c.ticker   AS ticker,
       c.fiscal_year AS fiscal_year,
       c.section  AS section,
       score
ORDER BY score DESC, chunk_id ASC
LIMIT $top_k
"""


def _map_chunks(
    cluster_entries: list[dict],
    top_k: int = 5,
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Aggregate cluster PPR scores onto mentioning chunks.

    For each cluster, find every Chunk that MENTIONS at least one alias,
    then SUM the cluster's score onto that chunk. A chunk mentioning
    multiple aliases of the same cluster contributes the cluster score
    exactly ONCE (alias-collapse from C1 stays intact). A chunk mentioning
    multiple distinct clusters accumulates all their scores — this is the
    multi-hop signal at chunk level.

    Args:
        cluster_entries: One entry per alias cluster:
            `[{"aliases": ["amd", "advanced micro devices", ...],
               "score": 1.93}, ...]`
            Aliases come from `_cluster_aliases`; score is the cluster's
            aggregated PPR mass (decided by C3 orchestrator).
        top_k: Number of top chunks to return.
        cfg:   Optional Config; defaults to cached singleton.

    Returns:
        Top-k chunks sorted by aggregated score desc (chunk_id ASC tiebreak):
        `[{"chunk_id": str, "text": str, "score": float}, ...]`. Empty list
        if `cluster_entries` is empty or no chunk mentions any alias.
    """
    if not cluster_entries or top_k <= 0:
        return []

    cfg = cfg or get_config()
    driver: Driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            rows = list(session.run(
                _CYPHER_MAP_CHUNKS,
                clusters=cluster_entries,
                top_k=top_k,
            ))
    finally:
        driver.close()

    return [
        {
            "chunk_id":    r["chunk_id"],
            "text":        r["text"],
            "ticker":      r["ticker"],
            "fiscal_year": r["fiscal_year"],
            "section":     r["section"],
            "score":       r["score"],
        }
        for r in rows
    ]


def _collapse_clusters(
    ppr_entities: list[dict],
    cluster_map: dict[str, list[str]],
) -> list[dict]:
    """Group PPR entities by alias cluster; SUM PPR scores per cluster.

    Two PPR entities that are aliases (e.g. `amd` + `advanced micro devices`)
    yield ONE cluster entry whose `score` is the sum of their PPR masses —
    recovering the AMD concept's total mass that Phase B2 left fragmented
    across alias nodes.

    Args:
        ppr_entities: Output of `run_ppr` — `[{name, type, score}, ...]`.
        cluster_map:  Output of `_cluster_aliases` —
                      `{seed_name: [alias_1, alias_2, ...]}`.

    Returns:
        `[{aliases: [...], score: float}, ...]` ready for `_map_chunks`.
        Order: highest cluster score first (deterministic).
    """
    name_to_score = {e["name"]: e["score"] for e in ppr_entities}
    seen_clusters: set[frozenset] = set()
    entries: list[dict] = []

    # Iterate ppr_entities in their original (PPR-rank) order so the first
    # alias encountered defines the cluster, and we skip subsequent aliases
    # belonging to the same cluster.
    for entity in ppr_entities:
        name = entity["name"]
        aliases = cluster_map.get(name, [name])
        key = frozenset(aliases)
        if key in seen_clusters:
            continue
        seen_clusters.add(key)

        # SUM scores of every alias that ranks in PPR top-k. Aliases outside
        # top-k aren't penalized — they simply contribute 0 (their mass is
        # already low or they fell outside the cap).
        cluster_score = sum(name_to_score.get(a, 0.0) for a in aliases)
        entries.append({"aliases": list(aliases), "score": cluster_score})

    entries.sort(key=lambda c: c["score"], reverse=True)
    return entries


def _select_seed_entities(
    query: str,
    seed_mode: str,
    top_k_triples: int,
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Select seed entities for graph retrieval diagnostics.

    `graph_search` keeps the production default as Query-to-Triple, but the
    Phase T-R evaluator needs to compare node/triple/hybrid seed loss without
    duplicating the graph pipeline.
    """
    if seed_mode == "triple":
        return query_to_triple_seeds(
            query,
            top_k_triples=top_k_triples,
            cfg=cfg,
        )
    if seed_mode == "node":
        return query_to_seeds(
            query,
            top_k=top_k_triples,
            cfg=cfg,
        )
    if seed_mode == "hybrid":
        return query_to_hybrid_seeds(
            query,
            top_k_nodes=top_k_triples,
            top_k_triples=top_k_triples,
            cfg=cfg,
        )
    raise ValueError(f"Unknown graph seed_mode: {seed_mode}")


def trace_graph_search(
    query: str,
    top_k_chunks: int = 5,
    top_k_entities: int = 20,
    damping: float = 0.7,
    top_k_triples: int = 8,
    use_expansion: bool = True,
    seed_mode: str = "triple",
    cfg: Optional[Config] = None,
) -> dict:
    """Run graph retrieval and return both chunks and stage-level trace.

    This is the same pipeline as `graph_search`, with extra intermediate
    artifacts for Phase T-R bottleneck attribution:
    query expansion -> seeds -> PPR entities -> alias clusters -> chunk
    candidates -> intent reranked chunks.
    """
    print(f"[graph_search] query={query!r} "
          f"top_k_chunks={top_k_chunks} top_k_entities={top_k_entities}")

    effective_query = expand_query(query, cfg=cfg) if use_expansion else query
    trace = {
        "query": query,
        "effective_query": effective_query,
        "use_expansion": use_expansion,
        "seed_mode": seed_mode,
        "top_k_chunks": top_k_chunks,
        "top_k_entities": top_k_entities,
        "top_k_triples": top_k_triples,
        "damping": damping,
        "seeds": [],
        "ppr_entities": [],
        "cluster_entries": [],
        "chunk_candidates": [],
        "chunks": [],
        "abort_reason": None,
    }

    seeds = _select_seed_entities(
        effective_query,
        seed_mode=seed_mode,
        top_k_triples=top_k_triples,
        cfg=cfg,
    )
    trace["seeds"] = seeds
    if not seeds:
        trace["abort_reason"] = "no_seeds"
        print("[graph_search] no seeds — aborting")
        return trace

    ppr_entities = run_ppr(
        seeds,
        top_k=top_k_entities,
        damping=damping,
        cfg=cfg,
    )
    trace["ppr_entities"] = ppr_entities
    if not ppr_entities:
        trace["abort_reason"] = "empty_ppr"
        print("[graph_search] PPR returned empty — aborting")
        return trace

    cluster_map = _cluster_aliases(
        [e["name"] for e in ppr_entities],
        cfg=cfg,
    )

    cluster_entries = _collapse_clusters(ppr_entities, cluster_map)
    trace["cluster_entries"] = cluster_entries
    print(f"[graph_search] {len(ppr_entities)} PPR entities → "
          f"{len(cluster_entries)} unique clusters")

    candidate_k = max(top_k_chunks, min(top_k_chunks * 4, 40))
    chunk_candidates = _map_chunks(cluster_entries, top_k=candidate_k, cfg=cfg)
    trace["chunk_candidates"] = chunk_candidates
    chunks = _rerank_chunks_by_query_intent(
        effective_query,
        chunk_candidates,
        cfg=cfg,
    )[:top_k_chunks]
    trace["chunks"] = chunks
    print(f"[graph_search] returning {len(chunks)} chunks")
    return trace


def graph_search(
    query: str,
    top_k_chunks: int = 5,
    top_k_entities: int = 20,
    damping: float = 0.7,
    top_k_triples: int = 8,
    use_expansion: bool = True,
    seed_mode: str = "triple",
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Full graph_search pipeline: query → top-k chunks ranked by PPR mass.

    Composes Phase C1a/C1b/C1b+ + this module's C1/C2 + Tier 1 augmentation:

        query
          → expand_query                (Tier 1 A — LLM entity hints)
          → query_to_triple_seeds       (HippoRAG v2 linker, top_k_triples=8)
          → run_ppr                     (Personalized PageRank, damping=0.7)
          → _cluster_aliases            (collapse SYNONYM_OF cluster)
          → _collapse_clusters          (SUM PPR scores per cluster)
          → _map_chunks                 (MENTIONS → chunk + SUM cluster scores)

    Args:
        query:          Natural-language question.
        top_k_chunks:   Number of chunks to return for downstream LLM context.
        top_k_entities: PPR top-k cap. Pick 3-5x `top_k_chunks` so each chunk
                        receives signal from multiple entities (multi-hop).
        damping:        PageRank damping. 0.7 (tuned for our sparse KG, avg
                        degree 2.37) narrows walk closer to seeds and reduces
                        hub leakage vs HippoRAG default 0.85.
        top_k_triples:  Number of triples retrieved at seed step. 8 (vs 5
                        default) widens the seed funnel after query expansion
                        — expanded query surfaces more relevant entities and
                        we want their triples to all reach PPR.
        use_expansion:  Toggle LLM query expansion. Set False for ablation
                        ("does the LLM call actually help?").
        seed_mode:      `triple` default, with `node` and `hybrid` available
                        for Phase T-R seed ablations.
        cfg:            Optional Config; defaults to cached singleton.

    Returns:
        `[{chunk_id, text, ticker, fiscal_year, section, score}, ...]`
        Empty list if seeds is empty, PPR returns nothing, or no chunk
        mentions any retrieved entity.
    """
    trace = trace_graph_search(
        query,
        top_k_chunks=top_k_chunks,
        top_k_entities=top_k_entities,
        damping=damping,
        top_k_triples=top_k_triples,
        use_expansion=use_expansion,
        seed_mode=seed_mode,
        cfg=cfg,
    )
    return trace["chunks"]


if __name__ == "__main__":
    # --- C1 smoke test: alias clustering ---
    test_names = [
        "amd",                          # expect 4 aliases (AMD cluster)
        "advanced micro devices",       # same cluster as 'amd'
        "amd ryzen",                    # likely alone (PRODUCT)
        "tsmc",                         # likely alone (COMP)
        "nonexistent_entity_xyz",       # absent in graph — should drop
    ]
    print(f"[C1] resolving {len(test_names)} entities...\n")
    clusters = _cluster_aliases(test_names)

    for name in test_names:
        cluster = clusters.get(name)
        if cluster is None:
            print(f"  '{name}' → NOT FOUND in graph")
            continue
        marker = "  multi-alias" if len(cluster) > 1 else ""
        print(f"  '{name}' → {len(cluster)} alias(es){marker}")
        for alias in cluster:
            print(f"    - {alias}")
        print()

    # --- C2 smoke test: cluster → chunks ---
    # Two synthetic clusters with arbitrary PPR-style scores. The AMD cluster
    # carries the full alias list from C1 so chunks mentioning ANY alias get
    # the cluster's score added exactly once.
    print(f"{'=' * 60}\n[C2] mapping clusters → top-5 chunks\n")
    fake_clusters = [
        {"aliases": clusters.get("amd", ["amd"]),   "score": 2.0},
        {"aliases": clusters.get("tsmc", ["tsmc"]), "score": 1.0},
    ]
    print(f"  Input clusters:")
    for c in fake_clusters:
        print(f"    aliases={c['aliases']!r}  score={c['score']}")

    chunks = _map_chunks(fake_clusters, top_k=5)
    print(f"\n  Top-{len(chunks)} chunks by aggregated score:")
    for ch in chunks:
        preview = ch["text"][:120].replace("\n", " ")
        print(f"    score={ch['score']:.3f}  "
              f"[{ch['ticker']} FY{ch['fiscal_year']} {ch['section']}]")
        print(f"      id: {ch['chunk_id']}")
        print(f"      └─ {preview}...")
        print()

    # --- C3 end-to-end test: 4-query suite (Phase C1b C3 validation set) ---
    print(f"{'=' * 60}\n[C3] full graph_search pipeline\n")
    for q in [
        "AMD",
        "TSMC supply chain",
        "china semiconductor ban",
        "Hopper data center segment revenue",
    ]:
        print(f"\n--- Query: {q!r} ---")
        results = graph_search(q, top_k_chunks=3)
        for i, ch in enumerate(results, start=1):
            preview = ch["text"][:120].replace("\n", " ")
            print(f"  #{i}  score={ch['score']:.3f}  "
                  f"[{ch['ticker']} FY{ch['fiscal_year']} {ch['section']}]")
            print(f"      └─ {preview}...")
