# Phase T Benchmark Chance Report

Generated: 2026-06-29

## What Changed

Added a chance baseline metric to `scripts/evaluate_retrieval_quality.py`.

The metric answers this question:

> If retrieval randomly sampled top-k chunks from the whole corpus, what is the probability that it would hit at least one gold chunk?

Formula used:

`Random Hit@k = 1 - P(no gold chunk appears in random top-k sample)`

This lets us separate real retrieval signal from lucky hits. On the current corpus:

- Corpus chunks: `2347`
- Scored queries: `21`
- Mean random Hit@5 baseline: `0.004`

So a system with Hit@5 around `0.50` is not just lucky. It is more than 100x above random.

## Benchmark Runs

Two benchmark runs were executed on the same 30-query Phase T set:

- No expansion: `analytics/phase_t_t3_chance_baseline_no_expansion_30q.md`
- With expansion: `analytics/phase_t_t3_chance_baseline_expansion_30q.md`

Both use:

- `top_k = 5`
- `oracle_k = 10`
- tools: `vector`, `graph`, `hybrid`

## Overall Results

### No Query Expansion

| Tool | Scored | Hit@5 | Random Hit@5 | Lift vs Random | Recall@5 | MRR@5 | Oracle Hit@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| vector | 21 | 0.333 | 0.004 | 78.3x | 0.224 | 0.286 | 0.429 |
| graph | 21 | 0.190 | 0.004 | 44.8x | 0.093 | 0.085 | 0.381 |
| hybrid | 21 | 0.381 | 0.004 | 89.5x | 0.248 | 0.248 | 0.429 |

Takeaway: without LLM query expansion, graph alone underperforms vector. Hybrid is best because it keeps vector as a floor and sometimes benefits from graph.

### With Query Expansion

| Tool | Scored | Hit@5 | Random Hit@5 | Lift vs Random | Recall@5 | MRR@5 | Oracle Hit@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| vector | 21 | 0.333 | 0.004 | 78.3x | 0.224 | 0.286 | 0.429 |
| graph | 21 | 0.524 | 0.004 | 123.1x | 0.348 | 0.345 | 0.571 |
| hybrid | 21 | 0.524 | 0.004 | 123.1x | 0.352 | 0.409 | 0.619 |

Takeaway: query expansion is currently the main unlock for graph retrieval. It helps graph bridge implicit descriptions like "main x86 desktop CPU rival of Intel" to concrete KG entities like `AMD` and `Instinct`.

## Expansion Effect

Graph improved on:

- `T004`
- `T017`
- `T018`
- `T019`
- `T022`
- `T024`
- `T026`

Graph worsened on:

- none

Hybrid improved on:

- `T003`
- `T004`
- `T017`
- `T020`

Hybrid worsened on:

- `T001`

Interpretation: expansion is clearly useful for graph. Hybrid can still be disturbed when graph brings noisy chunks into fusion, as seen in `T001`.

## Failure Patterns

### 1. Gold Anchors Are Sometimes Too Narrow

Examples:

- `T011` retrieved other relevant `ENTG Item_7` chunks but missed the exact pinned `ENTG_2026_Item_7_0000_6c99ba90`.
- `T028` retrieved adjacent Micron memory/product chunks but missed the pinned overview chunks.
- `T029` retrieved NVIDIA/Rambus/AI-memory related chunks instead of the pinned Micron HBM chunks.

This means some failures are evaluation-anchor issues, not purely retriever failure.

### 2. Graph Needs Better Query Intent Control

Examples:

- `T001` should emphasize `AMD + TSMC + Item_1A supplier risk`, but graph expansion drifted toward broad supplier-risk chunks from `ENTG`, `QCOM`, `RMBS`, and `LRCX`.
- `T021` stayed around Intel manufacturing roadmap chunks, but missed the older-generation third-party foundry risk chunks.

Likely fix: stronger ticker/section/entity constraints after expansion.

### 3. Hybrid Fusion Can Bury Good Graph Hits

Examples:

- `T022`: graph hit the gold chunks, but hybrid missed because vector chunks occupied high ranks.
- `T024`: graph hit, hybrid missed for the same reason.

Likely fix: make hybrid fusion evidence-aware. If graph returns a high-confidence ticker+section match, it should not be overruled too easily by vector.

### 4. Three-Hop Questions Remain Hard

Examples:

- `T023`
- `T027`

These involve product -> company -> subsidiary -> product/segment style chains. Current PPR can surface nearby Intel/Mobileye chunks, but chunk rank is not precise enough yet.

Likely fix: trace these questions and inspect seed quality vs PPR neighborhood vs chunk mapping separately.

## Key Conclusion

The benchmark is not being dominated by random luck. Random Hit@5 is only `0.004`, while graph/hybrid with expansion reaches `0.524`.

The current bottleneck is not PPR alone. The strongest signal is:

1. Query expansion is essential for implicit multi-hop queries.
2. Graph retrieval becomes competitive only after expansion.
3. Hybrid is currently the best practical retriever, but fusion can suppress graph wins.
4. Next tuning step should focus on confidence-aware hybrid fusion and tighter graph intent constraints.

## Recommended Next Step

Phase T next should be `T2.3: Confidence-Aware Hybrid Fusion`.

Goal:

- Preserve vector as a safety floor.
- Let graph win when it has strong ticker/section/entity agreement.
- Prevent vector from burying good graph evidence on multi-hop questions.
