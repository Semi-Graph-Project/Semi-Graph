import json
import re
import time
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError
from semigraph.agents.contracts import (
    AssessmentOutput,
    PlanRouteOutput,
    PlannedTask,
    ToolName,
)
from semigraph.agents.prompts import (
    ASSESS_PROMPT,
    SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT,
    build_ontology_planroute_prompt,
)
from semigraph.agents.state import AgentState, TaskWorkerState
from semigraph.agents.tools import RETRIEVERS
from semigraph.config import Config, get_config
from semigraph.connections import get_llm
from semigraph.ontology.schema import RELATIONSHIP_CATALOG



def plan_route_node(
    state: AgentState,
    tool: str,
    cfg: Config | None = None,
) -> dict:
    """Query to Plan
    """

    original_query = state.get("original_query","").strip()
    cfg = cfg or get_config()

    llm = get_llm(cfg)
    system_prompt = build_ontology_planroute_prompt(
        informative_relations=getattr(
            cfg,
            "informative_rel_types",
            RELATIONSHIP_CATALOG.keys(),
        ),
        max_planned_tasks=cfg.agent_max_planned_tasks,
        max_num_ontology=cfg.agent_max_num_ontology,
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
            raise ValueError("Error Provider")

        raw = str(getattr(response, "content", response))
        content = raw.strip()
        content = content[content.find("{") : content.rfind("}") + 1]
        try:
            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValueError("Parsed JSON is not a dictionary.")


        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            raise ValueError(f"Failed to parse and validate plan route response: {e}")
        try:
            plan_route = PlanRouteOutput.model_validate(payload)
        except ValidationError as e:
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
    cfg: Config | None = None,
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

    if selected_tool not in RETRIEVERS:
        raise ValueError("tool must be 'vector' or 'graph'")

    cfg= cfg or get_config()
    chunks = RETRIEVERS[selected_tool](
        query=query,
        top_k_chunks=top_k_chunks,
        cfg=cfg,
    )

    return {
        "chunks": chunks,
        "current_query": query,
        "current_strategy": strategy,
    }


def assess_node(
    state: TaskWorkerState,
    cfg: Config | None = None,
) -> dict:
    """Assess the retrieved chunks for a single Task and return the assessment result."""
    task = PlannedTask.model_validate(state["task"])
    chunks = state["chunks"]
    current_query = state.get("current_query", task.query)
    attempts = state.get("attempts", [])
    accepted_chunks = state.get("accepted_chunks", [])
    cfg = cfg or get_config()
    relation_names = getattr(
        cfg,
        "informative_rel_types",
        RELATIONSHIP_CATALOG,
    )
    allowed_relations = {}
    for relation in relation_names:
        relation = str(relation).lower()
        if relation in RELATIONSHIP_CATALOG:
            allowed_relations[relation] = RELATIONSHIP_CATALOG[relation][
                "description"
            ]
    llm = get_llm(cfg)
    user_prompt = json.dumps({
        "original_query": state["original_query"],
        "requirement": task.requirement,
        "current_query": current_query,
        "current_strategy": state.get("current_strategy"),
        "chunks": chunks,
        "accepted_chunks": accepted_chunks,
        "attempts": attempts,
        "allowed_relations": allowed_relations,
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
        content = str(getattr(response, "content", response)).strip()
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
    cfg: Config | None = None,
) -> dict:
    """Collect accepted chunks and prepare the synthesis input."""
    cfg = cfg or get_config()
    max_chunks = cfg.agent_max_synthesis_chunks
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
                "agent_max_synthesis_chunks must allow one chunk per task"
            )

        selected_chunks = [chunks[0] for chunks in chunks_by_task]
        for chunks in chunks_by_task:
            for chunk in chunks[1:]:
                if len(selected_chunks) >= max_chunks:
                    break
                selected_chunks.append(chunk)
            if len(selected_chunks) >= max_chunks:
                break

    return {
        "synthesis_input": {
            "original_query": state["original_query"],
            "accepted_chunks": selected_chunks,
        }
    }


def synthesize_node(
    state: AgentState,
    cfg: Config | None = None,
) -> dict:
    """Generate the final grounded answer from the collected evidence."""
    started_at = time.perf_counter()
    cfg = cfg or get_config()
    synthesis_input = state["synthesis_input"]
    evidence = [
        {
            "citation": f"[{index}]",
            "chunk": chunk,
        }
        for index, chunk in enumerate(
            synthesis_input["accepted_chunks"],
            start=1,
        )
    ]
    llm = get_llm(cfg)
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
    final_answer = str(getattr(response, "content", response)).strip()
    if not final_answer:
        raise ValueError("Synthesize returned an empty answer")

    return {
        "final_answer": final_answer,
        "synthesis_latency_ms": (time.perf_counter() - started_at) * 1000,
    }
