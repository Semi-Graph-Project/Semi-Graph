"""Protect the corrected evidence pack and the numeric errors found in the audit."""

import hashlib
import json
from pathlib import Path
import re

import pytest
import yaml


PACK = Path(__file__).resolve().parents[1] / "benchmark/datasets/sox74_repaired_v1"


@pytest.fixture(scope="module")
def pack():
    dataset = yaml.safe_load((PACK / "queries.yaml").read_text(encoding="utf-8"))
    chunks = {
        row["chunk_id"]: row
        for row in map(json.loads, (PACK / "gold_chunks.jsonl").read_text(encoding="utf-8").splitlines())
    }
    return dataset, chunks


def cell(chunks, chunk_id, label, column, occurrence=0):
    normalize = lambda text: re.sub(r"[^a-z0-9]", "", text.lower())
    tokens = [token.strip() for token in chunks[chunk_id]["text"].split("|")]
    indices = [i for i, token in enumerate(tokens) if normalize(token) == normalize(label)]
    raw = re.sub(r"[$,%\s]", "", tokens[indices[occurrence] + column])
    return -float(raw[1:-1]) if raw.startswith("(") else float(raw)


def test_pack_is_complete_and_reference_is_generated_from_same_points(pack):
    dataset, chunks = pack
    reference = yaml.safe_load((PACK / "reference_review.yaml").read_text(encoding="utf-8"))["queries"]
    queries = dataset["queries"]
    assert len(queries) == len({case["id"] for case in queries}) == 74
    assert len(chunks) == 79
    assert sum(len(case["answer_points"]) for case in queries) == 206
    for case, ref in zip(queries, reference):
        assert ref["id"] == case["id"] and ref["query"] == case["query"]
        assert ref["answer_points"] == [f"POINT {i}: {point}" for i, point in enumerate(case["answer_points"], 1)]
        assert set(case["gold_chunks"]) <= chunks.keys()
        assert len(case["answer_points"]) == len(case["answer_point_evidence"])
        for point in case["answer_point_evidence"]:
            assert point["evidence_chunk_ids"]
            assert set(point["evidence_chunk_ids"] + point["context_chunk_ids"]) <= set(case["gold_chunks"])
    for chunk in chunks.values():
        assert hashlib.sha256(chunk["text"].encode()).hexdigest() == chunk["text_sha256"]
        assert "embedding" not in chunk


def test_pack_files_match_recorded_hashes(pack):
    dataset, _ = pack
    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        assert hashlib.sha256((PACK / name).read_bytes()).hexdigest() == expected, name
    assert hashlib.sha256((PACK / "gold_chunks.jsonl").read_bytes()).hexdigest() == dataset["metadata"]["gold_chunks_sha256"]


def test_corrected_numeric_targets_use_actual_table_values(pack):
    dataset, chunks = pack
    answers = {case["id"]: " ".join(case["answer_points"]) for case in dataset["queries"]}
    intel = "INTC_10k_2023.pdf::page_88::chunk_2"
    loss21 = abs(cell(chunks, intel, "All other", 3, occurrence=1))
    loss22 = abs(cell(chunks, intel, "All other", 2, occurrence=1))
    assert loss21 - loss22 == 31
    assert "$31 million" in answers["FRKG073"]
    qct = "QCOM_10k_2024.pdf::page_73::chunk_6"
    total_change = cell(chunks, qct, "Total QCT revenues", 1) - cell(chunks, qct, "Total QCT revenues", 2)
    assert total_change == 2814
    for qid in ("FRKG360", "FRKG437"):
        assert "$2,814 million" in answers[qid]
    old_ti = "TXN_10k_2022.pdf::page_33::chunk_2"
    rev21 = cell(chunks, old_ti, "Other", 1)
    ti22 = "TXN_10k_2024.pdf::page_31::chunk_3"
    ti23 = "TXN_10k_2024.pdf::page_31::chunk_1"
    rev22 = cell(chunks, ti22, "Revenue", 3)
    rev23 = cell(chunks, ti23, "Revenue", 3)
    assert rev21 + rev22 + rev23 == 3764
    assert "$3,764 million" in answers["FRKG393"]
    ratio = cell(chunks, ti22, "Revenue", 2) / (rev22 - rev21)
    assert f"{ratio:.6f}:1" in answers["FRKG520"]
    assert "carrying goodwill" in answers["FRKG103"]
    assert "accounts receivable" not in answers["FRKG103"]
