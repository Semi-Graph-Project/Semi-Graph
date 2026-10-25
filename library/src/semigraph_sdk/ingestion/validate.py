"""Resolve quote evidence and filter only assertions that fail validation."""

from __future__ import annotations

import re

from .identity import assertion_identity, entity_identity, normalize_text
from .models import (
    ExtractionDocument,
    RELATIONSHIP_TYPE_PATTERN,
    ResolvedAssertion,
    ResolvedEntity,
    ValidatedExtraction,
)


RELATIONSHIP_TYPE = re.compile(RELATIONSHIP_TYPE_PATTERN)


class ExtractionValidationError(ValueError):
    """The extraction cannot be interpreted without guessing its structure."""


def canonicalize_relationship(value: str) -> str | None:
    """Convert prose/camel case to a restricted, stable Cypher type name."""
    label = normalize_text(value).strip()
    label = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", label)
    label = re.sub(r"[^A-Za-z0-9]+", "_", label).strip("_").upper()
    label = re.sub(r"_+", "_", label)
    return label if RELATIONSHIP_TYPE.fullmatch(label) else None


def _find_occurrences(text: str, quote: str) -> list[int]:
    positions: list[int] = []
    position = text.find(quote)
    while position >= 0:
        positions.append(position)
        position = text.find(quote, position + 1)
    return positions


def _resolve_span(
    text: str, quote_value: str, start_hint: int | None, end_hint: int | None
) -> tuple[int, int] | None:
    quote = normalize_text(quote_value)
    if not quote:
        return None
    positions = _find_occurrences(text, quote)
    if not positions:
        return None
    if start_hint is not None and end_hint == start_hint + len(quote):
        if start_hint in positions:
            return start_hint, end_hint
    if len(positions) == 1:
        start = positions[0]
        return start, start + len(quote)
    return None


def validate_extraction(
    document: ExtractionDocument, normalized_text: str, chunk_id: str
) -> ValidatedExtraction:
    """Build verified evidence spans; invalid assertions become warnings."""
    text = normalize_text(normalized_text)
    warnings: list[str] = []
    entities_by_id: dict[str, ResolvedEntity] = {}
    entities_by_key: dict[str, ResolvedEntity] = {}

    for entity in document.entities:
        name = normalize_text(entity.name).strip()
        entity_type = normalize_text(entity.type).strip()
        if not name or not entity_type:
            raise ExtractionValidationError(
                f"Entity {entity.id!r} needs a non-empty name and type"
            )
        if entity.id in entities_by_id:
            raise ExtractionValidationError(
                f"Duplicate entity id in extraction: {entity.id!r}"
            )
        span = _resolve_span(text, entity.evidence_quote, entity.start, entity.end)
        if span is None:
            warnings.append(
                f"Entity {entity.id!r} dropped: evidence quote was not found uniquely"
            )
            continue
        key = entity_identity(name, entity_type)
        resolved = ResolvedEntity(
            entity_id=entity.id,
            name=name,
            type=entity_type,
            entity_key=key,
            evidence_quote=normalize_text(entity.evidence_quote),
            start=span[0],
            end=span[1],
        )
        entities_by_id[entity.id] = resolved
        previous = entities_by_key.get(key)
        if previous is None or (resolved.start, resolved.end) < (
            previous.start, previous.end
        ):
            entities_by_key[key] = resolved

    assertions: dict[str, ResolvedAssertion] = {}
    for index, assertion in enumerate(document.assertions):
        head = entities_by_id.get(assertion.head_id)
        tail = entities_by_id.get(assertion.tail_id)
        if head is None or tail is None:
            warnings.append(
                f"Assertion {index} dropped: endpoint references an unknown or invalid entity"
            )
            continue
        relation_type = canonicalize_relationship(assertion.relation)
        if relation_type is None:
            warnings.append(
                f"Assertion {index} dropped: relationship type is not a safe canonical name"
            )
            continue
        span = _resolve_span(text, assertion.evidence_quote, assertion.start, assertion.end)
        if span is None:
            warnings.append(
                f"Assertion {index} dropped: evidence quote was not found uniquely"
            )
            continue
        quote = normalize_text(assertion.evidence_quote)
        assertion_id = assertion_identity(
            chunk_id, head.entity_key, relation_type, tail.entity_key, quote
        )
        description = assertion.relation_description
        if description is not None:
            description = normalize_text(description).strip() or None
        triple_text = (
            f"{head.name} {relation_type.lower().replace('_', ' ')} {tail.name}"
        )
        assertions[assertion_id] = ResolvedAssertion(
            assertion_id=assertion_id,
            head_key=head.entity_key,
            relation_type=relation_type,
            relation_description=description,
            tail_key=tail.entity_key,
            evidence_quote=quote,
            start=span[0],
            end=span[1],
            triple_text=triple_text,
        )

    return ValidatedExtraction(
        entities=sorted(entities_by_key.values(), key=lambda item: item.entity_key),
        assertions=sorted(assertions.values(), key=lambda item: item.assertion_id),
        warnings=warnings,
    )
