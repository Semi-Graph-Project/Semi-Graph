# Phase T Retrieval Baseline

Generated: 2026-07-01T15:22:33
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `graph, hybrid`
top_k: `5`
oracle_k: `20`
dry_run: `False`
corpus_chunks: `2347`
graph_use_expansion: `True`
graph_seed_mode: `triple`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Random Hit@k | Hit Lift | Hit-Random | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| graph | 21 | 0 | 0.381 | 0.004 | 89.518 | 0.377 | 0.248 | 0.210 | 0.571 |
| hybrid | 21 | 0 | 0.429 | 0.004 | 100.708 | 0.424 | 0.295 | 0.311 | 0.667 |

## By Type

| Type | graph Hit | graph Recall | hybrid Hit | hybrid Recall |
|---|---:|---:|---:|---:|
| competitor_product | 0.000 | 0.000 | 0.000 | 0.000 |
| customer_via_product | 0.000 | 0.000 | 0.000 | 0.000 |
| geo_via_product | 1.000 | 1.000 | 1.000 | 1.000 |
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 |
| partner_via_product | 0.333 | 0.333 | 0.333 | 0.167 |
| product_via_company | 0.000 | 0.000 | 0.000 | 0.000 |
| regulation_via_product | 0.000 | 0.000 | 0.000 | 0.000 |
| regulator_via_product | 1.000 | 0.500 | 1.000 | 1.000 |
| segment_via_product | 1.000 | 0.500 | 1.000 | 0.500 |
| subsidiary_via_product | 0.000 | 0.000 | 0.000 | 0.000 |
| supplier_via_company | 1.000 | 0.500 | 1.000 | 0.500 |
| supplier_via_product | 0.667 | 0.233 | 0.667 | 0.233 |
| three_hop_subsidiary_product | 0.000 | 0.000 | 0.000 | 0.000 |
| topical_memory | 0.000 | 0.000 | 0.000 | 0.000 |
| vector_friendly | 0.333 | 0.333 | 0.667 | 0.667 |

## By Subset

| Subset | graph Hit | graph Recall | graph Oracle | hybrid Hit | hybrid Recall | hybrid Oracle |
|---|---:|---:|---:|---:|---:|---:|
| legacy_subset | 0.333 | 0.292 | 0.500 | 0.333 | 0.333 | 0.500 |
| mixed_subset | 1.000 | 0.350 | 1.000 | 1.000 | 0.350 | 1.000 |
| reextract_subset | 0.286 | 0.143 | 0.571 | 0.429 | 0.214 | 0.857 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 1.000 | 1.000 | 0.667 | candidate_pool_loss=2, chunk_mapping_loss=7, hit_top_k=8, rerank_loss=4 |
| legacy_subset | 1.000 | 1.000 | 0.667 | candidate_pool_loss=2, chunk_mapping_loss=4, hit_top_k=4, rerank_loss=2 |
| mixed_subset | 1.000 | 1.000 | 1.000 | hit_top_k=2 |
| reextract_subset | 1.000 | 1.000 | 0.571 | chunk_mapping_loss=3, hit_top_k=2, rerank_loss=2 |

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
| graph |  | 30.495 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'ENTG_2026_Item_1A_0005_d2f79cf3', 'QCOM_2024_Item_1A_0031_686b8f2f', 'AMD_2024_Item_1A_0005_a057bdb2']` |
| hybrid |  | 5.284 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2025_Item_1A_0011_10eec6d1', 'AMD_2024_Item_1A_0002_0a71f57a', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1A_0006_820d3c64']` |

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
| graph |  | 4.423 | 1 | 0.011 | 0.200 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2025_Item_1_0008_a4407f7e']` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2025_Item_7_0003_d53d3047', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2026_Item_7_0002_74a3c132']` |
| hybrid |  | 5.152 | 1 | 0.011 | 0.200 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2026_Item_1_0013_cb483288', 'NVDA_2025_Item_7_0003_d53d3047', 'INTC_2026_Item_1_0006_d0f653da']` |

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
| graph |  | 4.209 | 1 | 0.008 | 0.500 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']` | `['NVDA_2024_Item_1_0007_bae70036', 'AMD_2024_Item_1A_0005_a057bdb2', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'AMD_2025_Item_1_0008_db609f8f']` |
| hybrid |  | 7.550 | 1 | 0.008 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']` | `['NVDA_2024_Item_1_0007_bae70036', 'RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'NVDA_2025_Item_1_0008_a4407f7e', 'INTC_2025_Item_7_0003_878f7d25']` |

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
| graph |  | 6.329 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2026_Item_1_0002_9bce02c2', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2026_Item_7_0001_b0167110', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2025_Item_1_0009_c842eea0']` |
| hybrid |  | 3.635 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_1_0002_9bce02c2', 'INTC_2025_Item_1_0003_707a268b', 'AMD_2024_Item_1_0011_49024c2d', 'INTC_2024_Item_1_0005_bcb431a8', 'AMD_2026_Item_7_0001_b0167110']` |

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
| graph |  | 3.440 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'ENTG_2024_Item_1A_0004_999d6dff', 'AVGO_2025_Item_1A_0003_7aabc04f', 'QCOM_2024_Item_1A_0031_686b8f2f', 'LRCX_2023_Item_1A_0006_e42302c0']` |
| hybrid |  | 3.884 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'QCOM_2023_Item_1A_0031_545bf96a', 'ENTG_2024_Item_1A_0004_999d6dff', 'INTC_2026_Item_1A_0002_066bd50c', 'AVGO_2025_Item_1A_0003_7aabc04f']` |

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
| graph |  | 3.592 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0007_bae70036', 'RMBS_2025_Item_1_0001_479b0c1e', 'AMD_2025_Item_1_0009_c842eea0']` |
| hybrid |  | 3.917 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0007_bae70036', 'MU_2024_Item_1A_0025_1809ff3b', 'AMKR_2026_Item_1_0003_8dee603e']` |

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
| graph |  | 7.721 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e']` |
| hybrid |  | 5.775 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965']` |

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
| graph |  | 3.983 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2026_Item_1_0009_8c403127', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2024_Item_1_0001_1bbcc1ae']` |
| hybrid |  | 4.214 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2025_Item_1_0008_a4407f7e', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0002_b74647bb']` |

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
| graph |  | 7.921 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0025_fb3ee783', 'NVDA_2025_Item_1A_0003_9003fee7', 'NVDA_2025_Item_1A_0024_d1a5b506']` |
| hybrid |  | 4.360 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0023_804c637e', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9']` |

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
| graph |  | 8.726 | 1 | 0.002 | 1.000 | 0.250 | 1 | 1 | 1 | 1 | hit_top_k | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0011_d7877367', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0007_4615acf5']` |
| hybrid |  | 10.689 | 1 | 0.002 | 1.000 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0007_4615acf5']` |

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
| graph |  | 21.121 | 0 | 0.002 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'AVGO_2025_Item_1A_0008_7b345bfe', 'ENTG_2024_Item_7_0005_b82d6e3c', 'LRCX_2024_Item_7_0001_7ebc9805', 'AMAT_2023_Item_7_0001_55c419c2']` |
| hybrid |  | 4.504 | 0 | 0.002 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2025_Item_7_0007_55d63e3c', 'ENTG_2024_Item_7_0017_71caf017', 'AVGO_2025_Item_1A_0008_7b345bfe', 'KLAC_2025_Item_7_0009_be3ecb77']` |

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
| graph |  | 7.604 | 0 | 0.002 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2026_Item_1_0011_d7877367', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2026_Item_1_0013_2fa9f11c', 'ENTG_2024_Item_1_0018_1e35f935']` |
| hybrid |  | 15.376 | 1 | 0.002 | 1.000 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2025_Item_1_0008_700da46e']` |

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
| graph |  | 4.462 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2025_Item_7_0001_223169cf', 'AMD_2024_Item_7_0004_67034475', 'AMD_2025_Item_7_0003_a2d9991c', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2026_Item_7_0000_6b145a7b']` |
| hybrid |  | 6.869 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_7_0006_2b606b28', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0001_223169cf', 'INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003']` |

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
| graph |  | 6.854 | n/a | n/a | n/a | n/a | n/a | 0 | 1 | n/a | unscored_discovery | `[]` | `['AMD_2026_Item_1_0005_808c1965', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0003_861e4bfa']` |
| hybrid |  | 9.823 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2025_Item_1_0003_861e4bfa']` |

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
| graph |  | 3.799 | n/a | n/a | n/a | n/a | n/a | 1 | 1 | n/a | unscored_discovery | `[]` | `['KLAC_2023_Item_7_0009_9b5b651f', 'KLAC_2024_Item_7_0006_313cb934', 'AMD_2024_Item_1A_0008_027b0f68', 'AMD_2025_Item_1A_0009_57657610', 'KLAC_2023_Item_7_0002_34d825f8']` |
| hybrid |  | 5.833 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['KLAC_2024_Item_1_0005_f2fc0653', 'MU_2023_Item_1A_0001_1b8ef3ed', 'AVGO_2025_Item_1A_0008_7b345bfe', 'KLAC_2023_Item_7_0009_9b5b651f', 'INTC_2024_Item_7_0015_575e5365']` |

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
| graph |  | 6.572 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | unscored_discovery | `[]` | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e']` |
| hybrid |  | 4.077 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'NVDA_2024_Item_1_0007_bae70036', 'INTC_2025_Item_1_0001_01b4d21e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2025_Item_1_0002_ba6af228']` |

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
| graph |  | 3.101 | 1 | 0.004 | 0.500 | 1.000 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2025_Item_1_0009_c842eea0']` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1A_0001_0fd81b24', 'NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2025_Item_1_0001_479b0c1e']` |
| hybrid |  | 3.738 | 1 | 0.004 | 0.500 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2025_Item_1_0009_c842eea0']` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'MU_2024_Item_1A_0025_1809ff3b']` |

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
| graph |  | 3.496 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2025_Item_1_0004_7a6fa20c']` |
| hybrid |  | 3.548 | 1 | 0.004 | 0.500 | 0.200 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0006_e41aed21']` | `['AMD_2026_Item_1_0005_808c1965', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2024_Item_1_0005_7be264c6', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0006_e41aed21']` |

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
| graph |  | 10.893 | 1 | 0.004 | 0.500 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2026_Item_7_0000_6b145a7b', 'AMD_2026_Item_7_0005_8ab9ed73', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0003_861e4bfa']` |
| hybrid |  | 7.750 | 1 | 0.004 | 0.500 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_7_0005_36426dd3']` |

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
| graph |  | 9.162 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2026_Item_1A_0022_3d4f4d9b', 'NVDA_2025_Item_1A_0003_9003fee7']` |
| hybrid |  | 8.118 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2026_Item_1A_0020_331dc537']` |

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
| graph |  | 26.175 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2024_Item_7_0011_0681e088', 'NVDA_2024_Item_1_0008_20833acc', 'AVGO_2024_Item_1_0012_88739b41']` |
| hybrid |  | 6.273 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2024_Item_7_0011_0681e088', 'INTC_2026_Item_7_0003_657be427', 'INTC_2024_Item_7_0000_e2ea081b']` |

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
| graph |  | 11.872 | 1 | 0.004 | 1.000 | 0.333 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2025_Item_1_0011_b8759c99', 'INTC_2024_Item_1A_0007_6560bf56']` | `['INTC_2025_Item_1A_0007_42fef1f5', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2025_Item_1_0011_b8759c99', 'INTC_2026_Item_1A_0007_7a211a24', 'INTC_2024_Item_1A_0007_6560bf56']` |
| hybrid |  | 5.811 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0004_63451c7a']` |

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
| graph |  | 3.972 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['INTC_2024_Item_7_0011_0681e088', 'INTC_2026_Item_7_0017_86b90f80', 'INTC_2024_Item_7_0002_7c82ed88', 'INTC_2024_Item_7_0009_2d5f3afe', 'INTC_2026_Item_7_0015_d45d810d']` |
| hybrid |  | 12.944 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0002_7c82ed88', 'INTC_2024_Item_7_0011_0681e088', 'NVDA_2024_Item_1_0004_12c02096', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2026_Item_7_0017_86b90f80']` |

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
| graph |  | 3.263 | 0 | 0.004 | 0.000 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_7_0004_63451c7a', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2026_Item_1_0006_d0f653da']` |
| hybrid |  | 4.712 | 0 | 0.004 | 0.000 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2024_Item_7_0000_e2ea081b']` |

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
| graph |  | 6.016 | 1 | 0.004 | 1.000 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2024_Item_1_0014_32e0816b', 'INTC_2025_Item_1_0004_c5a12b11']` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_1_0014_32e0816b', 'INTC_2025_Item_1_0004_c5a12b11', 'INTC_2025_Item_1_0009_d132a876', 'INTC_2025_Item_1_0010_5c90fb55']` |
| hybrid |  | 6.082 | 1 | 0.004 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_1_0014_32e0816b']` | `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2025_Item_1_0010_5c90fb55', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_1_0014_32e0816b', 'MU_2024_Item_1A_0025_1809ff3b']` |

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
| graph |  | 3.392 | 1 | 0.004 | 0.500 | 0.500 | 1 | 1 | 1 | 1 | hit_top_k | `['INTC_2025_Item_1A_0008_80e72e45']` | `['INTC_2024_Item_7_0011_0681e088', 'INTC_2025_Item_1A_0008_80e72e45', 'INTC_2025_Item_7_0016_775a205b', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2025_Item_7_0013_1869b003']` |
| hybrid |  | 11.948 | 1 | 0.004 | 1.000 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d']` | `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_7_0016_775a205b', 'MU_2025_Item_7_0006_849b23ef']` |

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
| graph |  | 3.720 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 1 | candidate_pool_loss | `[]` | `['INTC_2024_Item_7_0011_0681e088', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2026_Item_1_0007_f3f3671c', 'AVGO_2023_Item_1_0010_68f5ffd4', 'NVDA_2025_Item_1_0008_a4407f7e']` |
| hybrid |  | 3.568 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0011_0681e088', 'NVDA_2024_Item_1_0004_12c02096', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2026_Item_1_0007_f3f3671c']` |

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
| graph |  | 5.222 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 1 | candidate_pool_loss | `[]` | `['MU_2023_Item_1_0001_70be5bda', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2024_Item_1_0004_6e2de1a4', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2025_Item_1_0001_b64486b7']` |
| hybrid |  | 4.467 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['MU_2025_Item_1_0001_b64486b7', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0002_74d97a0e', 'MU_2023_Item_1_0001_70be5bda']` |

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
| graph |  | 6.689 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['RMBS_2025_Item_1_0001_479b0c1e', 'MU_2025_Item_1A_0005_edea08b6', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2026_Item_1_0001_bc3d8a01', 'INTC_2025_Item_1A_0000_ac3a3dbc']` |
| hybrid |  | 7.687 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'MU_2025_Item_1A_0005_edea08b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'QCOM_2025_Item_1_0002_29556203', 'NVDA_2026_Item_1_0007_bf6a51b6']` |

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
| graph |  | 8.235 | 0 | 0.004 | 0.000 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `['AMD_2024_Item_1_0011_49024c2d', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_7_0005_36426dd3']` |
| hybrid |  | 3.945 | 0 | 0.004 | 0.000 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f']` |
