from __future__ import annotations

import argparse
import json
import os
import sys
import time

from semigraph.agent.graph import build_agent


QUERIES = [
    (
        "filing_strategy",
        "How does NVIDIA describe the role of accelerated computing and AI "
        "in its business strategy?",
    ),
    (
        "graph_supply_risk",
        "How could AMD's dependence on TSMC create supply-chain exposure for "
        "AMD's data-center products?",
    ),
    (
        "recent_business_event",
        "What recent semiconductor news could affect ASML's business, and why "
        "might it matter to the company?",
    ),
]

RESET = "\033[0m"
BOLD = "\033[1m"
COLORS = {
    "query": "\033[96m",
    "plan_route": "\033[94m",
    "task_worker": "\033[93m",
    "collector": "\033[35m",
    "execute": "\033[93m",
    "assess": "\033[95m",
    "synthesize": "\033[92m",
    "error": "\033[91m",
    "dim": "\033[90m",
}


def _paint(text: str, color: str, enabled: bool, *, bold: bool = False) -> str:
    if not enabled:
        return text
    prefix = COLORS.get(color, COLORS["dim"])
    if bold:
        prefix = BOLD + prefix
    return f"{prefix}{text}{RESET}"


def _print_json(label: str, value: object, color: str, enabled: bool) -> None:
    print(_paint(label, color, enabled, bold=True))
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def _chunk_previews(chunks: list[dict]) -> list[dict]:
    return [
        {
            "chunk_id": chunk.get("chunk_id"),
            "ticker": chunk.get("ticker"),
            "section": chunk.get("section"),
            "score": chunk.get("score"),
            "text": str(chunk.get("text") or "").replace("\n", " ")[:180],
        }
        for chunk in chunks
    ]


def _citation_previews(citations: list[dict]) -> list[dict]:
    return [
        {
            "citation_index": item.get("citation_index"),
            "chunk_id": item.get("chunk_id"),
            "ticker": item.get("ticker"),
            "section": item.get("section"),
            "text": str(item.get("text") or "").replace("\n", " ")[:180],
        }
        for item in citations
    ]


def _print_node_trace(node_name: str, update: dict, color: bool) -> None:
    update = update or {}

    if node_name == "plan_route":
        _print_json(
            "PLAN",
            {
                "tasks": update.get("tasks", []),
                "current_action": update.get("current_action", {}),
                "plan_trace": update.get("plan_trace", {}),
            },
            node_name,
            color,
        )
        return

    if node_name == "task_worker":
        results = update.get("task_results") or []
        _print_json(
            "TASK WORKER RESULT",
            [
                {
                    "task_id": result.get("task_id"),
                    "attempts": [
                        {
                            "attempt_id": attempt.get("attempt_id"),
                            "tool": (attempt.get("action") or {}).get("tool"),
                            "retrieval_status": attempt.get("retrieval_status"),
                            "chunk_ids": [
                                chunk.get("chunk_id")
                                for chunk in (attempt.get("chunks") or [])
                                if isinstance(chunk, dict)
                            ],
                            "assessment_status": (
                                attempt.get("assessment") or {}
                            ).get("status"),
                        }
                        for attempt in (result.get("attempts") or [])
                    ],
                    "completion": result.get("completion"),
                }
                for result in results
            ],
            node_name,
            color,
        )
        return

    if node_name == "collector":
        _print_json(
            "COLLECTED STATE",
            {
                "attempt_order": [
                    attempt.get("attempt_id")
                    for attempt in (update.get("attempts") or [])
                ],
                "completed_tasks": update.get("completed_tasks") or [],
                "stop_reason": update.get("stop_reason"),
            },
            node_name,
            color,
        )
        return

    attempts = update.get("attempts") or []
    latest = attempts[-1] if attempts else {}

    if node_name == "execute":
        _print_json(
            "RETRIEVAL ATTEMPT",
            {
                "attempt_id": latest.get("attempt_id"),
                "action": latest.get("action"),
                "retrieval_status": latest.get("retrieval_status"),
                "chunks": _chunk_previews(latest.get("chunks") or []),
                "retrieval_trace": latest.get("retrieval_trace", {}),
            },
            node_name,
            color,
        )
        return

    if node_name == "assess":
        _print_json(
            "ASSESSMENT",
            {
                "attempt_id": latest.get("attempt_id"),
                "assessment": latest.get("assessment"),
                "next_action": update.get("current_action", {}),
                "completion": update.get("completion"),
                "stop_reason": update.get("stop_reason"),
            },
            node_name,
            color,
        )
        return

    if node_name == "synthesize":
        print(_paint("FINAL ANSWER", node_name, color, bold=True))
        print(update.get("final_answer", ""))
        _print_json(
            "CITATIONS",
            _citation_previews(update.get("citation_map") or []),
            node_name,
            color,
        )
        _print_json(
            "SYNTHESIS TRACE",
            update.get("synthesis_trace", {}),
            node_name,
            color,
        )


def _run_query(
    graph,
    label: str,
    query: str,
    recursion_limit: int,
    color: bool,
) -> bool:
    print("\n" + "=" * 88)
    print(_paint(f"SMOKE CASE: {label}", "query", color, bold=True))
    print(_paint(f"QUERY: {query}", "query", color))
    print("=" * 88)

    started = time.perf_counter()
    try:
        for event in graph.stream(
            {"original_query": query},
            stream_mode="updates",
            config={"recursion_limit": recursion_limit},
        ):
            for node_name, update in event.items():
                elapsed = time.perf_counter() - started
                header = f"[{elapsed:7.2f}s] {node_name.upper()}"
                print("\n" + _paint(header, node_name, color, bold=True))
                _print_node_trace(node_name, update, color)
    except Exception as exc:
        elapsed = time.perf_counter() - started
        message = f"FAILED after {elapsed:.2f}s: {type(exc).__name__}: {exc}"
        print(_paint(message, "error", color, bold=True))
        return False

    elapsed = time.perf_counter() - started
    print(_paint(f"COMPLETED in {elapsed:.2f}s", "query", color, bold=True))
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run three real narrative queries through the Full Agent.",
    )
    parser.add_argument("--recursion-limit", type=int, default=50)
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    if args.recursion_limit < 1:
        parser.error("--recursion-limit must be positive")

    color = (
        sys.stdout.isatty()
        and not args.no_color
        and "NO_COLOR" not in os.environ
    )
    graph = build_agent()
    results = [
        _run_query(graph, label, query, args.recursion_limit, color)
        for label, query in QUERIES
    ]

    passed = sum(results)
    print("\n" + "=" * 88)
    summary_color = "synthesize" if passed == len(results) else "error"
    print(
        _paint(
            f"SMOKE SUMMARY: {passed}/{len(results)} completed",
            summary_color,
            color,
            bold=True,
        )
    )
    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
