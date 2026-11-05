from copy import deepcopy
import json

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
import pytest
import yaml

from eval_scripts import oracle_bench as oracle
import semigraph.agents.nodes as nodes
from semigraph.config import Config


@pytest.fixture
def runtime(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump({
        "llm": {"provider": "openai", "model": "test-model", "json_mode": True},
    }), encoding="utf-8")
    cfg = Config(config_path)
    cfg.llm_api_key = "test-key-do-not-export"
    cfg.neo4j_password = "test-password-do-not-export"
    llm = FakeMessagesListChatModel(responses=[AIMessage(
        content=json.dumps({"parts": [], "final_answer": "Synthetic answer"}),
        usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    )])
    # FakeMessagesListChatModel does not support bind(response_format=...).
    cfg.llm_json_mode = False
    monkeypatch.setattr(oracle, "get_config", lambda: cfg)
    monkeypatch.setattr(nodes, "get_llm", lambda cfg: llm)
    return cfg


def test_first_50_use_real_gold_texts_and_existing_synthesize(runtime, monkeypatch, tmp_path):
    inputs = []
    checkpoints = []
    real_synthesize = oracle.synthesize_node
    real_write = oracle.write_results
    output_path = tmp_path / "oracle.yaml"

    def synthesize(state, cfg):
        inputs.append(deepcopy(state))
        return real_synthesize(state, cfg=cfg)

    def write(results, path, metadata):
        checkpoints.append(len(results))
        real_write(results, path, metadata)

    monkeypatch.setattr(oracle, "synthesize_node", synthesize)
    monkeypatch.setattr(oracle, "write_results", write)
    results = oracle.run_oracle_bench(output_path=output_path)

    expected = oracle.load_sox_queries()[:50]
    chunks = oracle.load_gold_chunks()
    assert [row["id"] for row in results] == [case["id"] for case in expected]
    assert len(inputs) == 50
    inputs_by_query = {state["synthesis_input"]["original_query"]: state for state in inputs}
    for case, row in zip(expected, results):
        state = inputs_by_query[case["query"]]
        evidence = [chunks[chunk_id] for chunk_id in case["gold_chunks"]]
        assert state == {"synthesis_input": {
            "original_query": case["query"], "accepted_chunks": evidence,
        }}
        assert all("embedding" not in chunk for chunk in evidence)
        assert row["answer_points"] == case["answer_points"]
        assert row["synthesis_trace"]["selected_chunk_ids"] == case["gold_chunks"]
        assert row["synthesis_trace"]["llm_calls"] == 1
        assert row["final_answer"] == "Synthetic answer"
        assert row["token_usage"]["total_tokens"] == 15

    saved = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert saved["results"] == results
    assert saved["summary"]["query_count"] == 50
    assert saved["summary"]["error_count"] == 0
    assert saved["summary"]["token_usage"]["total_tokens"] == 750
    assert saved["measurement"]["selection"] == {"start": 1, "end": 50, "query_count": 50}
    assert saved["config_snapshot"]["llm"]["model"] == "test-model"
    assert checkpoints == list(range(51))
    raw = output_path.read_text(encoding="utf-8")
    assert runtime.llm_api_key not in raw
    assert runtime.neo4j_password not in raw


def test_missing_gold_stops_before_synthesis_and_output(runtime, monkeypatch, tmp_path):
    chunks = oracle.load_gold_chunks()
    missing_id = oracle.load_sox_queries()[49]["gold_chunks"][0]
    del chunks[missing_id]
    monkeypatch.setattr(oracle, "load_gold_chunks", lambda: chunks)

    def unexpected_call(*args, **kwargs):
        pytest.fail("Synthesis must not start when any selected Gold Chunk is missing")

    monkeypatch.setattr(oracle, "synthesize_node", unexpected_call)
    output_path = tmp_path / "oracle.yaml"
    with pytest.raises(ValueError, match="missing Gold Chunks"):
        oracle.run_oracle_bench(output_path=output_path)
    assert not output_path.exists()


def test_synthesis_error_is_saved_and_next_question_continues(runtime, monkeypatch, tmp_path):
    first_query = oracle.load_sox_queries()[0]["query"]
    real_synthesize = oracle.synthesize_node

    def synthesize(state, cfg):
        if state["synthesis_input"]["original_query"] == first_query:
            raise TimeoutError("Provider timeout")
        return real_synthesize(state, cfg=cfg)

    monkeypatch.setattr(oracle, "synthesize_node", synthesize)
    output_path = tmp_path / "oracle.yaml"
    results = oracle.run_oracle_bench(limit=2, workers=1, output_path=output_path)

    assert results[0]["answer_error"] == "TimeoutError"
    assert results[0]["final_answer"] == oracle.GENERATION_ERROR_ANSWER
    assert results[1]["final_answer"] == "Synthetic answer"
    assert "answer_error" not in results[1]
    saved = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert saved["summary"]["error_count"] == 1
    assert saved["results"] == results


@pytest.mark.parametrize("limit,workers", [(0, 1), (75, 1), (1, 0)])
def test_invalid_selection_is_rejected(limit, workers, tmp_path):
    with pytest.raises(ValueError):
        oracle.run_oracle_bench(limit=limit, workers=workers, output_path=tmp_path / "oracle.yaml")


@pytest.mark.parametrize("records,error", [
    ([{"chunk_id": "c1", "text": "Evidence"}] * 2, "Duplicate Gold Chunk"),
    ([{"chunk_id": "c1", "text": " "}], "has no text"),
])
def test_invalid_gold_chunk_file_is_rejected(records, error, tmp_path):
    path = tmp_path / "gold.jsonl"
    path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        oracle.load_gold_chunks(path)


def test_repaired_dataset_runs_all_74_with_its_own_gold(runtime, monkeypatch, tmp_path):
    dataset_path = oracle.ROOT / "benchmark/datasets/sox74_repaired_v1/queries.yaml"
    dataset = yaml.safe_load(dataset_path.read_text(encoding="utf-8"))
    inputs = {}
    real_synthesize = oracle.synthesize_node

    def synthesize(state, cfg):
        synthesis_input = state["synthesis_input"]
        inputs[synthesis_input["original_query"]] = deepcopy(synthesis_input["accepted_chunks"])
        return real_synthesize(state, cfg=cfg)

    monkeypatch.setattr(oracle, "synthesize_node", synthesize)
    output = tmp_path / "repaired.yaml"
    results = oracle.run_oracle_bench(
        dataset_path=dataset_path, limit=74, workers=4, output_path=output,
    )

    assert [row["id"] for row in results] == [case["id"] for case in dataset["queries"]]
    for case in dataset["queries"]:
        evidence = inputs[case["query"]]
        assert [chunk["chunk_id"] for chunk in evidence] == case["gold_chunks"]
        assert all(set(chunk) <= set(oracle.EVIDENCE_FIELDS) for chunk in evidence)
    saved = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert saved["summary"]["error_count"] == 0
    assert saved["summary"]["token_usage"]["total_tokens"] == 74 * 15
    assert saved["measurement"]["dataset_revision"] == "sox74_repaired_v1"
    assert saved["measurement"]["gold_chunks_sha256"] == dataset["metadata"]["gold_chunks_sha256"]


def test_repaired_dataset_rejects_mismatched_gold_before_llm(runtime, monkeypatch, tmp_path):
    def unexpected_call(*args, **kwargs):
        pytest.fail("Mismatched corpus must be rejected before synthesis")

    monkeypatch.setattr(oracle, "synthesize_node", unexpected_call)
    with pytest.raises(ValueError, match="gold_chunks_sha256"):
        oracle.run_oracle_bench(
            dataset_path=oracle.ROOT / "benchmark/datasets/sox74_repaired_v1/queries.yaml",
            gold_chunks_path=oracle.GOLD_CHUNKS_FILE,
            limit=1, output_path=tmp_path / "bad.yaml",
        )


def test_custom_dataset_output_does_not_use_original_run_filename(runtime, monkeypatch, tmp_path):
    dataset_path = oracle.ROOT / "benchmark/datasets/sox74_repaired_v1/queries.yaml"
    monkeypatch.setattr(oracle, "ROOT", tmp_path)
    oracle.run_oracle_bench(dataset_path=dataset_path, limit=1, workers=1)
    assert (tmp_path / "benchmark/results2/oracle_sox74_repaired_v1_first1_full_answer.yaml").exists()
    assert not (tmp_path / "benchmark/results2/oracle_sox_smoke1_full_answer.yaml").exists()
