"""
Embedding model wrapper for Phase B.

A thin layer around sentence-transformers so the rest of the codebase doesn't
need to know which library/model is in use. Default model `BAAI/bge-base-en-v1.5`
(768 dim, ~1.5 GB RAM, MTEB 63.5) — sweet spot for an 8 GB CPU machine.

`EmbeddingModel` is a singleton — first call loads weights (~30 s on CPU,
downloads ~440 MB on first run), subsequent calls reuse the same instance.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from semigraph.config import Config, get_config


class EmbeddingModel:
    """Lazy-loaded sentence-transformer wrapper.

    BGE models are trained with cosine similarity → we L2-normalize at encode
    time so that downstream cosine == dot product, and Neo4j vector index can
    be configured for cosine without any extra step.
    """

    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or get_config()
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            print(f"[embeddings] loading {self.cfg.embed_model} on {self.cfg.embed_device}...")
            self._model = SentenceTransformer(
                self.cfg.embed_model,
                device=self.cfg.embed_device,
            )
            print(f"[embeddings] ready (dim={self._model.get_sentence_embedding_dimension()})")
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a batch. Returns float32 array shaped (len(texts), dim)."""
        if not texts:
            return np.zeros((0, self.cfg.embed_dim), dtype=np.float32)
        vecs = self.model.encode(
            texts,
            batch_size=self.cfg.embed_batch_size,
            show_progress_bar=False,
            normalize_embeddings=self.cfg.embed_normalize,
            convert_to_numpy=True,
        )
        return vecs.astype(np.float32)


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    """Cached singleton — call from any module that needs to embed."""
    return EmbeddingModel()
