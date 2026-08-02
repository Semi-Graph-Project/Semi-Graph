# SOX74 Retrieval Ablation Freeze v1

This directory is a byte-preserving evidence bundle for the first complete
SOX74 retrieval ablation run on 2026-08-02.

## Frozen comparison

All four runs contain the same 74 query IDs in the same order and report zero
errors. The matched final evidence budget is 9 chunks.

| Run | Hit@9 | Recall@9 | Mean latency |
|---|---:|---:|---:|
| Vector-only | 0.392 | 0.176 | 0.249 s |
| Agent + Vector | 0.514 | 0.270 | 33.965 s |
| Graph-only (`top_k_triples=20`) | 0.649 | 0.390 | 18.222 s |
| Agent + Graph (`top_k_triples=20`) | 0.743 | 0.450 | 84.196 s |

For non-agent runs, Hit@9 and Recall@9 are measured directly on the nine
returned chunks. For agent runs, they are measured on the final synthesis
context of at most nine chunks. Each individual agent retrieval attempt uses
`top_k_chunks=5`.

## What is preserved

- `inputs/`: the exact benchmark dataset used by all runs.
- `runs/`: original reports, per-query records, checkpoints, RAGAS-ready
  projections, summaries, and recorded run configuration.
- `provenance/`: the source snapshot and environment information captured when
  this bundle was created.
- `manifest.json`: the comparison contract, metrics, run times, and parameter
  provenance.
- `checksums.sha256`: content hashes for every frozen file except itself.

The Agent + Graph per-query runtime trace is the authoritative evidence that
`top_k_triples=20`, `ppr_graph_mode=entity_chunk`, `triple_filter=llm`, and
`final_rerank=none` were actually used. The current project default was later
returned to `top_k_triples=10`, so it must not be used to reinterpret this run.

## Verify

From the repository root:

```bash
python benchmark/freezes/sox74_retrieval_ablation_v1/verify_freeze.py
```

The verifier checks every SHA-256 digest, parses all primary JSONL artifacts,
confirms 74 unique query IDs per run, confirms identical query ordering, and
confirms zero recorded errors.

## Publish without rewriting history

Commit the bundle, create an annotated tag, and push both yourself:

```bash
git add benchmark/freezes/sox74_retrieval_ablation_v1
git commit -m "eval: freeze SOX74 retrieval ablation v1"
git tag -a eval/sox74-retrieval-ablation-v1 \
  -m "SOX74 retrieval ablation evidence bundle"
git push origin <your-branch>
git push origin eval/sox74-retrieval-ablation-v1
```

For stronger archival evidence, attach this directory as a GitHub Release asset
and archive that release with Zenodo. Do not add `.env` or API keys.

## Provenance limitation

This is a retrospective freeze of already completed local runs, not an
independently witnessed execution. The raw artifacts contain run timestamps,
per-query outputs, traces, and checkpoints, while their hashes prevent silent
changes after this bundle is committed and tagged.

The repository working tree was dirty during this development period and the
evaluator did not record a Git commit in each run. Therefore the exact
historical dirty-tree state cannot be proven from the old outputs alone. A
runtime source snapshot and current Git HEAD are included honestly as
freeze-time provenance. Future official runs should write Git commit, dirty
state, effective configuration, model ID, and environment versions into
`run_config.json` before the first query.
