# Phase T Retrieval Baseline

Generated: 2026-07-03T02:59:22
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `vector, graph, hybrid`
top_k: `5`
oracle_k: `20`
dry_run: `False`
corpus_chunks: `2346`
graph_use_expansion: `True`
graph_seed_mode: `triple`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Random Hit@k | Hit Lift | Hit-Random | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 21 | 0 | 0.333 | 0.004 | 78.295 | 0.329 | 0.224 | 0.286 | 0.524 |
| graph | 21 | 0 | 0.286 | 0.004 | 67.110 | 0.281 | 0.205 | 0.135 | 0.524 |
| hybrid | 21 | 0 | 0.429 | 0.004 | 100.665 | 0.424 | 0.293 | 0.299 | 0.571 |

## By Type

| Type | vector Hit | vector Recall | graph Hit | graph Recall | hybrid Hit | hybrid Recall |
|---|---:|---:|---:|---:|---:|---:|
| competitor_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| customer_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| geo_via_product | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 |
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| partner_via_product | 0.333 | 0.167 | 0.333 | 0.167 | 0.333 | 0.167 |
| product_via_company | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| regulation_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| regulator_via_product | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| segment_via_product | 1.000 | 0.500 | 0.000 | 0.000 | 1.000 | 0.500 |
| subsidiary_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| supplier_via_company | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.500 |
| supplier_via_product | 0.333 | 0.067 | 0.667 | 0.433 | 0.667 | 0.217 |
| three_hop_subsidiary_product | 0.000 | 0.000 | 1.000 | 0.500 | 0.000 | 0.000 |
| topical_memory | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| vector_friendly | 0.667 | 0.667 | 0.333 | 0.333 | 0.667 | 0.667 |

## By Subset

| Subset | vector Hit | vector Recall | vector Oracle | graph Hit | graph Recall | graph Oracle | hybrid Hit | hybrid Recall | hybrid Oracle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| reextract_subset | 0.333 | 0.224 | 0.524 | 0.286 | 0.205 | 0.524 | 0.429 | 0.293 | 0.571 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 1.000 | 1.000 | 0.524 | chunk_mapping_loss=10, hit_top_k=6, rerank_loss=5 |
| reextract_subset | 1.000 | 1.000 | 0.524 | chunk_mapping_loss=10, hit_top_k=6, rerank_loss=5 |

## Paired Recall Test vs Vector

| Subset | Tool | n | Mean Delta Recall | One-sided p |
|---|---|---:|---:|---:|
| full_mixed | graph | 21 | -0.019 | 1.000 |
| full_mixed | hybrid | 21 | 0.069 | 0.063 |
| reextract_subset | graph | 21 | -0.019 | 1.000 |
| reextract_subset | hybrid | 21 | 0.069 | 0.063 |

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
| vector |  | 12.137 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1A_0002_0a71f57a', 'INTC_2026_Item_1A_0006_820d3c64', 'MU_2024_Item_1A_0001_703555bd', 'MU_2025_Item_1A_0001_8d660135', 'INTC_2024_Item_1A_0000_1a5c79ae']` |
| graph |  | 40.040 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2026_Item_1A_0000_268148d2']` |
| hybrid |  | 4.794 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_1A_0000_268148d2', 'AMD_2024_Item_1A_0002_0a71f57a', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1A_0006_820d3c64']` |

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
| vector |  | 0.135 | 1 | 0.011 | 0.200 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2026_Item_1_0013_cb483288', 'INTC_2024_Item_1_0014_32e0816b', 'AMD_2024_Item_1_0012_9561038a']` |
| graph |  | 4.480 | 1 | 0.011 | 0.800 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2024_Item_1_0007_bae70036']` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2024_Item_1_0007_bae70036']` |
| hybrid |  | 3.698 | 1 | 0.011 | 0.400 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2025_Item_1_0008_a4407f7e']` | `['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2026_Item_1_0006_d0f653da', 'NVDA_2025_Item_1_0008_a4407f7e', 'INTC_2026_Item_1_0013_cb483288']` |

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
| vector |  | 0.130 | 0 | 0.009 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2026_Item_1_0005_9725a5a2', 'INTC_2026_Item_1_0004_c01224f1']` |
| graph |  | 4.406 | 1 | 0.009 | 0.500 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0007_bae70036']` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2024_Item_1A_0005_a057bdb2', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2024_Item_1_0008_20833acc']` |
| hybrid |  | 3.882 | 1 | 0.009 | 0.250 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2025_Item_1_0008_a4407f7e']` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'NVDA_2025_Item_1_0008_a4407f7e', 'INTC_2025_Item_7_0003_878f7d25']` |

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
| vector |  | 0.113 | 0 | 0.002 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2026_Item_1_0005_9725a5a2']` |
| graph |  | 7.981 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0008_db609f8f']` |
| hybrid |  | 13.640 | 0 | 0.002 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0006_551768e4', 'INTC_2024_Item_1_0005_bcb431a8', 'AMD_2026_Item_1_0007_f252541b', 'INTC_2026_Item_1_0004_c01224f1']` |

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
| vector |  | 0.135 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['QCOM_2023_Item_1A_0031_545bf96a', 'INTC_2026_Item_1A_0002_066bd50c', 'ENTG_2026_Item_1_0004_6f32215b', 'ENTG_2025_Item_1_0004_66634bce', 'MU_2023_Item_1A_0003_92be33e3']` |
| graph |  | 3.822 | n/a | n/a | n/a | n/a | n/a | 0 | 0 | n/a | unscored_discovery | `[]` | `['RMBS_2024_Item_1A_0009_16baaed9', 'QCOM_2025_Item_1A_0032_e982eae3', 'INTC_2026_Item_1A_0000_268148d2', 'AMKR_2025_Item_1A_0009_1710080b', 'RMBS_2024_Item_1A_0011_64758079']` |
| hybrid |  | 3.531 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['QCOM_2023_Item_1A_0031_545bf96a', 'RMBS_2024_Item_1A_0009_16baaed9', 'ENTG_2026_Item_1_0004_6f32215b', 'QCOM_2025_Item_1A_0032_e982eae3', 'ENTG_2025_Item_1_0004_66634bce']` |

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
| vector |  | 0.129 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1A_0025_1809ff3b', 'AMKR_2026_Item_1_0003_8dee603e', 'NVDA_2024_Item_1_0002_2ddf2e3b', 'AMD_2024_Item_1_0012_9561038a']` |
| graph |  | 3.666 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0007_bae70036', 'RMBS_2025_Item_1_0001_479b0c1e', 'AMD_2025_Item_1_0009_c842eea0']` |
| hybrid |  | 4.127 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0007_bae70036', 'MU_2024_Item_1A_0025_1809ff3b', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMKR_2026_Item_1_0003_8dee603e']` |

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
| vector |  | 0.132 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0007_0ffd6ad4', 'AMD_2025_Item_1A_0002_2bc1ccc8']` |
| graph |  | 3.409 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2024_Item_1_0009_01379c5a', 'AMD_2025_Item_1_0006_551768e4']` |
| hybrid |  | 8.269 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965']` |

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
| vector |  | 0.132 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2025_Item_1_0002_b74647bb', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2025_Item_1_0001_b64486b7']` |
| graph |  | 3.292 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2025_Item_1_0001_479b0c1e', 'NVDA_2024_Item_1_0007_bae70036', 'RMBS_2024_Item_1_0001_1bbcc1ae']` |
| hybrid |  | 5.382 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2025_Item_1_0002_b74647bb', 'NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2025_Item_1_0001_b64486b7']` |

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
| vector |  | 0.114 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2025_Item_1A_0019_46eda166']` |
| graph |  | 3.250 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2026_Item_1A_0025_fb3ee783', 'NVDA_2025_Item_1A_0003_9003fee7']` |
| hybrid |  | 4.150 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0023_804c637e', 'NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2026_Item_1A_0022_3d4f4d9b']` |

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
| vector |  | 0.125 | 1 | 0.002 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0009_ca7ef011', 'ENTG_2025_Item_1_0008_700da46e']` |
| graph |  | 8.212 | 1 | 0.002 | 1.000 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0013_d310ee7e', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0007_4615acf5']` |
| hybrid |  | 17.306 | 1 | 0.002 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0007_4615acf5']` |

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
| vector |  | 0.122 | 0 | 0.002 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'KLAC_2025_Item_7_0009_be3ecb77', 'KLAC_2024_Item_7_0008_8308f577', 'ENTG_2026_Item_7_0015_6af235b4', 'NVDA_2026_Item_7_0006_ec90a691']` |
| graph |  | 4.398 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2025_Item_7_0016_c8496ed0', 'ENTG_2024_Item_7_0019_28ef5c6a', 'ENTG_2026_Item_7_0015_6af235b4', 'ENTG_2024_Item_1A_0011_7fd5fc5f']` |
| hybrid |  | 26.149 | 0 | 0.002 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2026_Item_7_0015_6af235b4', 'ENTG_2025_Item_7_0016_c8496ed0', 'KLAC_2025_Item_7_0009_be3ecb77', 'ENTG_2024_Item_7_0019_28ef5c6a']` |

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
| vector |  | 0.116 | 1 | 0.002 | 1.000 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0014_8712752e', 'ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2024_Item_1_0019_b6aee1a3']` |
| graph |  | 13.489 | 0 | 0.002 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['ENTG_2024_Item_1_0008_9f625423', 'ENTG_2025_Item_7_0016_c8496ed0', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2024_Item_1_0001_61f633dc', 'ENTG_2025_Item_1_0000_7efdfd60']` |
| hybrid |  | 16.061 | 1 | 0.002 | 1.000 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2024_Item_1_0008_9f625423']` |

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
| vector |  | 0.123 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003', 'INTC_2024_Item_1_0003_02f7f00d', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2026_Item_7_0006_2b606b28']` |
| graph |  | 3.357 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2025_Item_7_0001_223169cf', 'AMD_2024_Item_7_0004_67034475', 'AMD_2025_Item_7_0003_a2d9991c', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2026_Item_7_0000_6b145a7b']` |
| hybrid |  | 3.925 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_7_0006_2b606b28', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0001_223169cf', 'INTC_2024_Item_7_0015_575e5365', 'AMD_2024_Item_7_0004_67034475']` |

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
| vector |  | 0.092 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_7_0000_6b145a7b']` |
| graph |  | 6.131 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2026_Item_1A_0002_72e02a77', 'AMD_2024_Item_1_0011_49024c2d']` |
| hybrid |  | 6.132 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0004_b5e66359']` |

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
| vector |  | 0.130 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['MU_2023_Item_1A_0001_1b8ef3ed', 'AVGO_2025_Item_1A_0008_7b345bfe', 'INTC_2024_Item_7_0015_575e5365', 'AVGO_2023_Item_1A_0018_717a6eeb', 'KLAC_2024_Item_7_0008_8308f577']` |
| graph |  | 11.210 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2024_Item_1A_0015_22ab1f05', 'AMD_2025_Item_1A_0011_10eec6d1', 'AMD_2024_Item_1A_0008_027b0f68', 'AMD_2025_Item_1A_0009_57657610', 'AMD_2024_Item_1A_0010_a0734f02']` |
| hybrid |  | 10.328 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1A_0010_a0734f02', 'AMD_2026_Item_1A_0010_025c9883', 'AMD_2024_Item_1A_0008_027b0f68', 'MU_2023_Item_1A_0001_1b8ef3ed', 'AMD_2025_Item_1A_0009_57657610']` |

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
| vector |  | 0.113 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'INTC_2025_Item_1_0001_01b4d21e', 'INTC_2025_Item_1_0002_ba6af228', 'QCOM_2024_Item_1_0009_e0fec737', 'AVGO_2024_Item_7_0008_174ffaeb']` |
| graph |  | 5.046 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | unscored_discovery | `[]` | `['RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2026_Item_1_0001_bc3d8a01', 'NVDA_2025_Item_1_0008_a4407f7e']` |
| hybrid |  | 5.524 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'INTC_2025_Item_1_0001_01b4d21e', 'RMBS_2025_Item_1_0001_479b0c1e', 'INTC_2025_Item_1_0002_ba6af228']` |

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
| vector |  | 0.111 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'MU_2024_Item_1A_0025_1809ff3b', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2024_Item_1_0013_596acde4']` |
| graph |  | 3.496 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['AMD_2025_Item_1A_0032_0a1cf7f3', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2024_Item_1A_0005_a057bdb2', 'AMD_2025_Item_1A_0000_ac2e47a8', 'AMD_2026_Item_1A_0002_72e02a77']` |
| hybrid |  | 6.573 | 1 | 0.004 | 0.500 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2025_Item_1_0009_c842eea0']` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'MU_2024_Item_1A_0025_1809ff3b']` |

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
| vector |  | 0.114 | 1 | 0.004 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2026_Item_1_0004_b5e66359']` | `['AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2024_Item_1_0005_7be264c6']` |
| graph |  | 4.288 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0005_7be264c6']` |
| hybrid |  | 4.311 | 1 | 0.004 | 0.500 | 0.200 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0006_e41aed21']` | `['AMD_2026_Item_1_0005_808c1965', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2024_Item_1_0005_7be264c6', 'AMD_2024_Item_1_0006_e41aed21']` |

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
| vector |  | 0.111 | 1 | 0.004 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'TXN_2025_Item_1_0002_e6c099ac', 'TXN_2024_Item_1_0002_9a773c8b', 'RMBS_2026_Item_7_0004_bb93ee55']` |
| graph |  | 3.942 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2024_Item_7_0004_67034475', 'AMD_2025_Item_7_0001_223169cf', 'AMD_2025_Item_7_0003_a2d9991c', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2026_Item_7_0006_2b606b28']` |
| hybrid |  | 4.842 | 1 | 0.004 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2026_Item_7_0005_8ab9ed73', 'TXN_2025_Item_1_0002_e6c099ac']` |

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
| vector |  | 0.120 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2025_Item_1A_0023_67392e5b']` |
| graph |  | 6.203 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'KLAC_2024_Item_1A_0003_7bca5862', 'NVDA_2024_Item_1A_0018_aa47ec2b']` |
| hybrid |  | 10.127 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2026_Item_1A_0020_331dc537']` |

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
| vector |  | 0.138 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_7_0003_657be427', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2025_Item_7_0000_d16d1424', 'INTC_2026_Item_1_0007_f3f3671c']` |
| graph |  | 13.474 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0004_c01224f1', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2026_Item_1A_0014_753689d7', 'INTC_2024_Item_7_0011_0681e088']` |
| hybrid |  | 9.446 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0000_d16d1424', 'NVDA_2026_Item_1_0007_bf6a51b6']` |

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
| vector |  | 0.133 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2025_Item_1_0007_1d4a96e6', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0008_57402d3f', 'INTC_2024_Item_1_0008_cca3187e']` |
| graph |  | 4.530 | 1 | 0.004 | 0.500 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2024_Item_1A_0007_6560bf56']` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_1A_0007_6560bf56', 'INTC_2025_Item_1_0000_22438b0f', 'INTC_2026_Item_1_0008_c74f560f']` |
| hybrid |  | 14.865 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0004_c01224f1']` |

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
| vector |  | 0.196 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0004_12c02096', 'INTC_2025_Item_1_0003_707a268b', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2026_Item_1_0010_4bfc9726']` |
| graph |  | 3.475 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0002_f7953bfd', 'INTC_2026_Item_1_0007_f3f3671c', 'INTC_2024_Item_7_0002_7c82ed88', 'INTC_2024_Item_7_0000_e2ea081b']` |
| hybrid |  | 6.307 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0002_7c82ed88', 'INTC_2026_Item_1_0010_4bfc9726', 'INTC_2026_Item_1_0004_c01224f1', 'NVDA_2024_Item_1_0004_12c02096', 'AMD_2025_Item_1_0002_6fadf6e4']` |

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
| vector |  | 0.130 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_7_0000_e2ea081b']` |
| graph |  | 9.209 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2026_Item_1_0011_4307b8ad']` |
| hybrid |  | 3.971 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_7_0003_878f7d25', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_7_0004_63451c7a']` |

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
| vector |  | 0.137 | 1 | 0.004 | 0.500 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1_0004_c5a12b11']` | `['INTC_2025_Item_1_0010_5c90fb55', 'INTC_2025_Item_1_0004_c5a12b11', 'MU_2024_Item_1A_0025_1809ff3b', 'TXN_2024_Item_1_0004_06070784', 'INTC_2026_Item_1_0005_f5ba2220']` |
| graph |  | 5.398 | 1 | 0.004 | 1.000 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_1_0014_32e0816b']` | `['INTC_2026_Item_1_0014_5d25166d', 'INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_1_0014_32e0816b', 'INTC_2025_Item_1_0009_d132a876']` |
| hybrid |  | 9.541 | 1 | 0.004 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_1_0014_32e0816b']` | `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2025_Item_1_0010_5c90fb55', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_1_0014_32e0816b', 'MU_2024_Item_1A_0025_1809ff3b']` |

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
| vector |  | 0.211 | 1 | 0.004 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45']` | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45', 'MU_2025_Item_7_0006_849b23ef', 'MU_2025_Item_1A_0029_541d266d', 'INTC_2026_Item_1_0005_f5ba2220']` |
| graph |  | 3.493 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2026_Item_7_0000_3c580005', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2026_Item_7_0017_86b90f80', 'INTC_2025_Item_1_0011_b8759c99', 'NVDA_2024_Item_1_0007_bae70036']` |
| hybrid |  | 5.821 | 1 | 0.004 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d']` | `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2026_Item_7_0000_3c580005', 'INTC_2025_Item_7_0016_775a205b', 'INTC_2024_Item_1A_0007_6560bf56']` |

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
| vector |  | 0.134 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'NVDA_2024_Item_1_0004_12c02096', 'NVDA_2024_Item_1_0006_f3efd950', 'NVDA_2025_Item_1_0005_85d95b7e', 'INTC_2025_Item_7_0003_878f7d25']` |
| graph |  | 5.373 | 1 | 0.004 | 0.500 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2024_Item_7_0010_3742bdd2']` | `['INTC_2024_Item_7_0009_2d5f3afe', 'INTC_2024_Item_7_0010_3742bdd2', 'INTC_2026_Item_1A_0000_268148d2', 'INTC_2024_Item_7_0011_0681e088', 'NVDA_2026_Item_1_0007_bf6a51b6']` |
| hybrid |  | 3.947 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1A_0000_268148d2', 'NVDA_2024_Item_1_0004_12c02096', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0006_f3efd950']` |

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
| vector |  | 0.137 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0002_74d97a0e', 'MU_2023_Item_1_0003_fb3cb967', 'RMBS_2025_Item_1_0001_479b0c1e']` |
| graph |  | 4.246 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['MU_2024_Item_1_0002_473014b9', 'MU_2024_Item_1_0009_25e18f42', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0001_70be5bda', 'MU_2023_Item_7_0002_c0fab91a']` |
| hybrid |  | 3.831 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['MU_2025_Item_1_0010_ef8bd774', 'RMBS_2025_Item_1_0001_479b0c1e', 'MU_2024_Item_1_0009_25e18f42', 'MU_2025_Item_1_0001_b64486b7', 'MU_2023_Item_1_0001_70be5bda']` |

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
| vector |  | 0.125 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'QCOM_2025_Item_1_0002_29556203', 'QCOM_2024_Item_1_0002_f2bb0f8a', 'NVDA_2026_Item_1_0005_9725a5a2', 'KLAC_2025_Item_1A_0021_f329ea02']` |
| graph |  | 4.970 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0007_bae70036', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2024_Item_7_0001_274d79f5']` |
| hybrid |  | 7.873 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'QCOM_2025_Item_1_0002_29556203', 'NVDA_2026_Item_1_0007_bf6a51b6']` |

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
| vector |  | 0.152 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_1_0010_842113d9', 'INTC_2024_Item_7_0008_57402d3f']` |
| graph |  | 5.097 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2024_Item_1_0011_49024c2d', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_7_0005_36426dd3']` |
| hybrid |  | 6.679 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f']` |
