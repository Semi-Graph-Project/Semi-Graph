from enum import Enum
from typing import Annotated, TypedDict

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, strict=True),
]
DEFAULT_TOP_K = 5
MAX_PLANNED_TASKS = 10


class AssessmentDecision(str, Enum):
    accept = "accept"
    retry = "retry"
    stop = "stop"


class RetryStrategy(str, Enum):
    anchor_enrichment = "anchor_enrichment"
    focus_missing = "focus_missing"
    bridge_hint = "bridge_hint"
    constraint_repair = "constraint_repair"
    news_query_refinement = "news_query_refinement"
    switch_tool = "switch_tool"


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
    requirements: list[EvidenceRequirement] = Field(min_length=1)
    initial_action: RetrievalAction


class PlanRouteOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[PlannedTask] = Field(min_length=1)

    @model_validator(mode="after")
    def limit_task_count(self) -> "PlanRouteOutput":
        self.tasks = self.tasks[:MAX_PLANNED_TASKS]
        return self


class AssessmentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted_chunk_ids: list[NonEmptyText]
    covered_requirement_ids: list[NonEmptyText]
    decision: AssessmentDecision
    retry_strategy: RetryStrategy | None = None
    next_action: RetrievalAction | None = None

    @model_validator(mode="after")
    def validate_decision_contract(self) -> "AssessmentOutput":
        if self.decision is AssessmentDecision.retry:
            if self.retry_strategy is None:
                raise ValueError("retry decision requires retry_strategy")
            if self.next_action is None:
                raise ValueError("retry decision requires next_action")
        elif (
            self.decision is AssessmentDecision.accept
            and not self.accepted_chunk_ids
        ):
            raise ValueError("accept decision requires accepted evidence")
        elif self.retry_strategy is not None or self.next_action is not None:
            raise ValueError(
                "accept/stop decisions must not include retry fields"
            )

        return self


class AttemptRecord(TypedDict):
    attempt_id: str
    task_id: str
    action: dict
    retrieval_status: str
    chunks: list[dict]
    retrieval_trace: dict
    assessment: dict | None
