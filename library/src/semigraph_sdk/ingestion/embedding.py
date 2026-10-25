"""Injectable embedding contract and Sentence Transformers adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ..config import EmbeddingConfig


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> Sequence[Sequence[float]]: ...


class EmbeddingError(RuntimeError):
    """An embedding call returned an unusable result."""


class EmbeddingInputTooLong(EmbeddingError):
    """One input would be silently truncated by the configured model."""


class SentenceTransformerEmbedder:
    """Load the configured model lazily and reject silently truncated input."""

    def __init__(self, config: EmbeddingConfig, *, batch_size: int = 64) -> None:
        self.config = config
        self.batch_size = batch_size
        self._model = None
        self._load_error: EmbeddingError | None = None

    def _get_model(self):
        if self._model is not None:
            return self._model
        if self._load_error is not None:
            raise self._load_error
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.config.model,
                revision=self.config.revision,
                device=self.config.device,
            )
        except Exception as exc:
            if isinstance(exc, ImportError):
                error = EmbeddingError(
                    "Install the ingestion extra to use local embeddings: "
                    "python -m pip install -e '.[ingestion]'"
                )
            else:
                error = EmbeddingError(
                    f"Cannot load embedding model {self.config.model!r}: "
                    f"{exc.__class__.__name__}: {exc}"
                )
            self._load_error = error
            raise error from exc
        return self._model

    def validate_text(self, text: str) -> None:
        model = self._get_model()
        tokenizer = getattr(model, "tokenizer", None)
        maximum = getattr(model, "max_seq_length", None)
        if tokenizer is None or not isinstance(maximum, int):
            return
        encoded = tokenizer(text, add_special_tokens=True, truncation=False)
        token_ids = encoded.get("input_ids", [])
        if token_ids and isinstance(token_ids[0], list):
            token_ids = token_ids[0]
        if len(token_ids) > maximum:
            raise EmbeddingInputTooLong(
                f"Input has {len(token_ids)} tokens; model limit is {maximum}. "
                "Split the text into smaller chunks and ingest again."
            )

    def embed(self, texts: list[str]) -> Sequence[Sequence[float]]:
        if not texts:
            return []
        for text in texts:
            self.validate_text(text)
        try:
            vectors = self._get_model().encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=self.config.normalize,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            return [vector.tolist() for vector in vectors]
        except EmbeddingError:
            raise
        except Exception as exc:
            raise EmbeddingError(
                f"Embedding call failed: {exc.__class__.__name__}: {exc}"
            ) from exc
