from operator import add
from typing import Annotated, TypedDict

from semigraph.agents.contracts import AttemptRecord, RetryStrategy
from semigraph.agents.contracts import PlannedTask


class AgentState(TypedDict, total=False):
    """Serializable state shared by the root Agent graph."""

    original_query: str
    tasks: list[dict]
    worker_results: Annotated[list[dict], add]
    synthesis_input: dict
    final_answer: str
    synthesis_latency_ms: float


class TaskWorkerState(TypedDict, total=False):
    """State owned by one worker while processing one Task."""

    original_query: str
    task_index: int
    task: PlannedTask
    current_query: str
    current_strategy: RetryStrategy | None
    chunks: list[dict]
    accepted_chunks: list[dict]
    attempts: list[AttemptRecord]
    assessment: dict
    stop_reason: str
