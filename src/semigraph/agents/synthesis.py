"""Small helpers shared by Agent and evaluation synthesis."""

import json
import re


DO_NOT_ANSWER = "Do not Answer"


def parse_synthesis_response(response: str, chunk_ids: list[str]) -> dict:
    """Parse structured output and compose every LLM-written part in order."""
    content = response.strip()
    if content.startswith("```") and content.endswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, count=1)
        content = content[:-3].rstrip()

    try:
        payload = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return {
            "final_answer": content,
            "parts": [],
            "output_format": "plain_text" if content else "empty",
        }

    if not isinstance(payload, dict):
        return {"final_answer": "", "parts": [], "output_format": "invalid"}

    parts = payload.get("parts")
    parts = (
        [part for part in parts if isinstance(part, dict)]
        if isinstance(parts, list)
        else []
    )
    part_answers = []
    for part in parts:
        answer = str(part.get("answer") or "").strip()
        if not answer:
            continue

        evidence_ids = list(part.get("evidence_ids") or [])
        for fact in part.get("supported_facts") or []:
            if isinstance(fact, dict):
                evidence_ids.extend(fact.get("evidence_ids") or [])
        for chunk_id in dict.fromkeys(evidence_ids):
            if chunk_id in chunk_ids and f"[{chunk_id}]" not in answer:
                answer += f" [{chunk_id}]"
        part_answers.append(answer)

    final_answer = " ".join(part_answers)
    if not final_answer:
        final_answer = str(payload.get("final_answer") or "").strip()
    return {
        "final_answer": final_answer,
        "parts": parts,
        "output_format": "structured_json",
    }


def build_synthesis_trace(parsed: dict, chunk_ids: list[str]) -> dict:
    """Return compact diagnostics without storing raw model output."""
    answer = parsed["final_answer"]
    bracketed_ids = re.findall(r"\[([^\[\]]+)\]", answer)
    cited_ids = list(dict.fromkeys(
        chunk_id for chunk_id in bracketed_ids if chunk_id in chunk_ids
    ))
    invalid_ids = list(dict.fromkeys(
        chunk_id for chunk_id in bracketed_ids if chunk_id not in chunk_ids
    ))
    if invalid_ids:
        citation_status = "invalid"
    elif answer and answer != DO_NOT_ANSWER and not cited_ids:
        citation_status = "missing"
    else:
        citation_status = "valid" if cited_ids else "not_applicable"

    return {
        "output_format": parsed["output_format"],
        "parts": parsed["parts"],
        "cited_chunk_ids": cited_ids,
        "invalid_citation_ids": invalid_ids,
        "citation_status": citation_status,
    }
