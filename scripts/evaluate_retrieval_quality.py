from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


DEFAULT_QUERY_FILE = ROOT / "benchmark" / "datasets" / "phase_t_multihop_queries.yaml"
DEFAULT_OUTPUT_DIR = ROOT / "analytics" / "Report Experiment"
TOOL_CHOICES = ("vector", "graph", "hybrid")
SEED_MODE_CHOICES = ("triple", "node", "hybrid")
RERANK_MODE_CHOICES = ("legacy", "metadata")
PPR_GRAPH_MODE_CHOICES = ("entity_only", "entity_chunk")
TRIPLE_FILTER_CHOICES = ("none", "llm")
FINAL_RERANK_CHOICES = ("none", "cohere")
DEFAULT_TICKER_SCOPE = (
    "AMAT",
    "AMD",
    "AMKR",
    "AVGO",
    "COHR",
    "ENTG",
    "INTC",
    "KLAC",
    "LRCX",
    "MU",
    "NVDA",
    "QCOM",
    "RMBS",
    "TXN",
)


def _get_config():
    from semigraph.config import get_config

    return get_config()


def _build_metadata_rerank_params(args):
    from semigraph.online.graph_search import MetadataRerankParams

    return MetadataRerankParams(
        risk_section_boost=args.metadata_risk_section_boost,
        business_section_boost=args.metadata_business_section_boost,
        financial_section_boost=args.metadata_financial_section_boost,
        ticker_boost=args.metadata_ticker_boost,
        cluster_boost_per_extra=args.metadata_cluster_boost_per_extra,
        cluster_boost_cap=args.metadata_cluster_boost_cap,
        latest_year_boost=args.metadata_latest_year_boost,
        latest_year_min=args.metadata_latest_year_min,
        lexical_match_weight=args.metadata_lexical_match_weight,
        lexical_boost_cap=args.metadata_lexical_boost_cap,
        broad_penalty_enabled=not args.disable_broad_penalty,
        broad_penalty_floor=args.metadata_broad_penalty_floor,
        broad_penalty_step=args.metadata_broad_penalty_step,
        broad_penalty_zero_match=args.metadata_broad_penalty_zero_match,
        broad_penalty_short_token_cutoff=args.metadata_broad_penalty_short_cutoff,
        broad_penalty_mid_token_cutoff=args.metadata_broad_penalty_mid_cutoff,
        broad_penalty_long_token_cutoff=args.metadata_broad_penalty_long_cutoff,
    )


def _get_corpus_chunk_count(cfg) -> int:
    from semigraph.connections import get_neo4j_driver

    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            row = session.run("MATCH (c:Chunk) RETURN count(c) AS n").single()
            return int(row["n"] or 0) if row else 0
    finally:
        driver.close()


def _get_existing_entities(cfg, names: list[str]) -> set[str]:
    from semigraph.connections import get_neo4j_driver

    unique_names = sorted({name for name in names if name})
    if not unique_names:
        return set()

    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            rows = list(session.run(
                """
                UNWIND $names AS name
                MATCH (e:Entity {name: name})
                RETURN DISTINCT e.name AS name
                """,
                names=unique_names,
            ))
            return {str(row["name"]) for row in rows}
    finally:
        driver.close()


def _get_tool(
    tool_name: str,
    use_graph_expansion: bool = True,
    graph_seed_mode: str = "triple",
    graph_rerank_mode: str = "legacy",
    candidate_pool_k: int = 100,
    graph_top_k_entities: int = 20,
    graph_top_k_triples: int = 8,
    graph_damping: float = 0.5,
    metadata_rerank_params=None,
    graph_ppr_mode: str = "entity_only",
    graph_triple_filter: str = "none",
):
    if tool_name == "vector":
        from semigraph.online.vector_search import vector_search

        return vector_search
    if tool_name == "graph":
        from semigraph.online.graph_search import graph_search

        def _graph(query: str, top_k_chunks: int, cfg):
            return graph_search(
                query,
                top_k_chunks=top_k_chunks,
                use_expansion=use_graph_expansion,
                seed_mode=graph_seed_mode,
                rerank_mode=graph_rerank_mode,
                candidate_pool_k=candidate_pool_k,
                top_k_entities=graph_top_k_entities,
                top_k_triples=graph_top_k_triples,
                damping=graph_damping,
                metadata_rerank_params=metadata_rerank_params,
                ppr_graph_mode=graph_ppr_mode,
                graph_triple_filter=graph_triple_filter,
                cfg=cfg,
            )

        return _graph
    if tool_name == "hybrid":
        from semigraph.online.hybrid_search import hybrid_search

        def _hybrid(query: str, top_k_chunks: int, cfg):
            return hybrid_search(
                query,
                top_k_chunks=top_k_chunks,
                graph_use_expansion=use_graph_expansion,
                graph_seed_mode=graph_seed_mode,
                graph_rerank_mode=graph_rerank_mode,
                candidate_pool_k=candidate_pool_k,
                graph_top_k_entities=graph_top_k_entities,
                graph_top_k_triples=graph_top_k_triples,
                graph_damping=graph_damping,
                metadata_rerank_params=metadata_rerank_params,
                ppr_graph_mode=graph_ppr_mode,
                graph_triple_filter=graph_triple_filter,
                cfg=cfg,
            )

        return _hybrid
    raise ValueError(f"Unknown retrieval tool: {tool_name}")


def _load_queries(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    queries = data.get("queries", []) if isinstance(data, dict) else []
    if not isinstance(queries, list):
        raise ValueError(f"{path} must contain a top-level 'queries' list")
    return queries


def _normalize_entity(name: str) -> str:
    return " ".join(str(name).strip().lower().split())


def _reference_gold_entities(item: dict) -> list[str]:
    return [
        _normalize_entity(name)
        for name in item.get("gold_entities", [])
        if _normalize_entity(name)
    ]


def _gold_entity_alias_groups(item: dict) -> dict[str, set[str]]:
    """Return each reference entity with its accepted graph-name aliases."""
    raw_aliases = item.get("gold_entity_aliases") or {}
    groups: dict[str, set[str]] = {}
    for reference in _reference_gold_entities(item):
        alternatives = {reference}
        if isinstance(raw_aliases, dict):
            alternatives.update(
                _normalize_entity(alias)
                for alias in raw_aliases.get(reference, [])
                if _normalize_entity(alias)
            )
        groups[reference] = alternatives
    return groups


def _gold_entities(item: dict) -> list[str]:
    """Flatten reference entities and verified aliases for hit diagnostics."""
    return sorted({
        entity
        for alternatives in _gold_entity_alias_groups(item).values()
        for entity in alternatives
    })


def _missing_gold_entity_groups(
    item: dict,
    existing_entities: set[str],
) -> list[str]:
    """A reference is missing only when none of its alternatives exist."""
    return [
        reference
        for reference, alternatives in _gold_entity_alias_groups(item).items()
        if not alternatives & existing_entities
    ]


def _gold_chunk_tickers(item: dict) -> set[str]:
    tickers: set[str] = set()
    for chunk_id in item.get("gold_chunks", []) or []:
        prefix = str(chunk_id).split("_", 1)[0].upper()
        if prefix:
            tickers.add(prefix)
    return tickers


def _mentioned_tickers(item: dict, known_tickers: set[str]) -> set[str]:
    haystack = " ".join(
        [
            str(item.get("query", "")),
            " ".join(str(e) for e in item.get("gold_entities", []) or []),
        ]
    ).upper()
    terms = set(haystack.replace("-", " ").replace("/", " ").split())
    return {ticker for ticker in known_tickers if ticker in terms}


def _classify_subset(
    item: dict,
    reextract_tickers: set[str],
    known_tickers: set[str],
) -> str:
    involved = _gold_chunk_tickers(item) | _mentioned_tickers(item, known_tickers)
    if involved & reextract_tickers:
        if involved - reextract_tickers:
            return "mixed_subset"
        return "reextract_subset"
    return "legacy_subset"


def _resolve_ticker_scope(raw_value: str, known_tickers: set[str]) -> set[str]:
    """Resolve the subset-reporting ticker scope.

    `all` means the current config's corpus tickers. This is the default now
    that the new extraction/repair pipeline is treated as the normal corpus.
    A comma-separated list is still accepted for historical comparisons.
    """
    value = str(raw_value or "").strip()
    if not value or value.lower() == "all":
        return set(known_tickers)
    return {
        ticker.strip().upper()
        for ticker in value.split(",")
        if ticker.strip()
    }


def _chunk_ids(chunks: list[dict], k: int) -> list[str]:
    return [
        str(chunk.get("chunk_id", ""))
        for chunk in chunks[:k]
        if chunk.get("chunk_id")
    ]


def _retrieval_trace_summary(trace: dict | None, top_k: int) -> dict | None:
    """Keep comparable raw/reranked IDs without duplicating chunk text."""
    if trace is None:
        return None

    candidates = trace.get(
        "raw_chunk_candidates",
        trace.get("chunk_candidates", []),
    )
    return {
        "candidate_pool_count": len(candidates),
        "candidate_pool_ids": _chunk_ids(candidates, len(candidates)),
        "raw_top_k_ids": _chunk_ids(candidates, top_k),
        "reranked_ids": _chunk_ids(trace.get("reranked_chunks", []), top_k),
        "final_rerank": trace.get("final_rerank", "none"),
        "reranker_trace": trace.get("reranker_trace", {}),
    }


def _score_result(returned_ids: list[str], gold_ids: list[str]) -> dict:
    if not gold_ids:
        return {
            "scored": False,
            "hit": None,
            "recall": None,
            "mrr": None,
            "hits": [],
        }

    gold = set(gold_ids)
    hits = [cid for cid in returned_ids if cid in gold]
    first_hit_rank = next(
        (idx for idx, cid in enumerate(returned_ids, start=1) if cid in gold),
        None,
    )
    return {
        "scored": True,
        "hit": 1 if hits else 0,
        "recall": len(set(hits)) / len(gold),
        "mrr": 1 / first_hit_rank if first_hit_rank else 0.0,
        "hits": hits,
    }


def _gold_evidence_groups(item: dict, gold_chunks: list[str]) -> dict[str, list[str]]:
    """Return evidence groups used for answer-level retrieval scoring.

    `gold_chunks` is a flat qrels-style list. It is useful for ChunkHit and
    diagnostic ChunkRecall, but it unfairly punishes alternative evidence
    chunks that say the same thing. Evidence groups model the answer
    requirements: a group is satisfied when any chunk in that group is found.

    If a query has no explicit groups, treat all gold chunks as one group. This
    keeps legacy/single-hop queries scored while making duplicate-year evidence
    behave like alternatives.
    """
    raw_groups = item.get("gold_evidence_groups") or {}
    groups: dict[str, list[str]] = {}
    if isinstance(raw_groups, dict):
        for name, chunk_ids in raw_groups.items():
            if not isinstance(chunk_ids, list):
                continue
            cleaned = [str(cid) for cid in chunk_ids if cid]
            if cleaned:
                groups[str(name)] = cleaned

    if groups:
        return groups
    if gold_chunks:
        return {"gold_chunks": gold_chunks}
    return {}


def _score_group_result(
    returned_ids: list[str],
    evidence_groups: dict[str, list[str]],
) -> dict:
    if not evidence_groups:
        return {
            "scored": False,
            "group_recall": None,
            "answerable": None,
            "group_hits": {},
        }

    returned = set(returned_ids)
    group_hits = {
        group_name: sorted(returned & set(chunk_ids))
        for group_name, chunk_ids in evidence_groups.items()
    }
    satisfied = sum(1 for hits in group_hits.values() if hits)
    total = len(evidence_groups)
    return {
        "scored": True,
        "group_recall": satisfied / total if total else None,
        "answerable": 1 if satisfied == total else 0,
        "group_hits": group_hits,
    }


def _random_hit_probability(corpus_size: int, gold_count: int, k: int) -> float | None:
    """Probability that random top-k retrieval hits at least one gold chunk.

    This is the benchmark's "chance baseline": if we randomly sampled `k`
    chunks without replacement from the whole corpus, how often would at least
    one of them be a gold chunk?
    """
    if corpus_size <= 0 or gold_count <= 0 or k <= 0:
        return None

    k = min(k, corpus_size)
    gold_count = min(gold_count, corpus_size)
    non_gold_count = corpus_size - gold_count
    if non_gold_count <= 0:
        return 1.0

    no_hit = 1.0
    for i in range(k):
        denominator = corpus_size - i
        if denominator <= 0:
            break
        no_hit *= max(non_gold_count - i, 0) / denominator
    return 1.0 - no_hit


def _unscored_result() -> dict:
    return {
        "scored": False,
        "hit": None,
        "recall": None,
        "mrr": None,
        "hits": [],
    }


def _hit_from_names(names: set[str], gold_entities: list[str]) -> int | None:
    if not gold_entities:
        return None
    return 1 if names & set(gold_entities) else 0


def _graph_stage_metrics(
    trace: dict | None,
    gold_entities: list[str],
    gold_chunks: list[str],
    missing_gold_entities: list[str],
    score_at_k: dict,
    score_at_oracle: dict,
    error: str | None,
    returned_chunk_ids: list[str] | None = None,
) -> dict:
    if trace is None:
        return {
            "seed_hit": None,
            "ppr_hit": None,
            "chunk_map_hit": None,
            "direct_ppr_chunk_hit": None,
            "bottleneck_label": "not_applicable",
        }

    seed_names = {
        _normalize_entity(seed.get("name", ""))
        for seed in trace.get("seeds", [])
        if seed.get("name")
    }
    ppr_names = {
        _normalize_entity(entity.get("name", ""))
        for entity in trace.get("ppr_entities", [])
        if entity.get("name")
    }
    for cluster in trace.get("cluster_entries", []):
        ppr_names.update(
            _normalize_entity(alias)
            for alias in cluster.get("aliases", [])
            if alias
        )

    candidate_ids = {
        str(chunk.get("chunk_id", ""))
        for chunk in trace.get("chunk_candidates", [])
        if chunk.get("chunk_id")
    }

    seed_hit = _hit_from_names(seed_names, gold_entities)
    ppr_hit = _hit_from_names(ppr_names, gold_entities)
    direct_ppr = trace.get("ppr_graph_mode") == "entity_chunk"
    chunk_map_hit = None if direct_ppr else 0
    if gold_chunks and not direct_ppr:
        chunk_map_hit = 1 if candidate_ids & set(gold_chunks) else 0
    direct_ppr_chunk_hit = None
    if direct_ppr and gold_chunks:
        direct_ppr_chunk_hit = int(
            bool(set(returned_chunk_ids or []) & set(gold_chunks))
        )

    if not gold_chunks:
        bottleneck = "unscored_discovery"
    elif error:
        bottleneck = "tool_error"
    elif score_at_k["hit"] == 1:
        bottleneck = "hit_top_k"
    elif missing_gold_entities:
        bottleneck = "corpus_not_ready"
    elif seed_hit == 0:
        bottleneck = "seed_loss"
    elif ppr_hit == 0:
        bottleneck = "ppr_loss"
    elif direct_ppr and direct_ppr_chunk_hit == 0:
        bottleneck = "direct_ppr_chunk_loss"
    elif chunk_map_hit == 0:
        bottleneck = "chunk_mapping_loss"
    elif score_at_oracle["hit"] == 1:
        bottleneck = "rerank_loss"
    else:
        bottleneck = "candidate_pool_loss"

    return {
        "seed_hit": seed_hit,
        "ppr_hit": ppr_hit,
        "chunk_map_hit": chunk_map_hit,
        "direct_ppr_chunk_hit": direct_ppr_chunk_hit,
        "ppr_graph_mode": trace.get("ppr_graph_mode", "entity_only"),
        "bottleneck_label": bottleneck,
        "abort_reason": trace.get("abort_reason"),
        "effective_query": trace.get("effective_query"),
        "seed_mode": trace.get("seed_mode"),
        "seed_names": sorted(seed_names),
        "ppr_entity_names": [
            str(entity.get("name", ""))
            for entity in trace.get("ppr_entities", [])[:20]
            if entity.get("name")
        ],
        "chunk_candidate_ids": _chunk_ids(
            trace.get("chunk_candidates", []),
            len(trace.get("chunk_candidates", [])),
        ),
    }


def _run_tool(
    tool_name: str,
    query: str,
    top_k: int,
    cfg,
    use_graph_expansion: bool,
    graph_seed_mode: str,
    graph_rerank_mode: str,
    candidate_pool_k: int,
    graph_top_k_entities: int,
    graph_top_k_triples: int,
    graph_damping: float,
    seed_weight_mode: str,
    metadata_rerank_params,
    graph_ppr_mode: str,
    graph_triple_filter: str,
    final_rerank: str,
) -> tuple[list[dict], str | None, float, dict | None]:
    started = time.time()
    try:
        if tool_name == "vector":
            from semigraph.online.vector_search import trace_vector_search

            trace = trace_vector_search(
                query,
                top_k_chunks=top_k,
                candidate_pool_k=candidate_pool_k,
                final_rerank=final_rerank,
                cfg=cfg,
            )
            return trace["chunks"], None, time.time() - started, trace

        if tool_name == "graph":
            from semigraph.online.graph_search import trace_graph_search

            trace = trace_graph_search(
                query,
                top_k_chunks=top_k,
                use_expansion=use_graph_expansion,
                seed_mode=graph_seed_mode,
                cfg=cfg,
                top_k_entities=graph_top_k_entities,
                top_k_triples=graph_top_k_triples,
                damping=graph_damping,
                rerank_mode=graph_rerank_mode,
                candidate_pool_k=candidate_pool_k,
                ppr_seed_weight_mode=seed_weight_mode,
                metadata_rerank_params=metadata_rerank_params,
                ppr_graph_mode=graph_ppr_mode,
                graph_triple_filter=graph_triple_filter,
                final_rerank=final_rerank,
            )
            return trace["chunks"], None, time.time() - started, trace

        chunks = _get_tool(
            tool_name,
            use_graph_expansion=use_graph_expansion,
            graph_seed_mode=graph_seed_mode,
            graph_rerank_mode=graph_rerank_mode,
            candidate_pool_k=candidate_pool_k,
            graph_top_k_entities=graph_top_k_entities,
            graph_top_k_triples=graph_top_k_triples,
            graph_damping=graph_damping,
            metadata_rerank_params=metadata_rerank_params,
            graph_ppr_mode=graph_ppr_mode,
            graph_triple_filter=graph_triple_filter,
        )(query, top_k_chunks=top_k, cfg=cfg)
        return chunks, None, time.time() - started, None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}", time.time() - started, None


def _evaluate_query(
    item: dict,
    tools: list[str],
    top_k: int,
    oracle_k: int,
    cfg,
    dry_run: bool,
    use_graph_expansion: bool,
    graph_seed_mode: str,
    corpus_size: int,
    subset: str,
    existing_entities: set[str],
    graph_rerank_mode: str,
    candidate_pool_k: int,
    graph_top_k_entities: int,
    graph_top_k_triples: int,
    graph_damping: float,
    seed_weight_mode: str,
    metadata_rerank_params,
    graph_ppr_mode: str,
    graph_triple_filter: str,
    final_rerank: str,
) -> dict:
    query = str(item.get("query", "")).strip()
    gold_chunks = [str(cid) for cid in item.get("gold_chunks", []) if cid]
    evidence_groups = _gold_evidence_groups(item, gold_chunks)
    gold_entities = _gold_entities(item)
    missing_gold_entities = _missing_gold_entity_groups(item, existing_entities)
    if not gold_chunks:
        corpus_status = "unscored_discovery"
    elif missing_gold_entities:
        corpus_status = "missing_gold_entities"
    else:
        corpus_status = "ready"

    result = {
        "id": item.get("id", ""),
        "query": query,
        "type": item.get("type", ""),
        "subset": subset,
        "gold_tools": item.get("gold_tools", []),
        "gold_entities": gold_entities,
        "reference_gold_entities": _reference_gold_entities(item),
        "gold_entity_aliases": item.get("gold_entity_aliases", {}),
        "missing_gold_entities": missing_gold_entities,
        "corpus_status": corpus_status,
        "gold_chunks": gold_chunks,
        "gold_evidence_groups": evidence_groups,
        "answer_points": item.get("answer_points", []),
        "tools": {},
    }
    chance_hit_at_k = _random_hit_probability(
        corpus_size=corpus_size,
        gold_count=len(gold_chunks),
        k=top_k,
    )
    chance_hit_at_oracle = _random_hit_probability(
        corpus_size=corpus_size,
        gold_count=len(gold_chunks),
        k=oracle_k,
    )

    for tool_name in tools:
        if dry_run:
            chunks, error, latency, trace = [], None, 0.0, None
        else:
            chunks, error, latency, trace = _run_tool(
                tool_name=tool_name,
                query=query,
                top_k=max(top_k, oracle_k),
                cfg=cfg,
                use_graph_expansion=use_graph_expansion,
                graph_seed_mode=graph_seed_mode,
                graph_rerank_mode=graph_rerank_mode,
                candidate_pool_k=candidate_pool_k,
                graph_top_k_entities=graph_top_k_entities,
                graph_top_k_triples=graph_top_k_triples,
                graph_damping=graph_damping,
                seed_weight_mode=seed_weight_mode,
                metadata_rerank_params=metadata_rerank_params,
                graph_ppr_mode=graph_ppr_mode,
                graph_triple_filter=graph_triple_filter,
                final_rerank=final_rerank,
            )

        returned_at_k = _chunk_ids(chunks, top_k)
        returned_at_oracle = _chunk_ids(chunks, oracle_k)
        if dry_run:
            score_at_k = _unscored_result()
            score_at_oracle = _unscored_result()
            group_score_at_k = _score_group_result([], {})
            group_score_at_oracle = _score_group_result([], {})
        else:
            score_at_k = _score_result(returned_at_k, gold_chunks)
            score_at_oracle = _score_result(returned_at_oracle, gold_chunks)
            group_score_at_k = _score_group_result(
                returned_at_k,
                evidence_groups,
            )
            group_score_at_oracle = _score_group_result(
                returned_at_oracle,
                evidence_groups,
            )

        stage = _graph_stage_metrics(
            trace=trace if tool_name == "graph" else None,
            gold_entities=gold_entities,
            gold_chunks=gold_chunks,
            missing_gold_entities=missing_gold_entities,
            score_at_k=score_at_k,
            score_at_oracle=score_at_oracle,
            error=error,
            returned_chunk_ids=returned_at_k,
        )
        result["tools"][tool_name] = {
            "latency_sec": round(latency, 3),
            "error": error,
            "returned_chunk_ids": returned_at_k,
            "oracle_chunk_ids": returned_at_oracle,
            "chunk_hit_at_k": score_at_k["hit"],
            "chunk_recall_at_k": score_at_k["recall"],
            "chunk_mrr_at_k": score_at_k["mrr"],
            "chunk_hits_at_k": score_at_k["hits"],
            "group_recall_at_k": group_score_at_k["group_recall"],
            "answerable_at_k": group_score_at_k["answerable"],
            "group_hits_at_k": group_score_at_k["group_hits"],
            "hit_at_k": score_at_k["hit"],
            "recall_at_k": score_at_k["recall"],
            "mrr_at_k": score_at_k["mrr"],
            "hits_at_k": score_at_k["hits"],
            "direct_ppr_chunk_hit": stage.get("direct_ppr_chunk_hit"),
            "chance_hit_at_k": chance_hit_at_k if score_at_k["scored"] else None,
            "oracle_chunk_hit": score_at_oracle["hit"],
            "oracle_chunk_recall": score_at_oracle["recall"],
            "oracle_group_recall": group_score_at_oracle["group_recall"],
            "oracle_answerable": group_score_at_oracle["answerable"],
            "oracle_group_hits": group_score_at_oracle["group_hits"],
            "oracle_hit": score_at_oracle["hit"],
            "oracle_recall": score_at_oracle["recall"],
            "oracle_hits": score_at_oracle["hits"],
            "chance_oracle_hit": chance_hit_at_oracle if score_at_oracle["scored"] else None,
            "retrieval_trace": _retrieval_trace_summary(trace, top_k),
            "stage": stage,
        }

    return result


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _metric_bucket() -> dict[str, list[float]]:
    return defaultdict(list)


def _add_tool_metrics(bucket: dict, tool_name: str, metrics: dict) -> None:
    chunk_hit = metrics.get("chunk_hit_at_k", metrics.get("hit_at_k"))
    chunk_recall = metrics.get("chunk_recall_at_k", metrics.get("recall_at_k"))
    group_recall = metrics.get("group_recall_at_k", chunk_recall)
    answerable = metrics.get("answerable_at_k", chunk_hit)

    bucket[tool_name]["chunk_hit"].append(float(chunk_hit))
    bucket[tool_name]["chunk_recall"].append(float(chunk_recall))
    if group_recall is not None:
        bucket[tool_name]["group_recall"].append(float(group_recall))
    if answerable is not None:
        bucket[tool_name]["answerable"].append(float(answerable))
    bucket[tool_name]["mrr"].append(float(metrics["mrr_at_k"]))
    bucket[tool_name]["oracle_hit"].append(float(metrics["oracle_hit"]))


def _summarize_grouped_metrics(grouped: dict, tools: list[str], key_name: str) -> list[dict]:
    rows: list[dict] = []
    for group in sorted(grouped):
        row = {key_name: group}
        for tool_name in tools:
            row[f"{tool_name}_chunk_hit"] = _mean(
                grouped[group][tool_name]["chunk_hit"]
            )
            row[f"{tool_name}_chunk_recall"] = _mean(
                grouped[group][tool_name]["chunk_recall"]
            )
            row[f"{tool_name}_group_recall"] = _mean(
                grouped[group][tool_name]["group_recall"]
            )
            row[f"{tool_name}_answerable"] = _mean(
                grouped[group][tool_name]["answerable"]
            )
            row[f"{tool_name}_mrr"] = _mean(grouped[group][tool_name]["mrr"])
            row[f"{tool_name}_oracle_hit"] = _mean(
                grouped[group][tool_name]["oracle_hit"]
            )
            # Backward-compatible aliases for older tests/reports.
            row[f"{tool_name}_hit"] = row[f"{tool_name}_chunk_hit"]
            row[f"{tool_name}_recall"] = row[f"{tool_name}_chunk_recall"]
        rows.append(row)
    return rows


def _paired_recall_test(
    results: list[dict],
    compare_tool: str,
    subset: str | None = None,
    baseline_tool: str = "vector",
    metric_key: str = "group_recall_at_k",
    iterations: int = 10000,
) -> dict:
    diffs: list[float] = []
    for row in results:
        if subset is not None and row.get("subset") != subset:
            continue
        tools = row.get("tools", {})
        if baseline_tool not in tools or compare_tool not in tools:
            continue
        base = tools[baseline_tool].get(metric_key)
        comp = tools[compare_tool].get(metric_key)
        if base is None or comp is None:
            continue
        diffs.append(float(comp) - float(base))

    observed = _mean(diffs)
    if len(diffs) < 2:
        return {
            "n": len(diffs),
            "mean_delta_recall": observed,
            "p_value_one_sided": None,
        }

    if observed <= 0:
        return {
            "n": len(diffs),
            "mean_delta_recall": observed,
            "p_value_one_sided": 1.0,
        }

    rng = random.Random(1337)
    more_extreme = 0
    for _ in range(iterations):
        signed_mean = _mean([
            diff if rng.random() < 0.5 else -diff
            for diff in diffs
        ])
        if signed_mean >= observed:
            more_extreme += 1

    return {
        "n": len(diffs),
        "mean_delta_recall": observed,
        "p_value_one_sided": (more_extreme + 1) / (iterations + 1),
    }


def _aggregate(results: list[dict], tools: list[str]) -> dict:
    aggregate: dict[str, dict] = {}
    by_type: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(_metric_bucket)
    )
    by_subset: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(_metric_bucket)
    )
    graph_stage = {
        "full_mixed": {
            "seed_hit": [],
            "ppr_hit": [],
            "chunk_map_hit": [],
            "direct_ppr_chunk_hit": [],
            "bottlenecks": Counter(),
        }
    }

    for tool_name in tools:
        chunk_hits: list[float] = []
        chunk_recalls: list[float] = []
        group_recalls: list[float] = []
        answerables: list[float] = []
        mrrs: list[float] = []
        oracle_hits: list[float] = []
        chance_hits: list[float] = []
        scored_count = 0
        errors = 0

        for row in results:
            metrics = row["tools"][tool_name]
            if metrics["error"]:
                errors += 1
            if metrics["hit_at_k"] is None:
                continue

            scored_count += 1
            chunk_hit = metrics.get("chunk_hit_at_k", metrics.get("hit_at_k"))
            chunk_recall = metrics.get("chunk_recall_at_k", metrics.get("recall_at_k"))
            group_recall = metrics.get("group_recall_at_k", chunk_recall)
            answerable = metrics.get("answerable_at_k", chunk_hit)
            chunk_hits.append(float(chunk_hit))
            chunk_recalls.append(float(chunk_recall))
            if group_recall is not None:
                group_recalls.append(float(group_recall))
            if answerable is not None:
                answerables.append(float(answerable))
            mrrs.append(float(metrics["mrr_at_k"]))
            oracle_hits.append(float(metrics["oracle_hit"]))
            if metrics["chance_hit_at_k"] is not None:
                chance_hits.append(float(metrics["chance_hit_at_k"]))

            qtype = row.get("type") or "unknown"
            _add_tool_metrics(by_type[qtype], tool_name, metrics)
            subset = row.get("subset") or "unknown_subset"
            _add_tool_metrics(by_subset[subset], tool_name, metrics)

            if tool_name == "graph":
                stage = metrics.get("stage", {})
                labels = ["full_mixed", subset]
                for label in labels:
                    graph_stage.setdefault(label, {
                        "seed_hit": [],
                        "ppr_hit": [],
                        "chunk_map_hit": [],
                        "direct_ppr_chunk_hit": [],
                        "bottlenecks": Counter(),
                    })
                    for metric_name in (
                        "seed_hit",
                        "ppr_hit",
                        "chunk_map_hit",
                        "direct_ppr_chunk_hit",
                    ):
                        value = stage.get(metric_name)
                        if value is not None:
                            graph_stage[label][metric_name].append(float(value))
                    graph_stage[label]["bottlenecks"][stage.get(
                        "bottleneck_label",
                        "unknown",
                    )] += 1

        random_baseline = _mean(chance_hits)
        chunk_hit_rate = _mean(chunk_hits)
        aggregate[tool_name] = {
            "scored_queries": scored_count,
            "errors": errors,
            "chunk_hit_rate": chunk_hit_rate,
            "avg_chunk_recall": _mean(chunk_recalls),
            "avg_group_recall": _mean(group_recalls),
            "answerable_rate": _mean(answerables),
            "hit_rate": chunk_hit_rate,
            "avg_recall": _mean(chunk_recalls),
            "avg_mrr": _mean(mrrs),
            "oracle_hit_rate": _mean(oracle_hits),
            "random_hit_baseline": random_baseline,
            "hit_minus_random": chunk_hit_rate - random_baseline,
            "hit_lift_vs_random": (
                chunk_hit_rate / random_baseline
                if random_baseline
                else None
            ),
        }

    stage_rows: list[dict] = []
    for subset, values in sorted(graph_stage.items()):
        stage_rows.append({
            "subset": subset,
            "seed_hit": _mean(values["seed_hit"]),
            "ppr_hit": _mean(values["ppr_hit"]),
            "chunk_map_hit": (
                _mean(values["chunk_map_hit"])
                if values["chunk_map_hit"]
                else None
            ),
            "direct_ppr_chunk_hit": (
                _mean(values["direct_ppr_chunk_hit"])
                if values["direct_ppr_chunk_hit"]
                else None
            ),
            "bottlenecks": dict(values["bottlenecks"]),
        })

    paired = {}
    if "vector" in tools:
        paired["full_mixed"] = {
            tool_name: _paired_recall_test(results, tool_name)
            for tool_name in tools
            if tool_name != "vector"
        }
        for subset in sorted(by_subset):
            paired[subset] = {
                tool_name: _paired_recall_test(results, tool_name, subset=subset)
                for tool_name in tools
                if tool_name != "vector"
            }

    return {
        "overall": aggregate,
        "by_type": _summarize_grouped_metrics(by_type, tools, "type"),
        "by_subset": _summarize_grouped_metrics(by_subset, tools, "subset"),
        "graph_stage": stage_rows,
        "paired_group_recall_vs_vector": paired,
        "paired_recall_vs_vector": paired,
    }


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _write_markdown(
    path: Path,
    query_file: Path,
    results: list[dict],
    aggregate: dict,
    tools: list[str],
    top_k: int,
    oracle_k: int,
    dry_run: bool,
    corpus_size: int,
    use_graph_expansion: bool,
    graph_seed_mode: str,
    graph_rerank_mode: str,
    candidate_pool_k: int,
    graph_top_k_entities: int,
    graph_top_k_triples: int,
    graph_damping: float,
    ppr_seed_weight_mode: str,
    graph_ppr_mode: str,
    graph_triple_filter: str,
    final_rerank: str,
    metadata_rerank_params,
    run_config: dict | None = None,
) -> None:
    lines: list[str] = []
    lines.append("# Phase T Retrieval Baseline")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Run Configuration")
    lines.append("")
    config_rows = {
        "script": "scripts/evaluate_retrieval_quality.py",
        "command": " ".join(sys.argv),
        "query_file": str(query_file),
        "query_count": len(results),
        "tools": ", ".join(tools),
        "top_k": top_k,
        "oracle_k": oracle_k,
        "dry_run": dry_run,
        "corpus_chunks": corpus_size,
        "graph_use_expansion": use_graph_expansion,
        "graph_seed_mode": graph_seed_mode,
        "graph_rerank_mode": graph_rerank_mode,
        "candidate_pool_k": candidate_pool_k,
        "graph_top_k_entities": graph_top_k_entities,
        "graph_top_k_triples": graph_top_k_triples,
        "graph_damping": graph_damping,
        "ppr_seed_weight_mode": ppr_seed_weight_mode,
        "graph_ppr_mode": graph_ppr_mode,
        "graph_triple_filter": graph_triple_filter,
        "final_rerank": final_rerank,
        "metadata_rerank_params": (
            metadata_rerank_params.to_dict()
            if hasattr(metadata_rerank_params, "to_dict")
            else metadata_rerank_params
        ),
    }
    if run_config:
        config_rows.update(run_config)
    for key, value in config_rows.items():
        if isinstance(value, (list, tuple, set)):
            value = ", ".join(str(item) for item in value)
        lines.append(f"- {key}: `{value}`")
    lines.append("")

    lines.append("## Overall")
    lines.append("")
    lines.append("| Tool | Scored Queries | Errors | ChunkHit@k | Random ChunkHit@k | Hit Lift | Hit-Random | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for tool_name in tools:
        row = aggregate["overall"][tool_name]
        lines.append(
            "| "
            f"{tool_name} | {row['scored_queries']} | {row['errors']} | "
            f"{row['chunk_hit_rate']:.3f} | "
            f"{_fmt(row['random_hit_baseline'])} | "
            f"{_fmt(row['hit_lift_vs_random'])} | "
            f"{_fmt(row['hit_minus_random'])} | "
            f"{row['avg_chunk_recall']:.3f} | "
            f"{row['avg_group_recall']:.3f} | "
            f"{row['answerable_rate']:.3f} | "
            f"{row['avg_mrr']:.3f} | {row['oracle_hit_rate']:.3f} |"
        )

    if aggregate["by_type"]:
        lines.append("")
        lines.append("## By Type")
        lines.append("")
        header = ["Type"]
        for tool_name in tools:
            header.extend([
                f"{tool_name} ChunkHit",
                f"{tool_name} ChunkRecall",
                f"{tool_name} GroupRecall",
                f"{tool_name} Answerable",
            ])
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] + ["---:"] * (len(header) - 1)) + "|")
        for row in aggregate["by_type"]:
            cells = [row["type"]]
            for tool_name in tools:
                cells.append(_fmt(row.get(f"{tool_name}_chunk_hit")))
                cells.append(_fmt(row.get(f"{tool_name}_chunk_recall")))
                cells.append(_fmt(row.get(f"{tool_name}_group_recall")))
                cells.append(_fmt(row.get(f"{tool_name}_answerable")))
            lines.append("| " + " | ".join(cells) + " |")

    if aggregate["by_subset"]:
        lines.append("")
        lines.append("## By Subset")
        lines.append("")
        header = ["Subset"]
        for tool_name in tools:
            header.extend([
                f"{tool_name} ChunkHit",
                f"{tool_name} ChunkRecall",
                f"{tool_name} GroupRecall",
                f"{tool_name} Answerable",
                f"{tool_name} Oracle",
            ])
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] + ["---:"] * (len(header) - 1)) + "|")
        for row in aggregate["by_subset"]:
            cells = [row["subset"]]
            for tool_name in tools:
                cells.append(_fmt(row.get(f"{tool_name}_chunk_hit")))
                cells.append(_fmt(row.get(f"{tool_name}_chunk_recall")))
                cells.append(_fmt(row.get(f"{tool_name}_group_recall")))
                cells.append(_fmt(row.get(f"{tool_name}_answerable")))
                cells.append(_fmt(row.get(f"{tool_name}_oracle_hit")))
            lines.append("| " + " | ".join(cells) + " |")

    if aggregate["graph_stage"]:
        lines.append("")
        lines.append("## Graph Stage Diagnostics")
        lines.append("")
        lines.append("| Subset | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottlenecks |")
        lines.append("|---|---:|---:|---:|---:|---|")
        for row in aggregate["graph_stage"]:
            bottlenecks = ", ".join(
                f"{name}={count}"
                for name, count in sorted(row["bottlenecks"].items())
            )
            lines.append(
                "| "
                f"{row['subset']} | "
                f"{_fmt(row['seed_hit'])} | "
                f"{_fmt(row['ppr_hit'])} | "
                f"{_fmt(row['chunk_map_hit'])} | "
                f"{_fmt(row['direct_ppr_chunk_hit'])} | "
                f"{bottlenecks or 'n/a'} |"
            )

    if aggregate["paired_group_recall_vs_vector"]:
        lines.append("")
        lines.append("## Paired GroupRecall Test vs Vector")
        lines.append("")
        lines.append("| Subset | Tool | n | Mean Delta GroupRecall | One-sided p |")
        lines.append("|---|---|---:|---:|---:|")
        for subset, comparisons in aggregate["paired_group_recall_vs_vector"].items():
            for tool_name, row in comparisons.items():
                lines.append(
                    "| "
                    f"{subset} | {tool_name} | {row['n']} | "
                    f"{_fmt(row['mean_delta_recall'])} | "
                    f"{_fmt(row['p_value_one_sided'])} |"
                )

    lines.append("")
    lines.append("## Per Query")
    for row in results:
        lines.append("")
        lines.append(f"### {row['id']}: `{row['query']}`")
        lines.append("")
        lines.append(f"- type: `{row['type']}`")
        lines.append(f"- subset: `{row['subset']}`")
        lines.append(f"- corpus_status: `{row['corpus_status']}`")
        lines.append(f"- gold_tools: `{row['gold_tools']}`")
        lines.append(f"- gold_entities: `{row['gold_entities']}`")
        lines.append(f"- missing_gold_entities: `{row['missing_gold_entities']}`")
        lines.append(f"- gold_chunks: `{row['gold_chunks']}`")
        lines.append(f"- gold_evidence_groups: `{row.get('gold_evidence_groups', {})}`")
        lines.append("")
        lines.append("| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|")
        for tool_name in tools:
            metrics = row["tools"][tool_name]
            stage = metrics.get("stage", {})
            lines.append(
                "| "
                f"{tool_name} | "
                f"{metrics['error'] or ''} | "
                f"{metrics['latency_sec']:.3f} | "
                f"{_fmt(metrics['chunk_hit_at_k'])} | "
                f"{_fmt(metrics['chance_hit_at_k'])} | "
                f"{_fmt(metrics['chunk_recall_at_k'])} | "
                f"{_fmt(metrics['group_recall_at_k'])} | "
                f"{_fmt(metrics['answerable_at_k'])} | "
                f"{_fmt(metrics['mrr_at_k'])} | "
                f"{_fmt(metrics['oracle_hit'])} | "
                f"{_fmt(stage.get('seed_hit'))} | "
                f"{_fmt(stage.get('ppr_hit'))} | "
                f"{_fmt(stage.get('chunk_map_hit'))} | "
                f"{_fmt(stage.get('direct_ppr_chunk_hit'))} | "
                f"{stage.get('bottleneck_label', 'n/a')} | "
                f"`{metrics['chunk_hits_at_k']}` | "
                f"`{metrics['group_hits_at_k']}` | "
                f"`{metrics['returned_chunk_ids']}` |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, results: list[dict]) -> None:
    payload = "\n".join(
        json.dumps(row, ensure_ascii=False, default=str)
        for row in results
    )
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Phase T retrieval quality for vector, graph, and hybrid tools."
    )
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERY_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--tools",
        nargs="+",
        choices=TOOL_CHOICES,
        default=["vector", "graph", "hybrid"],
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--oracle-k", type=int, default=10)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of queries for smoke runs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load queries and write reports without calling retrievers.",
    )
    parser.add_argument(
        "--no-llm-expansion",
        action="store_true",
        help="Disable graph query expansion for graph/hybrid diagnostic runs.",
    )
    parser.add_argument(
        "--graph-seed-mode",
        choices=SEED_MODE_CHOICES,
        default="triple",
        help="Seed strategy for graph retrieval diagnostics.",
    )
    parser.add_argument(
        "--graph-ppr-mode",
        choices=PPR_GRAPH_MODE_CHOICES,
        default="entity_only",
        help="PPR projection mode for graph/hybrid retrieval.",
    )
    parser.add_argument(
        "--graph-triple-filter",
        choices=TRIPLE_FILTER_CHOICES,
        default="none",
        help="Filter query-to-triple candidates with the LLM or keep all.",
    )
    parser.add_argument(
        "--reextract-tickers",
        default="all",
        help=(
            "Ticker scope for subset reporting. Default 'all' means every "
            "ticker in config/default.yaml; pass a comma-separated list only "
            "for historical comparisons."
        ),
    )
    parser.add_argument(
        "--ppr-seed-weight-mode",
        choices=["uniform", "similarity", "similarity_specificity"],
        default="uniform",
    )

    parser.add_argument(
        "--version-name",
        "--version_name",
        dest="version_name",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--graph-rerank-mode",
        choices=RERANK_MODE_CHOICES,
        default="legacy",
    )
    parser.add_argument(
        "--final-rerank",
        choices=FINAL_RERANK_CHOICES,
        default="none",
        help="External reranker for vector/graph retrieval; use cohere for control runs.",
    )

    parser.add_argument(
        "--candidate-pool-k",
        type=int,
        default=100,
    )
    parser.add_argument("--graph-top-k-entities", type=int, default=20)
    parser.add_argument("--graph-top-k-triples", type=int, default=10)
    parser.add_argument("--graph-damping", type=float, default=0.5)
    parser.add_argument("--metadata-risk-section-boost", type=float, default=1.35)
    parser.add_argument("--metadata-business-section-boost", type=float, default=1.18)
    parser.add_argument("--metadata-financial-section-boost", type=float, default=1.28)
    parser.add_argument("--metadata-ticker-boost", type=float, default=1.20)
    parser.add_argument("--metadata-cluster-boost-per-extra", type=float, default=0.04)
    parser.add_argument("--metadata-cluster-boost-cap", type=float, default=1.05)
    parser.add_argument("--metadata-latest-year-boost", type=float, default=1.08)
    parser.add_argument("--metadata-latest-year-min", type=int, default=2025)
    parser.add_argument("--metadata-lexical-match-weight", type=float, default=0.10)
    parser.add_argument("--metadata-lexical-boost-cap", type=float, default=0.55)
    parser.add_argument("--disable-broad-penalty", action="store_true")
    parser.add_argument("--metadata-broad-penalty-floor", type=float, default=0.92)
    parser.add_argument("--metadata-broad-penalty-step", type=float, default=0.97)
    parser.add_argument("--metadata-broad-penalty-zero-match", type=float, default=0.98)
    parser.add_argument("--metadata-broad-penalty-short-cutoff", type=int, default=80)
    parser.add_argument("--metadata-broad-penalty-mid-cutoff", type=int, default=140)
    parser.add_argument("--metadata-broad-penalty-long-cutoff", type=int, default=220)

    args = parser.parse_args()
    metadata_rerank_params = _build_metadata_rerank_params(args)
    if args.version_name is None:
        expansion_label = "expansion"
        if args.no_llm_expansion:
            expansion_label = "no_expansion"
        args.version_name = (
            f"{expansion_label}_{args.graph_rerank_mode}"
            f"_final{args.final_rerank}"
            f"_{args.graph_ppr_mode}"
            f"_filter{args.graph_triple_filter}"
            f"_pool{args.candidate_pool_k}"
            f"_lex{args.metadata_lexical_match_weight:g}"
            f"_ticker{args.metadata_ticker_boost:g}"
        )

    queries = _load_queries(args.queries)
    if args.limit is not None:
        queries = queries[: args.limit]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = args.output_dir / f"baseline_{args.version_name}_{stamp}.md"
    jsonl_path = args.output_dir / f"details_{args.version_name}_{stamp}.jsonl"

    cfg = None if args.dry_run else _get_config()
    corpus_size = 0 if args.dry_run else _get_corpus_chunk_count(cfg)
    known_tickers = {
        ticker.upper()
        for ticker in (getattr(cfg, "tickers", None) or DEFAULT_TICKER_SCOPE)
        if ticker
    }
    reextract_tickers = _resolve_ticker_scope(args.reextract_tickers, known_tickers)
    all_gold_entities = sorted({
        entity
        for item in queries
        for entity in _gold_entities(item)
    })
    existing_entities = (
        set(all_gold_entities)
        if args.dry_run
        else _get_existing_entities(cfg, all_gold_entities)
    )

    results = [
        _evaluate_query(
            item=item,
            tools=args.tools,
            top_k=args.top_k,
            oracle_k=args.oracle_k,
            cfg=cfg,
            dry_run=args.dry_run,
            use_graph_expansion=not args.no_llm_expansion,
            graph_seed_mode=args.graph_seed_mode,
            corpus_size=corpus_size,
            subset=_classify_subset(item, reextract_tickers, known_tickers),
            existing_entities=existing_entities,
            graph_rerank_mode=args.graph_rerank_mode,
            candidate_pool_k=args.candidate_pool_k,
            graph_top_k_entities=args.graph_top_k_entities,
            graph_top_k_triples=args.graph_top_k_triples,
            graph_damping=args.graph_damping,
            seed_weight_mode=args.ppr_seed_weight_mode,
            metadata_rerank_params=metadata_rerank_params,
            graph_ppr_mode=args.graph_ppr_mode,
            graph_triple_filter=args.graph_triple_filter,
            final_rerank=args.final_rerank,
        )
        for item in queries
    ]
    aggregate = _aggregate(results, args.tools)

    _write_markdown(
        path=md_path,
        query_file=args.queries,
        results=results,
        aggregate=aggregate,
        tools=args.tools,
        top_k=args.top_k,
        oracle_k=args.oracle_k,
        dry_run=args.dry_run,
        corpus_size=corpus_size,
        use_graph_expansion=not args.no_llm_expansion,
        graph_seed_mode=args.graph_seed_mode,
        graph_rerank_mode=args.graph_rerank_mode,
        candidate_pool_k=args.candidate_pool_k,
        graph_top_k_entities=args.graph_top_k_entities,
        graph_top_k_triples=args.graph_top_k_triples,
        graph_damping=args.graph_damping,
        ppr_seed_weight_mode=args.ppr_seed_weight_mode,
        graph_ppr_mode=args.graph_ppr_mode,
        graph_triple_filter=args.graph_triple_filter,
        final_rerank=args.final_rerank,
        metadata_rerank_params=metadata_rerank_params,
        run_config={
            "version_name": args.version_name,
            "final_rerank": args.final_rerank,
            "details_jsonl": str(jsonl_path),
            "reextract_tickers_arg": args.reextract_tickers,
            "resolved_ticker_scope": sorted(reextract_tickers),
            "known_tickers": sorted(known_tickers),
            "scored_queries": sum(1 for row in results if row["gold_chunks"]),
            "unscored_queries": sum(1 for row in results if not row["gold_chunks"]),
            "existing_gold_entities": len(existing_entities),
            "total_gold_entities": len(all_gold_entities),
        },
    )
    _write_jsonl(jsonl_path, results)

    print(f"Wrote report: {md_path}")
    print(f"Wrote details: {jsonl_path}")
    for tool_name in args.tools:
        row = aggregate["overall"][tool_name]
        print(
            f"{tool_name}: scored={row['scored_queries']} "
            f"errors={row['errors']} chunk_hit={row['chunk_hit_rate']:.3f} "
            f"random={row['random_hit_baseline']:.3f} "
            f"lift={_fmt(row['hit_lift_vs_random'])} "
            f"chunk_recall={row['avg_chunk_recall']:.3f} "
            f"group_recall={row['avg_group_recall']:.3f} "
            f"answerable={row['answerable_rate']:.3f} "
            f"mrr={row['avg_mrr']:.3f}"
        )


if __name__ == "__main__":
    main()
