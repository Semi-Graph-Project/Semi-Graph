"""Stable NFC-based identities for chunks, entities and assertions."""

from __future__ import annotations

import hashlib
import unicodedata


def normalize_text(text: str) -> str:
    """Return the one normalized text representation used by the pipeline."""
    if not isinstance(text, str):
        raise TypeError("chunk text must be a string")
    return unicodedata.normalize("NFC", text)


def _digest(namespace: str, value: str) -> str:
    payload = f"semigraph-sdk:{namespace}:v1\0{value}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def chunk_identity(normalized_text: str) -> str:
    return f"sgc_{_digest('chunk', normalized_text)}"


def entity_identity(name: str, entity_type: str) -> str:
    key = f"{normalize_text(name).strip()}\0{normalize_text(entity_type).strip()}"
    return f"sge_{_digest('entity', key)}"


def assertion_identity(
    chunk_id: str,
    head_key: str,
    relation_type: str,
    tail_key: str,
    evidence_quote: str,
) -> str:
    key = "\0".join(
        (chunk_id, head_key, relation_type, tail_key, normalize_text(evidence_quote))
    )
    return f"sga_{_digest('assertion', key)}"
