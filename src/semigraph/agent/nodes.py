
from semigraph.agent.state import AgentState
from semigraph.config import get_config
from semigraph.connections import get_llm
from semigraph.agent.prompts import PLANNER_SYSTEM_PROMPT,TOOL_SELECT_SYSTEM_PROMPT
from semigraph.agent.tools import TOOL_SCHEMAS
import json


def plan_node(state: AgentState) -> dict:
    """
    Plan the next action based on the current state.

    Args:
        state (AgentState): original_query (str).

    Returns:
        dict: {
            "subqueries": [str],          # 1-3 decomposed sub-questions
            "current_subquery_idx": int,  # always 0 at plan time
            "round": int,                 # always 0 at plan time
        }
    """
    print(f"Node : Plan Node")
    cfg = get_config()
    llm = get_llm(cfg)

    original_query = state["original_query"]
    fallback = {
        "subqueries": [original_query],
        "current_subquery_idx": 0,
        "round": 0,
    }

    response = llm.invoke([
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": original_query},
    ])

    raw = response.content if hasattr(response, "content") else str(response)

    try:
        content = raw.strip()
        content = content[content.find("{") : content.rfind("}") + 1]

        parsed = json.loads(content)

        subqueries = [
            q for q in parsed.get("subqueries", [])
            if isinstance(q, str) and q.strip()
        ][:3]

        if not subqueries:
            subqueries = [original_query]

        return {
            "subqueries": subqueries,
            "current_subquery_idx": 0,
            "round": 0,
        }

    except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
        return fallback

def tool_select_node(state: AgentState) -> dict:
    """
    Select the best tool for the current subquery.  
    Args:
        state (AgentState): subqueries (list[str]), current_subquery_idx (int).
    Returns:
        next_tool state
    """
    print(f"Node : Tool Select Node")
    cfg = get_config()
    llm = get_llm(cfg)

    subquery = state["subqueries"][state["current_subquery_idx"]]

    fallback = {"next_tool": {
        "name": "vector", 
        "args": {
            "query": subquery, 
            "top_k_chunks": 5
            }
        }
    }


    llm_with_tools = llm.bind_tools(TOOL_SCHEMAS)
    try:
        response = llm_with_tools.invoke([{"role": "system", "content": TOOL_SELECT_SYSTEM_PROMPT}, 
                                {"role": "user", "content": subquery}])
        
        if not response.tool_calls or not response.tool_calls[0]["args"] or "query" not in response.tool_calls[0]["args"]:
            return fallback

        return {
            "next_tool": {
                "name": response.tool_calls[0]["name"], 
                "args": response.tool_calls[0]["args"]
            }
        }
    except Exception as e:
        print(f"Error during tool selection: {e}")
        return fallback

def execute_node(state: AgentState) -> dict:
    print(f"Node : Execute Node")
    return {}

def observe_node(state: AgentState) -> dict:
    print(f"Node : Observe Node")
    return {}

def reflect_node(state: AgentState) -> dict:
    print(f"Node : Reflect Node")
    return {}

def synthesize_node(state: AgentState) -> dict:
    print(f"Node : Synthesize Node")
    return {}