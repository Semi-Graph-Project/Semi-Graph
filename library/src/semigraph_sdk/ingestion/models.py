"""Typed extraction, validation and public ingestion results."""

from __future__ import annotations

from enum import StrEnum
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


RELATIONSHIP_TYPE_PATTERN = r"^[A-Z][A-Z0-9_]{1,63}$"


class FailureKind(StrEnum):
    INVALID_INPUT = "INVALID_INPUT"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    STORAGE_FAILED = "STORAGE_FAILED"
    FINALIZATION_FAILED = "FINALIZATION_FAILED"


class IngestionStage(StrEnum):
    INPUT = "input"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    CHECKPOINT = "checkpoint"
    EMBEDDING = "embedding"
    STORAGE = "storage"
    FINALIZATION = "finalization"
    COMPLETE = "complete"


class ItemStatus(StrEnum):
    COMPLETE = "complete"
    SKIPPED = "skipped"
    FAILED = "failed"


class BatchStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class ExtractedEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=512)
    type: str = Field(min_length=1, max_length=128)
    evidence_quote: str = Field(min_length=1, max_length=4096)
    start: int | None = None
    end: int | None = None

    @field_validator("start", "end", mode="before")
    @classmethod
    def ignore_invalid_hint(cls, value):
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
        return None


class ExtractedAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    head_id: str = Field(min_length=1, max_length=128)
    relation: str = Field(min_length=1, max_length=256)
    relation_description: str | None = Field(default=None, max_length=1000)
    tail_id: str = Field(min_length=1, max_length=128)
    evidence_quote: str = Field(min_length=1, max_length=4096)
    start: int | None = None
    end: int | None = None

    @field_validator("start", "end", mode="before")
    @classmethod
    def ignore_invalid_hint(cls, value):
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
        return None


class ExtractionDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entities: list[ExtractedEntity] = Field(default_factory=list, max_length=500)
    assertions: list[ExtractedAssertion] = Field(default_factory=list, max_length=1000)


class ResolvedEntity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_id: str
    name: str
    type: str
    entity_key: str
    evidence_quote: str
    start: int
    end: int


class ResolvedAssertion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    assertion_id: str
    head_key: str
    relation_type: str
    relation_description: str | None = None
    tail_key: str
    evidence_quote: str
    start: int
    end: int
    triple_text: str

    @field_validator("relation_type")
    @classmethod
    def require_safe_relationship_type(cls, value: str) -> str:
        if not re.fullmatch(RELATIONSHIP_TYPE_PATTERN, value):
            raise ValueError("relationship_type must be a safe UPPER_SNAKE_CASE name")
        return value


class ValidatedExtraction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    entities: list[ResolvedEntity]
    assertions: list[ResolvedAssertion]
    warnings: list[str] = Field(default_factory=list)


class ItemOutcome(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    input_index: int = Field(ge=0)
    chunk_id: str | None = None
    status: ItemStatus
    last_completed_stage: IngestionStage
    warnings: list[str] = Field(default_factory=list)
    failure_kind: FailureKind | None = None
    error: str | None = None
    duplicate_of_index: int | None = None


class IngestionReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: BatchStatus
    input_count: int = Field(ge=0)
    inserted_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    search_ready: bool
    corpus_revision: int = Field(ge=0)
    outcomes: list[ItemOutcome]

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
