"""Collect provider-reported LLM tokens within one evaluation query."""

from contextlib import contextmanager
from contextvars import ContextVar
from threading import Lock

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tracers.context import register_configure_hook


TOKEN_FIELDS = ("prompt_tokens", "completion_tokens", "total_tokens")


def _normalize_usage(usage: dict | None) -> dict | None:
    if not isinstance(usage, dict):
        return None
    prompt = usage.get("input_tokens", usage.get("prompt_tokens"))
    completion = usage.get("output_tokens", usage.get("completion_tokens"))
    if not all(type(value) is int and value >= 0 for value in (prompt, completion)):
        return None
    total = usage.get("total_tokens", prompt + completion)
    if type(total) is not int or total < 0:
        return None
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }


def _response_usage(response) -> dict | None:
    """Prefer AIMessage usage; fall back to OpenAI-compatible response metadata."""
    if response.generations and response.generations[0]:
        message = getattr(response.generations[0][0], "message", None)
        usage = _normalize_usage(getattr(message, "usage_metadata", None))
        if usage is not None:
            return usage
        metadata = getattr(message, "response_metadata", {}) or {}
        usage = _normalize_usage(metadata.get("token_usage"))
        if usage is not None:
            return usage
    output = response.llm_output or {}
    return _normalize_usage(output.get("token_usage") or output.get("usage"))


def summarize_token_usage(usages: list[dict]) -> dict:
    """Sum reported tokens and preserve whether any LLM calls lack usage."""
    calls = sum(usage["llm_calls"] for usage in usages)
    reported = sum(usage["calls_with_usage"] for usage in usages)
    if calls == 0:
        status = "no_calls"
    elif reported == 0:
        status = "unavailable"
    elif reported == calls:
        status = "complete"
    else:
        status = "partial"
    return {
        **{
            field: sum(usage[field] or 0 for usage in usages)
            if reported or calls == 0 else None
            for field in TOKEN_FIELDS
        },
        "llm_calls": calls,
        "calls_with_usage": reported,
        "status": status,
    }


class TokenUsageCollector(BaseCallbackHandler):
    """A query-local callback shared safely by parallel LangGraph tasks."""

    def __init__(self):
        super().__init__()
        self._lock = Lock()
        self._calls = 0
        self._reported = 0
        self._tokens = dict.fromkeys(TOKEN_FIELDS, 0)

    def on_chat_model_start(self, serialized, messages, **kwargs):
        with self._lock:
            self._calls += len(messages)

    def on_llm_end(self, response, **kwargs):
        usage = _response_usage(response)
        if usage is not None:
            with self._lock:
                self._reported += 1
                for field in TOKEN_FIELDS:
                    self._tokens[field] += usage[field]

    def snapshot(self) -> dict:
        with self._lock:
            return summarize_token_usage([{
                **self._tokens,
                "llm_calls": self._calls,
                "calls_with_usage": self._reported,
            }])


_collector_var = ContextVar("semigraph_eval_token_usage", default=None)
register_configure_hook(_collector_var, inheritable=True)


@contextmanager
def collect_token_usage():
    """Attach one collector to nested LLM calls without changing their code."""
    collector = TokenUsageCollector()
    token = _collector_var.set(collector)
    try:
        yield collector
    finally:
        _collector_var.reset(token)
