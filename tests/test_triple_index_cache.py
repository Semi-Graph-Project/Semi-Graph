import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

import numpy as np
import pytest

from semigraph.online import triple_index_cache as cache_module


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch):
    monkeypatch.setattr(cache_module, "_TRIPLE_INDEX_CACHE", {})


def _cfg(uri="bolt://localhost:7690", user="neo4j", dim=2):
    return SimpleNamespace(neo4j_uri=uri, neo4j_user=user, embed_dim=dim)


def _row(head="intel", dim=2):
    return {
        "head": head,
        "head_type": "ORG",
        "head_spec": 1.0,
        "rel_type": "PRODUCES",
        "tail": "cpu",
        "tail_type": "PRODUCT",
        "tail_spec": 1.0,
        "embedding": [1.0] + [0.0] * (dim - 1),
    }


def _mock_driver(monkeypatch, read_rows):
    calls = {"opened": [], "closed": [], "reads": 0}

    class FakeSession:
        def __init__(self, cfg):
            self.cfg = cfg

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def run(self, query):
            assert query == cache_module._CYPHER_LOAD_TRIPLES
            calls["reads"] += 1
            return read_rows(self.cfg)

    class FakeDriver:
        def __init__(self, cfg):
            self.cfg = cfg

        def session(self):
            return FakeSession(self.cfg)

        def close(self):
            calls["closed"].append(self.cfg.neo4j_uri)

    def fake_get_driver(cfg):
        calls["opened"].append(cfg.neo4j_uri)
        return FakeDriver(cfg)

    monkeypatch.setattr(cache_module, "get_neo4j_driver", fake_get_driver)
    return calls


def test_cache_is_scoped_to_backend(monkeypatch):
    rows_by_uri = {
        "bolt://localhost:7690": [_row("benchmark")],
        "bolt://localhost:7687": [_row("production")],
    }
    calls = _mock_driver(monkeypatch, lambda cfg: rows_by_uri[cfg.neo4j_uri])
    benchmark_cfg = _cfg()
    production_cfg = _cfg(uri="bolt://localhost:7687")

    benchmark_index = cache_module.load_triple_index(benchmark_cfg)
    production_index = cache_module.load_triple_index(production_cfg)
    benchmark_index_again = cache_module.load_triple_index(benchmark_cfg)

    assert benchmark_index[1][0]["head"] == "benchmark"
    assert production_index[1][0]["head"] == "production"
    assert benchmark_index_again is benchmark_index
    assert calls["opened"] == ["bolt://localhost:7690", "bolt://localhost:7687"]
    assert calls["closed"] == calls["opened"]


@pytest.mark.parametrize("other_cfg", [_cfg(user="another_user"), _cfg(dim=3)])
def test_cache_is_scoped_to_user_and_embedding_dimensions(monkeypatch, other_cfg):
    calls = _mock_driver(monkeypatch, lambda cfg: [_row(dim=cfg.embed_dim)])

    first = cache_module.load_triple_index(_cfg())
    second = cache_module.load_triple_index(other_cfg)

    assert first is not second
    assert second[0].shape == (1, other_cfg.embed_dim)
    assert calls["reads"] == 2


def test_concurrent_cold_cache_loads_once_and_shares_same_objects(monkeypatch):
    workers = 8
    start_barrier = Barrier(workers)
    cfg = _cfg()

    def slow_read(_cfg):
        # Keep the first read in flight while the other workers reach the cache.
        time.sleep(0.05)
        return [_row()]

    calls = _mock_driver(monkeypatch, slow_read)

    def load(_worker):
        start_barrier.wait(timeout=5)
        return cache_module.load_triple_index(cfg)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(load, range(workers)))

    assert calls["reads"] == 1
    assert len(calls["opened"]) == len(calls["closed"]) == 1
    assert all(result is results[0] for result in results)
    assert all(result[0] is results[0][0] for result in results)
    assert all(result[1] is results[0][1] for result in results)


def test_empty_index_is_cached(monkeypatch):
    calls = _mock_driver(monkeypatch, lambda cfg: [])
    cfg = _cfg()

    first = cache_module.load_triple_index(cfg)
    second = cache_module.load_triple_index(cfg)

    assert second is first
    assert first[0].shape == (0, cfg.embed_dim)
    assert first[0].dtype == np.float32
    assert first[1] == []
    assert calls["reads"] == 1
    assert calls["closed"] == calls["opened"]


def test_failed_load_closes_driver_and_can_retry(monkeypatch):
    attempts = 0

    def read_rows(_cfg):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("Neo4j unavailable")
        return [_row()]

    calls = _mock_driver(monkeypatch, read_rows)
    cfg = _cfg()

    with pytest.raises(RuntimeError, match="Neo4j unavailable"):
        cache_module.load_triple_index(cfg)

    loaded = cache_module.load_triple_index(cfg)
    assert cache_module.load_triple_index(cfg) is loaded
    assert calls["reads"] == 2
    assert calls["closed"] == calls["opened"]


def test_clear_cache_reloads_updated_data(monkeypatch):
    rows = [_row("original")]
    calls = _mock_driver(monkeypatch, lambda cfg: rows)
    cfg = _cfg()
    first = cache_module.load_triple_index(cfg)
    rows = [_row("updated")]

    cache_module.clear_triple_index_cache()
    second = cache_module.load_triple_index(cfg)

    assert first[1][0]["head"] == "original"
    assert second[1][0]["head"] == "updated"
    assert second is not first
    assert calls["reads"] == 2
