"""
Build :SYNONYM_OF edges between Entity nodes that refer to the same real-world
thing (Phase B2 — Step 2-3).

The core problem: BGE cosine alone misses abbreviation pairs (e.g. `amd` ↔
`advanced micro devices` cosine = 0.77, below the usual 0.85 threshold). We
combine four signals into a rule-based decision so each known synonym pattern
has at least one rule that catches it:

  Rule 1 — Substring: shorter is a token of longer + high cosine
           catches paraphrase pairs like `nvidia` ↔ `nvidia corporation`
  Rule 2 — Acronym:   shorter is the initials of longer's words + reasonable cos
           catches `amd` ↔ `advanced micro devices`
  Rule 3 — Token set: token_set_ratio ≥ 0.85 + reasonable cosine
           catches `advanced micro devices` ↔ `advanced micro devices inc`
           and `5th gen amd epyc processors` ↔ `5th generation amd epyc processors`
  Rule 4 — Pure semantic: cosine ≥ 0.92 alone

Type filter: every pair must share `entity.type` to avoid linking
`nvidia` (ORG) with `nvidia rtx` (PRODUCT) just because both share the prefix.

Scoring: each rule emits a score ∈ [0,1]. The :SYNONYM_OF edge stores it as
`score` so we can inspect false positives later.
"""
from __future__ import annotations

import time
from typing import Optional

import numpy as np
from neo4j import Driver
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver


# ===========================================================================
# Config — tune these via build_synonymy(...) kwargs
# ===========================================================================

# Legal suffixes stripped before acronym detection
LEGAL_SUFFIXES = frozenset({
    "inc", "inc.", "corp", "corp.", "corporation", "ltd", "limited",
    "llc", "plc", "co", "co.", "company", "holding", "holdings",
    "group", "ag", "nv", "sa",
})

# Entity types for which synonymy is meaningful. Skip noisy types like
# RISK_FACTOR where many distinct concepts share token overlap.
DEFAULT_SYNONYMY_TYPES = frozenset({
    "ORG", "COMP", "PRODUCT", "GPE", "RAW_MATERIAL", "FIN_MARKET", "SEGMENT",
})


# ===========================================================================
# Helpers
# ===========================================================================


def _is_substring_token(short: str, long: str) -> bool:
    """True if `short` matches one of `long`'s whitespace tokens exactly."""
    return short.lower() in long.lower().split()


def _digits_match(a: str, b: str) -> bool:
    """
    Both names must have the same digit sequence (or both have no digits).
    Catches: 'mi300' vs 'mi355' (digits differ → reject as synonym).
    Allows:  'virtex 6' vs 'virtex-6' (same digit '6'), 'amd' vs 'amd inc' (no digits).
    Reason:  in semiconductor naming, digits encode model number — differing
             digits almost always mean different physical products.
    """
    da = "".join(c for c in a if c.isdigit())
    db = "".join(c for c in b if c.isdigit())
    return da == db


def _is_plural_variant(short: str, long: str) -> bool:
    """
    True if `long` == `short` + 's' or 'es' (English plural).
    Catches: 'gpu' ↔ 'gpus', 'blackwell architecture' ↔ 'blackwell architectures'
    Rejects: 'h20' ↔ 'h200' (digit, not 's'/'es'), 'virtex-4' ↔ 'virtex-5' (different)
    """
    short = short.strip().lower()
    long = long.strip().lower()
    return long == short + "s" or long == short + "es"


def _is_acronym_of(short: str, long: str) -> bool:
    """
    True if short is the initials of long's content words (legal suffixes
    stripped). 'amd' ↔ 'advanced micro devices' → True.
    Length of short ∈ [2, 7] — outside this range the false-positive rate
    on noise tokens is too high.
    """
    short_clean = short.replace(".", "").replace(" ", "").lower()
    if not 2 <= len(short_clean) <= 7:
        return False
    words = [w for w in long.lower().split() if w not in LEGAL_SUFFIXES]
    if len(words) < 2:
        return False
    initials = "".join(w[0] for w in words if w)
    return initials == short_clean


def _composite_score(name_a: str, name_b: str, cosine: float) -> tuple[bool, float, str]:
    """
    Decide if a pair is a synonym + which rule fired.

    Returns:
        (is_synonym, score, rule_name)
    """
    short, long = sorted([name_a, name_b], key=len)
    tokens_short = set(short.lower().split())
    tokens_long = set(long.lower().split())

    # Rule 1: Legal-suffix paraphrase
    # shorter's tokens ⊂ longer's tokens AND extra tokens are ALL legal suffixes
    # Catches: 'nvidia' ↔ 'nvidia corporation', 'amd' ↔ 'amd inc'
    # Rejects: 'blackwell' ↔ 'blackwell architecture' (extra='architecture' not legal)
    if tokens_short and tokens_short.issubset(tokens_long):
        extra = tokens_long - tokens_short
        if extra and extra.issubset(LEGAL_SUFFIXES) and cosine >= 0.80:
            return True, max(cosine, 0.95), "legal_suffix"

    # Rule 2: Acronym (abbreviation pattern)
    # Catches: 'amd' ↔ 'advanced micro devices'
    if _is_acronym_of(short, long) and cosine >= 0.65:
        return True, 0.90, "acronym"

    # Rule 3: Plural variant ('s' or 'es' suffix only)
    # Catches: 'gpu' ↔ 'gpus', 'blackwell architecture' ↔ 'blackwell architectures'
    # Rejects: 'h20' ↔ 'h200' (digit suffix not plural)
    if _is_plural_variant(short, long) and cosine >= 0.75:
        return True, 0.92, "plural"

    # Rule 4: Pure semantic confidence — very strict to avoid product-line false positives
    # like 'geforce rtx' ↔ 'nvidia rtx' (cos≈0.93). At 0.97+ we mostly catch
    # punctuation/whitespace variants like 'virtex 6' ↔ 'virtex-6'.
    # Additional gate: digits must match — rejects 'mi300' vs 'mi355' (cos very high
    # but model numbers differ → distinct products).
    if cosine >= 0.97 and _digits_match(name_a, name_b):
        return True, cosine, "semantic"

    return False, 0.0, ""


# ===========================================================================
# Pipeline
# ===========================================================================


def _load_entities_with_embeddings(
    driver: Driver, types: Optional[frozenset[str]] = None
) -> list[dict]:
    """Pull (name, type, embedding) for entities that have an embedding."""
    type_filter = "AND e.type IN $types " if types else ""
    cypher = (
        "MATCH (e:Entity) "
        "WHERE e.embedding IS NOT NULL "
        + type_filter +
        "RETURN e.name AS name, e.type AS type, e.embedding AS embedding"
    )
    with driver.session() as s:
        result = s.run(cypher, types=list(types) if types else [])
        return [dict(r) for r in result]


def _candidates_within_type(
    entities: list[dict], cosine_min: float
) -> list[tuple[str, str, str, float]]:
    """
    Group entities by type, compute cosine matrix per group, return candidate
    pairs (name_a, name_b, type, cosine) where cosine >= cosine_min and
    name_a < name_b (deduplicated, undirected).
    """
    by_type: dict[str, list[dict]] = {}
    for e in entities:
        by_type.setdefault(e["type"], []).append(e)

    pairs: list[tuple[str, str, str, float]] = []
    for t, group in by_type.items():
        if len(group) < 2:
            continue
        names = [g["name"] for g in group]
        # L2-normalized vectors → V @ V.T = cosine matrix
        V = np.asarray([g["embedding"] for g in group], dtype=np.float32)
        cos_mat = V @ V.T
        n = len(group)
        # Upper triangle without diagonal
        ii, jj = np.triu_indices(n, k=1)
        for i, j in zip(ii, jj):
            c = float(cos_mat[i, j])
            if c < cosine_min:
                continue
            a, b = names[i], names[j]
            if a > b:
                a, b = b, a
            pairs.append((a, b, t, c))
    return pairs


def _filter_synonym_pairs(
    candidates: list[tuple[str, str, str, float]]
) -> list[dict]:
    """Apply composite scoring; keep only pairs that satisfy a rule."""
    syns: list[dict] = []
    for a, b, t, cos in candidates:
        is_syn, score, rule = _composite_score(a, b, cos)
        if is_syn:
            syns.append({
                "name_a": a, "name_b": b, "type": t,
                "cosine": cos, "score": score, "rule": rule,
            })
    return syns


def _write_synonym_edges(driver: Driver, pairs: list[dict]) -> int:
    """
    Create undirected SYNONYM_OF edges (we store one direction; queries
    traverse undirected via `-[:SYNONYM_OF]-`).
    """
    if not pairs:
        return 0
    cypher = """
    UNWIND $rows AS row
    MATCH (a:Entity {name: row.name_a, type: row.type})
    MATCH (b:Entity {name: row.name_b, type: row.type})
    MERGE (a)-[r:SYNONYM_OF]->(b)
    SET r.score = row.score, r.cosine = row.cosine, r.rule = row.rule
    RETURN count(r) AS written
    """
    with driver.session() as s:
        result = s.run(cypher, rows=pairs).single()
        return result["written"] if result else 0


def build_synonymy(
    cosine_min: float = 0.65,
    types: Optional[frozenset[str]] = None,
    cfg: Optional[Config] = None,
    dry_run: bool = False,
) -> dict:
    """
    Compute synonym pairs across all (or filtered) entity types and write
    :SYNONYM_OF edges.

    Args:
        cosine_min: cosine threshold for candidate selection (before composite scoring)
        types:      restrict to these entity types; default = DEFAULT_SYNONYMY_TYPES
        cfg:        config; defaults to cached singleton
        dry_run:    compute pairs but don't write edges (for tuning)

    Returns: stats dict
    """
    cfg = cfg or get_config()
    types = types if types is not None else DEFAULT_SYNONYMY_TYPES

    driver = get_neo4j_driver(cfg)
    try:
        t0 = time.time()
        entities = _load_entities_with_embeddings(driver, types=types)
        print(f"[synonymy] loaded {len(entities)} entities across types {sorted(types)}")
        if not entities:
            return {"candidates": 0, "synonyms": 0, "written": 0}

        t1 = time.time()
        candidates = _candidates_within_type(entities, cosine_min=cosine_min)
        print(f"[synonymy] {len(candidates)} candidates with cosine >= {cosine_min} "
              f"(matmul {time.time()-t1:.1f}s)")

        t2 = time.time()
        synonyms = _filter_synonym_pairs(candidates)
        print(f"[synonymy] {len(synonyms)} synonym pairs after composite scoring "
              f"(filter {time.time()-t2:.1f}s)")

        # Per-rule breakdown
        rule_counts: dict[str, int] = {}
        for s_ in synonyms:
            rule_counts[s_["rule"]] = rule_counts.get(s_["rule"], 0) + 1
        print(f"[synonymy] rule breakdown: {rule_counts}")

        if dry_run:
            print("[synonymy] DRY RUN — not writing edges")
            return {
                "candidates": len(candidates),
                "synonyms": len(synonyms),
                "written": 0,
                "by_rule": rule_counts,
                "pairs": synonyms,
            }

        t3 = time.time()
        written = _write_synonym_edges(driver, synonyms)
        print(f"[synonymy] wrote {written} :SYNONYM_OF edges "
              f"(write {time.time()-t3:.1f}s)")

        print(f"[synonymy] DONE — total {time.time()-t0:.1f}s")
        return {
            "candidates": len(candidates),
            "synonyms": len(synonyms),
            "written": written,
            "by_rule": rule_counts,
        }
    finally:
        driver.close()
