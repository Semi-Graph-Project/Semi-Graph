"""Build compact UI trace events from Agent state updates."""

from semigraph.trace import TraceCallback, notify_trace


class AgentTraceEmitter:
    """Emit Agent progress without changing Agent state or control flow."""

    def __init__(self, callback: TraceCallback | None) -> None:
        self._callback = callback

    def _emit(
        self,
        stage: str,
        status: str,
        message: str,
        *,
        task_id: str | None = None,
        attempt_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        event = {"stage": stage, "status": status, "message": message}
        if task_id:
            event["task_id"] = task_id
        if attempt_id:
            event["attempt_id"] = attempt_id
        if details:
            event["details"] = details
        notify_trace(self._callback, event)

    def plan_started(self) -> None:
        self._emit("plan", "running", "Planning retrieval tasks")

    def plan_finished(self, update: dict) -> None:
        tasks = update.get("tasks") or []
        plan_status = (update.get("plan_trace") or {}).get("status")
        self._emit(
            "plan",
            "error" if plan_status == "error" else "complete",
            f"Created {len(tasks)} retrieval task(s)",
            details={
                "task_count": len(tasks),
                "tasks": [
                    f"{task.get('task_id')}: {task.get('query')}"
                    for task in tasks
                ],
            },
        )

    def execute_started(self, state: dict) -> None:
        task_id = state["task"]["task_id"]
        action = state["current_action"]
        attempt_id = f"{task_id}-A{len(state.get('attempts') or []) + 1}"
        self._emit(
            "execute",
            "running",
            f"{attempt_id} searching with {action.get('tool')}",
            task_id=task_id,
            attempt_id=attempt_id,
            details={"tool": action.get("tool"), "query": action.get("query")},
        )

    def execute_finished(self, update: dict) -> None:
        attempt = update["attempts"][-1]
        action = attempt.get("action") or {}
        chunks = attempt.get("chunks") or []
        attempt_id = attempt["attempt_id"]
        self._emit(
            "execute",
            "complete" if attempt.get("retrieval_status") == "ok" else "error",
            f"{attempt_id} retrieved {len(chunks)} evidence chunk(s)",
            task_id=attempt["task_id"],
            attempt_id=attempt_id,
            details={
                "tool": action.get("tool"),
                "query": action.get("query"),
                "chunk_count": len(chunks),
                "chunk_ids": [
                    chunk.get("chunk_id")
                    for chunk in chunks
                    if chunk.get("chunk_id")
                ],
            },
        )

    def assess_started(self, state: dict) -> None:
        latest = state["attempts"][-1]
        self._emit(
            "assess",
            "running",
            f"Assessing evidence for {latest['attempt_id']}",
            task_id=latest["task_id"],
            attempt_id=latest["attempt_id"],
        )

    def assess_finished(self, task: dict, update: dict) -> None:
        attempt = update["attempts"][-1]
        assessment = attempt.get("assessment") or {}
        output = assessment.get("output") or {}
        controller = assessment.get("controller") or {}
        covered = set(output.get("covered_requirement_ids") or [])
        missing = [
            (
                f"{requirement.get('requirement_id')}: "
                f"{requirement.get('description')}"
            )
            for requirement in task.get("requirements", [])
            if requirement.get("requirement_id") not in covered
        ]
        decision = controller.get("decision") or "stop"
        attempt_id = attempt["attempt_id"]
        task_id = attempt["task_id"]
        self._emit(
            "assess",
            "error" if assessment.get("status") == "fail_open" else "complete",
            {
                "accept": f"{attempt_id} has sufficient evidence",
                "retry": f"{attempt_id} needs more evidence",
                "stop": f"{attempt_id} stopped without sufficient evidence",
            }.get(decision, f"Assessed {attempt_id}"),
            task_id=task_id,
            attempt_id=attempt_id,
            details={
                "accepted_chunk_ids": output.get("accepted_chunk_ids") or [],
                "covered_requirement_ids": sorted(covered),
                "missing_requirements": missing,
                "reason": controller.get("reason"),
            },
        )
        if decision == "retry":
            self._retry(task_id, attempt_id, output, update)

    def _retry(
        self,
        task_id: str,
        attempt_id: str,
        assessment_output: dict,
        update: dict,
    ) -> None:
        next_action = update.get("current_action") or {}
        self._emit(
            "retry",
            "complete",
            f"Rewrote {task_id} query: {next_action.get('query')}",
            task_id=task_id,
            attempt_id=attempt_id,
            details={
                "strategy": assessment_output.get("retry_strategy"),
                "tool": next_action.get("tool"),
                "retry_query": next_action.get("query"),
            },
        )

    def task_finished(
        self,
        task: dict,
        result: dict,
        completion: dict,
    ) -> None:
        sufficient = completion["sufficient"]
        stop_reason = completion["stop_reason"]
        status = (
            "complete"
            if sufficient
            else "error"
            if stop_reason in {"tool_error", "assessment_error"}
            else "insufficient"
        )
        self._emit(
            "task_result",
            status,
            (
                f"{task['task_id']} has sufficient evidence"
                if sufficient
                else f"{task['task_id']} ended with insufficient evidence"
            ),
            task_id=task["task_id"],
            details={
                "task_query": task.get("query"),
                "attempt_count": len(result.get("attempts") or []),
                "sufficient": sufficient,
                "stop_reason": stop_reason,
            },
        )

    def synthesis_started(self) -> None:
        self._emit("synthesis", "running", "Synthesizing the final answer")

    def synthesis_finished(self, update: dict) -> None:
        trace = update.get("synthesis_trace") or {}
        selected_by_task = trace.get("selected_chunk_ids_by_task") or {}
        selected_count = sum(len(ids) for ids in selected_by_task.values())
        self._emit(
            "synthesis",
            trace.get("status") or "complete",
            f"Synthesized from {selected_count} selected evidence chunk(s)",
            details={
                "selected_evidence_count": selected_count,
                "citation_count": len(update.get("citation_map") or []),
            },
        )
