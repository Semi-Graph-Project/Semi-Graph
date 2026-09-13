from enum import Enum
from typing import Annotated, Literal, TypedDict

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)
from semigraph.config import get_config


NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, strict=True),
]


def _default_top_k_chunks() -> int:
    return get_config().agent_top_k_chunks


class AssessmentDecision(str, Enum):
    accept = "accept"
    retry = "retry"
    stop = "stop"


class ToolName(str, Enum):
    vector = "vector"
    graph = "graph"
    financial = "financial"
    news = "news"



class RetrievalAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: ToolName
    query: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=1000,
            strict=True,
        ),
    ]
    top_k_chunks: Annotated[int, Field(ge=1, le=100, strict=True)] = Field(
        default_factory=_default_top_k_chunks
    )


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
