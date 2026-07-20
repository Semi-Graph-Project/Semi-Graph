# FinReflectKG Agent Evaluation

| Mode | Queries | Errors | Hit@5 | Recall@5 | GroupRecall@5 | Answerable@5 | Hit@All | Recall@All | Synthesis GroupRecall | Avg Calls | Avg Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| agent_vector | 2 | 0 | 1.000 | 0.333 | 0.333 | 0.000 | 1.000 | 0.667 | 0.667 | 3.00 | 54.73s |
| agent_graph | 2 | 0 | 0.500 | 0.167 | 0.167 | 0.000 | 1.000 | 0.500 | 0.500 | 4.00 | 171.20s |
| full_agent | 2 | 0 | 1.000 | 0.500 | 0.500 | 0.000 | 1.000 | 0.500 | 0.333 | 4.50 | 187.56s |
