from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

PRIMARY_RUNS = {
    "vector_only": ROOT / "runs/vector_only/details.jsonl",
    "agent_vector": ROOT / "runs/agent_vector/details.jsonl",
    "graph_only_t20": ROOT / "runs/graph_only_t20/details.jsonl",
    "agent_graph_t20": ROOT / "runs/agent_graph_t20/details.jsonl",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def _verify_checksums() -> None:
    for line in (ROOT / "checksums.sha256").read_text().splitlines():
        expected, relative_path = line.split("  ", 1)
        path = ROOT / relative_path
        actual = _sha256(path)
        if actual != expected:
            raise AssertionError(f"checksum mismatch: {relative_path}")


def _recorded_error(row: dict, run_id: str) -> bool:
    if run_id.startswith("agent_"):
        return bool(row.get("error")) or row.get("status") != "ok"
    tool = "vector" if run_id == "vector_only" else "graph"
    return bool(row["tools"][tool].get("error"))


def main() -> None:
    _verify_checksums()
    ids_by_run: dict[str, list[str]] = {}

    for run_id, path in PRIMARY_RUNS.items():
        rows = _load_jsonl(path)
        ids = [row["id"] for row in rows]
        assert len(rows) == 74, f"{run_id}: expected 74 rows"
        assert len(set(ids)) == 74, f"{run_id}: duplicate query IDs"
        assert not any(_recorded_error(row, run_id) for row in rows), (
            f"{run_id}: recorded error found"
        )
        ids_by_run[run_id] = ids

    expected_ids = ids_by_run["vector_only"]
    assert all(ids == expected_ids for ids in ids_by_run.values()), (
        "query IDs or ordering differ between runs"
    )

    manifest = json.loads((ROOT / "manifest.json").read_text())
    print(f"PASS: {manifest['freeze_id']}")
    print("PASS: all frozen file checksums match")
    print("PASS: 4 runs x 74 ordered unique queries, 0 recorded errors")


if __name__ == "__main__":
    main()
