"""Load and share the Triple index once per Neo4j backend and process."""

from __future__ import annotations

from threading import Lock

import numpy as np

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver


_CYPHER_LOAD_TRIPLES = """
MATCH (s:Entity)-[r]->(t:Entity)
WHERE r.triple_embedding IS NOT NULL
RETURN s.name AS head,
       s.type AS head_type,
       s.specificity AS head_spec,
       type(r) AS rel_type,
       t.name AS tail,
       t.type AS tail_type,
       t.specificity AS tail_spec,
       r.triple_embedding AS embedding
"""


_TRIPLE_INDEX_CACHE: dict[
    tuple[str, str, int], tuple[np.ndarray, list[dict]]
] = {}
_load_lock = Lock()


def _read_triple_index(cfg: Config) -> tuple[np.ndarray, list[dict]]:
    """Read vectors and aligned metadata from Neo4j without managing cache."""
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            rows = list(session.run(_CYPHER_LOAD_TRIPLES))
        if not rows:
            print("[triple_index] EMPTY — run `python scripts/embed_triples.py` first")
            return np.empty((0, cfg.embed_dim), dtype=np.float32), []

        vectors = np.asarray(
            [row["embedding"] for row in rows], dtype=np.float32
        )
        metadata = [
            {
                "head": row["head"],
                "head_type": row["head_type"],
                "head_spec": row["head_spec"] if row["head_spec"] is not None else 1.0,
                "rel_type": row["rel_type"],
                "tail": row["tail"],
                "tail_type": row["tail_type"],
                "tail_spec": row["tail_spec"] if row["tail_spec"] is not None else 1.0,
            }
            for row in rows
        ]
        mb = vectors.nbytes / (1024 * 1024)
        print(f"[triple_index] loaded {len(rows)} triples ({mb:.1f} MB)")
        return vectors, metadata
    finally:
        driver.close()


def load_triple_index(cfg: Config | None = None) -> tuple[np.ndarray, list[dict]]:
    """Reuse cached vectors and metadata; serialize only cold-cache loading.

    Callers should treat the returned arrays and metadata as read-only.
    """
    cfg = cfg or get_config()
    cache_key = (cfg.neo4j_uri, cfg.neo4j_user, cfg.embed_dim)
    cached = _TRIPLE_INDEX_CACHE.get(cache_key)
    if cached is not None:
        return cached

    with _load_lock:
        # Another thread may have populated this backend while we waited.
        cached = _TRIPLE_INDEX_CACHE.get(cache_key)
        if cached is None:
            cached = _read_triple_index(cfg)
            _TRIPLE_INDEX_CACHE[cache_key] = cached
        return cached


def clear_triple_index_cache() -> None:
    """Invalidate all backend entries after Triple data changes."""
    with _load_lock:
        _TRIPLE_INDEX_CACHE.clear()
