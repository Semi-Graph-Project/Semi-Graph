# Spec 02 — Free Ontology ingestion

Status: implemented; unit and live Neo4j smoke checks passed 2026-10-25.

## Public contract

`Engine.ingest(texts: list[str]) -> IngestionReport` accepts plain text chunks. The caller supplies no chunk IDs, entity catalog, relationship catalog, ticker, fiscal year or filing sections. An empty list is a no-op. Invalid or blank entries are reported by input position; valid entries continue independently. Duplicate inputs share one stored chunk and retain per-position outcomes.

The report records `complete`, `partial` or `failed`, input/inserted/skipped/failed counts, `search_ready`, corpus revision and one outcome per input position. Each item reports its content ID, last completed stage, warnings and classified failure when present.

## Text identity and evidence

- Normalize input to Unicode NFC once; use that exact normalized string for hashing, extraction, stored text, evidence resolution and embedding.
- Derive a namespaced SHA256 chunk ID from normalized UTF-8 text. Re-ingestion of the same normalized text is idempotent; changed text creates another additive chunk.
- The extractor returns entity IDs, names, types, directed assertions and `evidence_quote` strings. LLM-provided offsets are hints only. Resolve quotes by Python search in normalized text; use a valid hint only to disambiguate repeated quotes. Drop only an assertion with an unknown endpoint or unresolved quote and add a warning. Malformed extraction structure/JSON fails that chunk.
- Canonicalize each relationship type to `UPPER_SNAKE_CASE` and accept it only when it matches `^[A-Z][A-Z0-9_]{1,63}$`. Store only the canonical type. Keep database writes parameterized, including APOC's relationship-type argument.
- A valid extraction with no entities/assertions remains searchable by Vector. Similarity alone does not merge entities or relations.

## Pipeline and storage

1. Validate input, normalize text, derive ID and compare pipeline/model fingerprints with prior item state.
2. Reuse a matching validated checkpoint or call the injected `LLMExtractor` protocol. Parse structured output, resolve quotes and keep valid assertions with per-item warnings.
3. Persist validated extraction JSON in an SDK-owned, non-searchable `IngestionCheckpoint` record before embedding. A retry after an embedding or publication failure can therefore skip the LLM call. Checkpoint identity is unique by chunk ID and extraction fingerprint.
4. Build texts for the chunk, unique entities and assertions; send them to the injected `Embedder` in bounded batches. Require the configured vector dimension and finite numeric values.
5. Publish each chunk, its `MENTIONS` links and source-scoped assertions in one Neo4j transaction. Sort entity keys and assertion IDs before writes. A transient write failure leaves the validated checkpoint for retry.
6. Finalize the batch: wait for configured vector indexes, refresh observed relation descriptions and entity specificity, invalidate any SDK retrieval cache, drop/recreate the workspace's GDS projection, and update corpus revision/readiness. If finalization fails, readiness stays false.

The checkpoint is stored in Neo4j. If Neo4j is unavailable before the extraction checkpoint is persisted, a later retry may repeat that LLM call; v1 does not add a separate local journal. A version-1 SDK database is upgraded additively for the checkpoint constraint without deleting data.

## Failure and readiness

Use explicit `FailureKind` values: `INVALID_INPUT`, `EXTRACTION_FAILED`, `VALIDATION_FAILED`, `EMBEDDING_FAILED`, `STORAGE_FAILED`, and `FINALIZATION_FAILED`. Invalid assertions are warnings, not chunk failures. Successful chunks remain published when siblings fail. The report is `partial` when at least one item failed but finalization succeeds. Query readiness is true only after indexes and projection are ready for the published revision.

`ensure_projection()` is idempotent and callable during finalization and later query setup, because GDS projections are in RAM and disappear after Neo4j restarts. A missing projection is recreated; a projection error keeps the SDK metadata not-ready.

## Test seams and boundaries

- Define small protocols for extraction and embedding; unit tests inject deterministic fakes.
- Never import the original project's global config, financial ontology, model singleton or PPR relation list. All new source remains under `library/`.
- Preserve the configured `BAAI/bge-base-en-v1.5` 768-dimensional default for the existing RAGTEST workspace; new workspaces can configure a multilingual model and its matching dimension.
- This stage provides ingestion/finalization and projection lifecycle only. Vector/Graph retrieval algorithms and `Engine.query()` belong to Spec 03.

## Implementation plan

1. [x] Finalize this spec and update ADR identity/checkpoint migration decisions.
2. [x] Add NFC identity, result/error models, extraction/embedding protocols and evidence validation.
3. [x] Add additive schema migration and deterministic checkpoint/chunk/assertion writes.
4. [x] Add bounded batch embedding, batch finalization, specificity and idempotent projection management.
5. [x] Expose `Engine.ingest` and update the user README with setup → configure LLM → ingest.
6. [x] Run SDK unit tests and live Neo4j smoke checks for persisted vectors, graph links, readiness, retry idempotency and projection recovery.

## Done when

Plain text becomes searchable without an ontology; NFC-equivalent text is idempotent; every published assertion has verified evidence; invalid assertions are isolated as warnings; retries reuse validated extraction; batches publish deterministically; relation names are safe/canonical; indexes and GDS projection are ready before `search_ready=true`; and a live smoke test confirms the complete contract without changing original project files.

## Verification evidence — 2026-10-25

- SDK suite: `36 passed`.
- Live target: dedicated RAGTEST Neo4j at `bolt://127.0.0.1:7695`; additive schema migration from version 1 to 2 preserved the empty workspace.
- A scripted-extractor smoke verified `partial` status for one deliberately failed input, two invalid assertion warnings without dropping the chunk, 768-dimensional chunk/entity/triple vectors, one verified `USES` assertion, and `search_ready=true`.
- One live OpenRouter call using a temporary SDK config (`openai/gpt-5.6-luna`) also completed ingestion and published one assertion. Both smoke paths used the configured local `BAAI/bge-base-en-v1.5` embedding model.
- Re-ingestion skipped a completed chunk without calling extractor or embedder. Dropping the SDK GDS projection and ingesting again restored it without changing the corpus revision.
- Smoke records and the temporary secret/config files were removed afterward. RAGTEST is empty again with `search_ready=false`, schema version 2 and the additive checkpoint constraint retained. The RAGTEST YAML and `.env` were not changed.
