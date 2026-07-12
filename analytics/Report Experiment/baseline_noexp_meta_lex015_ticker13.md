# Phase T Retrieval Baseline

Generated: 2026-07-06T20:22:49

## Run Configuration

- script: `scripts/evaluate_retrieval_quality.py`
- command: `scripts/evaluate_retrieval_quality.py --tools vector graph hybrid --top-k 5 --oracle-k 20 --no-llm-expansion --graph-rerank-mode metadata --metadata-lexical-match-weight 0.15 --metadata-lexical-boost-cap 0.65 --metadata-ticker-boost 1.30 --metadata-risk-section-boost 1.45 --metadata-business-section-boost 1.25 --metadata-financial-section-boost 1.35`
- query_file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
- query_count: `30`
- tools: `vector, graph, hybrid`
- top_k: `5`
- oracle_k: `20`
- dry_run: `False`
- corpus_chunks: `2346`
- graph_use_expansion: `False`
- graph_seed_mode: `triple`
- graph_rerank_mode: `metadata`
- candidate_pool_k: `100`
- graph_top_k_entities: `20`
- graph_top_k_triples: `8`
- graph_damping: `0.7`
- metadata_rerank_params: `{'risk_section_boost': 1.45, 'business_section_boost': 1.25, 'financial_section_boost': 1.35, 'ticker_boost': 1.3, 'cluster_boost_per_extra': 0.04, 'cluster_boost_cap': 1.05, 'latest_year_boost': 1.08, 'latest_year_min': 2025, 'lexical_match_weight': 0.15, 'lexical_boost_cap': 0.65, 'broad_penalty_enabled': True, 'broad_penalty_floor': 0.92, 'broad_penalty_step': 0.97, 'broad_penalty_zero_match': 0.98, 'broad_penalty_short_token_cutoff': 80, 'broad_penalty_mid_token_cutoff': 140, 'broad_penalty_long_token_cutoff': 220}`
- version_name: `no_expansion_metadata_pool100_lex0.15_ticker1.3`
- details_jsonl: `/home/kantinan/programming/project/analytics/Report Experiment/details_noexp_meta_lex015_ticker13.jsonl`
- reextract_tickers_arg: `all`
- resolved_ticker_scope: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- known_tickers: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- scored_queries: `21`
- unscored_queries: `9`
- existing_gold_entities: `57`
- total_gold_entities: `61`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Random Hit@k | Hit Lift | Hit-Random | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 21 | 0 | 0.333 | 0.004 | 78.295 | 0.329 | 0.248 | 0.286 | 0.571 |
| graph | 21 | 0 | 0.286 | 0.004 | 67.110 | 0.281 | 0.207 | 0.127 | 0.429 |
| hybrid | 21 | 0 | 0.429 | 0.004 | 100.665 | 0.424 | 0.245 | 0.240 | 0.619 |

## By Type

| Type | vector Hit | vector Recall | graph Hit | graph Recall | hybrid Hit | hybrid Recall |
|---|---:|---:|---:|---:|---:|---:|
| competitor_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| customer_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| geo_via_product | 1.000 | 0.500 | 0.000 | 0.000 | 1.000 | 0.500 |
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| partner_via_product | 0.333 | 0.333 | 0.000 | 0.000 | 0.333 | 0.167 |
| product_via_company | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| regulation_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| regulator_via_product | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.500 |
| segment_via_product | 1.000 | 0.500 | 0.000 | 0.000 | 1.000 | 0.500 |
| subsidiary_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| supplier_via_company | 0.000 | 0.000 | 1.000 | 0.500 | 1.000 | 0.500 |
| supplier_via_product | 0.333 | 0.067 | 0.667 | 0.283 | 0.667 | 0.217 |
| three_hop_subsidiary_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| topical_memory | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| vector_friendly | 0.667 | 0.667 | 0.667 | 0.667 | 0.333 | 0.333 |

## By Subset

| Subset | vector Hit | vector Recall | vector Oracle | graph Hit | graph Recall | graph Oracle | hybrid Hit | hybrid Recall | hybrid Oracle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| reextract_subset | 0.333 | 0.248 | 0.571 | 0.286 | 0.207 | 0.429 | 0.429 | 0.245 | 0.619 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 0.952 | 1.000 | 0.714 | candidate_pool_loss=4, chunk_mapping_loss=6, corpus_not_ready=2, hit_top_k=6, rerank_loss=3 |
| reextract_subset | 0.952 | 1.000 | 0.714 | candidate_pool_loss=4, chunk_mapping_loss=6, corpus_not_ready=2, hit_top_k=6, rerank_loss=3 |

## Paired Recall Test vs Vector

| Subset | Tool | n | Mean Delta Recall | One-sided p |
|---|---|---:|---:|---:|
| full_mixed | graph | 21 | -0.040 | 1.000 |
| full_mixed | hybrid | 21 | -0.002 | 1.000 |
| reextract_subset | graph | 21 | -0.040 | 1.000 |
| reextract_subset | hybrid | 21 | -0.002 | 1.000 |

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
| vector |  | 8.872 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1A_0002_0a71f57a', 'INTC_2026_Item_1A_0006_820d3c64', 'MU_2024_Item_1A_0001_703555bd', 'MU_2025_Item_1A_0001_8d660135', 'INTC_2024_Item_1A_0000_1a5c79ae']` |
| graph |  | 26.288 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2025_Item_1A_0009_57657610', 'INTC_2026_Item_1A_0000_268148d2', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1A_0011_10eec6d1']` |
| hybrid |  | 11.722 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_1A_0000_268148d2', 'AMD_2024_Item_1A_0002_0a71f57a', 'AMD_2025_Item_1A_0009_57657610', 'INTC_2026_Item_1A_0006_820d3c64', 'AMD_2025_Item_1_0009_c842eea0']` |

### T002: `Which foundry partner manufactures the Hopper architecture chips?`

- type: `supplier_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['hopper', 'nvidia', 'tsmc']`
- missing_gold_entities: `[]`
- gold_chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.758 | 1 | 0.011 | 0.200 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0013_cb483288', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_1_0014_32e0816b', 'AMD_2024_Item_1_0012_9561038a']` |
| graph |  | 2.192 | 1 | 0.011 | 0.600 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` | `['INTC_2026_Item_1A_0000_268148d2', 'INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2025_Item_1A_0000_ac3a3dbc']` |
| hybrid |  | 1.706 | 1 | 0.011 | 0.400 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1A_0000_268148d2', 'INTC_2026_Item_1_0013_cb483288', 'AMD_2025_Item_1_0009_c842eea0', 'INTC_2026_Item_1_0006_d0f653da']` |

### T003: `Who produces the dense memory chips that power modern AI training accelerators?`

- type: `supplier_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['micron', 'hbm', 'ai accelerators']`
- missing_gold_entities: `[]`
- gold_chunks: `['MU_2023_Item_1A_0003_92be33e3', 'MU_2025_Item_1A_0004_836bee10', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.133 | 0 | 0.009 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2026_Item_1_0005_9725a5a2', 'INTC_2026_Item_1_0004_c01224f1']` |
| graph |  | 1.714 | 1 | 0.009 | 0.250 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1_0008_a4407f7e']` | `['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01']` |
| hybrid |  | 1.450 | 1 | 0.009 | 0.250 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2025_Item_1_0008_a4407f7e']` | `['INTC_2026_Item_1_0008_c74f560f', 'RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'NVDA_2025_Item_1_0008_a4407f7e', 'INTC_2025_Item_7_0003_878f7d25']` |

### T004: `What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?`

- type: `competitor_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel', 'amd', 'amd instinct']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2026_Item_1_0003_ea53a6a5']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.135 | 0 | 0.002 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'AMD_2026_Item_1_0004_b5e66359']` |
| graph |  | 1.037 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2025_Item_7_0002_f7953bfd', 'AMD_2024_Item_1_0011_49024c2d']` |
| hybrid |  | 1.138 | 0 | 0.002 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2025_Item_1_0003_707a268b', 'AMD_2025_Item_1_0009_c842eea0', 'INTC_2024_Item_1_0005_bcb431a8', 'AMD_2026_Item_1_0010_460dfa17']` |

### T005: `What political risks affect the home country of the leading pure-play semiconductor foundry?`

- type: `geo_via_supplier`
- subset: `legacy_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['tsmc', 'taiwan', 'political risk']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.117 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['QCOM_2023_Item_1A_0031_545bf96a', 'INTC_2026_Item_1A_0002_066bd50c', 'ENTG_2026_Item_1_0004_6f32215b', 'MU_2023_Item_1A_0003_92be33e3', 'AMD_2025_Item_1A_0032_0a1cf7f3']` |
| graph |  | 1.268 | n/a | n/a | n/a | n/a | n/a | 0 | 0 | n/a | unscored_discovery | `[]` | `['QCOM_2023_Item_1A_0023_7335c8fd', 'RMBS_2024_Item_1A_0009_16baaed9', 'INTC_2025_Item_1A_0000_ac3a3dbc', 'INTC_2026_Item_1A_0000_268148d2', 'RMBS_2025_Item_1_0001_479b0c1e']` |
| hybrid |  | 1.126 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['QCOM_2023_Item_1A_0023_7335c8fd', 'QCOM_2023_Item_1A_0031_545bf96a', 'INTC_2026_Item_1A_0002_066bd50c', 'RMBS_2024_Item_1A_0009_16baaed9', 'INTC_2025_Item_1A_0000_ac3a3dbc']` |

### T006: `Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?`

- type: `supplier_via_company`
- subset: `legacy_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['nvidia', 'tsmc', 'samsung', 'sk hynix']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.119 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1A_0025_1809ff3b', 'AMKR_2026_Item_1_0003_8dee603e', 'NVDA_2025_Item_1_0002_b74647bb', 'NVDA_2024_Item_1_0002_2ddf2e3b']` |
| graph |  | 0.982 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` |
| hybrid |  | 1.114 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'MU_2024_Item_1A_0025_1809ff3b', 'NVDA_2024_Item_1_0007_bae70036', 'AMKR_2026_Item_1_0003_8dee603e']` |

### T007: `What graphics product line does AMD offer to compete with NVIDIA's RTX series?`

- type: `competitor_product`
- subset: `reextract_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['amd', 'nvidia', 'radeon', 'geforce rtx']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.122 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0007_0ffd6ad4', 'AMD_2025_Item_1_0009_c842eea0']` |
| graph |  | 1.080 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232']` |
| hybrid |  | 1.104 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965']` |

### T008: `Who supplies the high-bandwidth memory used in NVIDIA's H200 data center accelerator?`

- type: `supplier_via_product`
- subset: `legacy_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['h200', 'nvidia', 'hbm', 'micron', 'sk hynix', 'samsung']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.117 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2025_Item_1_0002_b74647bb', 'MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0001_90ffbd18']` |
| graph |  | 1.006 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2026_Item_1_0009_8c403127', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2024_Item_1_0011_49024c2d', 'NVDA_2026_Item_7_0001_485abbd3']` |
| hybrid |  | 1.167 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2026_Item_1_0009_8c403127', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2024_Item_1_0007_bae70036']` |

### T009: `How do export controls affect NVIDIA's data center business?`

- type: `risk_via_product`
- subset: `legacy_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_entities: `['nvidia', 'export controls', 'data center', 'china']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.113 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2025_Item_1A_0019_46eda166']` |
| graph |  | 1.201 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2025_Item_1A_0003_9003fee7', 'NVDA_2025_Item_1A_0024_d1a5b506', 'AMAT_2025_Item_1A_0017_af7d9be8']` |
| hybrid |  | 1.114 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0023_804c637e', 'NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2026_Item_1A_0022_3d4f4d9b']` |

### T010: `Which materials and purity solutions does Entegris provide to semiconductor manufacturers?`

- type: `vector_friendly`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector']`
- gold_entities: `['entegris', 'materials solutions', 'advanced purity solutions']`
- missing_gold_entities: `[]`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.120 | 1 | 0.002 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0009_ca7ef011', 'ENTG_2025_Item_1_0008_700da46e']` |
| graph |  | 1.032 | 1 | 0.002 | 1.000 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0013_d310ee7e', 'ENTG_2026_Item_7_0002_0ba0c07d', 'ENTG_2025_Item_1_0008_700da46e']` |
| hybrid |  | 1.119 | 1 | 0.002 | 1.000 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0007_4615acf5']` |

### T011: `What gross margin impact did Entegris expect from its useful-life accounting estimate change?`

- type: `vector_friendly`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector']`
- gold_entities: `['entegris', 'gross margin', 'depreciation']`
- missing_gold_entities: `[]`
- gold_chunks: `['ENTG_2026_Item_7_0003_d6e71ea2']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.109 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'KLAC_2025_Item_7_0009_be3ecb77', 'KLAC_2024_Item_7_0008_8308f577', 'KLAC_2023_Item_7_0011_e4c656e2', 'ENTG_2026_Item_7_0015_6af235b4']` |
| graph |  | 0.964 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2026_Item_7_0014_7f63f75a', 'ENTG_2024_Item_7_0019_28ef5c6a', 'ENTG_2025_Item_7_0016_c8496ed0']` |
| hybrid |  | 1.079 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2026_Item_7_0015_6af235b4', 'ENTG_2024_Item_7_0017_71caf017', 'KLAC_2025_Item_7_0009_be3ecb77', 'ENTG_2026_Item_7_0014_7f63f75a']` |

### T012: `What are Entegris's main business segments?`

- type: `vector_friendly`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector']`
- gold_entities: `['entegris', 'materials solutions', 'advanced purity solutions']`
- missing_gold_entities: `[]`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.106 | 1 | 0.002 | 1.000 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2026_Item_1_0014_8712752e', 'ENTG_2024_Item_1_0019_b6aee1a3']` |
| graph |  | 1.035 | 1 | 0.002 | 1.000 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2024_Item_1_0008_9f625423', 'ENTG_2024_Item_1_0009_c1b0a473', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2026_Item_1_0013_2fa9f11c']` |
| hybrid |  | 1.098 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2024_Item_1_0008_9f625423']` |

### T013: `What is AMD's latest FY2025 revenue and gross margin?`

- type: `financial_exact_metric`
- subset: `reextract_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['financial']`
- gold_entities: `['amd', 'revenue', 'gross margin']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.101 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003', 'AMD_2024_Item_1_0001_84491be9', 'INTC_2024_Item_1_0003_02f7f00d', 'AMD_2026_Item_7_0006_2b606b28']` |
| graph |  | 1.212 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2025_Item_7_0001_223169cf', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2024_Item_7_0004_67034475', 'AMD_2025_Item_7_0003_a2d9991c']` |
| hybrid |  | 1.100 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_7_0006_2b606b28', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0001_223169cf', 'INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003']` |

### T014: `What has AMD announced recently?`

- type: `news_recent_event`
- subset: `reextract_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['news']`
- gold_entities: `['amd']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.081 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_7_0000_6b145a7b']` |
| graph |  | 0.959 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2026_Item_1A_0002_72e02a77', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2025_Item_1_0013_9fc1134b', 'AMD_2026_Item_1_0014_30a9cc7d', 'AMD_2024_Item_1_0011_49024c2d']` |
| hybrid |  | 1.063 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2026_Item_1A_0002_72e02a77', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2025_Item_1_0013_9fc1134b']` |

### T015: `What is the relationship between KLA yield improvement tools and downstream AMD gross margin risk?`

- type: `graph_multihop`
- subset: `reextract_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['kla', 'tsmc', 'amd', 'yield', 'gross margin']`
- missing_gold_entities: `['yield']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.121 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['MU_2023_Item_1A_0001_1b8ef3ed', 'AVGO_2025_Item_1A_0008_7b345bfe', 'INTC_2024_Item_7_0015_575e5365', 'AVGO_2023_Item_1A_0018_717a6eeb', 'KLAC_2023_Item_7_0011_e4c656e2']` |
| graph |  | 1.060 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2024_Item_1A_0008_027b0f68', 'AMD_2025_Item_1A_0009_57657610', 'INTC_2026_Item_1A_0000_268148d2', 'AMD_2024_Item_1A_0015_22ab1f05', 'AMD_2025_Item_1A_0011_10eec6d1']` |
| hybrid |  | 1.282 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1A_0008_027b0f68', 'MU_2023_Item_1A_0001_1b8ef3ed', 'AMD_2025_Item_1A_0009_57657610', 'AVGO_2025_Item_1A_0008_7b345bfe', 'INTC_2024_Item_7_0015_575e5365']` |

### T016: `qwerty zzz random semiconductor nonsense`

- type: `off_corpus`
- subset: `legacy_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `[]`
- gold_entities: `[]`
- missing_gold_entities: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.101 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMKR_2026_Item_1A_0003_a2e1fdfd', 'AMKR_2025_Item_1A_0003_a68b7182', 'INTC_2025_Item_1_0001_01b4d21e', 'INTC_2025_Item_1_0002_ba6af228', 'QCOM_2024_Item_1_0009_e0fec737']` |
| graph |  | 1.004 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | unscored_discovery | `[]` | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'NVDA_2025_Item_1_0008_a4407f7e']` |
| hybrid |  | 1.279 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMKR_2026_Item_1A_0003_a2e1fdfd', 'NVDA_2024_Item_1_0007_bae70036', 'AMKR_2025_Item_1A_0003_a68b7182', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2025_Item_1_0001_01b4d21e']` |

### T017: `Which Taiwanese contract chipmaker fabricates AMD's processors?`

- type: `supplier_via_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['amd', 'tsmc', 'umc']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.112 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2024_Item_1_0013_596acde4', 'AMD_2025_Item_1_0004_7a6fa20c']` |
| graph |  | 1.004 | 1 | 0.004 | 0.500 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_1_0009_c842eea0']` | `['AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d']` |
| hybrid |  | 1.078 | 1 | 0.004 | 0.500 | 0.200 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2025_Item_1_0009_c842eea0']` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'AMD_2025_Item_1_0008_db609f8f', 'MU_2024_Item_1A_0025_1809ff3b', 'AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0009_c842eea0']` |

### T018: `Which gaming console makers partner with the Ryzen processor company?`

- type: `partner_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['ryzen', 'amd', 'sony', 'microsoft', 'valve']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.098 | 1 | 0.004 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2026_Item_1_0004_b5e66359', 'AMD_2024_Item_1_0006_e41aed21']` | `['AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2024_Item_1_0006_e41aed21']` |
| graph |  | 0.999 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2025_Item_1_0009_c842eea0', 'NVDA_2025_Item_1_0008_a4407f7e']` |
| hybrid |  | 1.046 | 1 | 0.004 | 0.500 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2026_Item_1_0004_b5e66359']` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0005_808c1965']` |

### T019: `What revenue segments does the developer of EPYC processors disclose?`

- type: `segment_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['epyc', 'amd', 'data center', 'client segment', 'gaming segment', 'embedded']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_7_0002_d4114c99']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.107 | 1 | 0.004 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2024_Item_1_0003_ee436d61', 'TXN_2025_Item_1_0002_e6c099ac', 'TXN_2024_Item_1_0002_9a773c8b', 'AMD_2026_Item_1_0003_ea53a6a5', 'RMBS_2026_Item_7_0004_bb93ee55']` |
| graph |  | 1.126 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0005_8ab9ed73', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2025_Item_7_0004_58e0bdd2', 'INTC_2024_Item_7_0005_d449d027']` |
| hybrid |  | 1.214 | 1 | 0.004 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0005_8ab9ed73', 'TXN_2025_Item_1_0002_e6c099ac', 'AMD_2025_Item_7_0005_36426dd3']` |

### T020: `What export controls affect AI chip sales from the maker of Blackwell architecture?`

- type: `regulation_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['blackwell', 'nvidia', 'export controls', 'china', 'export administration regulations']`
- missing_gold_entities: `[]`
- gold_chunks: `['NVDA_2024_Item_1A_0020_ac4ad7b4', 'NVDA_2024_Item_1A_0022_b1d57eb9']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.105 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2025_Item_1A_0023_67392e5b']` |
| graph |  | 0.994 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 1 | candidate_pool_loss | `[]` | `['NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2025_Item_1A_0019_46eda166', 'INTC_2026_Item_1A_0000_268148d2', 'INTC_2025_Item_1A_0000_ac3a3dbc', 'AMD_2025_Item_1A_0021_16aa3aa2']` |
| hybrid |  | 1.291 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2025_Item_1A_0019_46eda166', 'AMD_2025_Item_1A_0021_16aa3aa2', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'AMD_2026_Item_1A_0021_7fb03412', 'INTC_2026_Item_1A_0000_268148d2']` |

### T021: `Which Asian contract chipmakers fabricate older-generation processors for the developer of Intel 18A?`

- type: `supplier_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel 18a', 'intel', 'tsmc', 'umc', 'smic']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2024_Item_1A_0001_f0f6c35c', 'INTC_2025_Item_1A_0001_65932be2']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.101 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_7_0003_657be427', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2024_Item_7_0000_e2ea081b', 'MU_2024_Item_1A_0025_1809ff3b', 'INTC_2026_Item_7_0004_e8790cb8']` |
| graph |  | 1.020 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 1 | candidate_pool_loss | `[]` | `['INTC_2024_Item_7_0011_0681e088', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_1_0015_adfe2316', 'INTC_2026_Item_7_0003_657be427', 'INTC_2025_Item_1_0004_c5a12b11']` |
| hybrid |  | 1.136 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_1_0004_c01224f1', 'INTC_2024_Item_7_0011_0681e088', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0015_adfe2316']` |

### T022: `Which infrastructure investment firms partner with the maker of Xeon Scalable processors on fab financing?`

- type: `partner_via_product`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['xeon scalable', 'intel', 'brookfield', 'apollo', 'smart capital']`
- missing_gold_entities: `['smart capital']`
- gold_chunks: `['INTC_2025_Item_1_0011_b8759c99', 'INTC_2024_Item_1A_0007_6560bf56']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.102 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2025_Item_1_0007_1d4a96e6', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0008_57402d3f', 'INTC_2024_Item_1_0008_cca3187e']` |
| graph |  | 1.057 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 1 | corpus_not_ready | `[]` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_7_0004_63451c7a']` |
| hybrid |  | 1.243 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2025_Item_1_0007_1d4a96e6']` |

### T023: `Which autonomous driving subsidiary does the developer of Intel Core Ultra operate?`

- type: `subsidiary_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel core ultra', 'intel', 'mobileye']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2024_Item_1_0010_4835f632', 'INTC_2024_Item_7_0010_3742bdd2']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.103 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0004_12c02096', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2026_Item_1_0010_4bfc9726']` |
| graph |  | 1.024 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2025_Item_7_0002_f7953bfd', 'INTC_2024_Item_7_0002_7c82ed88', 'INTC_2026_Item_1_0007_f3f3671c', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0013_cb483288']` |
| hybrid |  | 1.182 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0002_7c82ed88', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2026_Item_1_0010_4bfc9726', 'INTC_2025_Item_1_0008_33a03f9d', 'INTC_2024_Item_7_0001_d1b7bdde']` |

### T024: `Which operating system maker collaborates with the Xeon Scalable processor developer on AI PC platforms?`

- type: `partner_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['xeon scalable', 'intel', 'microsoft', 'ai pc']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2024_Item_7_0002_7c82ed88', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.108 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_7_0000_e2ea081b']` |
| graph |  | 1.278 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 1 | candidate_pool_loss | `[]` | `['INTC_2024_Item_7_0000_e2ea081b', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_1A_0004_64e4feb4', 'INTC_2024_Item_1_0004_692d8999']` |
| hybrid |  | 1.149 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_7_0003_878f7d25', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0004_c01224f1']` |

### T025: `In which U.S. states does the developer of the Intel 18A process operate wafer fabrication facilities?`

- type: `geo_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel 18a', 'intel', 'arizona', 'ohio', 'oregon', 'new mexico']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_1_0014_32e0816b']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.122 | 1 | 0.004 | 0.500 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1_0004_c5a12b11']` | `['INTC_2025_Item_1_0010_5c90fb55', 'INTC_2025_Item_1_0004_c5a12b11', 'MU_2024_Item_1A_0025_1809ff3b', 'INTC_2026_Item_1_0005_f5ba2220', 'TXN_2024_Item_1_0004_06070784']` |
| graph |  | 1.031 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f', 'NVDA_2026_Item_1_0007_bf6a51b6', 'LRCX_2023_Item_1_0005_de991ae1']` |
| hybrid |  | 1.161 | 1 | 0.004 | 0.500 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1_0004_c5a12b11']` | `['AMD_2025_Item_1_0009_c842eea0', 'INTC_2025_Item_1_0010_5c90fb55', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2025_Item_1_0004_c5a12b11', 'INTC_2026_Item_1_0008_c74f560f']` |

### T026: `What U.S. legislative act funds domestic semiconductor manufacturing expansion at the Intel 18A developer?`

- type: `regulator_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel 18a', 'intel', 'chips act']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.100 | 1 | 0.004 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45']` | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45', 'MU_2025_Item_7_0006_849b23ef', 'INTC_2026_Item_1_0005_f5ba2220', 'MU_2025_Item_1A_0029_541d266d']` |
| graph |  | 1.033 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2026_Item_1_0006_d0f653da', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2026_Item_1A_0005_46d4d921', 'INTC_2026_Item_1A_0014_753689d7', 'INTC_2024_Item_7_0011_0681e088']` |
| hybrid |  | 1.229 | 1 | 0.004 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1A_0008_80e72e45']` | `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2026_Item_1A_0006_820d3c64', 'MU_2025_Item_7_0006_849b23ef', 'INTC_2026_Item_1A_0005_46d4d921']` |

### T027: `What advanced driver assistance product lines come from the autonomous driving subsidiary of the Xeon Scalable developer?`

- type: `three_hop_subsidiary_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['xeon scalable', 'intel', 'mobileye', 'mobileye supervision', 'mobileye chauffeur', 'mobileye drive']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2024_Item_7_0010_3742bdd2', 'INTC_2024_Item_7_0014_e766ac95']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.166 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0004_12c02096', 'INTC_2024_Item_7_0005_d449d027', 'NVDA_2024_Item_1_0006_f3efd950', 'NVDA_2025_Item_1_0005_85d95b7e', 'NVDA_2026_Item_1_0004_5a83036d']` |
| graph |  | 1.062 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'AVGO_2023_Item_1_0010_68f5ffd4', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2025_Item_1_0009_c842eea0']` |
| hybrid |  | 1.147 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0004_12c02096', 'NVDA_2026_Item_1_0007_bf6a51b6', 'AVGO_2023_Item_1_0010_68f5ffd4', 'INTC_2024_Item_7_0005_d449d027', 'NVDA_2024_Item_1_0006_f3efd950']` |

### T028: `What consumer storage and DRAM brand is sold by the U.S. supplier of HBM3E memory?`

- type: `product_via_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['hbm3e', 'micron', 'crucial']`
- missing_gold_entities: `[]`
- gold_chunks: `['MU_2025_Item_1_0000_6418b9d4', 'MU_2024_Item_1_0000_82417507']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.131 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0002_74d97a0e', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2023_Item_1_0004_fcaccc78']` |
| graph |  | 1.307 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 1 | candidate_pool_loss | `[]` | `['MU_2024_Item_1_0002_473014b9', 'MU_2024_Item_1_0009_25e18f42', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0001_70be5bda', 'NVDA_2025_Item_1A_0024_d1a5b506']` |
| hybrid |  | 1.149 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['MU_2025_Item_1_0010_ef8bd774', 'RMBS_2025_Item_1_0001_479b0c1e', 'MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0009_25e18f42']` |

### T029: `Why has HBM become critical for modern AI training and inference workloads?`

- type: `topical_memory`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_entities: `['hbm', 'hbm3e', 'ai', 'data center']`
- missing_gold_entities: `[]`
- gold_chunks: `['MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0003_acd8d0ff']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.114 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'QCOM_2025_Item_1_0002_29556203', 'QCOM_2024_Item_1_0002_f2bb0f8a', 'NVDA_2026_Item_1_0005_9725a5a2', 'KLAC_2025_Item_1A_0021_f329ea02']` |
| graph |  | 1.005 | 1 | 0.004 | 1.000 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['MU_2024_Item_1_0003_acd8d0ff', 'MU_2025_Item_1_0001_b64486b7']` | `['MU_2024_Item_1_0001_90ffbd18', 'MU_2024_Item_1_0003_acd8d0ff', 'MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_7_0000_aa4240e3']` |
| hybrid |  | 1.137 | 1 | 0.004 | 1.000 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['MU_2024_Item_1_0003_acd8d0ff', 'MU_2025_Item_1_0001_b64486b7']` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2024_Item_1_0003_acd8d0ff', 'QCOM_2025_Item_1_0002_29556203', 'MU_2025_Item_1_0001_b64486b7']` |

### T030: `Which cloud hyperscalers partner with the EPYC processor maker for server CPU deployments in their data centers?`

- type: `customer_via_product`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['epyc', 'amd', 'microsoft', 'amazon', 'google', 'meta']`
- missing_gold_entities: `['google', 'meta']`
- gold_chunks: `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.131 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_1_0010_842113d9', 'INTC_2024_Item_7_0008_57402d3f']` |
| graph |  | 1.016 | 0 | 0.004 | 0.000 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `['AMD_2024_Item_1_0011_49024c2d', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0001_1abc85fc', 'AMD_2025_Item_1_0002_6fadf6e4']` |
| hybrid |  | 1.172 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f']` |
