from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DEFAULT_QUERIES = {
    "T001": "How exposed is AMD to TSMC supply risk?",
    "T003": "Who produces the dense memory chips that power modern AI training accelerators?",
    "T004": "What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?",
    "T016": "qwerty zzz random semiconductor nonsense",
}

DEFAULT_QUERY_EXPAND_CACHE = (
    ROOT / "analytics" / "trace_cache" / "query_expand_cache.json"
)
TRACE_CACHE_VERSION = 1


def _cache_namespace(cfg) -> str:
    provider = getattr(cfg, "llm_provider", "unknown")
    model = getattr(cfg, "llm_model", "unknown")
    return f"{provider}:{model}"


def _load_expand_cache(path: Path) -> dict:
    if not path.exists():
        return {"version": TRACE_CACHE_VERSION, "namespaces": {}}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[trace-cache] WARN: failed to read {path.name}: {exc}")
        return {"version": TRACE_CACHE_VERSION, "namespaces": {}}

    if not isinstance(payload, dict):
        return {"version": TRACE_CACHE_VERSION, "namespaces": {}}

    namespaces = payload.get("namespaces", {})
    if not isinstance(namespaces, dict):
        namespaces = {}

    return {
        "version": int(payload.get("version", TRACE_CACHE_VERSION) or TRACE_CACHE_VERSION),
        "namespaces": namespaces,
    }


def _save_expand_cache(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _expand_query_cached(
    query: str,
    cfg,
    cache_path: Path,
    use_cache: bool,
    refresh_cache: bool,
) -> str:
    from semigraph.online.query_expand import expand_query

    if not query.strip():
        return query

    namespace = _cache_namespace(cfg)
    payload = _load_expand_cache(cache_path) if use_cache else {
        "version": TRACE_CACHE_VERSION,
        "namespaces": {},
    }
    namespaces = payload.setdefault("namespaces", {})
    ns_cache = namespaces.setdefault(namespace, {})

    if use_cache and not refresh_cache:
        cached = ns_cache.get(query)
        if isinstance(cached, dict):
            expanded = str(cached.get("expanded_query", "")).strip()
            if expanded:
                print(f"[trace-cache] hit namespace={namespace!r}")
                return expanded

    expanded = expand_query(query, cfg=cfg)
    if use_cache:
        ns_cache[query] = {
            "expanded_query": expanded,
            "cached_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        _save_expand_cache(cache_path, payload)
        print(f"[trace-cache] stored namespace={namespace!r} query={query!r}")
    return expanded


def trace_query(
    label: str,
    query: str,
    top_k_triples: int,
    top_k_entities: int,
    cfg,
    cache_path: Path,
    use_query_expand_cache: bool,
    refresh_query_expand_cache: bool,
) -> None:
    from semigraph.online.graph_search import (
        _cluster_aliases,
        _collapse_clusters,
        _map_chunks,
    )
    from semigraph.online.ppr import run_ppr
    from semigraph.online.seed import query_to_triple_seeds

    print("\n" + "=" * 90)
    print(f"{label}: {query}")

    expanded_query = _expand_query_cached(
        query=query,
        cfg=cfg,
        cache_path=cache_path,
        use_cache=use_query_expand_cache,
        refresh_cache=refresh_query_expand_cache,
    )
    if expanded_query != query:
        print(f"\nEXPANDED QUERY\n  {expanded_query}")

    seeds = query_to_triple_seeds(expanded_query, top_k_triples=top_k_triples, cfg=cfg)
    print(f"\nSEEDS ({len(seeds)})")
    for seed in seeds[:12]:
        print(
            f"  sim={seed['similarity']:.3f} "
            f"spec={seed['specificity']:.3f} "
            f"{seed['name']} ({seed['type']})"
        )

    ppr_entities = run_ppr(seeds, top_k=top_k_entities, damping=0.7)
    print(f"\nPPR TOP ENTITIES ({len(ppr_entities)})")
    for entity in ppr_entities[:12]:
        print(f"  ppr={entity['score']:.4f} {entity['name']} ({entity['type']})")

    cluster_map = _cluster_aliases([e["name"] for e in ppr_entities])
    cluster_entries = _collapse_clusters(ppr_entities, cluster_map)
    chunks = _map_chunks(cluster_entries, top_k=10)
    print(f"\nCHUNKS ({len(chunks)})")
    for chunk in chunks:
        print(
            f"  score={chunk['score']:.4f} "
            f"{chunk['chunk_id']} "
            f"[{chunk['ticker']} FY{chunk['fiscal_year']} {chunk['section']}]"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trace graph retrieval stages for Phase T bottleneck analysis."
    )
    parser.add_argument("query", nargs="*", help="Optional custom query.")
    parser.add_argument("--top-k-triples", type=int, default=8)
    parser.add_argument("--top-k-entities", type=int, default=20)
    parser.add_argument(
        "--query-expand-cache",
        type=Path,
        default=DEFAULT_QUERY_EXPAND_CACHE,
        help="JSON cache for LLM query expansion results.",
    )
    parser.add_argument(
        "--refresh-query-expand-cache",
        action="store_true",
        help="Bypass cached expansions and refresh them from the LLM.",
    )
    parser.add_argument(
        "--no-query-expand-cache",
        action="store_true",
        help="Disable cache reads/writes for query expansion.",
    )
    args = parser.parse_args()

    from semigraph.config import get_config

    cfg = get_config()
    use_query_expand_cache = not args.no_query_expand_cache

    if args.query:
        trace_query(
            "CUSTOM",
            " ".join(args.query),
            args.top_k_triples,
            args.top_k_entities,
            cfg,
            args.query_expand_cache,
            use_query_expand_cache,
            args.refresh_query_expand_cache,
        )
        return

    for label, query in DEFAULT_QUERIES.items():
        trace_query(
            label,
            query,
            args.top_k_triples,
            args.top_k_entities,
            cfg,
            args.query_expand_cache,
            use_query_expand_cache,
            args.refresh_query_expand_cache,
        )


if __name__ == "__main__":
    main()
