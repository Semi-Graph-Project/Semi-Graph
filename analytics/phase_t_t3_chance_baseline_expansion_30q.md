# Phase T Retrieval Baseline

Generated: 2026-06-29T19:14:13
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
| graph | 21 | 0 | 0.524 | 0.004 | 123.088 | 0.520 | 0.348 | 0.345 | 0.571 |
| hybrid | 21 | 0 | 0.524 | 0.004 | 123.088 | 0.520 | 0.352 | 0.409 | 0.619 |

## By Type

| Type | vector Hit | vector Recall | graph Hit | graph Recall | hybrid Hit | hybrid Recall |
|---|---:|---:|---:|---:|---:|---:|
| competitor_product | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| customer_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| geo_via_product | 1.000 | 0.500 | 1.000 | 0.500 | 1.000 | 0.500 |
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| partner_via_product | 0.333 | 0.167 | 1.000 | 0.667 | 0.333 | 0.167 |
| product_via_company | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| regulation_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.500 |
| regulator_via_product | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 1.000 |
| segment_via_product | 1.000 | 0.500 | 1.000 | 0.500 | 1.000 | 0.500 |
| subsidiary_via_product | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| supplier_via_company | 0.000 | 0.000 | 1.000 | 0.500 | 1.000 | 0.500 |
| supplier_via_product | 0.333 | 0.067 | 0.667 | 0.433 | 0.667 | 0.300 |
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
| vector |  | 3.891 | 0 | 0.002 | 0.000 | 0.000 | 1 | `[]` | `['AMD_2024_Item_1A_0002_0a71f57a', 'INTC_2026_Item_1A_0006_820d3c64', 'MU_2024_Item_1A_0001_703555bd', 'MU_2025_Item_1A_0001_8d660135', 'INTC_2024_Item_1A_0000_1a5c79ae']` |
| graph |  | 23.998 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'QCOM_2024_Item_1A_0031_686b8f2f', 'RMBS_2025_Item_1_0001_479b0c1e', 'LRCX_2023_Item_1_0005_de991ae1', 'LRCX_2023_Item_1A_0006_e42302c0']` |
| hybrid |  | 8.776 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2024_Item_1A_0002_0a71f57a', 'QCOM_2025_Item_1A_0032_e982eae3', 'INTC_2026_Item_1A_0006_820d3c64', 'QCOM_2024_Item_1A_0031_686b8f2f', 'MU_2024_Item_1A_0001_703555bd']` |

### T002: `Which foundry partner manufactures the Hopper architecture chips?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.096 | 1 | 0.011 | 0.200 | 1.000 | 1 | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0013_cb483288', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_1_0014_32e0816b', 'AMD_2024_Item_1_0012_9561038a']` |
| graph |  | 3.878 | 1 | 0.011 | 0.800 | 1.000 | 1 | `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` | `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0007_bae70036', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` |
| hybrid |  | 2.828 | 1 | 0.011 | 0.400 | 1.000 | 1 | `['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2025_Item_1_0008_a4407f7e']` | `['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2025_Item_1_0008_a4407f7e', 'INTC_2026_Item_1_0013_cb483288', 'NVDA_2026_Item_1_0007_bf6a51b6', 'INTC_2026_Item_1_0006_d0f653da']` |

### T003: `Who produces the dense memory chips that power modern AI training accelerators?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['MU_2023_Item_1A_0003_92be33e3', 'MU_2025_Item_1A_0004_836bee10', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.103 | 0 | 0.008 | 0.000 | 0.000 | 0 | `[]` | `['RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2026_Item_1_0005_9725a5a2', 'INTC_2026_Item_1_0004_c01224f1']` |
| graph |  | 3.483 | 1 | 0.008 | 0.500 | 1.000 | 1 | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']` | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01']` |
| hybrid |  | 4.141 | 1 | 0.008 | 0.500 | 1.000 | 1 | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']` | `['NVDA_2024_Item_1_0007_bae70036', 'RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'NVDA_2025_Item_1_0008_a4407f7e', 'INTC_2025_Item_7_0003_878f7d25']` |

### T004: `What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1_0003_ea53a6a5']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.101 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'AMD_2026_Item_1_0004_b5e66359']` |
| graph |  | 10.273 | 1 | 0.002 | 1.000 | 1.000 | 1 | `['AMD_2026_Item_1_0003_ea53a6a5']` | `['AMD_2026_Item_1_0003_ea53a6a5', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2026_Item_1_0002_9bce02c2', 'AMD_2024_Item_1_0009_01379c5a', 'AMD_2026_Item_1_0007_f252541b']` |
| hybrid |  | 6.677 | 1 | 0.002 | 1.000 | 1.000 | 1 | `['AMD_2026_Item_1_0003_ea53a6a5']` | `['AMD_2026_Item_1_0003_ea53a6a5', 'INTC_2025_Item_1_0003_707a268b', 'AMD_2026_Item_1_0007_f252541b', 'INTC_2024_Item_1_0005_bcb431a8', 'AMD_2025_Item_1_0006_551768e4']` |

### T005: `What political risks affect the home country of the leading pure-play semiconductor foundry?`

- type: `geo_via_supplier`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.152 | n/a | n/a | n/a | n/a | n/a | `[]` | `['QCOM_2023_Item_1A_0031_545bf96a', 'ENTG_2026_Item_1_0004_6f32215b', 'MU_2023_Item_1A_0003_92be33e3', 'ENTG_2025_Item_1_0004_66634bce', 'AMD_2025_Item_1A_0032_0a1cf7f3']` |
| graph |  | 3.939 | n/a | n/a | n/a | n/a | n/a | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'ENTG_2024_Item_1A_0004_999d6dff', 'AVGO_2025_Item_1A_0003_7aabc04f', 'QCOM_2024_Item_1A_0031_686b8f2f', 'ENTG_2025_Item_1A_0005_1b7cb400']` |
| hybrid |  | 3.302 | n/a | n/a | n/a | n/a | n/a | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'QCOM_2023_Item_1A_0031_545bf96a', 'ENTG_2024_Item_1A_0004_999d6dff', 'ENTG_2026_Item_1_0004_6f32215b', 'AVGO_2025_Item_1A_0003_7aabc04f']` |

### T006: `Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?`

- type: `supplier_via_company`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.108 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1A_0025_1809ff3b', 'AMKR_2026_Item_1_0003_8dee603e', 'NVDA_2025_Item_1_0002_b74647bb', 'ENTG_2024_Item_1_0007_38140456']` |
| graph |  | 3.859 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2024_Item_1A_0009_58e16c0f']` |
| hybrid |  | 3.635 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1A_0025_1809ff3b', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMKR_2026_Item_1_0003_8dee603e', 'NVDA_2024_Item_1_0007_bae70036']` |

### T007: `What graphics product line does AMD offer to compete with NVIDIA's RTX series?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.101 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0007_0ffd6ad4', 'AMD_2025_Item_1_0009_c842eea0']` |
| graph |  | 3.909 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2026_Item_1_0008_edf8fe4b', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232']` |
| hybrid |  | 3.721 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2025_Item_1_0005_e788d800', 'NVDA_2025_Item_1_0009_7a56593b']` |

### T008: `Who supplies the high-bandwidth memory used in NVIDIA's H200 data center accelerator?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.115 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2025_Item_1_0002_b74647bb', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2025_Item_1_0001_b64486b7']` |
| graph |  | 3.887 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2025_Item_1_0008_a4407f7e', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01', 'NVDA_2024_Item_1_0007_bae70036']` |
| hybrid |  | 4.620 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2025_Item_1_0008_a4407f7e', 'MU_2024_Item_1_0003_acd8d0ff', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'NVDA_2025_Item_1_0002_b74647bb']` |

### T009: `How do export controls affect NVIDIA's data center business?`

- type: `risk_via_product`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.110 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b']` |
| graph |  | 12.516 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2025_Item_1A_0003_9003fee7', 'NVDA_2025_Item_1A_0024_d1a5b506', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2026_Item_1A_0023_804c637e', 'NVDA_2026_Item_1A_0024_b70c7a18']` |
| hybrid |  | 12.293 | n/a | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2026_Item_1A_0023_804c637e', 'NVDA_2026_Item_1A_0021_5041da01', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2025_Item_1A_0024_d1a5b506']` |

### T010: `Which materials and purity solutions does Entegris provide to semiconductor manufacturers?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.138 | 1 | 0.002 | 1.000 | 1.000 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0009_ca7ef011', 'ENTG_2025_Item_1_0008_700da46e']` |
| graph |  | 13.908 | 1 | 0.002 | 1.000 | 0.250 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0011_d7877367', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0007_4615acf5']` |
| hybrid |  | 12.493 | 1 | 0.002 | 1.000 | 0.500 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0007_4615acf5', 'ENTG_2024_Item_1_0001_61f633dc']` |

### T011: `What gross margin impact did Entegris expect from its useful-life accounting estimate change?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_7_0000_6c99ba90']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.106 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'KLAC_2025_Item_7_0009_be3ecb77', 'KLAC_2024_Item_7_0008_8308f577', 'KLAC_2023_Item_7_0011_e4c656e2', 'ENTG_2026_Item_7_0015_6af235b4']` |
| graph |  | 12.665 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2024_Item_7_0018_b0a46a7f', 'ENTG_2024_Item_7_0019_28ef5c6a', 'AMAT_2023_Item_7_0001_55c419c2']` |
| hybrid |  | 10.713 | 0 | 0.002 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'INTC_2024_Item_7_0016_d8cbdb4c', 'ENTG_2024_Item_7_0017_71caf017', 'KLAC_2025_Item_7_0009_be3ecb77', 'COHR_2024_Item_7_0008_60c01b96']` |

### T012: `What are Entegris's main business segments?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.083 | 1 | 0.002 | 1.000 | 0.500 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0014_8712752e', 'ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2024_Item_1_0019_b6aee1a3']` |
| graph |  | 23.891 | 0 | 0.002 | 0.000 | 0.000 | 1 | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2024_Item_7_0019_28ef5c6a', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2026_Item_1_0013_2fa9f11c', 'ENTG_2024_Item_1_0000_647e6e2c']` |
| hybrid |  | 7.991 | 1 | 0.002 | 1.000 | 0.500 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2025_Item_1_0008_700da46e']` |

### T013: `What is AMD's latest FY2025 revenue and gross margin?`

- type: `financial_exact_metric`
- gold_tools: `['financial']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.105 | n/a | n/a | n/a | n/a | n/a | `[]` | `['INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003', 'INTC_2024_Item_1_0003_02f7f00d', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2026_Item_7_0006_2b606b28']` |
| graph |  | 9.266 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2025_Item_7_0001_223169cf', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2024_Item_7_0006_b8de17a3', 'AMD_2025_Item_7_0003_a2d9991c', 'AMD_2026_Item_7_0006_2b606b28']` |
| hybrid |  | 3.948 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_7_0006_2b606b28', 'AMD_2024_Item_7_0006_b8de17a3', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0001_223169cf']` |

### T014: `What has AMD announced recently?`

- type: `news_recent_event`
- gold_tools: `['news']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.083 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_7_0000_6b145a7b']` |
| graph |  | 25.496 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2025_Item_7_0005_36426dd3', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2024_Item_7_0005_86aec648', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2026_Item_1_0003_ea53a6a5']` |
| hybrid |  | 5.183 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_7_0000_6b145a7b', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2025_Item_1_0003_861e4bfa']` |

### T015: `What is the relationship between KLA yield improvement tools and downstream AMD gross margin risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.097 | n/a | n/a | n/a | n/a | n/a | `[]` | `['MU_2023_Item_1A_0001_1b8ef3ed', 'AVGO_2025_Item_1A_0008_7b345bfe', 'INTC_2024_Item_7_0015_575e5365', 'AVGO_2023_Item_1A_0018_717a6eeb', 'KLAC_2023_Item_7_0011_e4c656e2']` |
| graph |  | 10.138 | n/a | n/a | n/a | n/a | n/a | `[]` | `['KLAC_2024_Item_1_0005_f2fc0653', 'KLAC_2023_Item_1_0004_177e4dcd', 'KLAC_2023_Item_1_0001_a740ee30', 'AMD_2025_Item_1A_0000_ac2e47a8', 'AMD_2025_Item_1A_0001_0fd81b24']` |
| hybrid |  | 12.190 | n/a | n/a | n/a | n/a | n/a | `[]` | `['KLAC_2023_Item_7_0002_34d825f8', 'MU_2023_Item_1A_0001_1b8ef3ed', 'AVGO_2025_Item_1A_0008_7b345bfe', 'KLAC_2024_Item_7_0002_06735542', 'INTC_2024_Item_7_0015_575e5365']` |

### T016: `qwerty zzz random semiconductor nonsense`

- type: `off_corpus`
- gold_tools: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.082 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'INTC_2025_Item_1_0001_01b4d21e', 'INTC_2025_Item_1_0002_ba6af228', 'QCOM_2024_Item_1_0009_e0fec737', 'AVGO_2024_Item_7_0008_174ffaeb']` |
| graph |  | 5.723 | n/a | n/a | n/a | n/a | n/a | `[]` | `['RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01', 'RMBS_2024_Item_7_0001_274d79f5', 'RMBS_2026_Item_7_0001_544e4d1d']` |
| hybrid |  | 5.637 | n/a | n/a | n/a | n/a | n/a | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'INTC_2025_Item_1_0001_01b4d21e', 'RMBS_2025_Item_1_0001_479b0c1e', 'INTC_2025_Item_1_0002_ba6af228']` |

### T017: `Which Taiwanese contract chipmaker fabricates AMD's processors?`

- type: `supplier_via_company`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.108 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'MU_2024_Item_1A_0025_1809ff3b', 'NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2024_Item_1_0008_20833acc', 'AMD_2024_Item_1_0013_596acde4']` |
| graph |  | 6.137 | 1 | 0.004 | 0.500 | 0.333 | 1 | `['AMD_2025_Item_1_0009_c842eea0']` | `['RMBS_2025_Item_1_0001_479b0c1e', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2024_Item_1_0007_bae70036']` |
| hybrid |  | 3.540 | 1 | 0.004 | 0.500 | 0.250 | 1 | `['AMD_2025_Item_1_0009_c842eea0']` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'AMD_2024_Item_1_0001_84491be9', 'RMBS_2025_Item_1_0001_479b0c1e', 'AMD_2025_Item_1_0009_c842eea0', 'MU_2024_Item_1A_0025_1809ff3b']` |

### T018: `Which gaming console makers partner with the Ryzen processor company?`

- type: `partner_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.094 | 1 | 0.004 | 0.500 | 1.000 | 1 | `['AMD_2026_Item_1_0004_b5e66359']` | `['AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2024_Item_1_0005_7be264c6']` |
| graph |  | 4.065 | 1 | 0.004 | 0.500 | 1.000 | 1 | `['AMD_2024_Item_1_0006_e41aed21']` | `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2024_Item_1_0005_7be264c6', 'AMD_2025_Item_1_0004_7a6fa20c']` |
| hybrid |  | 3.609 | 1 | 0.004 | 0.500 | 1.000 | 1 | `['AMD_2024_Item_1_0006_e41aed21']` | `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2024_Item_1_0005_7be264c6', 'AMD_2026_Item_1_0010_460dfa17']` |

### T019: `What revenue segments does the developer of EPYC processors disclose?`

- type: `segment_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_7_0002_d4114c99']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.086 | 1 | 0.004 | 0.500 | 1.000 | 1 | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'TXN_2025_Item_1_0002_e6c099ac', 'TXN_2024_Item_1_0002_9a773c8b', 'AMD_2026_Item_1_0003_ea53a6a5']` |
| graph |  | 3.741 | 1 | 0.004 | 0.500 | 0.500 | 1 | `['AMD_2024_Item_7_0002_d4114c99']` | `['AMD_2025_Item_7_0000_16c93d97', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2025_Item_7_0001_223169cf', 'AMD_2025_Item_7_0005_36426dd3']` |
| hybrid |  | 4.536 | 1 | 0.004 | 0.500 | 1.000 | 1 | `['AMD_2024_Item_1_0003_ee436d61']` | `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2026_Item_7_0000_6b145a7b']` |

### T020: `What export controls affect AI chip sales from the maker of Blackwell architecture?`

- type: `regulation_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['NVDA_2024_Item_1A_0020_ac4ad7b4', 'NVDA_2024_Item_1A_0022_b1d57eb9']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.106 | 0 | 0.004 | 0.000 | 0.000 | 1 | `[]` | `['AMD_2025_Item_1A_0021_16aa3aa2', 'NVDA_2025_Item_1A_0019_46eda166', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2025_Item_1A_0023_67392e5b']` |
| graph |  | 6.059 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2025_Item_1A_0003_9003fee7', 'NVDA_2025_Item_1A_0024_d1a5b506', 'NVDA_2026_Item_1A_0023_804c637e']` |
| hybrid |  | 6.756 | 1 | 0.004 | 0.500 | 0.333 | 1 | `['NVDA_2024_Item_1A_0020_ac4ad7b4']` | `['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2024_Item_1A_0020_ac4ad7b4', 'NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0019_ea1fd2e4']` |

### T021: `Which Asian contract chipmakers fabricate older-generation processors for the developer of Intel 18A?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2024_Item_1A_0001_f0f6c35c', 'INTC_2025_Item_1A_0001_65932be2']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.108 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2026_Item_7_0003_657be427', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_7_0004_e8790cb8', 'MU_2024_Item_1A_0025_1809ff3b']` |
| graph |  | 13.264 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2026_Item_1_0015_adfe2316', 'INTC_2026_Item_1_0014_5d25166d', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2025_Item_1_0004_c5a12b11', 'INTC_2025_Item_1_0009_d132a876']` |
| hybrid |  | 7.977 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_7_0003_657be427', 'INTC_2024_Item_1_0007_bfb6b7ec', 'INTC_2024_Item_7_0000_e2ea081b', 'INTC_2026_Item_1_0014_5d25166d']` |

### T022: `Which infrastructure investment firms partner with the maker of Xeon Scalable processors on fab financing?`

- type: `partner_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2025_Item_1_0011_b8759c99', 'INTC_2024_Item_1A_0007_6560bf56']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.106 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2025_Item_1_0007_1d4a96e6', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0008_57402d3f', 'INTC_2024_Item_1_0008_cca3187e']` |
| graph |  | 6.241 | 1 | 0.004 | 1.000 | 0.333 | 1 | `['INTC_2025_Item_1_0011_b8759c99', 'INTC_2024_Item_1A_0007_6560bf56']` | `['INTC_2025_Item_1A_0007_42fef1f5', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2025_Item_1_0011_b8759c99', 'INTC_2026_Item_1A_0007_7a211a24', 'INTC_2024_Item_1A_0007_6560bf56']` |
| hybrid |  | 9.127 | 0 | 0.004 | 0.000 | 0.000 | 1 | `[]` | `['INTC_2024_Item_1_0004_692d8999', 'INTC_2025_Item_1A_0007_42fef1f5', 'INTC_2025_Item_1_0007_1d4a96e6', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2024_Item_7_0005_d449d027']` |

### T023: `Which autonomous driving subsidiary does the developer of Intel Core Ultra operate?`

- type: `subsidiary_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2024_Item_1_0010_4835f632', 'INTC_2024_Item_7_0010_3742bdd2']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.093 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['NVDA_2024_Item_1_0004_12c02096', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2026_Item_1_0010_4bfc9726', 'AMD_2025_Item_1_0002_6fadf6e4']` |
| graph |  | 3.634 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0009_2d5f3afe', 'INTC_2024_Item_7_0002_7c82ed88', 'INTC_2024_Item_7_0011_0681e088', 'INTC_2025_Item_7_0011_938c6e10', 'INTC_2025_Item_7_0012_9777af13']` |
| hybrid |  | 3.158 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0002_7c82ed88', 'INTC_2024_Item_7_0009_2d5f3afe', 'NVDA_2024_Item_1_0004_12c02096', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8']` |

### T024: `Which operating system maker collaborates with the Xeon Scalable processor developer on AI PC platforms?`

- type: `partner_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2024_Item_7_0002_7c82ed88', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.109 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_7_0000_e2ea081b']` |
| graph |  | 4.737 | 1 | 0.004 | 0.500 | 0.333 | 1 | `['INTC_2024_Item_7_0002_7c82ed88']` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_7_0002_7c82ed88', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2024_Item_7_0001_d1b7bdde']` |
| hybrid |  | 4.080 | 0 | 0.004 | 0.000 | 0.000 | 1 | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2024_Item_7_0008_57402d3f', 'INTC_2026_Item_1_0004_c01224f1']` |

### T025: `In which U.S. states does the developer of the Intel 18A process operate wafer fabrication facilities?`

- type: `geo_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2024_Item_1_0014_32e0816b']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.111 | 1 | 0.004 | 0.500 | 0.500 | 1 | `['INTC_2025_Item_1_0004_c5a12b11']` | `['INTC_2025_Item_1_0010_5c90fb55', 'INTC_2025_Item_1_0004_c5a12b11', 'MU_2024_Item_1A_0025_1809ff3b', 'INTC_2026_Item_1_0005_f5ba2220', 'MU_2025_Item_1_0007_ad907262']` |
| graph |  | 7.690 | 1 | 0.004 | 0.500 | 0.500 | 1 | `['INTC_2025_Item_1_0004_c5a12b11']` | `['INTC_2026_Item_1_0014_5d25166d', 'INTC_2025_Item_1_0004_c5a12b11', 'INTC_2025_Item_1_0009_d132a876', 'INTC_2026_Item_1_0016_327ea01c', 'INTC_2024_Item_1_0004_692d8999']` |
| hybrid |  | 8.452 | 1 | 0.004 | 0.500 | 1.000 | 1 | `['INTC_2025_Item_1_0004_c5a12b11']` | `['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2025_Item_1_0010_5c90fb55', 'INTC_2026_Item_1_0014_5d25166d', 'INTC_2025_Item_1_0009_d132a876', 'MU_2024_Item_1A_0025_1809ff3b']` |

### T026: `What U.S. legislative act funds domestic semiconductor manufacturing expansion at the Intel 18A developer?`

- type: `regulator_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.099 | 1 | 0.004 | 1.000 | 1.000 | 1 | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45']` | `['INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_1A_0008_80e72e45', 'MU_2025_Item_7_0006_849b23ef', 'MU_2025_Item_1A_0029_541d266d', 'INTC_2026_Item_1_0005_f5ba2220']` |
| graph |  | 8.299 | 1 | 0.004 | 0.500 | 1.000 | 1 | `['INTC_2025_Item_1A_0008_80e72e45']` | `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2025_Item_7_0016_775a205b', 'INTC_2025_Item_7_0013_1869b003', 'INTC_2024_Item_1A_0007_6560bf56', 'MU_2023_Item_7_0005_c1d0f140']` |
| hybrid |  | 4.435 | 1 | 0.004 | 1.000 | 1.000 | 1 | `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d']` | `['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2024_Item_1A_0007_6560bf56', 'INTC_2026_Item_1A_0008_662b7d4d', 'INTC_2025_Item_7_0016_775a205b', 'MU_2025_Item_7_0006_849b23ef']` |

### T027: `What advanced driver assistance product lines come from the autonomous driving subsidiary of the Xeon Scalable developer?`

- type: `three_hop_subsidiary_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['INTC_2024_Item_7_0010_3742bdd2', 'INTC_2024_Item_7_0014_e766ac95']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.103 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'NVDA_2024_Item_1_0004_12c02096', 'NVDA_2024_Item_1_0006_f3efd950', 'NVDA_2025_Item_1_0005_85d95b7e', 'INTC_2025_Item_7_0003_878f7d25']` |
| graph |  | 5.349 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0011_0681e088', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2026_Item_7_0017_86b90f80', 'AVGO_2023_Item_1_0010_68f5ffd4', 'NVDA_2025_Item_1_0008_a4407f7e']` |
| hybrid |  | 6.302 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2024_Item_7_0005_d449d027', 'INTC_2024_Item_7_0011_0681e088', 'NVDA_2024_Item_1_0004_12c02096', 'INTC_2026_Item_7_0017_86b90f80', 'NVDA_2024_Item_1_0006_f3efd950']` |

### T028: `What consumer storage and DRAM brand is sold by the U.S. supplier of HBM3E memory?`

- type: `product_via_company`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['MU_2025_Item_1_0000_6418b9d4', 'MU_2024_Item_1_0000_82417507']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.117 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0002_74d97a0e', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2024_Item_1_0001_90ffbd18']` |
| graph |  | 3.879 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['MU_2023_Item_1_0001_70be5bda', 'MU_2025_Item_1_0001_b64486b7', 'MU_2023_Item_1_0005_91e3e192', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2025_Item_7_0000_aa4240e3']` |
| hybrid |  | 3.457 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774', 'MU_2023_Item_1_0003_fb3cb967', 'MU_2023_Item_1_0002_74d97a0e', 'MU_2023_Item_1_0001_70be5bda']` |

### T029: `Why has HBM become critical for modern AI training and inference workloads?`

- type: `topical_memory`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_chunks: `['MU_2025_Item_1_0001_b64486b7', 'MU_2024_Item_1_0003_acd8d0ff']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.108 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'QCOM_2025_Item_1_0002_29556203', 'QCOM_2024_Item_1_0002_f2bb0f8a', 'NVDA_2026_Item_1_0005_9725a5a2', 'NVDA_2024_Item_1_0005_7f985cdb']` |
| graph |  | 4.050 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['RMBS_2026_Item_1_0001_bc3d8a01', 'RMBS_2026_Item_7_0001_544e4d1d', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']` |
| hybrid |  | 10.589 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2025_Item_1A_0012_fd8f7cd9', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'QCOM_2025_Item_1_0002_29556203', 'NVDA_2026_Item_1_0007_bf6a51b6']` |

### T030: `Which cloud hyperscalers partner with the EPYC processor maker for server CPU deployments in their data centers?`

- type: `customer_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359']`

| Tool | Error | Latency | Hit@k | Random Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.127 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_1_0010_842113d9', 'INTC_2024_Item_7_0005_d449d027']` |
| graph |  | 16.222 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2025_Item_7_0005_36426dd3', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232', 'AMD_2024_Item_7_0005_86aec648']` |
| hybrid |  | 7.795 | 0 | 0.004 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2026_Item_1_0009_ac9cc232', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2024_Item_1_0003_ee436d61']` |
