from langgraph.graph import END, START, StateGraph

from semigraph.agent import nodes
from semigraph.agent.state import AgentState


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


def _route_after_plan(state: AgentState) -> str:
    return "execute" if state.get("current_action") else "synthesize"


def _route_after_execute(state: AgentState) -> str:
    attempts = state.get("attempts") or []
    tasks = state.get("tasks") or []
    index = state.get("current_task_index")
    task_id = (
        tasks[index].get("task_id")
        if isinstance(index, int) and 0 <= index < len(tasks)
        else None
    )
    latest = attempts[-1] if attempts else {}

    if (
        latest.get("task_id") == task_id
        and latest.get("retrieval_status") == "ok"
        and latest.get("assessment") is None
    ):
        return "assess"
    return "execute" if state.get("current_action") else "synthesize"


def _route_after_assess(state: AgentState) -> str:
    return "execute" if state.get("current_action") else "synthesize"


def build_agent(
    *,
    locked_tool: str | None = None,
    top_k: int | None = None,
):
    """Build the Four-Node Agent harness.

    Production uses the default autonomous policy. Evaluations may lock every
    initial and retry action to Graph or Vector while keeping the same harness.
    """
    if locked_tool is not None and locked_tool not in LOCKABLE_TOOLS:
        raise ValueError(f"Unsupported locked tool: {locked_tool}")
    if top_k is not None and top_k < 1:
        raise ValueError("top_k must be positive")

    def plan_route(state: AgentState) -> dict:
        policy_state = {**state, "_locked_tool": locked_tool}
        return _apply_action_policy(
            nodes.plan_route_node(policy_state),
            locked_tool,
            top_k,
        )

    def assess(state: AgentState) -> dict:
        policy_state = {**state, "_locked_tool": locked_tool}
        return _apply_action_policy(
            nodes.assess_node(policy_state),
            locked_tool,
            top_k,
        )

    workflow = StateGraph(AgentState)
    workflow.add_node("plan_route", plan_route)
    workflow.add_node("execute", nodes.execute_attempt_node)
    workflow.add_node("assess", assess)
    workflow.add_node("synthesize", nodes.synthesize_attempts_node)

    workflow.add_edge(START, "plan_route")
    workflow.add_conditional_edges(
        "plan_route",
        _route_after_plan,
        {"execute": "execute", "synthesize": "synthesize"},
    )
    workflow.add_conditional_edges(
        "execute",
        _route_after_execute,
        {
            "execute": "execute",
            "assess": "assess",
            "synthesize": "synthesize",
        },
    )
    workflow.add_conditional_edges(
        "assess",
        _route_after_assess,
        {"execute": "execute", "synthesize": "synthesize"},
    )
    workflow.add_edge("synthesize", END)
    return workflow.compile()
