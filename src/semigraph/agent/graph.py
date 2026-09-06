from collections.abc import Callable

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from semigraph.agent import nodes
from semigraph.agent.contracts import ToolName
from semigraph.agent.state import AgentState, TaskWorkerState
from semigraph.agent.trace_events import AgentTraceEmitter
from semigraph.config import Config, get_config
from semigraph.trace import TraceCallback


SUPPORTED_TOOLS = {tool.value for tool in ToolName}


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
    return "end"


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
    tool: str,
    synthesis: Callable[[AgentState], dict] | None = None,
    cfg: Config | None = None,
    trace_callback: TraceCallback | None = None,
):
    """Build parallel Task workers that all use one caller-selected Tool."""
    if tool not in SUPPORTED_TOOLS:
        raise ValueError(f"Unsupported Tool: {tool}")

    agent_config = cfg or get_config()

    tracer = AgentTraceEmitter(trace_callback)

    def plan_route(state: AgentState) -> dict:
        tracer.plan_started()
        update = nodes.plan_route_node(
            state,
            tool=tool,
            cfg=agent_config,
        )
        tracer.plan_finished(update)
        return update

    def assess(state: TaskWorkerState) -> dict:
        tracer.assess_started(state)
        update = nodes.assess_node(
            state,
            tool=tool,
            cfg=agent_config,
        )
        tracer.assess_finished(state["task"], update)
        return update

    def execute_attempt(state: TaskWorkerState) -> dict:
        tracer.execute_started(state)
        update = nodes.execute_attempt_node(state, cfg=agent_config)
        tracer.execute_finished(update)
        return update

    task_workflow = StateGraph(TaskWorkerState)
    task_workflow.add_node("execute", execute_attempt)
    task_workflow.add_node("assess", assess)
    task_workflow.add_edge(START, "execute")
    task_workflow.add_conditional_edges(
        "execute",
        _route_after_execute,
        {"assess": "assess", "end": END},
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
        tracer.task_finished(task, result, completion)
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
    if synthesis is not None:
        run_synthesis = synthesis
    else:
        run_synthesis = lambda state: nodes.synthesize_attempts_node(
            state,
            cfg=agent_config,
        )

    def synthesis_node(state: AgentState) -> dict:
        tracer.synthesis_started()
        update = run_synthesis(state)
        tracer.synthesis_finished(update)
        return update

    workflow.add_node("synthesize", synthesis_node)

    workflow.add_edge(START, "plan_route")
    workflow.add_conditional_edges(
        "plan_route",
        _send_tasks,
        {"collector": "collector"},
    )
    workflow.add_edge("task_worker", "collector")
    workflow.add_edge("collector", "synthesize")
    workflow.add_edge("synthesize", END)
    max_parallel_tasks = agent_config.agent_max_parallel_tasks
    return workflow.compile().with_config({
        "max_concurrency": max_parallel_tasks,
    })
