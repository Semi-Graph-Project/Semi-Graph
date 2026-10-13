"""Run the real comparison UI with predictable results for browser tests."""

import json
import os
import runpy
import sys
from pathlib import Path
from threading import Lock
from time import sleep

from semigraph import demo
from semigraph.demo import ComparisonResult
from semigraph.trace import TRACE_STORE


ROOT = Path(__file__).resolve().parents[2]
CALL_LOG = Path(os.environ["SEMIGRAPH_E2E_CALL_LOG"])
CALL_LOCK = Lock()


def fake_run_comparison(mode, query, corpus, run_id, **_kwargs):
    """Return four independent results without touching Neo4j or an LLM."""
    corpus_key = demo.get_backend_corpus(corpus).key
    with CALL_LOCK:
        with CALL_LOG.open("a", encoding="utf-8") as log:
            log.write(json.dumps({"mode": mode, "query": query, "corpus": corpus_key}) + "\n")

    TRACE_STORE.start(run_id, mode=mode, query=query, corpus=corpus_key)
    TRACE_STORE.emit(run_id, {
        "stage": "retrieval",
        "status": "complete",
        "retriever": mode,
        "message": f"{mode} retrieved test evidence",
    })
    sleep(0.2)

    if query.startswith("ERROR CASE") and mode == "graph":
        status, answer, error = "error", "", "Test retrieval error"
    elif query.startswith("TIMEOUT CASE") and mode == "graph":
        status, answer, error = "timeout", "", "Test run timed out"
    else:
        status = "complete"
        answer = f"{mode} answer for {query}. [1]"
        error = None

    TRACE_STORE.emit(run_id, {
        "stage": "synthesis",
        "status": status,
        "message": f"{mode} finished",
    })
    trace = TRACE_STORE.finish(run_id, status)["events"]
    return ComparisonResult(
        status=status,
        answer=answer,
        citations=[{
            "citation_index": 1,
            "chunk_id": "NVDA_10k_2024.pdf::page_1::chunk_1",
            "source_file": "NVDA_10k_2024.pdf",
        }] if status == "complete" else [],
        synthesis_chunks=[
            {
                "chunk_id": "NVDA_10k_2024.pdf::page_1::chunk_1",
                "text": "## NVIDIA products\n---\nNVIDIA makes GPUs <not HTML>.",
            },
            {
                "chunk_id": "NVDA_10k_2024.pdf::page_2::chunk_1",
                "text": "Uncited evidence about another topic.",
            },
        ] if status == "complete" else [],
        trace=trace,
        latency_sec=0.2,
        error=error,
    )


demo.run_comparison = fake_run_comparison
sys.path.insert(0, str(ROOT / "Demo"))
runpy.run_path(str(ROOT / "Demo" / "comparison_app.py"), run_name="__main__")
