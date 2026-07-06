"""
Build :SYNONYM_OF edges between Entity nodes that refer to the same real-world
thing (Phase B2 — Step 2-3).

The core problem: cosine similarity is a useful candidate generator, but it is
not identity. Opposite or merely related phrases can share context and score
high, so every accepted pair must satisfy an interpretable identity rule:

  Rule 1 — Normalized string: punctuation/spacing/underscore variants
           catches `united states` ↔ `united_states`
  Rule 2 — Legal suffix: shorter tokens + legal suffix only
           catches `nvidia` ↔ `nvidia corporation`
  Rule 3 — Acronym: shorter is the initials of longer's content tokens
           catches `amd` ↔ `advanced micro devices`,
                   `hbm` ↔ `high-bandwidth memory`
  Rule 4 — Plural: English plural variants
           catches `gpu` ↔ `gpus`

Type filter: every pair must share `entity.type` to avoid linking
`nvidia` (ORG) with `nvidia rtx` (PRODUCT) just because both share the prefix.

Scoring: each rule emits a score ∈ [0,1]. The :SYNONYM_OF edge stores it as
`score` so we can inspect false positives later.
"""
from __future__ import annotations

import re
import time
from typing import Optional

import numpy as np
from neo4j import Driver

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

ACRONYM_SYNONYMY_TYPES = frozenset({
    "ORG", "COMP", "PRODUCT", "GPE", "RAW_MATERIAL",
})

# These token groups flip meaning while leaving the surrounding context very
# similar. They are a hard precision guard: such pairs may be related, but they
# are not aliases. Keep these as opposing groups rather than standalone tokens
# so legitimate terms like "high-bandwidth memory" are not blocked.
OPPOSING_TOKEN_GROUPS = (
    (
        frozenset({"high", "higher"}),
        frozenset({"low", "lower"}),
    ),
    (
        frozenset({
            "benefit", "benefits", "favorable", "gain", "gains",
            "increase", "increased", "increases", "positive", "positively",
            "up", "upside",
        }),
        frozenset({
            "adverse", "decrease", "decreased", "decreases", "decline",
            "declined", "declines", "down", "downside", "loss", "losses",
            "negative", "negatively", "reduction", "shortage",
            "unfavorable",
        }),
    ),
)


# ===========================================================================
# Helpers
# ===========================================================================


def _is_substring_token(short: str, long: str) -> bool:
    """True if `short` matches one of `long`'s whitespace tokens exactly."""
    return short.lower() in long.lower().split()


def _tokens(name: str) -> list[str]:
    """Lowercase alphanumeric tokens; punctuation and separators are ignored."""
    return re.findall(r"[a-z0-9]+", name.lower())


def _token_set(name: str) -> set[str]:
    return set(_tokens(name))


def _canonical_key(name: str) -> str:
    """String key for exact alias variants caused by punctuation/spacing only."""
    return "".join(_tokens(name))


def _has_plus_marker(name: str) -> bool:
    """Plus signs are meaningful in semiconductor product names."""
    return "+" in name


def _has_contrast_delta(a: str, b: str) -> bool:
    """True when the two names contain opposing polarity markers."""
    ta = _token_set(a)
    tb = _token_set(b)
    for positive, negative in OPPOSING_TOKEN_GROUPS:
        if (ta & positive and tb & negative) or (ta & negative and tb & positive):
            return True
    return False


def _is_normalized_string_variant(a: str, b: str) -> bool:
    """
    True for variants that become identical after separator normalization.

    The plus sign is intentionally not ignored: `Zen 3` and `Zen 3+` are not
    the same product line, even though a naive punctuation strip would merge
    them.
    """
    if _has_plus_marker(a) != _has_plus_marker(b):
        return False
    if _has_contrast_delta(a, b):
        return False
    return (
        _canonical_key(a) == _canonical_key(b)
        and a.strip().lower() != b.strip().lower()
    )


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
    Rejects: 'h20' ↔ 'h200' (digit, not 's'/'es'), 'virtex-4' ↔
             'virtex-5' (different), and single-token product codes like
             'l40' ↔ 'l40s' where the suffix is a model variant, not plural.
    """
    short = short.strip().lower()
    long = long.strip().lower()
    if len(short.split()) == 1 and any(c.isdigit() for c in short):
        return False
    return long == short + "s" or long == short + "es"


def _is_acronym_of(short: str, long: str) -> bool:
    """
    True if short is the initials of long's content words (legal suffixes
    stripped). 'amd' ↔ 'advanced micro devices' → True.
    Length of short ∈ [2, 7] — outside this range the false-positive rate
    on noise tokens is too high.
    """
    short_clean = "".join(_tokens(short))
    if not 2 <= len(short_clean) <= 7:
        return False
    words = [w for w in _tokens(long) if w not in LEGAL_SUFFIXES]
    if len(words) < 2:
        return False
    initials = "".join(w[0] for w in words if w)
    return initials == short_clean


def _is_candidate_without_cosine(name_a: str, name_b: str) -> bool:
    """Cheap lexical checks used before applying the cosine cutoff."""
    short, long = sorted([name_a, name_b], key=len)
    return (
        _is_normalized_string_variant(name_a, name_b)
        or _is_plural_variant(short, long)
        or _is_acronym_of(short, long)
    )


def _composite_score(
    name_a: str,
    name_b: str,
    cosine: float,
    entity_type: Optional[str] = None,
) -> tuple[bool, float, str]:
    """
    Decide if a pair is a synonym + which rule fired.

    Returns:
        (is_synonym, score, rule_name)
    """
    short, long = sorted([name_a, name_b], key=len)
    tokens_short = set(_tokens(short))
    tokens_long = set(_tokens(long))

    # Rule 1: Separator/format variant.
    # Catches: 'global foundries' ↔ 'globalfoundries',
    #          'united states' ↔ 'united_states',
    #          'high power modules' ↔ 'high-power modules'.
    # Rejects: 'zen 3' ↔ 'zen 3+' because plus marks a distinct product family.
    if _is_normalized_string_variant(name_a, name_b) and _digits_match(name_a, name_b):
        return True, max(cosine, 0.98), "normalized_string"

    # Rule 2: Legal-suffix paraphrase
    # shorter's tokens ⊂ longer's tokens AND extra tokens are ALL legal suffixes
    # Catches: 'nvidia' ↔ 'nvidia corporation', 'amd' ↔ 'amd inc'
    # Rejects: 'blackwell' ↔ 'blackwell architecture' (extra='architecture' not legal)
    if tokens_short and tokens_short.issubset(tokens_long):
        extra = tokens_long - tokens_short
        allowed_suffixes: frozenset[str]
        if entity_type == "SEGMENT":
            allowed_suffixes = frozenset({"group"})
        elif entity_type is None or entity_type in {"ORG", "COMP"}:
            allowed_suffixes = LEGAL_SUFFIXES
        else:
            allowed_suffixes = frozenset()
        if extra and extra.issubset(allowed_suffixes) and cosine >= 0.80:
            return True, max(cosine, 0.95), "legal_suffix"

    # Rule 3: Acronym (abbreviation pattern)
    # Catches: 'amd' ↔ 'advanced micro devices',
    #          'hbm' ↔ 'high-bandwidth memory'.
    # Two-letter acronyms are more collision-prone, so they need higher cosine.
    short_clean = "".join(_tokens(short))
    acronym_min_cosine = 0.80 if len(short_clean) <= 2 else 0.60
    acronym_type_allowed = entity_type is None or entity_type in ACRONYM_SYNONYMY_TYPES
    if acronym_type_allowed and _is_acronym_of(short, long) and cosine >= acronym_min_cosine:
        return True, 0.90, "acronym"

    # Rule 4: Plural variant ('s' or 'es' suffix only)
    # Catches: 'gpu' ↔ 'gpus', 'blackwell architecture' ↔ 'blackwell architectures'
    # Rejects: 'h20' ↔ 'h200' (digit suffix not plural), 'l40' ↔ 'l40s'
    if _is_plural_variant(short, long) and cosine >= 0.75:
        return True, 0.92, "plural"

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
            a, b = names[i], names[j]
            if c < cosine_min and not _is_candidate_without_cosine(a, b):
                continue
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
        is_syn, score, rule = _composite_score(a, b, cos, entity_type=t)
        if is_syn:
            syns.append({
                "name_a": a, "name_b": b, "type": t,
                "cosine": cos, "score": score, "rule": rule,
            })

    acronym_expansions: dict[tuple[str, str], set[str]] = {}
    for s in syns:
        if s["rule"] != "acronym":
            continue
        short, long = sorted([s["name_a"], s["name_b"]], key=len)
        key = (s["type"], _canonical_key(short))
        acronym_expansions.setdefault(key, set()).add(_canonical_key(long))

    ambiguous = {
        key for key, expansions in acronym_expansions.items()
        if len(expansions) > 1
    }
    if not ambiguous:
        return syns

    filtered: list[dict] = []
    for s in syns:
        if s["rule"] != "acronym":
            filtered.append(s)
            continue
        short, _long = sorted([s["name_a"], s["name_b"]], key=len)
        if (s["type"], _canonical_key(short)) not in ambiguous:
            filtered.append(s)
    return filtered


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
