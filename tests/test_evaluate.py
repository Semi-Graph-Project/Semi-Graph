import yaml

from eval_scripts.evaluate import _reciprocal_rank, write_yaml_trace


def test_reciprocal_rank_uses_first_gold_chunk():
    assert _reciprocal_rank(
        ["non-gold", "gold-b", "gold-a"],
        {"gold-a", "gold-b"},
    ) == 0.5
    assert _reciprocal_rank(["non-gold"], {"gold-a"}) == 0.0


def test_write_yaml_trace_reports_mrr(tmp_path):
    output_path = tmp_path / "trace.yaml"
    write_yaml_trace(
        [
            {"hit": 1, "recall": 1.0, "reciprocal_rank": 1.0, "latency_ms": 10.0},
            {"hit": 1, "recall": 0.5, "reciprocal_rank": 0.5, "latency_ms": 20.0},
        ],
        output_path,
    )

    summary = yaml.safe_load(output_path.read_text(encoding="utf-8"))["summary"]
    assert summary["mrr"] == 0.75
