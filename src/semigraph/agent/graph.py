from collections.abc import Callable

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from semigraph.agent import nodes
from semigraph.agent.state import AgentState, TaskWorkerState
from semigraph.config import get_config


LOCKABLE_TOOLS = {"vector", "graph"}


def _apply_action_policy(
    update: dict,
    locked_tool: str | None,
    top_k: int | None,
) -> dict:
    """Apply an evaluation policy without changing planner/assessor logic."""
    if locked_tool is None and top_k is None:
        return update

    def normalize(action: dict) -> dict:
        normalized = dict(action)
        if locked_tool is not None:
            normalized["tool"] = locked_tool
        if top_k is not None:
            normalized["top_k_chunks"] = top_k
        return normalized

    result = dict(update)
    if result.get("current_action"):
        result["current_action"] = normalize(result["current_action"])

    if result.get("tasks"):
        result["tasks"] = [
            {
                **task,
                "initial_action": normalize(task["initial_action"]),
            }
            for task in result["tasks"]
        ]
    return result


def _send_tasks(state: AgentState) -> list[Send] | str:
    """Fan out one isolated worker for every planned Task."""
    tasks = state.get("tasks") or []
    if not tasks:
        return "collector"
    return [
        Send(
            "task_worker",
            {
                "original_query": state.get("original_query", ""),
                "task": task,
            },
        )
        for task in tasks
    ]


def _route_after_execute(state: TaskWorkerState) -> str:
    attempts = state.get("attempts") or []
    task = state.get("task") or {}
    task_id = task.get("task_id") if isinstance(task, dict) else None
    latest = attempts[-1] if attempts else {}

    if (
        latest.get("task_id") == task_id
        and latest.get("retrieval_status") == "ok"
        and latest.get("assessment") is None
    ):
        return "assess"
    return "execute" if state.get("current_action") else "end"


def _route_after_assess(state: TaskWorkerState) -> str:
    return "execute" if state.get("current_action") else "end"


def _collect_task_results(state: AgentState) -> dict:
    """Restore deterministic Plan order before the single Synthesis call."""
    results_by_id = {
        result["task_id"]: result
        for result in (state.get("task_results") or [])
    }
    attempts = []
    completed_tasks = []

    for task in state.get("tasks") or []:
        result = results_by_id.get(task.get("task_id"))
        if not result:
            continue
        attempts.extend(result["attempts"])
        completed_tasks.append(result["completion"])

    update = {
        "attempts": attempts,
        "completed_tasks": completed_tasks,
    }
    if completed_tasks:
        update["stop_reason"] = completed_tasks[-1]["stop_reason"]
    return update


def build_agent(
    *,
    locked_tool: str | None = None,
    top_k: int | None = None,
    synthesis: Callable[[AgentState], dict] | None = None,
):
    """Build the Agent harness with isolated parallel Task workers.

    Production uses the default autonomous policy. Evaluations may lock every
    initial and retry action to Graph or Vector while keeping the same harness.
    """
    if locked_tool is not None and locked_tool not in LOCKABLE_TOOLS:
        raise ValueError(f"Unsupported locked tool: {locked_tool}")
    if top_k is not None and top_k < 1:
        raise ValueError("top_k must be positive")

    def plan_route(state: AgentState) -> dict:
        return _apply_action_policy(
            nodes.plan_route_node(state, locked_tool=locked_tool),
            locked_tool,
            top_k,
        )

    def assess(state: TaskWorkerState) -> dict:
        return _apply_action_policy(
            nodes.assess_node(state, locked_tool=locked_tool),
            locked_tool,
            top_k,
        )

    task_workflow = StateGraph(TaskWorkerState)
    task_workflow.add_node("execute", nodes.execute_attempt_node)
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
    workflow.add_node(
        "synthesize",
        synthesis or nodes.synthesize_attempts_node,
    )

    workflow.add_edge(START, "plan_route")
    workflow.add_conditional_edges(
        "plan_route",
        _send_tasks,
        {"collector": "collector"},
    )
    workflow.add_edge("task_worker", "collector")
    workflow.add_edge("collector", "synthesize")
    workflow.add_edge("synthesize", END)
    max_parallel_tasks = get_config().agent_max_parallel_tasks
    return workflow.compile().with_config({
        "max_concurrency": max_parallel_tasks,
    })
