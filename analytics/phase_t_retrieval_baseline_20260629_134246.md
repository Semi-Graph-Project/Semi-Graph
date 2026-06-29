# Phase T Retrieval Baseline

Generated: 2026-06-29T13:42:58
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `vector`
top_k: `3`
oracle_k: `3`
dry_run: `False`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|
| vector | 1 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |

## By Type

| Type | vector Hit | vector Recall |
|---|---:|---:|
| graph_multihop | 0.000 | 0.000 |

## Per Query

### T001: `How exposed is AMD to TSMC supply risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 12.817 | 0 | 0.000 | 0.000 | 0 | `[]` | `['AMD_2024_Item_1A_0002_0a71f57a', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2024_Item_1A_0000_1a5c79ae']` |
