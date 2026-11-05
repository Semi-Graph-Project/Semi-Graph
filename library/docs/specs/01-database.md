# Spec 01 — Database setup and shared configuration

Status: implementation complete; primary live database path accepted 2026-10-25.

## Goal

ผู้ใช้ใหม่เริ่ม Neo4j ที่มี plugin ครบและพื้นที่เก็บข้อมูลของตัวเองได้ ส่วนผู้ใช้ที่มี Neo4j แล้วส่ง config เพื่อเตรียม schema/index ได้ โดยทุก path และ credential ต้องเป็นของ SDK workspace นี้

## Contract

- `semigraph-sdk init <workspace>` creates a Compose file, SDK YAML, local secrets file, and `.gitignore`. Existing files are preserved or a clear conflict is returned; no overwrite by default.
- `semigraph-sdk db up --workspace <path>` starts only this workspace's Compose project, waits for Bolt and required GDS/APOC procedures, then performs the same schema/index setup as `Engine.setup()`. Ports and volume/project names are configurable and cannot silently reuse the original project resources.
- `semigraph-sdk db down --workspace <path>` stops only this Compose project and preserves its named volumes.
- `Engine.setup()` connects to the configured existing database, validates capabilities, creates owned constraints/indexes if absent, waits for vector indexes to become ONLINE, and returns a structured setup report.
- Repeating setup is safe. Existing objects with incompatible dimensions/schema are errors, not silently dropped and recreated.
- Docker provisions a server and its default database. On an existing server, SDK selects an existing database explicitly; it must not assume Neo4j Community supports arbitrary `CREATE DATABASE` operations.

## SDK configuration

This stage configures explicit database URI, user, password reference and database name; embedding model/revision/device/normalization; and optional LLM provider/model/base URL/key reference. Extraction and retrieval budgets will be added with Specs 02 and 03. All paths resolve against the supplied workspace/config path. No fallback to the original `.env`, `config/default.yaml`, production port or controlled benchmark port.

The SDK creates LLM/embedding/driver objects and passes them to components. Runtime configuration is immutable while an operation runs. Model fingerprints stored in the database must match on reopen. Query-level settings may change tool/agent/output and budgets without mutating embedding or database identity.

An SDK metadata record tracks ownership, schema version, embedding fingerprint, corpus revision and index readiness. An existing nonempty database without compatible SDK metadata is not automatically adopted or cleared. Supporting arbitrary pre-existing graph schemas is outside v1; an existing server can host an empty dedicated database for the SDK.

## Implementation plan

Concrete v1 choices: `init` writes `semigraph.yaml`, `compose.yaml`, a mode-0600 `.env` containing a generated password, and a `.gitignore` protecting that secret. It uses a random Compose project name, project-scoped named volumes, localhost-only ports (HTTP 17474, Bolt 17687 by default), and a pinned Neo4j 2025.04 Community image digest. The Compose file installs compatible APOC Core and GDS plugins through Neo4j's Docker development plugin helper. The SDK reads secrets only from that workspace's `.env`, never the root project environment. A caller with an existing dedicated database can edit the URI/credentials in the SDK workspace and call `Engine.setup()` or `semigraph-sdk db setup --config ...` directly.

The SDK owns `SDKMeta`, `Chunk`, `Entity` and `ObservedRelation` labels. It creates unique constraints for metadata key, chunk ID, entity `(name,type)` and observed relation identifier; an Entity type lookup; and cosine vector indexes for `Chunk.embedding` and `Entity.embedding` using the configured dimension. The metadata stores owner ID, schema version, embedding fingerprint, corpus revision and readiness. Setup starts with `search_ready=false`; ingestion will later move it to true. Existing nonempty databases without matching metadata, or conflicting indexes/constraints, cause explicit errors before any SDK schema write. LLM settings are optional during database setup; config supports provider, model, base URL and an API key reference in the same local secrets file.

1. Define immutable SDK config and setup report models under `library/src/semigraph_sdk/`.
2. Add the packaged standalone deployment template under `library/src/semigraph_sdk/deployment/`.
3. Implement CLI init/up/down/setup with health checks and port collision detection.
4. Implement owned schema/index initialization and compatibility checks. Keep connection ownership explicit and close all resources on failure.
5. Record live acceptance on a fresh dedicated workspace, restart it with the same volume, and repeat setup.

## Acceptance evidence

The 2026-10-25 live run used an isolated generated workspace. Fresh setup and a preserved-volume restart both reached ready; repeating setup was safe. Neo4j exposed its browser successfully, APOC 2025.04.0 and GDS 2.17.1 were available, and both 768-dimensional cosine vector indexes reached ONLINE. Setup correctly left `search_ready=false` because no ingestion revision had been published. Missing-plugin and incompatible-index failure injection were not part of this run.

## Done when

- Fresh setup reaches ready; restart preserves data; repeating setup changes no existing evidence.
- Incorrect password, missing plugin, incompatible index and occupied port yield actionable errors.
- No root project configuration, container or database is touched.
- New vector indexes have the actual configured model dimension, and database selection is explicit on every session.
- Image digest and commands are documented, and the primary Neo4j/APOC/GDS path has live evidence. No database backup, benchmark snapshot or original secrets are bundled.
