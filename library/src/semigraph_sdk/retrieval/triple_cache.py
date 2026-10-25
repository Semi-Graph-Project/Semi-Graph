"""One-revision read-only cache for arbitrary Free Ontology assertion vectors."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any

import numpy as np


_LOAD_TRIPLES = """
MATCH (head:Entity)-[assertion]->(tail:Entity)
WHERE assertion.source_chunk_id IS NOT NULL
  AND assertion.triple_embedding IS NOT NULL
RETURN assertion.assertion_id AS assertion_id,
       assertion.triple_text AS triple_text,
       type(assertion) AS relation,
       head.name AS head,
       head.type AS head_type,
       tail.name AS tail,
       tail.type AS tail_type,
       assertion.triple_embedding AS embedding
ORDER BY assertion.assertion_id
"""


@dataclass(frozen=True)
class TripleVectorEntry:
    rows: tuple[dict[str, Any], ...]
    matrix: np.ndarray
    norms: np.ndarray


class TripleVectorCache:
    """Serialize cold loads and evict the prior revision when corpus changes."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._key: tuple[str, str, int, str] | None = None
        self._entry: TripleVectorEntry | None = None

    def select(
        self,
        session,
        *,
        workspace_id: str,
        database_name: str,
        corpus_revision: int,
        embedding_fingerprint: str,
        query_vector: list[float],
        top_k: int,
        min_score: float | None,
    ) -> tuple[list[dict[str, Any]], bool]:
        key = (
            workspace_id,
            database_name,
            corpus_revision,
            embedding_fingerprint,
        )
        with self._lock:
            cache_hit = key == self._key and self._entry is not None
            if not cache_hit:
                self._entry = self._load(session)
                self._key = key
            assert self._entry is not None
            entry = self._entry
            if not entry.rows:
                return [], cache_hit
            if entry.matrix.shape[1] != len(query_vector):
                raise ValueError(
                    "Stored triple embedding dimensions differ from the query vector"
                )

            query = np.asarray(query_vector, dtype=np.float32)
            denominator = entry.norms * float(np.linalg.norm(query))
            scores = (entry.matrix @ query) / np.maximum(denominator, 1e-12)
            eligible = [
                (index, float(score))
                for index, score in enumerate(scores)
                if min_score is None or float(score) >= min_score
            ]
            eligible.sort(key=lambda item: (-item[1], entry.rows[item[0]]["assertion_id"]))
            return [
                {**entry.rows[index], "score": score, "rank": rank}
                for rank, (index, score) in enumerate(eligible[:top_k], start=1)
            ], cache_hit

    @staticmethod
    def _load(session) -> TripleVectorEntry:
        rows = tuple(dict(row) for row in session.run(_LOAD_TRIPLES))
        if not rows:
            matrix = np.empty((0, 0), dtype=np.float32)
            norms = np.empty((0,), dtype=np.float32)
        else:
            matrix = np.asarray([row["embedding"] for row in rows], dtype=np.float32)
            if matrix.ndim != 2 or not np.isfinite(matrix).all():
                raise ValueError("Stored triple embeddings are malformed or non-finite")
            norms = np.linalg.norm(matrix, axis=1)
            if np.any(norms == 0):
                raise ValueError("Stored triple embeddings contain a zero vector")
        matrix.setflags(write=False)
        norms.setflags(write=False)
        return TripleVectorEntry(rows=rows, matrix=matrix, norms=norms)

    @property
    def cached_revision(self) -> int | None:
        with self._lock:
            return None if self._key is None else self._key[2]
