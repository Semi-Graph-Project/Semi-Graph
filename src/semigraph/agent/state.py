from typing import TypedDict


class AgentState(TypedDict , total=False):
    original_query: str
    subqueries: list[str]
    current_subquery_idx: int
    next_tool: dict
    chunks_history: list[dict]
    tool_call_log: list[dict]
    observation_text: str
    round: int
    sufficient: bool
    reflection_reason: str
    final_answer: str
    citation_map: list[dict]