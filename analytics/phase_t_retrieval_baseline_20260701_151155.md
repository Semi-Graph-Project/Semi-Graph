# Phase T Retrieval Baseline

Generated: 2026-07-01T15:11:55
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `vector, graph, hybrid`
top_k: `5`
oracle_k: `20`
dry_run: `True`
corpus_chunks: `0`
graph_use_expansion: `False`
graph_seed_mode: `triple`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Random Hit@k | Hit Lift | Hit-Random | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 0 | 0 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 0.000 |
| graph | 0 | 0 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 0.000 |
| hybrid | 0 | 0 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 0.000 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 0.000 | 0.000 | 0.000 | n/a |

## Paired Recall Test vs Vector

| Subset | Tool | n | Mean Delta Recall | One-sided p |
|---|---|---:|---:|---:|
| full_mixed | graph | 0 | 0.000 | n/a |
| full_mixed | hybrid | 0 | 0.000 | n/a |

## Per Query

### T001: `How exposed is AMD to TSMC supply risk?`

- type: `graph_multihop`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['amd', 'tsmc']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `[]` |

### T002: `Which foundry partner manufactures the Hopper architecture chips?`

- type: `supplier_via_product`
- subset: `mixed_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['hopper', 'nvidia', 'tsmc']`
- missing_gold_entities: `[]`
- gold_chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `[]` |

### T003: `Who produces the dense memory chips that power modern AI training accelerators?`

- type: `supplier_via_product`
- subset: `mixed_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['micron', 'hbm', 'ai accelerators']`
- missing_gold_entities: `[]`
- gold_chunks: `['MU_2023_Item_1A_0003_92be33e3', 'MU_2025_Item_1A_0004_836bee10', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `[]` |
