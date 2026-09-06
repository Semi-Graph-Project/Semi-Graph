from enum import Enum
from typing import Annotated, TypedDict

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
DEFAULT_TOP_K = 5


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
    top_k_chunks: Annotated[int, Field(ge=1, le=100, strict=True)] = (
        DEFAULT_TOP_K
    )


class EvidenceRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=500,
            strict=True,
        ),
    ]


class PlannedTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: NonEmptyText
    requirement: EvidenceRequirement


class PlanRouteOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tasks: list[PlannedTask] = Field(min_length=1)


class AssessmentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted_chunk_ids: list[NonEmptyText]
    requirement_covered: bool
    decision: AssessmentDecision
    retry_query: NonEmptyText | None = None

    @model_validator(mode="after")
    def validate_decision_contract(self) -> "AssessmentOutput":
        if self.decision is AssessmentDecision.retry:
            if self.requirement_covered or self.retry_query is None:
                raise ValueError(
                    "retry requires an uncovered requirement and query"
                )
        elif self.retry_query is not None:
            raise ValueError("accept/stop must not include retry_query")

        if self.decision is AssessmentDecision.accept:
            if not self.requirement_covered or not self.accepted_chunk_ids:
                raise ValueError("accept requires covered evidence")
        elif self.requirement_covered:
            raise ValueError("covered requirement must be accepted")

        return self


class AttemptRecord(TypedDict):
    attempt_id: str
    task_id: str
    action: dict
    retrieval_status: str
    chunks: list[dict]
    retrieval_trace: dict
    assessment: dict | None
