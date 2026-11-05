#!/usr/bin/env python3
"""Recompute retrieval @5 from saved results without calling a retriever or LLM."""

from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics

import yaml


OUTPUT = Path(__file__).resolve().parent
SOURCE = OUTPUT.parent / "human_verify_2_fast"
K = 5


def score(chunk_ids, gold_ids):
    gold = set(gold_ids)
    matched = gold.intersection(chunk_ids)
    return {
        "hit": int(bool(matched)),
        "recall": len(matched) / len(gold),
        "reciprocal_rank": next(
            (1.0 / rank for rank, chunk_id in enumerate(chunk_ids, 1)
             if chunk_id in gold),
            0.0,
        ),
    }


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    source_paths = sorted(SOURCE.glob("*.yaml"))
    if not source_paths:
        raise ValueError(f"No YAML results found in {SOURCE}")

    # Validate every source before writing any derived result.
    sources = []
    reference = None
    for path in source_paths:
        raw = path.read_bytes()
        document = yaml.safe_load(raw)
        rows = document["results"]
        identities = {}
        for row in rows:
            if row["id"] in identities or not row["gold_chunks"]:
                raise ValueError(f"Duplicate query ID or empty gold: {path}:{row['id']}")
            identities[row["id"]] = (row["query"], set(row["gold_chunks"]))
            metrics = score(row["top_chunk_ids"], row["gold_chunks"])
            for name, value in metrics.items():
                if abs(value - row[name]) > 1e-12:
                    raise ValueError(f"Source metric mismatch: {path}:{row['id']}:{name}")
        if len(rows) != document["summary"]["query_count"]:
            raise ValueError(f"Source query count mismatch: {path}")
        if reference is None:
            reference = identities
        if identities != reference:
            raise ValueError(f"Questions or gold differ across configurations: {path}")
        sources.append((path, document, hashlib.sha256(raw).hexdigest()))

    generated_at = datetime.now(timezone.utc).isoformat()
    summaries = []
    per_query = []
    for path, original, source_hash in sources:
        config = path.stem.removeprefix("controlled_").split("_sox_", 1)[0]
        derived = deepcopy(original)
        derived["source_summary"] = derived.pop("summary")
        derived["evaluation"] = {
            "k": K,
            "method": "posthoc_saved_order_prefix",
            "source_file": f"../human_verify_2_fast/{path.name}",
            "source_sha256": source_hash,
            "generated_at_utc": generated_at,
            "ordering": "Keep saved top_chunk_ids order; no reranking or deduplication.",
            "gold": "Use each source row's full unique gold_chunks set.",
            "averaging": "macro: equal weight per query, including empty retrievals",
            "retrieval_rerun": False,
            "answers_recomputed": False,
            "historical_fields": (
                "final_answer, synthesis_trace, measurement, latency and token usage "
                "are preserved from the original run, not measured at K=5."
            ),
            "agent_order_note": (
                "Agent top_chunk_ids are saved final evidence order; "
                "a shared global relevance ranking is not established."
            ),
        }
        for row in derived["results"]:
            row["source_retrieval"] = {
                "top_chunk_ids": row["top_chunk_ids"],
                **{key: row[key] for key in ("hit", "recall", "reciprocal_rank")},
            }
            row["top_chunk_ids"] = row["top_chunk_ids"][:K]
            row.update(score(row["top_chunk_ids"], row["gold_chunks"]))
            row["evaluation_k"] = K
            row["matched_gold_chunk_ids"] = [
                chunk_id for chunk_id in dict.fromkeys(row["gold_chunks"])
                if chunk_id in row["top_chunk_ids"]
            ]
            per_query.append({
                "configuration": config,
                "id": row["id"],
                "gold_count": len(set(row["gold_chunks"])),
                "source_chunk_count": len(row["source_retrieval"]["top_chunk_ids"]),
                "evaluated_chunk_count": len(row["top_chunk_ids"]),
                "matched_gold_count_at_5": len(row["matched_gold_chunk_ids"]),
                "hit_at_5": row["hit"],
                "recall_at_5": row["recall"],
                "reciprocal_rank_at_5": row["reciprocal_rank"],
                "source_hit": row["source_retrieval"]["hit"],
                "source_recall": row["source_retrieval"]["recall"],
                "source_reciprocal_rank": row["source_retrieval"]["reciprocal_rank"],
            })

        rows = derived["results"]
        means = {
            "hit": statistics.fmean(row["hit"] for row in rows),
            "recall": statistics.fmean(row["recall"] for row in rows),
            "mrr": statistics.fmean(row["reciprocal_rank"] for row in rows),
        }
        counts = Counter(len(row["source_retrieval"]["top_chunk_ids"]) for row in rows)
        derived["summary"] = {
            "query_count": len(rows),
            "evaluation_k": K,
            **{name: round(value, 3) for name, value in means.items()},
        }
        # Put current metrics first; keep all other original data for audit.
        derived = {"summary": derived.pop("summary"), **derived}
        output_name = path.stem + "_at5.yaml"
        (OUTPUT / output_name).write_text(
            yaml.safe_dump(derived, allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8",
        )
        summaries.append({
            "configuration": config,
            "query_count": len(rows),
            "evaluation_k": K,
            "hit_at_5": means["hit"],
            "recall_at_5": means["recall"],
            "mrr_at_5": means["mrr"],
            "queries_with_hit_at_5": sum(row["hit"] for row in rows),
            "queries_truncated": sum(count for length, count in counts.items() if length > K),
            "queries_with_fewer_than_5": sum(count for length, count in counts.items() if length < K),
            "source_file": path.name,
            "source_sha256": source_hash,
            "result_file": output_name,
        })

    order = {name: i for i, name in enumerate(
        ("vector", "graph", "agent_vector", "agent_graph", "text_to_cypher")
    )}
    summaries.sort(key=lambda row: (order.get(row["configuration"], 99), row["configuration"]))
    write_csv(OUTPUT / "summary.csv", summaries)
    write_csv(OUTPUT / "per_query_metrics.csv", per_query)
    (OUTPUT / "summary.json").write_text(
        json.dumps({"generated_at_utc": generated_at, "configurations": summaries},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Evaluated {len(summaries)} configurations / {len(per_query)} query results at K={K}")
    for row in summaries:
        print(f"{row['configuration']}: Hit@5={row['hit_at_5']:.3f} "
              f"Recall@5={row['recall_at_5']:.3f} MRR@5={row['mrr_at_5']:.3f}")


if __name__ == "__main__":
    main()
