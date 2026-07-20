# FinReflectKG Agent Evaluation

| Mode | Queries | Errors | Hit@5 | Recall@5 | GroupRecall@5 | Answerable@5 | Hit@All | Recall@All | Synthesis GroupRecall | Avg Calls | Avg Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| agent_vector | 2 | 0 | 0.500 | 0.167 | 0.167 | 0.000 | 1.000 | 0.500 | 0.500 | 5.00 | 132.07s |
| agent_graph | 2 | 0 | 0.500 | 0.500 | 0.500 | 0.500 | 1.000 | 0.667 | 0.500 | 3.50 | 153.02s |
| full_agent | 2 | 0 | 1.000 | 0.333 | 0.333 | 0.000 | 1.000 | 0.500 | 0.333 | 7.50 | 266.11s |
