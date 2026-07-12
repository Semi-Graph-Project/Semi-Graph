# Phase T Retrieval Baseline

Generated: 2026-07-09T23:45:36

## Run Configuration

- script: `scripts/evaluate_retrieval_quality.py`
- command: `scripts/evaluate_retrieval_quality.py --tools vector graph hybrid --top-k 5 --oracle-k 20 --no-llm-expansion --version-name phase_t_audited_no_expansion`
- query_file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
- query_count: `30`
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
- version_name: `phase_t_audited_no_expansion`
- details_jsonl: `/home/kantinan/programming/project/analytics/Report Experiment/details_audited_noexp.jsonl`
- reextract_tickers_arg: `all`
- resolved_ticker_scope: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- known_tickers: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- scored_queries: `26`
- unscored_queries: `4`
- existing_gold_entities: `59`
- total_gold_entities: `59`

## Overall

| Tool | Scored Queries | Errors | ChunkHit@k | Random ChunkHit@k | Hit Lift | Hit-Random | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 26 | 0 | 0.615 | 0.011 | 53.857 | 0.604 | 0.219 | 0.410 | 0.192 | 0.445 | 0.923 |
| graph | 26 | 0 | 0.769 | 0.011 | 67.322 | 0.758 | 0.334 | 0.481 | 0.231 | 0.623 | 0.923 |
| hybrid | 26 | 0 | 0.846 | 0.011 | 74.054 | 0.835 | 0.336 | 0.590 | 0.346 | 0.604 | 1.000 |

## By Type

| Type | vector ChunkHit | vector ChunkRecall | vector GroupRecall | vector Answerable | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable | hybrid ChunkHit | hybrid ChunkRecall | hybrid GroupRecall | hybrid Answerable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| competitor_product | 0.500 | 0.111 | 0.167 | 0.000 | 1.000 | 0.333 | 0.417 | 0.000 | 1.000 | 0.250 | 0.417 | 0.000 |
| geo_via_product | 1.000 | 0.400 | 0.667 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.200 | 0.333 | 0.000 |
| geo_via_supplier | 1.000 | 0.143 | 0.500 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.533 | 0.750 | 0.500 | 1.000 | 0.367 | 0.750 | 0.500 |
| partner_via_product | 0.667 | 0.317 | 0.444 | 0.333 | 0.667 | 0.300 | 0.222 | 0.000 | 1.000 | 0.467 | 0.556 | 0.333 |
| product_via_company | 1.000 | 0.250 | 0.500 | 0.000 | 1.000 | 0.500 | 0.500 | 0.000 | 1.000 | 0.500 | 0.500 | 0.000 |
| regulation_via_product | 1.000 | 0.375 | 0.667 | 0.000 | 1.000 | 0.125 | 0.667 | 0.000 | 1.000 | 0.125 | 0.667 | 0.000 |
| regulator_via_product | 1.000 | 0.400 | 0.500 | 0.000 | 1.000 | 0.200 | 0.500 | 0.000 | 1.000 | 0.200 | 0.500 | 0.000 |
| risk_via_product | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 0.250 | 0.500 | 0.000 | 1.000 | 0.500 | 1.000 | 1.000 |
| segment_via_product | 1.000 | 0.125 | 0.667 | 0.000 | 1.000 | 0.375 | 0.333 | 0.000 | 1.000 | 0.500 | 1.000 | 1.000 |
| subsidiary_via_product | 1.000 | 0.250 | 0.500 | 0.000 | 1.000 | 0.250 | 0.500 | 0.000 | 1.000 | 0.250 | 0.500 | 0.000 |
| supplier_via_company | 0.500 | 0.167 | 0.500 | 0.500 | 1.000 | 0.667 | 1.000 | 1.000 | 1.000 | 0.583 | 1.000 | 1.000 |
| supplier_via_product | 0.500 | 0.158 | 0.250 | 0.000 | 0.750 | 0.242 | 0.375 | 0.000 | 0.750 | 0.250 | 0.458 | 0.000 |
| three_hop_subsidiary_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| topical_memory | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.600 | 1.000 | 1.000 |
| vector_friendly | 0.667 | 0.367 | 0.667 | 0.667 | 0.667 | 0.350 | 0.667 | 0.667 | 0.667 | 0.350 | 0.667 | 0.667 |

## By Subset

| Subset | vector ChunkHit | vector ChunkRecall | vector GroupRecall | vector Answerable | vector Oracle | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable | graph Oracle | hybrid ChunkHit | hybrid ChunkRecall | hybrid GroupRecall | hybrid Answerable | hybrid Oracle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| reextract_subset | 0.615 | 0.219 | 0.410 | 0.192 | 0.923 | 0.769 | 0.334 | 0.481 | 0.231 | 0.923 | 0.846 | 0.336 | 0.590 | 0.346 | 1.000 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 0.962 | 0.962 | 0.923 | chunk_mapping_loss=2, hit_top_k=20, rerank_loss=3, seed_loss=1 |
| reextract_subset | 0.962 | 0.962 | 0.923 | chunk_mapping_loss=2, hit_top_k=20, rerank_loss=3, seed_loss=1 |

## Paired GroupRecall Test vs Vector

| Subset | Tool | n | Mean Delta GroupRecall | One-sided p |
|---|---|---:|---:|---:|
| full_mixed | graph | 26 | 0.071 | 0.255 |
| full_mixed | hybrid | 26 | 0.179 | 0.015 |
| reextract_subset | graph | 26 | 0.071 | 0.255 |
| reextract_subset | hybrid | 26 | 0.179 | 0.015 |

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
| vector |  | 10.460 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'amd_tsmc_supply_risk': []}` | `['AMD_2024_Item_1A_0002_0a71f57a', 'INTC_2026_Item_1A_0006_820d3c64', 'MU_2024_Item_1A_0001_703555bd', 'MU_2025_Item_1A_0001_8d660135', 'INTC_2024_Item_1A_0000_1a5c79ae']` |
| graph |  | 19.541 | 1 | 0.006 | 0.667 | 1.000 | 1 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_1A_0009_57657610', 'AMD_2025_Item_1A_0011_10eec6d1']` | `{'amd_tsmc_supply_risk': ['AMD_2025_Item_1A_0009_57657610', 'AMD_2025_Item_1A_0011_10eec6d1']}` | `['AMD_2025_Item_1A_0009_57657610', 'INTC_2026_Item_1A_0000_268148d2', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1A_0011_10eec6d1']` |
| hybrid |  | 5.077 | 1 | 0.006 | 0.333 | 1.000 | 1 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2025_Item_1A_0009_57657610']` | `{'amd_tsmc_supply_risk': ['AMD_2025_Item_1A_0009_57657610']}` | `['INTC_2026_Item_1A_0000_268148d2', 'AMD_2024_Item_1A_0002_0a71f57a', 'AMD_2025_Item_1A_0009_57657610', 'INTC_2026_Item_1A_0006_820d3c64', 'AMD_2025_Item_1_0009_c842eea0']` |

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
| vector |  | 0.116 | 0 | 0.013 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hopper_evidence': [], 'supplier_evidence': []}` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0013_cb483288', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_1_0014_32e0816b', 'AMD_2024_Item_1_0012_9561038a']` |
| graph |  | 1.270 | 0 | 0.013 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `{'hopper_evidence': [], 'supplier_evidence': []}` | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1A_0000_268148d2', 'INTC_2026_Item_7_0017_86b90f80']` |
| hybrid |  | 1.228 | 0 | 0.013 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hopper_evidence': [], 'supplier_evidence': []}` | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'INTC_2026_Item_1_0013_cb483288', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0006_d0f653da']` |

### T003: `Who produces the dense memory chips that power modern AI training accelerators?`

- type: `supplier_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['micron', 'hbm', 'ai accelerators']`
- missing_gold_entities: `[]`
- gold_chunks: `['MU_2023_Item_1A_0003_92be33e3', 'MU_2025_Item_1A_0004_836bee10', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']`
- gold_evidence_groups: `{'direct_answer': ['MU_2023_Item_1A_0003_92be33e3', 'MU_2025_Item_1A_0004_836bee10'], 'supplier_context': ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.129 | 0 | 0.011 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'direct_answer': [], 'supplier_context': []}` | `['RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2026_Item_1_0005_9725a5a2', 'INTC_2026_Item_1_0004_c01224f1']` |
| graph |  | 1.340 | 1 | 0.011 | 0.400 | 0.500 | 0 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']` | `{'direct_answer': [], 'supplier_context': ['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']}` | `['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2024_Item_7_0005_d449d027', 'AMD_2024_Item_1A_0005_a057bdb2']` |
| hybrid |  | 1.065 | 1 | 0.011 | 0.200 | 0.500 | 0 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2025_Item_1_0008_a4407f7e']` | `{'direct_answer': [], 'supplier_context': ['NVDA_2025_Item_1_0008_a4407f7e']}` | `['INTC_2026_Item_1_0008_c74f560f', 'RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'NVDA_2025_Item_1_0008_a4407f7e', 'INTC_2025_Item_7_0003_878f7d25']` |

### T004: `What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?`

- type: `competitor_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel', 'amd', 'amd instinct']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2026_Item_1_0003_ea53a6a5', 'AMD_2026_Item_1_0007_f252541b', 'AMD_2025_Item_1_0006_551768e4', 'AMD_2024_Item_1_0009_01379c5a', 'INTC_2026_Item_1_0008_c74f560f', 'AMD_2024_Item_1_0011_49024c2d']`
- gold_evidence_groups: `{'direct_answer': ['AMD_2026_Item_1_0003_ea53a6a5', 'AMD_2026_Item_1_0007_f252541b', 'AMD_2025_Item_1_0006_551768e4', 'AMD_2024_Item_1_0009_01379c5a'], 'competitor_context': ['INTC_2026_Item_1_0008_c74f560f', 'AMD_2024_Item_1_0011_49024c2d']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.120 | 0 | 0.013 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'direct_answer': [], 'competitor_context': []}` | `['INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'AMD_2026_Item_1_0004_b5e66359']` |
| graph |  | 1.115 | 1 | 0.013 | 0.333 | 0.500 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2024_Item_1_0011_49024c2d']` | `{'direct_answer': [], 'competitor_context': ['AMD_2024_Item_1_0011_49024c2d', 'INTC_2026_Item_1_0008_c74f560f']}` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2025_Item_7_0002_f7953bfd', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d']` |
| hybrid |  | 1.084 | 1 | 0.013 | 0.167 | 0.500 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0008_c74f560f']` | `{'direct_answer': [], 'competitor_context': ['INTC_2026_Item_1_0008_c74f560f']}` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2025_Item_7_0002_f7953bfd', 'AMD_2025_Item_1_0009_c842eea0']` |

### T005: `What political risks affect the home country of the leading pure-play semiconductor foundry?`

- type: `geo_via_supplier`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['tsmc', 'taiwan', 'political risk']`
- missing_gold_entities: `[]`
- gold_chunks: `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1A_0032_0a1cf7f3', 'AMD_2026_Item_1A_0032_c870df0c', 'NVDA_2024_Item_1A_0022_b1d57eb9']`
- gold_evidence_groups: `{'foundry_identity': ['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17'], 'taiwan_political_risk': ['AMD_2025_Item_1A_0032_0a1cf7f3', 'AMD_2026_Item_1A_0032_c870df0c', 'NVDA_2024_Item_1A_0022_b1d57eb9']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.098 | 1 | 0.015 | 0.143 | 0.500 | 0 | 0.200 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2025_Item_1A_0032_0a1cf7f3']` | `{'foundry_identity': [], 'taiwan_political_risk': ['AMD_2025_Item_1A_0032_0a1cf7f3']}` | `['QCOM_2023_Item_1A_0031_545bf96a', 'INTC_2026_Item_1A_0002_066bd50c', 'ENTG_2026_Item_1_0004_6f32215b', 'MU_2023_Item_1A_0003_92be33e3', 'AMD_2025_Item_1A_0032_0a1cf7f3']` |
| graph |  | 1.472 | 0 | 0.015 | 0.000 | 0.000 | 0 | 0.000 | 1 | 0 | 0 | 1 | seed_loss | `[]` | `{'foundry_identity': [], 'taiwan_political_risk': []}` | `['QCOM_2023_Item_1A_0023_7335c8fd', 'RMBS_2024_Item_1A_0009_16baaed9', 'INTC_2025_Item_1A_0000_ac3a3dbc', 'INTC_2026_Item_1A_0000_268148d2', 'RMBS_2025_Item_1_0001_479b0c1e']` |
| hybrid |  | 1.194 | 0 | 0.015 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'foundry_identity': [], 'taiwan_political_risk': []}` | `['QCOM_2023_Item_1A_0023_7335c8fd', 'QCOM_2023_Item_1A_0031_545bf96a', 'INTC_2026_Item_1A_0002_066bd50c', 'RMBS_2024_Item_1A_0009_16baaed9', 'INTC_2025_Item_1A_0000_ac3a3dbc']` |

### T006: `Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?`

- type: `supplier_via_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['nvidia', 'tsmc', 'samsung', 'semiconductor wafers']`
- missing_gold_entities: `[]`
- gold_chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']`
- gold_evidence_groups: `{'wafer_foundry_supplier': ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.095 | 1 | 0.006 | 0.333 | 1.000 | 1 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2026_Item_1_0007_bf6a51b6']` | `{'wafer_foundry_supplier': ['NVDA_2026_Item_1_0007_bf6a51b6']}` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1A_0025_1809ff3b', 'AMKR_2026_Item_1_0003_8dee603e', 'NVDA_2025_Item_1_0002_b74647bb', 'NVDA_2024_Item_1_0002_2ddf2e3b']` |
| graph |  | 0.921 | 1 | 0.006 | 1.000 | 1.000 | 1 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']` | `{'wafer_foundry_supplier': ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']}` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` |
| hybrid |  | 1.047 | 1 | 0.006 | 1.000 | 1.000 | 1 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0007_bae70036']` | `{'wafer_foundry_supplier': ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']}` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'MU_2024_Item_1A_0025_1809ff3b', 'NVDA_2024_Item_1_0007_bae70036', 'AMKR_2026_Item_1_0003_8dee603e']` |

### T007: `What graphics product line does AMD offer to compete with NVIDIA's RTX series?`

- type: `competitor_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['amd', 'nvidia', 'radeon', 'geforce rtx']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2024_Item_1_0009_01379c5a', 'AMD_2025_Item_1_0006_551768e4', 'AMD_2026_Item_1_0007_f252541b', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2024_Item_1_0003_59fa75a8', 'NVDA_2025_Item_1_0003_ccc9ed65', 'NVDA_2026_Item_1_0003_0297d539']`
- gold_evidence_groups: `{'amd_radeon_product_line': ['AMD_2024_Item_1_0009_01379c5a', 'AMD_2025_Item_1_0006_551768e4', 'AMD_2026_Item_1_0007_f252541b'], 'amd_nvidia_graphics_competition': ['AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17'], 'nvidia_rtx_product_reference': ['NVDA_2024_Item_1_0003_59fa75a8', 'NVDA_2025_Item_1_0003_ccc9ed65', 'NVDA_2026_Item_1_0003_0297d539']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.088 | 1 | 0.019 | 0.222 | 0.333 | 0 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0009_c842eea0']` | `{'amd_radeon_product_line': [], 'amd_nvidia_graphics_competition': ['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17'], 'nvidia_rtx_product_reference': []}` | `['AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0007_0ffd6ad4', 'AMD_2025_Item_1_0009_c842eea0']` |
| graph |  | 0.935 | 1 | 0.019 | 0.333 | 0.333 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d']` | `{'amd_radeon_product_line': [], 'amd_nvidia_graphics_competition': ['AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17'], 'nvidia_rtx_product_reference': []}` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232']` |
| hybrid |  | 0.992 | 1 | 0.019 | 0.333 | 0.333 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2024_Item_1_0011_49024c2d']` | `{'amd_radeon_product_line': [], 'amd_nvidia_graphics_competition': ['AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17'], 'nvidia_rtx_product_reference': []}` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965']` |

### T008: `Who supplies the high-bandwidth memory used in NVIDIA's H200 data center accelerator?`

- type: `supplier_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['h200', 'nvidia', 'hbm', 'micron', 'sk hynix', 'samsung']`
- missing_gold_entities: `[]`
- gold_chunks: `['NVDA_2026_Item_1_0009_8c403127', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2026_Item_7_0001_485abbd3', 'NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0003_acd8d0ff']`
- gold_evidence_groups: `{'h200_nvidia_anchor': ['NVDA_2026_Item_1_0009_8c403127', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2026_Item_7_0001_485abbd3', 'NVDA_2025_Item_7_0002_b40db6b2'], 'nvidia_memory_suppliers': ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6'], 'micron_hbm_context': ['MU_2024_Item_1_0001_90ffbd18', 'MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0003_acd8d0ff']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.090 | 1 | 0.021 | 0.300 | 0.333 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['MU_2024_Item_1_0003_acd8d0ff', 'MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0001_90ffbd18']` | `{'h200_nvidia_anchor': [], 'nvidia_memory_suppliers': [], 'micron_hbm_context': ['MU_2024_Item_1_0001_90ffbd18', 'MU_2024_Item_1_0003_acd8d0ff', 'MU_2025_Item_1_0001_b64486b7']}` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2025_Item_1_0002_b74647bb', 'MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0001_90ffbd18']` |
| graph |  | 0.950 | 1 | 0.021 | 0.400 | 0.667 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2026_Item_1_0009_8c403127', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_7_0001_485abbd3']` | `{'h200_nvidia_anchor': ['NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2026_Item_1_0009_8c403127', 'NVDA_2026_Item_7_0001_485abbd3'], 'nvidia_memory_suppliers': ['NVDA_2024_Item_1_0007_bae70036'], 'micron_hbm_context': []}` | `['NVDA_2026_Item_1_0009_8c403127', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'AMD_2024_Item_1_0011_49024c2d', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_7_0001_485abbd3']` |
| hybrid |  | 1.056 | 1 | 0.021 | 0.300 | 0.667 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2026_Item_1_0009_8c403127', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2026_Item_1A_0022_3d4f4d9b']` | `{'h200_nvidia_anchor': ['NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2026_Item_1_0009_8c403127'], 'nvidia_memory_suppliers': [], 'micron_hbm_context': ['MU_2024_Item_1_0003_acd8d0ff']}` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2026_Item_1_0009_8c403127', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'AMD_2024_Item_1_0011_49024c2d']` |

### T009: `How do export controls affect NVIDIA's data center business?`

- type: `risk_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_entities: `['nvidia', 'export controls', 'data center', 'china']`
- missing_gold_entities: `[]`
- gold_chunks: `['NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9']`
- gold_evidence_groups: `{'export_control_restrictions': ['NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537'], 'data_center_business_impact': ['NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.099 | 1 | 0.017 | 0.500 | 1.000 | 1 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2025_Item_1A_0023_67392e5b']` | `{'export_control_restrictions': ['NVDA_2025_Item_1A_0023_67392e5b'], 'data_center_business_impact': ['NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2026_Item_1A_0024_b70c7a18']}` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2025_Item_1A_0019_46eda166']` |
| graph |  | 1.198 | 1 | 0.017 | 0.250 | 0.500 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537']` | `{'export_control_restrictions': ['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537'], 'data_center_business_impact': []}` | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2025_Item_1A_0024_d1a5b506', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2025_Item_1A_0003_9003fee7']` |
| hybrid |  | 1.127 | 1 | 0.017 | 0.500 | 1.000 | 1 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9']` | `{'export_control_restrictions': ['NVDA_2025_Item_1A_0023_67392e5b'], 'data_center_business_impact': ['NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2026_Item_1A_0024_b70c7a18']}` | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2024_Item_1A_0022_b1d57eb9']` |

### T010: `Which materials and purity solutions does Entegris provide to semiconductor manufacturers?`

- type: `vector_friendly`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector']`
- gold_entities: `['entegris', 'materials solutions', 'advanced purity solutions']`
- missing_gold_entities: `[]`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0007_4615acf5', 'ENTG_2026_Item_7_0002_0ba0c07d']`
- gold_evidence_groups: `{'entegis_materials_and_purity_segments': ['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0007_4615acf5', 'ENTG_2026_Item_7_0002_0ba0c07d']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.092 | 1 | 0.011 | 0.600 | 1.000 | 1 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e']` | `{'entegis_materials_and_purity_segments': ['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0000_a9f06bac']}` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0009_ca7ef011', 'ENTG_2025_Item_1_0008_700da46e']` |
| graph |  | 0.933 | 1 | 0.011 | 0.800 | 1.000 | 1 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_7_0002_0ba0c07d', 'ENTG_2025_Item_1_0008_700da46e']` | `{'entegis_materials_and_purity_segments': ['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_7_0002_0ba0c07d']}` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0013_d310ee7e', 'ENTG_2026_Item_7_0002_0ba0c07d', 'ENTG_2025_Item_1_0008_700da46e']` |
| hybrid |  | 1.026 | 1 | 0.011 | 0.800 | 1.000 | 1 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0007_4615acf5']` | `{'entegis_materials_and_purity_segments': ['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0007_4615acf5']}` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0007_4615acf5']` |

### T011: `What gross margin impact did Entegris expect from its useful-life accounting estimate change?`

- type: `vector_friendly`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector']`
- gold_entities: `['entegris', 'gross margin', 'depreciation']`
- missing_gold_entities: `[]`
- gold_chunks: `['ENTG_2026_Item_7_0003_d6e71ea2']`
- gold_evidence_groups: `{'useful_life_gross_margin_impact': ['ENTG_2026_Item_7_0003_d6e71ea2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.080 | 0 | 0.002 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'useful_life_gross_margin_impact': []}` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'KLAC_2025_Item_7_0009_be3ecb77', 'KLAC_2024_Item_7_0008_8308f577', 'KLAC_2023_Item_7_0011_e4c656e2', 'ENTG_2026_Item_7_0015_6af235b4']` |
| graph |  | 0.930 | 0 | 0.002 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `{'useful_life_gross_margin_impact': []}` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2026_Item_7_0014_7f63f75a', 'ENTG_2024_Item_7_0019_28ef5c6a', 'ENTG_2025_Item_7_0016_c8496ed0']` |
| hybrid |  | 1.015 | 0 | 0.002 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'useful_life_gross_margin_impact': []}` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2026_Item_7_0015_6af235b4', 'ENTG_2024_Item_7_0017_71caf017', 'KLAC_2025_Item_7_0009_be3ecb77', 'ENTG_2026_Item_7_0014_7f63f75a']` |

### T012: `What are Entegris's main business segments?`

- type: `vector_friendly`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector']`
- gold_entities: `['entegris', 'materials solutions', 'advanced purity solutions']`
- missing_gold_entities: `[]`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0007_4615acf5']`
- gold_evidence_groups: `{'entegris_business_segments': ['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0007_4615acf5']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.074 | 1 | 0.009 | 0.500 | 1.000 | 1 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac']` | `{'entegris_business_segments': ['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac']}` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2026_Item_1_0014_8712752e', 'ENTG_2024_Item_1_0019_b6aee1a3']` |
| graph |  | 0.934 | 1 | 0.009 | 0.250 | 1.000 | 1 | 0.200 | 1 | 1 | 1 | 1 | hit_top_k | `['ENTG_2026_Item_1_0000_a9f06bac']` | `{'entegris_business_segments': ['ENTG_2026_Item_1_0000_a9f06bac']}` | `['ENTG_2024_Item_1_0008_9f625423', 'ENTG_2024_Item_1_0009_c1b0a473', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2026_Item_1_0013_2fa9f11c', 'ENTG_2026_Item_1_0000_a9f06bac']` |
| hybrid |  | 0.999 | 1 | 0.009 | 0.250 | 1.000 | 1 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2025_Item_1_0000_7efdfd60']` | `{'entegris_business_segments': ['ENTG_2025_Item_1_0000_7efdfd60']}` | `['ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2024_Item_1_0008_9f625423', 'ENTG_2024_Item_1_0009_c1b0a473']` |

### T013: `What is AMD's latest FY2025 revenue and gross margin?`

- type: `financial_exact_metric`
- subset: `reextract_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['financial']`
- gold_entities: `['amd', 'revenue', 'gross margin']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`
- gold_evidence_groups: `{}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.103 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `['INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003', 'AMD_2024_Item_1_0001_84491be9', 'INTC_2024_Item_1_0003_02f7f00d', 'AMD_2026_Item_7_0006_2b606b28']` |
| graph |  | 0.906 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `{}` | `['AMD_2025_Item_7_0001_223169cf', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2024_Item_7_0004_67034475', 'AMD_2025_Item_7_0003_a2d9991c']` |
| hybrid |  | 1.159 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `['AMD_2026_Item_7_0006_2b606b28', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0001_223169cf', 'INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003']` |

### T014: `What has AMD announced recently?`

- type: `news_recent_event`
- subset: `reextract_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['news']`
- gold_entities: `['amd']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`
- gold_evidence_groups: `{}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.078 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_7_0000_6b145a7b']` |
| graph |  | 0.886 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `{}` | `['AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2026_Item_1A_0002_72e02a77', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_1_0013_9fc1134b']` |
| hybrid |  | 0.986 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_1A_0002_72e02a77']` |

### T015: `What is the relationship between KLA yield improvement tools and downstream AMD gross margin risk?`

- type: `graph_multihop`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['kla', 'tsmc', 'amd', 'failure to achieve expected manufacturing yields', 'gross margin']`
- missing_gold_entities: `[]`
- gold_chunks: `['KLAC_2023_Item_1_0000_849299a1', 'AMD_2025_Item_1A_0011_10eec6d1', 'AMD_2025_Item_1A_0009_57657610', 'AMD_2024_Item_1A_0008_027b0f68', 'AMD_2024_Item_1A_0011_fbb67bc3']`
- gold_evidence_groups: `{'kla_yield_improvement_tools': ['KLAC_2023_Item_1_0000_849299a1'], 'amd_yield_gross_margin_risk': ['AMD_2025_Item_1A_0011_10eec6d1', 'AMD_2025_Item_1A_0009_57657610', 'AMD_2024_Item_1A_0008_027b0f68', 'AMD_2024_Item_1A_0011_fbb67bc3']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.100 | 0 | 0.011 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'kla_yield_improvement_tools': [], 'amd_yield_gross_margin_risk': []}` | `['MU_2023_Item_1A_0001_1b8ef3ed', 'AVGO_2025_Item_1A_0008_7b345bfe', 'INTC_2024_Item_7_0015_575e5365', 'AVGO_2023_Item_1A_0018_717a6eeb', 'KLAC_2023_Item_7_0011_e4c656e2']` |
| graph |  | 0.938 | 1 | 0.011 | 0.400 | 0.500 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_1A_0009_57657610', 'AMD_2024_Item_1A_0008_027b0f68']` | `{'kla_yield_improvement_tools': [], 'amd_yield_gross_margin_risk': ['AMD_2024_Item_1A_0008_027b0f68', 'AMD_2025_Item_1A_0009_57657610']}` | `['AMD_2025_Item_1A_0009_57657610', 'INTC_2026_Item_1A_0000_268148d2', 'AMD_2024_Item_1A_0008_027b0f68', 'INTC_2025_Item_1A_0000_ac3a3dbc', 'AMD_2024_Item_1A_0015_22ab1f05']` |
| hybrid |  | 1.024 | 1 | 0.011 | 0.400 | 0.500 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2025_Item_1A_0009_57657610', 'AMD_2024_Item_1A_0008_027b0f68']` | `{'kla_yield_improvement_tools': [], 'amd_yield_gross_margin_risk': ['AMD_2024_Item_1A_0008_027b0f68', 'AMD_2025_Item_1A_0009_57657610']}` | `['AMD_2025_Item_1A_0009_57657610', 'MU_2023_Item_1A_0001_1b8ef3ed', 'AVGO_2025_Item_1A_0008_7b345bfe', 'INTC_2026_Item_1A_0000_268148d2', 'AMD_2024_Item_1A_0008_027b0f68']` |

### T016: `qwerty zzz random semiconductor nonsense`

- type: `off_corpus`
- subset: `legacy_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `[]`
- gold_entities: `[]`
- missing_gold_entities: `[]`
- gold_chunks: `[]`
- gold_evidence_groups: `{}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.077 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `['AMKR_2026_Item_1A_0003_a2e1fdfd', 'AMKR_2025_Item_1A_0003_a68b7182', 'INTC_2025_Item_1_0001_01b4d21e', 'INTC_2025_Item_1_0002_ba6af228', 'QCOM_2024_Item_1_0009_e0fec737']` |
| graph |  | 0.931 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | unscored_discovery | `[]` | `{}` | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'NVDA_2025_Item_1_0008_a4407f7e']` |
| hybrid |  | 0.940 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `['AMKR_2026_Item_1A_0003_a2e1fdfd', 'NVDA_2024_Item_1_0007_bae70036', 'AMKR_2025_Item_1A_0003_a68b7182', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2025_Item_1_0001_01b4d21e']` |

### T017: `Which Taiwanese contract chipmaker fabricates AMD's processors?`

- type: `supplier_via_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['amd', 'tsmc']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2024_Item_1A_0007_2f2587e1', 'AMD_2025_Item_1A_0008_27d1b419', 'AMD_2026_Item_1A_0007_6d154102', 'AMD_2024_Item_1_0012_9561038a', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']`
- gold_evidence_groups: `{'amd_tsmc_processor_foundry': ['AMD_2024_Item_1A_0007_2f2587e1', 'AMD_2025_Item_1A_0008_27d1b419', 'AMD_2026_Item_1A_0007_6d154102', 'AMD_2024_Item_1_0012_9561038a', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.082 | 0 | 0.013 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'amd_tsmc_processor_foundry': []}` | `['AMD_2024_Item_1_0001_84491be9', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2024_Item_1_0013_596acde4', 'AMD_2025_Item_1_0004_7a6fa20c']` |
| graph |  | 0.909 | 1 | 0.013 | 0.333 | 1.000 | 1 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` | `{'amd_tsmc_processor_foundry': ['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']}` | `['AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'RMBS_2025_Item_1_0001_479b0c1e']` |
| hybrid |  | 1.452 | 1 | 0.013 | 0.167 | 1.000 | 1 | 0.200 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2025_Item_1_0009_c842eea0']` | `{'amd_tsmc_processor_foundry': ['AMD_2025_Item_1_0009_c842eea0']}` | `['AMD_2025_Item_1_0008_db609f8f', 'MU_2024_Item_1A_0025_1809ff3b', 'AMD_2026_Item_1_0009_ac9cc232', 'NVDA_2026_Item_1_0007_bf6a51b6', 'AMD_2025_Item_1_0009_c842eea0']` |

### T018: `Which gaming console makers partner with the Ryzen processor company?`

- type: `partner_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['ryzen', 'amd', 'sony', 'microsoft', 'valve']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2024_Item_1_0005_7be264c6']`
- gold_evidence_groups: `{'amd_console_partners': ['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2024_Item_1_0005_7be264c6']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.079 | 1 | 0.009 | 0.750 | 1.000 | 1 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2024_Item_1_0006_e41aed21']` | `{'amd_console_partners': ['AMD_2024_Item_1_0006_e41aed21', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0004_b5e66359']}` | `['AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2024_Item_1_0006_e41aed21']` |
| graph |  | 0.888 | 0 | 0.009 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `{'amd_console_partners': []}` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_1_0001_17c029a7']` |
| hybrid |  | 1.025 | 1 | 0.009 | 0.750 | 1.000 | 1 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c']` | `{'amd_console_partners': ['AMD_2024_Item_1_0006_e41aed21', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0004_b5e66359']}` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0004_7a6fa20c']` |

### T019: `What revenue segments does the developer of EPYC processors disclose?`

- type: `segment_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['epyc', 'amd', 'data center', 'client', 'gaming', 'embedded']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2025_Item_1_0002_6fadf6e4', 'AMD_2026_Item_1_0002_9bce02c2', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2026_Item_7_0005_8ab9ed73']`
- gold_evidence_groups: `{'epyc_amd_anchor': ['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0002_6fadf6e4', 'AMD_2026_Item_1_0002_9bce02c2'], 'amd_reportable_segments': ['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0002_6fadf6e4', 'AMD_2026_Item_1_0002_9bce02c2'], 'segment_revenue_disclosure': ['AMD_2024_Item_7_0002_d4114c99', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2026_Item_7_0005_8ab9ed73']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.092 | 1 | 0.017 | 0.125 | 0.667 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0003_ee436d61']` | `{'epyc_amd_anchor': ['AMD_2024_Item_1_0003_ee436d61'], 'amd_reportable_segments': ['AMD_2024_Item_1_0003_ee436d61'], 'segment_revenue_disclosure': []}` | `['AMD_2024_Item_1_0003_ee436d61', 'TXN_2025_Item_1_0002_e6c099ac', 'TXN_2024_Item_1_0002_9a773c8b', 'AMD_2026_Item_1_0003_ea53a6a5', 'RMBS_2026_Item_7_0004_bb93ee55']` |
| graph |  | 0.966 | 1 | 0.017 | 0.375 | 0.333 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0005_8ab9ed73', 'AMD_2025_Item_7_0005_36426dd3']` | `{'epyc_amd_anchor': [], 'amd_reportable_segments': [], 'segment_revenue_disclosure': ['AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2026_Item_7_0005_8ab9ed73']}` | `['AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0005_8ab9ed73', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2025_Item_7_0004_58e0bdd2', 'INTC_2024_Item_7_0005_d449d027']` |
| hybrid |  | 0.977 | 1 | 0.017 | 0.500 | 1.000 | 1 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0005_8ab9ed73', 'AMD_2025_Item_7_0005_36426dd3']` | `{'epyc_amd_anchor': ['AMD_2024_Item_1_0003_ee436d61'], 'amd_reportable_segments': ['AMD_2024_Item_1_0003_ee436d61'], 'segment_revenue_disclosure': ['AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2026_Item_7_0005_8ab9ed73']}` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0005_8ab9ed73', 'TXN_2025_Item_1_0002_e6c099ac', 'AMD_2025_Item_7_0005_36426dd3']` |

### T020: `What export controls affect AI chip sales from the maker of Blackwell architecture?`

- type: `regulation_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['blackwell', 'nvidia', 'export controls', 'china', 'export administration regulations']`
- missing_gold_entities: `[]`
- gold_chunks: `['NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2024_Item_1A_0020_ac4ad7b4', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2026_Item_1A_0024_b70c7a18']`
- gold_evidence_groups: `{'blackwell_nvidia_anchor': ['NVDA_2025_Item_1_0009_7a56593b'], 'export_control_restrictions': ['NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2024_Item_1A_0020_ac4ad7b4', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2026_Item_1A_0024_b70c7a18'], 'ai_chip_sales_impact': ['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2026_Item_1A_0024_b70c7a18']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.078 | 1 | 0.017 | 0.375 | 0.667 | 0 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2025_Item_1A_0023_67392e5b']` | `{'blackwell_nvidia_anchor': [], 'export_control_restrictions': ['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537'], 'ai_chip_sales_impact': ['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537']}` | `['AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2025_Item_1A_0023_67392e5b']` |
| graph |  | 0.944 | 1 | 0.017 | 0.125 | 0.667 | 0 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1A_0019_46eda166']` | `{'blackwell_nvidia_anchor': [], 'export_control_restrictions': ['NVDA_2025_Item_1A_0019_46eda166'], 'ai_chip_sales_impact': ['NVDA_2025_Item_1A_0019_46eda166']}` | `['NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2025_Item_1A_0019_46eda166', 'INTC_2026_Item_1A_0000_268148d2', 'INTC_2025_Item_1A_0000_ac3a3dbc', 'AMD_2026_Item_1A_0031_ee99bb7d']` |
| hybrid |  | 0.949 | 1 | 0.017 | 0.125 | 0.667 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2025_Item_1A_0019_46eda166']` | `{'blackwell_nvidia_anchor': [], 'export_control_restrictions': ['NVDA_2025_Item_1A_0019_46eda166'], 'ai_chip_sales_impact': ['NVDA_2025_Item_1A_0019_46eda166']}` | `['NVDA_2025_Item_1A_0019_46eda166', 'AMD_2025_Item_1A_0021_16aa3aa2', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'AMD_2026_Item_1A_0021_7fb03412', 'INTC_2026_Item_1A_0000_268148d2']` |

### T021: `Which Asian foundries are relevant to third-party foundry risk and mature-node competition for the developer of Intel 18A?`

- type: `supplier_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel 18a', 'intel', 'tsmc', 'umc', 'smic']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_1_0015_adfe2316', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2026_Item_1_0005_f5ba2220', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2025_Item_1A_0001_65932be2']`
- gold_evidence_groups: `{'intel_18a_anchor': ['INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_1_0015_adfe2316'], 'third_party_foundry_risk': ['INTC_2026_Item_1A_0006_820d3c64', 'INTC_2026_Item_1_0005_f5ba2220'], 'mature_node_foundry_competitors': ['INTC_2026_Item_1_0008_c74f560f', 'INTC_2025_Item_1A_0001_65932be2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.117 | 1 | 0.013 | 0.333 | 0.667 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1A_0001_65932be2', 'INTC_2026_Item_1A_0006_820d3c64']` | `{'intel_18a_anchor': [], 'third_party_foundry_risk': ['INTC_2026_Item_1A_0006_820d3c64'], 'mature_node_foundry_competitors': ['INTC_2025_Item_1A_0001_65932be2']}` | `['INTC_2025_Item_1A_0001_65932be2', 'INTC_2025_Item_7_0010_325410df', 'INTC_2026_Item_1A_0001_7d386648', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2026_Item_1A_0002_066bd50c']` |
| graph |  | 0.964 | 1 | 0.013 | 0.167 | 0.333 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2026_Item_1_0008_c74f560f']` | `{'intel_18a_anchor': [], 'third_party_foundry_risk': [], 'mature_node_foundry_competitors': ['INTC_2026_Item_1_0008_c74f560f']}` | `['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` |
| hybrid |  | 1.165 | 1 | 0.013 | 0.500 | 0.667 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2025_Item_1A_0001_65932be2']` | `{'intel_18a_anchor': [], 'third_party_foundry_risk': ['INTC_2026_Item_1A_0006_820d3c64'], 'mature_node_foundry_competitors': ['INTC_2025_Item_1A_0001_65932be2', 'INTC_2026_Item_1_0008_c74f560f']}` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2025_Item_1A_0001_65932be2', 'INTC_2025_Item_7_0010_325410df', 'NVDA_2026_Item_1_0007_bf6a51b6']` |

### T022: `Which infrastructure investment firms partner with the maker of Xeon Scalable processors on fab financing?`

- type: `partner_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['xeon scalable', 'intel', 'brookfield', 'apollo', 'smart capital strategy']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2025_Item_1_0011_b8759c99', 'INTC_2024_Item_1A_0007_6560bf56', 'INTC_2026_Item_1A_0006_820d3c64']`
- gold_evidence_groups: `{'xeon_intel_anchor': ['INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_1_0004_692d8999'], 'smart_capital_financing': ['INTC_2025_Item_1_0011_b8759c99', 'INTC_2024_Item_1A_0007_6560bf56'], 'infrastructure_investment_partners': ['INTC_2025_Item_1_0011_b8759c99', 'INTC_2026_Item_1A_0006_820d3c64']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.093 | 1 | 0.011 | 0.200 | 0.333 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2024_Item_1_0004_692d8999']` | `{'xeon_intel_anchor': ['INTC_2024_Item_1_0004_692d8999'], 'smart_capital_financing': [], 'infrastructure_investment_partners': []}` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2025_Item_1_0007_1d4a96e6', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0008_57402d3f', 'INTC_2024_Item_1_0008_cca3187e']` |
| graph |  | 0.935 | 1 | 0.011 | 0.400 | 0.333 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0011_4307b8ad']` | `{'xeon_intel_anchor': ['INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0011_4307b8ad'], 'smart_capital_financing': [], 'infrastructure_investment_partners': []}` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_7_0004_63451c7a']` |
| hybrid |  | 1.071 | 1 | 0.011 | 0.400 | 0.333 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0011_4307b8ad']` | `{'xeon_intel_anchor': ['INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0011_4307b8ad'], 'smart_capital_financing': [], 'infrastructure_investment_partners': []}` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0011_4307b8ad', 'INTC_2025_Item_1_0007_1d4a96e6']` |

### T023: `Which autonomous driving subsidiary does the developer of Intel Core Ultra operate?`

- type: `subsidiary_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel core ultra', 'intel', 'mobileye']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2026_Item_1_0010_4bfc9726', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_1_0010_4835f632', 'INTC_2024_Item_7_0010_3742bdd2']`
- gold_evidence_groups: `{'core_ultra_intel_anchor': ['INTC_2026_Item_1_0010_4bfc9726', 'INTC_2024_Item_7_0000_e2ea081b'], 'mobileye_autonomous_driving': ['INTC_2024_Item_7_0010_3742bdd2', 'INTC_2024_Item_1_0010_4835f632']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.134 | 1 | 0.009 | 0.250 | 0.500 | 0 | 0.200 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0010_4bfc9726']` | `{'core_ultra_intel_anchor': ['INTC_2026_Item_1_0010_4bfc9726'], 'mobileye_autonomous_driving': []}` | `['NVDA_2024_Item_1_0004_12c02096', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2026_Item_1_0010_4bfc9726']` |
| graph |  | 0.949 | 1 | 0.009 | 0.250 | 0.500 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2024_Item_7_0000_e2ea081b']` | `{'core_ultra_intel_anchor': ['INTC_2024_Item_7_0000_e2ea081b'], 'mobileye_autonomous_driving': []}` | `['INTC_2024_Item_7_0000_e2ea081b', 'INTC_2025_Item_7_0002_f7953bfd', 'INTC_2024_Item_7_0002_7c82ed88', 'INTC_2026_Item_1_0007_f3f3671c', 'INTC_2026_Item_1_0013_cb483288']` |
| hybrid |  | 1.034 | 1 | 0.009 | 0.250 | 0.500 | 0 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0010_4bfc9726']` | `{'core_ultra_intel_anchor': ['INTC_2026_Item_1_0010_4bfc9726'], 'mobileye_autonomous_driving': []}` | `['INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_7_0002_7c82ed88', 'INTC_2026_Item_1_0010_4bfc9726', 'INTC_2024_Item_7_0001_d1b7bdde', 'INTC_2025_Item_1_0008_33a03f9d']` |

### T024: `Which operating system maker collaborates with the Xeon Scalable processor developer on AI PC platforms?`

- type: `partner_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['xeon scalable', 'intel', 'microsoft', 'ai pc']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0002_7c82ed88', 'INTC_2024_Item_7_0001_d1b7bdde']`
- gold_evidence_groups: `{'xeon_intel_anchor': ['INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_1_0004_692d8999'], 'microsoft_ai_pc_collaboration': ['INTC_2024_Item_7_0002_7c82ed88'], 'ai_pc_platform_context': ['INTC_2024_Item_7_0002_7c82ed88', 'INTC_2024_Item_7_0001_d1b7bdde']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.092 | 0 | 0.009 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'xeon_intel_anchor': [], 'microsoft_ai_pc_collaboration': [], 'ai_pc_platform_context': []}` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_7_0000_e2ea081b']` |
| graph |  | 0.952 | 1 | 0.009 | 0.500 | 0.333 | 0 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_1_0004_692d8999']` | `{'xeon_intel_anchor': ['INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0011_4307b8ad'], 'microsoft_ai_pc_collaboration': [], 'ai_pc_platform_context': []}` | `['INTC_2024_Item_7_0000_e2ea081b', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_7_0004_63451c7a', 'INTC_2024_Item_1_0004_692d8999']` |
| hybrid |  | 1.024 | 1 | 0.009 | 0.250 | 0.333 | 0 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2024_Item_1_0004_692d8999']` | `{'xeon_intel_anchor': ['INTC_2024_Item_1_0004_692d8999'], 'microsoft_ai_pc_collaboration': [], 'ai_pc_platform_context': []}` | `['INTC_2025_Item_7_0003_878f7d25', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0004_c01224f1']` |

### T025: `In which U.S. states does the developer of the Intel 18A process operate or expand wafer fabrication facilities?`

- type: `geo_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel 18a', 'intel', 'arizona', 'ohio', 'oregon']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_1_0015_adfe2316', 'INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_1_0014_32e0816b', 'INTC_2026_Item_1_0005_f5ba2220']`
- gold_evidence_groups: `{'intel_18a_anchor': ['INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_1_0015_adfe2316'], 'us_wafer_fab_locations': ['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_1_0014_32e0816b'], 'ohio_expansion_context': ['INTC_2024_Item_1_0014_32e0816b', 'INTC_2026_Item_1_0005_f5ba2220']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.107 | 1 | 0.011 | 0.400 | 0.667 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2026_Item_1_0005_f5ba2220']` | `{'intel_18a_anchor': [], 'us_wafer_fab_locations': ['INTC_2025_Item_1_0004_c5a12b11'], 'ohio_expansion_context': ['INTC_2026_Item_1_0005_f5ba2220']}` | `['INTC_2025_Item_1_0010_5c90fb55', 'INTC_2025_Item_1_0004_c5a12b11', 'MU_2024_Item_1A_0025_1809ff3b', 'INTC_2026_Item_1_0005_f5ba2220', 'TXN_2024_Item_1_0004_06070784']` |
| graph |  | 0.950 | 0 | 0.011 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `{'intel_18a_anchor': [], 'us_wafer_fab_locations': [], 'ohio_expansion_context': []}` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2026_Item_1_0008_c74f560f', 'LRCX_2023_Item_1_0005_de991ae1']` |
| hybrid |  | 1.168 | 1 | 0.011 | 0.200 | 0.333 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1_0004_c5a12b11']` | `{'intel_18a_anchor': [], 'us_wafer_fab_locations': ['INTC_2025_Item_1_0004_c5a12b11'], 'ohio_expansion_context': []}` | `['INTC_2025_Item_1_0004_c5a12b11', 'AMD_2025_Item_1_0009_c842eea0', 'INTC_2025_Item_1_0010_5c90fb55', 'AMD_2026_Item_1_0010_460dfa17', 'MU_2024_Item_1A_0025_1809ff3b']` |

### T026: `What U.S. legislative act funds domestic semiconductor manufacturing expansion at the Intel 18A developer?`

- type: `regulator_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel 18a', 'intel', 'chips act']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_1_0015_adfe2316', 'INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2024_Item_1A_0007_6560bf56']`
- gold_evidence_groups: `{'intel_18a_anchor': ['INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_1_0015_adfe2316'], 'chips_act_manufacturing_funding': ['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2024_Item_1A_0007_6560bf56']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.088 | 1 | 0.011 | 0.400 | 0.500 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45']` | `{'intel_18a_anchor': [], 'chips_act_manufacturing_funding': ['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d']}` | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45', 'MU_2025_Item_7_0006_849b23ef', 'INTC_2026_Item_1_0005_f5ba2220', 'MU_2025_Item_1A_0029_541d266d']` |
| graph |  | 0.966 | 1 | 0.011 | 0.200 | 0.500 | 0 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2026_Item_1_0004_c01224f1']` | `{'intel_18a_anchor': ['INTC_2026_Item_1_0004_c01224f1'], 'chips_act_manufacturing_funding': []}` | `['INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_7_0011_0681e088', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_7_0003_657be427', 'INTC_2025_Item_1_0004_c5a12b11']` |
| hybrid |  | 1.022 | 1 | 0.011 | 0.200 | 0.500 | 0 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1A_0008_80e72e45']` | `{'intel_18a_anchor': [], 'chips_act_manufacturing_funding': ['INTC_2025_Item_1A_0008_80e72e45']}` | `['INTC_2026_Item_1_0005_f5ba2220', 'INTC_2025_Item_1_0004_c5a12b11', 'INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_7_0011_0681e088']` |

### T027: `What advanced driver assistance product lines come from the autonomous driving subsidiary of the Xeon Scalable developer?`

- type: `three_hop_subsidiary_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['xeon scalable', 'intel', 'mobileye', 'mobileye supervision', 'mobileye chauffeur', 'mobileye drive']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0010_3742bdd2', 'INTC_2024_Item_7_0014_e766ac95']`
- gold_evidence_groups: `{'xeon_intel_anchor': ['INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_1_0004_692d8999'], 'mobileye_subsidiary_anchor': ['INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0010_3742bdd2'], 'mobileye_adas_product_lines': ['INTC_2024_Item_7_0010_3742bdd2', 'INTC_2024_Item_7_0014_e766ac95']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.091 | 0 | 0.009 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'xeon_intel_anchor': [], 'mobileye_subsidiary_anchor': [], 'mobileye_adas_product_lines': []}` | `['NVDA_2024_Item_1_0004_12c02096', 'INTC_2024_Item_7_0005_d449d027', 'NVDA_2024_Item_1_0006_f3efd950', 'NVDA_2025_Item_1_0005_85d95b7e', 'NVDA_2026_Item_1_0004_5a83036d']` |
| graph |  | 0.926 | 0 | 0.009 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `{'xeon_intel_anchor': [], 'mobileye_subsidiary_anchor': [], 'mobileye_adas_product_lines': []}` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'AVGO_2023_Item_1_0010_68f5ffd4', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2025_Item_1_0009_c842eea0']` |
| hybrid |  | 1.048 | 0 | 0.009 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'xeon_intel_anchor': [], 'mobileye_subsidiary_anchor': [], 'mobileye_adas_product_lines': []}` | `['INTC_2024_Item_7_0005_d449d027', 'NVDA_2024_Item_1_0004_12c02096', 'NVDA_2026_Item_1_0007_bf6a51b6', 'AVGO_2023_Item_1_0010_68f5ffd4', 'NVDA_2024_Item_1_0006_f3efd950']` |

### T028: `What consumer storage and DRAM brand is sold by the U.S. supplier of HBM3E memory?`

- type: `product_via_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['hbm3e', 'micron', 'crucial']`
- missing_gold_entities: `[]`
- gold_chunks: `['MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2025_Item_1_0000_6418b9d4', 'MU_2024_Item_1_0000_82417507']`
- gold_evidence_groups: `{'hbm3e_micron_anchor': ['MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_1_0010_ef8bd774'], 'crucial_brand': ['MU_2025_Item_1_0000_6418b9d4', 'MU_2024_Item_1_0000_82417507']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.086 | 1 | 0.009 | 0.250 | 0.500 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['MU_2025_Item_1_0010_ef8bd774']` | `{'hbm3e_micron_anchor': ['MU_2025_Item_1_0010_ef8bd774'], 'crucial_brand': []}` | `['MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0002_74d97a0e', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2023_Item_1_0004_fcaccc78']` |
| graph |  | 0.958 | 1 | 0.009 | 0.500 | 0.500 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_1_0010_ef8bd774']` | `{'hbm3e_micron_anchor': ['MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_1_0010_ef8bd774'], 'crucial_brand': []}` | `['MU_2024_Item_1_0002_473014b9', 'MU_2024_Item_1_0009_25e18f42', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0001_70be5bda', 'MU_2025_Item_7_0001_7b8c9ee6']` |
| hybrid |  | 1.033 | 1 | 0.009 | 0.500 | 0.500 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['MU_2025_Item_1_0010_ef8bd774', 'MU_2024_Item_1_0002_473014b9']` | `{'hbm3e_micron_anchor': ['MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_1_0010_ef8bd774'], 'crucial_brand': []}` | `['MU_2025_Item_1_0010_ef8bd774', 'RMBS_2025_Item_1_0001_479b0c1e', 'MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0009_25e18f42']` |

### T029: `Why has HBM become critical for modern AI training and inference workloads?`

- type: `topical_memory`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_entities: `['hbm', 'hbm3e', 'ai', 'data center']`
- missing_gold_entities: `[]`
- gold_chunks: `['MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2024_Item_1_0003_acd8d0ff', 'MU_2025_Item_7_0000_aa4240e3', 'MU_2024_Item_1_0002_473014b9']`
- gold_evidence_groups: `{'hbm_architecture_benefit': ['MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0001_90ffbd18'], 'ai_workload_demand': ['MU_2024_Item_1_0003_acd8d0ff', 'MU_2025_Item_7_0000_aa4240e3', 'MU_2024_Item_1_0002_473014b9']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.082 | 0 | 0.011 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hbm_architecture_benefit': [], 'ai_workload_demand': []}` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'QCOM_2025_Item_1_0002_29556203', 'QCOM_2024_Item_1_0002_f2bb0f8a', 'NVDA_2026_Item_1_0005_9725a5a2', 'KLAC_2025_Item_1A_0021_f329ea02']` |
| graph |  | 0.922 | 1 | 0.011 | 1.000 | 1.000 | 1 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['MU_2024_Item_1_0001_90ffbd18', 'MU_2024_Item_1_0003_acd8d0ff', 'MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_7_0000_aa4240e3', 'MU_2025_Item_1_0001_b64486b7']` | `{'hbm_architecture_benefit': ['MU_2024_Item_1_0001_90ffbd18', 'MU_2025_Item_1_0001_b64486b7'], 'ai_workload_demand': ['MU_2024_Item_1_0002_473014b9', 'MU_2024_Item_1_0003_acd8d0ff', 'MU_2025_Item_7_0000_aa4240e3']}` | `['MU_2024_Item_1_0001_90ffbd18', 'MU_2024_Item_1_0003_acd8d0ff', 'MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_7_0000_aa4240e3', 'MU_2025_Item_1_0001_b64486b7']` |
| hybrid |  | 1.195 | 1 | 0.011 | 0.600 | 1.000 | 1 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['MU_2024_Item_1_0001_90ffbd18', 'MU_2024_Item_1_0003_acd8d0ff', 'MU_2024_Item_1_0002_473014b9']` | `{'hbm_architecture_benefit': ['MU_2024_Item_1_0001_90ffbd18'], 'ai_workload_demand': ['MU_2024_Item_1_0002_473014b9', 'MU_2024_Item_1_0003_acd8d0ff']}` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2024_Item_1_0003_acd8d0ff', 'QCOM_2025_Item_1_0002_29556203', 'MU_2024_Item_1_0002_473014b9']` |

### T030: `Which cloud hyperscalers partner with the EPYC processor maker for server CPU deployments in their data centers?`

- type: `customer_via_product`
- subset: `reextract_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `[]`
- gold_entities: `['epyc', 'amd', 'hyperscale cloud']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`
- gold_evidence_groups: `{}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.099 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `['AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_1_0010_842113d9', 'INTC_2024_Item_7_0008_57402d3f']` |
| graph |  | 0.940 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 1 | n/a | unscored_discovery | `[]` | `{}` | `['NVDA_2024_Item_1_0007_bae70036', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0001_1abc85fc', 'AMD_2025_Item_1_0002_6fadf6e4']` |
| hybrid |  | 0.956 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2026_Item_1_0009_ac9cc232', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2024_Item_1_0011_49024c2d']` |
