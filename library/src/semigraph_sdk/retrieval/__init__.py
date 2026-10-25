"""SDK-owned retrieval helpers."""

from .models import (
    CorpusChangedError,
    CorpusNotReadyError,
    InvalidQueryError,
    LLMExecutionError,
    LLMNotConfiguredError,
    OptionalDependencyError,
    RetrievalBackendError,
    RetrievalConfigError,
    RetrievalError,
    RetrievalMatch,
    RetrievalResult,
    RetrievalStatus,
    RetrievedChunk,
)
from .projection import ensure_projection, projection_name

__all__ = [
    "CorpusChangedError",
    "CorpusNotReadyError",
    "InvalidQueryError",
    "LLMExecutionError",
    "LLMNotConfiguredError",
    "OptionalDependencyError",
    "RetrievalBackendError",
    "RetrievalConfigError",
    "RetrievalError",
    "RetrievalMatch",
    "RetrievalResult",
    "RetrievalStatus",
    "RetrievedChunk",
    "ensure_projection",
    "projection_name",
]
