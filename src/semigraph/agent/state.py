from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed between agent nodes.

    All keys are optional because each node only populates the fields it owns.
    The examples below show the shape that each value usually takes.

    Example:
        {
            "original_query": "How exposed is AMD to TSMC supply risk?",
            "subqueries": [
                "What is the supplier relationship between AMD and TSMC?",
                "What does AMD say about supply chain concentration risk?"
            ],
            "current_subquery_idx": 0,
            "completed_subqueries": [
                {
                    "subquery_idx": 0,
                    "subquery": "What is the supplier relationship between AMD and TSMC?",
                    "stop_reason": "sufficient",
                    "reflection_reason": "Evidence directly answers the subquery.",
                    "round": 1
                }
            ],
            "next_tool": {
                "name": "graph",
                "args": {"query": "AMD TSMC supplier relationship", "top_k_chunks": 5}
            },
            "chunks_history": [
                {
                    "chunk_id": "AMD_2025_Item_1A_0008",
                    "ticker": "AMD",
                    "fiscal_year": 2025,
                    "section": "Risk_Factors",
                    "text": "AMD relies on third-party foundries...",
                    "score": 0.91
                }
            ],
            "latest_chunks": [...],
            "tool_call_log": [
                {
                    "round": 1,
                    "subquery": "What is the supplier relationship between AMD and TSMC?",
                    "tool": "graph",
                    "query": "AMD TSMC supplier relationship",
                    "top_k_chunks": 5,
                    "n_chunks": 3,
                    "status": "ok"
                }
            ],
            "retrieval_trace_history": [
                {
                    "round": 1,
                    "subquery": "What is the supplier relationship between AMD and TSMC?",
                    "tool": "graph",
                    "query": "AMD TSMC supplier relationship",
                    "status": "ok",
                    "profile": "phase_t",
                    "parameters": {
                        "ppr_graph_mode": "entity_chunk",
                        "triple_filter": "llm",
                        "final_rerank": "cohere"
                    },
                    "seed_count": 5,
                    "candidate_count": 100,
                    "returned_chunk_ids": ["AMD_2025_Item_1A_0008"]
                }
            ],
            "observation_text": "The retrieved chunks mention AMD's reliance on external foundries.",
            "observation_history": [
                {
                    "round": 1,
                    "subquery": "What is the supplier relationship between AMD and TSMC?",
                    "tool": "graph",
                    "n_chunks": 3,
                    "observation_text": "The retrieved chunks mention AMD's reliance on external foundries."
                }
            ],
            "round": 1,
            "sufficient": False,
            "reflection_reason": "Need a more direct supplier relationship chunk.",
            "reflection_history": [
                {
                    "round": 1,
                    "subquery": "What is the supplier relationship between AMD and TSMC?",
                    "sufficient": False,
                    "reason": "Current chunks are relevant but incomplete.",
                    "feedback": "Use graph evidence focused on supplier dependency.",
                    "retry_query": "AMD TSMC supplier dependency",
                    "stop_reason": "needs_more_evidence"
                }
            ],
            "reflection_feedback": "Use graph evidence focused on supplier dependency.",
            "retry_query": "AMD TSMC supplier dependency",
            "stop_reason": "needs_more_evidence",
            "final_answer": "AMD relies on third-party foundries for manufacturing.",
            "citation_map": [
                {
                    "citation_index": 1,
                    "chunk_id": "AMD_2025_Item_1A_0008",
                    "ticker": "AMD",
                    "fiscal_year": 2025,
                    "section": "Risk_Factors",
                    "text": "AMD relies on third-party foundries..."
                }
            ]
        }
    """

    original_query: str
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
