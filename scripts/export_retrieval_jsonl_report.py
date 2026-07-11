from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OBSIDIAN_DIR = Path(
    "/home/kantinan/Documents/Obsidian Vault/Agentic GraphRAG/Evaluation"
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Line {line_no} must be a JSON object")
            rows.append(item)
    return rows


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "-"
    return str(value)


def _clip_list(values: list[Any] | None, limit: int) -> str:
    if not values:
        return "-"
    shown = [f"`{value}`" for value in values[:limit]]
    suffix = f" ... +{len(values) - limit}" if len(values) > limit else ""
    return ", ".join(shown) + suffix


def _tool_names(rows: list[dict[str, Any]]) -> list[str]:
    names: set[str] = set()
    for row in rows:
        tools = row.get("tools", {})
        if isinstance(tools, dict):
            names.update(str(name) for name in tools)
    preferred = ["vector", "graph", "hybrid"]
    return [name for name in preferred if name in names] + sorted(names - set(preferred))


def _metric_average(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _summarize_tools(rows: list[dict[str, Any]], tools: list[str]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for tool in tools:
        metrics: dict[str, list[float]] = defaultdict(list)
        errors = 0
        for row in rows:
            result = (row.get("tools") or {}).get(tool)
            if not isinstance(result, dict):
                continue
            if result.get("error"):
                errors += 1
            for key in (
                "hit_at_k",
                "recall_at_k",
                "mrr_at_k",
                "oracle_hit",
                "oracle_recall",
                "chance_hit_at_k",
                "chance_oracle_hit",
                "latency_sec",
            ):
                value = result.get(key)
                if isinstance(value, (int, float)):
                    metrics[key].append(float(value))
        summary[tool] = {
            "n": len(metrics.get("hit_at_k", [])),
            "errors": errors,
            **{key: _metric_average(values) for key, values in metrics.items()},
        }
    return summary


def _stage_counts(rows: list[dict[str, Any]], tool: str = "graph") -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        result = (row.get("tools") or {}).get(tool)
        if not isinstance(result, dict):
            continue
        label = ((result.get("stage") or {}).get("bottleneck_label") or "unknown")
        counts[str(label)] += 1
    return counts


def _query_result_row(row: dict[str, Any], tools: list[str]) -> str:
    cells = [
        str(row.get("id", "-")),
        str(row.get("type", "-")),
        str(row.get("subset", "-")),
        str(row.get("corpus_status", "-")),
    ]
    for tool in tools:
        result = (row.get("tools") or {}).get(tool) or {}
        if result.get("error"):
            cells.append("error")
            continue
        hit = _fmt(result.get("hit_at_k"))
        recall = _fmt(result.get("recall_at_k"))
        oracle = _fmt(result.get("oracle_hit"))
        cells.append(f"H {hit} / R {recall} / O {oracle}")
    graph_stage = (((row.get("tools") or {}).get("graph") or {}).get("stage") or {})
    cells.append(str(graph_stage.get("bottleneck_label", "-")))
    return "| " + " | ".join(cells) + " |"


def _render_tool_summary(tool_summary: dict[str, dict[str, Any]]) -> list[str]:
    lines = [
        "| Tool | N | Hit@k | Recall@k | MRR@k | OracleHit | OracleRecall | ChanceHit | Latency | Errors |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for tool, stats in tool_summary.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    tool,
                    _fmt(stats.get("n")),
                    _fmt(stats.get("hit_at_k")),
                    _fmt(stats.get("recall_at_k")),
                    _fmt(stats.get("mrr_at_k")),
                    _fmt(stats.get("oracle_hit")),
                    _fmt(stats.get("oracle_recall")),
                    _fmt(stats.get("chance_hit_at_k")),
                    _fmt(stats.get("latency_sec")),
                    _fmt(stats.get("errors")),
                ]
            )
            + " |"
        )
    return lines


def _render_query_detail(row: dict[str, Any], tools: list[str], candidate_limit: int) -> list[str]:
    lines = [
        f"### {row.get('id', '-')}: {row.get('query', '-')}",
        "",
        f"- Type: `{row.get('type', '-')}`",
        f"- Subset: `{row.get('subset', '-')}`",
        f"- Corpus status: `{row.get('corpus_status', '-')}`",
        f"- Gold entities: {_clip_list(row.get('gold_entities') or [], 12)}",
        f"- Missing gold entities: {_clip_list(row.get('missing_gold_entities') or [], 12)}",
        f"- Gold chunks: {_clip_list(row.get('gold_chunks') or [], 12)}",
        f"- Answer points: {_fmt(row.get('answer_points') or [])}",
        "",
        "| Tool | Hit@k | Recall@k | MRR@k | OracleHit | OracleRecall | ChanceHit | Latency | Bottleneck |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for tool in tools:
        result = (row.get("tools") or {}).get(tool)
        if not isinstance(result, dict):
            continue
        stage = result.get("stage") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    tool,
                    _fmt(result.get("hit_at_k")),
                    _fmt(result.get("recall_at_k")),
                    _fmt(result.get("mrr_at_k")),
                    _fmt(result.get("oracle_hit")),
                    _fmt(result.get("oracle_recall")),
                    _fmt(result.get("chance_hit_at_k")),
                    _fmt(result.get("latency_sec")),
                    str(stage.get("bottleneck_label", "-")),
                ]
            )
            + " |"
        )

    lines.append("")
    for tool in tools:
        result = (row.get("tools") or {}).get(tool)
        if not isinstance(result, dict):
            continue
        stage = result.get("stage") or {}
        lines.extend(
            [
                f"#### {tool}",
                "",
                f"- Returned chunks: {_clip_list(result.get('returned_chunk_ids') or [], candidate_limit)}",
                f"- Hits@k: {_clip_list(result.get('hits_at_k') or [], candidate_limit)}",
                f"- Oracle hits: {_clip_list(result.get('oracle_hits') or [], candidate_limit)}",
                f"- Oracle candidates: {_clip_list(result.get('oracle_chunk_ids') or [], candidate_limit)}",
            ]
        )
        if stage:
            lines.extend(
                [
                    f"- Effective query: `{stage.get('effective_query', '-')}`",
                    f"- Seed mode: `{stage.get('seed_mode', '-')}`",
                    f"- Seed hit / PPR hit / Chunk map hit: `{_fmt(stage.get('seed_hit'))}` / `{_fmt(stage.get('ppr_hit'))}` / `{_fmt(stage.get('chunk_map_hit'))}`",
                    f"- Seed names: {_clip_list(stage.get('seed_names') or [], candidate_limit)}",
                    f"- PPR entity names: {_clip_list(stage.get('ppr_entity_names') or [], candidate_limit)}",
                    f"- Chunk candidate ids: {_clip_list(stage.get('chunk_candidate_ids') or [], candidate_limit)}",
                ]
            )
        lines.append("")
    return lines


def _render_report(
    rows: list[dict[str, Any]],
    input_path: Path,
    title: str,
    candidate_limit: int,
) -> str:
    tools = _tool_names(rows)
    tool_summary = _summarize_tools(rows, tools)
    stage_counts = _stage_counts(rows)

    lines = [
        f"# {title}",
        "",
        "[[00_INDEX]]",
        "[[Phase T Quality Tuning Plan]]",
        "",
        "## Metadata",
        "",
        f"- Source JSONL: `{input_path}`",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Queries: `{len(rows)}`",
        f"- Tools: `{', '.join(tools) if tools else '-'}`",
        "",
        "## Overall Metrics",
        "",
        *_render_tool_summary(tool_summary),
        "",
        "## Graph Bottlenecks",
        "",
        "| Bottleneck | Count |",
        "|---|---:|",
    ]

    for label, count in stage_counts.most_common():
        lines.append(f"| {label} | {count} |")

    lines.extend(
        [
            "",
            "## Per-query Snapshot",
            "",
            "| ID | Type | Subset | Corpus | "
            + " | ".join(tools)
            + " | Graph bottleneck |",
            "|---|---|---|---|"
            + "|".join(["---:" for _ in tools])
            + "|---|",
        ]
    )
    lines.extend(_query_result_row(row, tools) for row in rows)

    lines.extend(["", "## Query Details", ""])
    for row in rows:
        lines.extend(_render_query_detail(row, tools, candidate_limit))

    return "\n".join(lines).rstrip() + "\n"


def _default_output_path(input_path: Path, output_dir: Path) -> Path:
    stem = input_path.stem
    if stem.endswith(".jsonl"):
        stem = stem[:-6]
    return output_dir / f"{stem}_obsidian_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export retrieval benchmark JSONL details to an Obsidian Markdown report."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to phase_t_retrieval_details*.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Markdown output path. Defaults to the Obsidian Evaluation folder.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OBSIDIAN_DIR,
        help="Output directory used when --output is not provided.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Report title. Defaults to the input filename.",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=12,
        help="Maximum number of chunk/entity ids shown per list.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input.expanduser().resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    rows = _load_jsonl(input_path)
    title = args.title or f"Retrieval JSONL Report - {input_path.stem}"
    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else _default_output_path(input_path, args.output_dir.expanduser()).resolve()
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _render_report(rows, input_path, title, args.candidate_limit),
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")
    print(f"Queries: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
