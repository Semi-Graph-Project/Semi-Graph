import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from semigraph.online import cross_encoder_runtime


def test_runtime_loads_local_onnx_once(monkeypatch):
    calls = {}

    def fake_snapshot_download(model_name, **kwargs):
        calls["download"] = (model_name, kwargs)
        return "/cached/jina-reranker"

    class FakeCrossEncoder:
        def __init__(self, model_path, **kwargs):
            calls["model"] = (model_path, kwargs)
            calls["model_load_count"] = calls.get("model_load_count", 0) + 1

        def predict(self, pairs, **kwargs):
            calls.setdefault("predict", []).append((pairs, kwargs))
            return [0.5]

    monkeypatch.setattr(cross_encoder_runtime, "_model", None)
    monkeypatch.setattr(
        cross_encoder_runtime,
        "snapshot_download",
        fake_snapshot_download,
    )
    monkeypatch.setattr(
        cross_encoder_runtime,
        "CrossEncoder",
        FakeCrossEncoder,
    )

    pairs = [("query", "passage")]
    cross_encoder_runtime.predict_cross_encoder_scores(pairs)
    cross_encoder_runtime.predict_cross_encoder_scores(pairs)

    assert calls["download"] == (
        "jinaai/jina-reranker-v1-tiny-en",
        {"local_files_only": True},
    )
    assert calls["model"] == (
        "/cached/jina-reranker",
        {
            "backend": "onnx",
            "max_length": 2048,
            "local_files_only": True,
            "model_kwargs": {
                "file_name": "onnx/model_quantized.onnx",
                "provider": "CPUExecutionProvider",
            },
        },
    )
    assert calls["model_load_count"] == 1
    assert calls["predict"] == [
        (pairs, {"batch_size": 2, "show_progress_bar": False}),
        (pairs, {"batch_size": 2, "show_progress_bar": False}),
    ]


def test_runtime_serializes_inference(monkeypatch):
    state = {"active": 0, "max_active": 0}
    state_lock = Lock()

    class FakeModel:
        def predict(self, pairs, **kwargs):
            with state_lock:
                state["active"] += 1
                state["max_active"] = max(
                    state["max_active"],
                    state["active"],
                )
            time.sleep(0.02)
            with state_lock:
                state["active"] -= 1
            return [0.5]

    monkeypatch.setattr(cross_encoder_runtime, "_model", FakeModel())

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(
            cross_encoder_runtime.predict_cross_encoder_scores,
            [[("query", "passage")]] * 4,
        ))

    assert results == [[0.5]] * 4
    assert state["max_active"] == 1
