from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.agent.graph import build_agent


_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}
_NODE_COLORS = {
    "plan": "blue",
    "tool_select": "cyan",
    "execute": "yellow",
    "observe": "magenta",
    "reflect": "red",
    "advance_subquery": "green",
    "synthesize": "white",
}


def _use_color() -> bool:
    return sys.stdout.isatty() and not any(
        flag in sys.argv for flag in ("--no-color",)
    ) and "NO_COLOR" not in __import__("os").environ


def c_print(text: str, *, color: str | None = None, bold: bool = False, dim: bool = False, end: str = "\n") -> None:
    if _use_color() and (color or bold or dim):
        prefix = ""
        if bold:
            prefix += _BOLD
        if dim:
            prefix += _DIM
        if color:
            prefix += _COLORS.get(color, "")
        print(f"{prefix}{text}{_RESET}", end=end)
    else:
        print(text, end=end)


def _node_color(node_name: str) -> str:
    return _NODE_COLORS.get(node_name, "green")


def _compact_text(value: object, limit: int = 220) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _summarize_update(update: dict) -> str:
    if "subqueries" in update:
        return f"subqueries={update['subqueries']}"
    if "next_tool" in update:
        return f"next_tool={update['next_tool']}"
    if "latest_chunks" in update:
        log = (update.get("tool_call_log") or [{}])[-1]
        return (
            f"tool={log.get('tool')} status={log.get('status')} "
            f"n_chunks={len(update.get('latest_chunks') or [])} "
            f"query={log.get('query')!r}"
        )
    if "observation_text" in update:
        return f"observation={_compact_text(update.get('observation_text'))}"
    if "sufficient" in update:
        return (
            f"sufficient={update.get('sufficient')} "
            f"stop_reason={update.get('stop_reason')} "
            f"retry_query={update.get('retry_query')!r}"
        )
    if "completed_subqueries" in update and "final_answer" not in update:
        return f"completed_subqueries={update['completed_subqueries']}"
    if "final_answer" in update:
        return (
            f"final_answer={_compact_text(update.get('final_answer'))} "
            f"citations={len(update.get('citation_map') or [])}"
        )
    return _compact_text(update)


def _summarize_citation_map(citations: list[dict]) -> list[dict]:
    compact = []
    for item in citations:
        text = str(item.get("text") or "").replace("\n", " ")
        compact.append(
            {
                "citation_index": item.get("citation_index"),
                "chunk_id": item.get("chunk_id"),
                "ticker": item.get("ticker"),
                "fiscal_year": item.get("fiscal_year"),
                "section": item.get("section"),
                "score": item.get("score"),
                "preview": text[:240],
            }
        )
    return compact


def _print_json(label: str, value: object) -> None:
    c_print(f"{label}:", color="cyan", bold=True)
    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the SemiGraph agent end-to-end with a real query and print trace."
    )
    parser.add_argument("query", help="Sample query to run through the agent")
    parser.add_argument(
        "--recursion-limit",
        type=int,
        default=50,
        help="LangGraph recursion limit for the trace run",
    )
    parser.add_argument(
        "--show-final-state",
        action="store_true",
        help="Print the final state as JSON",
    )
    parser.add_argument(
        "--show-citations",
        action="store_true",
        help="Print a compact citation map after the run",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in trace output",
    )
    args = parser.parse_args()

    graph = build_agent()
    c_print("QUERY:", color="cyan", bold=True, end=" ")
    c_print(args.query, color="white")
    c_print("RECURSION_LIMIT:", color="cyan", bold=True, end=" ")
    c_print(str(args.recursion_limit), color="white")

    started = time.time()
    final_state: dict | None = None

    try:
        for event in graph.stream(
            {"original_query": args.query},
            stream_mode="updates",
            config={"recursion_limit": args.recursion_limit},
        ):
            for node_name, update in event.items():
                final_state = update
                elapsed = time.time() - started
                c_print(f"[{elapsed:7.2f}s]", color="magenta", dim=True, end=" ")
                c_print(f"{node_name}:", color=_node_color(node_name), bold=True, end=" ")
                c_print(_summarize_update(update), color="white")
                print("\n\n--------------------------------")
    except Exception as exc:
        elapsed = time.time() - started
        c_print(
            f"ERROR after {elapsed:.2f}s: {type(exc).__name__}: {exc}",
            color="red",
            bold=True,
        )
        raise

    elapsed = time.time() - started
    c_print(f"--- completed in {elapsed:.2f}s ---", color="cyan", bold=True)

    if not final_state:
        return

    if "final_answer" in final_state:
        c_print("\nFINAL_ANSWER:", color="yellow", bold=True)
        c_print(final_state.get("final_answer", ""), color="white")

    if args.show_citations:
        c_print("\nCITATION_MAP:", color="yellow", bold=True)
        c_print(
            json.dumps(
                _summarize_citation_map(final_state.get("citation_map", [])),
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            color="white",
        )

    if args.show_final_state:
        _print_json("\nFINAL_STATE", final_state)

        c_print(f"\n\n Answer : {final_state.get('final_answer')}", color="green",bold=True)
        # c_print("\n\n Answer : ", color="green",bold=True)
        



if __name__ == "__main__":
    main()
