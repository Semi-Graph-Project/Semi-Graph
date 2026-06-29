# Phase T Retrieval Baseline

Generated: 2026-06-29T13:22:38
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Tools: `vector, graph, hybrid`
top_k: `5`
oracle_k: `10`
dry_run: `True`

## Overall

| Tool | Scored Queries | Errors | Hit@k | Recall@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|
| vector | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| graph | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| hybrid | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |

## Per Query

### T001: `How exposed is AMD to TSMC supply risk?`

- type: `graph_multihop`
- gold_tools: `['graph', 'hybrid']`
- gold_chunks: `['AMD_2026_Item_1A_0008_e84e4130']`

| Tool | Error | Latency | Hit@k | Recall@k | MRR@k | Oracle Hit | Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | `[]` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | `[]` | `[]` |
