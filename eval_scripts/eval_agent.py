"""Evaluation-only Vector and Graph Agents."""

from __future__ import annotations

import re
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
from semigraph.config import get_config  # noqa: E402
from semigraph.connections import get_llm  # noqa: E402


VECTOR_INDEX = "gold_chunk_embedding"
DEFAULT_TOP_K = 5
EVAL_TOOLS = {"vector", "graph"}
DO_NOT_ANSWER = "Do not Answer"
GENERATION_ERROR_ANSWER = "Can't Generate Answer"

HUMAN_REVIEW_SYNTHESIS_PROMPT = """
Answer the question using only the supplied evidence chunks.

Return one line for each independently requested part, in the same order as the
question, using exactly this format:
POINT 1 [COMPLETE | PARTIAL | INSUFFICIENT]: <answer>
POINT 2 [COMPLETE | PARTIAL | INSUFFICIENT]: <answer>
Choose exactly one status inside each pair of brackets and continue numbering
POINT 3, POINT 4, and so on only when the question has more requested parts.

Point rules:
- Put only one independently checkable answer in each POINT.
- When comparing named entities, give each entity's facts in a separate POINT,
  then put the requested comparison or implication in the next POINT.
- Keep a financial metric separate from a governance, audit, or regulatory role.
- Keep calculation inputs, formula, and result together in one POINT.
- Use COMPLETE only when every detail requested by that POINT is supported.
- Use PARTIAL when only part is supported; answer that part and state the missing detail.
- Use INSUFFICIENT when no supplied evidence answers that POINT; write only
  "Insufficient evidence."

Evidence rules:
- Cite every supported claim with its exact chunk_id in square brackets, for
  example [INTC_10k_2024.pdf::page_71::chunk_1].
- Never cite a chunk_id that was not supplied.
- Preserve exact company names, periods, values, signs, and units.
- For comparisons, state both sides explicitly.
- For calculations, use only numeric inputs explicitly present in the evidence,
  show the formula and result, and do not round intermediate values.
- For percentages, state the denominator and formula.
- Do not infer causation unless the evidence explicitly states it.
- Do not use outside knowledge or mention these instructions.

If no supplied chunk is relevant to any requested part, return exactly
"Do not Answer" and nothing else.
Otherwise return only the POINT lines, without a heading, Markdown, blank lines,
or an overall status. Use no more than 1,500 characters.
""".strip()

HUMAN_REVIEW_AUDIT_PROMPT = f"""
Act as the final evidence auditor. Rewrite the complete final answer after
checking the original question, every supplied evidence chunk, and the draft.

Audit rules:
- Derive all requested parts again from the original question; do not assume
  the draft found every part.
- Check every evidence chunk against every requested part.
- Add any omitted supported part and split combined parts when needed.
- Keep correct supported content, but correct wrong companies, periods, values,
  signs, units, calculations, statuses, and citations.
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


def _has_answer_format(answer: str) -> bool:
    return bool(answer) and (
        answer == DO_NOT_ANSWER
        or bool(
            re.search(
                r"^POINT \d+ \[(?:COMPLETE|PARTIAL|INSUFFICIENT)\]:",
                answer,
                re.MULTILINE,
            )
        )
    )


def generate_final_answer(llm, question: str, chunks: list[dict]) -> str:
    """Draft an answer, then audit it against every retrieved Chunk."""
    if not chunks:
        return DO_NOT_ANSWER

    evidence_input = (
        f"Question:\n{question}\n\n"
        f"Evidence Chunks:\n{format_evidence(chunks)}"
    )

    try:
        draft = _invoke_answer(
            llm,
            HUMAN_REVIEW_SYNTHESIS_PROMPT,
            evidence_input,
        )
    except Exception:
        draft = ""

    audit_input = (
        f"{evidence_input}\n\n"
        f"Draft Answer:\n{draft or 'Draft unavailable. Build the answer directly.'}"
    )
    try:
        final_answer = _invoke_answer(
            llm,
            HUMAN_REVIEW_AUDIT_PROMPT,
            audit_input,
        )
    except Exception:
        final_answer = ""

    if _has_answer_format(final_answer):
        return final_answer
    if _has_answer_format(draft):
        return draft
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
                "latency_sec": round(time.perf_counter() - started_at, 3),
                "error_type": None,
            },
        }

    llm_calls = 0
    try:
        answer = generate_final_answer(
            get_llm(cfg),
            str(state.get("original_query") or ""),
            chunks,
        )
        llm_calls = 2
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
            "latency_sec": round(time.perf_counter() - started_at, 3),
            "error_type": error_type,
        },
    }


def _build_eval_graph(
    locked_tool: str,
    top_k: int,
    generate_answer: bool,
):
    """Build the shared Production-shaped evaluation Agent graph."""
    if locked_tool not in EVAL_TOOLS:
        raise ValueError(f"Unsupported evaluation tool: {locked_tool}")
    if top_k < 1:
        raise ValueError("top_k must be positive")

    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri
    if locked_tool == "vector":
        cfg.agent_retrieval["vector"]["vector_index"] = VECTOR_INDEX
    else:
        cfg.agent_retrieval["graph"]["chunk_seed_vector_index"] = VECTOR_INDEX

    def eval_synthesize(state: AgentState) -> dict:
        return eval_synthesize_node(state, generate_answer=generate_answer)

    return build_agent(
        locked_tool=locked_tool,
        top_k=top_k,
        synthesis=eval_synthesize,
    )


def build_vector_eval_graph(
    top_k: int = DEFAULT_TOP_K,
    generate_answer: bool = True,
):
    return _build_eval_graph("vector", top_k, generate_answer)


def build_graph_eval_graph(
    top_k: int = DEFAULT_TOP_K,
    generate_answer: bool = True,
):
    return _build_eval_graph("graph", top_k, generate_answer)


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

    graph = build_graph_eval_graph(top_k=10)
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
