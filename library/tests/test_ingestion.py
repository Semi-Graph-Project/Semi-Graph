"""Unit coverage for Free Ontology ingestion contracts without external APIs."""

import json
from types import SimpleNamespace

import pytest

from semigraph_sdk.ingestion.extract import ExtractionError, StructuredLLMExtractor
from semigraph_sdk.ingestion.identity import chunk_identity, normalize_text
from semigraph_sdk.ingestion.models import (
    ExtractionDocument,
    ResolvedAssertion,
    ValidatedExtraction,
)
from semigraph_sdk.ingestion.pipeline import _PendingItem, _build_embeddings
from semigraph_sdk.ingestion.validate import (
    RELATIONSHIP_TYPE,
    canonicalize_relationship,
    validate_extraction,
)


def test_nfc_identity_and_stored_text_use_the_same_normalized_form():
    composed = "café ใช้ปั๊ม P7"
    decomposed = "cafe\u0301 ใช้ปั๊ม P7"
    assert normalize_text(composed) == normalize_text(decomposed)
    assert chunk_identity(normalize_text(composed)) == chunk_identity(
        normalize_text(decomposed)
    )


def test_quote_resolution_ignores_wrong_offsets_and_filters_invalid_assertions():
    text = "บริษัท A ใช้ปั๊ม P7 กับซีลเซรามิก"
    document = ExtractionDocument.model_validate(
        {
            "entities": [
                {
                    "id": "company",
                    "name": "บริษัท A",
                    "type": "Organization",
                    "evidence_quote": "บริษัท A",
                    "start": 900,
                    "end": 908,
                },
                {
                    "id": "pump",
                    "name": "ปั๊ม P7",
                    "type": "Equipment",
                    "evidence_quote": "ปั๊ม P7",
                },
                {
                    "id": "missing",
                    "name": "ซีลปลอม",
                    "type": "Part",
                    "evidence_quote": "ซีลปลอม",
                },
            ],
            "assertions": [
                {
                    "head_id": "company",
                    "relation": "uses Pump",
                    "relation_description": "องค์กรใช้อุปกรณ์",
                    "tail_id": "pump",
                    "evidence_quote": "ใช้ปั๊ม P7",
                    "start": 0,
                    "end": 1,
                },
                {
                    "head_id": "company",
                    "relation": "HAS_PART",
                    "tail_id": "missing",
                    "evidence_quote": "ซีลเซรามิก",
                },
                {
                    "head_id": "company",
                    "relation": "HAS_PART",
                    "tail_id": "pump",
                    "evidence_quote": "ข้อความที่แต่งขึ้น",
                },
                {
                    "head_id": "company",
                    "relation": "!!!",
                    "tail_id": "pump",
                    "evidence_quote": "บริษัท A",
                },
            ],
        }
    )

    result = validate_extraction(document, normalize_text(text), "sgc_test")

    assert {entity.name for entity in result.entities} == {"บริษัท A", "ปั๊ม P7"}
    assert len(result.assertions) == 1
    assertion = result.assertions[0]
    assert assertion.relation_type == "USES_PUMP"
    assert text[assertion.start : assertion.end] == assertion.evidence_quote
    assert len(result.warnings) == 4
    assert RELATIONSHIP_TYPE.fullmatch(assertion.relation_type)


def test_repeated_quote_requires_a_valid_offset_hint_and_bad_hints_are_ignored():
    text = "P7 / P7"
    document = ExtractionDocument.model_validate(
        {
            "entities": [
                {
                    "id": "p7",
                    "name": "P7",
                    "type": "Equipment",
                    "evidence_quote": "P7",
                    "start": 5,
                    "end": 7,
                },
                {
                    "id": "p7-ambiguous",
                    "name": "P7 other",
                    "type": "Equipment",
                    "evidence_quote": "P7",
                    "start": "bad offset",
                    "end": 2,
                },
            ],
            "assertions": [],
        }
    )

    result = validate_extraction(document, text, "sgc_test")

    assert len(result.entities) == 1
    assert result.entities[0].start == 5
    assert result.entities[0].end == 7
    assert len(result.warnings) == 1


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("uses material", "USES_MATERIAL"),
        ("hasPart", "HAS_PART"),
        ("USES_MATERIAL", "USES_MATERIAL"),
        ("A", None),
        ("x" * 65, None),
        ("ภาษาไทย", None),
    ],
)
def test_relationship_types_are_canonical_and_bounded(source, expected):
    result = canonicalize_relationship(source)
    assert result == expected
    if result is not None:
        assert RELATIONSHIP_TYPE.fullmatch(result)


def test_resolved_assertion_rejects_noncanonical_relationship_before_storage():
    with pytest.raises(ValueError, match="safe UPPER_SNAKE_CASE"):
        ResolvedAssertion(
            assertion_id="assertion",
            head_key="head",
            relation_type="CALL db.labels()",
            tail_key="tail",
            evidence_quote="evidence",
            start=0,
            end=8,
            triple_text="head relation tail",
        )


def test_structured_extractor_rejects_malformed_json():
    class Client:
        def invoke(self, _messages):
            return SimpleNamespace(content="not json")

    with pytest.raises(ExtractionError, match="invalid structured data"):
        StructuredLLMExtractor(Client()).extract("plain text")


def test_structured_extractor_parses_a_successful_free_ontology_response():
    class Client:
        def invoke(self, _messages):
            return SimpleNamespace(content=json.dumps({
                "entities": [{
                    "id": "e1", "name": "Pump P7", "type": "Equipment",
                    "evidence_quote": "Pump P7",
                }],
                "assertions": [],
            }))

    result = StructuredLLMExtractor(Client()).extract("Pump P7 uses a seal.")

    assert result.entities[0].name == "Pump P7"
    assert result.assertions == []


def test_embeddings_are_deduplicated_and_sent_in_bounded_batches():
    class FakeEmbedder:
        def __init__(self):
            self.calls = []

        def embed(self, texts):
            self.calls.append(list(texts))
            return [[float(len(text)), 0.0] for text in texts]

    empty = ValidatedExtraction(entities=[], assertions=[])
    items = [
        _PendingItem(i, f"chunk-{i:02}", "same text", empty)
        for i in range(65)
    ]
    embedder = FakeEmbedder()

    vectors = _build_embeddings(items, embedder, 2, outcomes={})

    assert [len(call) for call in embedder.calls] == [1]
    assert len(vectors) == 65
    assert all(vectors[f"chunk\0chunk-{i:02}"] == [9.0, 0.0] for i in range(65))


def test_embeddings_split_unique_texts_at_request_batch_limit():
    class FakeEmbedder:
        def __init__(self):
            self.calls = []

        def embed(self, texts):
            self.calls.append(list(texts))
            return [[1.0, 0.0] for _ in texts]

    empty = ValidatedExtraction(entities=[], assertions=[])
    items = [
        _PendingItem(i, f"chunk-{i:03}", f"unique text {i}", empty)
        for i in range(65)
    ]
    embedder = FakeEmbedder()

    _build_embeddings(items, embedder, 2, outcomes={})

    assert [len(call) for call in embedder.calls] == [64, 1]


def test_embedding_failure_is_classified_per_dependent_chunk():
    class TooShortEmbedder:
        def embed(self, texts):
            return [[1.0] for _ in texts]

    empty = ValidatedExtraction(entities=[], assertions=[])
    items = [_PendingItem(0, "chunk-0", "short", empty)]
    outcomes = {}

    _build_embeddings(items, TooShortEmbedder(), 2, outcomes)

    assert outcomes[0].failure_kind.value == "EMBEDDING_FAILED"
    assert outcomes[0].chunk_id == "chunk-0"
