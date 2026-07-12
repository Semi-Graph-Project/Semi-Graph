"""LLM recognition filtering for query-to-triple candidates."""
from __future__ import annotations

import json
import time
from typing import Optional

from semigraph.config import Config, get_config
from semigraph.connections import get_llm
from semigraph.online.seed import TripleCandidate


MAX_SELECTED_TRIPLES = 5
MAX_FILTER_ATTEMPTS = 2

TRIPLE_FILTER_SYSTEM_PROMPT = """
You filter retrieved knowledge-graph triples for graph search.

Select at most 5 candidate triples that are directly relevant or useful as
bridges for answering the query. Multi-hop bridge triples are allowed.

Return JSON only:
{"selected_candidate_ids": [0, 2]}

Rules:
- Select only IDs present in the candidate list.
- Do not create or rewrite triples.
- Return an empty list when none are relevant.
""".strip()


def _format_candidates(query: str, candidates: list[TripleCandidate]) -> str:
    rows = [
        {
            "candidate_id": candidate["candidate_id"],
            "triple": [
                candidate["head"],
                candidate["relation"],
                candidate["tail"],
            ],
            "similarity": round(candidate["similarity"], 4),
        }
        for candidate in candidates
    ]
    return json.dumps(
        {"query": query, "candidates": rows},
        ensure_ascii=False,
    )


def _parse_selected_ids(
    raw: str,
    valid_ids: set[int],
) -> list[int]:
    """
        Parsed to ID List + Validate the raw from LLM
    """
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("filter response must be a JSON object")

    selected_ids = payload.get("selected_candidate_ids")
    if not isinstance(selected_ids, list):
        raise ValueError("selected_candidate_ids must be a list")

    valid_selected_ids = [
        candidate_id
        for candidate_id in selected_ids
        if type(candidate_id) is int and candidate_id in valid_ids
    ]
    if selected_ids and not valid_selected_ids:
        raise ValueError("response contains no valid candidate IDs")
    return valid_selected_ids


def _build_trace(
    candidates: list[TripleCandidate],
    selected: list[TripleCandidate],
    started: float,
    *,
    attempts: int,
    fallback: bool,
    reason: str,
    parse_error: str | None = None,
) -> dict:
    selected_ids = [candidate["candidate_id"] for candidate in selected]
    candidate_ids = [candidate["candidate_id"] for candidate in candidates]
    return {
        "candidates_before_filter": candidates,
        "candidates_after_filter": selected,
        "rejected_candidate_ids": [
            candidate_id
            for candidate_id in candidate_ids
            if candidate_id not in selected_ids
        ],
        "selected_candidate_ids": selected_ids,
        "filter_latency_sec": round(time.perf_counter() - started, 3),
        "attempts": attempts,
        "parse_error": parse_error,
        "fallback": fallback,
        "reason": reason,
    }


def filter_triple_candidates(
    query: str,
    candidates: list[TripleCandidate],
    max_selected: int = MAX_SELECTED_TRIPLES,
    cfg: Optional[Config] = None,
) -> tuple[list[TripleCandidate], dict]:
    """Filter retrieved triples and return selected candidates plus trace.

    The LLM can only select existing candidate IDs. Invalid responses are
    retried once, then the highest-ranked embedding candidates are returned
    as a deterministic fallback. An explicit empty selection also falls back
    to the embedding ranking so production retrieval does not silently lose
    all seeds.

    Return : List of Selected Triple Candidates, Trace
    """
    if max_selected <= 0:
        raise ValueError("max_selected must be positive")

    limit = min(max_selected, MAX_SELECTED_TRIPLES)
    started = time.perf_counter()
    if not candidates:
        return [], _build_trace(
            candidates,
            [],
            started,
            attempts=0,
            fallback=False,
            reason="no_candidates",
        )

    valid_ids = {candidate["candidate_id"] for candidate in candidates}
    messages = [
        {"role": "system", "content": TRIPLE_FILTER_SYSTEM_PROMPT},
        {"role": "user", "content": _format_candidates(query, candidates)},
    ]
    last_error: str | None = None

    for attempt in range(1, MAX_FILTER_ATTEMPTS + 1):
        try:
            llm = get_llm(cfg or get_config())
            response = llm.invoke(messages)
            raw = response.content if hasattr(response, "content") else str(response)
            selected_ids = _parse_selected_ids(raw, valid_ids)

            if not selected_ids:
                selected = candidates[:limit]
                return selected, _build_trace(
                    candidates,
                    selected,
                    started,
                    attempts=attempt,
                    fallback=True,
                    reason="empty_selection",
                )

            selected_set = set(selected_ids[:limit])
            selected = [
                candidate
                for candidate in candidates
                if candidate["candidate_id"] in selected_set
            ]
            return selected, _build_trace(
                candidates,
                selected,
                started,
                attempts=attempt,
                fallback=False,
                reason="llm_selection",
            )
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"

    selected = candidates[:limit]
    return selected, _build_trace(
        candidates,
        selected,
        started,
        attempts=MAX_FILTER_ATTEMPTS,
        fallback=True,
        reason="llm_error",
        parse_error=last_error,
    )
