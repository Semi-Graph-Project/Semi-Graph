import json
import re
import time
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError

from semigraph.agent.contracts import (
    AssessmentOutput,
    PlanRouteOutput,
    RetrievalAction,
)
from semigraph.agent.prompts import (
    ASSESS_SYSTEM_PROMPT,
    PLAN_ROUTE_SYSTEM_PROMPT,
    SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT,
)
from semigraph.agent.retry_policy import (
    decide_retry,
    measure_evidence_gain,
    validate_assessment_context,
)
from semigraph.agent.state import AgentState
from semigraph.agent.tools import DEFAULT_TOP_K, RETRIEVERS
from semigraph.config import Config, get_config
from semigraph.connections import get_llm


MAX_PLAN_ROUTE_ATTEMPTS = 2


def _is_transient_retrieval_error(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True

    return type(exc).__name__ in {
        "ServiceUnavailable",
        "SessionExpired",
        "ReadTimeout",
        "ConnectTimeout",
        "TimeoutException",
        "ConnectError",
        "RemoteProtocolError",
    }


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


def _normalize_plan_tasks(
    plan: PlanRouteOutput,
) -> list[dict]:
    """Return bounded, one-requirement Tasks ready for execution."""
    tasks: list[dict] = []

    for planned_task in plan.tasks:
        split_task = len(planned_task.requirements) > 1
        for requirement in planned_task.requirements:
            task_id = f"T{len(tasks) + 1}"
            query = (
                requirement.description if split_task else planned_task.query
            )
            action = planned_task.initial_action.model_dump(mode="json")
            if split_task:
                action["query"] = query

            tasks.append({
                "task_id": task_id,
                "query": query,
                "requirements": [{
                    "requirement_id": f"{task_id}-R1",
                    "description": requirement.description,
                }],
                "initial_action": action,
            })

    return tasks


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
    system_prompt = PLAN_ROUTE_SYSTEM_PROMPT
    locked_tool = state.get("_locked_tool")
    if locked_tool:
        system_prompt += (
            "\n\nEvaluation constraint: every initial_action.tool must be "
            f'"{locked_tool}". Do not select any other Tool.'
        )
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
                {"role": "system", "content": system_prompt},
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
        tasks = _normalize_plan_tasks(plan_route)

        return {
            "tasks": tasks,
            "current_task_index": 0,
            "current_action": tasks[0]["initial_action"],
            "plan_trace": {
                "status": "ok" if attempt_number == 1 else "repaired",
                "validation_mode": "structural_only_v1",
                "normalization": {
                    "input_tasks": len(plan_route.tasks),
                    "input_requirements": sum(
                        len(task.requirements) for task in plan_route.tasks
                    ),
                    "output_tasks": len(tasks),
                },
                "attempts": attempts,
                "warnings": warnings,
                "llm_calls": llm_calls,
                "latency_sec": time.perf_counter() - started_at,
                "fallback_source": None,
            },
        }

    return error_update("validation_failed_after_repair")


def execute_attempt_node(state: AgentState) -> dict:
    """Execute one retrieval action and append one cohesive Attempt."""
    tasks = state.get("tasks") or []
    current_index = state.get("current_task_index")
    attempts = state.get("attempts") or []

    if (
        not isinstance(tasks, list)
        or not isinstance(current_index, int)
        or not 0 <= current_index < len(tasks)
        or not isinstance(attempts, list)
    ):
        return {"current_action": {}, "stop_reason": "unsupported"}

    task = tasks[current_index]
    task_id = task.get("task_id") if isinstance(task, dict) else None
    if not task_id:
        return {"current_action": {}, "stop_reason": "unsupported"}

    try:
        action = RetrievalAction.model_validate(state.get("current_action"))
    except (ValidationError, TypeError, ValueError):
        return {"current_action": {}, "stop_reason": "unsupported"}

    attempt_number = 1 + sum(
        1
        for attempt in attempts
        if isinstance(attempt, dict) and attempt.get("task_id") == task_id
    )

    cfg = get_config()
    retriever = RETRIEVERS[action.tool.value]
    technical_tries = []
    retriever_result = None
    last_error_type = None

    for technical_try in range(1, cfg.agent_max_technical_retries + 2):
        started_at = time.perf_counter()
        try:
            retriever_result = retriever(
                query=action.query,
                top_k_chunks=action.top_k_chunks,
                cfg=cfg,
            )
            technical_tries.append(
                {
                    "technical_try": technical_try,
                    "status": "ok",
                    "latency_sec": round(time.perf_counter() - started_at, 3),
                    "error_type": None,
                }
            )
            break
        except Exception as exc:
            last_error_type = type(exc).__name__
            technical_tries.append(
                {
                    "technical_try": technical_try,
                    "status": "error",
                    "latency_sec": round(time.perf_counter() - started_at, 3),
                    "error_type": type(exc).__name__,
                }
            )
            if not _is_transient_retrieval_error(exc):
                break

    if retriever_result is None:
        retrieval_trace = {
            "status": "terminal",
            "error_type": last_error_type,
            "technical_tries": technical_tries,
        }
        attempt = {
            "attempt_id": f"{task_id}-A{attempt_number}",
            "task_id": task_id,
            "action": action.model_dump(mode="json"),
            "retrieval_status": "tool_error",
            "chunks": [],
            "retrieval_trace": retrieval_trace,
            "assessment": None,
        }
        return _complete_current_task(
            state,
            [*attempts, attempt],
            "tool_error",
        )


    if isinstance(retriever_result, dict):
        raw_chunks = retriever_result.get("chunks") or []
        raw_trace = retriever_result.get("trace")
        retriever_trace = dict(raw_trace) if isinstance(raw_trace, dict) else {}
    elif isinstance(retriever_result, list):
        raw_chunks = retriever_result
        retriever_trace = {}
    else:
        raw_chunks = []
        retriever_trace = {}

    chunks = [item for item in raw_chunks if isinstance(item, dict)]
    retrieval_trace = {
        **retriever_trace,
        "technical_tries": technical_tries,
    }
    attempt = {
        "attempt_id": f"{task_id}-A{attempt_number}",
        "task_id": task_id,
        "action": action.model_dump(mode="json"),
        "retrieval_status": "ok",
        "chunks": chunks,
        "retrieval_trace": retrieval_trace,
        "assessment": None,
    }

    return {
        "attempts": [*attempts, attempt],
        "current_action": action.model_dump(mode="json"),
        "stop_reason": None,
    }


def _select_synthesis_chunks(
    attempts: list[dict],
    max_per_task: int = 3,
    max_total: int = 9,
) -> list[dict]:
    """Return prioritized, unique raw chunks ready for Synthesis."""
    if max_per_task < 1 or max_total < 1:
        raise ValueError("Synthesis chunk limits must be positive")

    attempts_by_task: dict[str, list[dict]] = {}
    for attempt in attempts:
        task_id = attempt.get("task_id")
        if task_id:
            attempts_by_task.setdefault(task_id, []).append(attempt)

    accepted: dict[str, list[dict]] = {}
    fallback: dict[str, list[dict]] = {}

    for task_id, task_attempts in attempts_by_task.items():
        accepted[task_id] = []
        fallback[task_id] = []
        seen_task_ids: set[str] = set()

        for attempt in reversed(task_attempts):
            assessment = attempt.get("assessment") or {}
            if assessment.get("status") not in {"valid", "repaired"}:
                continue
            output = assessment.get("output") or {}
            accepted_ids = set(output.get("accepted_chunk_ids") or [])
            for chunk in attempt.get("chunks") or []:
                chunk_id = chunk.get("chunk_id")
                if chunk_id in accepted_ids and chunk_id not in seen_task_ids:
                    accepted[task_id].append(chunk)
                    seen_task_ids.add(chunk_id)

        # Prefer the first two results from every Attempt, then use remaining
        # ranks only when the global synthesis budget still has room.
        for attempt in reversed(task_attempts):
            for chunk in (attempt.get("chunks") or [])[:2]:
                chunk_id = chunk.get("chunk_id")
                if chunk_id and chunk_id not in seen_task_ids:
                    fallback[task_id].append(chunk)
                    seen_task_ids.add(chunk_id)

        for attempt in reversed(task_attempts):
            for chunk in (attempt.get("chunks") or [])[2:]:
                chunk_id = chunk.get("chunk_id")
                if chunk_id and chunk_id not in seen_task_ids:
                    fallback[task_id].append(chunk)
                    seen_task_ids.add(chunk_id)

    def fair_order(queues: dict[str, list[dict]]) -> list[dict]:
        ordered = [
            chunk
            for task_id in attempts_by_task
            for chunk in queues[task_id][:max_per_task]
        ]
        longest = max((len(queue) for queue in queues.values()), default=0)
        ordered.extend(
            queues[task_id][index]
            for index in range(max_per_task, longest)
            for task_id in attempts_by_task
            if index < len(queues[task_id])
        )
        return ordered

    selected: list[dict] = []
    seen_ids: set[str] = set()
    candidates = [*fair_order(accepted), *fair_order(fallback)]
    for chunk in candidates:
        chunk_id = chunk.get("chunk_id")
        if not chunk_id or chunk_id in seen_ids:
            continue
        selected.append(chunk)
        seen_ids.add(chunk_id)
        if len(selected) == max_total:
            break

    return selected


def synthesize_attempts_node(state: AgentState) -> dict:
    """Synthesize once from evidence selected from the Attempt Ledger."""
    started_at = time.perf_counter()
    attempts = state.get("attempts") or []
    selected_chunks = _select_synthesis_chunks(attempts)
    eligible_ids_by_task: dict[str, set[str]] = {
        task["task_id"]: set()
        for task in (state.get("tasks") or [])
        if isinstance(task, dict) and task.get("task_id")
    }

    for attempt in attempts:
        task_id = attempt.get("task_id")
        if not task_id:
            continue
        eligible_ids = eligible_ids_by_task.setdefault(task_id, set())
        eligible_ids.update(
            chunk["chunk_id"]
            for chunk in (attempt.get("chunks") or [])
            if isinstance(chunk, dict) and chunk.get("chunk_id")
        )

    selected_ids_by_task = {
        task_id: [
            chunk["chunk_id"]
            for chunk in selected_chunks
            if chunk["chunk_id"] in eligible_ids
        ]
        for task_id, eligible_ids in eligible_ids_by_task.items()
    }

    if not selected_chunks:
        return {
            "final_answer": (
                "I do not have enough evidence to answer the question."
            ),
            "citation_map": [],
            "synthesis_trace": {
                "status": "no_evidence",
                "selected_chunk_ids_by_task": selected_ids_by_task,
                "llm_calls": 0,
                "latency_sec": round(time.perf_counter() - started_at, 3),
                "error_type": None,
            },
        }

    evidence_text, citation_lookup = _format_chunks_for_synthesis(
        selected_chunks
    )
    user_message = (
        f"Original Query:\n{state.get('original_query', '')}\n\n"
        f"Tasks:\n{json.dumps(state.get('tasks') or [], ensure_ascii=False)}"
        "\n\n"
        "Task Completions:\n"
        f"{json.dumps(state.get('completed_tasks') or [], ensure_ascii=False)}"
        "\n\n"
        f"Selected Evidence Chunks:\n{evidence_text}"
    )

    try:
        llm = get_llm(get_config())
        response = llm.invoke([
            {
                "role": "system",
                "content": SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT,
            },
            {"role": "user", "content": user_message},
        ])
        raw = response.content if hasattr(response, "content") else str(response)
        answer = _remove_invalid_citations(
            str(raw).strip(),
            set(citation_lookup),
        )
        cited_indices = _extract_citation_indices(answer)
        citation_map = [
            {"citation_index": index, **citation_lookup[index]}
            for index in cited_indices
            if index in citation_lookup
        ]
        status = "ok"
        error_type = None
    except Exception as exc:
        answer = (
            "I could not synthesize a grounded final answer from the "
            "current evidence."
        )
        citation_map = []
        status = "provider_error"
        error_type = type(exc).__name__

    return {
        "final_answer": answer,
        "citation_map": citation_map,
        "synthesis_trace": {
            "status": status,
            "selected_chunk_ids_by_task": selected_ids_by_task,
            "llm_calls": 1,
            "latency_sec": round(time.perf_counter() - started_at, 3),
            "error_type": error_type,
        },
    }


def _chunk_preview(
    chunk: dict,
    text_limit: int | None = None,
) -> dict:
    """Return Assess-facing chunk data without mutating the raw chunk.

    Current evidence uses the full text by leaving ``text_limit`` unset.
    Historical accepted evidence can pass a smaller explicit limit.
    """
    if text_limit is not None and text_limit < 0:
        raise ValueError("text_limit must be non-negative")

    metadata_fields = (
        "chunk_id",
        "rank",
        "original_rank",
        "score",
        "rerank_score",
        "ticker",
        "fiscal_year",
        "fiscal_quarter",
        "period_end",
        "section",
        "metric",
        "value",
        "unit",
        "frequency",
        "source_kind",
        "published_at",
        "source_url",
    )
    preview = {
        field: chunk[field]
        for field in metadata_fields
        if chunk.get(field) is not None
    }
    text = str(chunk.get("text") or "")
    preview["text"] = text if text_limit is None else text[:text_limit]
    return preview


def _compact_assess_diagnostics(trace: dict) -> dict:
    """Keep only retrieval diagnostics that help Assess make a decision."""
    fields = (
        "status",
        "reason",
        "abort_reason",
        "returned_chunk_ids",
        "seed_count",
        "candidate_count",
        "error_type",
    )
    diagnostics = {
        field: trace[field]
        for field in fields
        if trace.get(field) is not None
    }

    seeds = [item for item in trace.get("seeds", []) if isinstance(item, dict)]
    if seeds:
        diagnostics["seeds"] = seeds[:5]

    triple_filter = trace.get("triple_filter")
    if isinstance(triple_filter, dict):
        selected_triples = [
            item
            for item in triple_filter.get("selected_triples", [])
            if isinstance(item, dict)
        ][:5]
        compact_filter = {
            "reason": triple_filter.get("reason"),
            "selected_triples": selected_triples,
        }
        diagnostics["triple_filter"] = {
            field: value
            for field, value in compact_filter.items()
            if value is not None
        }

    return diagnostics


def _build_assess_context(state: AgentState, cfg: Config) -> str:
    """Derive a bounded Assess view from the Attempt Ledger."""
    tasks = state.get("tasks") or []
    current_index = state.get("current_task_index", 0)
    current_task = (
        tasks[current_index]
        if isinstance(current_index, int) and 0 <= current_index < len(tasks)
        else {}
    )
    task_id = (
        current_task.get("task_id")
        if isinstance(current_task, dict)
        else None
    )
    task_attempts = [
        attempt
        for attempt in (state.get("attempts") or [])
        if isinstance(attempt, dict) and attempt.get("task_id") == task_id
    ]
    latest_attempt = task_attempts[-1] if task_attempts else {}
    latest_chunks = [
        _chunk_preview(chunk)
        for chunk in (latest_attempt.get("chunks") or [])
        if isinstance(chunk, dict)
    ]
    accepted_ids: set[str] = set()
    covered_ids: set[str] = set()
    for attempt in task_attempts[:-1]:
        assessment = attempt.get("assessment") or {}
        output = assessment.get("output") or {}
        accepted_ids.update(output.get("accepted_chunk_ids", []))
        covered_ids.update(output.get("covered_requirement_ids", []))
        if assessment.get("status") == "fail_open":
            accepted_ids.update(
                chunk.get("chunk_id")
                for chunk in attempt.get("chunks", [])
                if isinstance(chunk, dict) and chunk.get("chunk_id")
            )

    accepted_evidence = [
        chunk
        for attempt in task_attempts[:-1]
        for chunk in attempt.get("chunks", [])
        if isinstance(chunk, dict) and chunk.get("chunk_id") in accepted_ids
    ][-9:]
    prior_attempts = [
        {
            "attempt_id": attempt.get("attempt_id"),
            "action": attempt.get("action"),
            "retrieval_status": attempt.get("retrieval_status"),
            "accepted_chunk_ids": (
                ((attempt.get("assessment") or {}).get("output") or {}).get(
                    "accepted_chunk_ids", []
                )
            ),
            "returned_chunk_ids": [
                chunk.get("chunk_id")
                for chunk in (attempt.get("chunks") or [])
                if isinstance(chunk, dict) and chunk.get("chunk_id")
            ],
        }
        for attempt in task_attempts[:-1]
    ]

    context = {
        "original_query": state.get("original_query", ""),
        "current_task": current_task,
        "current_action": latest_attempt.get("action")
        or state.get("current_action", {}),
        "latest_chunks": latest_chunks,
        "covered_requirement_ids": sorted(covered_ids),
        "accepted_evidence": [
            _chunk_preview(chunk, text_limit=240)
            for chunk in accepted_evidence
        ],
        "prior_attempts": prior_attempts,
        "latest_diagnostics": _compact_assess_diagnostics(
            latest_attempt.get("retrieval_trace", {})
            if isinstance(latest_attempt.get("retrieval_trace"), dict)
            else {}
        ),
    }

    max_chars = cfg.agent_assess_context_max_chars
    serialized = json.dumps(context, ensure_ascii=False, separators=(",", ":"))

    while len(serialized) > max_chars and context["prior_attempts"]:
        context["prior_attempts"].pop(0)
        serialized = json.dumps(
            context, ensure_ascii=False, separators=(",", ":")
        )

    while len(serialized) > max_chars and context["accepted_evidence"]:
        context["accepted_evidence"].pop(0)
        serialized = json.dumps(
            context, ensure_ascii=False, separators=(",", ":")
        )

    while len(serialized) > max_chars:
        for chunk in reversed(context["latest_chunks"]):
            text = chunk.get("text", "")
            if text:
                excess = len(serialized) - max_chars
                chunk["text"] = text[: max(0, len(text) - max(1, excess))]
                break
        else:
            raise ValueError("Required Assess context exceeds configured limit")
        serialized = json.dumps(
            context, ensure_ascii=False, separators=(",", ":")
        )

    return serialized


def _parse_assessment_response(raw: str) -> AssessmentOutput:
    """Parse one optional JSON fence and validate the Assess contract."""
    if not isinstance(raw, str):
        raise TypeError("Assessment response must be a string")

    content = raw.strip()
    lines = content.splitlines()
    if (
        len(lines) >= 2
        and lines[0].strip().casefold() in {"```", "```json"}
        and lines[-1].strip() == "```"
    ):
        content = "\n".join(lines[1:-1]).strip()

    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise TypeError("Assessment response root must be a JSON object")

    return AssessmentOutput.model_validate(payload)


def _normalize_assessment_error(
    error: Exception | list[dict],
) -> list[dict]:
    """Return repair-safe errors without raw model output."""
    if isinstance(error, list):
        return [dict(item) for item in error]

    if isinstance(error, json.JSONDecodeError):
        return [{"code": "invalid_json"}]

    if isinstance(error, ValidationError):
        return [
            {
                "code": "schema_validation_error",
                "loc": list(item["loc"]),
                "type": item["type"],
            }
            for item in error.errors(
                include_url=False,
                include_context=False,
                include_input=False,
            )
        ]

    if isinstance(error, (TypeError, ValueError)):
        return [{"code": "invalid_assessment_root"}]

    return [
        {
            "code": "assessment_error",
            "type": type(error).__name__,
        }
    ]


def _complete_current_task(
    state: AgentState,
    attempts: list[dict],
    stop_reason: str,
) -> dict:
    """Record one Task outcome and prepare the next Task, if any."""
    tasks = state["tasks"]
    current_index = state["current_task_index"]
    task = tasks[current_index]
    completed_tasks = [
        *(state.get("completed_tasks") or []),
        {
            "task_id": task["task_id"],
            "sufficient": stop_reason == "sufficient",
            "stop_reason": stop_reason,
        },
    ]

    next_index = current_index + 1
    if next_index < len(tasks):
        return {
            "attempts": attempts,
            "completed_tasks": completed_tasks,
            "current_task_index": next_index,
            "current_action": dict(tasks[next_index]["initial_action"]),
            "stop_reason": None,
        }

    return {
        "attempts": attempts,
        "completed_tasks": completed_tasks,
        "current_action": {},
        "stop_reason": stop_reason,
    }


def assess_node(state: AgentState) -> dict:
    """Assess the latest Attempt and let the controller approve any retry."""
    try:
        task = state["tasks"][state["current_task_index"]]
        latest = state["attempts"][-1]
    except (KeyError, IndexError, TypeError):
        return {"current_action": {}, "stop_reason": "assessment_error"}

    if (
        latest.get("task_id") != task.get("task_id")
        or latest.get("retrieval_status") != "ok"
        or latest.get("assessment") is not None
    ):
        return {"current_action": {}, "stop_reason": "assessment_error"}

    cfg = get_config()
    llm = get_llm(cfg)
    locked_tool = state.get("_locked_tool")
    system_prompt = ASSESS_SYSTEM_PROMPT
    if locked_tool:
        system_prompt += (
            "\n\nEvaluation constraint: if decision is retry, next_action.tool "
            f'must remain "{locked_tool}". Tool switching is forbidden.'
        )
    user_message = _build_assess_context(state, cfg)
    llm_calls = 0
    started_at = time.perf_counter()
    error_codes: list[str] = []
    assessment = None
    failure_source = "validation_failed_after_repair"
    current_chunk_ids = {
        chunk["chunk_id"]
        for chunk in (latest.get("chunks") or [])
        if isinstance(chunk, dict) and chunk.get("chunk_id")
    }

    for assessment_try in range(1, cfg.agent_max_assessment_attempts + 1):
        llm_calls += 1
        try:
            response = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ])
        except Exception as exc:
            failure_source = "provider_error"
            error_codes.append(f"provider_error:{type(exc).__name__}")
            break

        raw = str(getattr(response, "content", response))

        try:
            assessment = _parse_assessment_response(raw)
            errors = validate_assessment_context(
                assessment,
                task=task,
                current_chunk_ids=current_chunk_ids,
                locked_tool=locked_tool,
            )
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            errors = _normalize_assessment_error(exc)

        if not errors:
            break

        assessment = None
        error_codes.extend(error.get("code", "assessment_error") for error in errors)
        if assessment_try < cfg.agent_max_assessment_attempts:
            user_message = (
                f"Original Query:\n{state.get('original_query', '')}\n\n"
                f"Current Task:\n{json.dumps(task, ensure_ascii=False)}\n\n"
                f"Previous invalid output:\n{raw}\n\n"
                f"Validation errors:\n{json.dumps(errors, ensure_ascii=False)}\n\n"
                "Return only repaired JSON matching the same schema."
            )

    attempts = list(state["attempts"])
    assessed_attempt = dict(latest)
    trace = {
        "llm_calls": llm_calls,
        "latency_sec": time.perf_counter() - started_at,
        "error_codes": error_codes,
    }

    if assessment is None:
        controller = {
            "decision": "stop",
            "allowed": False,
            "reason": failure_source,
            "stop_reason": "assessment_error",
            "next_action": None,
        }
        assessed_attempt["assessment"] = {
            "status": "fail_open",
            "output": None,
            "controller": controller,
            "trace": trace,
        }
        attempts[-1] = assessed_attempt
        return _complete_current_task(
            state,
            attempts,
            "assessment_error",
        )

    evidence_gain = measure_evidence_gain(assessment, state["attempts"])
    controller = decide_retry(
        assessment,
        state["attempts"],
        evidence_gain,
        cfg.agent_max_attempts_per_task,
    )
    assessed_attempt["assessment"] = {
        "status": "valid" if llm_calls == 1 else "repaired",
        "output": assessment.model_dump(mode="json"),
        "controller": controller,
        "trace": {**trace, "evidence_gain": evidence_gain},
    }
    attempts[-1] = assessed_attempt

    if controller["decision"] == "retry":
        return {
            "attempts": attempts,
            "current_action": controller["next_action"],
            "stop_reason": None,
        }

    stop_reason = (
        "sufficient"
        if controller["decision"] == "accept"
        else controller["stop_reason"] or "unsupported"
    )
    return _complete_current_task(state, attempts, stop_reason)


        


# Helper


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


def _format_chunks_for_synthesis(
    chunks: list[dict],
    max_chunks: int | None = None,
) -> tuple[str, dict[int, dict]]:
    formatted: list[str] = []
    citation_lookup: dict[int, dict] = {}
    selected_chunks = chunks if max_chunks is None else chunks[:max_chunks]

    for i, chunk in enumerate(selected_chunks, start=1):
        text = str(chunk.get("text") or "").strip()

        lines = [f"[{i}] chunk_id={chunk.get('chunk_id', 'UNKNOWN')}"]
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
        citation_lookup[i] = {
            key: value
            for key, value in chunk.items()
            if not str(key).startswith("_")
        }

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


def _workbench() -> None:
    """Show how synthesis-ready chunks are selected from Attempts."""
    first_c1 = {"chunk_id": "C1", "text": "older raw C1 from A1"}
    retry_c1 = {"chunk_id": "C1", "text": "newer raw C1 from A2"}
    retry_c2 = {"chunk_id": "C2", "text": "raw C2 from A2"}
    fallback_c3 = {"chunk_id": "C3", "text": "fail-open raw C3"}
    attempts = [
        {
            "attempt_id": "T1-A1",
            "task_id": "T1",
            "chunks": [first_c1],
            "assessment": {
                "status": "valid",
                "output": {"accepted_chunk_ids": ["C1"]},
            },
        },
        {
            "attempt_id": "T1-A2",
            "task_id": "T1",
            "chunks": [retry_c1, retry_c2],
            "assessment": {
                "status": "repaired",
                "output": {"accepted_chunk_ids": ["C1", "C2"]},
            },
        },
        {
            "attempt_id": "T2-A1",
            "task_id": "T2",
            "chunks": [fallback_c3],
            "assessment": {"status": "fail_open", "output": None},
        },
    ]

    selected = _select_synthesis_chunks(attempts)
    print("Attempts:")
    for attempt in attempts:
        returned = [chunk["chunk_id"] for chunk in attempt["chunks"]]
        output = attempt["assessment"].get("output") or {}
        accepted_ids = output.get("accepted_chunk_ids", [])
        status = attempt["assessment"]["status"]
        print(
            f"  {attempt['attempt_id']}: status={status}, "
            f"returned={returned}, accepted={accepted_ids}"
        )

    print("\nSynthesis-ready raw chunks:")
    print(json.dumps(selected, indent=2, ensure_ascii=False))
    print(f"\nNewer retry C1 preserved: {selected[0] is retry_c1}")


if __name__ == "__main__":
    _workbench()
