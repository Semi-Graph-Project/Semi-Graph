# ADR: Agent Evaluator Checkpoint and Resume

Status: Accepted  
Date: 2026-07-20

## Context

The FinReflectKG Agent benchmark may run hundreds of network-dependent units.
The previous evaluator wrote `details.jsonl` and `ragas.jsonl` after each unit,
but it could not reopen a run directory and skip work that had already
completed.

## Decision

- The idempotency key is `(query_id, mode)`.
- Only a record with `status=ok` is complete. An error remains retryable.
- `checkpoint.jsonl` is the canonical, atomically replaced checkpoint. Each
  row contains the detail record and its RAGAS projection together.
- `details.jsonl`, `ragas.jsonl`, summaries, and progress are derived views.
- Resume requires `--resume --run-name NAME` and rejects incompatible dataset,
  query selection, modes, `top_k`, `score_k`, or recursion limit.
- Existing runs created before this ADR can be resumed by importing their
  matching `details.jsonl` and `ragas.jsonl` once.

## State Model

```text
missing record  -> pending
status=error    -> retryable
status=ok       -> complete and skipped on resume
```

A retry replaces the previous record for the same idempotency key; it never
adds a second logical result.

## Consequences

- A process or network failure loses at most the currently executing unit.
- Re-running with `--resume` does not repeat successful LLM/retriever calls.
- Configuration drift fails closed instead of mixing incomparable results.
- The canonical checkpoint duplicates some output data, trading disk space for
  simple recovery and an atomic detail/RAGAS boundary.

## Glossary

- **Run**: One benchmark directory and one immutable experiment configuration.
- **Unit**: One query evaluated in one mode.
- **Idempotency key**: The `(query_id, mode)` identity of a unit.
- **Canonical checkpoint**: The authoritative atomic snapshot used for resume.
- **Derived view**: A report regenerated from the canonical checkpoint.
- **Retryable record**: A unit whose latest status is not `ok`.
