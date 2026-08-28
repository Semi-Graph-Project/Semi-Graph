"""Run PlanRoute only against SOX questions and extra Graph probes."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from semigraph.agent import nodes as agent_nodes  # noqa: E402
from semigraph.agent.prompts import build_plan_route_system_prompt  # noqa: E402
from semigraph.config import get_config  # noqa: E402


DEFAULT_DATASET = ROOT / "benchmark" / "datasets" / "finreflectkg_sox_strict74.yaml"
SOX_GRAPH_QUERY_IDS = ("FRKG082", "FRKG177", "FRKG276")
EXTRA_QUERIES = [
    (
        "EXTRA_GRAPH_CHAIN",
        "How could TSMC capacity constraints affect AMD's data-center products, "
        "and which company does AMD depend on for manufacturing?",
    ),
    (
        "EXTRA_GRAPH_FACTS",
        "Which companies supply NVIDIA with components, and which business "
        "segments does NVIDIA have a stake in?",
    ),
    (
        "EXTRA_GRAPH_FINANCIAL",
        "How does AMD's dependence on TSMC connect to the products AMD produces, "
        "and what was AMD's FY2024 revenue?",
    ),
]

RESET = "\033[0m"
BOLD = "\033[1m"
COLORS = {
    "query": "\033[96m",
    "task": "\033[94m",
    "action": "\033[93m",
    "info": "\033[90m",
    "ok": "\033[92m",
    "error": "\033[91m",
}
ONTOLOGY_PROMPT_BUILDER = agent_nodes.build_ontology_planroute_prompt


def paint(text: object, color: str, enabled: bool, *, bold: bool = False) -> str:
    if not enabled:
        return str(text)
    prefix = (BOLD if bold else "") + COLORS[color]
    return f"{prefix}{text}{RESET}"


def load_queries(path: Path, count: int | None = None) -> list[dict]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    queries = payload.get("queries") or []
    if not isinstance(queries, list) or not queries:
        raise ValueError(f"No queries found in {path}")
    selected = queries if count is None else queries[:count]
    return [item for item in selected if isinstance(item, dict)]


def configure_prompt(prompt_name: str) -> None:
    """Select the PlanRoute prompt for this smoke test only."""
    if prompt_name == "ontology":
        agent_nodes.build_ontology_planroute_prompt = ONTOLOGY_PROMPT_BUILDER
        return

    def legacy_prompt(*_args: object, **_kwargs: object) -> str:
        return build_plan_route_system_prompt(get_config())

    agent_nodes.build_ontology_planroute_prompt = legacy_prompt


def print_plan(result: dict, color: bool) -> None:
    trace = result.get("plan_trace") or {}
    print(paint(f"STATUS: {trace.get('status', 'unknown')}", "ok", color, bold=True))
    print(paint(f"LLM calls: {trace.get('llm_calls', 0)}", "info", color))
    print(paint(f"Latency: {trace.get('latency_sec', 0):.2f}s", "info", color))
    tasks = result.get("tasks") or []
    if not tasks:
        print(paint("No tasks returned", "error", color, bold=True))
        print(paint(f"Fallback: {trace.get('fallback_source')}", "error", color))
        return

    for task in tasks:
        action = task.get("initial_action") or {}
        print(
            paint(
                f"{task.get('task_id', '?')} | tool={action.get('tool')}",
                "task",
                color,
                bold=True,
            )
        )
        print(f"  Task:   {task.get('query', '')}")
        print(f"  Action: {action.get('query', '')}")
        print(f"  top_k:  {action.get('top_k_chunks')}")
        for requirement in task.get("requirements") or []:
            print(f"  Need:   {requirement.get('requirement_id')} — {requirement.get('description')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test PlanRoute with real benchmark queries")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument(
        "--prompt",
        choices=("ontology", "legacy"),
        default="ontology",
        help="PlanRoute prompt to use (default: ontology)",
    )
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be positive")

    color = not args.no_color
    configure_prompt(args.prompt)
    print(paint(f"Prompt: {args.prompt}", "info", color, bold=True))
    all_queries = load_queries(args.dataset)
    cases = [
        (item.get("id", f"Q{index}"), str(item.get("query") or "").strip())
        for index, item in enumerate(all_queries[:args.count], start=1)
    ]
    queries_by_id = {item.get("id"): item for item in all_queries}
    missing_ids = [query_id for query_id in SOX_GRAPH_QUERY_IDS if query_id not in queries_by_id]
    if missing_ids:
        raise ValueError(f"SOX query IDs not found: {', '.join(missing_ids)}")
    cases.extend(
        (query_id, str(queries_by_id[query_id].get("query") or "").strip())
        for query_id in SOX_GRAPH_QUERY_IDS
    )
    cases.extend(EXTRA_QUERIES)

    for index, (query_id, query) in enumerate(cases, start=1):
        print("\n" + paint(f"QUERY {index}: {query_id}", "query", color, bold=True))
        print(query)

        started_at = time.perf_counter()
        try:
            result = agent_nodes.plan_route_node(
                {"original_query": query},
                locked_tool="graph",
            )
        except Exception as exc:
            print(paint(f"ERROR: {type(exc).__name__}: {exc}", "error", color, bold=True))
            continue

        print_plan(result, color)
        print(paint(f"Finished in {time.perf_counter() - started_at:.2f}s", "info", color))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
