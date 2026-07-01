"""Deterministic entity-name normalization for KG extraction.

The LLM prompt asks for canonical names, but graph quality should not depend
on the model following that instruction perfectly. These helpers apply only
low-risk canonicalization that is stable across semiconductor filings.

WTF it's HardCode
"""
from __future__ import annotations

import re


LEGAL_SUFFIXES: frozenset[str] = frozenset({
    "inc",
    "incorporated",
    "corp",
    "corporation",
    "co",
    "company",
    "ltd",
    "limited",
    "llc",
    "plc",
    "holdings",
    "holding",
    "group",
    "ag",
    "nv",
    "sa",
})

_PUBLIC_COMPANY_ALIASES: dict[str, str] = {
    "advanced micro devices inc": "advanced micro devices",
    "advanced micro devices incorporated": "advanced micro devices",
    "advanced micro devices": "advanced micro devices",
    "nvidia corporation": "nvidia",
    "nvidia corp": "nvidia",
    "micron technology inc": "micron",
    "micron technology": "micron",
    "intel corporation": "intel",
    "intel corp": "intel",
    "taiwan semiconductor manufacturing company": "tsmc",
    "taiwan semiconductor manufacturing co": "tsmc",
    "taiwan semiconductor manufacturing": "tsmc",
    "tsmc limited": "tsmc",
    "sk hynix inc": "sk hynix",
    "samsung electronics co ltd": "samsung electronics",
    "lam research corporation": "lam research",
    "kla corporation": "kla",
    "applied materials inc": "applied materials",
}

_PRODUCT_ALIASES: dict[str, str] = {
    "amd instinct accelerators": "amd instinct",
    "instinct accelerators": "amd instinct",
    "instinct accelerator": "amd instinct",
    "instinct": "amd instinct",
    "geforce rtx series": "geforce rtx",
    "nvidia rtx series": "geforce rtx",
    "rtx series": "geforce rtx",
    "rtx": "geforce rtx",
    "xeon scalable processors": "xeon scalable",
    "xeon scalable processor": "xeon scalable",
    "intel xeon scalable processors": "xeon scalable",
    "intel xeon scalable processor": "xeon scalable",
}

_REGULATION_ALIASES: dict[str, str] = {
    "chips and science act": "chips act",
    "u s chips act": "chips act",
    "us chips act": "chips act",
    "export control": "export controls",
}

_EVENT_ALIASES: dict[str, str] = {
    "smart capital program": "smart capital",
    "smart capital strategy": "smart capital",
}

_ALIASES_BY_TYPE: dict[str, dict[str, str]] = {
    "ORG": _PUBLIC_COMPANY_ALIASES,
    "COMP": _PUBLIC_COMPANY_ALIASES,
    "PRODUCT": _PRODUCT_ALIASES,
    "REGULATORY_REQUIREMENT": _REGULATION_ALIASES,
    "RISK_FACTOR": _REGULATION_ALIASES,
    "EVENT": _EVENT_ALIASES,
}


def _basic_clean(value: str) -> str:
    """Lowercase and remove punctuation that only fragments entity names."""
    text = value.strip().strip("\"'").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[()\[\]{}]", " ", text)
    text = re.sub(r"[.,;:]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _strip_legal_suffixes(name: str) -> str:
    words = name.split()
    while words and words[-1] in LEGAL_SUFFIXES:
        words.pop()
    return " ".join(words)


def normalize_entity_name(value: str, entity_type: str | None = None) -> str:
    """Return the canonical entity name used as Neo4j Entity.name.

    The function is intentionally conservative: it handles punctuation, legal
    suffixes, and a small curated alias table for entities already present in
    the Phase T benchmark. It does not infer facts from context.
    """
    name = _basic_clean(value)
    if not name:
        return ""

    aliases = _ALIASES_BY_TYPE.get(entity_type or "", {})
    if name in aliases:
        return aliases[name]

    if entity_type in {"ORG", "COMP"}:
        stripped = _strip_legal_suffixes(name)
        return aliases.get(stripped, stripped)

    return aliases.get(name, name)


def is_known_product_name(name: str) -> bool:
    """True for product aliases that often get mislabeled as organizations."""
    canonical = normalize_entity_name(name, "PRODUCT")
    return canonical in set(_PRODUCT_ALIASES.values()) or canonical in {
        "blackwell",
        "hopper",
        "hbm",
        "hbm3e",
        "radeon",
        "ryzen",
        "epyc",
        "xeon scalable",
        "geforce rtx",
        "amd instinct",
    }
