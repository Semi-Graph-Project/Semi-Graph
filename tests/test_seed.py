import numpy as np
import pytest

from semigraph.online import seed as seed_module


def _candidate(
    candidate_id,
    head,
    head_type,
    relation,
    tail,
    tail_type,
    similarity,
    head_specificity=0.5,
    tail_specificity=0.2,
):
    return {
        "candidate_id": candidate_id,
        "head": head,
        "head_type": head_type,
        "relation": relation,
        "tail": tail,
        "tail_type": tail_type,
        "similarity": similarity,
        "head_specificity": head_specificity,
        "tail_specificity": tail_specificity,
    }


def test_triple_candidates_deduplicate_entity_seeds():
    candidates = [
        _candidate(
            0,
            "intel",
            "COMP",
            "OPERATES_IN",
            "united states",
            "GPE",
            0.9,
        ),
        _candidate(
            1,
            "intel",
            "COMP",
            "PRODUCES",
            "processor",
            "PRODUCT",
            0.8,
            tail_specificity=1.0,
        ),
    ]

    seeds = seed_module.triple_candidates_to_seeds(candidates)
    intel = next(seed for seed in seeds if seed["name"] == "intel")

    assert intel["similarity"] == 0.9
    assert intel["specificity"] == 0.5
    assert intel["triple_similarities"] == [0.9, 0.8]
    assert sum(seed["name"] == "intel" for seed in seeds) == 1
    assert [seed["name"] for seed in seeds] == [
        "intel",
        "united states",
        "processor",
    ]


def test_query_to_triple_candidates_returns_ranked_triples(monkeypatch):
    class FakeEmbeddingModel:
        def encode(self, queries):
            assert queries == ["intel processor"]
            return np.asarray([[1.0, 0.0]], dtype=np.float32)

    metadata = [
        {
            "head": "intel",
            "head_type": "COMP",
            "rel_type": "PRODUCES",
            "tail": "processor",
            "tail_type": "PRODUCT",
            "head_spec": 0.8,
            "tail_spec": 0.9,
        },
        {
            "head": "intel",
            "head_type": "COMP",
            "rel_type": "OPERATES_IN",
            "tail": "united states",
            "tail_type": "GPE",
            "head_spec": 0.8,
            "tail_spec": 0.2,
        },
        {
            "head": "noise",
            "head_type": "CONCEPT",
            "rel_type": "RELATED_TO",
            "tail": "other",
            "tail_type": "CONCEPT",
            "head_spec": 0.1,
            "tail_spec": 0.1,
        },
    ]

    monkeypatch.setattr(seed_module, "get_embedding_model", lambda: FakeEmbeddingModel())
    monkeypatch.setattr(
        seed_module,
        "_load_triple_index",
        lambda: (
            np.asarray([
                [0.90, 0.10],
                [0.80, 0.20],
                [0.40, 0.90],
            ], dtype=np.float32),
            metadata,
        ),
    )

    candidates = seed_module.query_to_triple_candidates(
        "intel processor",
        top_k_candidates=2,
        min_similarity=0.6,
        cfg=object(),
    )

    assert [candidate["candidate_id"] for candidate in candidates] == [0, 1]
    assert [candidate["head"] for candidate in candidates] == ["intel", "intel"]
    assert candidates[0]["relation"] == "PRODUCES"
    assert candidates[0]["tail_type"] == "PRODUCT"
    assert candidates[0]["similarity"] > candidates[1]["similarity"]
    assert "embedding" not in candidates[0]


def test_query_to_triple_candidates_deduplicates_typed_triples(monkeypatch):
    class FakeEmbeddingModel:
        def encode(self, queries):
            return np.asarray([[1.0, 0.0]], dtype=np.float32)

    base = {
        "head": "intel",
        "head_type": "ORG",
        "rel_type": "HAS_STAKE_IN",
        "tail": "mobileye",
        "head_spec": 0.8,
        "tail_spec": 0.7,
    }
    metadata = [
        {**base, "tail_type": "COMP"},
        {**base, "tail_type": "COMP"},
        {**base, "tail_type": "SEGMENT"},
        {
            **base,
            "rel_type": "DISCLOSES",
            "tail": "revenue",
            "tail_type": "FIN_METRIC",
        },
    ]

    monkeypatch.setattr(seed_module, "get_embedding_model", lambda: FakeEmbeddingModel())
    monkeypatch.setattr(
        seed_module,
        "_load_triple_index",
        lambda: (
            np.asarray([
                [0.95, 0.05],
                [0.94, 0.06],
                [0.93, 0.07],
                [0.92, 0.08],
            ], dtype=np.float32),
            metadata,
        ),
    )

    candidates = seed_module.query_to_triple_candidates(
        "intel mobileye revenue",
        top_k_candidates=3,
        min_similarity=0.6,
        cfg=object(),
    )

    assert [candidate["candidate_id"] for candidate in candidates] == [0, 1, 2]
    assert [candidate["tail_type"] for candidate in candidates] == [
        "COMP",
        "SEGMENT",
        "FIN_METRIC",
    ]
    assert [candidate["similarity"] for candidate in candidates] == [
        pytest.approx(0.95),
        pytest.approx(0.93),
        pytest.approx(0.92),
    ]


def test_query_to_triple_seeds_is_compatibility_wrapper(monkeypatch):
    candidates = [_candidate(
        0,
        "intel",
        "COMP",
        "PRODUCES",
        "processor",
        "PRODUCT",
        0.9,
    )]
    expected_seeds = [{
        "name": "intel",
        "type": "COMP",
        "similarity": 0.9,
        "specificity": 0.5,
    }]
    calls = {}

    def fake_candidates(query, **kwargs):
        calls["query"] = query
        calls.update(kwargs)
        return candidates

    def fake_converter(received_candidates):
        assert received_candidates is candidates
        return expected_seeds

    monkeypatch.setattr(seed_module, "query_to_triple_candidates", fake_candidates)
    monkeypatch.setattr(seed_module, "triple_candidates_to_seeds", fake_converter)

    seeds = seed_module.query_to_triple_seeds(
        "intel processor",
        top_k_candidates=4,
        min_similarity=0.7,
        cfg="cfg-sentinel",
    )

    assert seeds == expected_seeds
    assert calls == {
        "query": "intel processor",
        "top_k_candidates": 4,
        "min_similarity": 0.7,
        "cfg": "cfg-sentinel",
    }
