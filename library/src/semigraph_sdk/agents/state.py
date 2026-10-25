# Copied from src/semigraph/agents/state.py; base SHA256: 78b18ead5a447d293a016cd393ac839bbf2882e6f64b6ac2646e2099b8a5c81f
from operator import add
from typing import Annotated, TypedDict

from semigraph_sdk.agents.contracts import AttemptRecord, RetryStrategy
from semigraph_sdk.agents.contracts import PlannedTask


class AgentState(TypedDict, total=False):
    """Serializable state shared by the root Agent graph."""

    original_query: str
    tasks: list[dict]
    worker_results: Annotated[list[dict], add]
    synthesis_input: dict
    final_answer: str
    synthesis_latency_ms: float
    synthesis_trace: dict


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
