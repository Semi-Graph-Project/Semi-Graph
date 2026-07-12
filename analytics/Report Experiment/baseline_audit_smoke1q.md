# Phase T Retrieval Baseline

Generated: 2026-07-08T16:18:13

## Run Configuration

- script: `scripts/evaluate_retrieval_quality.py`
- command: `scripts/evaluate_retrieval_quality.py --limit 1 --tools vector graph hybrid --top-k 5 --oracle-k 20 --no-llm-expansion --version-name phase_t_audit_smoke_1q`
- query_file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
- query_count: `1`
- tools: `vector, graph, hybrid`
- top_k: `5`
- oracle_k: `20`
- dry_run: `False`
- corpus_chunks: `2346`
- graph_use_expansion: `False`
- graph_seed_mode: `triple`
- graph_rerank_mode: `legacy`
- candidate_pool_k: `100`
- graph_top_k_entities: `20`
- graph_top_k_triples: `8`
- graph_damping: `0.7`
- metadata_rerank_params: `{'risk_section_boost': 1.35, 'business_section_boost': 1.18, 'financial_section_boost': 1.28, 'ticker_boost': 1.2, 'cluster_boost_per_extra': 0.04, 'cluster_boost_cap': 1.05, 'latest_year_boost': 1.08, 'latest_year_min': 2025, 'lexical_match_weight': 0.1, 'lexical_boost_cap': 0.55, 'broad_penalty_enabled': True, 'broad_penalty_floor': 0.92, 'broad_penalty_step': 0.97, 'broad_penalty_zero_match': 0.98, 'broad_penalty_short_token_cutoff': 80, 'broad_penalty_mid_token_cutoff': 140, 'broad_penalty_long_token_cutoff': 220}`
- version_name: `phase_t_audit_smoke_1q`
- details_jsonl: `/home/kantinan/programming/project/analytics/Report Experiment/details_audit_smoke1q.jsonl`
- reextract_tickers_arg: `all`
- resolved_ticker_scope: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- known_tickers: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- scored_queries: `1`
- unscored_queries: `0`
- existing_gold_entities: `2`
- total_gold_entities: `2`

## Overall

| Tool | Scored Queries | Errors | ChunkHit@k | Random ChunkHit@k | Hit Lift | Hit-Random | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 1 | 0 | 0.000 | 0.006 | 0.000 | -0.006 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| graph | 1 | 0 | 1.000 | 0.006 | 156.667 | 0.994 | 0.667 | 1.000 | 1.000 | 1.000 | 1.000 |
| hybrid | 1 | 0 | 1.000 | 0.006 | 156.667 | 0.994 | 0.333 | 1.000 | 1.000 | 0.333 | 1.000 |

## By Type

| Type | vector ChunkHit | vector ChunkRecall | vector GroupRecall | vector Answerable | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable | hybrid ChunkHit | hybrid ChunkRecall | hybrid GroupRecall | hybrid Answerable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.667 | 1.000 | 1.000 | 1.000 | 0.333 | 1.000 | 1.000 |

## By Subset

| Subset | vector ChunkHit | vector ChunkRecall | vector GroupRecall | vector Answerable | vector Oracle | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable | graph Oracle | hybrid ChunkHit | hybrid ChunkRecall | hybrid GroupRecall | hybrid Answerable | hybrid Oracle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| reextract_subset | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.667 | 1.000 | 1.000 | 1.000 | 1.000 | 0.333 | 1.000 | 1.000 | 1.000 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 1.000 | 1.000 | 1.000 | hit_top_k=1 |
| reextract_subset | 1.000 | 1.000 | 1.000 | hit_top_k=1 |

## Paired GroupRecall Test vs Vector

| Subset | Tool | n | Mean Delta GroupRecall | One-sided p |
|---|---|---:|---:|---:|
| full_mixed | graph | 1 | 1.000 | n/a |
| full_mixed | hybrid | 1 | 1.000 | n/a |
| reextract_subset | graph | 1 | 1.000 | n/a |
| reextract_subset | hybrid | 1 | 1.000 | n/a |

## Per Query

### T001: `How exposed is AMD to TSMC supply risk?`

- type: `graph_multihop`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['amd', 'tsmc']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2026_Item_1A_0008_e84e4130', 'AMD_2025_Item_1A_0009_57657610', 'AMD_2025_Item_1A_0011_10eec6d1']`
- gold_evidence_groups: `{'amd_tsmc_supply_risk': ['AMD_2026_Item_1A_0008_e84e4130', 'AMD_2025_Item_1A_0009_57657610', 'AMD_2025_Item_1A_0011_10eec6d1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 13.304 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'amd_tsmc_supply_risk': []}` | `['AMD_2024_Item_1A_0002_0a71f57a', 'INTC_2026_Item_1A_0006_820d3c64', 'MU_2024_Item_1A_0001_703555bd', 'MU_2025_Item_1A_0001_8d660135', 'INTC_2024_Item_1A_0000_1a5c79ae']` |
| graph |  | 25.988 | 1 | 0.006 | 0.667 | 1.000 | 1 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_1A_0009_57657610', 'AMD_2025_Item_1A_0011_10eec6d1']` | `{'amd_tsmc_supply_risk': ['AMD_2025_Item_1A_0009_57657610', 'AMD_2025_Item_1A_0011_10eec6d1']}` | `['AMD_2025_Item_1A_0009_57657610', 'INTC_2026_Item_1A_0000_268148d2', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1A_0011_10eec6d1']` |
| hybrid |  | 4.185 | 1 | 0.006 | 0.333 | 1.000 | 1 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2025_Item_1A_0009_57657610']` | `{'amd_tsmc_supply_risk': ['AMD_2025_Item_1A_0009_57657610']}` | `['INTC_2026_Item_1A_0000_268148d2', 'AMD_2024_Item_1A_0002_0a71f57a', 'AMD_2025_Item_1A_0009_57657610', 'INTC_2026_Item_1A_0006_820d3c64', 'AMD_2025_Item_1_0009_c842eea0']` |
