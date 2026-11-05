# Plan — staged delivery of the library

Each stage begins with its Spec/Plan, then code and focused verification. New files stay under `library/`; existing project code, configuration, databases and untracked work are preserved.

| Stage | Spec | Status | Exit condition |
|---|---|---|---|
| 0. Agent compatibility copies | [04](specs/04-agent-compatibility.md) | Implemented; final checks recorded in README | Generic/empty relations, both tools, optional synthesis, no original-runtime imports |
| 1. SDK configuration and database setup | [01](specs/01-database.md) | Implemented; primary live path accepted | Independent workspace and ready dedicated Neo4j with compatible indexes |
| 2. Free Ontology extraction and durable chunk publication | [02](specs/02-ingestion.md) | Implemented; 36 tests and live smoke passed | Plain text, validated assertions/provenance, embeddings and resumable item outcomes |
| 3. Configured Vector/Graph retrieval kernels | [03](specs/03-retrieval.md) | Implemented; 33 focused tests; RAGTEST and isolated relation/revision/restart smoke passed | Vector/Graph return the same finalized corpus evidence; three graph seed modes work |
| 4. Engine query facade and Agent binding | [03](specs/03-retrieval.md) | Implemented; 12 mode contracts, 69 SDK tests, and live RAGTEST 12-mode smoke passed | All tool/Agent/output combinations return one result contract |
| 5. Clean-install example and end-to-end handoff | All three integration specs | README usage path and isolated setup → ingest → query smoke passed with injected test adapters; clean consumer pip install not run | New user can setup → ingest → query on a clean dedicated database |

## Stage 1 status

Spec 01 code is in place. Live acceptance on 2026-10-25 used an independent workspace and confirmed fresh setup, preserved-volume restart, repeated setup, APOC/GDS availability, and ONLINE 768-dimensional vector indexes. The initial `search_ready=false` state is expected until Spec 02 publishes a successful ingestion revision. Failure injection for missing plugins and incompatible pre-existing indexes remains outside this acceptance run.

## Stage 2 design decisions

The implemented ingestion uses NFC-normalized content IDs, quote-based evidence resolution, partial assertion filtering, canonical relationship types, bounded embedding batches and deterministic write order. Validated extraction is checkpointed in Neo4j so retries can avoid another LLM call. The checkpoint constraint is an additive v1-to-v2 schema migration. Finalization owns observed relation metadata, specificity and an idempotent SDK GDS projection; `search_ready` is written only after these steps succeed. Unit and live smoke evidence are recorded in Spec 02; smoke records were removed after verification.

## Cross-stage acceptance

- No edits outside `library/`, except user-requested output workspaces for future runtime tests.
- Checkpoint completion is tied to config/model/schema versions, not text hash alone.
- Partial ingestion is visible. Query refuses a dirty revision; a successful chunk count alone does not prove readiness.
- Generic ontology acceptance is tested at extraction, storage, PPR and Agent planning boundaries.
- Retrieval Only with agents remains an LLM workflow; no synthesis is called.
- Package users supply their own keys. Tests use deterministic local doubles unless live integration is explicitly part of the stage.
- Full Answer cites the same evidence returned by the API. Error cases are not successful empty results.
- Source-copy provenance is updated intentionally whenever new copies or upstream fixes are brought in.

## Current limitations to carry forward

The legacy financial benchmark is not validation of a general-purpose library. Homonym resolution, multilingual retrieval quality, semantic synonym merging and large-corpus scaling require separate evidence. V1 does not add multi-tenant service hosting, multiple engine configurations per program, automatic document parsing/chunking, implicit deletion/replacement, or arbitrary pre-existing graph-schema migration.
