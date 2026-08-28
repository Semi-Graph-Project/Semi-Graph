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
from semigraph.online.ppr import run_passage_ppr, run_ppr
from semigraph.online.query_expand import expand_query
from semigraph.online.rerank import company_rerank, fiscal_year_rerank
from semigraph.online.seed import (
    query_to_chunk_seeds,
    query_to_triple_candidates,
    query_to_hybrid_seeds,
    query_to_seeds,
    query_to_triple_seeds,
    triple_candidates_to_seeds,
)
from semigraph.online.triple_filter import filter_triple_candidates
from semigraph.online.vector_search import DEFAULT_VECTOR_INDEX
from semigraph.trace import TraceCallback, notify_trace


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
MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
WHERE e.name IN cluster.aliases
WITH
  c,
  cluster.aliases AS cluster_aliases,
  cluster.score AS cluster_score,
  collect(DISTINCT e.name) AS matched_aliases_for_cluster
WITH
  c,
  sum(cluster_score) AS score,
  collect({
    cluster_aliases: cluster_aliases,
    matched_aliases: matched_aliases_for_cluster,
    cluster_score: cluster_score
  }) AS matched_clusters,
  collect(matched_aliases_for_cluster) AS matched_alias_groups
WITH
  c,
  score,
  matched_clusters,
  reduce(acc = [], group IN matched_alias_groups | acc + group) AS matched_aliases
RETURN c.chunk_id AS chunk_id,
       c.text AS text,
       c.ticker AS ticker,
       c.fiscal_year AS fiscal_year,
       c.section AS section,
       score,
       matched_aliases,
       matched_clusters,
       size(matched_clusters) AS matched_cluster_count
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
            "matched_aliases": r["matched_aliases"],
            "matched_cluster_count": r["matched_cluster_count"],
            "matched_clusters": r["matched_clusters"],
        }
        for r in rows
    ]


def _collapse_clusters(
    ppr_entities: list[dict],
    cluster_map: dict[str, list[str]],
) -> list[dict]:
    """
    entity + clus_name => SUM up each cluster's aliases and return
    [{group , group_score}] 
    
    Group PPR entities by alias cluster; SUM PPR scores per cluster.

    Args:
        ppr_entities: Output of `run_ppr` — `[{name, type, score}, ...]`.
        cluster_map:  Output of `_cluster_aliases` —
                      `{seed_name: [alias_1, alias_2, ...]}`.

    Returns:
        `[{aliases: [...], score: float}, ...]` ready for `_map_chunks`.
        Order: highest cluster score first (deterministic).
    """
    name_to_score: dict[str, float] = {}
    for entity in ppr_entities:
        name = str(entity.get("name", ""))
        if not name:
            continue
        score = float(entity.get("score") or 0.0)
        name_to_score[name] = max(name_to_score.get(name, 0.0), score)
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
        cluster_score = sum(name_to_score.get(a, 0.0) for a in set(aliases))
        entries.append({"aliases": list(aliases), "score": cluster_score})

    entries.sort(key=lambda c: c["score"], reverse=True)
    return entries


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
    if seed_mode == "hybrid":
        return query_to_hybrid_seeds(
            query,
            top_k_nodes=top_k_triples,
            top_k_triples=top_k_triples,
            cfg=cfg,
        ), {"mode": triple_filter_mode, "applied": False, "reason": "hybrid_mode"}
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
    ppr_graph_mode: str = "entity_only",
    graph_triple_filter: str = "none",
    cfg: Optional[Config] = None,
    trace_callback: TraceCallback | None = None,
) -> dict:
    """Run graph retrieval and return both chunks and stage-level trace.

    query expansion -> seeds -> PPR entities -> alias clusters -> chunk
    candidates -> company/year reranking -> final chunks.
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
        "cluster_entries": [],
        "chunk_candidates": [],
        "raw_chunk_candidates": [],
        "reranked_chunks": [],
        "reranker_trace": {"mode": "company+fiscal_year", "status": "not_run"},
        "chunks": [],
        "abort_reason": None,
        "ppr_graph_mode": ppr_graph_mode,
        "ppr_seed_weight_mode": ppr_seed_weight_mode,
        "graph_triple_filter": graph_triple_filter,
    }

    if seed_mode == "chunk_only" and ppr_graph_mode != "entity_chunk":
        raise ValueError(
            "chunk_only seed mode requires ppr_graph_mode='entity_chunk'"
        )

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
            "graph_mode": ppr_graph_mode,
            "damping": damping,
            "seed_weight_mode": ppr_seed_weight_mode,
            "seed_count": len(seeds),
        },
    })
    if ppr_graph_mode == "entity_chunk":
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
        # trace["reranked_chunks"] = trace["raw_chunk_candidates"]
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

    ppr_entities = run_ppr(
        seeds,
        top_k=top_k_entities,
        damping=damping,
        seed_weight_mode=ppr_seed_weight_mode,
        cfg=cfg,
    )
    trace["ppr_entities"] = ppr_entities
    notify_trace(trace_callback, {
        "stage": "personalized_pagerank",
        "status": "complete",
        "message": f"Ranked {len(ppr_entities)} graph entities",
        "details": {
            "entity_count": len(ppr_entities),
            "top_entities": [
                {
                    key: entity[key]
                    for key in ("name", "type", "score")
                    if entity.get(key) is not None
                }
                for entity in ppr_entities[:20]
            ],
        },
    })
    if not ppr_entities:
        trace["abort_reason"] = "empty_ppr"
        notify_trace(trace_callback, {
            "stage": "retrieval_complete",
            "status": "complete",
            "message": "Graph retrieval stopped because PageRank returned no entities",
            "details": {"abort_reason": "empty_ppr"},
        })
        print("[graph_search] PPR returned empty — aborting")
        return trace

    notify_trace(trace_callback, {
        "stage": "alias_clustering",
        "status": "running",
        "message": "Grouping aliases for ranked entities",
        "details": {"entity_count": len(ppr_entities)},
    })
    cluster_map = _cluster_aliases(
        [e["name"] for e in ppr_entities],
        cfg=cfg,
    )

    cluster_entries = _collapse_clusters(ppr_entities, cluster_map)
    trace["cluster_entries"] = cluster_entries
    notify_trace(trace_callback, {
        "stage": "alias_clustering",
        "status": "complete",
        "message": f"Collapsed entities into {len(cluster_entries)} clusters",
        "details": {"cluster_count": len(cluster_entries)},
    })
    # print(f"[graph_search] {len(ppr_entities)} PPR entities → "
    #       f"{len(cluster_entries)} unique clusters")

    notify_trace(trace_callback, {
        "stage": "chunk_mapping",
        "status": "running",
        "message": "Mapping ranked entity clusters to evidence chunks",
        "details": {"candidate_pool_k": candidate_pool_k},
    })
    chunk_candidates = _map_chunks(cluster_entries, top_k=candidate_pool_k, cfg=cfg)
    trace["chunk_candidates"] = chunk_candidates
    trace["raw_chunk_candidates"] = chunk_candidates
    trace["reranked_chunks"] = fiscal_year_rerank(
        query,
        company_rerank(query, chunk_candidates, cfg=cfg),
    )
    trace["chunks"] = trace["reranked_chunks"][:top_k_chunks]
    trace["reranker_trace"] = {
        "mode": "company+fiscal_year",
        "status": "complete",
        "candidate_count": len(trace["reranked_chunks"]),
        "returned_count": len(trace["chunks"]),
    }
    notify_trace(trace_callback, {
        "stage": "chunk_mapping",
        "status": "complete",
        "message": f"Mapped graph evidence to {len(chunk_candidates)} candidates",
        "details": {
            "candidate_count": len(chunk_candidates),
            "candidate_chunk_ids": [
                str(chunk["chunk_id"])
                for chunk in chunk_candidates[:20]
                if chunk.get("chunk_id")
            ],
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
    # print(f"[graph_search] returning {len(trace['chunks'])} chunks")
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
    ppr_graph_mode: str = "entity_only",
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
        ppr_graph_mode=ppr_graph_mode,
        graph_triple_filter=graph_triple_filter,
        cfg=cfg,
    )
    return trace["chunks"]


if __name__ == "__main__":
    #debug map_chunks
    fake_clusters_entries =  [
        {"aliases": ["amd"], "score": 1.0},
        {"aliases": ["tsmc"], "score": 1.0},
    ]

    _map_chunks(fake_clusters_entries, top_k=5)
