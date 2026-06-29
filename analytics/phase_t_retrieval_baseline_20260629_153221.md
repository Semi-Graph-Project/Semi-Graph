# Phase T Retrieval Baseline

Generated: 2026-06-29T15:36:47
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `graph, hybrid`
top_k: `5`
oracle_k: `10`
dry_run: `False`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|
| graph | 7 | 0 | 0.286 | 0.257 | 0.179 | 0.571 |
| hybrid | 7 | 0 | 0.571 | 0.386 | 0.405 | 0.571 |

## By Type

| Type | graph Hit | graph Recall | hybrid Hit | hybrid Recall |
|---|---:|---:|---:|---:|
| competitor_product | 0.000 | 0.000 | 0.000 | 0.000 |
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 |
| supplier_via_product | 0.500 | 0.400 | 1.000 | 0.350 |
| vector_friendly | 0.333 | 0.333 | 0.667 | 0.667 |

## Per Query

### T001: `How exposed is AMD to TSMC supply risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 40.091 | 0 | 0.000 | 0.000 | 0 | `[]` | `['QCOM_2024_Item_1A_0031_686b8f2f', 'ENTG_2026_Item_1A_0005_d2f79cf3', 'ENTG_2025_Item_1A_0005_1b7cb400', 'LRCX_2023_Item_1A_0006_e42302c0', 'LRCX_2023_Item_1_0005_de991ae1']` |
| hybrid |  | 10.683 | 0 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2024_Item_1A_0002_0a71f57a', 'QCOM_2024_Item_1A_0031_686b8f2f', 'ENTG_2026_Item_1A_0005_d2f79cf3', 'INTC_2026_Item_1A_0006_820d3c64', 'ENTG_2025_Item_1A_0005_1b7cb400']` |

### T002: `Which foundry partner manufactures the Hopper architecture chips?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 4.302 | 1 | 0.800 | 1.000 | 1 | `['NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f']` | `['NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f', 'NVDA_2026_Item_1_0007_bf6a51b6']` |
| hybrid |  | 2.998 | 1 | 0.200 | 1.000 | 1 | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_7_0017_86b90f80', 'INTC_2026_Item_1_0013_cb483288', 'AVGO_2024_Item_1_0012_88739b41', 'INTC_2026_Item_1_0006_d0f653da']` |

### T003: `Who produces the dense memory chips that power modern AI training accelerators?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['MU_2023_Item_1A_0003_92be33e3', 'MU_2025_Item_1A_0004_836bee10', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 3.644 | 0 | 0.000 | 0.000 | 1 | `[]` | `['RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2024_Item_7_0001_274d79f5', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01', 'RMBS_2026_Item_7_0001_544e4d1d']` |
| hybrid |  | 6.245 | 1 | 0.500 | 1.000 | 1 | `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']` | `['NVDA_2024_Item_1_0007_bae70036', 'RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'NVDA_2025_Item_1_0008_a4407f7e', 'INTC_2025_Item_7_0003_878f7d25']` |

### T004: `What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1_0003_ea53a6a5']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 10.830 | 0 | 0.000 | 0.000 | 1 | `[]` | `['AMD_2026_Item_1_0007_f252541b', 'AMD_2025_Item_1_0006_551768e4', 'AMD_2024_Item_1_0009_01379c5a', 'AMD_2025_Item_1_0007_0ffd6ad4', 'AMD_2026_Item_1_0008_302d3abf']` |
| hybrid |  | 6.260 | 0 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2026_Item_1_0007_f252541b', 'INTC_2025_Item_1_0003_707a268b', 'AMD_2024_Item_1_0009_01379c5a', 'INTC_2024_Item_1_0005_bcb431a8', 'AMD_2025_Item_1_0006_551768e4']` |

### T005: `What political risks affect the home country of the leading pure-play semiconductor foundry?`

- type: `geo_via_supplier`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 3.550 | n/a | n/a | n/a | n/a | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'ENTG_2024_Item_1A_0004_999d6dff', 'AVGO_2025_Item_1A_0003_7aabc04f', 'AMKR_2024_Item_1A_0009_d14b856d', 'QCOM_2024_Item_1A_0031_686b8f2f']` |
| hybrid |  | 3.272 | n/a | n/a | n/a | n/a | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'QCOM_2023_Item_1A_0031_545bf96a', 'ENTG_2024_Item_1A_0004_999d6dff', 'ENTG_2026_Item_1_0004_6f32215b', 'AVGO_2025_Item_1A_0003_7aabc04f']` |

### T006: `Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?`

- type: `supplier_via_company`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 5.867 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'NVDA_2025_Item_1_0008_a4407f7e', 'INTC_2026_Item_1_0008_c74f560f', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e']` |
| hybrid |  | 4.525 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'MU_2024_Item_1A_0025_1809ff3b', 'RMBS_2025_Item_1_0001_479b0c1e', 'AMKR_2026_Item_1_0003_8dee603e']` |

### T007: `What graphics product line does AMD offer to compete with NVIDIA's RTX series?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 3.998 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'AMD_2024_Item_1_0011_49024c2d']` |
| hybrid |  | 6.822 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0005_e788d800', 'RMBS_2024_Item_1_0001_1bbcc1ae']` |

### T008: `Who supplies the high-bandwidth memory used in NVIDIA's H200 data center accelerator?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 3.989 | n/a | n/a | n/a | n/a | `[]` | `['RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01', 'RMBS_2024_Item_7_0001_274d79f5', 'RMBS_2026_Item_7_0001_544e4d1d']` |
| hybrid |  | 3.395 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'MU_2024_Item_1_0003_acd8d0ff', 'RMBS_2025_Item_1_0001_479b0c1e', 'NVDA_2025_Item_1_0002_b74647bb']` |

### T009: `How do export controls affect NVIDIA's data center business?`

- type: `risk_via_product`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 6.660 | n/a | n/a | n/a | n/a | `[]` | `['AMAT_2025_Item_1A_0017_af7d9be8', 'ENTG_2026_Item_1A_0005_d2f79cf3', 'NVDA_2025_Item_1A_0003_9003fee7', 'NVDA_2025_Item_1A_0024_d1a5b506', 'NVDA_2026_Item_1A_0020_331dc537']` |
| hybrid |  | 4.186 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2026_Item_1A_0023_804c637e', 'KLAC_2025_Item_1A_0004_8b3ac9dd', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9']` |

### T010: `Which materials and purity solutions does Entegris provide to semiconductor manufacturers?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 9.029 | 1 | 1.000 | 0.250 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0011_d7877367', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0007_4615acf5']` |
| hybrid |  | 8.496 | 1 | 1.000 | 0.500 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0007_4615acf5']` |

### T011: `What gross margin impact did Entegris expect from its useful-life accounting estimate change?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_7_0000_6c99ba90']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 12.927 | 0 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2024_Item_7_0018_b0a46a7f', 'ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2025_Item_7_0014_7ec44ac1', 'ENTG_2024_Item_7_0019_28ef5c6a']` |
| hybrid |  | 21.710 | 0 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'INTC_2024_Item_7_0016_d8cbdb4c', 'ENTG_2024_Item_7_0017_71caf017', 'COHR_2024_Item_7_0008_60c01b96', 'KLAC_2025_Item_7_0009_be3ecb77']` |

### T012: `What are Entegris's main business segments?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 16.746 | 0 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2024_Item_7_0019_28ef5c6a', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2026_Item_1_0013_2fa9f11c', 'ENTG_2024_Item_7_0018_b0a46a7f']` |
| hybrid |  | 14.055 | 1 | 1.000 | 0.333 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2025_Item_1_0008_700da46e']` |

### T013: `What is AMD's latest FY2025 revenue and gross margin?`

- type: `financial_exact_metric`
- gold_tools: `['financial']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 2.810 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2024_Item_7_0002_d4114c99', 'AMD_2025_Item_7_0001_223169cf', 'AMD_2024_Item_7_0006_b8de17a3', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2025_Item_7_0005_36426dd3']` |
| hybrid |  | 3.728 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_7_0006_2b606b28', 'AMD_2024_Item_7_0006_b8de17a3', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2026_Item_7_0000_6b145a7b', 'INTC_2024_Item_7_0015_575e5365']` |

### T014: `What has AMD announced recently?`

- type: `news_recent_event`
- gold_tools: `['news']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 6.070 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2025_Item_7_0005_36426dd3', 'AMD_2024_Item_7_0005_86aec648', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2026_Item_7_0000_6b145a7b', 'AMD_2025_Item_7_0001_223169cf']` |
| hybrid |  | 4.447 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2024_Item_7_0005_86aec648']` |

### T015: `What is the relationship between KLA yield improvement tools and downstream AMD gross margin risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 9.914 | n/a | n/a | n/a | n/a | `[]` | `['KLAC_2024_Item_1_0005_f2fc0653', 'AMD_2025_Item_1A_0000_ac2e47a8', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2024_Item_7_0006_b8de17a3']` |
| hybrid |  | 13.365 | n/a | n/a | n/a | n/a | `[]` | `['KLAC_2024_Item_1_0005_f2fc0653', 'MU_2023_Item_1A_0001_1b8ef3ed', 'AMD_2024_Item_7_0002_d4114c99', 'AVGO_2025_Item_1A_0008_7b345bfe', 'AMD_2024_Item_7_0006_b8de17a3']` |

### T016: `qwerty zzz random semiconductor nonsense`

- type: `off_corpus`
- gold_tools: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 6.602 | n/a | n/a | n/a | n/a | `[]` | `['AVGO_2024_Item_1_0012_88739b41', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2024_Item_7_0001_274d79f5', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01']` |
| hybrid |  | 4.026 | n/a | n/a | n/a | n/a | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'INTC_2025_Item_1_0001_01b4d21e', 'RMBS_2025_Item_1_0001_479b0c1e', 'INTC_2025_Item_1_0002_ba6af228']` |
