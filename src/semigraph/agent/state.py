from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed between agent nodes.

    All keys are optional because each node only populates the fields it owns.
    The examples below show the shape that each value usually takes.
    
    planRouteShape = {
        "original_query": "What is the impact of climate change on polar bear populations?",
        "tasks": [
            {
                "task_id": "T1",
                "query": "What is the impact of climate change on polar bear populations?",
                "requirements": [
                    {
                        "requirement_id": "R1",
                        "description": "Provide scientific studies and data on polar bear populations and climate change."
                    }
                ]
            }
        ]
    }
    """

    original_query: str
    tasks: list[dict]
    current_task_index: int
    current_action: dict
    plan_trace: dict

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
