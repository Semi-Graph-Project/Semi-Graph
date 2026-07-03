# Phase T Retrieval Baseline

Generated: 2026-06-29T19:05:44
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `vector, graph, hybrid`
top_k: `5`
oracle_k: `10`
dry_run: `False`
corpus_chunks: `2347`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Random Hit@k | Hit Lift | Hit-Random | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 21 | 0 | 0.333 | 0.004 | 78.329 | 0.329 | 0.224 | 0.286 | 0.429 |
| graph | 21 | 0 | 0.190 | 0.004 | 44.759 | 0.186 | 0.093 | 0.085 | 0.381 |
| hybrid | 21 | 0 | 0.381 | 0.004 | 89.518 | 0.377 | 0.248 | 0.248 | 0.429 |

## By Type

| Type | vector Hit | vector Recall | graph Hit | graph Recall | hybrid Hit | hybrid Recall |
|---|---:|---:|---:|---:|---:|---:|
| competitor_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| customer_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| geo_via_product | 1.000 | 0.500 | 1.000 | 0.500 | 1.000 | 0.500 |
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| partner_via_product | 0.333 | 0.167 | 0.000 | 0.000 | 0.333 | 0.167 |
| product_via_company | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| regulation_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| regulator_via_product | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.500 |
| segment_via_product | 1.000 | 0.500 | 0.000 | 0.000 | 1.000 | 0.500 |
| subsidiary_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| supplier_via_company | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| supplier_via_product | 0.333 | 0.067 | 0.667 | 0.150 | 0.333 | 0.067 |
| three_hop_subsidiary_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| topical_memory | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| vector_friendly | 0.667 | 0.667 | 0.333 | 0.333 | 0.667 | 0.667 |

## Per Query

### T001: `How exposed is AMD to TSMC supply risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 4.360 | 0 | 0.002 | 0.000 | 0.000 | 1 | `[]` | `['AMD_2024_Item_1A_0002_0a71f57a', 'INTC_2026_Item_1A_0006_820d3c64', 'MU_2024_Item_1A_0001_703555bd', 'MU_2025_Item_1A_0001_8d660135', 'INTC_2024_Item_1A_0000_1a5c79ae']` |
| graph |  | 21.774 | 0 | 0.002 | 0.000 | 0.000 | 1 | `[]` | `['AMD_2025_Item_1A_0000_ac2e47a8', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2025_Item_1A_0011_10eec6d1', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` |
| hybrid |  | 2.700 | 1 | 0.002 | 1.000 | 1.000 | 1 | `['AMD_2026_Item_1A_0008_e84e4130']` | `['AMD_2026_Item_1A_0008_e84e4130', 'AMD_2024_Item_1A_0002_0a71f57a', 'AMD_2025_Item_1A_0000_ac2e47a8', 'AMD_2025_Item_1A_0001_0fd81b24', 'INTC_2026_Item_1A_0006_820d3c64']` |

### T002: `Which foundry partner manufactures the Hopper architecture chips?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.114 | 1 | 0.011 | 0.200 | 1.000 | 1 | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0013_cb483288', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_1_0014_32e0816b', 'AMD_2024_Item_1_0012_9561038a']` |
| graph |  | 2.228 | 1 | 0.011 | 0.200 | 1.000 | 1 | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_7_0017_86b90f80', 'INTC_2024_Item_7_0011_0681e088', 'RMBS_2026_Item_7_0001_544e4d1d', 'NVDA_2025_Item_7_0003_d53d3047']` |
| hybrid |  | 1.766 | 1 | 0.011 | 0.200 | 1.000 | 1 | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0013_cb483288', 'INTC_2026_Item_7_0017_86b90f80', 'INTC_2024_Item_7_0011_0681e088', 'INTC_2026_Item_1_0006_d0f653da']` |

### T003: `Who produces the dense memory chips that power modern AI training accelerators?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['MU_2023_Item_1A_0003_92be33e3', 'MU_2025_Item_1A_0004_836bee10', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.170 | 0 | 0.008 | 0.000 | 0.000 | 0 | `[]` | `['RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2026_Item_1_0005_9725a5a2', 'INTC_2026_Item_1_0004_c01224f1']` |
| graph |  | 1.814 | 1 | 0.008 | 0.250 | 0.250 | 1 | `['NVDA_2025_Item_1_0008_a4407f7e']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2024_Item_7_0005_d449d027', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']` |
| hybrid |  | 1.622 | 0 | 0.008 | 0.000 | 0.000 | 1 | `[]` | `['INTC_2025_Item_7_0003_878f7d25', 'INTC_2026_Item_1_0008_c74f560f', 'RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2024_Item_7_0005_d449d027']` |

### T004: `What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1_0003_ea53a6a5']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.100 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'AMD_2026_Item_1_0004_b5e66359']` |
| graph |  | 1.508 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2025_Item_1_0006_551768e4', 'AMD_2026_Item_1_0007_f252541b', 'INTC_2026_Item_1_0007_f3f3671c', 'INTC_2026_Item_1_0008_c74f560f', 'AMD_2024_Item_1_0009_01379c5a']` |
| hybrid |  | 1.536 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2026_Item_1_0007_f3f3671c', 'AMD_2025_Item_1_0006_551768e4', 'INTC_2025_Item_1_0003_707a268b', 'AMD_2026_Item_1_0007_f252541b', 'INTC_2024_Item_1_0005_bcb431a8']` |

### T005: `What political risks affect the home country of the leading pure-play semiconductor foundry?`

- type: `geo_via_supplier`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.095 | n/a | n/a | n/a | n/a | n/a | `[]` | `['QCOM_2023_Item_1A_0031_545bf96a', 'ENTG_2026_Item_1_0004_6f32215b', 'MU_2023_Item_1A_0003_92be33e3', 'ENTG_2025_Item_1_0004_66634bce', 'AMD_2025_Item_1A_0032_0a1cf7f3']` |
| graph |  | 1.626 | n/a | n/a | n/a | n/a | n/a | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'INTC_2024_Item_1A_0009_dd11a01d', 'AVGO_2024_Item_1A_0002_60697233', 'RMBS_2024_Item_1A_0009_16baaed9', 'RMBS_2026_Item_1A_0011_ca481e8f']` |
| hybrid |  | 1.546 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_1A_0032_c870df0c', 'ENTG_2026_Item_1A_0005_d2f79cf3', 'QCOM_2023_Item_1A_0031_545bf96a', 'ENTG_2026_Item_1_0004_6f32215b', 'INTC_2024_Item_1A_0009_dd11a01d']` |

### T006: `Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?`

- type: `supplier_via_company`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.100 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1A_0025_1809ff3b', 'AMKR_2026_Item_1_0003_8dee603e', 'NVDA_2025_Item_1_0002_b74647bb', 'ENTG_2024_Item_1_0007_38140456']` |
| graph |  | 1.460 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2025_Item_1_0001_479b0c1e', 'NVDA_2025_Item_1_0008_a4407f7e', 'RMBS_2026_Item_1_0001_bc3d8a01', 'INTC_2026_Item_1_0008_c74f560f']` |
| hybrid |  | 1.646 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1A_0025_1809ff3b', 'RMBS_2025_Item_1_0001_479b0c1e', 'AMKR_2026_Item_1_0003_8dee603e', 'NVDA_2025_Item_1_0008_a4407f7e']` |

### T007: `What graphics product line does AMD offer to compete with NVIDIA's RTX series?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.108 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0007_0ffd6ad4', 'AMD_2025_Item_1_0009_c842eea0']` |
| graph |  | 1.445 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` |
| hybrid |  | 1.797 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2025_Item_1_0005_e788d800', 'AMD_2025_Item_1_0008_db609f8f']` |

### T008: `Who supplies the high-bandwidth memory used in NVIDIA's H200 data center accelerator?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.110 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2025_Item_1_0002_b74647bb', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2025_Item_1_0001_b64486b7']` |
| graph |  | 1.475 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_7_0001_485abbd3', 'NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2026_Item_1_0009_8c403127', 'NVDA_2026_Item_1_0008_edf8fe4b', 'RMBS_2024_Item_1_0001_1bbcc1ae']` |
| hybrid |  | 1.475 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2026_Item_7_0001_485abbd3', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2025_Item_1_0002_b74647bb']` |

### T009: `How do export controls affect NVIDIA's data center business?`

- type: `risk_via_product`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.082 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b']` |
| graph |  | 1.507 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'AMAT_2025_Item_1A_0017_af7d9be8', 'ENTG_2026_Item_1A_0005_d2f79cf3', 'NVDA_2025_Item_1A_0024_d1a5b506']` |
| hybrid |  | 1.572 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'AMAT_2025_Item_1A_0017_af7d9be8', 'ENTG_2026_Item_1A_0005_d2f79cf3']` |

### T010: `Which materials and purity solutions does Entegris provide to semiconductor manufacturers?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.116 | 1 | 0.002 | 1.000 | 1.000 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0009_ca7ef011', 'ENTG_2025_Item_1_0008_700da46e']` |
| graph |  | 1.542 | 1 | 0.002 | 1.000 | 0.333 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0008_700da46e', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0007_4615acf5', 'ENTG_2026_Item_1_0011_d7877367']` |
| hybrid |  | 1.949 | 1 | 0.002 | 1.000 | 1.000 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0007_4615acf5']` |

### T011: `What gross margin impact did Entegris expect from its useful-life accounting estimate change?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_7_0000_6c99ba90']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.126 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'KLAC_2025_Item_7_0009_be3ecb77', 'KLAC_2024_Item_7_0008_8308f577', 'KLAC_2023_Item_7_0011_e4c656e2', 'ENTG_2026_Item_7_0015_6af235b4']` |
| graph |  | 1.565 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2024_Item_7_0018_b0a46a7f', 'ENTG_2024_Item_7_0019_28ef5c6a', 'AMAT_2023_Item_7_0001_55c419c2']` |
| hybrid |  | 1.754 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2025_Item_7_0007_55d63e3c', 'ENTG_2024_Item_7_0017_71caf017', 'KLAC_2025_Item_7_0009_be3ecb77', 'ENTG_2024_Item_7_0018_b0a46a7f']` |

### T012: `What are Entegris's main business segments?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.115 | 1 | 0.002 | 1.000 | 0.500 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0014_8712752e', 'ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2024_Item_1_0019_b6aee1a3']` |
| graph |  | 1.611 | 0 | 0.002 | 0.000 | 0.000 | 1 | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2026_Item_1_0011_d7877367', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2026_Item_1_0013_2fa9f11c', 'ENTG_2024_Item_1_0018_1e35f935']` |
| hybrid |  | 1.682 | 1 | 0.002 | 1.000 | 0.250 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2024_Item_1_0000_647e6e2c']` |

### T013: `What is AMD's latest FY2025 revenue and gross margin?`

- type: `financial_exact_metric`
- gold_tools: `['financial']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.087 | n/a | n/a | n/a | n/a | n/a | `[]` | `['INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003', 'INTC_2024_Item_1_0003_02f7f00d', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2026_Item_7_0006_2b606b28']` |
| graph |  | 1.650 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2025_Item_7_0001_223169cf', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2024_Item_7_0006_b8de17a3', 'AMD_2025_Item_7_0003_a2d9991c']` |
| hybrid |  | 1.516 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_7_0006_2b606b28', 'AMD_2024_Item_7_0006_b8de17a3', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0001_223169cf']` |

### T014: `What has AMD announced recently?`

- type: `news_recent_event`
- gold_tools: `['news']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.073 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_7_0000_6b145a7b']` |
| graph |  | 1.339 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2025_Item_1_0003_861e4bfa', 'AMD_2026_Item_1_0003_ea53a6a5', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2024_Item_7_0005_86aec648', 'AMD_2024_Item_1_0001_84491be9']` |
| hybrid |  | 4.016 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_1_0003_ea53a6a5']` |

### T015: `What is the relationship between KLA yield improvement tools and downstream AMD gross margin risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.113 | n/a | n/a | n/a | n/a | n/a | `[]` | `['MU_2023_Item_1A_0001_1b8ef3ed', 'AVGO_2025_Item_1A_0008_7b345bfe', 'INTC_2024_Item_7_0015_575e5365', 'AVGO_2023_Item_1A_0018_717a6eeb', 'KLAC_2023_Item_7_0011_e4c656e2']` |
| graph |  | 1.604 | n/a | n/a | n/a | n/a | n/a | `[]` | `['MU_2025_Item_1A_0001_8d660135', 'KLAC_2023_Item_7_0009_9b5b651f', 'KLAC_2023_Item_7_0002_34d825f8', 'KLAC_2024_Item_7_0002_06735542', 'KLAC_2024_Item_7_0006_313cb934']` |
| hybrid |  | 1.647 | n/a | n/a | n/a | n/a | n/a | `[]` | `['MU_2023_Item_1A_0001_1b8ef3ed', 'MU_2025_Item_1A_0001_8d660135', 'AVGO_2025_Item_1A_0008_7b345bfe', 'KLAC_2023_Item_7_0009_9b5b651f', 'INTC_2024_Item_7_0015_575e5365']` |

### T016: `qwerty zzz random semiconductor nonsense`

- type: `off_corpus`
- gold_tools: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.098 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'INTC_2025_Item_1_0001_01b4d21e', 'INTC_2025_Item_1_0002_ba6af228', 'QCOM_2024_Item_1_0009_e0fec737', 'AVGO_2024_Item_7_0008_174ffaeb']` |
| graph |  | 1.686 | n/a | n/a | n/a | n/a | n/a | `[]` | `['RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01', 'RMBS_2024_Item_7_0001_274d79f5', 'RMBS_2026_Item_7_0001_544e4d1d']` |
| hybrid |  | 1.554 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'INTC_2025_Item_1_0001_01b4d21e', 'RMBS_2025_Item_1_0001_479b0c1e', 'INTC_2025_Item_1_0002_ba6af228']` |

### T017: `Which Taiwanese contract chipmaker fabricates AMD's processors?`

- type: `supplier_via_company`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.084 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'MU_2024_Item_1A_0025_1809ff3b', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2024_Item_1_0013_596acde4']` |
| graph |  | 1.429 | 0 | 0.004 | 0.000 | 0.000 | 1 | `[]` | `['AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232', 'RMBS_2025_Item_1_0001_479b0c1e', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1A_0001_0fd81b24']` |
| hybrid |  | 1.448 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232', 'MU_2024_Item_1A_0025_1809ff3b']` |

### T018: `Which gaming console makers partner with the Ryzen processor company?`

- type: `partner_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.082 | 1 | 0.004 | 0.500 | 1.000 | 1 | `['AMD_2026_Item_1_0004_b5e66359']` | `['AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2024_Item_1_0005_7be264c6']` |
| graph |  | 1.366 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_1_0005_7be264c6', 'AMD_2024_Item_1_0009_01379c5a', 'AMD_2025_Item_1_0007_0ffd6ad4']` |
| hybrid |  | 1.711 | 1 | 0.004 | 0.500 | 0.200 | 1 | `['AMD_2026_Item_1_0004_b5e66359']` | `['AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_1_0005_7be264c6', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2026_Item_1_0004_b5e66359']` |

### T019: `What revenue segments does the developer of EPYC processors disclose?`

- type: `segment_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_7_0002_d4114c99']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.099 | 1 | 0.004 | 0.500 | 1.000 | 1 | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'TXN_2025_Item_1_0002_e6c099ac', 'TXN_2024_Item_1_0002_9a773c8b', 'AMD_2026_Item_1_0003_ea53a6a5']` |
| graph |  | 1.438 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2026_Item_7_0005_8ab9ed73', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2025_Item_7_0004_58e0bdd2']` |
| hybrid |  | 1.625 | 1 | 0.004 | 0.500 | 0.500 | 1 | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2025_Item_1_0003_861e4bfa', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2026_Item_7_0005_8ab9ed73']` |

### T020: `What export controls affect AI chip sales from the maker of Blackwell architecture?`

- type: `regulation_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['NVDA_2024_Item_1A_0020_ac4ad7b4', 'NVDA_2024_Item_1A_0022_b1d57eb9']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.095 | 0 | 0.004 | 0.000 | 0.000 | 1 | `[]` | `['AMD_2025_Item_1A_0021_16aa3aa2', 'NVDA_2025_Item_1A_0019_46eda166', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2025_Item_1A_0023_67392e5b']` |
| graph |  | 1.398 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2026_Item_1A_0023_804c637e', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'AMD_2025_Item_1A_0000_ac2e47a8']` |
| hybrid |  | 1.503 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2026_Item_1A_0024_b70c7a18', 'AMD_2025_Item_1A_0021_16aa3aa2']` |

### T021: `Which Asian contract chipmakers fabricate older-generation processors for the developer of Intel 18A?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2024_Item_1A_0001_f0f6c35c', 'INTC_2025_Item_1A_0001_65932be2']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.111 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2026_Item_7_0003_657be427', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_7_0004_e8790cb8', 'MU_2024_Item_1A_0025_1809ff3b']` |
| graph |  | 1.589 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2026_Item_1_0015_adfe2316', 'INTC_2026_Item_1_0014_5d25166d', 'INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_7_0011_0681e088', 'INTC_2026_Item_7_0003_657be427']` |
| hybrid |  | 1.869 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2026_Item_7_0003_657be427', 'INTC_2026_Item_1_0015_adfe2316', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0014_5d25166d', 'INTC_2025_Item_1_0004_c5a12b11']` |

### T022: `Which infrastructure investment firms partner with the maker of Xeon Scalable processors on fab financing?`

- type: `partner_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2025_Item_1_0011_b8759c99', 'INTC_2024_Item_1A_0007_6560bf56']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.119 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2025_Item_1_0007_1d4a96e6', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0008_57402d3f', 'INTC_2024_Item_1_0008_cca3187e']` |
| graph |  | 1.516 | 0 | 0.004 | 0.000 | 0.000 | 1 | `[]` | `['INTC_2026_Item_1_0006_d0f653da', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2024_Item_1_0011_73ce8585', 'INTC_2025_Item_1_0002_ba6af228', 'INTC_2024_Item_1_0012_d9112a33']` |
| hybrid |  | 1.611 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2025_Item_1_0007_1d4a96e6', 'INTC_2026_Item_1_0008_c74f560f']` |

### T023: `Which autonomous driving subsidiary does the developer of Intel Core Ultra operate?`

- type: `subsidiary_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2024_Item_1_0010_4835f632', 'INTC_2024_Item_7_0010_3742bdd2']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.095 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['NVDA_2024_Item_1_0004_12c02096', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2026_Item_1_0010_4bfc9726', 'AMD_2025_Item_1_0002_6fadf6e4']` |
| graph |  | 1.561 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2026_Item_1_0007_f3f3671c', 'INTC_2026_Item_1_0013_cb483288', 'INTC_2025_Item_1_0008_33a03f9d', 'INTC_2025_Item_7_0002_f7953bfd', 'INTC_2024_Item_1_0003_02f7f00d']` |
| hybrid |  | 1.659 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2026_Item_1_0010_4bfc9726', 'INTC_2025_Item_1_0008_33a03f9d', 'INTC_2024_Item_7_0001_d1b7bdde', 'INTC_2026_Item_1_0007_f3f3671c', 'NVDA_2024_Item_1_0004_12c02096']` |

### T024: `Which operating system maker collaborates with the Xeon Scalable processor developer on AI PC platforms?`

- type: `partner_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2024_Item_7_0002_7c82ed88', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.106 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_7_0000_e2ea081b']` |
| graph |  | 1.713 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0011_4307b8ad', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2026_Item_1_0006_d0f653da']` |
| hybrid |  | 1.588 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_1_0004_692d8999', 'INTC_2024_Item_7_0008_57402d3f', 'INTC_2026_Item_1_0004_c01224f1']` |

### T025: `In which U.S. states does the developer of the Intel 18A process operate wafer fabrication facilities?`

- type: `geo_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_1_0014_32e0816b']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.119 | 1 | 0.004 | 0.500 | 0.500 | 1 | `['INTC_2025_Item_1_0004_c5a12b11']` | `['INTC_2025_Item_1_0010_5c90fb55', 'INTC_2025_Item_1_0004_c5a12b11', 'MU_2024_Item_1A_0025_1809ff3b', 'INTC_2026_Item_1_0005_f5ba2220', 'MU_2025_Item_1_0007_ad907262']` |
| graph |  | 1.491 | 1 | 0.004 | 0.500 | 0.200 | 1 | `['INTC_2025_Item_1_0004_c5a12b11']` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'LRCX_2023_Item_1_0005_de991ae1', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2025_Item_1_0004_c5a12b11']` |
| hybrid |  | 1.553 | 1 | 0.004 | 0.500 | 1.000 | 1 | `['INTC_2025_Item_1_0004_c5a12b11']` | `['INTC_2025_Item_1_0004_c5a12b11', 'AMD_2025_Item_1_0009_c842eea0', 'INTC_2025_Item_1_0010_5c90fb55', 'AMD_2026_Item_1_0010_460dfa17', 'LRCX_2023_Item_1_0005_de991ae1']` |

### T026: `What U.S. legislative act funds domestic semiconductor manufacturing expansion at the Intel 18A developer?`

- type: `regulator_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.081 | 1 | 0.004 | 1.000 | 1.000 | 1 | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45']` | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45', 'MU_2025_Item_7_0006_849b23ef', 'MU_2025_Item_1A_0029_541d266d', 'INTC_2026_Item_1_0005_f5ba2220']` |
| graph |  | 1.492 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2026_Item_1_0015_adfe2316', 'INTC_2026_Item_1_0005_f5ba2220', 'INTC_2026_Item_7_0003_657be427', 'INTC_2026_Item_7_0007_62b94998', 'INTC_2026_Item_1_0014_5d25166d']` |
| hybrid |  | 1.734 | 1 | 0.004 | 0.500 | 0.250 | 1 | `['INTC_2026_Item_1A_0008_662b7d4d']` | `['INTC_2026_Item_1_0005_f5ba2220', 'INTC_2026_Item_7_0003_657be427', 'INTC_2025_Item_1_0004_c5a12b11', 'INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2026_Item_1_0015_adfe2316']` |

### T027: `What advanced driver assistance product lines come from the autonomous driving subsidiary of the Xeon Scalable developer?`

- type: `three_hop_subsidiary_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2024_Item_7_0010_3742bdd2', 'INTC_2024_Item_7_0014_e766ac95']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.096 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'NVDA_2024_Item_1_0004_12c02096', 'NVDA_2024_Item_1_0006_f3efd950', 'NVDA_2025_Item_1_0005_85d95b7e', 'INTC_2025_Item_7_0003_878f7d25']` |
| graph |  | 1.688 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'AVGO_2023_Item_1_0010_68f5ffd4', 'NVDA_2025_Item_1_0008_a4407f7e', 'AVGO_2024_Item_1_0012_88739b41', 'NVDA_2026_Item_1_0007_bf6a51b6']` |
| hybrid |  | 1.520 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'AVGO_2023_Item_1_0010_68f5ffd4', 'NVDA_2024_Item_1_0004_12c02096', 'NVDA_2024_Item_1_0006_f3efd950', 'NVDA_2025_Item_1_0008_a4407f7e']` |

### T028: `What consumer storage and DRAM brand is sold by the U.S. supplier of HBM3E memory?`

- type: `product_via_company`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['MU_2025_Item_1_0000_6418b9d4', 'MU_2024_Item_1_0000_82417507']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.102 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0002_74d97a0e', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2024_Item_1_0001_90ffbd18']` |
| graph |  | 1.498 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['MU_2023_Item_1_0001_70be5bda', 'MU_2023_Item_7_0000_e9f96198', 'MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_7_0000_aa4240e3', 'MU_2023_Item_7_0002_c0fab91a']` |
| hybrid |  | 1.619 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['MU_2025_Item_1_0001_b64486b7', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0002_74d97a0e', 'MU_2023_Item_1_0001_70be5bda']` |

### T029: `Why has HBM become critical for modern AI training and inference workloads?`

- type: `topical_memory`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_chunks: `['MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0003_acd8d0ff']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.092 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'QCOM_2025_Item_1_0002_29556203', 'QCOM_2024_Item_1_0002_f2bb0f8a', 'NVDA_2026_Item_1_0005_9725a5a2', 'NVDA_2024_Item_1_0005_7f985cdb']` |
| graph |  | 1.485 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['NVDA_2025_Item_1A_0009_6334facf', 'COHR_2025_Item_1A_0002_f9fff32e', 'MU_2025_Item_1A_0005_edea08b6', 'AMD_2025_Item_7_0001_223169cf', 'INTC_2024_Item_7_0005_d449d027']` |
| hybrid |  | 1.871 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'NVDA_2025_Item_1A_0009_6334facf', 'COHR_2025_Item_1A_0002_f9fff32e', 'QCOM_2025_Item_1_0002_29556203', 'MU_2025_Item_1A_0005_edea08b6']` |

### T030: `Which cloud hyperscalers partner with the EPYC processor maker for server CPU deployments in their data centers?`

- type: `customer_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.108 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_1_0010_842113d9', 'INTC_2024_Item_7_0005_d449d027']` |
| graph |  | 1.479 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2025_Item_7_0005_36426dd3', 'AMD_2024_Item_7_0005_86aec648', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232']` |
| hybrid |  | 1.605 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2024_Item_7_0005_86aec648', 'AMD_2024_Item_1_0003_ee436d61']` |
