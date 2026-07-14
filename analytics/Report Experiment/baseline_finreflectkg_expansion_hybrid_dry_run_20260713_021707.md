# Phase T Retrieval Baseline

Generated: 2026-07-13T02:17:07

## Run Configuration

- script: `scripts/evaluate_retrieval_quality.py`
- command: `scripts/evaluate_retrieval_quality.py --queries data/evaluate/finreflectkg_sox_smoke10.yaml --tools vector graph hybrid --top-k 5 --oracle-k 20 --graph-seed-mode triple --candidate-pool-k 100 --graph-top-k-entities 40 --graph-damping 0.5 --graph-ppr-mode entity_only --graph-triple-filter none --reextract-tickers AMD,AVGO,INTC,NVDA,QCOM,TXN --version-name finreflectkg_expansion_hybrid_dry_run --ppr-seed-weight-mode uniform --dry-run`
- query_file: `data/evaluate/finreflectkg_sox_smoke10.yaml`
- query_count: `10`
- tools: `vector, graph, hybrid`
- top_k: `5`
- oracle_k: `20`
- dry_run: `True`
- corpus_chunks: `0`
- graph_use_expansion: `True`
- graph_seed_mode: `triple`
- graph_rerank_mode: `legacy`
- candidate_pool_k: `100`
- graph_top_k_entities: `40`
- graph_top_k_triples: `10`
- graph_damping: `0.5`
- ppr_seed_weight_mode: `uniform`
- graph_ppr_mode: `entity_only`
- graph_triple_filter: `none`
- metadata_rerank_params: `{'risk_section_boost': 1.35, 'business_section_boost': 1.18, 'financial_section_boost': 1.28, 'ticker_boost': 1.2, 'cluster_boost_per_extra': 0.04, 'cluster_boost_cap': 1.05, 'latest_year_boost': 1.08, 'latest_year_min': 2025, 'lexical_match_weight': 0.1, 'lexical_boost_cap': 0.55, 'broad_penalty_enabled': True, 'broad_penalty_floor': 0.92, 'broad_penalty_step': 0.97, 'broad_penalty_zero_match': 0.98, 'broad_penalty_short_token_cutoff': 80, 'broad_penalty_mid_token_cutoff': 140, 'broad_penalty_long_token_cutoff': 220}`
- version_name: `finreflectkg_expansion_hybrid_dry_run`
- details_jsonl: `/home/kantinan/programming/project/analytics/Report Experiment/details_finreflectkg_expansion_hybrid_dry_run_20260713_021707.jsonl`
- reextract_tickers_arg: `AMD,AVGO,INTC,NVDA,QCOM,TXN`
- resolved_ticker_scope: `AMD, AVGO, INTC, NVDA, QCOM, TXN`
- known_tickers: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- scored_queries: `10`
- unscored_queries: `0`
- existing_gold_entities: `21`
- total_gold_entities: `21`

## Overall

| Tool | Scored Queries | Errors | ChunkHit@k | Random ChunkHit@k | Hit Lift | Hit-Random | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 0 | 0 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| graph | 0 | 0 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| hybrid | 0 | 0 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottlenecks |
|---|---:|---:|---:|---:|---|
| full_mixed | 0.000 | 0.000 | n/a | n/a | n/a |

## Paired GroupRecall Test vs Vector

| Subset | Tool | n | Mean Delta GroupRecall | One-sided p |
|---|---|---:|---:|---:|
| full_mixed | graph | 0 | 0.000 | n/a |
| full_mixed | hybrid | 0 | 0.000 | n/a |

## Per Query

### FRKG003: `Based on the segment disclosures and term definitions in their 2024 10-K filings, how do Intel and NVIDIA differ in the treatment of stock-based compensation expenses within their 'All Other' categories, and what does this reveal about their corporate expense allocation practices?`

- type: `3hop_inter_document_cross_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['all other', 'cdp', 'intc', 'stock-based compensation expense']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2024.pdf::page_102::chunk_2', 'INTC_10k_2024.pdf::page_71::chunk_1', 'NVDA_10k_2024.pdf::page_78::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_102::chunk_2'], 'hop_2': ['INTC_10k_2024.pdf::page_71::chunk_1'], 'hop_3': ['NVDA_10k_2024.pdf::page_78::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |

### FRKG009: `What percentage of Texas Instruments' 2022 total revenue was represented by restructuring charges disclosed in the Other segment, and how does the company's segment reporting structure explain the separation of these charges from operating segments like Embedded Processing?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embedded processing', 'other segment', 'restructuring charges', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |

### FRKG010: `What was the total operating profit contribution from the Embedded Processing and Other segments in 2022 compared to 2023, considering that the Other segment includes restructuring charges and gains/losses from other activities as disclosed in the prior year's filing?`

- type: `3hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embedded processing', 'gains and losses from other activities', 'other', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_31::chunk_1', 'TXN_10k_2022.pdf::page_6::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_31::chunk_1'], 'hop_3': ['TXN_10k_2022.pdf::page_6::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |

### FRKG011: `What was the change in AMD's deferred tax liability related to acquired intangibles from 2022 to 2023, and how might the company's increasing compliance costs associated with SEC regulations influence this financial metric?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['acquired intangibles', 'amd', 'sec']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_10k_2023.pdf::page_36::chunk_1', 'AMD_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['AMD_10k_2023.pdf::page_36::chunk_1'], 'hop_2': ['AMD_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |

### FRKG070: `Calculate the total percentage growth in Mobileye's revenue from 2021 to 2023 and explain how the strategic initiatives outlined in the 2022 filing contributed to this increase.`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'mobileye', 'revenue']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2022.pdf::page_30::chunk_1', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2022.pdf::page_30::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |

### FRKG071: `Which segment includes acquisition, integration and restructuring charges, and what was its reported revenue in 2024?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['acquisition charges', 'other segment', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_2': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |

### FRKG073: `What was the change in operating losses for the 'All other' segment between 2021 and 2022, and what asset transfer amount into this segment was disclosed in 2023 according to Intel's financial reports?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['all other', 'intc', 'operating income']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2023.pdf::page_97::chunk_2', 'INTC_10k_2022.pdf::page_86::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2023.pdf::page_97::chunk_2'], 'hop_2': ['INTC_10k_2022.pdf::page_86::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |

### FRKG082: `What was the impact of the All Other segment's operating loss in 2023 on Intel's total operating income, and how does the segment's composition of non-reportable businesses and intersegment allocations contribute to this financial outcome?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['all other', 'intc', 'total operating income']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2024.pdf::page_71::chunk_1', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_71::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |

### FRKG084: `By how many percentage points did the operating income growth rate for AVGO's Infrastructure Software segment exceed its revenue growth rate in fiscal year 2022, and what does this indicate about the segment's operational efficiency?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['avgo', 'infrastructure software', 'operating income']`
- missing_gold_entities: `[]`
- gold_chunks: `['AVGO_10k_2022.pdf::page_70::chunk_2', 'AVGO_10k_2022.pdf::page_71::chunk_4']`
- gold_evidence_groups: `{'hop_1': ['AVGO_10k_2022.pdf::page_70::chunk_2'], 'hop_2': ['AVGO_10k_2022.pdf::page_71::chunk_4']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |

### FRKG093: `What was the percentage change in the value per percentage point of Mobileye's non-controlling interest from 2022 to 2023, and how does this reflect Intel's stake valuation in the segment?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['$ 989', 'intc', 'mobileye']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2024.pdf::page_70::chunk_1', 'INTC_10k_2023.pdf::page_89::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_70::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_89::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| vector |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| graph |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
| hybrid |  | 0.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not_applicable | `[]` | `{}` | `[]` |
