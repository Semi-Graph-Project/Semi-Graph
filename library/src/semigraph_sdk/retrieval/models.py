"""Stable public results and typed failures for database retrieval."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RetrievalError(RuntimeError):
    """Base class for query failures that callers can handle explicitly."""


class InvalidQueryError(RetrievalError, ValueError):
    """The question, mode, or requested result budget is invalid."""


class RetrievalConfigError(RetrievalError, ValueError):
    """Configured retrieval budgets contradict one another."""


class CorpusNotReadyError(RetrievalError):
    """No finalized, searchable ingestion revision exists."""


class RetrievalBackendError(RetrievalError):
    """Neo4j, vector-index, projection, or GDS operation failed."""

    def __init__(self, stage: str, cause_type: str, message: str) -> None:
        self.stage = stage
        self.cause_type = cause_type
        super().__init__(f"Retrieval failed during {stage} ({cause_type}): {message}")


class LLMNotConfiguredError(RetrievalError):
    """An Agent or answer was requested without an LLM configuration."""


class LLMExecutionError(RetrievalError):
    """The configured LLM failed during planning, assessment, or synthesis."""


class OptionalDependencyError(RetrievalError, ImportError):
    """A selected feature needs an optional Python dependency."""


class CorpusChangedError(RetrievalError):
    """Ingestion changed readiness or revision during one query."""


class RetrievalStatus(StrEnum):
    OK = "ok"
    NO_EVIDENCE = "no_evidence"


class RetrievalMatch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    tool: Literal["vector", "graph"]
    rank: int = Field(ge=1)
    score: float
    score_kind: Literal["cosine", "ppr"]


class RetrievedChunk(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str
    text: str
    rank: int = Field(ge=1)
    matches: list[RetrievalMatch] = Field(default_factory=list)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    assertions: list[dict[str, Any]] = Field(default_factory=list)


class RetrievalResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: RetrievalStatus
    question: str
    tool: Literal["vector", "graph"]
    agent: Literal["none", "task_specific", "deepagent"]
    output: Literal["chunks", "answer"]
    chunks: list[RetrievedChunk]
    answer: str | None = None
    corpus_revision: int = Field(ge=1)
    trace: dict[str, Any] = Field(default_factory=dict)
