# Phase T Retrieval Baseline

Generated: 2026-06-29T13:59:15
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `vector`
top_k: `5`
oracle_k: `10`
dry_run: `False`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|
| vector | 7 | 0 | 0.429 | 0.314 | 0.357 | 0.571 |

## By Type

| Type | vector Hit | vector Recall |
|---|---:|---:|
| competitor_product | 0.000 | 0.000 |
| graph_multihop | 0.000 | 0.000 |
| supplier_via_product | 0.500 | 0.100 |
| vector_friendly | 0.667 | 0.667 |

## Per Query

### T001: `How exposed is AMD to TSMC supply risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 12.700 | 0 | 0.000 | 0.000 | 1 | `[]` | `['AMD_2024_Item_1A_0002_0a71f57a', 'INTC_2026_Item_1A_0006_820d3c64', 'MU_2024_Item_1A_0001_703555bd', 'MU_2025_Item_1A_0001_8d660135', 'INTC_2024_Item_1A_0000_1a5c79ae']` |

### T002: `Which foundry partner manufactures the Hopper architecture chips?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.360 | 1 | 0.200 | 1.000 | 1 | `['INTC_2026_Item_1_0008_c74f560f']` | `['INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0013_cb483288', 'INTC_2026_Item_1_0006_d0f653da', 'INTC_2024_Item_1_0014_32e0816b', 'AMD_2024_Item_1_0012_9561038a']` |

### T003: `Who produces the dense memory chips that power modern AI training accelerators?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['MU_2023_Item_1A_0003_92be33e3', 'MU_2025_Item_1A_0004_836bee10', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.135 | 0 | 0.000 | 0.000 | 0 | `[]` | `['RMBS_2025_Item_1_0000_b00f6cec', 'AMD_2025_Item_1_0002_6fadf6e4', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2026_Item_1_0005_9725a5a2', 'INTC_2026_Item_1_0004_c01224f1']` |

### T004: `What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1_0003_ea53a6a5']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.115 | 0 | 0.000 | 0.000 | 0 | `[]` | `['INTC_2025_Item_1_0003_707a268b', 'INTC_2024_Item_1_0005_bcb431a8', 'INTC_2026_Item_1_0004_c01224f1', 'INTC_2025_Item_7_0003_878f7d25', 'AMD_2026_Item_1_0004_b5e66359']` |

### T005: `What political risks affect the home country of the leading pure-play semiconductor foundry?`

- type: `geo_via_supplier`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.102 | n/a | n/a | n/a | n/a | `[]` | `['QCOM_2023_Item_1A_0031_545bf96a', 'ENTG_2026_Item_1_0004_6f32215b', 'MU_2023_Item_1A_0003_92be33e3', 'ENTG_2025_Item_1_0004_66634bce', 'AMD_2025_Item_1A_0032_0a1cf7f3']` |

### T006: `Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?`

- type: `supplier_via_company`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.102 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1_0007_bf6a51b6', 'MU_2024_Item_1A_0025_1809ff3b', 'AMKR_2026_Item_1_0003_8dee603e', 'NVDA_2025_Item_1_0002_b74647bb', 'ENTG_2024_Item_1_0007_38140456']` |

### T007: `What graphics product line does AMD offer to compete with NVIDIA's RTX series?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.128 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2025_Item_1_0005_e788d800', 'AMD_2026_Item_1_0005_808c1965', 'AMD_2026_Item_1_0010_460dfa17', 'AMD_2025_Item_1_0007_0ffd6ad4', 'AMD_2025_Item_1_0009_c842eea0']` |

### T008: `Who supplies the high-bandwidth memory used in NVIDIA's H200 data center accelerator?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.126 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2024_Item_1_0002_2ddf2e3b', 'MU_2024_Item_1_0003_acd8d0ff', 'NVDA_2025_Item_1_0002_b74647bb', 'MU_2024_Item_1_0001_90ffbd18', 'MU_2025_Item_1_0001_b64486b7']` |

### T009: `How do export controls affect NVIDIA's data center business?`

- type: `risk_via_product`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.174 | n/a | n/a | n/a | n/a | `[]` | `['NVDA_2026_Item_1A_0024_b70c7a18', 'NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b']` |

### T010: `Which materials and purity solutions does Entegris provide to semiconductor manufacturers?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.172 | 1 | 1.000 | 1.000 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2024_Item_1_0000_647e6e2c', 'ENTG_2026_Item_1_0009_ca7ef011', 'ENTG_2025_Item_1_0008_700da46e']` |

### T011: `What gross margin impact did Entegris expect from its useful-life accounting estimate change?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_7_0000_6c99ba90']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.138 | 0 | 0.000 | 0.000 | 0 | `[]` | `['ENTG_2024_Item_7_0005_b82d6e3c', 'KLAC_2025_Item_7_0009_be3ecb77', 'KLAC_2024_Item_7_0008_8308f577', 'KLAC_2023_Item_7_0011_e4c656e2', 'ENTG_2026_Item_7_0015_6af235b4']` |

### T012: `What are Entegris's main business segments?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.132 | 1 | 1.000 | 0.500 | 1 | `['ENTG_2026_Item_1_0000_a9f06bac']` | `['ENTG_2025_Item_1_0000_7efdfd60', 'ENTG_2026_Item_1_0000_a9f06bac', 'ENTG_2026_Item_1_0014_8712752e', 'ENTG_2025_Item_1_0017_ca134e0e', 'ENTG_2024_Item_1_0019_b6aee1a3']` |

### T013: `What is AMD's latest FY2025 revenue and gross margin?`

- type: `financial_exact_metric`
- gold_tools: `['financial']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.125 | n/a | n/a | n/a | n/a | `[]` | `['INTC_2024_Item_7_0015_575e5365', 'INTC_2025_Item_7_0013_1869b003', 'INTC_2024_Item_1_0003_02f7f00d', 'AMD_2024_Item_1_0001_84491be9', 'AMD_2026_Item_7_0006_2b606b28']` |

### T014: `What has AMD announced recently?`

- type: `news_recent_event`
- gold_tools: `['news']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.100 | n/a | n/a | n/a | n/a | `[]` | `['AMD_2024_Item_1_0001_84491be9', 'AMD_2024_Item_7_0001_2f628a3f', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_7_0000_6b145a7b']` |

### T015: `What is the relationship between KLA yield improvement tools and downstream AMD gross margin risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.174 | n/a | n/a | n/a | n/a | `[]` | `['MU_2023_Item_1A_0001_1b8ef3ed', 'AVGO_2025_Item_1A_0008_7b345bfe', 'INTC_2024_Item_7_0015_575e5365', 'AVGO_2023_Item_1A_0018_717a6eeb', 'KLAC_2023_Item_7_0011_e4c656e2']` |

### T016: `qwerty zzz random semiconductor nonsense`

- type: `off_corpus`
- gold_tools: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.151 | n/a | n/a | n/a | n/a | `[]` | `['AMKR_2025_Item_1A_0003_a68b7182', 'INTC_2025_Item_1_0001_01b4d21e', 'INTC_2025_Item_1_0002_ba6af228', 'QCOM_2024_Item_1_0009_e0fec737', 'AVGO_2024_Item_7_0008_174ffaeb']` |
