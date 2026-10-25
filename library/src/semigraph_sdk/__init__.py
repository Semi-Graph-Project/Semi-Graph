"""SemiGraph SDK: isolated databases, Free Ontology ingestion and Agents."""

from .database import SetupReport
from .engine import Engine
from .ingestion.models import FailureKind, IngestionReport, ItemOutcome
from .retrieval.models import (
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

__all__ = [
    "CorpusChangedError",
    "CorpusNotReadyError",
    "Engine",
    "FailureKind",
    "IngestionReport",
    "InvalidQueryError",
    "ItemOutcome",
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
    "SetupReport",
]
