# Run commands

The two baseline commands below are copied exactly from their generated reports.
The two agent commands are reconstructed from `run_config.json`; the historical
evaluator did not save the original shell command.

## Vector-only — exact recorded command

```bash
python scripts/evaluate_retrieval_quality.py \
  --queries benchmark/datasets/finreflectkg_sox_strict74.yaml \
  --output-dir "analytics/Report Experiment" \
  --tools vector \
  --top-k 9 \
  --oracle-k 20 \
  --reextract-tickers AMD,AVGO,INTC,NVDA,QCOM,TXN \
  --final-rerank none \
  --candidate-pool-k 100 \
  --version-name vectoronly_strict74_top9_agent_ablation_20260802
```

## Graph-only t20 — exact recorded command

```bash
python scripts/evaluate_retrieval_quality.py \
  --queries benchmark/datasets/finreflectkg_sox_strict74.yaml \
  --output-dir "analytics/Report Experiment" \
  --tools graph \
  --top-k 9 \
  --oracle-k 20 \
  --no-llm-expansion \
  --graph-seed-mode triple \
  --graph-ppr-mode entity_chunk \
  --graph-triple-filter llm \
  --reextract-tickers AMD,AVGO,INTC,NVDA,QCOM,TXN \
  --ppr-seed-weight-mode uniform \
  --version-name graphonly_strict74_t20_llmfilter_top9_agent_ablation_20260802 \
  --graph-rerank-mode legacy \
  --final-rerank none \
  --candidate-pool-k 100 \
  --graph-top-k-entities 20 \
  --graph-top-k-triples 20 \
  --graph-damping 0.5
```

## Agent + Vector — reconstructed command

```bash
conda run -n senior_project python scripts/evaluate_finreflectkg_agent.py \
  --dataset benchmark/datasets/finreflectkg_sox_strict74.yaml \
  --modes agent_vector \
  --top-k 5 \
  --score-k 9 \
  --recursion-limit 50 \
  --run-name parallel_patch_strict74_vector
```

## Agent + Graph t20 — reconstructed command

Before this command, set `agent_retrieval.graph.top_k_triples: 20`. The value is
confirmed independently in every Graph retrieval trace stored in the run.

```bash
conda run -n senior_project python scripts/evaluate_finreflectkg_agent.py \
  --dataset benchmark/datasets/finreflectkg_sox_strict74.yaml \
  --modes agent_graph \
  --top-k 5 \
  --score-k 9 \
  --recursion-limit 50 \
  --run-name parallel_patch_strict74_graph_t20
```
