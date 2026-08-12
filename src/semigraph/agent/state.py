from operator import add
from typing import Annotated, TypedDict

from semigraph.agent.contracts import AttemptRecord


class TaskResult(TypedDict):
    """Result returned by one isolated Task worker."""

    task_id: str
    attempts: list[AttemptRecord]
    completion: dict


class TaskWorkerState(TypedDict, total=False):
    """State owned by one worker while processing one Task."""

    original_query: str
    task: dict
    current_action: dict
    attempts: list[AttemptRecord]
    completion: dict
    stop_reason: str


class AgentState(TypedDict, total=False):
    """Serializable state shared by the root Agent graph."""

    original_query: str
    tasks: list[dict]
    plan_trace: dict
    task_results: Annotated[list[TaskResult], add]
    attempts: list[AttemptRecord]
    completed_tasks: list[dict]
    synthesis_trace: dict
    stop_reason: str
    final_answer: str
    citation_map: list[dict]
