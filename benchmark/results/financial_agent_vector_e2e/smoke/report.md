# Financial Agent: NumPy Vector vs SQL

Both configurations use the same Agent graph, Planner, tool name, prompts,
LLM, benchmark, and financial facts. Only the backend behind the `financial`
tool is changed.

## Overall result

| Metric | Agent + Vector | Agent + SQL |
|---|---:|---:|
| Tool selection accuracy | 100.00% | 100.00% |
| Retrieval exact rate | 100.00% | 100.00% |
| Retrieval micro recall | 100.00% | 100.00% |
| Final-answer accuracy | 100.00% | 100.00% |
| Abstention accuracy | N/A | N/A |
| Citation validity | 100.00% | 100.00% |
| Overall pass rate | 100.00% | 100.00% |

## Agent + Vector by category

| Category | N | Retrieval Exact | Final Answer | Abstention | Overall Pass |
|---|---:|---:|---:|---:|---:|
| single_company_lookup | 1 | 100.00% | 100.00% | N/A | 100.00% |

## Runtime

- Agent + Vector median latency: 16.343 seconds
- Agent + SQL median latency: 17.824 seconds
- Vector top-k: 5
- Vector corpus: `benchmark/datasets/financial_vector_facts.jsonl`
- SQL reference: `benchmark/results/financial_agent_e2e/smoke_1/summary.json`
