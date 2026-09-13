from enum import Enum

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from semigraph.agents.nodes import (
    assess_node,
    collector_node,
    execute_node,
    plan_route_node,
    synthesize_node,
)
from semigraph.agents.state import AgentState, TaskWorkerState
from semigraph.config import Config, get_config


class ToolName(str, Enum):
    VECTOR = "vector"
    GRAPH = "graph"


def fan_out(state: AgentState):
    return [
        Send(
            "task_worker",
            {
                "original_query": state["original_query"],
                "task_index": task_index,
                "task": task,
            },
        )
        for task_index, task in enumerate(state["tasks"])
    ]


def build_agent(
    tool: ToolName | str = ToolName.GRAPH,
    cfg: Config | None = None,
    generate_answer: bool = True,
):
    selected_tool = ToolName(tool).value
    cfg = cfg or get_config()
    task_worker_graph = build_task_worker(tool=selected_tool, cfg=cfg)

    def plan_route(state: AgentState) -> dict:
        """
        PlanRoute Caller
        """
        return plan_route_node(
            state,
            tool=selected_tool,
            cfg=cfg,
        )

    def task_worker(state: TaskWorkerState) -> dict:
        result = task_worker_graph.invoke(state)
        return {"worker_results": [result]}

    def collector(state: AgentState) -> dict:
        return collector_node(state, cfg=cfg)

    def synthesize(state: AgentState) -> dict:
        return synthesize_node(state, cfg=cfg)

    workflow = StateGraph(AgentState)
    workflow.add_node("plan_route", plan_route)
    workflow.add_node("task_worker", task_worker)
    workflow.add_node("collector", collector)
    workflow.add_edge(START, "plan_route")
    workflow.add_conditional_edges(
        "plan_route",
        fan_out,
        ["task_worker"],
    )
    workflow.add_edge("task_worker", "collector")
    if generate_answer:
        workflow.add_node("synthesize", synthesize)
        workflow.add_edge("collector", "synthesize")
        workflow.add_edge("synthesize", END)
    else:
        workflow.add_edge("collector", END)

    return workflow.compile()


def run_agent(
    state: AgentState,
    tool: ToolName | str = ToolName.GRAPH,
    cfg: Config | None = None,
    generate_answer: bool = True,
) -> dict:
    """Run the root Agent with the configured parallel-task limit."""
    cfg = cfg or get_config()
    return build_agent(
        tool=tool,
        cfg=cfg,
        generate_answer=generate_answer,
    ).invoke(
        state,
        config={"max_concurrency": cfg.agent_max_parallel_tasks},
    )


def build_task_worker(
    tool: ToolName | str = ToolName.GRAPH,
    cfg: Config | None = None,
):
    selected_tool = ToolName(tool).value
    cfg = cfg or get_config()
    max_attempts = cfg.agent_max_attempts_per_task

    def execute(state: TaskWorkerState) -> dict:
        """
        Execute Caller
        """
        return execute_node(
            state,
            tool=selected_tool,
            top_k_chunks=cfg.agent_top_k_chunks,
            cfg=cfg,
        )

    def assess(state: TaskWorkerState) -> dict:
        """
        Assess Caller
        """
        return assess_node(
            state,
            cfg=cfg,
        )

    def route_after_assess(state: TaskWorkerState) -> str:
        if state.get("stop_reason"):
            return "stop"

        if state["assessment"]["is_covered"]:
            return "stop"

        attempts_used = len(state.get("attempts", []))
        return "stop" if attempts_used >= max_attempts else "retry"

    workflow = StateGraph(TaskWorkerState)
    workflow.add_node("execute", execute)
    workflow.add_node("assess", assess)

    workflow.add_edge(START, "execute")
    workflow.add_edge("execute", "assess")
    workflow.add_conditional_edges(
        "assess",
        route_after_assess,
        {
            "retry": "execute",
            "stop": END,
        },
    )

    return workflow.compile()


def run_task_worker(
    state: TaskWorkerState,
    tool: ToolName | str = ToolName.GRAPH,
    cfg: Config | None = None,
) -> dict:
    """Run one Task through the TaskWorker workflow."""
    return build_task_worker(tool=tool, cfg=cfg).invoke(state)
