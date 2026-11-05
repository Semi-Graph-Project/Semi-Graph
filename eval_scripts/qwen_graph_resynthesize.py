#!/usr/bin/env python3
"""Re-synthesize saved Qwen Agent + Graph evidence without running retrieval.

Run from the project root, for example:
    python /path/to/qwen_graph_resynthesize.py --limit 25 --output /path/to/result.yaml

The source result stores selected chunk IDs, not the original synthesis prompt.
The original chunk text and available metadata are reconstructed from the
controlled Gold and distractor stores; the original retrieval scores are not
available. The new output is a new synthesis run, not the original answer.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime

import yaml


ROOT = Path.cwd()
if not (ROOT / "src/semigraph/agents/nodes.py").is_file():
    raise SystemExit("Run this script from the SemiGraph project root.")
sys.path.insert(0, str(ROOT / "src"))

from semigraph.agents.nodes import synthesize_node  # noqa: E402
from semigraph.config import get_config  # noqa: E402


DEFAULT_INPUT = ROOT / (
    "benchmark/้human_verify_2_local/"
    "controlled_agent_graph_sox_smoke50_qwen_full_graph_fix2_full_answer.yaml"
)
CHUNK_STORES = (
    ROOT / "data/neo4j/finreflectkg_gold_chunks.jsonl",
    ROOT / "data/neo4j/finreflectkg_distractor_820_chunks.jsonl",
)
DEFAULT_OUTPUT = ROOT / "benchmark/results2/qwen_agent_graph_resynthesized.yaml"
EVIDENCE_FIELDS = ("chunk_id", "text", "ticker", "fiscal_year", "section")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases(path: Path, start: int, limit: int | None) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    rows = data.get("results") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("Input YAML must contain a non-empty results list")
    if start < 1 or start > len(rows):
        raise ValueError(f"--start must be between 1 and {len(rows)}")
    if limit is not None and (limit < 1 or start - 1 + limit > len(rows)):
        raise ValueError(f"--limit must fit within the {len(rows)} input rows")

    selected = rows[start - 1 : start - 1 + limit if limit is not None else None]
    for row in selected:
        trace = row.get("synthesis_trace") or {}
        ids = trace.get("selected_chunk_ids")
        if not row.get("id") or not isinstance(row.get("query"), str) or not row["query"].strip():
            raise ValueError("Each selected row must have an id and non-empty query")
        if not isinstance(ids, list) or any(not isinstance(cid, str) or not cid for cid in ids):
            raise ValueError(f"{row['id']}: synthesis_trace.selected_chunk_ids missing or invalid")
    return selected


def load_chunks(wanted: set[str], stores: tuple[Path, ...] = CHUNK_STORES) -> dict[str, dict]:
    """Load selected chunks only; fail on missing IDs or conflicting text."""
    found: dict[str, dict] = {}
    for store in stores:
        with store.open(encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                record = json.loads(line)
                chunk_id = record.get("chunk_id")
                if chunk_id not in wanted:
                    continue
                chunk = {key: record[key] for key in EVIDENCE_FIELDS if key in record}
                if not isinstance(chunk.get("text"), str) or not chunk["text"].strip():
                    raise ValueError(f"Chunk has no text: {chunk_id}")
                if chunk_id in found and found[chunk_id] != chunk:
                    raise ValueError(f"Conflicting chunk data across stores: {chunk_id}")
                found[chunk_id] = chunk

    missing = wanted - found.keys()
    if missing:
        raise ValueError("Missing selected chunks: " + ", ".join(sorted(missing)))
    return found


def write_output(path: Path, metadata: dict, results: list[dict]) -> None:
    """Checkpoint completed results without leaving a partially written YAML."""
    payload = {"measurement": metadata, "results": results}
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Saved Qwen full-answer YAML")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="New output YAML")
    parser.add_argument("--start", type=int, default=1, help="First question number, starting at 1")
    parser.add_argument("--limit", type=int, help="Number of questions; default: all remaining")
    args = parser.parse_args()

    source = args.input.resolve()
    output = args.output.resolve()
    if output == source:
        raise ValueError("Output must be different from the source YAML")
    if output.exists():
        raise FileExistsError(f"Output already exists; choose another --output: {output}")
    if not output.parent.is_dir():
        raise FileNotFoundError(f"Output directory does not exist: {output.parent}")

    cases = load_cases(source, args.start, args.limit)
    selected_ids = {
        cid for row in cases for cid in row["synthesis_trace"]["selected_chunk_ids"]
    }
    chunks = load_chunks(selected_ids)
    cfg = get_config()
    if not cfg.llm_api_key.strip():
        raise RuntimeError(f"No API key configured for llm.provider={cfg.llm_provider!r}")

    metadata = {
        "source_file": str(source),
        "source_sha256": sha256(source),
        "selection": {"start": args.start, "end": args.start + len(cases) - 1, "query_count": len(cases)},
        "chunk_stores": [{"path": str(path), "sha256": sha256(path)} for path in CHUNK_STORES],
        "chunk_selection": "synthesis_trace.selected_chunk_ids, retaining order and duplicates",
        "evidence_note": "Chunk text and metadata reconstructed from stored JSONL; original input scores and full prompt were not saved.",
        "synthesis_node": "semigraph.agents.nodes.synthesize_node",
        "synthesis_model": {"provider": cfg.llm_provider, "model": cfg.llm_model,
                            "temperature": cfg.llm_temperature, "json_mode": cfg.llm_json_mode},
        "created_at": datetime.now().astimezone().isoformat(),
        "retrieval_rerun": False,
    }
    results: list[dict] = []
    for index, case in enumerate(cases, args.start):
        ids = case["synthesis_trace"]["selected_chunk_ids"]
        synthesis_input = {
            "original_query": case["query"],
            "accepted_chunks": [dict(chunks[cid]) for cid in ids],
        }
        row = {"number": index, "id": case["id"], "query": case["query"],
               "selected_chunk_ids": ids}
        try:
            answer = synthesize_node({"synthesis_input": synthesis_input}, cfg=cfg)
            trace = answer["synthesis_trace"]
            row.update({"final_answer": answer["final_answer"],
                        "citations": trace["cited_chunk_ids"],
                        "invalid_citations": trace["invalid_citation_ids"],
                        "citation_status": trace["citation_status"]})
        except Exception as error:
            row.update({"final_answer": None, "citations": [], "invalid_citations": [],
                        "citation_status": "error", "error": type(error).__name__})
        results.append(row)
        write_output(output, metadata, results)
        print(f"{len(results)}/{len(cases)} {case['id']}: {row['citation_status']}", flush=True)

    print(f"YAML: {output}")
    if any(row["citation_status"] == "error" for row in results):
        raise SystemExit("One or more synthesis calls failed; see error types in the output YAML.")


if __name__ == "__main__":
    main()
