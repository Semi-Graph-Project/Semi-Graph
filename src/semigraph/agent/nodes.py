import json
import re
import time
from decimal import Decimal, InvalidOperation

from semigraph.agent.prompts import (
    OBSERVE_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    REFLECT_SYSTEM_PROMPT,
    SYNTHESIZE_SYSTEM_PROMPT,
    TOOL_SELECT_SYSTEM_PROMPT,
)
from semigraph.agent.state import AgentState
from semigraph.agent.tools import DEFAULT_TOP_K, RETRIEVERS, TOOL_SCHEMAS
from semigraph.config import Config, get_config
from semigraph.connections import get_llm

from pydantic import ValidationError
from semigraph.agent.contracts import PlanRouteOutput
from semigraph.agent.prompts import PLAN_ROUTE_SYSTEM_PROMPT




MAX_REFLECTION_ROUNDS = 3
MAX_PLAN_ROUTE_ATTEMPTS = 2

FINANCIAL_METRIC_PATTERNS = (
    r"\brevenue\b",
    r"\bgross margin\b",
    r"\beps\b",
    r"\bearnings per share\b",
    r"\bnet income\b",
    r"\boperating margin\b",
    r"\bcash flow\b",
    r"\bmarket cap\b",
    r"\bdebt\b",
    r"\bstock price\b",
    r"\bp/e\b",
    r"\broe\b",
)

FINANCIAL_PERIOD_PATTERNS = (
    r"\bannual\b",
    r"\bfiscal year\b",
    r"\bfy\s*20\d{2}\b",
    r"\bq[1-4]\b",
    r"\bquarter(?:ly)?\b",
)

RECENCY_PATTERNS = (
    r"\blatest\b",
    r"\brecent\b",
    r"\btoday\b",
    r"\bthis week\b",
    r"ข่าวล่าสุด",
    r"เมื่อเร็ว ๆ นี้",
)

EXPLICIT_NEWS_PATTERNS = (
    r"\bnews\b",
    r"\bannouncement(?:s)?\b",
    r"\bpress release(?:s)?\b",
    r"\barticle(?:s)?\b",
    r"\bcoverage\b",
    r"ข่าว",
    r"พาดหัว",
    r"ประกาศ",
    r"บทความ",
)

def _parse_plan_route_response(raw: str) -> PlanRouteOutput:
    """
    Parse the raw response from the LLM for the plan route node.

    Args:
        raw (str): The raw string response from the LLM.

    Returns:
        PlanRouteOutput: Validated plan route output.
    """
    content = raw.strip()
    content = content[content.find("{") : content.rfind("}") + 1]

    try:
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("Parsed JSON is not a dictionary.")
        # create + validate PlanRouteOutput
        return PlanRouteOutput.model_validate(payload)

    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        raise ValueError(f"Failed to parse and validate plan route response: {e}")


def _collect_plan_warnings(
    original_query: str,
    plan: PlanRouteOutput,
    cfg: Config,
) -> list[dict]:
    """Report explicit query anchors that disappeared from a valid plan.

    This is a conservative diagnostic check. It never changes or rejects the
    plan; semantic validation remains the planner's responsibility.
    """

    def normalize(text: str) -> str:
        return re.sub(r"[_\-\s]+", " ", text).strip().casefold()

    def contains_phrase(text: str, phrase: str) -> bool:
        return bool(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text))

    plan_parts: list[str] = []
    for task in plan.tasks:
        plan_parts.append(task.query)
        plan_parts.extend(requirement.description for requirement in task.requirements)
        plan_parts.append(task.initial_action.query)


    plan_text = " ".join(plan_parts)
    normalized_query = normalize(original_query)
    normalized_plan = normalize(plan_text)
    warnings: list[dict] = []

    for ticker in cfg.tickers:
        ticker_text = normalize(ticker)
        if (
            contains_phrase(normalized_query, ticker_text)
            and not contains_phrase(normalized_plan, ticker_text)
        ):
            warnings.append({
                "code": "missing_explicit_anchor",
                "anchor_type": "ticker",
                "value": ticker,
            })

    period_pattern = re.compile(
        r"\b(?:fy\s*(?:19|20)\d{2}|(?:19|20)\d{2}|q[1-4])\b",
        re.IGNORECASE,
    )

    def extract_periods(text: str) -> list[tuple[str, str]]:
        periods: list[tuple[str, str]] = []
        seen_keys: set[str] = set()
        for match in period_pattern.finditer(text):
            display_value = re.sub(r"\s+", "", match.group()).upper()
            comparison_key = (
                display_value[2:] if display_value.startswith("FY") else display_value
            )
            if comparison_key not in seen_keys:
                periods.append((comparison_key, display_value))
                seen_keys.add(comparison_key)
        return periods

    plan_periods = {key for key, _ in extract_periods(plan_text)}
    for comparison_key, display_value in extract_periods(original_query):
        if comparison_key not in plan_periods:
            warnings.append({
                "code": "missing_explicit_anchor",
                "anchor_type": "period",
                "value": display_value,
            })

    registered_metrics = sorted({
        metric
        for metric_group in cfg.financial_metric_registry.values()
        for metric in metric_group
    })
    for metric in registered_metrics:
        metric_text = normalize(metric)
        if (
            contains_phrase(normalized_query, metric_text)
            and not contains_phrase(normalized_plan, metric_text)
        ):
            warnings.append({
                "code": "missing_explicit_anchor",
                "anchor_type": "metric",
                "value": metric,
            })

    return warnings


def plan_route_node(state: AgentState) -> dict:
    print(f"Node : Plan Route Node")
    started_at = time.perf_counter()
    original_query = state.get("original_query", "")
    attempts: list[dict] = []
    llm_calls = 0

    def error_update(fallback_source: str) -> dict:
        return {
            "tasks": [],
            "current_task_index": 0,
            "current_action": {},
            "stop_reason": "plan_error",
            "plan_trace": {
                "status": "error",
                "validation_mode": "structural_only_v1",
                "attempts": attempts,
                "warnings": [],
                "llm_calls": llm_calls,
                "latency_sec": time.perf_counter() - started_at,
                "fallback_source": fallback_source,
            },
        }

    if not isinstance(original_query, str) or not original_query.strip():
        return error_update("empty_query")

    original_query = original_query.strip()
    cfg = get_config()
    llm = get_llm(cfg)
    previous_raw = ""
    previous_error = ""

    for attempt_number in range(1, MAX_PLAN_ROUTE_ATTEMPTS + 1):
        user_message = original_query
        if attempt_number > 1:
            user_message = (
                f"Original query:\n{original_query}\n\n"
                f"Previous invalid output:\n{previous_raw}\n\n"
                f"Validation error:\n{previous_error}\n\n"
                "Repair the plan and return only valid JSON matching the required schema."
            )

        try:
            llm_calls += 1
            response = llm.invoke([
                {"role": "system", "content": PLAN_ROUTE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ])
        except Exception as exc:
            attempts.append({
                "attempt": attempt_number,
                "status": "provider_error",
                "errors": [type(exc).__name__],
            })
            return error_update("provider_error")

        raw = response.content if hasattr(response, "content") else str(response)
        if not isinstance(raw, str):
            raw = str(raw)

        try:
            plan_route = _parse_plan_route_response(raw)
        except ValueError as e:
            attempts.append({
                "attempt": attempt_number,
                "status": "invalid",
                "errors": ["plan_response_failed_validation"],
            })
            previous_raw = raw
            previous_error = str(e)
            if attempt_number == MAX_PLAN_ROUTE_ATTEMPTS:
                return error_update("validation_failed_after_repair")
            continue

        attempts.append({
            "attempt": attempt_number,
            "status": "valid",
            "errors": [],
        })
        warnings = _collect_plan_warnings(original_query, plan_route, cfg)
        serialized = plan_route.model_dump(mode="json")

        return {
            "tasks": serialized["tasks"],
            "current_task_index": 0,
            "current_action": serialized["tasks"][0]["initial_action"],
            "plan_trace": {
                "status": "ok" if attempt_number == 1 else "repaired",
                "validation_mode": "structural_only_v1",
                "attempts": attempts,
                "warnings": warnings,
                "llm_calls": llm_calls,
                "latency_sec": time.perf_counter() - started_at,
                "fallback_source": None,
            },
        }

    return error_update("validation_failed_after_repair")


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
    fallback_tool = (
        "financial"
        if _should_force_financial_tool(subquery, retry_query, reflection_feedback)
        else "vector"
    )

    fallback = {"next_tool": {
        "name": fallback_tool,
        "args": {
            "query": retry_query, 
            "top_k_chunks": DEFAULT_TOP_K
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

        print("responds : ")
        print(response)

        print("Tools Calls : ")
        print(response.tool_calls)

        selected_tool_name = response.tool_calls[0]["name"]
        selected_tool_args = dict(response.tool_calls[0]["args"])

        if (
            _should_force_financial_tool(subquery, retry_query, reflection_feedback)
            and selected_tool_name != "financial"
        ):
            selected_tool_name = "financial"
            selected_tool_args["query"] = retry_query
            selected_tool_args.setdefault("top_k_chunks", DEFAULT_TOP_K)

        return {
            "next_tool": {
                "name": selected_tool_name,
                "args": selected_tool_args,
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
            "retrieval_trace_history": list[dict],  # stage-level debug traces
        }
    """
    print(f"Node : Execute Node")

    cfg = get_config()
    next_tool = state.get("next_tool", {})
    tool_name = next_tool.get("name")
    tool_args = next_tool.get("args") or {}
    chunks_history = list(state.get("chunks_history") or [])
    tool_call_log = list(state.get("tool_call_log") or [])
    retrieval_trace_history = list(state.get("retrieval_trace_history") or [])

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
        retrieval_trace_history.append({
            "round": state.get("round", 0),
            "subquery": current_subquery,
            "tool": tool_name,
            "query": query,
            "status": "error",
            "error": error_msg,
        })
        return {
            "chunks_history": chunks_history,
            "latest_chunks": [],
            "tool_call_log": tool_call_log,
            "retrieval_trace_history": retrieval_trace_history,
        }

    try:
        retrieval_started = time.perf_counter()
        retriever_result = retriever(
            query=query,
            top_k_chunks=top_k_chunks,
            cfg=cfg,
        )
        if isinstance(retriever_result, dict) and "chunks" in retriever_result:
            raw_chunks = retriever_result.get("chunks") or []
            retriever_trace = dict(retriever_result.get("trace") or {})
        else:
            raw_chunks = retriever_result or []
            retriever_trace = {
                "retriever": tool_name,
                "profile": "default",
                "parameters": {"top_k_chunks": top_k_chunks},
            }

        chunks = [c for c in (raw_chunks or []) if isinstance(c, dict)]
        chunks_history.extend(chunks)
        retrieval_trace_history.append({
            "round": state.get("round", 0),
            "subquery": current_subquery,
            "tool": tool_name,
            "query": query,
            "status": "ok",
            "latency_sec": round(time.perf_counter() - retrieval_started, 3),
            **retriever_trace,
            "returned_count": len(chunks),
            "returned_chunk_ids": [
                str(chunk["chunk_id"])
                for chunk in chunks
                if chunk.get("chunk_id")
            ],
        })
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
            "retrieval_trace_history": retrieval_trace_history,
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
        retrieval_trace_history.append({
            "round": state.get("round", 0),
            "subquery": current_subquery,
            "tool": tool_name,
            "query": query,
            "status": "error",
            "latency_sec": round(time.perf_counter() - retrieval_started, 3),
            "error_type": type(e).__name__,
            "error": str(e),
        })
        return {
            "chunks_history": chunks_history,
            "latest_chunks": [],
            "tool_call_log": tool_call_log,
            "retrieval_trace_history": retrieval_trace_history,
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

    selected_chunks = _select_chunks_for_synthesis(state)
    deduped_chunks = _dedupe_chunks_for_synthesis(selected_chunks or chunks_history)
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
            {"citation_index": i, **citation_lookup[i]}
            for i in cited_indices
            if i in citation_lookup
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


def _normalize_router_text(*parts: str) -> str:
    return re.sub(r"\s+", " ", " ".join(part for part in parts if part)).strip().lower()


def _matches_any_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _has_financial_metric_intent(text: str) -> bool:
    return _matches_any_pattern(text, FINANCIAL_METRIC_PATTERNS)


def _has_financial_period_intent(text: str) -> bool:
    return _matches_any_pattern(text, FINANCIAL_PERIOD_PATTERNS)


def _has_recency_marker(text: str) -> bool:
    return _matches_any_pattern(text, RECENCY_PATTERNS)


def _has_explicit_news_intent(text: str) -> bool:
    return _matches_any_pattern(text, EXPLICIT_NEWS_PATTERNS)


def _should_force_financial_tool(*parts: str) -> bool:
    text = _normalize_router_text(*parts)
    if not text or _has_explicit_news_intent(text):
        return False
    return _has_financial_metric_intent(text) or (
        _has_recency_marker(text) and _has_financial_period_intent(text)
    )


_PERCENTAGE_METRICS = frozenset({
    "gross_margin",
    "operating_margin",
    "net_margin",
    "rd_intensity",
    "free_cash_flow_margin",
    "revenue_growth_yoy",
    "net_income_growth_yoy",
    "roa",
    "roe",
})

_FINANCIAL_PROVENANCE_KEYS = (
    "fact_id",
    "derived_id",
    "input_fact_ids",
    "formula_version",
    "accession",
    "raw_payload_id",
    "source_concept",
    "missing_inputs",
    "aggregation",
    "row_count",
    "tickers",
)


def _is_structured_financial_chunk(chunk: dict) -> bool:
    return bool(chunk.get("metric")) and "value" in chunk


def _decimal_text(value: Decimal, places: int = 2) -> str:
    return f"{value:,.{places}f}".rstrip("0").rstrip(".")


def _scaled_currency(value: Decimal) -> str:
    for threshold, suffix in (
        (Decimal("1000000000000"), "T"),
        (Decimal("1000000000"), "B"),
        (Decimal("1000000"), "M"),
        (Decimal("1000"), "K"),
    ):
        if abs(value) >= threshold:
            return f"${_decimal_text(value / threshold)}{suffix}"
    return f"${_decimal_text(value)}"


def _format_financial_value(chunk: dict) -> str:
    raw_value = chunk.get("value")
    unit = str(chunk.get("unit") or "").strip()
    if raw_value is None:
        return "unavailable"

    exact = f"{raw_value} {unit}".strip()
    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError):
        return exact

    normalized_unit = unit.lower()
    metric = str(chunk.get("metric") or "").lower()
    if normalized_unit == "ratio":
        display = (
            f"{_decimal_text(value * 100)}%"
            if metric in _PERCENTAGE_METRICS
            else f"{_decimal_text(value)}x"
        )
    elif normalized_unit == "percent":
        display = f"{_decimal_text(value)}%"
    elif normalized_unit == "usd_million":
        display = _scaled_currency(value * Decimal("1000000"))
    elif normalized_unit in {"usd", "u_usd"}:
        display = _scaled_currency(value)
    elif "share" in normalized_unit:
        display = f"${_decimal_text(value)}/share"
    else:
        display = f"{_decimal_text(value)} {unit}".strip()
    return f"{display} (exact={exact})"


def _financial_period_label(chunk: dict) -> str:
    fiscal_year = chunk.get("fiscal_year")
    fiscal_quarter = chunk.get("fiscal_quarter")
    if fiscal_year and fiscal_quarter:
        label = f"FY{fiscal_year} Q{fiscal_quarter}"
    elif fiscal_year:
        label = f"FY{fiscal_year}"
    else:
        label = "latest snapshot"

    timestamp = chunk.get("period_end") or chunk.get("observed_at")
    return f"{label} (as of {timestamp})" if timestamp else label


def _compact_financial_provenance(chunk: dict) -> dict:
    provenance = chunk.get("provenance") or {}
    if not isinstance(provenance, dict):
        return {}
    return {
        key: provenance[key]
        for key in _FINANCIAL_PROVENANCE_KEYS
        if provenance.get(key) not in (None, [], {})
    }


def _financial_chunk_lines(chunk: dict) -> list[str]:
    provenance = _compact_financial_provenance(chunk)
    return [
        f"ticker={chunk.get('ticker', 'UNKNOWN')}",
        f"metric={chunk.get('metric', 'unknown')}",
        f"period={_financial_period_label(chunk)}",
        f"value={_format_financial_value(chunk)}",
        f"status={chunk.get('status', 'unknown')}",
        f"source_kind={chunk.get('source_kind', 'unknown')}",
        "provenance=" + json.dumps(provenance, ensure_ascii=False),
    ]


def _format_chunks_for_observation(
    chunks: list[dict],
    max_chunks: int = 5,
    max_chars: int = 2000,
) -> str:
    formatted = []
    half = max_chars // 2

    for chunk in chunks[:max_chunks]:
        if _is_structured_financial_chunk(chunk):
            formatted.append("\n".join([
                f"[{chunk.get('chunk_id', 'unknown_chunk')}] FINANCIAL",
                *_financial_chunk_lines(chunk),
            ]))
            continue

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


def _chunk_identity_key(chunk: dict) -> tuple[str, ...]:
    chunk_id = str(chunk.get("chunk_id") or "").strip()
    if chunk_id:
        return ("chunk_id", chunk_id)

    return (
        "fingerprint",
        str(chunk.get("ticker") or ""),
        str(chunk.get("fiscal_year") or ""),
        str(chunk.get("section") or ""),
        str(chunk.get("text") or ""),
    )


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

        key = _chunk_identity_key(chunk)

        if key in seen:
            continue

        seen.add(key)
        deduped.append(chunk)

    return deduped


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _annotate_chunk_for_synthesis(chunk: dict, batch: dict) -> dict:
    annotated = dict(chunk)
    annotated["_retrieval_tool"] = batch.get("tool", "")
    annotated["_retrieval_round"] = batch.get("round")
    annotated["_retrieval_subquery"] = batch.get("subquery", "")
    return annotated


def _strip_internal_chunk_keys(chunk: dict) -> dict:
    return {
        key: value
        for key, value in chunk.items()
        if not str(key).startswith("_")
    }


def _build_retrieval_batches(state: AgentState) -> list[dict]:
    tool_call_log = list(state.get("tool_call_log") or [])
    chunks_history = [
        chunk for chunk in list(state.get("chunks_history") or [])
        if isinstance(chunk, dict)
    ]

    if not tool_call_log:
        if not chunks_history:
            return []
        return [{
            "round": state.get("round", 0),
            "subquery": _get_current_subquery(state),
            "tool": (state.get("next_tool") or {}).get("name", ""),
            "query": "",
            "top_k_chunks": len(chunks_history),
            "n_chunks": len(chunks_history),
            "status": "ok",
            "chunks": chunks_history,
        }]

    batches: list[dict] = []
    cursor = 0

    for entry in tool_call_log:
        batch = dict(entry)
        n_chunks = max(_safe_int(entry.get("n_chunks"), 0), 0)
        batch_chunks: list[dict] = []

        if entry.get("status") == "ok" and n_chunks:
            next_cursor = min(cursor + n_chunks, len(chunks_history))
            batch_chunks = chunks_history[cursor:next_cursor]
            cursor = next_cursor

        batch["chunks"] = batch_chunks
        batches.append(batch)

    if cursor < len(chunks_history):
        batches.append({
            "round": state.get("round", 0),
            "subquery": _get_current_subquery(state),
            "tool": "unknown",
            "query": "",
            "top_k_chunks": len(chunks_history) - cursor,
            "n_chunks": len(chunks_history) - cursor,
            "status": "ok",
            "chunks": chunks_history[cursor:],
        })

    return batches


def _get_preferred_round_for_subquery(
    reflection_history: list[dict],
    subquery: str,
) -> int | None:
    for entry in reversed(reflection_history):
        if entry.get("subquery") != subquery:
            continue
        if entry.get("stop_reason") in {"sufficient", "max_rounds"}:
            return _safe_int(entry.get("round"), 0) - 1

    for entry in reversed(reflection_history):
        if entry.get("subquery") == subquery:
            return _safe_int(entry.get("round"), 0) - 1

    return None


def _select_chunks_for_synthesis(
    state: AgentState,
    max_chunks_per_subquery: int = 3,
    min_total_chunks: int = 8,
) -> list[dict]:
    batches = _build_retrieval_batches(state)
    if not batches:
        return []

    subquery_progress = _collect_subquery_progress(state)
    ordered_subqueries = [
        item.get("subquery", "")
        for item in subquery_progress
        if item.get("subquery")
    ]
    if not ordered_subqueries:
        ordered_subqueries = state.get("subqueries") or [state.get("original_query", "")]

    target_total = max(min_total_chunks, len(ordered_subqueries) * max_chunks_per_subquery)
    reflection_history = list(state.get("reflection_history") or [])
    subquery_order = {
        subquery: idx for idx, subquery in enumerate(ordered_subqueries)
    }
    preferred_rounds = {
        subquery: _get_preferred_round_for_subquery(reflection_history, subquery)
        for subquery in ordered_subqueries
    }

    selected: list[dict] = []
    seen_keys: set[tuple[str, ...]] = set()

    def add_chunk(chunk: dict, batch: dict) -> bool:
        key = _chunk_identity_key(chunk)
        if key in seen_keys:
            return False
        seen_keys.add(key)
        selected.append(_annotate_chunk_for_synthesis(chunk, batch))
        return True

    for subquery in ordered_subqueries:
        candidate_batches = [
            batch for batch in batches
            if batch.get("subquery") == subquery and batch.get("chunks")
        ]
        preferred_round = preferred_rounds.get(subquery)
        candidate_batches.sort(
            key=lambda batch: (
                0 if batch.get("round") == preferred_round else 1,
                -_safe_int(batch.get("round"), -1),
            )
        )

        picked = 0
        for batch in candidate_batches:
            for chunk in batch.get("chunks", []):
                if add_chunk(chunk, batch):
                    picked += 1
                if picked >= max_chunks_per_subquery:
                    break
            if picked >= max_chunks_per_subquery:
                break

    if len(selected) >= target_total:
        return selected[:target_total]

    remaining_batches = sorted(
        [batch for batch in batches if batch.get("chunks")],
        key=lambda batch: (
            0 if batch.get("round") == preferred_rounds.get(batch.get("subquery", "")) else 1,
            subquery_order.get(batch.get("subquery", ""), len(subquery_order)),
            -_safe_int(batch.get("round"), -1),
        ),
    )

    for batch in remaining_batches:
        for chunk in batch.get("chunks", []):
            if add_chunk(chunk, batch) and len(selected) >= target_total:
                return selected

    return selected


def _format_chunks_for_synthesis(
    chunks: list[dict],
    max_chunks: int | None = None,
    max_chars: int = 2000,
) -> tuple[str, dict[int, dict]]:
    formatted: list[str] = []
    citation_lookup: dict[int, dict] = {}
    selected_chunks = chunks if max_chunks is None else chunks[:max_chunks]

    for i, chunk in enumerate(selected_chunks, start=1):
        text = str(chunk.get("text") or "").strip()
        if len(text) > max_chars:
            text = f"{text[:max_chars]}..."

        lines = [f"[{i}] chunk_id={chunk.get('chunk_id', 'UNKNOWN')}"]
        if chunk.get("_retrieval_subquery"):
            lines.append(f"retrieval_subquery={chunk.get('_retrieval_subquery', '')}")
        if chunk.get("_retrieval_tool"):
            lines.append(f"retrieval_tool={chunk.get('_retrieval_tool', '')}")
        if chunk.get("_retrieval_round") is not None:
            lines.append(f"retrieval_round={chunk.get('_retrieval_round')}")
        if _is_structured_financial_chunk(chunk):
            lines.append("evidence_type=financial")
            lines.extend(_financial_chunk_lines(chunk))
        else:
            lines.extend([
                f"ticker={chunk.get('ticker', '')}",
                f"fiscal_year={chunk.get('fiscal_year', '')}",
                f"section={chunk.get('section', '')}",
                f"text={text}",
            ])

        formatted.append("\n".join(lines))
        citation_lookup[i] = _strip_internal_chunk_keys(chunk)

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
