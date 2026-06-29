# Phase T Retrieval Baseline

Generated: 2026-06-29T15:27:13
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `graph, hybrid`
top_k: `5`
oracle_k: `10`
dry_run: `False`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|
| graph | 7 | 16 | 0.000 | 0.000 | 0.000 | 0.000 |
| hybrid | 7 | 16 | 0.000 | 0.000 | 0.000 | 0.000 |

## By Type

| Type | graph Hit | graph Recall | hybrid Hit | hybrid Recall |
|---|---:|---:|---:|---:|
| competitor_product | 0.000 | 0.000 | 0.000 | 0.000 |
| graph_multihop | 0.000 | 0.000 | 0.000 | 0.000 |
| supplier_via_product | 0.000 | 0.000 | 0.000 | 0.000 |
| vector_friendly | 0.000 | 0.000 | 0.000 | 0.000 |

## Per Query

### T001: `How exposed is AMD to TSMC supply risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 9.795 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.107 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |

### T002: `Which foundry partner manufactures the Hopper architecture chips?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.112 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.103 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |

### T003: `Who produces the dense memory chips that power modern AI training accelerators?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['MU_2023_Item_1A_0003_92be33e3', 'MU_2025_Item_1A_0004_836bee10', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.104 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.085 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |

### T004: `What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1_0003_ea53a6a5']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.100 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.105 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |

### T005: `What political risks affect the home country of the leading pure-play semiconductor foundry?`

- type: `geo_via_supplier`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.118 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.110 | n/a | n/a | n/a | n/a | `[]` | `[]` |

### T006: `Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?`

- type: `supplier_via_company`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.101 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.097 | n/a | n/a | n/a | n/a | `[]` | `[]` |

### T007: `What graphics product line does AMD offer to compete with NVIDIA's RTX series?`

- type: `competitor_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.099 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.089 | n/a | n/a | n/a | n/a | `[]` | `[]` |

### T008: `Who supplies the high-bandwidth memory used in NVIDIA's H200 data center accelerator?`

- type: `supplier_via_product`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.091 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.088 | n/a | n/a | n/a | n/a | `[]` | `[]` |

### T009: `How do export controls affect NVIDIA's data center business?`

- type: `risk_via_product`
- gold_tools: `['graph', 'hybrid', 'vector']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.088 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.080 | n/a | n/a | n/a | n/a | `[]` | `[]` |

### T010: `Which materials and purity solutions does Entegris provide to semiconductor manufacturers?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.089 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.076 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |

### T011: `What gross margin impact did Entegris expect from its useful-life accounting estimate change?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_7_0000_6c99ba90']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.083 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.074 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |

### T012: `What are Entegris's main business segments?`

- type: `vector_friendly`
- gold_tools: `['vector']`
- gold_chunks: `['ENTG_2026_Item_1_0000_a9f06bac']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.069 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.070 | 0 | 0.000 | 0.000 | 0 | `[]` | `[]` |

### T013: `What is AMD's latest FY2025 revenue and gross margin?`

- type: `financial_exact_metric`
- gold_tools: `['financial']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.073 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.071 | n/a | n/a | n/a | n/a | `[]` | `[]` |

### T014: `What has AMD announced recently?`

- type: `news_recent_event`
- gold_tools: `['news']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.062 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.061 | n/a | n/a | n/a | n/a | `[]` | `[]` |

### T015: `What is the relationship between KLA yield improvement tools and downstream AMD gross margin risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.075 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.073 | n/a | n/a | n/a | n/a | `[]` | `[]` |

### T016: `qwerty zzz random semiconductor nonsense`

- type: `off_corpus`
- gold_tools: `[]`
- gold_chunks: `[]`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| graph | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.067 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| hybrid | ServiceUnavailable: Couldn't connect to localhost:7687 (resolved to ('127.0.0.1:7687',)):
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [Errno 1] Operation not permitted) | 0.065 | n/a | n/a | n/a | n/a | `[]` | `[]` |
