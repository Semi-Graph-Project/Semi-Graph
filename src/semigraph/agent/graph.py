from langgraph.graph import StateGraph, END, START

from semigraph.agent.state import AgentState
from semigraph.agent.nodes import plan_node, tool_select_node, execute_node, observe_node, reflect_node, synthesize_node



def build_agent():
    """
    Builds the agent's workflow graph.
    Returns:
        A compiled StateGraph representing the agent's workflow.
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("tool_select", tool_select_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("observe", observe_node)
    workflow.add_node("reflect", reflect_node)
    workflow.add_node("synthesize", synthesize_node)

    workflow.add_edge(START, "plan")
    workflow.add_edge("plan", "tool_select")
    workflow.add_edge("tool_select", "execute")
    workflow.add_edge("execute", "observe")
    workflow.add_edge("observe", "reflect")
    workflow.add_edge("reflect", "synthesize")
    workflow.add_edge("synthesize", END)

    graph = workflow.compile()
    return graph