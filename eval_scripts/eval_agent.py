"""Evaluation-only Vector and Graph Agents."""

from __future__ import annotations

import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.agent.graph import build_agent  # noqa: E402
from semigraph.agent.ledger import select_synthesis_chunks  # noqa: E402
from semigraph.agent.state import AgentState  # noqa: E402
from semigraph.agents.prompts import SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT  # noqa: E402
from semigraph.agents.synthesis import (  # noqa: E402
    build_synthesis_trace,
    parse_synthesis_response,
)
from semigraph.config import get_config  # noqa: E402
from semigraph.connections import get_llm  # noqa: E402


VECTOR_INDEX = "gold_chunk_embedding"
EVAL_TOOLS = {"vector", "graph"}
DO_NOT_ANSWER = "Do not Answer"
GENERATION_ERROR_ANSWER = "Can't Generate Answer"

HUMAN_REVIEW_SYNTHESIS_PROMPT = SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT.strip()

HUMAN_REVIEW_AUDIT_PROMPT = f"""
Act as the final evidence auditor. Rewrite the complete final answer after
checking the original question, every supplied evidence chunk, and the draft.

Audit rules:
- Derive all requested parts again from the original question; do not assume
  the draft found every part.
- Check every evidence chunk against every requested part.
- Add any omitted supported part and organize the answer in question order.
- Keep correct supported content, but correct wrong companies, periods, values,
  signs, units, calculations, and citations.
- Check that each inference follows from the cited evidence without missing
  premises or outside knowledge. Keep justified inferences, qualify uncertain
  conclusions, and remove unsupported explanations or causal claims.
- Recalculate numeric answers from the explicit inputs in the chunks and show
  the formula briefly. Never invent a missing input.
- When multiple chunks support the same answer, cite all of them.
- Return the whole revised answer, not comments about the draft.

Final answer rules:
{HUMAN_REVIEW_SYNTHESIS_PROMPT}
""".strip()


def format_evidence(chunks: list[dict]) -> str:
    """Format Chunk IDs and text for the evaluation answer prompt."""
    return "\n\n".join(
        f"chunk_id={chunk['chunk_id']}\n{chunk.get('text', '')}"
        for chunk in chunks
    )


def _invoke_answer(llm, system_prompt: str, user_prompt: str) -> str:
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])
    content = response.content if hasattr(response, "content") else response
    return str(content).strip()


def _parse_synthesis_response(
    response: str,
    chunks: list[dict] | None = None,
) -> dict:
    """Parse the response using the shared Agent synthesis contract."""
    chunk_ids = [
        str(chunk["chunk_id"])
        for chunk in (chunks or [])
        if chunk.get("chunk_id")
    ]
    return parse_synthesis_response(response, chunk_ids)


def _final_answer_from_response(response: str) -> str:
    """Extract the user-facing answer from the structured LLM response."""
    return _parse_synthesis_response(response)["final_answer"]


def _update_synthesis_trace(
    trace: dict | None,
    parsed: dict,
    chunks: list[dict],
) -> None:
    """Store compact part and citation diagnostics for later inspection."""
    if trace is None:
        return

    chunk_ids = [
        str(chunk["chunk_id"])
        for chunk in chunks
        if chunk.get("chunk_id")
    ]
    trace.update(build_synthesis_trace(parsed, chunk_ids))


def generate_final_answer(
    llm,
    question: str,
    chunks: list[dict],
    *,
    audit_enabled: bool | None = None,
    synthesis_trace: dict | None = None,
) -> str:
    """Draft an answer; optionally audit it using the evaluation config."""
    if not chunks:
        _update_synthesis_trace(
            synthesis_trace,
            {
                "final_answer": DO_NOT_ANSWER,
                "parts": [],
                "output_format": "no_evidence",
            },
            chunks,
        )
        return DO_NOT_ANSWER
    if audit_enabled is None:
        audit_enabled = get_config().eval_answer_audit_enabled

    evidence_input = (
        f"Question:\n{question}\n\n"
        f"Evidence Chunks:\n{format_evidence(chunks)}"
    )

    try:
        draft_response = _invoke_answer(
            llm,
            HUMAN_REVIEW_SYNTHESIS_PROMPT,
            evidence_input,
        )
    except Exception:
        draft_response = ""

    draft_payload = _parse_synthesis_response(draft_response, chunks)
    draft = draft_payload["final_answer"]

    if not audit_enabled:
        _update_synthesis_trace(synthesis_trace, draft_payload, chunks)
        return draft or GENERATION_ERROR_ANSWER

    audit_input = (
        f"{evidence_input}\n\n"
        f"Draft Answer:\n{draft_response or 'Draft unavailable. Build the answer directly.'}"
    )
    try:
        audit_response = _invoke_answer(
            llm,
            HUMAN_REVIEW_AUDIT_PROMPT,
            audit_input,
        )
    except Exception:
        audit_response = ""

    audit_payload = _parse_synthesis_response(audit_response, chunks)
    final_answer = audit_payload["final_answer"]

    if final_answer:
        _update_synthesis_trace(synthesis_trace, audit_payload, chunks)
        return final_answer
    if draft:
        _update_synthesis_trace(synthesis_trace, draft_payload, chunks)
        return draft
    _update_synthesis_trace(synthesis_trace, audit_payload, chunks)
    return GENERATION_ERROR_ANSWER


def eval_synthesize_node(
    state: AgentState,
    generate_answer: bool = True,
) -> dict:
    """Create the evaluation answer from Assess-selected evidence only."""
    started_at = time.perf_counter()
    cfg = get_config()
    max_chunks = cfg.agent_max_synthesis_chunks
    attempts = state.get("attempts") or []
    chunks = select_synthesis_chunks(attempts, max_total=max_chunks)
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]

    if not chunks:
        return {
            "final_answer": DO_NOT_ANSWER,
            "citation_map": [],
            "synthesis_trace": {
                "status": "no_evidence",
                "selected_chunk_ids": [],
                "max_chunks": max_chunks,
                "llm_calls": 0,
                "answer_audit_enabled": False,
                "latency_sec": round(time.perf_counter() - started_at, 3),
                "error_type": None,
            },
        }

    if not generate_answer:
        return {
            "final_answer": "",
            "citation_map": [],
            "synthesis_trace": {
                "status": "retrieve_only",
                "selected_chunk_ids": chunk_ids,
                "max_chunks": max_chunks,
                "llm_calls": 0,
                "answer_audit_enabled": False,
                "latency_sec": round(time.perf_counter() - started_at, 3),
                "error_type": None,
            },
        }

    llm_calls = 0
    audit_enabled = cfg.eval_answer_audit_enabled
    answer_trace = {}
    try:
        answer = generate_final_answer(
            get_llm(cfg),
            str(state.get("original_query") or ""),
            chunks,
            audit_enabled=audit_enabled,
            synthesis_trace=answer_trace,
        )
        llm_calls = 2 if audit_enabled else 1
        failed = answer == GENERATION_ERROR_ANSWER
        status = "generation_error" if failed else "ok"
        error_type = "AnswerGenerationError" if failed else None
    except Exception as exc:
        answer = GENERATION_ERROR_ANSWER
        status = "provider_error"
        error_type = type(exc).__name__

    return {
        "final_answer": answer,
        "citation_map": [],
        "synthesis_trace": {
            "status": status,
            "selected_chunk_ids": chunk_ids,
            "max_chunks": max_chunks,
            "llm_calls": llm_calls,
            "answer_audit_enabled": audit_enabled,
            "latency_sec": round(time.perf_counter() - started_at, 3),
            "error_type": error_type,
            **answer_trace,
        },
    }


def _build_eval_graph(
    tool: str,
    generate_answer: bool,
):
    """Build the shared Production-shaped evaluation Agent graph."""
    if tool not in EVAL_TOOLS:
        raise ValueError(f"Unsupported evaluation tool: {tool}")

    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri
    if tool == "vector":
        cfg.agent_retrieval["vector"]["vector_index"] = VECTOR_INDEX
    else:
        cfg.agent_retrieval["graph"]["chunk_seed_vector_index"] = VECTOR_INDEX

    def eval_synthesize(state: AgentState) -> dict:
        return eval_synthesize_node(state, generate_answer=generate_answer)

    return build_agent(
        tool=tool,
        synthesis=eval_synthesize,
        cfg=cfg,
    )


def build_vector_eval_graph(
    generate_answer: bool = True,
):
    return _build_eval_graph("vector", generate_answer)


def build_graph_eval_graph(
    generate_answer: bool = True,
):
    return _build_eval_graph("graph", generate_answer)


SMOKE_QUERY = (
    "What percentage of Texas Instruments' 2022 total revenue was represented "
    "by restructuring charges disclosed in the Other segment, and how does "
    "the company's segment reporting structure explain the separation of these "
    "charges from operating segments like Embedded Processing?"
)


def _run_smoke_test() -> None:
    """Run one real Vector Agent query against Neo4j 7690 and the LLM."""
    print("=== Vector Agent Eval Smoke Test ===")
    print(f"Query: {SMOKE_QUERY}")

    graph = build_graph_eval_graph()
    result = graph.invoke({"original_query": SMOKE_QUERY})

    print("\n=== Final Answer ===")
    print(result.get("final_answer", ""))

    print("\n=== Attempts ===")
    for attempt in result.get("attempts") or []:
        action = attempt.get("action") or {}
        chunk_ids = [
            chunk.get("chunk_id")
            for chunk in (attempt.get("chunks") or [])
            if chunk.get("chunk_id")
        ]
        assessment = attempt.get("assessment") or {}
        print(
            f"{attempt.get('attempt_id')} | "
            f"tool={action.get('tool')} | "
            f"retrieval={attempt.get('retrieval_status')} | "
            f"chunks={chunk_ids} | "
            f"assessment={assessment.get('status')}"
        )

    trace = result.get("synthesis_trace") or {}
    print("\n=== Eval Synthesis Trace ===")
    print(f"status={trace.get('status')}")
    print(f"selected_chunk_ids={trace.get('selected_chunk_ids', [])}")
    print(f"latency_sec={trace.get('latency_sec')}")


if __name__ == "__main__":
    _run_smoke_test()
