# Phase T Retrieval Baseline

Generated: 2026-07-07T13:47:14

## Run Configuration

- script: `scripts/evaluate_retrieval_quality.py`
- command: `scripts/evaluate_retrieval_quality.py --dry-run --limit 2 --version-name metric_smoke`
- query_file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
- query_count: `2`
- tools: `vector, graph, hybrid`
- top_k: `5`
- oracle_k: `10`
- dry_run: `True`
- corpus_chunks: `0`
- graph_use_expansion: `True`
- graph_seed_mode: `triple`
- graph_rerank_mode: `legacy`
- candidate_pool_k: `100`
- graph_top_k_entities: `20`
- graph_top_k_triples: `8`
- graph_damping: `0.7`
- metadata_rerank_params: `{'risk_section_boost': 1.35, 'business_section_boost': 1.18, 'financial_section_boost': 1.28, 'ticker_boost': 1.2, 'cluster_boost_per_extra': 0.04, 'cluster_boost_cap': 1.05, 'latest_year_boost': 1.08, 'latest_year_min': 2025, 'lexical_match_weight': 0.1, 'lexical_boost_cap': 0.55, 'broad_penalty_enabled': True, 'broad_penalty_floor': 0.92, 'broad_penalty_step': 0.97, 'broad_penalty_zero_match': 0.98, 'broad_penalty_short_token_cutoff': 80, 'broad_penalty_mid_token_cutoff': 140, 'broad_penalty_long_token_cutoff': 220}`
- version_name: `metric_smoke`
- details_jsonl: `/home/kantinan/programming/project/analytics/Report Experiment/details_metric_smoke.jsonl`
- reextract_tickers_arg: `all`
- resolved_ticker_scope: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- known_tickers: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- scored_queries: `2`
- unscored_queries: `0`
- existing_gold_entities: `4`
- total_gold_entities: `4`

## Overall

| Tool | Scored Queries | Errors | ChunkHit@k | Random ChunkHit@k | Hit Lift | Hit-Random | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 0 | 0 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| graph | 0 | 0 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| hybrid | 0 | 0 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 0.000 | 0.000 | 0.000 | n/a |

## Paired GroupRecall Test vs Vector

| Subset | Tool | n | Mean Delta GroupRecall | One-sided p |
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
- gold_chunks: `['AMD_2026_Item_1A_0008_e84e4130', 'AMD_2025_Item_1A_0009_57657610', 'AMD_2025_Item_1A_0011_10eec6d1']`
- gold_evidence_groups: `{'gold_chunks': ['AMD_2026_Item_1A_0008_e84e4130', 'AMD_2025_Item_1A_0009_57657610', 'AMD_2025_Item_1A_0011_10eec6d1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |

### T002: `Which foundry partner manufactures the Hopper architecture chips?`

- type: `supplier_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['hopper', 'nvidia', 'tsmc']`
- missing_gold_entities: `[]`
- gold_chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_7_0007_d25e117d', 'NVDA_2025_Item_7_0000_78a2a641', 'NVDA_2025_Item_7_0003_d53d3047']`
- gold_evidence_groups: `{'hopper_evidence': ['NVDA_2024_Item_7_0007_d25e117d', 'NVDA_2025_Item_7_0000_78a2a641', 'NVDA_2025_Item_7_0003_d53d3047'], 'supplier_evidence': ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
