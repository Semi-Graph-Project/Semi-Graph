#!/usr/bin/env python3
"""Rescore saved retrievals against repaired Gold without rerunning the systems."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import statistics

import yaml


OUTPUT = Path(__file__).resolve().parent
BENCHMARK = OUTPUT.parent
SOURCE = BENCHMARK / "human_verify_2_fast"
DATASET = BENCHMARK / "datasets/sox74_repaired_v1/queries.yaml"
CHANGES = DATASET.with_name("changes.yaml")
METRIC_FIELDS = ("hit", "recall", "reciprocal_rank")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def score(retrieved_ids, gold_ids):
    gold = set(gold_ids)
    if not gold:
        raise ValueError("Cannot score an empty Gold set")
    matches = gold.intersection(retrieved_ids)
    return {
        "hit": int(bool(matches)),
        "recall": len(matches) / len(gold),
        "reciprocal_rank": next(
            (1.0 / rank for rank, chunk in enumerate(retrieved_ids, 1) if chunk in gold),
            0.0,
        ),
    }


def means(rows):
    return {
        "hit": statistics.fmean(row["hit"] for row in rows),
        "recall": statistics.fmean(row["recall"] for row in rows),
        "mrr": statistics.fmean(row["reciprocal_rank"] for row in rows),
    }


def write_yaml(path, value):
    path.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )


def main():
    dataset_bytes = DATASET.read_bytes()
    dataset = yaml.safe_load(dataset_bytes)
    references = {row["id"]: row for row in dataset["queries"]}
    changes_bytes = CHANGES.read_bytes()
    changes = {row["id"]: row for row in yaml.safe_load(changes_bytes)["changes"]}
    if len(references) != len(dataset["queries"]):
        raise ValueError("Duplicate ID in repaired dataset")

    paths = sorted(SOURCE.glob("*.yaml"))
    if not paths:
        raise ValueError(f"No saved YAML experiments in {SOURCE}")

    # Validate all inputs before writing any results.
    sources = []
    expected_ids = None
    for path in paths:
        raw = path.read_bytes()
        document = yaml.safe_load(raw)
        rows = document["results"]
        ids = [row["id"] for row in rows]
        if len(ids) != len(set(ids)) or len(rows) != document["summary"]["query_count"]:
            raise ValueError(f"Duplicate IDs or incorrect query count: {path}")
        if expected_ids is None:
            expected_ids = ids
        if ids != expected_ids:
            raise ValueError(f"Different query selection/order: {path}")
        for row in rows:
            case_id = row["id"]
            if case_id not in references or case_id not in changes:
                raise ValueError(f"No repaired reference: {path}:{case_id}")
            change = changes[case_id]
            if row["query"] != change["original_query"]:
                raise ValueError(f"Unexpected original question: {path}:{case_id}")
            if set(row["gold_chunks"]) != set(change["original_gold_chunks"]):
                raise ValueError(f"Unexpected original Gold: {path}:{case_id}")
            if set(references[case_id]["gold_chunks"]) != set(change["repaired_gold_chunks"]):
                raise ValueError(f"Repair files disagree on Gold: {case_id}")
            original_metrics = score(row["top_chunk_ids"], row["gold_chunks"])
            for name, value in original_metrics.items():
                if abs(value - row[name]) > 1e-12:
                    raise ValueError(f"Original metric mismatch: {path}:{case_id}:{name}")
            score(row["top_chunk_ids"], references[case_id]["gold_chunks"])
        for name, value in means(rows).items():
            if round(value, 3) != document["summary"][name]:
                raise ValueError(f"Original summary mismatch: {path}:{name}")
        sources.append((path, document, digest(raw)))

    evaluation = {
        "method": "posthoc_saved_retrieval_against_repaired_gold",
        "reference_dataset_revision": dataset["metadata"]["dataset_revision"],
        "reference_dataset": "../datasets/sox74_repaired_v1/queries.yaml",
        "reference_dataset_sha256": digest(dataset_bytes),
        "reference_changes_sha256": digest(changes_bytes),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "retrieval_selection": "All saved top_chunk_ids in their original order; no additional cutoff, reranking or deduplication.",
        "gold_policy": "Full unique repaired gold_chunks set, including context chunks.",
        "averaging": "Macro average over all selected query IDs, including empty retrievals.",
        "retrieval_rerun": False,
        "answers_recomputed": False,
        "answers_evaluated": False,
        "queries_excluded": 0,
        "query_policy": "query remains the original retrieval input; reference_query records the repaired question for audit.",
        "answer_points_policy": "answer_points uses the repaired reference; no final-answer grading has been performed.",
        "historical_fields": "final_answer, traces, measurement, mode, latency and tokens remain from the original run.",
        "scope_note": "Old-question retrievals rescored against repaired Gold; this is not a new retrieval run on repaired questions or an updated corpus.",
        "ranking_note": "MRR uses saved top_chunk_ids order. For Agents this is final evidence order, not a verified shared global relevance ranking.",
        "excluded_source_files": "ragas_faithfulness_*.json are answer-level judgments and are not rescored.",
    }

    configurations = []
    per_query = []
    for path, original, source_hash in sources:
        derived = deepcopy(original)
        configuration = original["measurement"]["tool"]
        derived["source_summary"] = deepcopy(original["summary"])
        derived["evaluation"] = {
            **evaluation,
            "source_file": f"../human_verify_2_fast/{path.name}",
            "source_sha256": source_hash,
        }
        for row in derived["results"]:
            ref = references[row["id"]]
            row["source_reference"] = {
                "gold_chunks": row["gold_chunks"],
                "answer_points": row.get("answer_points", []),
            }
            row["source_retrieval_metrics"] = {name: row[name] for name in METRIC_FIELDS}
            row["reference_query"] = ref["query"]
            row["gold_chunks"] = ref["gold_chunks"]
            row["answer_points"] = ref.get("answer_points", [])
            row.update(score(row["top_chunk_ids"], row["gold_chunks"]))
            row["matched_gold_chunk_ids"] = list(dict.fromkeys(
                chunk for chunk in row["top_chunk_ids"] if chunk in set(row["gold_chunks"])
            ))
            row["missing_gold_chunk_ids"] = [
                chunk for chunk in dict.fromkeys(row["gold_chunks"]) if chunk not in row["top_chunk_ids"]
            ]
            per_query.append({
                "configuration": configuration,
                "id": row["id"],
                "retrieved_chunk_count": len(row["top_chunk_ids"]),
                "original_gold_count": len(set(row["source_reference"]["gold_chunks"])),
                "repaired_gold_count": len(set(row["gold_chunks"])),
                "matched_gold_count": len(row["matched_gold_chunk_ids"]),
                **{name: row[name] for name in METRIC_FIELDS},
                "original_metrics": row["source_retrieval_metrics"],
            })

        new_means = means(derived["results"])
        derived["summary"].update({name: round(value, 3) for name, value in new_means.items()})
        write_yaml(OUTPUT / path.name, derived)
        configurations.append({
            "configuration": configuration,
            "query_count": len(derived["results"]),
            **{name: round(value, 3) for name, value in new_means.items()},
            "unrounded_metrics": new_means,
            "queries_with_hit": sum(row["hit"] for row in derived["results"]),
            "queries_with_changed_gold": sum(
                set(row["gold_chunks"]) != set(row["source_reference"]["gold_chunks"])
                for row in derived["results"]
            ),
            "original_metrics": means(original["results"]),
            "source_file": f"../human_verify_2_fast/{path.name}",
            "source_sha256": source_hash,
            "result_file": path.name,
        })

    order = {name: index for index, name in enumerate(("vector", "graph", "agent_vector", "agent_graph", "text_to_cypher"))}
    configurations.sort(key=lambda row: order.get(row["configuration"], 99))
    write_yaml(OUTPUT / "summary.yaml", {"evaluation": evaluation, "configurations": configurations})
    write_yaml(OUTPUT / "per_query_metrics.yaml", {"evaluation": evaluation, "results": per_query})
    print(f"Rescored {len(configurations)} experiments / {len(per_query)} saved query results")
    for row in configurations:
        print(f"{row['configuration']}: Hit={row['hit']:.3f} Recall={row['recall']:.3f} MRR={row['mrr']:.3f}")


if __name__ == "__main__":
    main()
