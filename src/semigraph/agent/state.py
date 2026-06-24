from typing import TypedDict


class AgentState(TypedDict, total=False):
    original_query: str
    subqueries: list[str]
    current_subquery_idx: int
    completed_subqueries: list[dict]
    next_tool: dict
    chunks_history: list[dict]
    latest_chunks: list[dict]
    tool_call_log: list[dict]
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
