# Copied from src/semigraph/agents/contracts.py; base SHA256: 968bb26436fa86b9b356d0950cf349a5bda0cd9c9c892c2df72946c8f9ff230c
from enum import Enum
from typing import Annotated, Literal, TypedDict

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, strict=True),
]


class ToolName(str, Enum):
    vector = "vector"
    graph = "graph"


class PlannedTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: NonEmptyText
    requirement: NonEmptyText


class PlanRouteOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tasks: list[PlannedTask] = Field(min_length=1)


RetryStrategy = Literal["anchor_enrichment", "focus_missing", "relation_enrichment"]


class AssessmentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted_chunk_ids: list[NonEmptyText]
    is_covered: bool
    retry_query: NonEmptyText | None = None
    retry_strategy: RetryStrategy | None = None

    @model_validator(mode="after")
    def validate_retry(self) -> "AssessmentOutput":
        if self.is_covered:
            if self.retry_query is not None or self.retry_strategy is not None:
                raise ValueError("Covered requirements must not propose a retry")
            if not self.accepted_chunk_ids:
                raise ValueError("Covered requirements need accepted chunks")
        elif self.retry_query is None or self.retry_strategy is None:
            raise ValueError("Uncovered requirements need retry_query and retry_strategy")
        return self


class AttemptRecord(TypedDict):
    query: str
    strategy: RetryStrategy | None
    chunks: list[dict]
    assessment: dict
