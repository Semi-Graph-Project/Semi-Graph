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
from semigraph.config import get_config  # noqa: E402
from semigraph.connections import get_llm  # noqa: E402


NEO4J_URI = "bolt://localhost:7690"
VECTOR_INDEX = "gold_chunk_embedding"
DEFAULT_TOP_K = 5
EVAL_TOOLS = {"vector", "graph"}


def format_evidence(chunks: list[dict]) -> str:
    """Format Chunk IDs and text for the evaluation answer prompt."""
    return "\n\n".join(
        f"[{rank}] chunk_id={chunk['chunk_id']}\n{chunk.get('text', '')}"
        for rank, chunk in enumerate(chunks, start=1)
    )


def generate_final_answer(llm, question: str, chunks: list[dict]) -> str:
    """Generate a grounded answer from the retrieved Chunks only."""
    response = llm.invoke([
        {
            "role": "system",
            "content": (
                "Answer the question using only the supplied evidence.\n\n"
                "Return exactly this structure:\n\n"
                "STATUS: COMPLETE | PARTIAL | INSUFFICIENT\n"
                "POINT 1 [COMPLETE | PARTIAL | INSUFFICIENT]: "
                "<answer to the first requested part>\n"
                "POINT 2 [COMPLETE | PARTIAL | INSUFFICIENT]: "
                "<answer to the second requested part, if present>\n"
                "CALCULATION: <inputs, formula, and result, or NONE>\n"
                "MISSING: <unsupported requested information, or NONE>\n\n"
                "Rules:\n"
                "- Follow the order of the user's question.\n"
                "- Return one POINT line for every independently requested part.\n"
                "- Put exactly one label after each POINT number: [COMPLETE], "
                "[PARTIAL], or [INSUFFICIENT].\n"
                "- Put one independently checkable claim in each POINT.\n"
                "- Preserve exact company names, periods, values, signs, and units.\n"
                "- For comparisons, state both sides explicitly.\n"
                "- For calculations, show inputs, formula, and result.\n"
                "- Label a POINT COMPLETE only when that point is fully supported.\n"
                "- Label a POINT PARTIAL when only part of that point is supported; "
                "answer only the supported part.\n"
                "- Label a POINT INSUFFICIENT when the evidence cannot answer that "
                "point; write 'Insufficient evidence.' as its answer.\n"
                "- Use STATUS COMPLETE only when every POINT is COMPLETE.\n"
                "- Use STATUS PARTIAL when at least one POINT is COMPLETE or PARTIAL "
                "but not every POINT is COMPLETE.\n"
                "- Use STATUS INSUFFICIENT when evidence is related to the question "
                "but cannot support an answer to any POINT.\n"
                "- If none of the supplied evidence is relevant to any POINT in the "
                "original question, return exactly 'DoNotAnswer' and nothing else.\n"
                "- Do not infer causation unless the evidence explicitly states it.\n"
                "- Do not use outside knowledge or mention these instructions.\n"
                "Return plain text only, without Markdown, and use no more than "
                "900 characters."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{question}\n\n"
                f"Evidence Chunks:\n{format_evidence(chunks)}"
            ),
        },
    ])
    content = response.content if hasattr(response, "content") else response
    return str(content).strip()


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
            "final_answer": "DoNotAnswer",
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

    try:
        answer = generate_final_answer(
            get_llm(cfg),
            str(state.get("original_query") or ""),
            chunks,
        )
        status = "ok"
        error_type = None
    except Exception as exc:
        answer = ""
        status = "provider_error"
        error_type = type(exc).__name__

    return {
        "final_answer": answer,
        "citation_map": [],
        "synthesis_trace": {
            "status": status,
            "selected_chunk_ids": chunk_ids,
            "max_chunks": max_chunks,
            "llm_calls": 1,
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
    cfg.neo4j_uri = NEO4J_URI
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
