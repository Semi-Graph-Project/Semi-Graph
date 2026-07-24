from enum import Enum
from typing import Annotated, Any, TypedDict

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from semigraph.agent.tools import DEFAULT_TOP_K


NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, strict=True),
]


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


class AgentState(TypedDict, total=False):

    tasks: list[dict[str, Any]]
    current_task_index: int
    current_action: dict[str, Any]
    plan_trace: dict[str, Any]
