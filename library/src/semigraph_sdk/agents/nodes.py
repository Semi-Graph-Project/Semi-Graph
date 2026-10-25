# Copied from src/semigraph/agents/nodes.py; base SHA256: 94ba59bdd6918c030af8dee57c02f74929c83b74ad3f9bbd58c0ab90e98d236c
import json
import re
import time

from pydantic import ValidationError
from semigraph_sdk.agents.contracts import (
    AssessmentOutput,
    PlanRouteOutput,
    PlannedTask,
    ToolName,
)
from semigraph_sdk.agents.prompts import (
    ASSESS_PROMPT,
    SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT,
    build_planroute_prompt,
)
from semigraph_sdk.agents.state import AgentState, TaskWorkerState
from semigraph_sdk.agents.synthesis import (
    build_synthesis_trace,
    parse_synthesis_response,
)
from semigraph_sdk.agents.runtime import AgentRuntime, response_text



def plan_route_node(
    state: AgentState,
    tool: str,
    runtime: AgentRuntime,
) -> dict:
    """Build a bounded plan using optional corpus relation hints."""
    original_query = state.get("original_query", "").strip()
    cfg = runtime.config

    llm = runtime.llm
    if getattr(cfg, "json_mode", False):
        llm = llm.bind(response_format={"type": "json_object"})
    if not original_query:
        raise ValueError("original_query must not be empty")
    system_prompt = build_planroute_prompt(
        relations=runtime.relations,
        max_planned_tasks=cfg.max_planned_tasks,
        max_num_relations=cfg.max_num_relations,
        tool=tool,
    )

    last_validation_error = ""

    for attempt in range(2):
        user_prompt = (
                f"{original_query}\n\n"
                "The previous response did not match the required schema.\n"
                f"Validation error:\n{last_validation_error}\n"
                "Return corrected JSON only."
            ) if  attempt == 1 else original_query

        try:
            response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            ])
        except Exception as exc:
            raise ValueError("Planning LLM call failed") from exc

        raw = response_text(response)
        content = raw.strip()
        content = content[content.find("{") : content.rfind("}") + 1]
        try:
            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValueError("Parsed JSON is not a dictionary.")
            plan_route = PlanRouteOutput.model_validate(payload)
            if len(plan_route.tasks) > cfg.max_planned_tasks:
                raise ValueError(f"Plan exceeds {cfg.max_planned_tasks} tasks")
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            if attempt == 0:
                last_validation_error = str(e)
                continue
            raise ValueError(
                f"Failed to validate plan route response after retry: {e}"
            ) from e

        return {
            "tasks":[task.model_dump() for task in plan_route.tasks]
        }


def execute_node(
    state: TaskWorkerState,
    tool: ToolName | str,
    top_k_chunks: int,
    runtime: AgentRuntime,
) -> dict:
    """Execute a single Task with the given tool and return the result."""
    task = PlannedTask.model_validate(state["task"])
    selected_tool = ToolName(tool).value
    assessment = state.get("assessment")

    if assessment and not assessment["is_covered"]:
        query = assessment["retry_query"]
        strategy = assessment["retry_strategy"]
    else:
        query = task.query
        strategy = None

    chunks = runtime.retriever(selected_tool)(
        query=query,
        top_k_chunks=top_k_chunks,
    )

    return {
        "chunks": chunks,
        "current_query": query,
        "current_strategy": strategy,
    }


def assess_node(
    state: TaskWorkerState,
    runtime: AgentRuntime,
) -> dict:
    """Assess the retrieved chunks for a single Task and return the assessment result."""
    task = PlannedTask.model_validate(state["task"])
    chunks = state["chunks"]
    current_query = state.get("current_query", task.query)
    attempts = state.get("attempts", [])
    accepted_chunks = state.get("accepted_chunks", [])
    llm = runtime.llm
    user_prompt = json.dumps({
        "original_query": state["original_query"],
        "requirement": task.requirement,
        "current_query": current_query,
        "current_strategy": state.get("current_strategy"),
        "chunks": chunks,
        "accepted_chunks": accepted_chunks,
        "attempts": attempts,
        "observed_relations": dict(runtime.relations),
    }, ensure_ascii=False)
    last_validation_error = ""

    for attempt_number in range(2):
        current_user_prompt = user_prompt
        if attempt_number == 1:
            current_user_prompt += (
                "\n\nThe previous response did not match the required schema.\n"
                f"Validation error:\n{last_validation_error}\n"
                "Return corrected JSON only."
            )

        response = llm.invoke([
            {"role": "system", "content": ASSESS_PROMPT},
            {"role": "user", "content": current_user_prompt},
        ])
        content = response_text(response).strip()
        if content.startswith("```") and content.endswith("```"):
            content = re.sub(
                r"^```(?:json)?\s*",
                "",
                content,
                count=1,
                flags=re.IGNORECASE,
            )
            content = content[:-3].rstrip()
        try:
            assessment = AssessmentOutput.model_validate_json(content)
            break
        except ValidationError as exc:
            if attempt_number == 0:
                last_validation_error = str(exc)
                continue
            raise ValueError(
                "Failed to validate assessment response after retry"
            ) from exc

    evidence = {chunk["chunk_id"]: chunk for chunk in [*accepted_chunks, *chunks]}
    unknown_chunk_ids = set(assessment.accepted_chunk_ids) - set(evidence)
    stop_reason = "unknown_chunk_ids" if unknown_chunk_ids else None

    if stop_reason is None and assessment.retry_query is not None:
        searched_queries = [current_query] + [attempt["query"] for attempt in attempts]
        normalized_queries = [" ".join(query.casefold().split()) for query in searched_queries]
        retry_query = " ".join(assessment.retry_query.casefold().split())
        if retry_query in normalized_queries:
            stop_reason = "repeated_retry_query"

    selected = {chunk["chunk_id"]: chunk for chunk in accepted_chunks}
    for chunk_id in assessment.accepted_chunk_ids:
        if chunk_id in evidence:
            selected[chunk_id] = evidence[chunk_id]
    result = assessment.model_dump()
    attempt = {
        "query": current_query,
        "strategy": state.get("current_strategy"),
        "chunks": chunks,
        "assessment": result,
    }
    output = {
        "assessment": result,
        "attempts": [*attempts, attempt],
        "accepted_chunks": list(selected.values()),
    }
    if stop_reason:
        output["stop_reason"] = stop_reason
    return output


def collector_node(
    state: AgentState,
    runtime: AgentRuntime,
) -> dict:
    """Collect accepted chunks and prepare the synthesis input."""
    cfg = runtime.config
    max_chunks = cfg.max_synthesis_chunks
    worker_results = sorted(
        state.get("worker_results", []),
        key=lambda result: result["task_index"],
    )
    chunks_by_task = [
        result.get("accepted_chunks", [])
        for result in worker_results
        if result.get("accepted_chunks")
    ]
    all_chunks = [chunk for chunks in chunks_by_task for chunk in chunks]

    if len(all_chunks) <= max_chunks:
        selected_chunks = all_chunks
    else:
        if len(chunks_by_task) > max_chunks:
            raise ValueError(
                "max_synthesis_chunks must allow one chunk per task"
            )

        selected_chunks = [chunks[0] for chunks in chunks_by_task]
        for chunks in chunks_by_task:
            for chunk in chunks[1:]:
                if len(selected_chunks) >= max_chunks:
                    break
                selected_chunks.append(chunk)
            if len(selected_chunks) >= max_chunks:
                break

    unique_chunks = {}
    for chunk in selected_chunks:
        unique_chunks.setdefault(chunk["chunk_id"], chunk)
    selected_chunks = list(unique_chunks.values())
    return {
        "synthesis_input": {
            "original_query": state["original_query"],
            "accepted_chunks": selected_chunks,
        }
    }


def synthesize_node(
    state: AgentState,
    runtime: AgentRuntime,
) -> dict:
    """Generate the final grounded answer from the collected evidence."""
    started_at = time.perf_counter()
    cfg = runtime.config
    synthesis_input = state["synthesis_input"]
    evidence = synthesis_input["accepted_chunks"]
    if not evidence:
        return {
            "final_answer": "Do not Answer",
            "synthesis_latency_ms": 0.0,
            "synthesis_trace": {
                "status": "no_evidence", "llm_calls": 0, "selected_chunk_ids": [],
            },
        }
    llm = runtime.llm
    json_mode = getattr(cfg, "json_mode", False)
    if json_mode:
        llm = llm.bind(response_format={"type": "json_object"})
    response = llm.invoke([
        {
            "role": "system",
            "content": SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": json.dumps({
                "original_query": synthesis_input["original_query"],
                "selected_evidence": evidence,
            }, ensure_ascii=False),
        },
    ])
    chunk_ids = [str(chunk["chunk_id"]) for chunk in evidence]
    parsed = parse_synthesis_response(
        response_text(response),
        chunk_ids,
        strict_json=json_mode,
    )
    final_answer = parsed["final_answer"]
    if not final_answer:
        raise ValueError("Synthesize returned an empty answer")

    latency_ms = (time.perf_counter() - started_at) * 1000
    trace = build_synthesis_trace(parsed, chunk_ids)

    return {
        "final_answer": final_answer,
        "synthesis_latency_ms": latency_ms,
        "synthesis_trace": {
            "status": "ok",
            "selected_chunk_ids": chunk_ids,
            "llm_calls": 1,
            "latency_ms": latency_ms,
            **trace,
        },
    }
