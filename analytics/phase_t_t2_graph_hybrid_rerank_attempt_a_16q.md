# Phase T Retrieval Baseline

Generated: 2026-06-29T15:32:05
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `graph, hybrid`
top_k: `5`
oracle_k: `10`
dry_run: `False`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|
| graph | 7 | 0 | 0.286 | 0.171 | 0.119 | 0.429 |
| hybrid | 7 | 0 | 0.286 | 0.171 | 0.286 | 0.429 |

## By Type

| Type | graph Hit | graph Recall | hybrid Hit | hybrid Recall |
|---|---:|---:|---:|---:|
| competitor_product | 0.000 | 0.000 | 0.000 | 0.000 |
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 |
| supplier_via_product | 0.500 | 0.100 | 0.500 | 0.100 |
| vector_friendly | 0.333 | 0.333 | 0.333 | 0.333 |

## Per Query

### T001: `How exposed is AMD to TSMC supply risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 28.075 | 0 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2025_Item_1A_0000_ac2e47a8', 'AMD_2025_Item_1A_0001_0fd81b24', 'AMD_2025_Item_1A_0011_10eec6d1', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` |
| hybrid |  | 2.299 | 0 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2024_Item_1A_0002_0a71f57a', 'AMD_2025_Item_1A_0000_ac2e47a8', 'AMD_2025_Item_1A_0001_0fd81b24', 'INTC_2026_Item_1A_0006_820d3c64', 'AMD_2025_Item_1A_0011_10eec6d1']` |

### T002: `Which foundry partner manufactures the Hopper architecture chips?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.647 | 1 | 0.200 | 0.500 | 1 | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_7_0017_86b90f80', 'INTC_2026_Item_1_0008_c74f560f', 'AVGO_2024_Item_1_0012_88739b41', 'RMBS_2026_Item_7_0001_544e4d1d', 'NVDA_2025_Item_7_0003_d53d3047']` |
| hybrid |  | 1.686 | 1 | 0.200 | 1.000 | 1 | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_7_0017_86b90f80', 'INTC_2026_Item_1_0013_cb483288', 'AVGO_2024_Item_1_0012_88739b41', 'INTC_2026_Item_1_0006_d0f653da']` |

### T003: `Who produces the dense memory chips that power modern AI training accelerators?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['MU_2023_Item_1A_0003_92be33e3', 'MU_2025_Item_1A_0004_836bee10', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.564 | 0 | 0.000 | 0.000 | 1 | `[]` | `['AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f', 'NVDA_2024_Item_1_0008_20833acc']` |
| hybrid |  | 1.908 | 0 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2025_Item_7_0003_878f7d25', 'AMD_2024_Item_1_0011_49024c2d', 'RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'AMD_2025_Item_1_0009_c842eea0']` |

### T004: `What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1_0003_ea53a6a5']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.520 | 0 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2025_Item_1_0006_551768e4', 'AMD_2026_Item_1_0007_f252541b', 'AMD_2024_Item_1_0009_01379c5a', 'AMD_2025_Item_1_0007_0ffd6ad4', 'AMD_2026_Item_1_0008_302d3abf']` |
| hybrid |  | 1.584 | 0 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2025_Item_1_0006_551768e4', 'INTC_2025_Item_1_0003_707a268b', 'AMD_2026_Item_1_0007_f252541b', 'INTC_2024_Item_1_0005_bcb431a8', 'AMD_2024_Item_1_0009_01379c5a']` |

### T005: `What political risks affect the home country of the leading pure-play semiconductor foundry?`

- type: `geo_via_supplier`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.488 | n/a | n/a | n/a | n/a | `[]` | `['ENTG_2026_Item_1A_0005_d2f79cf3', 'INTC_2024_Item_1A_0009_dd11a01d', 'AVGO_2024_Item_1A_0002_60697233', 'RMBS_2024_Item_1A_0009_16baaed9', 'RMBS_2026_Item_1A_0011_ca481e8f']` |
| hybrid |  | 1.570 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_1A_0032_c870df0c', 'ENTG_2026_Item_1A_0005_d2f79cf3', 'QCOM_2023_Item_1A_0031_545bf96a', 'ENTG_2026_Item_1_0004_6f32215b', 'INTC_2024_Item_1A_0009_dd11a01d']` |

### T006: `Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?`

- type: `supplier_via_company`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.600 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01', 'NVDA_2025_Item_1_0008_a4407f7e']` |
| hybrid |  | 1.802 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1A_0025_1809ff3b', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'AMKR_2026_Item_1_0003_8dee603e', 'RMBS_2025_Item_1_0001_479b0c1e']` |

### T007: `What graphics product line does AMD offer to compete with NVIDIA's RTX series?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.477 | n/a | n/a | n/a | n/a | `[]` | `['RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']` |
| hybrid |  | 1.591 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0005_e788d800', 'RMBS_2024_Item_1_0001_1bbcc1ae']` |

### T008: `Who supplies the high-bandwidth memory used in NVIDIA's H200 data center accelerator?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.521 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_7_0001_485abbd3', 'NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2026_Item_1_0008_edf8fe4b', 'NVDA_2025_Item_1_0010_ad20d7da', 'NVDA_2026_Item_1_0009_8c403127']` |
| hybrid |  | 1.667 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2026_Item_7_0001_485abbd3', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2025_Item_1_0002_b74647bb']` |

### T009: `How do export controls affect NVIDIA's data center business?`

- type: `risk_via_product`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.707 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'AMAT_2025_Item_1A_0017_af7d9be8', 'ENTG_2026_Item_1A_0005_d2f79cf3', 'NVDA_2025_Item_1A_0024_d1a5b506']` |
| hybrid |  | 1.614 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2026_Item_1A_0023_804c637e', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'AMAT_2025_Item_1A_0017_af7d9be8']` |

### T010: `Which materials and purity solutions does Entegris provide to semiconductor manufacturers?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.570 | 1 | 1.000 | 0.333 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0008_700da46e', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0007_4615acf5', 'ENTG_2026_Item_1_0011_d7877367']` |
| hybrid |  | 1.627 | 1 | 1.000 | 1.000 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2025_Item_1_0008_700da46e', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0007_4615acf5']` |

### T011: `What gross margin impact did Entegris expect from its useful-life accounting estimate change?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_7_0000_6c99ba90']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.609 | 0 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2024_Item_7_0018_b0a46a7f', 'ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2025_Item_7_0014_7ec44ac1', 'ENTG_2024_Item_7_0019_28ef5c6a']` |
| hybrid |  | 1.642 | 0 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'ENTG_2024_Item_7_0017_71caf017', 'ENTG_2024_Item_7_0018_b0a46a7f', 'KLAC_2025_Item_7_0009_be3ecb77', 'KLAC_2024_Item_7_0008_8308f577']` |

### T012: `What are Entegris's main business segments?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.728 | 0 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0017_71caf017', 'ENTG_2026_Item_1_0011_d7877367', 'ENTG_2024_Item_1_0018_1e35f935', 'ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2024_Item_1_0017_6dea4db1']` |
| hybrid |  | 1.687 | 0 | 0.000 | 0.000 | 1 | `[]` | `['ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2024_Item_1_0017_6dea4db1', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2024_Item_7_0017_71caf017', 'ENTG_2025_Item_1_0000_7efdfd60']` |

### T013: `What is AMD's latest FY2025 revenue and gross margin?`

- type: `financial_exact_metric`
- gold_tools: `['financial']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.552 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2024_Item_7_0002_d4114c99', 'AMD_2025_Item_7_0001_223169cf', 'AMD_2026_Item_7_0006_2b606b28', 'AMD_2024_Item_7_0006_b8de17a3', 'INTC_2024_Item_7_0002_7c82ed88']` |
| hybrid |  | 1.565 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2026_Item_7_0006_2b606b28', 'AMD_2024_Item_7_0002_d4114c99', 'AMD_2024_Item_7_0006_b8de17a3', 'AMD_2026_Item_7_0000_6b145a7b', 'INTC_2024_Item_7_0015_575e5365']` |

### T014: `What has AMD announced recently?`

- type: `news_recent_event`
- gold_tools: `['news']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.441 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2025_Item_7_0005_36426dd3', 'AMD_2024_Item_7_0005_86aec648', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2026_Item_1_0003_ea53a6a5', 'AMD_2024_Item_1_0001_84491be9']` |
| hybrid |  | 1.653 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2024_Item_7_0005_86aec648']` |

### T015: `What is the relationship between KLA yield improvement tools and downstream AMD gross margin risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.466 | n/a | n/a | n/a | n/a | `[]` | `['MU_2025_Item_1A_0001_8d660135', 'KLAC_2023_Item_7_0009_9b5b651f', 'KLAC_2024_Item_7_0006_313cb934', 'KLAC_2023_Item_7_0002_34d825f8', 'KLAC_2024_Item_7_0002_06735542']` |
| hybrid |  | 1.606 | n/a | n/a | n/a | n/a | `[]` | `['MU_2023_Item_1A_0001_1b8ef3ed', 'MU_2025_Item_1A_0001_8d660135', 'AVGO_2025_Item_1A_0008_7b345bfe', 'KLAC_2023_Item_7_0009_9b5b651f', 'INTC_2024_Item_7_0015_575e5365']` |

### T016: `qwerty zzz random semiconductor nonsense`

- type: `off_corpus`
- gold_tools: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph |  | 1.444 | n/a | n/a | n/a | n/a | `[]` | `['RMBS_2024_Item_1_0001_1bbcc1ae', 'RMBS_2025_Item_1_0001_479b0c1e', 'RMBS_2026_Item_1_0001_bc3d8a01', 'AMD_2026_Item_1_0006_9061ffe7', 'RMBS_2024_Item_7_0001_274d79f5']` |
| hybrid |  | 1.491 | n/a | n/a | n/a | n/a | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'RMBS_2024_Item_1_0001_1bbcc1ae', 'INTC_2025_Item_1_0001_01b4d21e', 'RMBS_2025_Item_1_0001_479b0c1e', 'INTC_2025_Item_1_0002_ba6af228']` |
