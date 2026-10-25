"""Single SDK ingestion flow from text to search-ready Neo4j data."""

from __future__ import annotations

import hashlib
import json
import math
import threading
from dataclasses import dataclass, field
from typing import Any

from neo4j import Driver

from ..config import SDKConfig
from .embedding import Embedder
from .extract import LLMExtractor
from .finalize import ensure_existing_projection, finalize_batch
from .identity import chunk_identity, normalize_text
from .models import (
    BatchStatus,
    ExtractionDocument,
    FailureKind,
    IngestionReport,
    IngestionStage,
    ItemOutcome,
    ItemStatus,
    ValidatedExtraction,
)
from .store import (
    corpus_state,
    decode_checkpoint,
    load_checkpoint,
    mark_search_not_ready,
    publish_chunk,
    save_validated_checkpoint,
)
from .validate import validate_extraction


EMBEDDING_REQUEST_BATCH_SIZE = 64
PIPELINE_VERSION = 1

_LOCKS_GUARD = threading.Lock()
_WORKSPACE_LOCKS: dict[str, threading.RLock] = {}


@dataclass
class _PendingItem:
    input_index: int
    chunk_id: str
    text: str
    extraction: ValidatedExtraction
    embedding_keys: set[str] = field(default_factory=set)


def _workspace_lock(workspace_id: str) -> threading.RLock:
    with _LOCKS_GUARD:
        return _WORKSPACE_LOCKS.setdefault(workspace_id, threading.RLock())


def _pipeline_fingerprint(
    config: SDKConfig, extractor: LLMExtractor | None
) -> str:
    if config.llm is not None:
        llm_identity: Any = config.llm.model_dump(mode="json")
    elif extractor is not None:
        llm_identity = (
            f"{extractor.__class__.__module__}.{extractor.__class__.__qualname__}"
        )
    else:
        llm_identity = "not-configured"
    payload = {
        "pipeline_version": PIPELINE_VERSION,
        "embedding_fingerprint": config.embedding.fingerprint,
        "llm": llm_identity,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _record_failure(
    outcomes: dict[int, ItemOutcome],
    *,
    input_index: int,
    chunk_id: str | None,
    stage: IngestionStage,
    kind: FailureKind,
    error: Exception | str,
    warnings: list[str] | None = None,
) -> None:
    message = str(error)
    outcomes[input_index] = ItemOutcome(
        input_index=input_index,
        chunk_id=chunk_id,
        status=ItemStatus.FAILED,
        last_completed_stage=stage,
        warnings=warnings or [],
        failure_kind=kind,
        error=message,
    )


def _required_embeddings(item: _PendingItem) -> dict[str, str]:
    required = {f"chunk\0{item.chunk_id}": item.text}
    for entity in item.extraction.entities:
        required[f"entity\0{entity.name}\0{entity.type}"] = (
            f"{entity.name} ({entity.type})"
        )
    for assertion in item.extraction.assertions:
        required[f"triple\0{assertion.triple_text}"] = assertion.triple_text
    item.embedding_keys = set(required)
    return required


def _build_embeddings(
    items: list[_PendingItem],
    embedder: Embedder,
    dimension: int,
    outcomes: dict[int, ItemOutcome],
) -> dict[str, list[float]]:
    """Encode unique text values in bounded batches and isolate bad inputs."""
    item_by_id = {item.chunk_id: item for item in items}
    item_requirements = {
        item.chunk_id: _required_embeddings(item) for item in items
    }
    key_dependencies: dict[str, set[str]] = {}
    key_to_text: dict[str, str] = {}
    for chunk_id, requirements in item_requirements.items():
        for key, text in requirements.items():
            key_to_text[key] = text
            key_dependencies.setdefault(key, set()).add(chunk_id)

    text_to_keys: dict[str, set[str]] = {}
    for key, text in key_to_text.items():
        text_to_keys.setdefault(text, set()).add(key)

    failed_chunks: set[str] = set()
    validate_text = getattr(embedder, "validate_text", None)
    if callable(validate_text):
        for text in sorted(text_to_keys):
            try:
                valid = validate_text(text)
                if valid is False:
                    raise ValueError("embedder rejected the input text")
            except Exception as exc:
                keys = text_to_keys[text]
                affected = set().union(*(key_dependencies[key] for key in keys))
                for chunk_id in sorted(affected):
                    item = item_by_id[chunk_id]
                    _record_failure(
                        outcomes,
                        input_index=item.input_index,
                        chunk_id=chunk_id,
                        stage=IngestionStage.CHECKPOINT,
                        kind=FailureKind.EMBEDDING_FAILED,
                        error=exc,
                        warnings=item.extraction.warnings,
                    )
                failed_chunks.update(affected)

    active_chunks = set(item_by_id) - failed_chunks
    active_keys = {
        key
        for chunk_id in active_chunks
        for key in item_requirements[chunk_id]
    }
    active_texts: dict[str, set[str]] = {}
    for key in active_keys:
        active_texts.setdefault(key_to_text[key], set()).add(key)

    vectors_by_text: dict[str, list[float]] = {}
    ordered_texts = sorted(active_texts)
    for start in range(0, len(ordered_texts), EMBEDDING_REQUEST_BATCH_SIZE):
        batch = ordered_texts[start : start + EMBEDDING_REQUEST_BATCH_SIZE]
        try:
            vectors = list(embedder.embed(batch))
            if len(vectors) != len(batch):
                raise ValueError(
                    f"embedder returned {len(vectors)} vectors for {len(batch)} texts"
                )
        except Exception as exc:
            affected = set()
            for text in batch:
                for key in active_texts[text]:
                    affected.update(key_dependencies[key])
            for chunk_id in sorted(affected):
                if chunk_id in failed_chunks:
                    continue
                item = item_by_id[chunk_id]
                _record_failure(
                    outcomes,
                    input_index=item.input_index,
                    chunk_id=chunk_id,
                    stage=IngestionStage.CHECKPOINT,
                    kind=FailureKind.EMBEDDING_FAILED,
                    error=exc,
                    warnings=item.extraction.warnings,
                )
            failed_chunks.update(affected)
            continue

        for text, vector in zip(batch, vectors, strict=True):
            try:
                values = [float(value) for value in vector]
                if len(values) != dimension:
                    raise ValueError(
                        f"embedding dimension {len(values)} does not match "
                        f"configured dimension {dimension}"
                    )
                if not all(math.isfinite(value) for value in values):
                    raise ValueError("embedding contains a non-finite value")
                vectors_by_text[text] = values
            except Exception as exc:
                affected = set()
                for key in active_texts[text]:
                    affected.update(key_dependencies[key])
                for chunk_id in sorted(affected):
                    if chunk_id in failed_chunks:
                        continue
                    item = item_by_id[chunk_id]
                    _record_failure(
                        outcomes,
                        input_index=item.input_index,
                        chunk_id=chunk_id,
                        stage=IngestionStage.CHECKPOINT,
                        kind=FailureKind.EMBEDDING_FAILED,
                        error=exc,
                        warnings=item.extraction.warnings,
                    )
                failed_chunks.update(affected)

    output: dict[str, list[float]] = {}
    for key in active_keys:
        text = key_to_text[key]
        vector = vectors_by_text.get(text)
        if vector is not None:
            output[key] = vector
    for chunk_id in failed_chunks:
        item = item_by_id[chunk_id]
        for key in item.embedding_keys:
            output.pop(key, None)
    return output


def _duplicate_outcomes(
    outcomes: dict[int, ItemOutcome], duplicates: dict[int, int]
) -> None:
    for duplicate_index, primary_index in duplicates.items():
        primary = outcomes[primary_index]
        if primary.status == ItemStatus.FAILED:
            outcomes[duplicate_index] = ItemOutcome(
                input_index=duplicate_index,
                chunk_id=primary.chunk_id,
                status=ItemStatus.FAILED,
                last_completed_stage=primary.last_completed_stage,
                warnings=primary.warnings,
                failure_kind=primary.failure_kind,
                error=primary.error,
                duplicate_of_index=primary_index,
            )
        else:
            outcomes[duplicate_index] = ItemOutcome(
                input_index=duplicate_index,
                chunk_id=primary.chunk_id,
                status=ItemStatus.SKIPPED,
                last_completed_stage=primary.last_completed_stage,
                warnings=primary.warnings,
                duplicate_of_index=primary_index,
            )


def ingest_texts(
    driver: Driver,
    config: SDKConfig,
    texts: list[str],
    *,
    extractor: LLMExtractor | None,
    embedder: Embedder | None,
) -> IngestionReport:
    """Ingest plain text and return per-input progress and readiness."""
    if not isinstance(texts, list):
        raise TypeError("Engine.ingest expects a list of text chunks")
    if any(isinstance(value, str) and normalize_text(value).strip() for value in texts):
        if extractor is None:
            raise ValueError("A valid text chunk needs a configured LLM extractor")
        if embedder is None:
            raise ValueError("A valid text chunk needs a configured embedder")
    database = config.database.name
    outcomes: dict[int, ItemOutcome] = {}
    unique_inputs: dict[str, tuple[int, str]] = {}
    duplicates: dict[int, int] = {}

    for index, value in enumerate(texts):
        if not isinstance(value, str) or not normalize_text(value).strip():
            _record_failure(
                outcomes,
                input_index=index,
                chunk_id=None,
                stage=IngestionStage.INPUT,
                kind=FailureKind.INVALID_INPUT,
                error="Chunk text must be a non-empty string",
            )
            continue
        normalized = normalize_text(value)
        chunk_id = chunk_identity(normalized)
        if chunk_id in unique_inputs:
            duplicates[index] = unique_inputs[chunk_id][0]
        else:
            unique_inputs[chunk_id] = (index, normalized)

    if not texts:
        state = corpus_state(driver, database)
        return IngestionReport(
            status=BatchStatus.COMPLETE,
            input_count=0,
            inserted_count=0,
            skipped_count=0,
            failed_count=0,
            search_ready=state["search_ready"],
            corpus_revision=state["corpus_revision"],
            outcomes=[],
        )

    with _workspace_lock(config.workspace_id):
        fingerprint = _pipeline_fingerprint(config, extractor)
        pending: list[_PendingItem] = []
        for chunk_id, (index, normalized) in sorted(
            unique_inputs.items(), key=lambda entry: entry[0]
        ):
            try:
                checkpoint = load_checkpoint(driver, database, chunk_id)
            except Exception as exc:
                _record_failure(
                    outcomes,
                    input_index=index,
                    chunk_id=chunk_id,
                    stage=IngestionStage.INPUT,
                    kind=FailureKind.STORAGE_FAILED,
                    error=exc,
                )
                continue

            if (
                checkpoint
                and checkpoint["fingerprint"] == fingerprint
                and checkpoint["status"] == "COMPLETE"
                and checkpoint["chunk_exists"]
            ):
                try:
                    extraction = decode_checkpoint(checkpoint["extraction_json"])
                except Exception as exc:
                    _record_failure(
                        outcomes,
                        input_index=index,
                        chunk_id=chunk_id,
                        stage=IngestionStage.CHECKPOINT,
                        kind=FailureKind.VALIDATION_FAILED,
                        error=f"Stored checkpoint is invalid: {exc}",
                    )
                    continue
                outcomes[index] = ItemOutcome(
                    input_index=index,
                    chunk_id=chunk_id,
                    status=ItemStatus.SKIPPED,
                    last_completed_stage=IngestionStage.COMPLETE,
                    warnings=extraction.warnings,
                )
                continue

            if (
                checkpoint
                and checkpoint["fingerprint"] == fingerprint
                and checkpoint["extraction_json"]
            ):
                try:
                    extraction = decode_checkpoint(checkpoint["extraction_json"])
                except Exception as exc:
                    _record_failure(
                        outcomes,
                        input_index=index,
                        chunk_id=chunk_id,
                        stage=IngestionStage.CHECKPOINT,
                        kind=FailureKind.VALIDATION_FAILED,
                        error=f"Stored checkpoint is invalid: {exc}",
                    )
                    continue
            else:
                try:
                    if extractor is None:
                        raise ValueError("No LLM extractor is configured")
                    raw = extractor.extract(normalized)
                    document = ExtractionDocument.model_validate(raw)
                except Exception as exc:
                    _record_failure(
                        outcomes,
                        input_index=index,
                        chunk_id=chunk_id,
                        stage=IngestionStage.INPUT,
                        kind=FailureKind.EXTRACTION_FAILED,
                        error=exc,
                    )
                    continue
                try:
                    extraction = validate_extraction(document, normalized, chunk_id)
                except Exception as exc:
                    _record_failure(
                        outcomes,
                        input_index=index,
                        chunk_id=chunk_id,
                        stage=IngestionStage.EXTRACTION,
                        kind=FailureKind.VALIDATION_FAILED,
                        error=exc,
                    )
                    continue
                try:
                    save_validated_checkpoint(
                        driver, database, chunk_id, fingerprint, extraction
                    )
                except Exception as exc:
                    _record_failure(
                        outcomes,
                        input_index=index,
                        chunk_id=chunk_id,
                        stage=IngestionStage.VALIDATION,
                        kind=FailureKind.STORAGE_FAILED,
                        error=exc,
                    )
                    continue
            pending.append(
                _PendingItem(
                    input_index=index,
                    chunk_id=chunk_id,
                    text=normalized,
                    extraction=extraction,
                )
            )

        inserted_count = 0
        if pending:
            if embedder is None:
                raise ValueError("No embedder is configured")
            vectors = _build_embeddings(
                pending, embedder, config.embedding.dimension, outcomes
            )
            ready_items = [
                item
                for item in pending
                if item.input_index not in outcomes
                and all(key in vectors for key in item.embedding_keys)
            ]
            if ready_items:
                try:
                    mark_search_not_ready(driver, database)
                except Exception as exc:
                    for item in ready_items:
                        _record_failure(
                            outcomes,
                            input_index=item.input_index,
                            chunk_id=item.chunk_id,
                            stage=IngestionStage.EMBEDDING,
                            kind=FailureKind.STORAGE_FAILED,
                            error=exc,
                            warnings=item.extraction.warnings,
                        )
                    ready_items = []

            for item in sorted(ready_items, key=lambda value: value.chunk_id):
                try:
                    publish_chunk(
                        driver,
                        database,
                        chunk_id=item.chunk_id,
                        text=item.text,
                        chunk_embedding=vectors[f"chunk\0{item.chunk_id}"],
                        pipeline_fingerprint=fingerprint,
                        extraction=item.extraction,
                        embeddings_by_text=vectors,
                    )
                    inserted_count += 1
                    outcomes[item.input_index] = ItemOutcome(
                        input_index=item.input_index,
                        chunk_id=item.chunk_id,
                        status=ItemStatus.COMPLETE,
                        last_completed_stage=IngestionStage.STORAGE,
                        warnings=item.extraction.warnings,
                    )
                except Exception as exc:
                    _record_failure(
                        outcomes,
                        input_index=item.input_index,
                        chunk_id=item.chunk_id,
                        stage=IngestionStage.EMBEDDING,
                        kind=FailureKind.STORAGE_FAILED,
                        error=exc,
                        warnings=item.extraction.warnings,
                    )

        _duplicate_outcomes(outcomes, duplicates)
        state = corpus_state(driver, database)
        valid_input_exists = bool(unique_inputs)
        try:
            if inserted_count or (not state["search_ready"] and state["chunk_count"]):
                finalized = finalize_batch(driver, config)
                state = corpus_state(driver, database)
            elif valid_input_exists and state["search_ready"]:
                ensure_existing_projection(driver, config)
                finalized = None
            else:
                finalized = None
        except Exception as exc:
            if inserted_count or state["chunk_count"]:
                try:
                    mark_search_not_ready(driver, database)
                except Exception:
                    pass
            for index, outcome in list(outcomes.items()):
                if outcome.status == ItemStatus.FAILED:
                    continue
                _record_failure(
                    outcomes,
                    input_index=index,
                    chunk_id=outcome.chunk_id,
                    stage=IngestionStage.STORAGE,
                    kind=FailureKind.FINALIZATION_FAILED,
                    error=exc,
                    warnings=outcome.warnings,
                )
            state = corpus_state(driver, database)

        _duplicate_outcomes(outcomes, duplicates)
        ordered_outcomes = [outcomes[index] for index in range(len(texts))]
        failed_count = sum(
            outcome.status == ItemStatus.FAILED for outcome in ordered_outcomes
        )
        skipped_count = sum(
            outcome.status == ItemStatus.SKIPPED for outcome in ordered_outcomes
        )
        status = (
            BatchStatus.FAILED
            if failed_count == len(texts) or not state["search_ready"]
            else BatchStatus.PARTIAL
            if failed_count
            else BatchStatus.COMPLETE
        )
        return IngestionReport(
            status=status,
            input_count=len(texts),
            inserted_count=inserted_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            search_ready=state["search_ready"],
            corpus_revision=state["corpus_revision"],
            outcomes=ordered_outcomes,
        )
