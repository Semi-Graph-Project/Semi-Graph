# Phase T Retrieval Baseline

Generated: 2026-07-01T15:14:31
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `vector, graph, hybrid`
top_k: `5`
oracle_k: `20`
dry_run: `False`
corpus_chunks: `2347`
graph_use_expansion: `False`
graph_seed_mode: `triple`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Random Hit@k | Hit Lift | Hit-Random | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 21 | 0 | 0.333 | 0.004 | 78.329 | 0.329 | 0.224 | 0.286 | 0.571 |
| graph | 21 | 0 | 0.190 | 0.004 | 44.759 | 0.186 | 0.121 | 0.095 | 0.333 |
| hybrid | 21 | 0 | 0.381 | 0.004 | 89.518 | 0.377 | 0.243 | 0.210 | 0.571 |

## By Type

| Type | vector Hit | vector Recall | graph Hit | graph Recall | hybrid Hit | hybrid Recall |
|---|---:|---:|---:|---:|---:|---:|
| competitor_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| customer_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| geo_via_product | 1.000 | 0.500 | 0.000 | 0.000 | 1.000 | 0.500 |
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| partner_via_product | 0.333 | 0.167 | 0.000 | 0.000 | 0.333 | 0.167 |
| product_via_company | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| regulation_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| regulator_via_product | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.500 |
| segment_via_product | 1.000 | 0.500 | 0.000 | 0.000 | 1.000 | 0.500 |
| subsidiary_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| supplier_via_company | 0.000 | 0.000 | 1.000 | 0.500 | 1.000 | 0.500 |
| supplier_via_product | 0.333 | 0.067 | 0.667 | 0.350 | 0.333 | 0.200 |
| three_hop_subsidiary_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| topical_memory | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| vector_friendly | 0.667 | 0.667 | 0.333 | 0.333 | 0.667 | 0.667 |

## By Subset

| Subset | vector Hit | vector Recall | vector Oracle | graph Hit | graph Recall | graph Oracle | hybrid Hit | hybrid Recall | hybrid Oracle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| legacy_subset | 0.333 | 0.292 | 0.583 | 0.083 | 0.083 | 0.333 | 0.333 | 0.250 | 0.417 |
| mixed_subset | 0.500 | 0.100 | 0.500 | 1.000 | 0.525 | 1.000 | 0.500 | 0.300 | 1.000 |
| reextract_subset | 0.286 | 0.143 | 0.571 | 0.143 | 0.071 | 0.143 | 0.429 | 0.214 | 0.714 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 0.952 | 1.000 | 0.333 | chunk_mapping_loss=13, hit_top_k=4, rerank_loss=3, seed_loss=1 |
| legacy_subset | 1.000 | 1.000 | 0.333 | chunk_mapping_loss=8, hit_top_k=1, rerank_loss=3 |
| mixed_subset | 1.000 | 1.000 | 1.000 | hit_top_k=2 |
| reextract_subset | 0.857 | 1.000 | 0.143 | chunk_mapping_loss=5, hit_top_k=1, seed_loss=1 |

## Paired Recall Test vs Vector

| Subset | Tool | n | Mean Delta Recall | One-sided p |
|---|---|---:|---:|---:|
| full_mixed | graph | 21 | -0.102 | 1.000 |
| full_mixed | hybrid | 21 | 0.019 | 0.495 |
| legacy_subset | graph | 12 | -0.208 | 1.000 |
| legacy_subset | hybrid | 12 | -0.042 | 1.000 |
| mixed_subset | graph | 2 | 0.425 | 0.251 |
| mixed_subset | hybrid | 2 | 0.200 | 0.501 |
| reextract_subset | graph | 7 | -0.071 | 1.000 |
| reextract_subset | hybrid | 7 | 0.071 | 0.496 |

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
| vector |  | 5.838 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1A_0002_0a71f57a', 'INTC_2026_Item_1A_0006_820d3c64', 'MU_2024_Item_1A_0001_703555bd', 'MU_2025_Item_1A_0001_8d660135', 'INTC_2024_Item_1A_0000_1a5c79ae']` |
| graph |  | 24.058 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2025_Item_1A_0009_57657610', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1A_0005_a057bdb2', 'AMD_2025_Item_1A_0000_ac2e47a8']` |
| hybrid |  | 2.604 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2025_Item_1A_0011_10eec6d1', 'AMD_2024_Item_1A_0002_0a71f57a', 'AMD_2025_Item_1A_0009_57657610', 'AMD_2025_Item_1_0009_c842eea0', 'INTC_2026_Item_1A_0006_820d3c64']` |

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
| vector |  | 0.125 | 1 | 0.011 | 0.200 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0013_cb483288', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_1_0014_32e0816b', 'AMD_2024_Item_1_0012_9561038a']` |
| graph |  | 2.009 | 1 | 0.011 | 0.800 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2025_Item_1_0008_a4407f7e']` | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e']` |
| hybrid |  | 1.704 | 1 | 0.011 | 0.600 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'INTC_2026_Item_1_0013_cb483288', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0006_d0f653da']` |

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
| vector |  | 0.126 | 0 | 0.008 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2026_Item_1_0005_9725a5a2', 'INTC_2026_Item_1_0004_c01224f1']` |
| graph |  | 4.288 | 1 | 0.008 | 0.250 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1_0008_a4407f7e']` | `['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2024_Item_1A_0005_a057bdb2', 'INTC_2024_Item_7_0005_d449d027']` |
| hybrid |  | 1.935 | 0 | 0.008 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2025_Item_7_0003_878f7d25']` |

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
| vector |  | 0.122 | 0 | 0.002 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2026_Item_1_0005_9725a5a2']` |
| graph |  | 1.613 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'NVDA_2024_Item_1_0007_bae70036']` |
| hybrid |  | 1.804 | 0 | 0.002 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2025_Item_1_0003_707a268b', 'AMD_2025_Item_1_0009_c842eea0', 'INTC_2024_Item_1_0005_bcb431a8', 'AMD_2026_Item_1_0010_460dfa17']` |

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
| vector |  | 0.116 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['QCOM_2023_Item_1A_0031_545bf96a', 'INTC_2026_Item_1A_0002_066bd50c', 'ENTG_2026_Item_1_0004_6f32215b', 'MU_2023_Item_1A_0003_92be33e3', 'ENTG_2025_Item_1_0004_66634bce']` |
| graph |  | 1.764 | n/a | n/a | n/a | n/a | n/a | 0 | 0 | n/a | unscored_discovery | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'INTC_2024_Item_1A_0009_dd11a01d', 'LRCX_2023_Item_1A_0006_e42302c0', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2026_Item_1A_0020_331dc537']` |
| hybrid |  | 1.631 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'QCOM_2023_Item_1A_0031_545bf96a', 'INTC_2024_Item_1A_0009_dd11a01d', 'INTC_2026_Item_1A_0002_066bd50c', 'ENTG_2026_Item_1_0004_6f32215b']` |

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
| vector |  | 0.134 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1A_0025_1809ff3b', 'AMKR_2026_Item_1_0003_8dee603e', 'ENTG_2024_Item_1_0007_38140456', 'NVDA_2024_Item_1_0002_2ddf2e3b']` |
| graph |  | 2.438 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` |
| hybrid |  | 1.711 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0007_bae70036', 'MU_2024_Item_1A_0025_1809ff3b', 'AMKR_2026_Item_1_0003_8dee603e']` |

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
| vector |  | 0.187 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0007_0ffd6ad4', 'AMD_2025_Item_1A_0002_2bc1ccc8']` |
| graph |  | 1.644 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'AVGO_2023_Item_1_0010_68f5ffd4']` |
| hybrid |  | 1.756 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965']` |

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
| vector |  | 0.123 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2025_Item_1_0002_b74647bb', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2025_Item_1_0001_b64486b7']` |
| graph |  | 1.701 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2026_Item_1_0009_8c403127', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2026_Item_7_0001_485abbd3', 'NVDA_2025_Item_7_0002_b40db6b2', 'AMD_2024_Item_1_0011_49024c2d']` |
| hybrid |  | 1.659 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2026_Item_1_0009_8c403127', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2025_Item_1_0002_b74647bb']` |

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
| vector |  | 0.110 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2025_Item_1A_0019_46eda166']` |
| graph |  | 1.596 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2025_Item_1A_0003_9003fee7', 'AMAT_2025_Item_1A_0017_af7d9be8', 'ENTG_2026_Item_1A_0005_d2f79cf3']` |
| hybrid |  | 1.634 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0023_804c637e', 'NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2026_Item_1A_0022_3d4f4d9b']` |

### T010: `Which materials and purity solutions does Entegris provide to semiconductor manufacturers?`

- type: `vector_friendly`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['vector']`
- gold_entities: `['entegris', 'materials solutions', 'advanced purity solutions']`
- missing_gold_entities: `[]`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.117 | 1 | 0.002 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0009_ca7ef011', 'ENTG_2025_Item_1_0008_700da46e']` |
| graph |  | 1.639 | 1 | 0.002 | 1.000 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0008_700da46e', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0007_4615acf5', 'ENTG_2026_Item_1_0011_d7877367']` |
| hybrid |  | 1.704 | 1 | 0.002 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0007_4615acf5']` |

### T011: `What gross margin impact did Entegris expect from its useful-life accounting estimate change?`

- type: `vector_friendly`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['vector']`
- gold_entities: `['entegris', 'gross margin', 'depreciation']`
- missing_gold_entities: `[]`
- gold_chunks: `['ENTG_2026_Item_7_0003_d6e71ea2']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.109 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'KLAC_2025_Item_7_0009_be3ecb77', 'KLAC_2024_Item_7_0008_8308f577', 'KLAC_2023_Item_7_0011_e4c656e2', 'ENTG_2026_Item_7_0015_6af235b4']` |
| graph |  | 1.843 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2024_Item_7_0018_b0a46a7f', 'ENTG_2024_Item_7_0019_28ef5c6a', 'AMAT_2023_Item_7_0001_55c419c2']` |
| hybrid |  | 1.756 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2024_Item_7_0017_71caf017', 'KLAC_2025_Item_7_0009_be3ecb77', 'ENTG_2024_Item_7_0018_b0a46a7f', 'KLAC_2024_Item_7_0008_8308f577']` |

### T012: `What are Entegris's main business segments?`

- type: `vector_friendly`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['vector']`
- gold_entities: `['entegris', 'materials solutions', 'advanced purity solutions']`
- missing_gold_entities: `[]`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.100 | 1 | 0.002 | 1.000 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0014_8712752e', 'ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2024_Item_1_0019_b6aee1a3']` |
| graph |  | 1.675 | 0 | 0.002 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2026_Item_1_0011_d7877367', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2026_Item_1_0013_2fa9f11c', 'ENTG_2024_Item_1_0018_1e35f935']` |
| hybrid |  | 1.709 | 1 | 0.002 | 1.000 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2024_Item_1_0000_647e6e2c']` |

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
| vector |  | 0.100 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003', 'INTC_2024_Item_1_0003_02f7f00d', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2026_Item_7_0006_2b606b28']` |
| graph |  | 1.513 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2025_Item_7_0001_223169cf', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2024_Item_7_0004_67034475', 'AMD_2025_Item_7_0003_a2d9991c']` |
| hybrid |  | 1.809 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_7_0006_2b606b28', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0001_223169cf', 'INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003']` |

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
| vector |  | 0.084 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_7_0000_6b145a7b']` |
| graph |  | 1.427 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2026_Item_1A_0002_72e02a77', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` |
| hybrid |  | 1.549 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_1A_0002_72e02a77']` |

### T015: `What is the relationship between KLA yield improvement tools and downstream AMD gross margin risk?`

- type: `graph_multihop`
- subset: `reextract_subset`
- corpus_status: `unscored_discovery`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['kla', 'tsmc', 'amd', 'yield', 'gross margin']`
- missing_gold_entities: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.115 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['MU_2023_Item_1A_0001_1b8ef3ed', 'AVGO_2025_Item_1A_0008_7b345bfe', 'INTC_2024_Item_7_0015_575e5365', 'AVGO_2023_Item_1A_0018_717a6eeb', 'KLAC_2023_Item_7_0011_e4c656e2']` |
| graph |  | 1.562 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2024_Item_1A_0008_027b0f68', 'AMD_2025_Item_1A_0009_57657610', 'AMD_2024_Item_1A_0015_22ab1f05', 'AMD_2025_Item_1A_0011_10eec6d1', 'AMD_2024_Item_7_0004_67034475']` |
| hybrid |  | 1.607 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1A_0008_027b0f68', 'MU_2023_Item_1A_0001_1b8ef3ed', 'AMD_2025_Item_1A_0009_57657610', 'AVGO_2025_Item_1A_0008_7b345bfe', 'AMD_2024_Item_1A_0015_22ab1f05']` |

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
| vector |  | 0.089 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'INTC_2025_Item_1_0001_01b4d21e', 'INTC_2025_Item_1_0002_ba6af228', 'QCOM_2024_Item_1_0009_e0fec737', 'AVGO_2024_Item_7_0008_174ffaeb']` |
| graph |  | 1.519 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | unscored_discovery | `[]` | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e']` |
| hybrid |  | 1.809 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'NVDA_2024_Item_1_0007_bae70036', 'INTC_2025_Item_1_0001_01b4d21e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2025_Item_1_0002_ba6af228']` |

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
| vector |  | 0.089 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'MU_2024_Item_1A_0025_1809ff3b', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2024_Item_1_0013_596acde4']` |
| graph |  | 1.444 | 1 | 0.004 | 0.500 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_1_0009_c842eea0']` | `['AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d']` |
| hybrid |  | 1.556 | 1 | 0.004 | 0.500 | 0.200 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2025_Item_1_0009_c842eea0']` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232', 'MU_2024_Item_1A_0025_1809ff3b', 'AMD_2025_Item_1_0009_c842eea0']` |

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
| vector |  | 0.100 | 1 | 0.004 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2026_Item_1_0004_b5e66359']` | `['AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2024_Item_1_0005_7be264c6']` |
| graph |  | 1.532 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_7_0000_16c93d97', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2026_Item_1_0001_17c029a7']` |
| hybrid |  | 1.588 | 1 | 0.004 | 0.500 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2026_Item_1_0004_b5e66359']` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2025_Item_7_0000_16c93d97']` |

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
| vector |  | 0.099 | 1 | 0.004 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'TXN_2025_Item_1_0002_e6c099ac', 'TXN_2024_Item_1_0002_9a773c8b', 'RMBS_2026_Item_7_0004_bb93ee55']` |
| graph |  | 1.527 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0005_8ab9ed73', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2025_Item_7_0004_58e0bdd2', 'INTC_2024_Item_7_0005_d449d027']` |
| hybrid |  | 1.863 | 1 | 0.004 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2026_Item_7_0005_8ab9ed73', 'AMD_2025_Item_7_0005_36426dd3']` |

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
| vector |  | 0.114 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2025_Item_1A_0023_67392e5b']` |
| graph |  | 1.592 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2025_Item_1A_0019_46eda166', 'AMD_2025_Item_1A_0000_ac2e47a8', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'AMD_2024_Item_1A_0005_a057bdb2']` |
| hybrid |  | 1.627 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'AMD_2025_Item_1A_0000_ac2e47a8']` |

### T021: `Which Asian contract chipmakers fabricate older-generation processors for the developer of Intel 18A?`

- type: `supplier_via_product`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel 18a', 'intel', 'tsmc', 'umc', 'smic']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2024_Item_1A_0001_f0f6c35c', 'INTC_2025_Item_1A_0001_65932be2']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.117 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_7_0003_657be427', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_7_0004_e8790cb8', 'MU_2024_Item_1A_0025_1809ff3b']` |
| graph |  | 1.569 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2024_Item_7_0011_0681e088', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2026_Item_1_0014_5d25166d']` |
| hybrid |  | 1.689 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_7_0003_657be427', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2024_Item_7_0011_0681e088', 'AMD_2025_Item_1_0009_c842eea0', 'INTC_2024_Item_7_0000_e2ea081b']` |

### T022: `Which infrastructure investment firms partner with the maker of Xeon Scalable processors on fab financing?`

- type: `partner_via_product`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['xeon scalable', 'intel', 'brookfield', 'apollo', 'smart capital']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2025_Item_1_0011_b8759c99', 'INTC_2024_Item_1A_0007_6560bf56']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.098 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2025_Item_1_0007_1d4a96e6', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0008_57402d3f', 'INTC_2024_Item_1_0008_cca3187e']` |
| graph |  | 1.680 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2026_Item_1_0006_d0f653da', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2024_Item_7_0011_0681e088', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2024_Item_7_0005_d449d027']` |
| hybrid |  | 1.651 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0006_d0f653da']` |

### T023: `Which autonomous driving subsidiary does the developer of Intel Core Ultra operate?`

- type: `subsidiary_via_product`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel core ultra', 'intel', 'mobileye']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2024_Item_1_0010_4835f632', 'INTC_2024_Item_7_0010_3742bdd2']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.092 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0004_12c02096', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2026_Item_1_0010_4bfc9726']` |
| graph |  | 1.553 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2026_Item_1_0007_f3f3671c', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2026_Item_1_0013_cb483288', 'AMD_2025_Item_1_0009_c842eea0']` |
| hybrid |  | 1.596 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_1_0007_f3f3671c', 'NVDA_2024_Item_1_0004_12c02096', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8']` |

### T024: `Which operating system maker collaborates with the Xeon Scalable processor developer on AI PC platforms?`

- type: `partner_via_product`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['xeon scalable', 'intel', 'microsoft', 'ai pc']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2024_Item_7_0002_7c82ed88', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.111 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_7_0000_e2ea081b']` |
| graph |  | 1.530 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2025_Item_7_0003_878f7d25', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2024_Item_7_0000_e2ea081b']` |
| hybrid |  | 1.658 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0004_c01224f1']` |

### T025: `In which U.S. states does the developer of the Intel 18A process operate wafer fabrication facilities?`

- type: `geo_via_product`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel 18a', 'intel', 'arizona', 'ohio', 'oregon', 'new mexico']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_1_0014_32e0816b']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.146 | 1 | 0.004 | 0.500 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1_0004_c5a12b11']` | `['INTC_2025_Item_1_0010_5c90fb55', 'INTC_2025_Item_1_0004_c5a12b11', 'MU_2024_Item_1A_0025_1809ff3b', 'TXN_2024_Item_1_0004_06070784', 'INTC_2026_Item_1_0005_f5ba2220']` |
| graph |  | 1.858 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0008_20833acc']` |
| hybrid |  | 1.666 | 1 | 0.004 | 0.500 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1_0004_c5a12b11']` | `['AMD_2025_Item_1_0009_c842eea0', 'INTC_2025_Item_1_0010_5c90fb55', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2025_Item_1_0004_c5a12b11', 'INTC_2026_Item_1_0008_c74f560f']` |

### T026: `What U.S. legislative act funds domestic semiconductor manufacturing expansion at the Intel 18A developer?`

- type: `regulator_via_product`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['intel 18a', 'intel', 'chips act']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.108 | 1 | 0.004 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45']` | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45', 'MU_2025_Item_7_0006_849b23ef', 'MU_2025_Item_1A_0029_541d266d', 'INTC_2026_Item_1_0005_f5ba2220']` |
| graph |  | 1.492 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2024_Item_7_0011_0681e088', 'INTC_2026_Item_1_0015_adfe2316', 'INTC_2026_Item_7_0003_657be427', 'INTC_2026_Item_1_0005_f5ba2220', 'AMD_2025_Item_1_0009_c842eea0']` |
| hybrid |  | 1.597 | 1 | 0.004 | 0.500 | 0.200 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1A_0008_662b7d4d']` | `['INTC_2026_Item_1_0005_f5ba2220', 'INTC_2026_Item_7_0003_657be427', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2024_Item_7_0011_0681e088', 'INTC_2026_Item_1A_0008_662b7d4d']` |

### T027: `What advanced driver assistance product lines come from the autonomous driving subsidiary of the Xeon Scalable developer?`

- type: `three_hop_subsidiary_product`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['xeon scalable', 'intel', 'mobileye', 'mobileye supervision', 'mobileye chauffeur', 'mobileye drive']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_2024_Item_7_0010_3742bdd2', 'INTC_2024_Item_7_0014_e766ac95']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.098 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'NVDA_2024_Item_1_0004_12c02096', 'NVDA_2024_Item_1_0006_f3efd950', 'NVDA_2025_Item_1_0005_85d95b7e', 'INTC_2025_Item_7_0003_878f7d25']` |
| graph |  | 1.532 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'AVGO_2023_Item_1_0010_68f5ffd4', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2025_Item_1_0009_c842eea0']` |
| hybrid |  | 1.876 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'NVDA_2026_Item_1_0007_bf6a51b6', 'AVGO_2023_Item_1_0010_68f5ffd4', 'NVDA_2024_Item_1_0004_12c02096', 'NVDA_2024_Item_1_0006_f3efd950']` |

### T028: `What consumer storage and DRAM brand is sold by the U.S. supplier of HBM3E memory?`

- type: `product_via_company`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['hbm3e', 'micron', 'crucial']`
- missing_gold_entities: `[]`
- gold_chunks: `['MU_2025_Item_1_0000_6418b9d4', 'MU_2024_Item_1_0000_82417507']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.101 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0002_74d97a0e', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2024_Item_1_0001_90ffbd18']` |
| graph |  | 1.623 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['MU_2023_Item_1_0001_70be5bda', 'MU_2023_Item_7_0000_e9f96198', 'MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_7_0000_aa4240e3', 'MU_2023_Item_7_0002_c0fab91a']` |
| hybrid |  | 1.792 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['MU_2025_Item_1_0001_b64486b7', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0002_74d97a0e', 'MU_2023_Item_1_0001_70be5bda']` |

### T029: `Why has HBM become critical for modern AI training and inference workloads?`

- type: `topical_memory`
- subset: `legacy_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_entities: `['hbm', 'hbm3e', 'ai', 'data center']`
- missing_gold_entities: `[]`
- gold_chunks: `['MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0003_acd8d0ff']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.108 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'QCOM_2025_Item_1_0002_29556203', 'QCOM_2024_Item_1_0002_f2bb0f8a', 'NVDA_2026_Item_1_0005_9725a5a2', 'NVDA_2024_Item_1_0005_7f985cdb']` |
| graph |  | 1.582 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['MU_2025_Item_1A_0005_edea08b6', 'COHR_2025_Item_1A_0002_f9fff32e', 'RMBS_2026_Item_1A_0002_d45dae6f', 'MU_2025_Item_7_0005_9a17157d', 'KLAC_2025_Item_1A_0021_f329ea02']` |
| hybrid |  | 1.707 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'MU_2025_Item_1A_0005_edea08b6', 'COHR_2025_Item_1A_0002_f9fff32e', 'QCOM_2025_Item_1_0002_29556203', 'QCOM_2024_Item_1_0002_f2bb0f8a']` |

### T030: `Which cloud hyperscalers partner with the EPYC processor maker for server CPU deployments in their data centers?`

- type: `customer_via_product`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['graph', 'hybrid']`
- gold_entities: `['epyc', 'amd', 'microsoft', 'amazon', 'google', 'meta']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| vector |  | 0.123 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_1_0010_842113d9', 'INTC_2024_Item_7_0005_d449d027']` |
| graph |  | 1.586 | 0 | 0.004 | 0.000 | 0.000 | 0 | 0 | 1 | 0 | seed_loss | `[]` | `['AMD_2024_Item_1_0011_49024c2d', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0001_1abc85fc', 'AMD_2025_Item_1_0002_6fadf6e4']` |
| hybrid |  | 1.988 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f']` |
