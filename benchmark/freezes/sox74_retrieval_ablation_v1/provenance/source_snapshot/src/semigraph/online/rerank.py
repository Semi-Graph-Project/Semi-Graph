"""Small OpenRouter reranker client used by retrieval experiments."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from semigraph.config import Config, get_config


def _post_rerank(payload: dict[str, Any], cfg: Config) -> dict[str, Any]:
    """Send one rerank request and return the decoded JSON response."""
    if not cfg.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    request = Request(
        f"{cfg.reranker_base_url.rstrip('/')}/rerank",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {cfg.openrouter_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=cfg.reranker_timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _request_with_retry(payload: dict[str, Any], cfg: Config) -> dict[str, Any]:
    """Retry transient HTTP failures, then re-raise the final error."""
    attempts = max(0, int(cfg.reranker_max_retries)) + 1

    for attempt in range(attempts):
        try:
            return _post_rerank(payload, cfg)
        except HTTPError as exc:
            if exc.code not in {408, 429, 500, 502, 503, 504} or attempt == attempts - 1:
                raise
        except URLError:
            if attempt == attempts - 1:
                raise

        time.sleep(min(2**attempt, 4))

    raise RuntimeError("Reranker request failed without a response")


def _original_order(chunks: list[dict], top_n: int) -> list[dict]:
    """Return copies so fallback never mutates retrieval results."""
    return [dict(chunk) for chunk in chunks[:top_n]]


def rerank_chunks(
    query: str,
    chunks: list[dict],
    top_n: int,
    cfg: Config | None = None,
    fail_open: bool = True,
) -> tuple[list[dict], dict]:
    """Rerank chunks with OpenRouter and return ranked chunks plus trace.

    When ``fail_open`` is true, an API/config/network failure returns the
    original retrieval order instead of breaking the retrieval pipeline.
    """
    if not query.strip() or not chunks or top_n <= 0:
        return [], {"status": "skipped"}

    cfg = cfg or get_config()
    top_n = min(top_n, len(chunks))
    
    payload = {
        "model": cfg.reranker_model,
        "query": query,
        "documents": [chunk.get("text", "") for chunk in chunks],
        "top_n": top_n,
    }

    try:
        response = _request_with_retry(payload, cfg)
        results = response.get("results", [])
        ranked = []
        for result in results:
            index = result.get("index")
            if not isinstance(index, int) or not 0 <= index < len(chunks):
                continue
            item = dict(chunks[index])
            item["original_rank"] = index + 1
            item["rerank_score"] = float(result.get("relevance_score", 0.0))
            ranked.append(item)

        if not ranked:
            raise RuntimeError("Reranker returned no valid results")

        return ranked[:top_n], {
            "status": "ok",
            "provider": cfg.reranker_provider,
            "model": response.get("model", cfg.reranker_model),
            "candidate_count": len(chunks),
            "returned_count": len(ranked[:top_n]),
            "usage": response.get("usage", {}),
        }
    except Exception as exc:
        if not fail_open:
            raise
        return _original_order(chunks, top_n), {
            "status": "fallback",
            "provider": cfg.reranker_provider,
            "model": cfg.reranker_model,
            "candidate_count": len(chunks),
            "returned_count": top_n,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
