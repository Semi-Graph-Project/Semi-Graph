# Financial Agent: NumPy Vector vs SQL

Both configurations use the same Agent graph, Planner, tool name, prompts,
LLM, benchmark, and financial facts. Only the backend behind the `financial`
tool is changed.

## Overall result

| Metric | Agent + Vector | Agent + SQL |
|---|---:|---:|
| Tool selection accuracy | 98.33% | 100.00% |
| Retrieval exact rate | 93.75% | 100.00% |
| Retrieval micro recall | 95.24% | 100.00% |
| Final-answer accuracy | 93.75% | 100.00% |
| Abstention accuracy | 100.00% | 91.67% |
| Citation validity | 100.00% | 100.00% |
| Overall pass rate | 95.00% | 98.33% |

## Agent + Vector by category

| Category | N | Retrieval Exact | Final Answer | Abstention | Overall Pass |
|---|---:|---:|---:|---:|---:|
| derived_metric | 12 | 100.00% | 100.00% | N/A | 100.00% |
| multi_company_comparison | 12 | 75.00% | 75.00% | N/A | 75.00% |
| multi_year_trend | 12 | 100.00% | 100.00% | N/A | 100.00% |
| single_company_lookup | 12 | 100.00% | 100.00% | N/A | 100.00% |
| unsupported_abstention | 12 | N/A | N/A | 100.00% | 100.00% |

## Runtime

- Agent + Vector median latency: 11.039 seconds
- Agent + SQL median latency: 15.053 seconds
- Vector top-k: 5
- Vector corpus: `benchmark/datasets/financial_vector_facts.jsonl`
- SQL reference: `benchmark/results/financial_agent_e2e/20260718_180149/summary.json`
