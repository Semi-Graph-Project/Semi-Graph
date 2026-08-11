"""Evaluation-only Vector and Graph Agents."""

from __future__ import annotations

import time
from pathlib import Path
import sys

from langgraph.graph import END, START, StateGraph

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.agent import nodes as agent_nodes  # noqa: E402
from semigraph.agent.graph import (  # noqa: E402
    _apply_action_policy,
    _collect_task_results,
    _send_tasks,
    _route_after_assess,
    _route_after_execute,
)
from semigraph.agent.ledger import select_synthesis_chunks  # noqa: E402
from semigraph.agent.state import AgentState, TaskWorkerState  # noqa: E402
from semigraph.config import get_config  # noqa: E402
from semigraph.connections import get_llm  # noqa: E402


NEO4J_URI = "bolt://localhost:7690"
VECTOR_INDEX = "gold_chunk_embedding"
DEFAULT_TOP_K = 5
EVAL_TOOLS = {"vector", "graph"}


def format_evidence(chunks: list[dict]) -> str:
    """Format Chunk IDs and text for the evaluation answer prompt."""
    return "\n\n".join(
        f"[{rank}] chunk_id={chunk['chunk_id']}\n{chunk.get('text', '')}"
        for rank, chunk in enumerate(chunks, start=1)
    )


def generate_final_answer(llm, question: str, chunks: list[dict]) -> str:
    """Generate a grounded answer from the retrieved Chunks only."""
    response = llm.invoke([
        {
            "role": "system",
            "content": (
                "Answer the user's question using only the supplied evidence "
                "chunks. Do not use outside knowledge or invent facts. "
                "Return plain text only, without Markdown, and use no more "
                "than 900 characters. If none of the chunks contains relevant "
                "information to answer the question, reply exactly: Do not answers"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{question}\n\n"
                f"Evidence Chunks:\n{format_evidence(chunks)}"
            ),
        },
    ])
    content = response.content if hasattr(response, "content") else response
    return str(content).strip()


def eval_synthesize_node(
    state: AgentState,
    generate_answer: bool = True,
) -> dict:
    """Create the evaluation answer from Assess-selected evidence only."""
    started_at = time.perf_counter()
    cfg = get_config()
    max_chunks = cfg.agent_max_synthesis_chunks
    attempts = state.get("attempts") or []
    chunks = select_synthesis_chunks(attempts, max_total=max_chunks)
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]

    if not chunks:
        return {
            "final_answer": "Do not answers",
            "citation_map": [],
            "synthesis_trace": {
                "status": "no_evidence",
                "selected_chunk_ids": [],
                "max_chunks": max_chunks,
                "llm_calls": 0,
                "latency_sec": round(time.perf_counter() - started_at, 3),
                "error_type": None,
            },
        }

    if not generate_answer:
        return {
            "final_answer": "",
            "citation_map": [],
            "synthesis_trace": {
                "status": "retrieve_only",
                "selected_chunk_ids": chunk_ids,
                "max_chunks": max_chunks,
                "llm_calls": 0,
                "latency_sec": round(time.perf_counter() - started_at, 3),
                "error_type": None,
            },
        }

    try:
        answer = generate_final_answer(
            get_llm(cfg),
            str(state.get("original_query") or ""),
            chunks,
        )
        status = "ok"
        error_type = None
    except Exception as exc:
        answer = ""
        status = "provider_error"
        error_type = type(exc).__name__

    return {
        "final_answer": answer,
        "citation_map": [],
        "synthesis_trace": {
            "status": status,
            "selected_chunk_ids": chunk_ids,
            "max_chunks": max_chunks,
            "llm_calls": 1,
            "latency_sec": round(time.perf_counter() - started_at, 3),
            "error_type": error_type,
        },
    }


def _build_eval_graph(
    locked_tool: str,
    top_k: int,
    generate_answer: bool,
):
    """Build the shared Production-shaped evaluation Agent graph."""
    if locked_tool not in EVAL_TOOLS:
        raise ValueError(f"Unsupported evaluation tool: {locked_tool}")
    if top_k < 1:
        raise ValueError("top_k must be positive")

    cfg = get_config()
    cfg.neo4j_uri = NEO4J_URI
    if locked_tool == "vector":
        cfg.agent_retrieval["vector"]["vector_index"] = VECTOR_INDEX
    else:
        cfg.agent_retrieval["graph"]["chunk_seed_vector_index"] = VECTOR_INDEX

    def plan_route(state: AgentState) -> dict:
        policy_state = {**state, "_locked_tool": locked_tool}
        return _apply_action_policy(
            agent_nodes.plan_route_node(policy_state),
            locked_tool=locked_tool,
            top_k=top_k,
        )

    def assess(state: TaskWorkerState) -> dict:
        policy_state = {
            **state,
            "_locked_tool": locked_tool,
            "_assess_prompt_mode": "locked_eval",
        }
        return _apply_action_policy(
            agent_nodes.assess_node(policy_state),
            locked_tool=locked_tool,
            top_k=top_k,
        )

    def eval_synthesize(state: AgentState) -> dict:
        return eval_synthesize_node(state, generate_answer=generate_answer)

    task_workflow = StateGraph(TaskWorkerState)
    task_workflow.add_node("execute", agent_nodes.execute_attempt_node)
    task_workflow.add_node("assess", assess)
    task_workflow.add_edge(START, "execute")
    task_workflow.add_conditional_edges(
        "execute",
        _route_after_execute,
        {"execute": "execute", "assess": "assess", "end": END},
    )
    task_workflow.add_conditional_edges(
        "assess",
        _route_after_assess,
        {"execute": "execute", "end": END},
    )
    task_graph = task_workflow.compile()

    def task_worker(state: dict) -> dict:
        task = state["task"]
        result = task_graph.invoke({
            "original_query": state.get("original_query", ""),
            "task": task,
            "current_action": dict(task["initial_action"]),
            "attempts": [],
        })
        completion = result.get("completion") or {
            "task_id": task["task_id"],
            "sufficient": False,
            "stop_reason": result.get("stop_reason") or "unsupported",
        }
        return {
            "task_results": [{
                "task_id": task["task_id"],
                "attempts": result.get("attempts") or [],
                "completion": completion,
            }],
        }

    workflow = StateGraph(AgentState)
    workflow.add_node("plan_route", plan_route)
    workflow.add_node("task_worker", task_worker)
    workflow.add_node("collector", _collect_task_results)
    workflow.add_node("eval_synthesize", eval_synthesize)

    workflow.add_edge(START, "plan_route")
    workflow.add_conditional_edges(
        "plan_route",
        _send_tasks,
        {"collector": "collector"},
    )
    workflow.add_edge("task_worker", "collector")
    workflow.add_edge("collector", "eval_synthesize")
    workflow.add_edge("eval_synthesize", END)
    max_parallel_tasks = get_config().agent_max_parallel_tasks
    return workflow.compile().with_config({
        "max_concurrency": max_parallel_tasks,
    })


def build_vector_eval_graph(
    top_k: int = DEFAULT_TOP_K,
    generate_answer: bool = True,
):
    return _build_eval_graph("vector", top_k, generate_answer)


def build_graph_eval_graph(
    top_k: int = DEFAULT_TOP_K,
    generate_answer: bool = True,
):
    return _build_eval_graph("graph", top_k, generate_answer)


SMOKE_QUERY = (
    "What percentage of Texas Instruments' 2022 total revenue was represented "
    "by restructuring charges disclosed in the Other segment, and how does "
    "the company's segment reporting structure explain the separation of these "
    "charges from operating segments like Embedded Processing?"
)


def _run_smoke_test() -> None:
    """Run one real Vector Agent query against Neo4j 7690 and the LLM."""
    print("=== Vector Agent Eval Smoke Test ===")
    print(f"Query: {SMOKE_QUERY}")

    graph = build_graph_eval_graph(top_k=10)
    result = graph.invoke({"original_query": SMOKE_QUERY})

    print("\n=== Final Answer ===")
    print(result.get("final_answer", ""))

    print("\n=== Attempts ===")
    for attempt in result.get("attempts") or []:
        action = attempt.get("action") or {}
        chunk_ids = [
            chunk.get("chunk_id")
            for chunk in (attempt.get("chunks") or [])
            if chunk.get("chunk_id")
        ]
        assessment = attempt.get("assessment") or {}
        print(
            f"{attempt.get('attempt_id')} | "
            f"tool={action.get('tool')} | "
            f"retrieval={attempt.get('retrieval_status')} | "
            f"chunks={chunk_ids} | "
            f"assessment={assessment.get('status')}"
        )

    trace = result.get("synthesis_trace") or {}
    print("\n=== Eval Synthesis Trace ===")
    print(f"status={trace.get('status')}")
    print(f"selected_chunk_ids={trace.get('selected_chunk_ids', [])}")
    print(f"latency_sec={trace.get('latency_sec')}")


if __name__ == "__main__":
    _run_smoke_test()
