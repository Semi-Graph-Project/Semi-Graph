
from __future__ import annotations

from threading import Lock
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from semigraph.config import Config, get_config


class EmbeddingModel:
    """Lazy-loaded sentence-transformer wrapper.
    """

    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or get_config()
        self._model: Optional[SentenceTransformer] = None
        self._load_lock = Lock()

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            with self._load_lock:
                if self._model is None:
                    print(
                        f"[embeddings] loading {self.cfg.embed_model} "
                        f"on {self.cfg.embed_device}..."
                    )
                    self._model = SentenceTransformer(
                        self.cfg.embed_model,
                        device=self.cfg.embed_device,
                    )
                    print(
                        "[embeddings] ready "
                        f"(dim={self._model.get_sentence_embedding_dimension()})"
                    )
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


_embedding_model: Optional[EmbeddingModel] = None
_embedding_model_lock = Lock()


def get_embedding_model() -> EmbeddingModel:
    """Return the process-wide embedding model without concurrent creation."""
    global _embedding_model
    if _embedding_model is None:
        with _embedding_model_lock:
            if _embedding_model is None:
                _embedding_model = EmbeddingModel()
    return _embedding_model
