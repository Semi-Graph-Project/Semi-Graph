import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

from semigraph.offline import embeddings


def test_get_embedding_model_loads_once_across_threads(monkeypatch):
    workers = 4
    barrier = Barrier(workers)
    constructor_calls = []
    loaded_model = SimpleNamespace(
        get_sentence_embedding_dimension=lambda: 768,
    )

    def fake_sentence_transformer(*args, **kwargs):
        constructor_calls.append((args, kwargs))
        time.sleep(0.05)
        return loaded_model

    monkeypatch.setattr(
        embeddings,
        "SentenceTransformer",
        fake_sentence_transformer,
    )
    cfg = SimpleNamespace(
        embed_model="test-model",
        embed_device="cpu",
    )
    monkeypatch.setattr(embeddings, "get_config", lambda: cfg)
    monkeypatch.setattr(embeddings, "_embedding_model", None)

    def load_model():
        barrier.wait()
        return embeddings.get_embedding_model().model

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda _: load_model(), range(workers)))

    assert constructor_calls == [(("test-model",), {"device": "cpu"})]
    assert all(result is loaded_model for result in results)
