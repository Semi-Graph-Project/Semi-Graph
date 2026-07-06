"""Unit tests for conservative synonym edge decisions."""
from __future__ import annotations

import numpy as np

from semigraph.offline.synonymy import (
    _candidates_within_type,
    _composite_score,
    _filter_synonym_pairs,
)


def _accepted(a: str, b: str, cosine: float) -> tuple[bool, str]:
    ok, _score, rule = _composite_score(a, b, cosine)
    return ok, rule


def test_composite_score_accepts_deterministic_false_negative_fixes():
    assert _accepted("united states", "united_states", 0.72) == (
        True,
        "normalized_string",
    )
    assert _accepted("global foundries", "globalfoundries", 0.81) == (
        True,
        "normalized_string",
    )
    assert _accepted("hbm", "high-bandwidth memory", 0.60) == (
        True,
        "acronym",
    )
    assert _accepted("gpu", "gpus", 0.93) == (True, "plural")


def test_composite_score_rejects_cosine_only_and_polarity_false_positives():
    assert _accepted("high risk", "low risk", 0.99) == (False, "")
    assert _accepted("revenue increase", "revenue decrease", 0.99) == (False, "")
    assert _accepted("zen 3", "zen 3+", 0.99) == (False, "")
    assert _accepted("l40", "l40s", 0.93) == (False, "")
    assert _accepted("mi300", "mi355", 0.99) == (False, "")


def test_composite_score_rejects_risky_segment_shortcuts():
    assert _composite_score(
        "ebu",
        "embedded business unit",
        0.99,
        entity_type="SEGMENT",
    ) == (False, 0.0, "")
    assert _composite_score(
        "silicon carbide",
        "silicon carbide llc",
        0.99,
        entity_type="SEGMENT",
    ) == (False, 0.0, "")
    assert _composite_score(
        "client computing",
        "client computing group",
        0.95,
        entity_type="SEGMENT",
    ) == (True, 0.95, "legal_suffix")


def test_filter_synonym_pairs_drops_ambiguous_acronym_expansions():
    candidates = [
        ("ebu", "embedded business unit", "PRODUCT", 0.91),
        ("ebu", "etch business unit", "PRODUCT", 0.92),
        ("hbm", "high-bandwidth memory", "PRODUCT", 0.61),
    ]

    pairs = _filter_synonym_pairs(candidates)

    assert [(p["name_a"], p["name_b"], p["rule"]) for p in pairs] == [
        ("hbm", "high-bandwidth memory", "acronym")
    ]


def test_candidates_include_deterministic_pairs_below_cosine_cutoff():
    entities = [
        {"name": "hbm", "type": "PRODUCT", "embedding": [1.0, 0.0]},
        {"name": "high-bandwidth memory", "type": "PRODUCT", "embedding": [0.0, 1.0]},
        {"name": "unrelated", "type": "PRODUCT", "embedding": [0.0, 1.0]},
    ]

    pairs = _candidates_within_type(entities, cosine_min=0.65)

    assert ("hbm", "high-bandwidth memory", "PRODUCT", 0.0) in [
        (a, b, t, round(c, 6)) for a, b, t, c in pairs
    ]


def test_candidates_still_require_same_type():
    entities = [
        {"name": "hbm", "type": "PRODUCT", "embedding": np.array([1.0, 0.0])},
        {
            "name": "high-bandwidth memory",
            "type": "RAW_MATERIAL",
            "embedding": np.array([0.0, 1.0]),
        },
    ]

    assert _candidates_within_type(entities, cosine_min=0.65) == []
