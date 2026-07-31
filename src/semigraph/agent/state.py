from typing import TypedDict

from semigraph.agent.contracts import AttemptRecord


class AgentState(TypedDict, total=False):
    """Serializable state shared by Agent nodes."""

    # Four-node harness state
    original_query: str
    tasks: list[dict]
    current_task_index: int
    current_action: dict
    plan_trace: dict
    attempts: list[AttemptRecord]
    completed_tasks: list[dict]
    synthesis_trace: dict

    # Legacy flow; removed when the production graph cuts over.
    subqueries: list[str]
    current_subquery_idx: int
    completed_subqueries: list[dict]
    next_tool: dict
    chunks_history: list[dict]
    latest_chunks: list[dict]
    tool_call_log: list[dict]
    retrieval_trace_history: list[dict]
    observation_text: str
    observation_history: list[dict]
    round: int
    sufficient: bool
    reflection_reason: str
    reflection_history: list[dict]
    reflection_feedback: str
    retry_query: str
    stop_reason: str
    final_answer: str
    citation_map: list[dict]
