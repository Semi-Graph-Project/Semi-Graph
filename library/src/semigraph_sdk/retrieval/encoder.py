"""Thread-safe, lazy query embedding that matches SDK ingestion settings."""

from __future__ import annotations

from math import isfinite
from threading import Lock

from ..config import EmbeddingConfig
from ..ingestion.embedding import Embedder, EmbeddingError, SentenceTransformerEmbedder
from .models import OptionalDependencyError, RetrievalBackendError


class QueryEncoder:
    def __init__(
        self,
        config: EmbeddingConfig,
        *,
        embedder: Embedder | None = None,
    ) -> None:
        self.config = config
        self._embedder = embedder
        self._lock = Lock()

    def encode(self, text: str) -> list[float]:
        with self._lock:
            if self._embedder is None:
                self._embedder = SentenceTransformerEmbedder(self.config)
            try:
                vectors = self._embedder.embed([text])
            except EmbeddingError as exc:
                if "Install the ingestion extra" in str(exc):
                    raise OptionalDependencyError(str(exc)) from exc
                raise RetrievalBackendError(
                    "embedding", type(exc).__name__, str(exc)
                ) from exc
            except Exception as exc:
                raise RetrievalBackendError(
                    "embedding", type(exc).__name__, str(exc)
                ) from exc

        if len(vectors) != 1:
            raise RetrievalBackendError(
                "embedding", "InvalidEmbedding", "the embedder returned the wrong number of vectors"
            )
        vector = [float(value) for value in vectors[0]]
        if len(vector) != self.config.dimension:
            raise RetrievalBackendError(
                "embedding", "InvalidEmbedding",
                f"expected {self.config.dimension} dimensions, got {len(vector)}",
            )
        if not all(isfinite(value) for value in vector):
            raise RetrievalBackendError(
                "embedding", "InvalidEmbedding", "the query vector contains a non-finite value"
            )
        if not vector or sum(value * value for value in vector) == 0:
            raise RetrievalBackendError(
                "embedding", "InvalidEmbedding", "the query vector has zero magnitude"
            )
        return vector
