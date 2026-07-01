# Phase T-R Retriever Baseline After Partial Re-extract

Generated: `2026-07-01`

Input health report: `analytics/reextract_health_report_20260701.md`

## What Changed In This Run

Phase T-R now evaluates retriever quality with stage-aware graph diagnostics:

- `SeedHit@k`: whether graph seeds contain expected gold entities.
- `PPRHit@k`: whether PPR reaches expected gold entities.
- `ChunkMapHit@k`: whether entity-to-chunk mapping surfaces gold chunks into the candidate pool.v
- `BottleneckLabel`: `seed_loss`, `ppr_loss`, `chunk_mapping_loss`, `rerank_loss`, `candidate_pool_loss`, or `hit_top_k`.
- `subset`: `reextract_subset`, `mixed_subset`, or `legacy_subset`.

This separates the partial re-extract signal from the still-old corpus.

## Reports

| Run | Report | Details |
|---|---|---|
| No expansion | `analytics/phase_t_retrieval_baseline_20260701_151204.md` | `analytics/phase_t_retrieval_details_20260701_151204.jsonl` |
| With expansion | `analytics/phase_t_retrieval_baseline_20260701_151517.md` | `analytics/phase_t_retrieval_details_20260701_151517.jsonl` |

Commands:

```bash
HF_HUB_OFFLINE=1 conda run -n senior_project python scripts/evaluate_retrieval_quality.py --tools vector graph hybrid --top-k 5 --oracle-k 20 --no-llm-expansion
HF_HUB_OFFLINE=1 conda run -n senior_project python scripts/evaluate_retrieval_quality.py --tools graph hybrid --top-k 5 --oracle-k 20
```

## No Expansion Result

This is the main PPR-only diagnostic because it does not rely on LLM query expansion.

| Scope | Tool | Hit@5 | Recall@5 | Oracle@20 |
|---|---|---:|---:|---:|
| full_mixed | vector | 0.333 | 0.224 | 0.571 |
| full_mixed | graph | 0.190 | 0.121 | 0.333 |
| full_mixed | hybrid | 0.381 | 0.243 | 0.571 |
| reextract_subset | vector | 0.286 | 0.143 | 0.571 |
| reextract_subset | graph | 0.143 | 0.071 | 0.143 |
| reextract_subset | hybrid | 0.429 | 0.214 | 0.714 |

Paired recall vs vector:

| Scope | Tool | Mean Delta Recall | p |
|---|---|---:|---:|
| full_mixed | graph | -0.102 | 1.000 |
| full_mixed | hybrid | 0.019 | 0.495 |
| reextract_subset | graph | -0.071 | 1.000 |
| reextract_subset | hybrid | 0.071 | 0.496 |

Interpretation: Hybrid no-expansion is slightly better than Vector on the re-extracted subset, but the sample is too small and the p-value is not significant.

## Stage Bottleneck

No expansion graph diagnostics:

| Scope | SeedHit | PPRHit | ChunkMapHit | Main Bottleneck |
|---|---:|---:|---:|---|
| full_mixed | 0.952 | 1.000 | 0.333 | `chunk_mapping_loss=13` |
| reextract_subset | 0.857 | 1.000 | 0.143 | `chunk_mapping_loss=5` |

With expansion graph diagnostics:

| Scope | SeedHit | PPRHit | ChunkMapHit | Main Bottleneck |
|---|---:|---:|---:|---|
| full_mixed | 1.000 | 1.000 | 0.667 | `chunk_mapping_loss=7`, `rerank_loss=4` |
| reextract_subset | 1.000 | 1.000 | 0.571 | `chunk_mapping_loss=3`, `rerank_loss=2` |

Interpretation: after partial re-extract, the graph can usually seed and walk to relevant entities. The dominant failure is mapping/ranking entity evidence back into the correct evidence chunk.

## Key Query Failures

No expansion graph misses on re-extracted scored queries:

| ID | Type | Bottleneck | Meaning |
|---|---|---|---|
| T001 | graph_multihop | `chunk_mapping_loss` | AMD/TSMC are found, but the correct Item 1A supply-risk chunk is not in candidate chunks. |
| T004 | competitor_product | `chunk_mapping_loss` | AMD/Instinct path is reachable, but product evidence chunk is not mapped high enough. |
| T018 | partner_via_product | `chunk_mapping_loss` | Ryzen/AMD path exists, but console partner chunk is missed. |
| T019 | segment_via_product | `chunk_mapping_loss` | EPYC/AMD path exists, but segment evidence chunk is missed. |
| T020 | regulation_via_product | `chunk_mapping_loss` | Blackwell/NVIDIA/export-control path exists, but evidence chunk is missed. |
| T030 | customer_via_product | `seed_loss` in no-expansion; `chunk_mapping_loss` with expansion | expansion fixes seed, but mapping still misses hyperscaler evidence. |

## Decision

Do not tune damping first. The strongest signal is not PPR walk failure.

Next implementation should prioritize **T-R2 Chunk Mapping / Rerank**:

1. Return matched entities and per-cluster contribution from `_map_chunks`.
2. Compare aggregation modes: `SUM`, `MAX`, and capped/log-normalized `SUM`.
3. Add query-chunk cosine rerank over PPR candidate chunks.
4. Penalize broad chunks with very high mention density.
5. Keep ticker and section priors, but make their contribution visible in debug output.

Only after `ChunkMapHit` improves should we tune seed mode or PPR damping.
