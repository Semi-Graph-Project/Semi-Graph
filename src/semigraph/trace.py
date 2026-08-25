"""Small thread-safe JSON trace store used by the comparison demo."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import gettempdir
from threading import Lock
from typing import Any, Callable


TraceCallback = Callable[[dict[str, Any]], None]
TRACE_DIRECTORY = Path(gettempdir()) / "semigraph-traces"


def notify_trace(
    callback: TraceCallback | None,
    event: dict[str, Any],
) -> None:
    """Report progress without allowing trace failures to break retrieval."""
    if callback is None:
        return
    try:
        callback(deepcopy(event))
    except Exception:
        return


class TraceStore:
    """Keep one JSON document per run and persist it atomically in ``/tmp``."""

    def __init__(self, directory: Path = TRACE_DIRECTORY) -> None:
        self.directory = directory
        self._runs: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def start(
        self,
        run_id: str,
        *,
        mode: str,
        query: str,
        corpus: str,
    ) -> None:
        document = {
            "run_id": run_id,
            "mode": mode,
            "query": query,
            "corpus": corpus,
            "status": "running",
            "started_at": _utc_now(),
            "finished_at": None,
            "events": [],
        }
        with self._lock:
            self._runs[run_id] = document
            self._write(document)

    def emit(self, run_id: str, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            document = self._runs[run_id]
            stored_event = {
                "run_id": run_id,
                "seq": len(document["events"]) + 1,
                "timestamp": _utc_now(),
                **deepcopy(event),
            }
            document["events"].append(stored_event)
            self._write(document)
            return deepcopy(stored_event)

    def finish(self, run_id: str, status: str) -> dict[str, Any]:
        with self._lock:
            document = self._runs[run_id]
            document["status"] = status
            document["finished_at"] = _utc_now()
            self._write(document)
            return deepcopy(document)

    def read(self, run_id: str) -> dict[str, Any]:
        """Read the same JSON document consumed by the UI."""
        path = self.path(run_id)
        if path.exists():
            with path.open(encoding="utf-8") as trace_file:
                return json.load(trace_file)
        with self._lock:
            return deepcopy(self._runs.get(run_id, {}))

    def path(self, run_id: str) -> Path:
        return self.directory / f"{run_id}.json"

    def _write(self, document: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.path(str(document["run_id"]))
        temporary = target.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as trace_file:
            json.dump(
                document,
                trace_file,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        temporary.replace(target)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


TRACE_STORE = TraceStore()
