from semigraph.agent.state import AgentState
from semigraph.agent.tools import DEFAULT_TOP_K, RETRIEVERS, TOOL_SCHEMAS
from semigraph.config import get_config
from semigraph.connections import get_llm
import json
import re

from semigraph.agent.prompts import (
    OBSERVE_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    REFLECT_SYSTEM_PROMPT,
    SYNTHESIZE_SYSTEM_PROMPT,
    TOOL_SELECT_SYSTEM_PROMPT,
)


MAX_REFLECTION_ROUNDS = 5


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

    subquery = _get_current_subquery(state)
    retry_query = state.get("retry_query") or subquery
    reflection_feedback = state.get("reflection_feedback", "")

    fallback = {"next_tool": {
        "name": "vector", 
        "args": {
            "query": retry_query, 
            "top_k_chunks": 5
            }
        }
    }


    llm_with_tools = llm.bind_tools(TOOL_SCHEMAS)
    try:
        user_content = (
            f"Subquery: {subquery}\n"
            f"Query candidate: {retry_query}"
        )
        if reflection_feedback:
            user_content += f"\nReflection feedback: {reflection_feedback}"

        response = llm_with_tools.invoke([
            {"role": "system", "content": TOOL_SELECT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ])
        
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
    """Run the tool selected by tool_select_node and persist its outputs.

    This node is intentionally dumb: it should only execute the already-picked
    retriever, append new chunks into the running history, and record a compact
    trace entry for later observation / visualization nodes.
    Args:
        state (AgentState): next_tool (dict), chunks_history (list[dict]), tool_call_log (list[dict]), current_subquery_idx (int), subqueries (list[str]), original_query (str), round (int).
    Returns:
        dict: {
            "chunks_history": list[dict],  # all chunks seen so far
            "latest_chunks": list[dict],   # chunks returned by this tool call
            "tool_call_log": list[dict],   # compact trace of tool calls
        }
    """
    print(f"Node : Execute Node")

    cfg = get_config()
    next_tool = state.get("next_tool", {})
    tool_name = next_tool.get("name")
    tool_args = next_tool.get("args") or {}
    chunks_history = list(state.get("chunks_history") or [])
    tool_call_log = list(state.get("tool_call_log") or [])

    current_idx = state.get("current_subquery_idx", 0)
    subqueries = state.get("subqueries") or []
    current_subquery = (
        subqueries[current_idx]
        if 0 <= current_idx < len(subqueries)
        else state.get("original_query", "")
    )

    query = tool_args.get("query") or current_subquery
    top_k_chunks = tool_args.get("top_k_chunks", DEFAULT_TOP_K)

    retriever = RETRIEVERS.get(tool_name) if tool_name else None
    if retriever is None:
        error_msg = f"No retriever found for tool '{tool_name}'"
        print(f"Error: {error_msg}")
        tool_call_log.append({
            "round": state.get("round", 0),
            "subquery": current_subquery,
            "tool": tool_name,
            "query": query,
            "top_k_chunks": top_k_chunks,
            "n_chunks": 0,
            "status": "error",
            "error": error_msg,
        })
        return {
            "chunks_history": chunks_history,
            "latest_chunks": [],
            "tool_call_log": tool_call_log,
        }

    try:
        raw_chunks = retriever(
            query=query,
            top_k_chunks=top_k_chunks,
            cfg=cfg,
        )
        chunks = [c for c in (raw_chunks or []) if isinstance(c, dict)]
        chunks_history.extend(chunks)
        tool_call_log.append({
            "round": state.get("round", 0),
            "subquery": current_subquery,
            "tool": tool_name,
            "query": query,
            "top_k_chunks": top_k_chunks,
            "n_chunks": len(chunks),
            "status": "ok",
        })
        return {
            "chunks_history": chunks_history,
            "latest_chunks": chunks,
            "tool_call_log": tool_call_log,
        }
    except Exception as e:
        print(f"Error during execution of tool '{tool_name}': {e}")
        tool_call_log.append({
            "round": state.get("round", 0),
            "subquery": current_subquery,
            "tool": tool_name,
            "query": query,
            "top_k_chunks": top_k_chunks,
            "n_chunks": 0,
            "status": "error",
            "error": str(e),
        })
        return {
            "chunks_history": chunks_history,
            "latest_chunks": [],
            "tool_call_log": tool_call_log,
        }


def observe_node(state: AgentState) -> dict:
    print(f"Node : Observe Node")
    latest_chunks = list(state.get("latest_chunks") or [])
    observation_history = list(state.get("observation_history") or [])
    current_subquery = _get_current_subquery(state)
    tool_name = (state.get("next_tool") or {}).get("name")
    round_no = state.get("round", 0)

    if not latest_chunks:
        observation_text = "The retrieval did not find evidence."
    else:
        try:
            cfg = get_config()
            llm = get_llm(cfg)
            chunks_text = _format_chunks_for_observation(latest_chunks)
            response = llm.invoke([
                {"role": "system", "content": OBSERVE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Subquery: {current_subquery}\n"
                        f"Selected tool: {tool_name or 'unknown'}\n"
                        f"Retrieved chunks ({len(latest_chunks)}):\n"
                        f"{chunks_text}"
                    ),
                },
            ])
            raw = response.content if hasattr(response, "content") else str(response)
            observation_text = raw.strip() or "The retrieval did not find relevant evidence."
        except Exception as e:
            print(f"Error during observation: {e}")
            observation_text = _fallback_observation(
                chunks=latest_chunks,
                subquery=current_subquery,
                tool_name=tool_name,
            )

    observation_history.append({
        "round": round_no,
        "subquery": current_subquery,
        "tool": tool_name,
        "n_chunks": len(latest_chunks),
        "observation_text": observation_text,
    })

    return {
        "observation_text": observation_text,
        "observation_history": observation_history,
    }


        


def reflect_node(state: AgentState) -> dict:
    print(f"Node : Reflect Node")
    current_round = state.get("round", 0)
    next_round = current_round + 1
    current_subquery = _get_current_subquery(state)
    reflection_history = list(state.get("reflection_history") or [])
    default_retry_query = (
        current_subquery
        or state.get("retry_query")
        or state.get("original_query", "")
    )

    if next_round >= MAX_REFLECTION_ROUNDS:
        sufficient = True
        reflection_reason = (
            f"Forced stop at round {next_round}: reached max reflection rounds "
            f"({MAX_REFLECTION_ROUNDS})."
        )
        reflection_feedback = ""
        retry_query = ""
        stop_reason = "max_rounds"
    else:
        try:
            cfg = get_config()
            llm = get_llm(cfg)
            response = llm.invoke([
                {"role": "system", "content": REFLECT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _format_reflection_context(state),
                },
            ])
            raw = response.content if hasattr(response, "content") else str(response)
            parsed = _parse_reflection_response(raw)

            sufficient = parsed["sufficient"]
            reflection_reason = parsed["reason"]
            reflection_feedback = parsed["feedback"]
            retry_query = parsed["retry_query"]
            stop_reason = "sufficient" if sufficient else "needs_more_evidence"

            if sufficient:
                reflection_feedback = ""
                retry_query = ""
            else:
                retry_query = retry_query or default_retry_query
        except Exception as e:
            print(f"Error during reflection: {e}")
            sufficient = False
            reflection_reason = (
                f"Reflection fallback: could not parse reflection response "
                f"({type(e).__name__})."
            )
            reflection_feedback = (
                "Need a more targeted retrieval pass based on the missing evidence."
            )
            retry_query = default_retry_query
            stop_reason = "reflection_fallback"

    reflection_history.append({
        "round": next_round,
        "subquery": current_subquery,
        "sufficient": sufficient,
        "reason": reflection_reason,
        "feedback": reflection_feedback,
        "retry_query": retry_query,
        "stop_reason": stop_reason,
    })

    return {
        "round": next_round,
        "sufficient": sufficient,
        "reflection_reason": reflection_reason,
        "reflection_feedback": reflection_feedback,
        "retry_query": retry_query,
        "stop_reason": stop_reason,
        "reflection_history": reflection_history,
    }


def advance_subquery_node(state: AgentState) -> dict:
    print(f"Node : Advance Subquery Node")

    current_idx = state.get("current_subquery_idx", 0)
    subqueries = state.get("subqueries") or []
    next_idx = min(current_idx + 1, max(len(subqueries) - 1, 0))
    completed_subqueries = list(state.get("completed_subqueries") or [])
    completed_subqueries.append(_build_subquery_completion(state))

    return {
        "current_subquery_idx": next_idx,
        "completed_subqueries": completed_subqueries,
        "round": 0,
        "sufficient": False,
        "retry_query": "",
        "reflection_feedback": "",
        "reflection_reason": "",
        "stop_reason": "advance_subquery",
        "next_tool": {},
        "latest_chunks": [],
        "observation_text": "",
    }


def synthesize_node(state: AgentState) -> dict:
    print(f"Node : Synthesize Node")

    original_query = state.get("original_query", "")
    chunks_history = list(state.get("chunks_history") or [])
    subquery_progress = _collect_subquery_progress(state)
    stop_reason = _derive_overall_stop_reason(subquery_progress)
    reflection_reason = state.get("reflection_reason", "")

    deduped_chunks = _dedupe_chunks_for_synthesis(chunks_history)
    if not deduped_chunks:
        return {
            "final_answer": "I do not have enough evidence to answer the question.",
            "citation_map": [],
            "completed_subqueries": subquery_progress,
        }
    
    formatted_context, citation_lookup = _format_chunks_for_synthesis(deduped_chunks)
    try:
        llm = get_llm(get_config())
        response = llm.invoke([
            {"role": "system", "content": SYNTHESIZE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Original Query: {original_query}\n"
                    f"stop_reason: {stop_reason}\n"
                    f"reflection_reason: {reflection_reason}\n"
                    f"subquery_progress:\n{_format_subquery_progress(subquery_progress)}\n"
                    f"evidence chunks:\n{formatted_context}"
                ),
            },
        ])
        raw = response.content if hasattr(response, "content") else str(response)
        answer = str(raw).strip()
        answer = _remove_invalid_citations(answer, set(citation_lookup))
        cited_indices = _extract_citation_indices(answer)
        citation_map = [
            citation_lookup[i] for i in cited_indices if i in citation_lookup
        ]
        return {
            "final_answer": answer,
            "citation_map": citation_map,
            "completed_subqueries": subquery_progress,
        }
    except Exception as e:
        print(f"Error during synthesis: {e}")
        return {
            "final_answer": "I could not synthesize a grounded final answer from the current evidence.",
            "citation_map": [],
            "completed_subqueries": subquery_progress,
        }



# Helper
def _get_current_subquery(state: AgentState) -> str:
    current_idx = state.get("current_subquery_idx", 0)
    subqueries = state.get("subqueries") or []
    if 0 <= current_idx < len(subqueries):
        return subqueries[current_idx]
    return state.get("original_query", "")


def _format_chunks_for_observation(
    chunks: list[dict],
    max_chunks: int = 5,
    max_chars: int = 800,
) -> str:
    formatted = []
    half = max_chars // 2

    for chunk in chunks[:max_chunks]:
        text = str(chunk.get("text") or "").strip()
        if len(text) > max_chars:
            text = f"{text[:half]} ... {text[-half:]}"

        formatted.append(
            (
                f"[{chunk.get('chunk_id', 'unknown_chunk')}] "
                f"{chunk.get('ticker', 'UNKNOWN')} "
                f"FY{chunk.get('fiscal_year', 'unknown')} "
                f"{chunk.get('section', 'unknown_section')}\n"
                f"{text}"
            )
        )

    return "\n\n".join(formatted)

def _format_reflection_context(state: AgentState) -> str:
    observation_history = list(state.get("observation_history") or [])
    tool_call_log = list(state.get("tool_call_log") or [])
    subqueries = list(state.get("subqueries") or [])
    current_idx = state.get("current_subquery_idx", 0)
    return "\n".join([
        f"Original query: {state.get('original_query', '')}",
        f"Planned subqueries: {json.dumps(subqueries)}",
        f"Current subquery position: {current_idx + 1}/{max(len(subqueries), 1)}",
        f"Current subquery: {_get_current_subquery(state)}",
        f"Current round: {state.get('round', 0)}",
        f"Latest observation: {state.get('observation_text', '')}",
        f"Observation history: {json.dumps(observation_history[-3:])}",
        f"Tool call log: {json.dumps(tool_call_log[-3:])}",
    ])

def _parse_reflection_response(raw: str) -> dict:
    content = raw.strip()
    content = content[content.find("{") : content.rfind("}") + 1]
    parsed = json.loads(content)

    sufficient = parsed.get("sufficient")
    if not isinstance(sufficient, bool):
        raise ValueError("reflection response missing boolean 'sufficient'")

    return {
        "sufficient": sufficient,
        "reason": str(parsed.get("reason", "")).strip(),
        "retry_query": str(parsed.get("retry_query", "")).strip(),
        "feedback": str(parsed.get("feedback", "")).strip(),
    }


def _route_after_reflect(state: AgentState) -> str:
    stop_reason = state.get("stop_reason", "")
    if stop_reason in {"sufficient", "max_rounds"}:
        if _has_remaining_subqueries(state):
            return "advance_subquery"
        return "synthesize"
    return "tool_select"


def _has_remaining_subqueries(state: AgentState) -> bool:
    subqueries = state.get("subqueries") or []
    current_idx = state.get("current_subquery_idx", 0)
    return current_idx + 1 < len(subqueries)


def _build_subquery_completion(state: AgentState) -> dict:
    return {
        "subquery_idx": state.get("current_subquery_idx", 0),
        "subquery": _get_current_subquery(state),
        "stop_reason": state.get("stop_reason", ""),
        "reflection_reason": state.get("reflection_reason", ""),
        "round": state.get("round", 0),
    }


def _collect_subquery_progress(state: AgentState) -> list[dict]:
    progress = list(state.get("completed_subqueries") or [])
    current_completion = _build_subquery_completion(state)

    if not progress:
        return [current_completion]

    if progress[-1].get("subquery_idx") != current_completion.get("subquery_idx"):
        progress.append(current_completion)

    return progress


def _derive_overall_stop_reason(subquery_progress: list[dict]) -> str:
    if any(item.get("stop_reason") == "max_rounds" for item in subquery_progress):
        return "max_rounds"
    return subquery_progress[-1].get("stop_reason", "") if subquery_progress else ""


def _format_subquery_progress(subquery_progress: list[dict]) -> str:
    if not subquery_progress:
        return "No subquery progress recorded."

    lines = []
    for item in subquery_progress:
        lines.append(
            (
                f"- subquery_{item.get('subquery_idx', 0) + 1}: "
                f"{item.get('subquery', '')} | "
                f"stop_reason={item.get('stop_reason', '')} | "
                f"round={item.get('round', 0)} | "
                f"reason={item.get('reflection_reason', '')}"
            )
        )

    return "\n".join(lines)



def _fallback_observation(
    chunks: list[dict],
    subquery: str,
    tool_name: str | None,
) -> str:
    first = chunks[0] if chunks else {}
    snippet = str(first.get("text") or "").strip().replace("\n", " ")
    snippet = snippet[:220]
    ticker = first.get("ticker", "UNKNOWN")
    fiscal_year = first.get("fiscal_year", "unknown")
    section = first.get("section", "unknown_section")
    return (
        f"Observation fallback: retrieved {len(chunks)} chunk(s) from "
        f"{tool_name or 'unknown'} for subquery '{subquery}'. "
        f"Top evidence is {ticker} FY{fiscal_year} {section}: {snippet}"
    ).strip()

def _dedupe_chunks_for_synthesis(chunk_history: list[dict]) -> list[dict]:
    """Return chunk history with duplicate evidence removed, preserving order.

    Primary dedupe key is `chunk_id`, because that is the stable identity
    across repeated runs. If a chunk is missing `chunk_id`, fall back to a
    content fingerprint built from the metadata fields we already surface in the
    agent trace.
    """
    deduped: list[dict] = []
    seen: set[tuple[str, ...]] = set()

    for chunk in chunk_history or []:
        if not isinstance(chunk, dict):
            continue

        chunk_id = str(chunk.get("chunk_id") or "").strip()
        if chunk_id:
            key = ("chunk_id", chunk_id)
        else:
            key = (
                "fingerprint",
                str(chunk.get("ticker") or ""),
                str(chunk.get("fiscal_year") or ""),
                str(chunk.get("section") or ""),
                str(chunk.get("text") or ""),
            )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(chunk)

    return deduped

def _format_chunks_for_synthesis(
    chunks: list[dict],
    max_chunks: int = 8,
    max_chars: int = 2000,
) -> tuple[str, dict[int, dict]]:
    formatted: list[str] = []
    citation_lookup: dict[int, dict] = {}

    for i, chunk in enumerate(chunks[:max_chunks], start=1):
        text = str(chunk.get("text") or "").strip()
        if len(text) > max_chars:
            text = f"{text[:max_chars]}..."

        formatted.append(
            (
                f"[{i}] chunk_id={chunk.get('chunk_id', 'UNKNOWN')}\n"
                f"ticker={chunk.get('ticker', '')}\n"
                f"fiscal_year={chunk.get('fiscal_year', '')}\n"
                f"section={chunk.get('section', '')}\n"
                f"text={text}"
            )
        )
        citation_lookup[i] = chunk

    return "\n\n".join(formatted), citation_lookup


def _extract_citation_indices(answer: str) -> list[int]:
    indices: list[int] = []
    seen: set[int] = set()

    for match in re.findall(r"\[(\d+)\]", answer or ""):
        index = int(match)
        if index in seen:
            continue
        seen.add(index)
        indices.append(index)

    return indices


def _remove_invalid_citations(answer: str, valid_indices: set[int]) -> str:
    def replace(match: re.Match[str]) -> str:
        index = int(match.group(1))
        return match.group(0) if index in valid_indices else ""

    sanitized = re.sub(r"\[(\d+)\]", replace, answer or "")
    sanitized = re.sub(r"\s+([.,;:])", r"\1", sanitized)
    sanitized = re.sub(r"[ \t]{2,}", " ", sanitized)
    return sanitized.strip()




if __name__ == "__main__":
    # Example usage
    state = AgentState(original_query="What are the NVDA?")
    plan_result = plan_node(state)
    print("Plan Result:", plan_result)

    state.update(plan_result)
    tool_select_result = tool_select_node(state)
    print("Tool Select Result:", tool_select_result)

    state.update(tool_select_result)
    execute_result = execute_node(state)
    print("Execute Result:", execute_result)
    
    state.update(execute_result)
    observe_result = observe_node(state)
    print("Observe Result:", observe_result)

    state.update(observe_result)
    
    
