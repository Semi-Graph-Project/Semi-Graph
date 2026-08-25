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
from semigraph.agent.ledger import build_assess_context, select_synthesis_chunks
from semigraph.agent.prompts import (
    SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT,
    build_assess_system_prompt,
    build_plan_route_system_prompt,
)
from semigraph.agent.retry_policy import (
    decide_retry,
    measure_evidence_gain,
    validate_assessment_context,
)
from semigraph.agent.state import AgentState, TaskWorkerState
from semigraph.agent.tools import RETRIEVERS
from semigraph.config import Config, get_config
from semigraph.connections import get_llm


MAX_PLAN_ROUTE_ATTEMPTS = 2


# Plan

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


def plan_route_node(
    state: AgentState,
    locked_tool: str | None = None,
    cfg: Config | None = None,
) -> dict:
    started_at = time.perf_counter()
    original_query = state.get("original_query", "")
    attempts: list[dict] = []
    llm_calls = 0

    def error_update(fallback_source: str) -> dict:
        return {
            "tasks": [],
            "stop_reason": "plan_error",
            "plan_trace": {
                "status": "error",
                "validation_mode": "structural_only_v1",
                "attempts": attempts,
                "llm_calls": llm_calls,
                "latency_sec": time.perf_counter() - started_at,
                "fallback_source": fallback_source,
            },
        }

    if not isinstance(original_query, str) or not original_query.strip():
        return error_update("empty_query")

    original_query = original_query.strip()
    cfg = cfg or get_config()
    llm = get_llm(cfg)
    system_prompt = build_plan_route_system_prompt(cfg)
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
        tasks = _normalize_plan_tasks(plan_route)

        return {
            "tasks": tasks,
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
                "llm_calls": llm_calls,
                "latency_sec": time.perf_counter() - started_at,
                "fallback_source": None,
            },
        }

    return error_update("validation_failed_after_repair")


# Execute

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


def execute_attempt_node(
    state: TaskWorkerState,
    cfg: Config | None = None,
) -> dict:
    """Execute one retrieval action and append one cohesive Attempt."""
    task = state["task"]
    attempts = state.get("attempts") or []
    task_id = task["task_id"]

    try:
        action = RetrievalAction.model_validate(state.get("current_action"))
    except (ValidationError, TypeError, ValueError):
        return _complete_task(state, attempts, "unsupported")

    attempt_number = 1 + sum(
        1
        for attempt in attempts
        if isinstance(attempt, dict) and attempt.get("task_id") == task_id
    )

    cfg = cfg or get_config()
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
        return _complete_task(
            state,
            [*attempts, attempt],
            "tool_error",
        )


    raw_chunks = retriever_result["chunks"]
    retriever_trace = retriever_result["trace"]
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


# Assess

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


def _complete_task(
    state: TaskWorkerState,
    attempts: list[dict],
    stop_reason: str,
) -> dict:
    """Record the outcome of the single Task owned by this worker."""
    task = state["task"]
    return {
        "attempts": attempts,
        "completion": {
            "task_id": task["task_id"],
            "sufficient": stop_reason == "sufficient",
            "stop_reason": stop_reason,
        },
        "current_action": {},
        "stop_reason": stop_reason,
    }


def assess_node(
    state: TaskWorkerState,
    locked_tool: str | None = None,
    cfg: Config | None = None,
) -> dict:
    """Assess the latest Attempt and let the controller approve any retry."""
    task = state["task"]
    latest = state["attempts"][-1]

    cfg = cfg or get_config()
    llm = get_llm(cfg)
    system_prompt = build_assess_system_prompt(locked_tool)
    user_message = build_assess_context(state, cfg)
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
        return _complete_task(
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
    return _complete_task(state, attempts, stop_reason)


# Synthesize


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


def synthesize_attempts_node(
    state: AgentState,
    cfg: Config | None = None,
) -> dict:
    """Synthesize once from evidence selected from the Attempt Ledger."""
    started_at = time.perf_counter()
    cfg = cfg or get_config()
    max_chunks = cfg.agent_max_synthesis_chunks
    attempts = state.get("attempts") or []
    selected_chunks = select_synthesis_chunks(
        attempts,
        max_total=max_chunks,
    )
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
                "max_chunks": max_chunks,
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
        llm = get_llm(cfg)
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
            "max_chunks": max_chunks,
            "llm_calls": 1,
            "latency_sec": round(time.perf_counter() - started_at, 3),
            "error_type": error_type,
        },
    }
