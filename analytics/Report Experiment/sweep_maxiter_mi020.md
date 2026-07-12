# Phase T Retrieval Baseline

Generated: 2026-07-10T03:35:58

## Run Configuration

- script: `scripts/evaluate_retrieval_quality.py`
- command: `scripts/evaluate_retrieval_quality.py --tools graph --top-k 5 --oracle-k 20 --no-llm-expansion --graph-damping 0.50 --version-name phase_t_maxiter_sweep_mi020_d050`
- query_file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
- query_count: `30`
- tools: `graph`
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
- graph_damping: `0.5`
- metadata_rerank_params: `{'risk_section_boost': 1.35, 'business_section_boost': 1.18, 'financial_section_boost': 1.28, 'ticker_boost': 1.2, 'cluster_boost_per_extra': 0.04, 'cluster_boost_cap': 1.05, 'latest_year_boost': 1.08, 'latest_year_min': 2025, 'lexical_match_weight': 0.1, 'lexical_boost_cap': 0.55, 'broad_penalty_enabled': True, 'broad_penalty_floor': 0.92, 'broad_penalty_step': 0.97, 'broad_penalty_zero_match': 0.98, 'broad_penalty_short_token_cutoff': 80, 'broad_penalty_mid_token_cutoff': 140, 'broad_penalty_long_token_cutoff': 220}`
- version_name: `phase_t_maxiter_sweep_mi020_d050`
- details_jsonl: `/home/kantinan/programming/project/analytics/Report Experiment/details_maxiter_mi020.jsonl`
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
| graph | 26 | 0 | 0.654 | 0.011 | 57.223 | 0.642 | 0.260 | 0.391 | 0.154 | 0.474 | 0.885 |

## By Type

| Type | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable |
|---|---:|---:|---:|---:|
| competitor_product | 1.000 | 0.194 | 0.417 | 0.000 |
| geo_via_product | 0.000 | 0.000 | 0.000 | 0.000 |
| geo_via_supplier | 1.000 | 0.143 | 0.500 | 0.000 |
| graph_multihop | 0.500 | 0.200 | 0.250 | 0.000 |
| partner_via_product | 0.333 | 0.133 | 0.111 | 0.000 |
| product_via_company | 1.000 | 0.500 | 0.500 | 0.000 |
| regulation_via_product | 1.000 | 0.125 | 0.667 | 0.000 |
| regulator_via_product | 1.000 | 0.400 | 0.500 | 0.000 |
| risk_via_product | 1.000 | 0.250 | 1.000 | 1.000 |
| segment_via_product | 1.000 | 0.375 | 0.333 | 0.000 |
| subsidiary_via_product | 1.000 | 0.250 | 0.500 | 0.000 |
| supplier_via_company | 0.500 | 0.500 | 0.500 | 0.500 |
| supplier_via_product | 0.750 | 0.283 | 0.375 | 0.000 |
| three_hop_subsidiary_product | 0.000 | 0.000 | 0.000 | 0.000 |
| topical_memory | 1.000 | 0.600 | 1.000 | 1.000 |
| vector_friendly | 0.333 | 0.267 | 0.333 | 0.333 |

## By Subset

| Subset | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable | graph Oracle |
|---|---:|---:|---:|---:|---:|
| reextract_subset | 0.654 | 0.260 | 0.391 | 0.154 | 0.885 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 0.962 | 0.962 | 0.923 | candidate_pool_loss=1, chunk_mapping_loss=2, hit_top_k=17, rerank_loss=6 |
| reextract_subset | 0.962 | 0.962 | 0.923 | candidate_pool_loss=1, chunk_mapping_loss=2, hit_top_k=17, rerank_loss=6 |

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
| graph |  | 25.858 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `{'amd_tsmc_supply_risk': []}` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2026_Item_1A_0000_268148d2']` |

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
| graph |  | 1.988 | 0 | 0.013 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `{'hopper_evidence': [], 'supplier_evidence': []}` | `['INTC_2026_Item_7_0017_86b90f80', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_7_0000_3c580005', 'INTC_2026_Item_1A_0000_268148d2', 'NVDA_2026_Item_7_0006_ec90a691']` |

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
| graph |  | 1.032 | 1 | 0.011 | 0.400 | 0.500 | 0 | 0.250 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']` | `{'direct_answer': [], 'supplier_context': ['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']}` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']` |

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
| graph |  | 0.961 | 1 | 0.013 | 0.167 | 0.500 | 0 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2024_Item_1_0011_49024c2d']` | `{'direct_answer': [], 'competitor_context': ['AMD_2024_Item_1_0011_49024c2d']}` | `['INTC_2025_Item_7_0002_f7953bfd', 'AMD_2024_Item_1A_0005_a057bdb2', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1A_0000_ac2e47a8', 'AMD_2025_Item_1A_0001_0fd81b24']` |

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
| graph |  | 0.991 | 1 | 0.015 | 0.143 | 0.500 | 0 | 0.200 | 1 | 0 | 0 | 1 | hit_top_k | `['AMD_2025_Item_1_0009_c842eea0']` | `{'foundry_identity': ['AMD_2025_Item_1_0009_c842eea0'], 'taiwan_political_risk': []}` | `['RMBS_2024_Item_1A_0009_16baaed9', 'NVDA_2026_Item_1A_0024_b70c7a18', 'QCOM_2024_Item_1A_0021_d747cb53', 'QCOM_2024_Item_1A_0003_50517ec6', 'AMD_2025_Item_1_0009_c842eea0']` |

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
| graph |  | 0.981 | 1 | 0.006 | 1.000 | 1.000 | 1 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']` | `{'wafer_foundry_supplier': ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']}` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0007_bae70036', 'QCOM_2024_Item_1A_0009_b69d631a', 'NVDA_2025_Item_1_0008_a4407f7e', 'AVGO_2023_Item_1A_0010_b51535cb']` |

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
| graph |  | 1.143 | 1 | 0.019 | 0.222 | 0.333 | 0 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` | `{'amd_radeon_product_line': [], 'amd_nvidia_graphics_competition': ['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17'], 'nvidia_rtx_product_reference': []}` | `['INTC_2026_Item_1A_0000_268148d2', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2026_Item_1_0007_bf6a51b6']` |

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
| graph |  | 1.037 | 1 | 0.021 | 0.400 | 0.333 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2026_Item_7_0001_485abbd3', 'NVDA_2026_Item_1_0009_8c403127']` | `{'h200_nvidia_anchor': ['NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2026_Item_1_0009_8c403127', 'NVDA_2026_Item_7_0001_485abbd3'], 'nvidia_memory_suppliers': [], 'micron_hbm_context': []}` | `['NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2026_Item_7_0001_485abbd3', 'NVDA_2026_Item_1_0009_8c403127', 'AMD_2024_Item_1_0011_49024c2d']` |

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
| graph |  | 0.981 | 1 | 0.017 | 0.250 | 1.000 | 1 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2025_Item_7_0002_b40db6b2']` | `{'export_control_restrictions': ['NVDA_2025_Item_1A_0023_67392e5b'], 'data_center_business_impact': ['NVDA_2025_Item_7_0002_b40db6b2']}` | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2025_Item_1A_0003_9003fee7', 'NVDA_2025_Item_1A_0024_d1a5b506']` |

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
| graph |  | 1.227 | 1 | 0.011 | 0.800 | 1.000 | 1 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0007_4615acf5']` | `{'entegis_materials_and_purity_segments': ['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0007_4615acf5']}` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0013_d310ee7e', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0007_4615acf5']` |

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
| graph |  | 1.069 | 0 | 0.002 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `{'useful_life_gross_margin_impact': []}` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2026_Item_7_0014_7f63f75a', 'ENTG_2026_Item_7_0013_16ad8335', 'ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2024_Item_7_0009_7ec7e035']` |

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
| graph |  | 1.006 | 0 | 0.009 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `{'entegris_business_segments': []}` | `['ENTG_2025_Item_7_0016_c8496ed0', 'ENTG_2024_Item_1_0009_c1b0a473', 'ENTG_2024_Item_7_0018_b0a46a7f', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2026_Item_1_0013_2fa9f11c']` |

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
| graph |  | 0.965 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `{}` | `['AMD_2025_Item_7_0001_223169cf', 'AMD_2026_Item_7_0006_2b606b28', 'INTC_2026_Item_1A_0000_268148d2', 'AMD_2024_Item_7_0002_d4114c99', 'INTC_2025_Item_1A_0000_ac3a3dbc']` |

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
| graph |  | 0.925 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `{}` | `['AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_1_0013_9fc1134b', 'AMD_2026_Item_1_0014_30a9cc7d', 'AMD_2024_Item_1_0011_49024c2d']` |

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
| graph |  | 1.003 | 1 | 0.011 | 0.400 | 0.500 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2024_Item_1A_0008_027b0f68', 'AMD_2025_Item_1A_0009_57657610']` | `{'kla_yield_improvement_tools': [], 'amd_yield_gross_margin_risk': ['AMD_2024_Item_1A_0008_027b0f68', 'AMD_2025_Item_1A_0009_57657610']}` | `['AMD_2024_Item_1A_0008_027b0f68', 'AMD_2025_Item_1A_0009_57657610', 'INTC_2025_Item_1A_0000_ac3a3dbc', 'INTC_2026_Item_1A_0000_268148d2', 'AMD_2024_Item_7_0004_67034475']` |

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
| graph |  | 0.977 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | unscored_discovery | `[]` | `{}` | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01']` |

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
| graph |  | 0.932 | 0 | 0.013 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `{'amd_tsmc_processor_foundry': []}` | `['NVDA_2024_Item_1_0008_20833acc', 'NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2026_Item_1_0008_edf8fe4b', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e']` |

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
| graph |  | 1.132 | 0 | 0.009 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `{'amd_console_partners': []}` | `['AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_1A_0004_3da97b4d', 'AMD_2026_Item_1A_0003_bc568432', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2026_Item_1_0010_460dfa17']` |

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
| graph |  | 0.997 | 1 | 0.017 | 0.375 | 0.333 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_7_0005_36426dd3', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0005_8ab9ed73']` | `{'epyc_amd_anchor': [], 'amd_reportable_segments': [], 'segment_revenue_disclosure': ['AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2026_Item_7_0005_8ab9ed73']}` | `['AMD_2025_Item_7_0005_36426dd3', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_7_0004_58e0bdd2', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_7_0005_8ab9ed73']` |

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
| graph |  | 0.946 | 1 | 0.017 | 0.125 | 0.667 | 0 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1A_0019_46eda166']` | `{'blackwell_nvidia_anchor': [], 'export_control_restrictions': ['NVDA_2025_Item_1A_0019_46eda166'], 'ai_chip_sales_impact': ['NVDA_2025_Item_1A_0019_46eda166']}` | `['NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2025_Item_1A_0019_46eda166', 'INTC_2026_Item_1A_0000_268148d2', 'INTC_2025_Item_1A_0000_ac3a3dbc', 'INTC_2024_Item_7_0005_d449d027']` |

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
| graph |  | 0.986 | 1 | 0.013 | 0.333 | 0.667 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1A_0006_820d3c64']` | `{'intel_18a_anchor': [], 'third_party_foundry_risk': ['INTC_2026_Item_1A_0006_820d3c64'], 'mature_node_foundry_competitors': ['INTC_2026_Item_1_0008_c74f560f']}` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2025_Item_7_0010_325410df', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2026_Item_1A_0005_46d4d921', 'NVDA_2024_Item_1_0008_20833acc']` |

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
| graph |  | 0.954 | 1 | 0.011 | 0.400 | 0.333 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0011_4307b8ad']` | `{'xeon_intel_anchor': ['INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0011_4307b8ad'], 'smart_capital_financing': [], 'infrastructure_investment_partners': []}` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_7_0004_63451c7a']` |

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
| graph |  | 0.943 | 1 | 0.009 | 0.250 | 0.500 | 0 | 0.200 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2024_Item_7_0000_e2ea081b']` | `{'core_ultra_intel_anchor': ['INTC_2024_Item_7_0000_e2ea081b'], 'mobileye_autonomous_driving': []}` | `['INTC_2025_Item_7_0002_f7953bfd', 'INTC_2026_Item_1_0007_f3f3671c', 'INTC_2024_Item_7_0002_7c82ed88', 'INTC_2026_Item_1_0013_cb483288', 'INTC_2024_Item_7_0000_e2ea081b']` |

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
| graph |  | 1.008 | 0 | 0.009 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `{'xeon_intel_anchor': [], 'microsoft_ai_pc_collaboration': [], 'ai_pc_platform_context': []}` | `['INTC_2024_Item_7_0000_e2ea081b', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_1A_0004_64e4feb4', 'INTC_2025_Item_1A_0005_09499ac8']` |

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
| graph |  | 0.981 | 0 | 0.011 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | 1 | candidate_pool_loss | `[]` | `{'intel_18a_anchor': [], 'us_wafer_fab_locations': [], 'ohio_expansion_context': []}` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_7_0017_86b90f80']` |

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
| graph |  | 1.222 | 1 | 0.011 | 0.400 | 0.500 | 0 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_1_0015_adfe2316']` | `{'intel_18a_anchor': ['INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_1_0015_adfe2316'], 'chips_act_manufacturing_funding': []}` | `['INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_7_0011_0681e088', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2026_Item_1_0015_adfe2316', 'INTC_2026_Item_7_0003_657be427']` |

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
| graph |  | 0.958 | 0 | 0.009 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `{'xeon_intel_anchor': [], 'mobileye_subsidiary_anchor': [], 'mobileye_adas_product_lines': []}` | `['INTC_2026_Item_1A_0000_268148d2', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2026_Item_1_0007_bf6a51b6']` |

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
| graph |  | 0.967 | 1 | 0.009 | 0.500 | 0.500 | 0 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_1_0010_ef8bd774']` | `{'hbm3e_micron_anchor': ['MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_1_0010_ef8bd774'], 'crucial_brand': []}` | `['MU_2024_Item_1_0002_473014b9', 'MU_2025_Item_7_0001_7b8c9ee6', 'MU_2024_Item_1_0009_25e18f42', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0001_70be5bda']` |

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
| graph |  | 0.961 | 1 | 0.011 | 0.600 | 1.000 | 1 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['MU_2025_Item_7_0000_aa4240e3', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2024_Item_1_0003_acd8d0ff']` | `{'hbm_architecture_benefit': ['MU_2024_Item_1_0001_90ffbd18'], 'ai_workload_demand': ['MU_2024_Item_1_0003_acd8d0ff', 'MU_2025_Item_7_0000_aa4240e3']}` | `['MU_2025_Item_7_0000_aa4240e3', 'MU_2024_Item_1A_0004_6b8d5aad', 'MU_2023_Item_1A_0010_9e151f4c', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2024_Item_1_0003_acd8d0ff']` |

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
| graph |  | 0.987 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 1 | n/a | unscored_discovery | `[]` | `{}` | `['AMD_2025_Item_7_0005_36426dd3', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_7_0004_58e0bdd2', 'AMD_2024_Item_7_0005_86aec648', 'AMD_2026_Item_7_0005_8ab9ed73']` |
