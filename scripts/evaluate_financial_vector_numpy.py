"""Evaluate plain NumPy vector retrieval over PostgreSQL financial facts.

This is an evaluation-only baseline. It does not change the production Agent,
Neo4j indexes, or PostgreSQL schema. The script performs four steps:

1. Export every in-scope curated financial row as one text fact document.
2. Embed the corpus and benchmark questions with the project embedding model.
3. Rank documents by NumPy dot product (cosine on normalized embeddings).
4. Compare vector retrieval with benchmark gold rows and a saved SQL run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import statistics
import time
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from semigraph.config import get_config
from semigraph.financial.db import financial_connection
from semigraph.offline.embeddings import get_embedding_model


DEFAULT_BENCHMARK = Path("benchmark/datasets/financial_agent_e2e_60.yaml")
DEFAULT_CORPUS = Path("benchmark/datasets/financial_vector_facts.jsonl")
DEFAULT_CACHE = Path("benchmark/cache/financial_vector_facts_embeddings.npz")
DEFAULT_RESULTS_ROOT = Path("benchmark/results/financial_vector_numpy")
SQL_RESULTS_ROOT = Path("benchmark/results/financial_agent_e2e")

CSV_FIELDS = (
    "id",
    "category",
    "expected_outcome",
    "query",
    "gold_count",
    "retrieved_gold_count",
    "recall_at_k",
    "complete_evidence",
    "precision_at_k",
    "constraint_precision_at_k",
    "first_gold_rank",
    "latency_ms",
    "retrieved_evidence_ids",
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _fact_text(fact: dict[str, Any]) -> str:
    """Render one structured row as a neutral, human-readable fact card."""

    metric_label = fact["metric"].replace("_", " ")
    if fact["frequency"] == "annual":
        period = f"fiscal year FY{fact['fiscal_year']}"
    elif fact["frequency"] == "quarterly":
        period = (
            f"fiscal quarter Q{fact['fiscal_quarter']} "
            f"of FY{fact['fiscal_year']}"
        )
    else:
        period = "latest market snapshot"

    observed = fact.get("period_end") or fact.get("observed_at")
    return (
        f"{fact['ticker']} financial fact. "
        f"Metric: {metric_label} ({fact['metric']}). "
        f"Period: {period}. Date: {observed}. "
        f"Value: {fact['value']} {fact['unit']}. "
        f"Frequency: {fact['frequency']}. "
        f"Source kind: {fact['source_kind']}."
    )


def _periodic_facts(conn: Any, tickers: list[str]) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT evidence_id, ticker, frequency, fiscal_year, fiscal_quarter,
               period_end, NULL::timestamptz AS observed_at, metric, value,
               unit, source_kind, status, provenance
        FROM financial.agent_periodic_metrics
        WHERE ticker = ANY(%s)
          AND status = 'ok'
          AND value IS NOT NULL
        ORDER BY ticker, frequency, fiscal_year, fiscal_quarter,
                 metric, evidence_id
        """,
        (tickers,),
    ).fetchall()
    return [dict(row) for row in rows]


def _snapshot_facts(conn: Any, tickers: list[str]) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT evidence_id, ticker, 'snapshot'::text AS frequency,
               NULL::integer AS fiscal_year,
               NULL::smallint AS fiscal_quarter,
               NULL::date AS period_end, observed_at, metric, value, unit,
               source_kind, 'ok'::text AS status, provenance
        FROM financial.agent_market_metrics
        WHERE ticker = ANY(%s)
          AND value IS NOT NULL
        ORDER BY ticker, metric, evidence_id
        """,
        (tickers,),
    ).fetchall()
    return [dict(row) for row in rows]


def build_corpus(path: Path) -> list[dict[str, Any]]:
    """Export all Agent-visible financial rows to a deterministic JSONL file."""

    tickers = list(get_config().tickers)
    with financial_connection(readonly=True) as conn:
        rows = _periodic_facts(conn, tickers) + _snapshot_facts(conn, tickers)

    facts: list[dict[str, Any]] = []
    seen_document_ids: set[str] = set()
    for row in rows:
        fact = _json_safe(row)
        evidence_id = str(fact["evidence_id"])
        fact["evidence_id"] = evidence_id
        document_id = ":".join(
            (evidence_id, fact["frequency"], fact["metric"])
        )
        if document_id in seen_document_ids:
            raise ValueError(f"Duplicate document_id in vector corpus: {document_id}")
        seen_document_ids.add(document_id)
        fact["document_id"] = document_id
        fact["text"] = _fact_text(fact)
        facts.append(fact)

    content = "".join(
        json.dumps(fact, ensure_ascii=False, sort_keys=True) + "\n"
        for fact in facts
    )
    _write_atomic(path, content)
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_views": [
            "financial.agent_periodic_metrics",
            "financial.agent_market_metrics",
        ],
        "ticker_scope": tickers,
        "document_count": len(facts),
        "corpus_sha256": _corpus_hash(path),
        "frequency_counts": dict(Counter(fact["frequency"] for fact in facts)),
        "source_kind_counts": dict(Counter(fact["source_kind"] for fact in facts)),
        "metric_counts": dict(Counter(fact["metric"] for fact in facts)),
        "document_contract": "one curated database row per fact document",
    }
    _write_atomic(
        path.with_suffix(".meta.json"),
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
    )
    return facts


def load_corpus(path: Path) -> list[dict[str, Any]]:
    facts = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not facts:
        raise ValueError(f"Vector corpus is empty: {path}")
    return facts


def _corpus_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_or_build_embeddings(
    facts: list[dict[str, Any]],
    corpus_path: Path,
    cache_path: Path,
    *,
    rebuild: bool,
) -> np.ndarray:
    """Return normalized corpus embeddings, reusing a validated cache."""

    cfg = get_config()
    digest = _corpus_hash(corpus_path)
    if cache_path.exists() and not rebuild:
        with np.load(cache_path, allow_pickle=False) as cached:
            cached_hash = str(cached["corpus_hash"].item())
            cached_model = str(cached["model"].item())
            embeddings = cached["embeddings"].astype(np.float32)
        if (
            cached_hash == digest
            and cached_model == cfg.embed_model
            and embeddings.shape[0] == len(facts)
        ):
            return embeddings

    model = get_embedding_model()
    embeddings = model.encode([fact["text"] for fact in facts])
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = cache_path.with_suffix(cache_path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle,
            embeddings=embeddings,
            corpus_hash=np.array(digest),
            model=np.array(cfg.embed_model),
        )
    temporary.replace(cache_path)
    return embeddings


def load_benchmark(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cases = list(data.get("queries") or [])
    if not cases:
        raise ValueError(f"No benchmark cases found: {path}")
    return dict(data.get("metadata") or {}), cases


def _top_k(scores: np.ndarray, k: int) -> np.ndarray:
    """Return deterministic descending score indices."""

    k = min(k, scores.shape[0])
    return np.argsort(-scores, kind="stable")[:k]


def _matches_constraints(fact: dict[str, Any], spec: dict[str, Any]) -> bool:
    year = fact.get("fiscal_year")
    return (
        fact.get("ticker") in set(spec.get("tickers") or [])
        and fact.get("metric") in set(spec.get("metrics") or [])
        and fact.get("frequency") == spec.get("frequency")
        and (spec.get("start_year") is None or year >= spec["start_year"])
        and (spec.get("end_year") is None or year <= spec["end_year"])
        and (spec.get("quarter") is None or fact.get("fiscal_quarter") == spec["quarter"])
    )


def score_case(
    case: dict[str, Any],
    facts: list[dict[str, Any]],
    scores: np.ndarray,
    *,
    top_k: int,
    latency_ms: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    indices = _top_k(scores, top_k)
    retrieved = [facts[index] for index in indices]
    retrieved_ids = [fact["evidence_id"] for fact in retrieved]
    gold_ids = {
        str(row["evidence_id"])
        for row in (case.get("gold_rows") or [])
    }
    matched_ids = gold_ids & set(retrieved_ids)
    gold_count = len(gold_ids)
    recall = len(matched_ids) / gold_count if gold_count else None
    complete = len(matched_ids) == gold_count if gold_count else None
    precision = len(matched_ids) / len(retrieved) if gold_count else None

    spec = case.get("gold_spec")
    constraint_precision = (
        sum(_matches_constraints(fact, spec) for fact in retrieved) / len(retrieved)
        if spec and retrieved
        else None
    )
    gold_ranks = [
        rank
        for rank, evidence_id in enumerate(retrieved_ids, start=1)
        if evidence_id in gold_ids
    ]

    result = {
        "id": case["id"],
        "category": case["category"],
        "expected_outcome": case["expected_outcome"],
        "query": case["query"],
        "gold_count": gold_count,
        "retrieved_gold_count": len(matched_ids),
        "recall_at_k": round(recall, 6) if recall is not None else None,
        "complete_evidence": complete,
        "precision_at_k": round(precision, 6) if precision is not None else None,
        "constraint_precision_at_k": (
            round(constraint_precision, 6)
            if constraint_precision is not None
            else None
        ),
        "first_gold_rank": min(gold_ranks) if gold_ranks else None,
        "latency_ms": round(latency_ms, 3),
        "retrieved_evidence_ids": "|".join(retrieved_ids),
    }
    trace = {
        "id": case["id"],
        "query": case["query"],
        "expected_outcome": case["expected_outcome"],
        "gold_evidence_ids": sorted(gold_ids),
        "retrieved": [
            {
                "rank": rank,
                "score": round(float(scores[index]), 8),
                **facts[index],
            }
            for rank, index in enumerate(indices, start=1)
        ],
    }
    return result, trace


def _mean(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return round(statistics.mean(values), 6) if values else None


def _rate(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [bool(row[field]) for row in rows if row.get(field) is not None]
    return round(sum(values) / len(values), 6) if values else None


def find_sql_summary(
    explicit_path: Path | None,
    *,
    expected_query_count: int,
) -> tuple[Path | None, dict[str, Any] | None]:
    candidates = [explicit_path] if explicit_path else sorted(
        SQL_RESULTS_ROOT.glob("*/summary.json"), reverse=True
    )
    for path in candidates:
        if path is None or not path.exists():
            continue
        summary = json.loads(path.read_text(encoding="utf-8"))
        if int(summary.get("query_count") or 0) == expected_query_count:
            return path, summary
    return None, None


def build_summary(
    results: list[dict[str, Any]],
    *,
    benchmark_path: Path,
    corpus_path: Path,
    cache_path: Path,
    corpus_count: int,
    top_k: int,
    sql_path: Path | None,
    sql_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    answerable = [row for row in results if row["expected_outcome"] == "answer"]
    unsupported = [row for row in results if row["expected_outcome"] == "abstain"]
    gold_total = sum(int(row["gold_count"]) for row in answerable)
    found_total = sum(int(row["retrieved_gold_count"]) for row in answerable)

    by_category: dict[str, dict[str, Any]] = {}
    for category in sorted({row["category"] for row in results}):
        rows = [row for row in results if row["category"] == category]
        by_category[category] = {
            "count": len(rows),
            "micro_recall_at_k": (
                round(
                    sum(int(row["retrieved_gold_count"]) for row in rows)
                    / sum(int(row["gold_count"]) for row in rows),
                    6,
                )
                if sum(int(row["gold_count"]) for row in rows)
                else None
            ),
            "complete_evidence_rate": _rate(rows, "complete_evidence"),
            "mean_constraint_precision_at_k": _mean(
                rows, "constraint_precision_at_k"
            ),
        }

    vector = {
        "micro_recall_at_k": round(found_total / gold_total, 6),
        "complete_evidence_rate": _rate(answerable, "complete_evidence"),
        "mean_precision_at_k": _mean(answerable, "precision_at_k"),
        "mean_constraint_precision_at_k": _mean(
            answerable, "constraint_precision_at_k"
        ),
        "mean_query_search_latency_ms": _mean(results, "latency_ms"),
    }
    sql = None
    delta = None
    if sql_summary:
        sql = {
            "source": str(sql_path),
            "micro_recall": sql_summary.get("retrieval_micro_recall"),
            "complete_evidence_rate": sql_summary.get("retrieval_exact_rate"),
            "final_answer_accuracy": sql_summary.get("final_answer_accuracy"),
            "overall_pass_rate": sql_summary.get("overall_pass_rate"),
        }
        delta = {
            "sql_minus_vector_micro_recall": round(
                float(sql["micro_recall"]) - vector["micro_recall_at_k"], 6
            ),
            "sql_minus_vector_complete_evidence_rate": round(
                float(sql["complete_evidence_rate"])
                - float(vector["complete_evidence_rate"]),
                6,
            ),
        }

    return {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_scope": "retrieval-only; no Vector Agent synthesis",
        "benchmark": str(benchmark_path),
        "vector_corpus": str(corpus_path),
        "embedding_cache": str(cache_path),
        "embedding_model": get_config().embed_model,
        "corpus_document_count": corpus_count,
        "query_count": len(results),
        "answerable_count": len(answerable),
        "unsupported_count": len(unsupported),
        "top_k": top_k,
        "vector_numpy": vector,
        "sql_agent_reference": sql,
        "retrieval_delta": delta,
        "unsupported_note": (
            "Plain top-k vector retrieval always returns candidates; abstention "
            "requires an Agent or a separately calibrated threshold and is not "
            "scored in this retrieval-only experiment."
        ),
        "by_category": by_category,
    }


def _markdown_report(summary: dict[str, Any]) -> str:
    vector = summary["vector_numpy"]
    sql = summary.get("sql_agent_reference") or {}
    delta = summary.get("retrieval_delta") or {}
    category_rows = "\n".join(
        "| {name} | {count} | {recall} | {complete} | {constraint} |".format(
            name=name,
            count=values["count"],
            recall=_percent(values["micro_recall_at_k"]),
            complete=_percent(values["complete_evidence_rate"]),
            constraint=_percent(values["mean_constraint_precision_at_k"]),
        )
        for name, values in summary["by_category"].items()
    )
    return f"""# Financial SQL vs NumPy Vector Retrieval

## Experimental control

- Both methods use the same PostgreSQL-derived financial facts and benchmark gold rows.
- Vector baseline: normalized `{summary['embedding_model']}` embeddings with plain NumPy cosine/dot-product top-{summary['top_k']} retrieval.
- SQL reference: saved full-Agent Financial SQL benchmark run.
- Scope: retrieval only. Vector answer synthesis and abstention are not evaluated here.

## Overall retrieval result

| Metric | NumPy Vector | SQL reference | SQL - Vector |
|---|---:|---:|---:|
| Micro gold-row recall | {_percent(vector['micro_recall_at_k'])} | {_percent(sql.get('micro_recall'))} | {_points(delta.get('sql_minus_vector_micro_recall'))} |
| Complete evidence rate | {_percent(vector['complete_evidence_rate'])} | {_percent(sql.get('complete_evidence_rate'))} | {_points(delta.get('sql_minus_vector_complete_evidence_rate'))} |
| Mean precision@{summary['top_k']} | {_percent(vector['mean_precision_at_k'])} | N/A | N/A |
| Mean constraint precision@{summary['top_k']} | {_percent(vector['mean_constraint_precision_at_k'])} | N/A | N/A |
| NumPy search latency/query | {vector['mean_query_search_latency_ms']:.3f} ms | N/A | N/A |

## Result by question category

| Category | N | Micro Recall@{summary['top_k']} | Complete Evidence | Constraint Precision@{summary['top_k']} |
|---|---:|---:|---:|---:|
{category_rows}

## Interpretation boundary

This experiment isolates retrieval over structured financial facts. It may show
that deterministic SQL filtering retrieves complete constrained rows more
reliably than approximate semantic top-k search. It does **not** show that SQL
is universally better than vector retrieval for narrative or qualitative text.
Plain vector search always returns top-k candidates, so unsupported-query
abstention must be evaluated later through the full Agent or a calibrated
similarity threshold.
"""


def _percent(value: Any) -> str:
    return "N/A" if value is None else f"{float(value) * 100:.2f}%"


def _points(value: Any) -> str:
    return "N/A" if value is None else f"{float(value) * 100:+.2f} pp"


def write_outputs(
    output_dir: Path,
    results: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(results)
    _write_atomic(output_dir / "results.csv", csv_buffer.getvalue())
    _write_atomic(
        output_dir / "retrievals.jsonl",
        "".join(
            json.dumps(trace, ensure_ascii=False, default=str) + "\n"
            for trace in traces
        ),
    )
    _write_atomic(
        output_dir / "summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2),
    )
    _write_atomic(output_dir / "report.md", _markdown_report(summary))


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--embedding-cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--sql-summary", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--rebuild-corpus", action="store_true")
    parser.add_argument("--rebuild-embeddings", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top_k < 1:
        raise SystemExit("--top-k must be positive")
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be positive")

    metadata, cases = load_benchmark(args.benchmark)
    if args.limit:
        cases = cases[: args.limit]

    if args.rebuild_corpus or not args.corpus.exists():
        print(f"Building vector fact corpus: {args.corpus}", flush=True)
        facts = build_corpus(args.corpus)
    else:
        facts = load_corpus(args.corpus)
    print(f"Corpus documents: {len(facts)}", flush=True)

    embeddings = load_or_build_embeddings(
        facts,
        args.corpus,
        args.embedding_cache,
        rebuild=args.rebuild_embeddings,
    )
    model = get_embedding_model()
    print(f"Embedding {len(cases)} benchmark queries...", flush=True)
    query_embeddings = model.encode([case["query"] for case in cases])

    results: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for case, query_vector in zip(cases, query_embeddings):
        started = time.perf_counter()
        scores = embeddings @ query_vector
        elapsed_ms = (time.perf_counter() - started) * 1000
        result, trace = score_case(
            case,
            facts,
            scores,
            top_k=args.top_k,
            latency_ms=elapsed_ms,
        )
        results.append(result)
        traces.append(trace)

    sql_path, sql_summary = find_sql_summary(
        args.sql_summary,
        expected_query_count=int(metadata.get("question_count") or len(cases)),
    )
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_dir or DEFAULT_RESULTS_ROOT / timestamp
    summary = build_summary(
        results,
        benchmark_path=args.benchmark,
        corpus_path=args.corpus,
        cache_path=args.embedding_cache,
        corpus_count=len(facts),
        top_k=args.top_k,
        sql_path=sql_path,
        sql_summary=sql_summary,
    )
    write_outputs(output_dir, results, traces, summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Results written to: {output_dir}")


if __name__ == "__main__":
    main()
