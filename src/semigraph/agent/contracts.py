from enum import Enum
from typing import Annotated, Any, TypedDict

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from semigraph.agent.tools import DEFAULT_TOP_K


NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, strict=True),
]

class CoverageStatus(str, Enum):
    missing = "missing"
    partial = "partial"
    covered = "covered"

class AssessmentDecision(str, Enum):
    accept = "accept"
    retry = "retry"
    stop = "stop"

class FailureType(str, Enum):
    zero_results = "zero_results"
    partial_coverage = "partial_coverage"
    irrelevant_results = "irrelevant_results"
    duplicate_results = "duplicate_results"
    tool_mismatch = "tool_mismatch"

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

    @model_validator(mode="before")
    def validate_query(cls, values):
        query = values.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")
        return values


class EvidenceRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: NonEmptyText
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
    
    task_id: NonEmptyText
    query: NonEmptyText
    requirements: list[EvidenceRequirement] = Field(min_length=1)
    initial_action: RetrievalAction



class PlanRouteOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[PlannedTask] = Field(min_length=1, max_length=3)
    @model_validator(mode="after")
    def validate_unique_ids(self) -> "PlanRouteOutput":
        task_ids = set()
        requirement_ids = set()

        for task in self.tasks:
            if task.task_id in task_ids:
                raise ValueError(f"Duplicate task_id found: {task.task_id}")
            task_ids.add(task.task_id)

            for req in task.requirements:
                req_id = req.requirement_id
                if req_id in requirement_ids:
                    raise ValueError(f"Duplicate requirement_id found: {req_id}")
                requirement_ids.add(req_id)

        return self

class RequirementCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: NonEmptyText
    status: CoverageStatus
    supporting_chunk_ids: list[NonEmptyText]

    @model_validator(mode="after")
    def validate_supporting_chunks(self) -> "RequirementCoverage":
        chunk_ids = self.supporting_chunk_ids

        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("supporting_chunk_ids must not contain duplicates")

        if self.status is CoverageStatus.missing and chunk_ids:
            raise ValueError(
                "missing coverage must not have supporting_chunk_ids"
            )

        if (
            self.status in {CoverageStatus.partial, CoverageStatus.covered}
            and not chunk_ids
        ):
            raise ValueError(
                "partial or covered coverage must have supporting_chunk_ids"
            )

        return self

class RetryFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_requirement_ids: list[NonEmptyText] = Field(min_length=1)
    failure_type: FailureType
    preserved_anchors: list[NonEmptyText]
    diagnostic_summary: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    retry_strategy: RetryStrategy
    @model_validator(mode="after")
    def validate_unique_target_ids(self) -> "RetryFeedback":
        target_ids = self.target_requirement_ids

        if len(target_ids) != len(set(target_ids)):
            raise ValueError(
                "target_requirement_ids must not contain duplicates"
            )

        return self



class AssessmentStopReason(str, Enum):
    no_evidence_gain = "no_evidence_gain"
    budget_exhausted = "budget_exhausted"
    unsupported = "unsupported"
    assessment_error = "assessment_error"


class AssessmentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    reason: NonEmptyText
    requirement_coverage: list[RequirementCoverage] = Field(min_length=1)
    accepted_chunk_ids: list[NonEmptyText]
    decision: AssessmentDecision
    missing_evidence: list[NonEmptyText]
    retry_feedback: RetryFeedback | None = None
    next_action: RetrievalAction | None = None
    stop_reason: AssessmentStopReason | None = None
    @model_validator(mode="after")
    def validate_decision_contract(self) -> "AssessmentOutput":
        requirement_ids = [
            coverage.requirement_id
            for coverage in self.requirement_coverage
        ]

        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("requirement_id must not contain duplicates")

        if len(self.accepted_chunk_ids) != len(set(self.accepted_chunk_ids)):
            raise ValueError("accepted_chunk_ids must not contain duplicates")

        supporting_chunk_ids = {
            chunk_id
            for coverage in self.requirement_coverage
            for chunk_id in coverage.supporting_chunk_ids
        }

        if not set(self.accepted_chunk_ids) <= supporting_chunk_ids:
            raise ValueError(
                "accepted_chunk_ids must appear in requirement coverage"
            )

        if self.decision is AssessmentDecision.retry:
            if self.retry_feedback is None:
                raise ValueError("retry decision requires retry_feedback")
            if self.next_action is None:
                raise ValueError("retry decision requires next_action")
            if not self.missing_evidence:
                raise ValueError("retry decision requires missing_evidence")
            if self.stop_reason is not None:
                raise ValueError("retry decision must not have stop_reason")

        elif self.decision is AssessmentDecision.accept:
            if any(
                coverage.status is not CoverageStatus.covered
                for coverage in self.requirement_coverage
            ):
                raise ValueError(
                    "accept decision requires all requirements to be covered"
                )
            if self.missing_evidence:
                raise ValueError(
                    "accept decision must not have missing_evidence"
                )
            if self.retry_feedback is not None:
                raise ValueError(
                    "accept decision must not have retry_feedback"
                )
            if self.next_action is not None:
                raise ValueError("accept decision must not have next_action")
            if self.stop_reason is not None:
                raise ValueError("accept decision must not have stop_reason")

        elif self.decision is AssessmentDecision.stop:
            if self.stop_reason is None:
                raise ValueError("stop decision requires stop_reason")
            if self.next_action is not None:
                raise ValueError("stop decision must not have next_action")

        return self


class AttemptRecord(TypedDict):
    attempt_id: str                  # T1-A1
    task_id: str
    attempt_number: int              # 1..3 in Task
    action: dict                     # RetrievalAction.model_dump(mode="json")
    retrieval_status: str            # ok | tool_error
    chunks: list[dict]               # Chunk.model_dump(mode="json")
    retrieval_trace: dict            # RetrievalTrace.model_dump(mode="json")
    assessment: dict | None           # AssessmentOutput.model_dump(mode="json") or None


