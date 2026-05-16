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

from typing import Optional

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.online.ppr import run_ppr
from semigraph.online.seed import query_to_triple_seeds


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


def graph_search(
    query: str,
    top_k_chunks: int = 5,
    top_k_entities: int = 20,
    damping: float = 0.85,
    cfg: Optional[Config] = None,
) -> list[dict]:
    """Full graph_search pipeline: query → top-k chunks ranked by PPR mass.

    Composes Phase C1a/C1b/C1b+ + this module's C1/C2:

        query
          → query_to_triple_seeds       (HippoRAG v2 linker)
          → run_ppr                     (Personalized PageRank top-k)
          → _cluster_aliases            (collapse SYNONYM_OF cluster)
          → _collapse_clusters          (SUM PPR scores per cluster)
          → _map_chunks                 (MENTIONS → chunk + SUM cluster scores)

    Args:
        query:          Natural-language question.
        top_k_chunks:   Number of chunks to return for downstream LLM context.
        top_k_entities: PPR top-k cap. Pick 3-5x `top_k_chunks` so each chunk
                        receives signal from multiple entities (multi-hop).
        damping:        PageRank damping (0.85 = HippoRAG default; lower
                        narrows walk to seeds, higher leaks to global hubs).
        cfg:            Optional Config; defaults to cached singleton.

    Returns:
        `[{chunk_id, text, ticker, fiscal_year, section, score}, ...]`
        Empty list if seeds is empty, PPR returns nothing, or no chunk
        mentions any retrieved entity.
    """
    print(f"[graph_search] query={query!r} "
          f"top_k_chunks={top_k_chunks} top_k_entities={top_k_entities}")

    seeds = query_to_triple_seeds(query, cfg=cfg)
    if not seeds:
        print("[graph_search] no seeds — aborting")
        return []

    ppr_entities = run_ppr(
        seeds,
        top_k=top_k_entities,
        damping=damping,
        cfg=cfg,
    )
    if not ppr_entities:
        print("[graph_search] PPR returned empty — aborting")
        return []

    cluster_map = _cluster_aliases(
        [e["name"] for e in ppr_entities],
        cfg=cfg,
    )

    cluster_entries = _collapse_clusters(ppr_entities, cluster_map)
    print(f"[graph_search] {len(ppr_entities)} PPR entities → "
          f"{len(cluster_entries)} unique clusters")

    chunks = _map_chunks(cluster_entries, top_k=top_k_chunks, cfg=cfg)
    print(f"[graph_search] returning {len(chunks)} chunks")
    return chunks


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
