# Phase T Retrieval Baseline

Generated: 2026-07-10T20:37:39

## Run Configuration

- script: `scripts/evaluate_retrieval_quality.py`
- command: `scripts/evaluate_retrieval_quality.py --queries data/evaluate/finreflectkg_sox_strict74.yaml --tools vector graph --top-k 5 --oracle-k 20 --no-llm-expansion --graph-seed-mode node --candidate-pool-k 100 --graph-top-k-entities 40 --graph-damping 0.5 --reextract-tickers AMD,AVGO,INTC,NVDA,QCOM,TXN --version-name finreflectkg_sox_strict74_node_ppr`
- query_file: `data/evaluate/finreflectkg_sox_strict74.yaml`
- query_count: `74`
- tools: `vector, graph`
- top_k: `5`
- oracle_k: `20`
- dry_run: `False`
- corpus_chunks: `3251`
- graph_use_expansion: `False`
- graph_seed_mode: `node`
- graph_rerank_mode: `legacy`
- candidate_pool_k: `100`
- graph_top_k_entities: `40`
- graph_top_k_triples: `8`
- graph_damping: `0.5`
- metadata_rerank_params: `{'risk_section_boost': 1.35, 'business_section_boost': 1.18, 'financial_section_boost': 1.28, 'ticker_boost': 1.2, 'cluster_boost_per_extra': 0.04, 'cluster_boost_cap': 1.05, 'latest_year_boost': 1.08, 'latest_year_min': 2025, 'lexical_match_weight': 0.1, 'lexical_boost_cap': 0.55, 'broad_penalty_enabled': True, 'broad_penalty_floor': 0.92, 'broad_penalty_step': 0.97, 'broad_penalty_zero_match': 0.98, 'broad_penalty_short_token_cutoff': 80, 'broad_penalty_mid_token_cutoff': 140, 'broad_penalty_long_token_cutoff': 220}`
- version_name: `finreflectkg_sox_strict74_node_ppr`
- details_jsonl: `/home/kantinan/programming/project/analytics/Report Experiment/details_sox_strict74_node.jsonl`
- reextract_tickers_arg: `AMD,AVGO,INTC,NVDA,QCOM,TXN`
- resolved_ticker_scope: `AMD, AVGO, INTC, NVDA, QCOM, TXN`
- known_tickers: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- scored_queries: `74`
- unscored_queries: `0`
- existing_gold_entities: `46`
- total_gold_entities: `88`

## Overall

| Tool | Scored Queries | Errors | ChunkHit@k | Random ChunkHit@k | Hit Lift | Hit-Random | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 74 | 0 | 0.311 | 0.004 | 86.519 | 0.307 | 0.142 | 0.149 | 0.014 | 0.176 | 0.554 |
| graph | 74 | 0 | 0.068 | 0.004 | 18.808 | 0.064 | 0.036 | 0.038 | 0.000 | 0.019 | 0.203 |

## By Type

| Type | vector ChunkHit | vector ChunkRecall | vector GroupRecall | vector Answerable | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2hop_inter_document_cross_company | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2hop_inter_document_same_company | 0.316 | 0.184 | 0.184 | 0.053 | 0.053 | 0.026 | 0.026 | 0.000 |
| 2hop_intra_document | 0.227 | 0.114 | 0.114 | 0.000 | 0.091 | 0.045 | 0.045 | 0.000 |
| 3hop_inter_document_cross_company | 0.429 | 0.143 | 0.143 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3hop_inter_document_same_company | 0.625 | 0.229 | 0.250 | 0.000 | 0.125 | 0.083 | 0.083 | 0.000 |
| 3hop_intra_document | 0.250 | 0.104 | 0.125 | 0.000 | 0.062 | 0.031 | 0.042 | 0.000 |

## By Subset

| Subset | vector ChunkHit | vector ChunkRecall | vector GroupRecall | vector Answerable | vector Oracle | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable | graph Oracle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| reextract_subset | 0.311 | 0.142 | 0.149 | 0.014 | 0.554 | 0.068 | 0.036 | 0.038 | 0.000 | 0.203 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 0.108 | 1.000 | 0.419 | chunk_mapping_loss=2, corpus_not_ready=53, hit_top_k=5, rerank_loss=1, seed_loss=13 |
| reextract_subset | 0.108 | 1.000 | 0.419 | chunk_mapping_loss=2, corpus_not_ready=53, hit_top_k=5, rerank_loss=1, seed_loss=13 |

## Paired GroupRecall Test vs Vector

| Subset | Tool | n | Mean Delta GroupRecall | One-sided p |
|---|---|---:|---:|---:|
| full_mixed | graph | 74 | -0.110 | 1.000 |
| reextract_subset | graph | 74 | -0.110 | 1.000 |

## Per Query

### FRKG003: `Based on the segment disclosures and term definitions in their 2024 10-K filings, how do Intel and NVIDIA differ in the treatment of stock-based compensation expenses within their 'All Other' categories, and what does this reveal about their corporate expense allocation practices?`

- type: `3hop_inter_document_cross_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['cdp', 'intc', 'all other', 'stock-based compensation expense']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2024.pdf::page_102::chunk_2', 'INTC_10k_2024.pdf::page_71::chunk_1', 'NVDA_10k_2024.pdf::page_78::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_102::chunk_2'], 'hop_2': ['INTC_10k_2024.pdf::page_71::chunk_1'], 'hop_3': ['NVDA_10k_2024.pdf::page_78::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 10.139 | 1 | 0.005 | 0.333 | 0.333 | 0 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_10k_2024.pdf::page_78::chunk_1']` | `{'hop_1': [], 'hop_2': [], 'hop_3': ['NVDA_10k_2024.pdf::page_78::chunk_1']}` | `['NVDA_10k_2022.pdf::page_99::chunk_1', 'NVDA_10k_2023.pdf::page_78::chunk_1', 'NVDA_10k_2024.pdf::page_79::chunk_1', 'NVDA_10k_2024.pdf::page_78::chunk_1', 'AMD_10k_2023.pdf::page_70::chunk_1']` |
| graph |  | 3.682 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2022.pdf::page_54::chunk_1', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1', 'INTC_10k_2022.pdf::page_120::chunk_1', 'INTC_10k_2022.pdf::page_23::chunk_1']` |

### FRKG009: `What percentage of Texas Instruments' 2022 total revenue was represented by restructuring charges disclosed in the Other segment, and how does the company's segment reporting structure explain the separation of these charges from operating segments like Embedded Processing?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embedded processing', 'txn', 'other segment', 'restructuring charges']`
- missing_gold_entities: `['embedded processing', 'restructuring charges']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.139 | 1 | 0.005 | 0.333 | 0.333 | 0 | 0.200 | 1 | n/a | n/a | n/a | not_applicable | `['TXN_10k_2023.pdf::page_30::chunk_1']` | `{'hop_1': [], 'hop_2': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_3': []}` | `['TXN_10k_2023.pdf::page_4::chunk_1', 'TXN_10k_2022.pdf::page_6::chunk_1', 'INTC_10k_2024.pdf::page_22::chunk_3', 'TXN_10k_2022.pdf::page_32::chunk_1', 'TXN_10k_2023.pdf::page_30::chunk_1']` |
| graph |  | 2.674 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2023.pdf::page_43::chunk_2', 'INTC_10k_2024.pdf::page_28::chunk_2', 'INTC_10k_2022.pdf::page_43::chunk_2', 'INTC_10k_2023.pdf::page_92::chunk_4']` |

### FRKG010: `What was the total operating profit contribution from the Embedded Processing and Other segments in 2022 compared to 2023, considering that the Other segment includes restructuring charges and gains/losses from other activities as disclosed in the prior year's filing?`

- type: `3hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embedded processing', 'txn', 'other', 'gains and losses from other activities']`
- missing_gold_entities: `['embedded processing', 'gains and losses from other activities']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_31::chunk_1', 'TXN_10k_2022.pdf::page_6::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_31::chunk_1'], 'hop_3': ['TXN_10k_2022.pdf::page_6::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.119 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_22::chunk_3', 'INTC_10k_2024.pdf::page_16::chunk_1', 'TXN_10k_2022.pdf::page_33::chunk_2', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2024.pdf::page_19::chunk_3']` |
| graph |  | 2.436 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2022.pdf::page_27::chunk_4', 'INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1', 'INTC_10k_2022.pdf::page_54::chunk_1']` |

### FRKG011: `What was the change in AMD's deferred tax liability related to acquired intangibles from 2022 to 2023, and how might the company's increasing compliance costs associated with SEC regulations influence this financial metric?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['sec', 'amd', 'acquired intangibles']`
- missing_gold_entities: `['acquired intangibles']`
- gold_chunks: `['AMD_10k_2023.pdf::page_36::chunk_1', 'AMD_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['AMD_10k_2023.pdf::page_36::chunk_1'], 'hop_2': ['AMD_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.119 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2024.pdf::page_85::chunk_3', 'AMD_10k_2023.pdf::page_88::chunk_3', 'NVDA_10k_2024.pdf::page_32::chunk_1', 'AMD_10k_2024.pdf::page_85::chunk_1', 'AMD_10k_2024.pdf::page_73::chunk_5']` |
| graph |  | 2.288 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['NVDA_10k_2024.pdf::page_39::chunk_1', 'NVDA_10k_2023.pdf::page_37::chunk_1', 'NVDA_10k_2024.pdf::page_76::chunk_2', 'NVDA_10k_2022.pdf::page_72::chunk_1', 'NVDA_10k_2022.pdf::page_49::chunk_1']` |

### FRKG070: `Calculate the total percentage growth in Mobileye's revenue from 2021 to 2023 and explain how the strategic initiatives outlined in the 2022 filing contributed to this increase.`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'mobileye', 'revenue']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2022.pdf::page_30::chunk_1', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2022.pdf::page_30::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.104 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2023.pdf::page_20::chunk_4', 'QCOM_10k_2024.pdf::page_73::chunk_6', 'QCOM_10k_2022.pdf::page_40::chunk_3', 'TXN_10k_2023.pdf::page_20::chunk_6', 'TXN_10k_2023.pdf::page_20::chunk_2']` |
| graph |  | 2.332 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_32::chunk_1', 'INTC_10k_2023.pdf::page_97::chunk_4', 'TXN_10k_2024.pdf::page_38::chunk_6', 'INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2022.pdf::page_95::chunk_2']` |

### FRKG071: `Which segment includes acquisition, integration and restructuring charges, and what was its reported revenue in 2024?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['txn', 'other segment', 'acquisition charges']`
- missing_gold_entities: `['acquisition charges']`
- gold_chunks: `['TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_2': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.108 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_79::chunk_5', 'INTC_10k_2024.pdf::page_28::chunk_3', 'AVGO_10k_2024.pdf::page_93::chunk_3', 'AVGO_10k_2023.pdf::page_93::chunk_3', 'AMD_10k_2024.pdf::page_73::chunk_5']` |
| graph |  | 2.436 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2024.pdf::page_30::chunk_1', 'INTC_10k_2024.pdf::page_27::chunk_1', 'INTC_10k_2024.pdf::page_28::chunk_3']` |

### FRKG073: `What was the change in operating losses for the 'All other' segment between 2021 and 2022, and what asset transfer amount into this segment was disclosed in 2023 according to Intel's financial reports?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'all other', 'operating income']`
- missing_gold_entities: `['operating income']`
- gold_chunks: `['INTC_10k_2023.pdf::page_97::chunk_2', 'INTC_10k_2022.pdf::page_86::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2023.pdf::page_97::chunk_2'], 'hop_2': ['INTC_10k_2022.pdf::page_86::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.115 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2024.pdf::page_26::chunk_1', 'INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2024.pdf::page_22::chunk_3']` |
| graph |  | 2.315 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2023.pdf::page_89::chunk_2', 'INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2023.pdf::page_22::chunk_1', 'INTC_10k_2023.pdf::page_49::chunk_2']` |

### FRKG082: `What was the impact of the All Other segment's operating loss in 2023 on Intel's total operating income, and how does the segment's composition of non-reportable businesses and intersegment allocations contribute to this financial outcome?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'all other', 'total operating income']`
- missing_gold_entities: `['total operating income']`
- gold_chunks: `['INTC_10k_2024.pdf::page_71::chunk_1', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_71::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.123 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_10k_2024.pdf::page_71::chunk_1']` | `{'hop_1': ['INTC_10k_2024.pdf::page_71::chunk_1'], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_22::chunk_3', 'INTC_10k_2024.pdf::page_19::chunk_3', 'INTC_10k_2024.pdf::page_71::chunk_1', 'INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2023.pdf::page_32::chunk_2']` |
| graph |  | 2.304 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2023.pdf::page_49::chunk_2', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2024.pdf::page_76::chunk_2', 'INTC_10k_2024.pdf::page_60::chunk_2']` |

### FRKG084: `By how many percentage points did the operating income growth rate for AVGO's Infrastructure Software segment exceed its revenue growth rate in fiscal year 2022, and what does this indicate about the segment's operational efficiency?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['avgo', 'infrastructure software', 'operating income']`
- missing_gold_entities: `['operating income']`
- gold_chunks: `['AVGO_10k_2022.pdf::page_70::chunk_2', 'AVGO_10k_2022.pdf::page_71::chunk_4']`
- gold_evidence_groups: `{'hop_1': ['AVGO_10k_2022.pdf::page_70::chunk_2'], 'hop_2': ['AVGO_10k_2022.pdf::page_71::chunk_4']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.112 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AVGO_10k_2022.pdf::page_71::chunk_5', 'AVGO_10k_2024.pdf::page_45::chunk_5', 'AVGO_10k_2023.pdf::page_45::chunk_5', 'NVDA_10k_2024.pdf::page_41::chunk_5', 'INTC_10k_2023.pdf::page_32::chunk_1']` |
| graph |  | 2.444 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_27::chunk_4', 'AVGO_10k_2024.pdf::page_90::chunk_2', 'AVGO_10k_2023.pdf::page_90::chunk_2', 'INTC_10k_2023.pdf::page_76::chunk_2', 'INTC_10k_2024.pdf::page_19::chunk_2']` |

### FRKG093: `What was the percentage change in the value per percentage point of Mobileye's non-controlling interest from 2022 to 2023, and how does this reflect Intel's stake valuation in the segment?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'mobileye', '$ 989']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2024.pdf::page_70::chunk_1', 'INTC_10k_2023.pdf::page_89::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_70::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_89::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.106 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2022.pdf::page_41::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2', 'INTC_10k_2024.pdf::page_74::chunk_10', 'QCOM_10k_2022.pdf::page_43::chunk_2']` |
| graph |  | 2.323 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2023.pdf::page_89::chunk_3', 'INTC_10k_2023.pdf::page_46::chunk_1', 'INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2024.pdf::page_74::chunk_8', 'INTC_10k_2023.pdf::page_50::chunk_1']` |

### FRKG096: `What was the total revenue contribution from Texas Instruments' Other segment in 2024, and which specific non-operational items are explicitly included in this segment's financial reporting?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['txn', 'other segment', 'asset dispositions']`
- missing_gold_entities: `['asset dispositions']`
- gold_chunks: `['TXN_10k_2024.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_30::chunk_1'], 'hop_2': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.109 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_22::chunk_3', 'AVGO_10k_2023.pdf::page_91::chunk_3', 'AVGO_10k_2024.pdf::page_91::chunk_3', 'TXN_10k_2022.pdf::page_68::chunk_1', 'INTC_10k_2024.pdf::page_16::chunk_1']` |
| graph |  | 2.250 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'NVDA_10k_2023.pdf::page_36::chunk_3', 'TXN_10k_2024.pdf::page_38::chunk_6', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1']` |

### FRKG098: `How does AMD disclose its executive compensation agreements, such as the sign-on bonus agreement with Jean Hu, to regulatory bodies and the public?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['sec', 'amd', 'sign-on bonus agreement with john doe']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_10k_2024.pdf::page_16::chunk_1', 'AMD_10k_2024.pdf::page_101::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['AMD_10k_2024.pdf::page_16::chunk_1'], 'hop_2': ['AMD_10k_2024.pdf::page_101::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.082 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2024.pdf::page_96::chunk_1', 'AMD_10k_2022.pdf::page_94::chunk_1', 'AMD_10k_2024.pdf::page_15::chunk_1', 'NVDA_10k_2023.pdf::page_46::chunk_1', 'AMD_10k_2022.pdf::page_95::chunk_1']` |
| graph |  | 2.396 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2022.pdf::page_63::chunk_2', 'TXN_10k_2023.pdf::page_61::chunk_2', 'TXN_10k_2024.pdf::page_58::chunk_1', 'TXN_10k_2024.pdf::page_59::chunk_2', 'TXN_10k_2022.pdf::page_29::chunk_1']` |

### FRKG100: `What was the operating profit contribution from the Embedded Processing segment in 2022, and how does this directly affect Texas Instruments' deferred tax liabilities under their asset and liability accounting approach for income taxes?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embedded processing', 'txn', 'deferred tax assets and liabilities']`
- missing_gold_entities: `['embedded processing', 'deferred tax assets and liabilities']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_32::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_32::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.097 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2024.pdf::page_20::chunk_5', 'TXN_10k_2023.pdf::page_4::chunk_1', 'TXN_10k_2022.pdf::page_22::chunk_5', 'TXN_10k_2022.pdf::page_6::chunk_1', 'TXN_10k_2023.pdf::page_20::chunk_5']` |
| graph |  | 2.435 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AVGO_10k_2023.pdf::page_88::chunk_2', 'AVGO_10k_2024.pdf::page_88::chunk_2', 'AMD_10k_2024.pdf::page_85::chunk_2', 'AMD_10k_2023.pdf::page_88::chunk_2', 'AMD_10k_2022.pdf::page_75::chunk_2']` |

### FRKG102: `What was the return on assets for Intel's Programmable Solutions Group in 2021, and how does this reflect the segment's efficiency in converting investments into operating income?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'programmable solutions group', 'net revenue']`
- missing_gold_entities: `['programmable solutions group']`
- gold_chunks: `['INTC_10k_2022.pdf::page_95::chunk_2', 'INTC_10k_2022.pdf::page_86::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2022.pdf::page_95::chunk_2'], 'hop_2': ['INTC_10k_2022.pdf::page_86::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.086 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2024.pdf::page_22::chunk_3', 'INTC_10k_2024.pdf::page_19::chunk_3', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2024.pdf::page_15::chunk_1']` |
| graph |  | 2.302 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2023.pdf::page_89::chunk_2', 'INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2022.pdf::page_27::chunk_4']` |

### FRKG103: `What percentage of QCT's fiscal 2024 revenue was represented by its accounts receivable balance as of September 29, 2024, and how does this relationship reflect the segment's revenue recognition practices for customer incentives?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['qcom', 'qct segment', 'accounts receivable']`
- missing_gold_entities: `['accounts receivable']`
- gold_chunks: `['QCOM_10k_2023.pdf::page_72::chunk_4', 'QCOM_10k_2023.pdf::page_59::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['QCOM_10k_2023.pdf::page_72::chunk_4'], 'hop_2': ['QCOM_10k_2023.pdf::page_59::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.098 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['QCOM_10k_2023.pdf::page_59::chunk_1']` | `{'hop_1': [], 'hop_2': ['QCOM_10k_2023.pdf::page_59::chunk_1']}` | `['QCOM_10k_2024.pdf::page_59::chunk_1', 'QCOM_10k_2023.pdf::page_59::chunk_1', 'QCOM_10k_2022.pdf::page_58::chunk_1', 'NVDA_10k_2022.pdf::page_100::chunk_5', 'QCOM_10k_2023.pdf::page_41::chunk_3']` |
| graph |  | 2.343 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2024.pdf::page_38::chunk_6', 'TXN_10k_2022.pdf::page_66::chunk_1', 'INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2024.pdf::page_88::chunk_4', 'QCOM_10k_2024.pdf::page_73::chunk_6']` |

### FRKG104: `What was the dollar increase in Intel's consolidated share of Mobileye's operating income between 2022 and 2023, and how did this compare to the overall decline in Intel's total operating income during the same period?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'mobileye', 'total operating income']`
- missing_gold_entities: `['total operating income']`
- gold_chunks: `['INTC_10k_2023.pdf::page_89::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2023.pdf::page_89::chunk_2'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.101 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_10k_2023.pdf::page_88::chunk_2']` | `{'hop_1': [], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}` | `['INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2023.pdf::page_88::chunk_2', 'INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2024.pdf::page_20::chunk_1']` |
| graph |  | 2.446 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.333 | 1 | 0 | 1 | 1 | hit_top_k | `['INTC_10k_2023.pdf::page_89::chunk_2']` | `{'hop_1': ['INTC_10k_2023.pdf::page_89::chunk_2'], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2023.pdf::page_89::chunk_2', 'INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2023.pdf::page_76::chunk_2']` |

### FRKG105: `What is the ratio of goodwill allocated to the Embedded Processing segment relative to its average operating profit across 2022 and 2023, and how does this compare to the company's total goodwill allocation?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embedded processing', 'txn', 'goodwill']`
- missing_gold_entities: `['embedded processing']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_31::chunk_1', 'TXN_10k_2024.pdf::page_52::chunk_8']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_31::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_52::chunk_8']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.117 | 1 | 0.005 | 0.333 | 0.333 | 0 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['TXN_10k_2024.pdf::page_52::chunk_8']` | `{'hop_1': [], 'hop_2': [], 'hop_3': ['TXN_10k_2024.pdf::page_52::chunk_8']}` | `['TXN_10k_2022.pdf::page_55::chunk_6', 'TXN_10k_2023.pdf::page_54::chunk_2', 'TXN_10k_2024.pdf::page_52::chunk_8', 'INTC_10k_2024.pdf::page_22::chunk_3', 'NVDA_10k_2023.pdf::page_63::chunk_5']` |
| graph |  | 2.308 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['AMD_10k_2023.pdf::page_50::chunk_1', 'TXN_10k_2022.pdf::page_33::chunk_2', 'AMD_10k_2022.pdf::page_45::chunk_1', 'AMD_10k_2022.pdf::page_59::chunk_1', 'TXN_10k_2023.pdf::page_3::chunk_1']` |

### FRKG107: `What was the percentage change in Mobileye's total equity from 2022 to 2023, based on Intel's non-controlling interest disclosures and ownership percentages?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'mobileye', '$ 989']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2024.pdf::page_74::chunk_6', 'INTC_10k_2023.pdf::page_89::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_74::chunk_6'], 'hop_2': ['INTC_10k_2023.pdf::page_89::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.092 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2', 'INTC_10k_2022.pdf::page_41::chunk_2', 'INTC_10k_2022.pdf::page_95::chunk_2', 'INTC_10k_2022.pdf::page_95::chunk_4']` |
| graph |  | 2.342 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2023.pdf::page_46::chunk_1', 'INTC_10k_2023.pdf::page_45::chunk_3', 'INTC_10k_2023.pdf::page_8::chunk_1']` |

### FRKG108: `What was the operating profit per share contributed by Texas Instruments' 'Other' segment in 2022, based on the total shares outstanding as of January 25, 2022?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['other', 'txn', 'shares outstanding']`
- missing_gold_entities: `['shares outstanding']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2022.pdf::page_1::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2022.pdf::page_1::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.114 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['TXN_10k_2024.pdf::page_31::chunk_3']` | `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': []}` | `['QCOM_10k_2022.pdf::page_43::chunk_2', 'NVDA_10k_2024.pdf::page_55::chunk_2', 'TXN_10k_2023.pdf::page_66::chunk_1', 'TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_64::chunk_1']` |
| graph |  | 2.286 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_27::chunk_4', 'TXN_10k_2022.pdf::page_33::chunk_2', 'AMD_10k_2023.pdf::page_48::chunk_1', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1']` |

### FRKG111: `What was the ratio of the amortization of capitalized software in 2021 to the operating profit of the 'Other' segment in 2022?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['other', 'txn', 'amort. cap. software']`
- missing_gold_entities: `['amort. cap. software']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2022.pdf::page_30::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2022.pdf::page_30::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.090 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_86::chunk_3', 'AMD_10k_2024.pdf::page_73::chunk_5', 'INTC_10k_2023.pdf::page_98::chunk_3', 'AMD_10k_2023.pdf::page_76::chunk_4', 'AMD_10k_2024.pdf::page_74::chunk_1']` |
| graph |  | 2.422 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_95::chunk_10', 'INTC_10k_2022.pdf::page_27::chunk_4', 'INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1']` |

### FRKG138: `As Senior Vice President and Chief Financial Officer listed in Texas Instruments' governance records, how does Rafael R. Lizardi's organizational role specifically connect to the $249 million tax benefit disclosed from the settlement of a depreciation-related uncertain tax position in 2020?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['rafael r. lizardi', 'txn', 'tax benefit']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2022.pdf::page_69::chunk_2', 'TXN_10k_2022.pdf::page_42::chunk_3']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_69::chunk_2'], 'hop_2': ['TXN_10k_2022.pdf::page_42::chunk_3']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.117 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2024.pdf::page_64::chunk_1', 'TXN_10k_2022.pdf::page_68::chunk_1', 'TXN_10k_2023.pdf::page_66::chunk_1', 'TXN_10k_2022.pdf::page_69::chunk_1', 'TXN_10k_2023.pdf::page_61::chunk_3']` |
| graph |  | 2.280 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2022.pdf::page_64::chunk_2', 'TXN_10k_2024.pdf::page_60::chunk_2', 'TXN_10k_2024.pdf::page_55::chunk_2', 'TXN_10k_2022.pdf::page_58::chunk_2', 'TXN_10k_2022.pdf::page_59::chunk_1']` |

### FRKG141: `What accrued balance is disclosed in Intel's 2024 financial statements, and how does Michelle Johnston Holthaus's executive role relate to this financial disclosure?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['michelle johnston holthaus', 'intc', 'accrued balance']`
- missing_gold_entities: `['accrued balance']`
- gold_chunks: `['INTC_10k_2024.pdf::page_111::chunk_1', 'INTC_10k_2024.pdf::page_79::chunk_6']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_111::chunk_1'], 'hop_2': ['INTC_10k_2024.pdf::page_79::chunk_6']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.100 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2023.pdf::page_81::chunk_1', 'INTC_10k_2024.pdf::page_64::chunk_1', 'INTC_10k_2024.pdf::page_56::chunk_1', 'INTC_10k_2022.pdf::page_120::chunk_1', 'INTC_10k_2022.pdf::page_66::chunk_3']` |
| graph |  | 2.351 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AVGO_10k_2022.pdf::page_107::chunk_2', 'AVGO_10k_2022.pdf::page_116::chunk_2', 'AVGO_10k_2023.pdf::page_2::chunk_1', 'AVGO_10k_2024.pdf::page_65::chunk_9', 'AVGO_10k_2024.pdf::page_73::chunk_6']` |

### FRKG142: `What was the total cash payments for interest on long-term debt made by Texas Instruments during Richard K. Templeton's tenure as President and Chief Executive Officer, based on the disclosed amounts for 2022 through 2024?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['richard k. templeton', 'txn', 'cash payments for interest on long-term debt']`
- missing_gold_entities: `['cash payments for interest on long-term debt']`
- gold_chunks: `['TXN_10k_2022.pdf::page_69::chunk_2', 'TXN_10k_2024.pdf::page_50::chunk_3']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_69::chunk_2'], 'hop_2': ['TXN_10k_2024.pdf::page_50::chunk_3']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.110 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['QCOM_10k_2024.pdf::page_79::chunk_1', 'QCOM_10k_2023.pdf::page_79::chunk_1', 'AVGO_10k_2023.pdf::page_83::chunk_1', 'AVGO_10k_2024.pdf::page_83::chunk_1', 'QCOM_10k_2024.pdf::page_79::chunk_3']` |
| graph |  | 2.451 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2023.pdf::page_77::chunk_2', 'AVGO_10k_2023.pdf::page_83::chunk_2', 'AVGO_10k_2024.pdf::page_83::chunk_2', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1']` |

### FRKG161: `What was the dollar increase in Mobileye's non-controlling interest value from 2022 to 2023, and how does this growth relate to Intel's retained ownership stake following Mobileye's IPO?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'mobileye', '$ 989']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2022.pdf::page_30::chunk_1', 'INTC_10k_2023.pdf::page_89::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2022.pdf::page_30::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_89::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.122 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2022.pdf::page_41::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2', 'INTC_10k_2022.pdf::page_95::chunk_2', 'INTC_10k_2022.pdf::page_95::chunk_4']` |
| graph |  | 2.303 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2022.pdf::page_95::chunk_2', 'INTC_10k_2022.pdf::page_40::chunk_1', 'INTC_10k_2022.pdf::page_32::chunk_1']` |

### FRKG163: `How does the inclusion of gains and losses from asset dispositions in the Other segment affect the evaluation of its $947 million revenue in 2024?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['txn', 'other segment', 'gains and losses']`
- missing_gold_entities: `['gains and losses']`
- gold_chunks: `['TXN_10k_2024.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_30::chunk_1'], 'hop_2': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.112 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AVGO_10k_2023.pdf::page_61::chunk_1', 'AVGO_10k_2024.pdf::page_61::chunk_1', 'INTC_10k_2024.pdf::page_82::chunk_5', 'INTC_10k_2024.pdf::page_29::chunk_5', 'QCOM_10k_2022.pdf::page_86::chunk_3']` |
| graph |  | 2.336 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2024.pdf::page_38::chunk_6', 'INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2023.pdf::page_49::chunk_2', 'INTC_10k_2022.pdf::page_48::chunk_1', 'INTC_10k_2023.pdf::page_48::chunk_1']` |

### FRKG173: `What was the percentage change in the Programmable Solutions Group's operating income from 2020 to 2021, and how does this relate to the segment's asset adjustments and the auditor's evaluation of inventory valuation practices?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['ernst & young llp', 'intc', 'programmable solutions group', 'operating income']`
- missing_gold_entities: `['programmable solutions group', 'operating income']`
- gold_chunks: `['INTC_10k_2022.pdf::page_72::chunk_1', 'INTC_10k_2022.pdf::page_95::chunk_4', 'INTC_10k_2022.pdf::page_86::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2022.pdf::page_72::chunk_1'], 'hop_2': ['INTC_10k_2022.pdf::page_95::chunk_4'], 'hop_3': ['INTC_10k_2022.pdf::page_86::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.107 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['AMD_10k_2022.pdf::page_87::chunk_1', 'TXN_10k_2022.pdf::page_22::chunk_7', 'AVGO_10k_2023.pdf::page_48::chunk_3', 'AVGO_10k_2024.pdf::page_48::chunk_3', 'AVGO_10k_2022.pdf::page_71::chunk_5']` |
| graph |  | 2.428 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2022.pdf::page_27::chunk_4', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1', 'INTC_10k_2022.pdf::page_54::chunk_1', 'INTC_10k_2022.pdf::page_120::chunk_1']` |

### FRKG177: `How does CDP's role in managing environmental impacts influence the structure of corporate infrastructure and support cost reporting in Intel's 'All Other' segment, and how does this compare to NVIDIA's treatment of similar costs in its 'All Other' category?`

- type: `3hop_inter_document_cross_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['cdp', 'intc', 'all other', 'corporate infrastructure and support costs']`
- missing_gold_entities: `['corporate infrastructure and support costs']`
- gold_chunks: `['INTC_10k_2024.pdf::page_102::chunk_2', 'INTC_10k_2024.pdf::page_70::chunk_1', 'NVDA_10k_2024.pdf::page_78::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_102::chunk_2'], 'hop_2': ['INTC_10k_2024.pdf::page_70::chunk_1'], 'hop_3': ['NVDA_10k_2024.pdf::page_78::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.113 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['NVDA_10k_2022.pdf::page_16::chunk_1', 'NVDA_10k_2022.pdf::page_99::chunk_1', 'NVDA_10k_2024.pdf::page_79::chunk_1', 'NVDA_10k_2023.pdf::page_78::chunk_1', 'AMD_10k_2024.pdf::page_69::chunk_1']` |
| graph |  | 2.328 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['QCOM_10k_2022.pdf::page_30::chunk_1', 'QCOM_10k_2024.pdf::page_30::chunk_1', 'QCOM_10k_2024.pdf::page_4::chunk_1', 'QCOM_10k_2024.pdf::page_16::chunk_1', 'QCOM_10k_2022.pdf::page_3::chunk_1']` |

### FRKG179: `What was the total net income reported by Texas Instruments (TXN) during Rafael R. Lizardi's tenure as Chief Financial Officer, based on the financial data provided for the years 2019 through 2021?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['rafael r. lizardi', 'txn', 'net income']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2022.pdf::page_69::chunk_2', 'TXN_10k_2022.pdf::page_31::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_69::chunk_2'], 'hop_2': ['TXN_10k_2022.pdf::page_31::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.111 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2022.pdf::page_68::chunk_1', 'TXN_10k_2024.pdf::page_64::chunk_1', 'TXN_10k_2023.pdf::page_66::chunk_1', 'TXN_10k_2024.pdf::page_59::chunk_3', 'TXN_10k_2022.pdf::page_57::chunk_1']` |
| graph |  | 2.338 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_27::chunk_4', 'TXN_10k_2022.pdf::page_64::chunk_2', 'INTC_10k_2023.pdf::page_124::chunk_2', 'INTC_10k_2023.pdf::page_70::chunk_2', 'INTC_10k_2022.pdf::page_68::chunk_2']` |

### FRKG182: `How does the auditor's assessment of internal control effectiveness influence the reliability of Texas Instruments' purchase commitment disclosures, and what total amount is committed beyond 2023?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['ernst & young llp', 'txn', 'thereafter payments']`
- missing_gold_entities: `['thereafter payments']`
- gold_chunks: `['TXN_10k_2022.pdf::page_60::chunk_1', 'TXN_10k_2023.pdf::page_52::chunk_6']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_60::chunk_1'], 'hop_2': ['TXN_10k_2023.pdf::page_52::chunk_6']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.109 | 1 | 0.003 | 0.500 | 0.500 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['TXN_10k_2022.pdf::page_60::chunk_1']` | `{'hop_1': ['TXN_10k_2022.pdf::page_60::chunk_1'], 'hop_2': []}` | `['TXN_10k_2022.pdf::page_60::chunk_1', 'TXN_10k_2024.pdf::page_57::chunk_1', 'NVDA_10k_2022.pdf::page_63::chunk_1', 'TXN_10k_2024.pdf::page_54::chunk_1', 'TXN_10k_2022.pdf::page_57::chunk_1']` |
| graph |  | 2.192 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AVGO_10k_2022.pdf::page_129::chunk_1', 'AVGO_10k_2023.pdf::page_91::chunk_4', 'NVDA_10k_2024.pdf::page_50::chunk_1', 'AVGO_10k_2023.pdf::page_95::chunk_1', 'AVGO_10k_2022.pdf::page_78::chunk_1']` |

### FRKG185: `What was the year-over-year change in Qualcomm's current year tax position additions between 2023 and 2024, and how does this relate to Kornelis Smit's governance role at the company?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['kornelis neil smit', 'qcom', 'additions current year tax pos.']`
- missing_gold_entities: `['additions current year tax pos.']`
- gold_chunks: `['QCOM_10k_2024.pdf::page_57::chunk_2', 'QCOM_10k_2023.pdf::page_77::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['QCOM_10k_2024.pdf::page_57::chunk_2'], 'hop_2': ['QCOM_10k_2023.pdf::page_77::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.152 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['QCOM_10k_2022.pdf::page_77::chunk_1', 'QCOM_10k_2023.pdf::page_77::chunk_1', 'QCOM_10k_2024.pdf::page_77::chunk_1', 'QCOM_10k_2024.pdf::page_78::chunk_1', 'QCOM_10k_2023.pdf::page_78::chunk_1']` |
| graph |  | 2.465 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['QCOM_10k_2024.pdf::page_13::chunk_1', 'QCOM_10k_2023.pdf::page_17::chunk_1', 'QCOM_10k_2023.pdf::page_80::chunk_2', 'QCOM_10k_2024.pdf::page_16::chunk_1', 'TXN_10k_2024.pdf::page_55::chunk_2']` |

### FRKG187: `What was the total revenue decline in Texas Instruments' 'Other' segment from 2022 to 2024, and how does this relate to the inclusion of asset dispositions in the segment's financial reporting as disclosed in both 2023 and 2024 filings?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['other', 'txn', 'other segment', 'asset dispositions']`
- missing_gold_entities: `['asset dispositions']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2023.pdf::page_4::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2023.pdf::page_4::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.114 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['TXN_10k_2024.pdf::page_20::chunk_7', 'TXN_10k_2023.pdf::page_20::chunk_7', 'INTC_10k_2024.pdf::page_25::chunk_3', 'NVDA_10k_2023.pdf::page_40::chunk_1', 'TXN_10k_2022.pdf::page_1::chunk_1']` |
| graph |  | 2.351 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1', 'INTC_10k_2022.pdf::page_54::chunk_1', 'INTC_10k_2022.pdf::page_120::chunk_1']` |

### FRKG192: `What financial impact did Texas Instruments' delegation of signing authority to attorneys-in-fact have on its pension plan obligations, specifically regarding plan amendments disclosed in the 2021 financial statements?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['attorneys-in-fact', 'txn', 'plan amendments']`
- missing_gold_entities: `['plan amendments']`
- gold_chunks: `['TXN_10k_2022.pdf::page_69::chunk_1', 'TXN_10k_2022.pdf::page_47::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_69::chunk_1'], 'hop_2': ['TXN_10k_2022.pdf::page_47::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.108 | 1 | 0.003 | 0.500 | 0.500 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['TXN_10k_2022.pdf::page_69::chunk_1']` | `{'hop_1': ['TXN_10k_2022.pdf::page_69::chunk_1'], 'hop_2': []}` | `['TXN_10k_2022.pdf::page_69::chunk_1', 'TXN_10k_2022.pdf::page_68::chunk_1', 'TXN_10k_2023.pdf::page_67::chunk_1', 'TXN_10k_2024.pdf::page_65::chunk_1', 'TXN_10k_2024.pdf::page_64::chunk_1']` |
| graph |  | 2.286 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2022.pdf::page_64::chunk_2', 'TXN_10k_2024.pdf::page_60::chunk_2', 'TXN_10k_2023.pdf::page_26::chunk_2', 'TXN_10k_2023.pdf::page_44::chunk_1', 'TXN_10k_2022.pdf::page_18::chunk_3']` |

### FRKG239: `What percentage of the Client Computing Group's 2021 net revenue did its value represent as of December 25, 2021?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'client computing group', 'net revenue']`
- missing_gold_entities: `['client computing group']`
- gold_chunks: `['INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2022.pdf::page_86::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2023.pdf::page_97::chunk_4'], 'hop_2': ['INTC_10k_2022.pdf::page_86::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.098 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_10k_2022.pdf::page_86::chunk_2']` | `{'hop_1': [], 'hop_2': ['INTC_10k_2022.pdf::page_86::chunk_2']}` | `['AMD_10k_2024.pdf::page_50::chunk_2', 'INTC_10k_2022.pdf::page_86::chunk_2', 'AMD_10k_2023.pdf::page_51::chunk_2', 'INTC_10k_2022.pdf::page_95::chunk_2', 'INTC_10k_2022.pdf::page_87::chunk_1']` |
| graph |  | 2.436 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_54::chunk_1', 'INTC_10k_2022.pdf::page_95::chunk_2', 'NVDA_10k_2024.pdf::page_38::chunk_3', 'AMD_10k_2023.pdf::page_69::chunk_7', 'INTC_10k_2023.pdf::page_50::chunk_1']` |

### FRKG240: `How did the increase in Mobileye's research and development expenditures and operating costs in 2023 affect its operating income compared to 2022, and what was the resulting impact on Intel's total operating income?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'mobileye', 'total operating income']`
- missing_gold_entities: `['total operating income']`
- gold_chunks: `['INTC_10k_2024.pdf::page_24::chunk_1', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_24::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.119 | 1 | 0.003 | 1.000 | 1.000 | 1 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_10k_2023.pdf::page_88::chunk_2', 'INTC_10k_2024.pdf::page_24::chunk_1']` | `{'hop_1': ['INTC_10k_2024.pdf::page_24::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}` | `['INTC_10k_2023.pdf::page_88::chunk_2', 'INTC_10k_2024.pdf::page_20::chunk_1', 'INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2024.pdf::page_21::chunk_1', 'INTC_10k_2024.pdf::page_24::chunk_1']` |
| graph |  | 2.307 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2022.pdf::page_32::chunk_1', 'INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2022.pdf::page_95::chunk_2']` |

### FRKG241: `What amount in Texas Instruments' 2024 financial statements represents environmental costs included within the Other segment's restructuring charges/other line item?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['txn', 'other segment', 'environmental costs']`
- missing_gold_entities: `['environmental costs']`
- gold_chunks: `['TXN_10k_2024.pdf::page_30::chunk_2', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_30::chunk_2'], 'hop_2': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.107 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_28::chunk_3', 'QCOM_10k_2023.pdf::page_42::chunk_4', 'QCOM_10k_2024.pdf::page_42::chunk_4', 'TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2022.pdf::page_32::chunk_1']` |
| graph |  | 2.277 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2024.pdf::page_55::chunk_2', 'INTC_10k_2023.pdf::page_43::chunk_2', 'INTC_10k_2024.pdf::page_28::chunk_2', 'INTC_10k_2023.pdf::page_72::chunk_2']` |

### FRKG249: `What was the percentage decrease in revenue and change in operating income for Intel's Network and Edge segment from 2022 to 2023, and how do these changes reflect the impact of the organizational restructuring announced in 2023?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'network and edge', 'revenue']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2023.pdf::page_87::chunk_1', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2023.pdf::page_87::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.111 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_20::chunk_1', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2024.pdf::page_19::chunk_3', 'INTC_10k_2023.pdf::page_32::chunk_2', 'INTC_10k_2024.pdf::page_22::chunk_3']` |
| graph |  | 2.267 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2023.pdf::page_89::chunk_2', 'INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1']` |

### FRKG273: `What total value of stock options outstanding is disclosed in Texas Instruments' 2021 financial report, calculated using the weighted average exercise price per share, and which individuals are explicitly authorized to file regulatory disclosures containing this metric?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['attorneys-in-fact', 'txn', 'weighted average exercise price per share']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2022.pdf::page_69::chunk_1', 'TXN_10k_2022.pdf::page_38::chunk_8']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_69::chunk_1'], 'hop_2': ['TXN_10k_2022.pdf::page_38::chunk_8']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.120 | 1 | 0.003 | 0.500 | 0.500 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['TXN_10k_2022.pdf::page_38::chunk_8']` | `{'hop_1': [], 'hop_2': ['TXN_10k_2022.pdf::page_38::chunk_8']}` | `['TXN_10k_2022.pdf::page_38::chunk_8', 'TXN_10k_2023.pdf::page_37::chunk_6', 'TXN_10k_2024.pdf::page_64::chunk_1', 'TXN_10k_2023.pdf::page_66::chunk_1', 'TXN_10k_2022.pdf::page_68::chunk_1']` |
| graph |  | 2.406 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.200 | 1 | 1 | 1 | 1 | hit_top_k | `['TXN_10k_2022.pdf::page_38::chunk_8']` | `{'hop_1': [], 'hop_2': ['TXN_10k_2022.pdf::page_38::chunk_8']}` | `['TXN_10k_2024.pdf::page_59::chunk_2', 'TXN_10k_2022.pdf::page_38::chunk_6', 'TXN_10k_2023.pdf::page_37::chunk_4', 'TXN_10k_2024.pdf::page_37::chunk_4', 'TXN_10k_2022.pdf::page_38::chunk_8']` |

### FRKG274: `What is the combined total of the Other segment's 2022 revenue and restructuring charges, and how does this amount relate to the segment's 2024 revenue disclosure considering corporate-level environmental costs included in Other?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['analog', 'txn', 'other segment', 'environmental costs']`
- missing_gold_entities: `['environmental costs']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_30::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.111 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['QCOM_10k_2023.pdf::page_42::chunk_4', 'QCOM_10k_2024.pdf::page_42::chunk_4', 'INTC_10k_2024.pdf::page_79::chunk_5', 'INTC_10k_2024.pdf::page_28::chunk_3', 'AVGO_10k_2022.pdf::page_127::chunk_3']` |
| graph |  | 2.369 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2022.pdf::page_39::chunk_2', 'INTC_10k_2023.pdf::page_39::chunk_2', 'INTC_10k_2024.pdf::page_31::chunk_3', 'INTC_10k_2024.pdf::page_25::chunk_2']` |

### FRKG275: `What is the total restructuring charge impact on TXN's financial reporting when considering the historical charges disclosed in the Other segment's 2022 results and its inclusion in corporate-level financial evaluations alongside the Embedded Processing segment's 2024 revenue contribution?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embedded processing', 'txn', 'other segment', 'restructuring charges']`
- missing_gold_entities: `['embedded processing', 'restructuring charges']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_4::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.120 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_28::chunk_3', 'TXN_10k_2022.pdf::page_54::chunk_5', 'INTC_10k_2023.pdf::page_92::chunk_5', 'AVGO_10k_2024.pdf::page_93::chunk_3', 'INTC_10k_2022.pdf::page_43::chunk_3']` |
| graph |  | 2.357 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2022.pdf::page_39::chunk_2', 'INTC_10k_2023.pdf::page_39::chunk_2', 'INTC_10k_2024.pdf::page_25::chunk_2', 'INTC_10k_2024.pdf::page_59::chunk_2']` |

### FRKG276: `How did CDP's environmental disclosure requirements influence Intel's restructuring of Intel Foundry, and what was the combined financial impact on Intel Foundry Services' operating loss in 2023?`

- type: `3hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['cdp', 'intc', 'intel foundry services', 'total operating income']`
- missing_gold_entities: `['intel foundry services', 'total operating income']`
- gold_chunks: `['INTC_10k_2024.pdf::page_102::chunk_2', 'INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_102::chunk_2'], 'hop_2': ['INTC_10k_2024.pdf::page_85::chunk_2'], 'hop_3': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.101 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_21::chunk_1', 'INTC_10k_2024.pdf::page_70::chunk_1', 'INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2024.pdf::page_71::chunk_1']` |
| graph |  | 2.572 | 1 | 0.005 | 0.667 | 0.667 | 0 | 0.333 | 1 | 0 | 1 | 1 | hit_top_k | `['INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2']` | `{'hop_1': [], 'hop_2': ['INTC_10k_2024.pdf::page_85::chunk_2'], 'hop_3': ['INTC_10k_2023.pdf::page_88::chunk_2']}` | `['INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2024.pdf::page_21::chunk_1', 'INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2', 'INTC_10k_2024.pdf::page_36::chunk_1']` |

### FRKG279: `How did the Network and Edge segment's operating loss in 2023 contribute to Intel's total operating income, given its unchanged asset balance and the historical tax settlements with authorities?`

- type: `3hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['tax authorities', 'intc', 'network and edge', 'total operating income']`
- missing_gold_entities: `['tax authorities', 'total operating income']`
- gold_chunks: `['INTC_10k_2022.pdf::page_92::chunk_2', 'INTC_10k_2023.pdf::page_97::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2022.pdf::page_92::chunk_2'], 'hop_2': ['INTC_10k_2023.pdf::page_97::chunk_2'], 'hop_3': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.103 | 1 | 0.005 | 0.333 | 0.333 | 0 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_10k_2023.pdf::page_88::chunk_2']` | `{'hop_1': [], 'hop_2': [], 'hop_3': ['INTC_10k_2023.pdf::page_88::chunk_2']}` | `['INTC_10k_2023.pdf::page_32::chunk_2', 'INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2', 'INTC_10k_2024.pdf::page_19::chunk_3', 'INTC_10k_2024.pdf::page_16::chunk_1']` |
| graph |  | 2.284 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2023.pdf::page_76::chunk_2', 'INTC_10k_2024.pdf::page_25::chunk_2', 'INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2024.pdf::page_59::chunk_2']` |

### FRKG284: `What was AMD's total depreciation expense from 2021 to 2023, and how does this financial metric relate to SEC regulatory requirements that involve attorneys-in-fact for compliance filings?`

- type: `3hop_inter_document_cross_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['attorney-in-fact', 'sec', 'amd', 'depreciation expense']`
- missing_gold_entities: `[]`
- gold_chunks: `['AVGO_10k_2023.pdf::page_104::chunk_1', 'AMD_10k_2023.pdf::page_36::chunk_1', 'AMD_10k_2023.pdf::page_69::chunk_5']`
- gold_evidence_groups: `{'hop_1': ['AVGO_10k_2023.pdf::page_104::chunk_1'], 'hop_2': ['AMD_10k_2023.pdf::page_36::chunk_1'], 'hop_3': ['AMD_10k_2023.pdf::page_69::chunk_5']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.102 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['NVDA_10k_2024.pdf::page_70::chunk_1', 'AMD_10k_2023.pdf::page_63::chunk_1', 'INTC_10k_2024.pdf::page_77::chunk_3', 'AMD_10k_2022.pdf::page_58::chunk_1', 'AMD_10k_2024.pdf::page_62::chunk_1']` |
| graph |  | 2.319 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2022.pdf::page_95::chunk_10', 'INTC_10k_2023.pdf::page_42::chunk_1', 'INTC_10k_2024.pdf::page_26::chunk_1', 'INTC_10k_2024.pdf::page_71::chunk_1', 'INTC_10k_2024.pdf::page_78::chunk_1']` |

### FRKG288: `How does the confirmation of effective internal control over financial reporting by Ernst & Young LLP in their 2022 audit relate to the reliability of Texas Instruments' 2022 cash flows from financing activities disclosure?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['ernst & young llp', 'txn', 'cash flows from financing activities']`
- missing_gold_entities: `['cash flows from financing activities']`
- gold_chunks: `['TXN_10k_2022.pdf::page_60::chunk_1', 'TXN_10k_2024.pdf::page_28::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_60::chunk_1'], 'hop_2': ['TXN_10k_2024.pdf::page_28::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.107 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['TXN_10k_2022.pdf::page_60::chunk_1']` | `{'hop_1': ['TXN_10k_2022.pdf::page_60::chunk_1'], 'hop_2': []}` | `['TXN_10k_2024.pdf::page_57::chunk_1', 'TXN_10k_2022.pdf::page_60::chunk_1', 'AMD_10k_2023.pdf::page_98::chunk_1', 'AMD_10k_2022.pdf::page_90::chunk_1', 'TXN_10k_2022.pdf::page_57::chunk_1']` |
| graph |  | 2.375 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2022.pdf::page_88::chunk_1', 'TXN_10k_2022.pdf::page_64::chunk_2', 'INTC_10k_2024.pdf::page_58::chunk_1', 'TXN_10k_2022.pdf::page_59::chunk_1', 'TXN_10k_2023.pdf::page_58::chunk_1']` |

### FRKG290: `As the Chief Financial Officer of Texas Instruments, Rafael R. Lizardi oversees financial reporting. What was the dollar amount and percentage increase in Texas Instruments' total revenue from 2020 to 2021, and how does this growth reflect the financial disclosures under his responsibility?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['rafael r. lizardi', 'txn', 'total revenue']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2022.pdf::page_69::chunk_2', 'TXN_10k_2022.pdf::page_33::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_69::chunk_2'], 'hop_2': ['TXN_10k_2022.pdf::page_33::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.116 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['QCOM_10k_2024.pdf::page_44::chunk_2', 'QCOM_10k_2023.pdf::page_44::chunk_2', 'NVDA_10k_2024.pdf::page_71::chunk_3', 'QCOM_10k_2022.pdf::page_43::chunk_2', 'QCOM_10k_2024.pdf::page_41::chunk_3']` |
| graph |  | 2.301 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_88::chunk_4', 'TXN_10k_2024.pdf::page_38::chunk_6', 'TXN_10k_2022.pdf::page_64::chunk_2', 'TXN_10k_2024.pdf::page_60::chunk_2', 'TXN_10k_2022.pdf::page_29::chunk_1']` |

### FRKG300: `What is the total revenue generated by the Other segment across the fiscal years 2022, 2023, and 2024, and how does this reflect the segment's role in including integration and restructuring charges over time?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embedded processing', 'txn', 'other segment', 'integration charges']`
- missing_gold_entities: `['embedded processing', 'integration charges']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2023.pdf::page_4::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2023.pdf::page_4::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.105 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['QCOM_10k_2023.pdf::page_42::chunk_4', 'QCOM_10k_2024.pdf::page_42::chunk_4', 'NVDA_10k_2023.pdf::page_79::chunk_5', 'INTC_10k_2023.pdf::page_92::chunk_5', 'NVDA_10k_2022.pdf::page_100::chunk_5']` |
| graph |  | 2.310 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'TXN_10k_2024.pdf::page_38::chunk_6', 'AVGO_10k_2023.pdf::page_90::chunk_1', 'AVGO_10k_2023.pdf::page_3::chunk_1', 'AVGO_10k_2024.pdf::page_65::chunk_9']` |

### FRKG356: `As a director of Qualcomm (QCOM), what role does Jeffrey W. Henderson play in overseeing the financial performance of the QCT segment, which reported revenues of $33.2 billion in fiscal 2024?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['jeffrey w. henderson', 'qcom', 'qct segment', 'revenues']`
- missing_gold_entities: `['revenues']`
- gold_chunks: `['QCOM_10k_2024.pdf::page_57::chunk_2', 'QCOM_10k_2024.pdf::page_73::chunk_5', 'QCOM_10k_2024.pdf::page_59::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['QCOM_10k_2024.pdf::page_57::chunk_2'], 'hop_2': ['QCOM_10k_2024.pdf::page_73::chunk_5'], 'hop_3': ['QCOM_10k_2024.pdf::page_59::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.104 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['QCOM_10k_2023.pdf::page_40::chunk_1', 'QCOM_10k_2024.pdf::page_40::chunk_1', 'QCOM_10k_2023.pdf::page_3::chunk_1', 'QCOM_10k_2023.pdf::page_73::chunk_6', 'QCOM_10k_2022.pdf::page_39::chunk_1']` |
| graph |  | 2.267 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['QCOM_10k_2024.pdf::page_13::chunk_1', 'QCOM_10k_2023.pdf::page_80::chunk_2', 'QCOM_10k_2023.pdf::page_17::chunk_1', 'QCOM_10k_2022.pdf::page_40::chunk_3', 'QCOM_10k_2022.pdf::page_5::chunk_1']` |

### FRKG357: `How do Intel's and NVIDIA's disclosures about non-recurring charges and benefits within their 'All Other' segments reflect differences in their corporate expense allocation strategies?`

- type: `2hop_inter_document_cross_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'all other', 'non-recurring charges and benefits']`
- missing_gold_entities: `['non-recurring charges and benefits']`
- gold_chunks: `['INTC_10k_2024.pdf::page_71::chunk_1', 'NVDA_10k_2024.pdf::page_78::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_71::chunk_1'], 'hop_2': ['NVDA_10k_2024.pdf::page_78::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.099 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['NVDA_10k_2024.pdf::page_79::chunk_1', 'NVDA_10k_2022.pdf::page_99::chunk_1', 'NVDA_10k_2023.pdf::page_78::chunk_1', 'NVDA_10k_2023.pdf::page_55::chunk_1', 'NVDA_10k_2022.pdf::page_71::chunk_1']` |
| graph |  | 2.475 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2023.pdf::page_49::chunk_2', 'INTC_10k_2024.pdf::page_76::chunk_2', 'INTC_10k_2024.pdf::page_60::chunk_2', 'INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2023.pdf::page_47::chunk_1']` |

### FRKG358: `What was the change in operating income (loss) for Intel's 'All Other' segment from 2023 to 2024, and how might this relate to the non-recurring charges typically disclosed in similar segments like NVIDIA's?`

- type: `2hop_inter_document_cross_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'all other', 'non-recurring charges and benefits']`
- missing_gold_entities: `['non-recurring charges and benefits']`
- gold_chunks: `['INTC_10k_2024.pdf::page_72::chunk_2', 'NVDA_10k_2024.pdf::page_78::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_72::chunk_2'], 'hop_2': ['NVDA_10k_2024.pdf::page_78::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.104 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2023.pdf::page_32::chunk_2', 'INTC_10k_2024.pdf::page_71::chunk_1', 'INTC_10k_2024.pdf::page_22::chunk_3', 'INTC_10k_2024.pdf::page_70::chunk_1']` |
| graph |  | 2.282 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2022.pdf::page_78::chunk_2', 'INTC_10k_2024.pdf::page_60::chunk_2', 'INTC_10k_2024.pdf::page_63::chunk_2', 'INTC_10k_2023.pdf::page_49::chunk_2']` |

### FRKG359: `As a director of Qualcomm, how does Sylvia Acevedo's role in signing the 2024 10-K filing relate to the QCT segment's $33.2 billion revenue disclosure and its audit considerations?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['sylvia acevedo', 'qcom', 'qct segment', 'revenues']`
- missing_gold_entities: `['revenues']`
- gold_chunks: `['QCOM_10k_2024.pdf::page_57::chunk_2', 'QCOM_10k_2024.pdf::page_59::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['QCOM_10k_2024.pdf::page_57::chunk_2'], 'hop_2': ['QCOM_10k_2024.pdf::page_59::chunk_1'], 'hop_3': ['QCOM_10k_2024.pdf::page_59::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.105 | 1 | 0.003 | 0.500 | 0.667 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['QCOM_10k_2024.pdf::page_59::chunk_1']` | `{'hop_1': [], 'hop_2': ['QCOM_10k_2024.pdf::page_59::chunk_1'], 'hop_3': ['QCOM_10k_2024.pdf::page_59::chunk_1']}` | `['QCOM_10k_2022.pdf::page_58::chunk_1', 'QCOM_10k_2024.pdf::page_59::chunk_1', 'QCOM_10k_2023.pdf::page_59::chunk_1', 'QCOM_10k_2023.pdf::page_40::chunk_1', 'QCOM_10k_2024.pdf::page_40::chunk_1']` |
| graph |  | 2.232 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['NVDA_10k_2023.pdf::page_9::chunk_1', 'NVDA_10k_2024.pdf::page_13::chunk_3', 'QCOM_10k_2023.pdf::page_17::chunk_1', 'QCOM_10k_2023.pdf::page_27::chunk_1', 'QCOM_10k_2023.pdf::page_81::chunk_1']` |

### FRKG360: `What was the increase in Qualcomm's QCT segment revenue in fiscal 2024, and how does this growth relate to customer incentive arrangements that affect other current liabilities, as disclosed in the financial statements signed by the CEO?`

- type: `3hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['cristiano r. amon', 'qcom', 'qct segment', 'other current liabilities']`
- missing_gold_entities: `['other current liabilities']`
- gold_chunks: `['QCOM_10k_2024.pdf::page_57::chunk_2', 'QCOM_10k_2023.pdf::page_41::chunk_3', 'QCOM_10k_2023.pdf::page_59::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['QCOM_10k_2024.pdf::page_57::chunk_2'], 'hop_2': ['QCOM_10k_2023.pdf::page_41::chunk_3'], 'hop_3': ['QCOM_10k_2023.pdf::page_59::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.114 | 1 | 0.005 | 0.333 | 0.333 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['QCOM_10k_2023.pdf::page_59::chunk_1']` | `{'hop_1': [], 'hop_2': [], 'hop_3': ['QCOM_10k_2023.pdf::page_59::chunk_1']}` | `['QCOM_10k_2023.pdf::page_59::chunk_1', 'QCOM_10k_2024.pdf::page_59::chunk_1', 'QCOM_10k_2022.pdf::page_58::chunk_1', 'QCOM_10k_2023.pdf::page_74::chunk_1', 'QCOM_10k_2024.pdf::page_74::chunk_1']` |
| graph |  | 2.481 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['QCOM_10k_2023.pdf::page_44::chunk_3', 'QCOM_10k_2024.pdf::page_44::chunk_3', 'QCOM_10k_2022.pdf::page_73::chunk_9', 'QCOM_10k_2023.pdf::page_73::chunk_7', 'QCOM_10k_2024.pdf::page_73::chunk_7']` |

### FRKG393: `What was the total revenue generated by the Other segment across 2021, 2022, and 2023, and how did its operating profit contribution change year-over-year when considering the segment's disclosed components?`

- type: `3hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['other', 'txn', '$1.25 billion revenue']`
- missing_gold_entities: `['$1.25 billion revenue']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_31::chunk_1', 'TXN_10k_2022.pdf::page_6::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_31::chunk_1'], 'hop_3': ['TXN_10k_2022.pdf::page_6::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.123 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_23::chunk_3', 'INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2024.pdf::page_22::chunk_3', 'TXN_10k_2023.pdf::page_20::chunk_6', 'TXN_10k_2023.pdf::page_20::chunk_4']` |
| graph |  | 2.308 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2022.pdf::page_23::chunk_1', 'TXN_10k_2024.pdf::page_38::chunk_6', 'AMD_10k_2024.pdf::page_68::chunk_7', 'INTC_10k_2022.pdf::page_27::chunk_4', 'INTC_10k_2023.pdf::page_50::chunk_1']` |

### FRKG395: `What was the dollar decrease in the Analog segment's operating profit from 2022 to 2023, and what percentage does this decrease represent of the total Goodwill allocated to the Analog segment?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['analog', 'txn', 'goodwill']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_31::chunk_1', 'TXN_10k_2024.pdf::page_52::chunk_8']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_31::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_52::chunk_8']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.113 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['TXN_10k_2023.pdf::page_20::chunk_1', 'TXN_10k_2023.pdf::page_20::chunk_3', 'TXN_10k_2023.pdf::page_20::chunk_7', 'TXN_10k_2024.pdf::page_20::chunk_1', 'TXN_10k_2022.pdf::page_55::chunk_6']` |
| graph |  | 2.304 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['TXN_10k_2022.pdf::page_33::chunk_2', 'TXN_10k_2023.pdf::page_3::chunk_1', 'TXN_10k_2024.pdf::page_3::chunk_1', 'TXN_10k_2023.pdf::page_5::chunk_3', 'TXN_10k_2022.pdf::page_29::chunk_1']` |

### FRKG396: `What was the total amount settled with tax authorities from 2019 to 2021, and how might this financial outflow influence Intel's reliance on government grants for semiconductor manufacturing expansions?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['tax authorities', 'intc', 'government grants']`
- missing_gold_entities: `['tax authorities', 'government grants']`
- gold_chunks: `['INTC_10k_2022.pdf::page_92::chunk_2', 'INTC_10k_2023.pdf::page_53::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2022.pdf::page_92::chunk_2'], 'hop_2': ['INTC_10k_2023.pdf::page_53::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.109 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2024.pdf::page_71::chunk_1', 'AVGO_10k_2022.pdf::page_103::chunk_6', 'INTC_10k_2024.pdf::page_25::chunk_3', 'TXN_10k_2023.pdf::page_21::chunk_1']` |
| graph |  | 2.267 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.333 | 1 | 0 | 1 | 1 | hit_top_k | `['INTC_10k_2022.pdf::page_92::chunk_2']` | `{'hop_1': ['INTC_10k_2022.pdf::page_92::chunk_2'], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2024.pdf::page_30::chunk_1', 'INTC_10k_2022.pdf::page_92::chunk_2', 'INTC_10k_2023.pdf::page_95::chunk_2', 'INTC_10k_2024.pdf::page_11::chunk_1']` |

### FRKG397: `How does the audit of internal control over financial reporting by Ernst & Young LLP relate to the disclosure of amortization expenses in AMD's non-reportable 'All Other' category?`

- type: `3hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['ernst & young llp', 'amd', 'all other category', 'amortization of acquisition-related intangibles']`
- missing_gold_entities: `['amortization of acquisition-related intangibles']`
- gold_chunks: `['AMD_10k_2022.pdf::page_88::chunk_1', 'AMD_10k_2024.pdf::page_6::chunk_1', 'AMD_10k_2024.pdf::page_69::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['AMD_10k_2022.pdf::page_88::chunk_1'], 'hop_2': ['AMD_10k_2024.pdf::page_6::chunk_1'], 'hop_3': ['AMD_10k_2024.pdf::page_69::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.105 | 1 | 0.005 | 0.333 | 0.333 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['AMD_10k_2022.pdf::page_88::chunk_1']` | `{'hop_1': ['AMD_10k_2022.pdf::page_88::chunk_1'], 'hop_2': [], 'hop_3': []}` | `['AMD_10k_2022.pdf::page_88::chunk_1', 'AMD_10k_2023.pdf::page_95::chunk_1', 'AMD_10k_2023.pdf::page_98::chunk_1', 'INTC_10k_2024.pdf::page_58::chunk_1', 'AMD_10k_2024.pdf::page_92::chunk_1']` |
| graph |  | 2.445 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2023.pdf::page_117::chunk_1', 'INTC_10k_2022.pdf::page_47::chunk_1', 'INTC_10k_2022.pdf::page_116::chunk_1', 'INTC_10k_2023.pdf::page_75::chunk_1', 'INTC_10k_2024.pdf::page_104::chunk_1']` |

### FRKG405: `How does the audit opinion from Ernst & Young LLP on Intel's internal controls influence the transparency of corporate infrastructure cost disclosures, and what does this reveal about similar segment reporting practices in NVIDIA's financial statements?`

- type: `3hop_inter_document_cross_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['ernst & young llp', 'intc', 'all other', 'corporate infrastructure and support costs']`
- missing_gold_entities: `['corporate infrastructure and support costs']`
- gold_chunks: `['INTC_10k_2024.pdf::page_58::chunk_1', 'INTC_10k_2024.pdf::page_70::chunk_1', 'NVDA_10k_2024.pdf::page_78::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_58::chunk_1'], 'hop_2': ['INTC_10k_2024.pdf::page_70::chunk_1'], 'hop_3': ['NVDA_10k_2024.pdf::page_78::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.092 | 1 | 0.005 | 0.333 | 0.333 | 0 | 1.000 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_10k_2024.pdf::page_58::chunk_1']` | `{'hop_1': ['INTC_10k_2024.pdf::page_58::chunk_1'], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_58::chunk_1', 'INTC_10k_2023.pdf::page_75::chunk_1', 'INTC_10k_2022.pdf::page_73::chunk_1', 'NVDA_10k_2022.pdf::page_62::chunk_1', 'NVDA_10k_2023.pdf::page_48::chunk_1']` |
| graph |  | 2.239 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2023.pdf::page_117::chunk_1', 'TXN_10k_2022.pdf::page_60::chunk_1', 'INTC_10k_2022.pdf::page_116::chunk_1', 'INTC_10k_2024.pdf::page_104::chunk_1', 'INTC_10k_2023.pdf::page_75::chunk_1']` |

### FRKG436: `As Chair of the Board in 2024, how does Mark D. McLaughlin's role at Qualcomm relate to the $10.4 billion equipment/services revenue increase in the QCT segment during fiscal 2022, considering the segment's revenue recognition methods disclosed in 2023?`

- type: `3hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['mark d. mclaughlin', 'qcom', 'qct segment', 'revenue']`
- missing_gold_entities: `[]`
- gold_chunks: `['QCOM_10k_2024.pdf::page_57::chunk_2', 'QCOM_10k_2022.pdf::page_40::chunk_3', 'QCOM_10k_2023.pdf::page_73::chunk_5']`
- gold_evidence_groups: `{'hop_1': ['QCOM_10k_2024.pdf::page_57::chunk_2'], 'hop_2': ['QCOM_10k_2022.pdf::page_40::chunk_3'], 'hop_3': ['QCOM_10k_2023.pdf::page_73::chunk_5']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.120 | 1 | 0.005 | 0.333 | 0.333 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['QCOM_10k_2022.pdf::page_40::chunk_3']` | `{'hop_1': [], 'hop_2': ['QCOM_10k_2022.pdf::page_40::chunk_3'], 'hop_3': []}` | `['QCOM_10k_2023.pdf::page_41::chunk_3', 'QCOM_10k_2022.pdf::page_40::chunk_3', 'QCOM_10k_2024.pdf::page_41::chunk_3', 'QCOM_10k_2023.pdf::page_40::chunk_1', 'QCOM_10k_2024.pdf::page_40::chunk_1']` |
| graph |  | 2.241 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | 0 | 1 | 1 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['QCOM_10k_2023.pdf::page_44::chunk_3', 'QCOM_10k_2024.pdf::page_44::chunk_3', 'QCOM_10k_2024.pdf::page_13::chunk_1', 'QCOM_10k_2022.pdf::page_40::chunk_1', 'QCOM_10k_2023.pdf::page_17::chunk_1']` |

### FRKG437: `What was the total revenue of Qualcomm's QCT segment in fiscal 2024, and by how much did this represent an increase from fiscal 2023?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['qcom', 'qct segment', 'revenues']`
- missing_gold_entities: `['revenues']`
- gold_chunks: `['QCOM_10k_2023.pdf::page_41::chunk_3', 'QCOM_10k_2023.pdf::page_59::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['QCOM_10k_2023.pdf::page_41::chunk_3'], 'hop_2': ['QCOM_10k_2023.pdf::page_59::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.101 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['QCOM_10k_2023.pdf::page_41::chunk_3']` | `{'hop_1': ['QCOM_10k_2023.pdf::page_41::chunk_3'], 'hop_2': []}` | `['QCOM_10k_2023.pdf::page_41::chunk_1', 'QCOM_10k_2024.pdf::page_41::chunk_1', 'QCOM_10k_2023.pdf::page_41::chunk_3', 'QCOM_10k_2024.pdf::page_41::chunk_3', 'QCOM_10k_2023.pdf::page_73::chunk_6']` |
| graph |  | 2.469 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['QCOM_10k_2023.pdf::page_44::chunk_3', 'QCOM_10k_2024.pdf::page_44::chunk_3', 'QCOM_10k_2022.pdf::page_40::chunk_1', 'QCOM_10k_2022.pdf::page_73::chunk_6', 'QCOM_10k_2023.pdf::page_73::chunk_6']` |

### FRKG451: `What is the combined monetary decrease in revenue for both the Analog and Other segments from 2022 to 2024, and how does this decline relate to the changes in restructuring charges disclosed in the Other segment's financial results?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['analog', 'txn', 'other segment', '$947 million revenue']`
- missing_gold_entities: `['$947 million revenue']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_30::chunk_2', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_30::chunk_2'], 'hop_3': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.102 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['TXN_10k_2023.pdf::page_20::chunk_3', 'TXN_10k_2023.pdf::page_20::chunk_7', 'TXN_10k_2024.pdf::page_20::chunk_7', 'TXN_10k_2024.pdf::page_20::chunk_1', 'TXN_10k_2023.pdf::page_20::chunk_1']` |
| graph |  | 2.379 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['TXN_10k_2023.pdf::page_3::chunk_1', 'TXN_10k_2023.pdf::page_20::chunk_3', 'TXN_10k_2024.pdf::page_3::chunk_1', 'INTC_10k_2022.pdf::page_33::chunk_1', 'INTC_10k_2024.pdf::page_73::chunk_4']` |

### FRKG455: `What was the total operating income increase for AVGO from fiscal 2021 to 2022, and how does PricewaterhouseCoopers' audit evaluation of uncertain tax positions relate to the reliability of the Infrastructure Software segment's reported operating income growth that contributes to this total?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['pricewaterhousecoopers llp', 'avgo', 'infrastructure software', 'operating income']`
- missing_gold_entities: `['operating income']`
- gold_chunks: `['AVGO_10k_2022.pdf::page_79::chunk_1', 'AVGO_10k_2022.pdf::page_71::chunk_4']`
- gold_evidence_groups: `{'hop_1': ['AVGO_10k_2022.pdf::page_79::chunk_1'], 'hop_2': ['AVGO_10k_2022.pdf::page_71::chunk_4'], 'hop_3': ['AVGO_10k_2022.pdf::page_71::chunk_4']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.131 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['AVGO_10k_2024.pdf::page_45::chunk_5', 'AVGO_10k_2023.pdf::page_45::chunk_5', 'AVGO_10k_2022.pdf::page_71::chunk_5', 'AVGO_10k_2023.pdf::page_48::chunk_3', 'AVGO_10k_2024.pdf::page_48::chunk_3']` |
| graph |  | 2.359 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2022.pdf::page_27::chunk_4', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1', 'INTC_10k_2022.pdf::page_54::chunk_1', 'INTC_10k_2022.pdf::page_120::chunk_1']` |

### FRKG456: `What is the effective tax rate contribution from changes in uncertain tax positions for Texas Instruments in 2024, and how does this relate to Rafael R. Lizardi's responsibilities as Chief Financial Officer?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['rafael r. lizardi', 'txn', 'changes in uncertain tax positions']`
- missing_gold_entities: `['changes in uncertain tax positions']`
- gold_chunks: `['TXN_10k_2022.pdf::page_69::chunk_2', 'TXN_10k_2024.pdf::page_38::chunk_10']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_69::chunk_2'], 'hop_2': ['TXN_10k_2024.pdf::page_38::chunk_10']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.117 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2024.pdf::page_64::chunk_1', 'TXN_10k_2022.pdf::page_68::chunk_1', 'TXN_10k_2023.pdf::page_66::chunk_1', 'TXN_10k_2022.pdf::page_42::chunk_3', 'TXN_10k_2024.pdf::page_40::chunk_1']` |
| graph |  | 2.266 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2022.pdf::page_64::chunk_2', 'TXN_10k_2024.pdf::page_40::chunk_3', 'TXN_10k_2023.pdf::page_41::chunk_3', 'TXN_10k_2023.pdf::page_39::chunk_4', 'TXN_10k_2022.pdf::page_41::chunk_5']` |

### FRKG458: `As a director who signed Intel's 2024 10-K filing, how does Eric Meurice's role relate to the litigation charges disclosed in the company's 2023 financial statements?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['eric meurice', 'intc', 'litigation charges and other']`
- missing_gold_entities: `['litigation charges and other']`
- gold_chunks: `['INTC_10k_2024.pdf::page_111::chunk_1', 'INTC_10k_2023.pdf::page_43::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_111::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_43::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.106 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_112::chunk_1', 'INTC_10k_2022.pdf::page_1::chunk_1', 'INTC_10k_2023.pdf::page_1::chunk_1', 'INTC_10k_2024.pdf::page_101::chunk_1', 'INTC_10k_2023.pdf::page_124::chunk_2']` |
| graph |  | 2.465 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2024.pdf::page_28::chunk_3', 'INTC_10k_2022.pdf::page_43::chunk_3', 'INTC_10k_2023.pdf::page_17::chunk_1', 'INTC_10k_2023.pdf::page_43::chunk_3']` |

### FRKG463: `What was the total revenue decline in Texas Instruments' 'Other' segment from 2022 to 2024, and how did restructuring charges in 2022 and the inclusion of litigation expenses influence this trend?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['other', 'txn', 'other segment', 'litigation expenses']`
- missing_gold_entities: `['litigation expenses']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.095 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['QCOM_10k_2023.pdf::page_42::chunk_4', 'QCOM_10k_2024.pdf::page_42::chunk_4', 'INTC_10k_2024.pdf::page_28::chunk_3', 'TXN_10k_2024.pdf::page_30::chunk_2', 'INTC_10k_2023.pdf::page_43::chunk_3']` |
| graph |  | 2.263 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2022.pdf::page_33::chunk_1', 'INTC_10k_2022.pdf::page_24::chunk_2', 'INTC_10k_2023.pdf::page_25::chunk_1', 'INTC_10k_2024.pdf::page_94::chunk_2']` |

### FRKG515: `What was the unrecognized tax benefit at the end of 2021, and how did this compare to the Non-Volatile Memory Solutions Group's net revenue and operating income for the same period?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['tax authorities', 'intc', 'non-volatile memory solutions group', 'net revenue']`
- missing_gold_entities: `['tax authorities', 'non-volatile memory solutions group']`
- gold_chunks: `['INTC_10k_2022.pdf::page_92::chunk_2', 'INTC_10k_2022.pdf::page_86::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2022.pdf::page_92::chunk_2'], 'hop_2': ['INTC_10k_2022.pdf::page_86::chunk_2'], 'hop_3': ['INTC_10k_2022.pdf::page_86::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.098 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['AMD_10k_2022.pdf::page_76::chunk_5', 'NVDA_10k_2024.pdf::page_77::chunk_3', 'QCOM_10k_2022.pdf::page_77::chunk_1', 'NVDA_10k_2023.pdf::page_77::chunk_3', 'AMD_10k_2023.pdf::page_89::chunk_3']` |
| graph |  | 2.326 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2023.pdf::page_95::chunk_3', 'INTC_10k_2024.pdf::page_83::chunk_3', 'INTC_10k_2022.pdf::page_92::chunk_3', 'QCOM_10k_2022.pdf::page_77::chunk_3', 'QCOM_10k_2024.pdf::page_77::chunk_3']` |

### FRKG516: `How does the SEC's regulatory framework connect to AMD's disclosure of interest expense, involving executive authorizations like those for Kirsten M. Spears?`

- type: `3hop_inter_document_cross_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['kirsten m. spears', 'sec', 'amd', 'interest expense']`
- missing_gold_entities: `['kirsten m. spears']`
- gold_chunks: `['AVGO_10k_2022.pdf::page_140::chunk_1', 'AMD_10k_2024.pdf::page_2::chunk_1', 'AMD_10k_2024.pdf::page_51::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['AVGO_10k_2022.pdf::page_140::chunk_1'], 'hop_2': ['AMD_10k_2024.pdf::page_2::chunk_1'], 'hop_3': ['AMD_10k_2024.pdf::page_51::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.098 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['AMD_10k_2024.pdf::page_96::chunk_1', 'AMD_10k_2022.pdf::page_97::chunk_2', 'QCOM_10k_2023.pdf::page_70::chunk_1', 'QCOM_10k_2024.pdf::page_70::chunk_1', 'INTC_10k_2023.pdf::page_71::chunk_1']` |
| graph |  | 2.448 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['AMD_10k_2022.pdf::page_93::chunk_1', 'AMD_10k_2022.pdf::page_2::chunk_1', 'AMD_10k_2023.pdf::page_108::chunk_2', 'AMD_10k_2023.pdf::page_99::chunk_1', 'AMD_10k_2024.pdf::page_96::chunk_1']` |

### FRKG517: `What was the total number of shares repurchased by Texas Instruments during Haviv Ilan's directorship as disclosed in the 10-K filings from 2022 to 2024?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['haviv ilan', 'txn', 'opening balance']`
- missing_gold_entities: `['opening balance']`
- gold_chunks: `['TXN_10k_2022.pdf::page_69::chunk_2', 'TXN_10k_2024.pdf::page_38::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_69::chunk_2'], 'hop_2': ['TXN_10k_2024.pdf::page_38::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.110 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2023.pdf::page_67::chunk_1', 'TXN_10k_2024.pdf::page_64::chunk_1', 'TXN_10k_2024.pdf::page_59::chunk_3', 'TXN_10k_2022.pdf::page_68::chunk_1', 'TXN_10k_2023.pdf::page_66::chunk_1']` |
| graph |  | 2.181 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1', 'INTC_10k_2022.pdf::page_54::chunk_1', 'INTC_10k_2022.pdf::page_120::chunk_1', 'INTC_10k_2022.pdf::page_23::chunk_1']` |

### FRKG520: `What is the ratio of Embedded Processing segment's 2022 revenue to the increase in Other segment's revenue from 2021 to 2022?`

- type: `3hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embedded processing', 'txn', 'other', '$1.25 billion revenue']`
- missing_gold_entities: `['embedded processing', '$1.25 billion revenue']`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2022.pdf::page_6::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2022.pdf::page_6::chunk_1'], 'hop_3': ['TXN_10k_2022.pdf::page_6::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.095 | 1 | 0.003 | 0.500 | 0.667 | 0 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['TXN_10k_2022.pdf::page_6::chunk_1']` | `{'hop_1': [], 'hop_2': ['TXN_10k_2022.pdf::page_6::chunk_1'], 'hop_3': ['TXN_10k_2022.pdf::page_6::chunk_1']}` | `['INTC_10k_2024.pdf::page_22::chunk_3', 'INTC_10k_2024.pdf::page_19::chunk_3', 'TXN_10k_2022.pdf::page_33::chunk_2', 'TXN_10k_2022.pdf::page_6::chunk_1', 'TXN_10k_2023.pdf::page_4::chunk_1']` |
| graph |  | 2.372 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_88::chunk_4', 'INTC_10k_2023.pdf::page_26::chunk_3', 'INTC_10k_2023.pdf::page_3::chunk_1', 'INTC_10k_2022.pdf::page_3::chunk_1', 'INTC_10k_2023.pdf::page_50::chunk_1']` |

### FRKG522: `What was Qualcomm's Research and Development expenditure in 2024, and which director's signature appears on the 10-K filing that disclosed this metric?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['sylvia acevedo', 'qcom', 'research and development']`
- missing_gold_entities: `[]`
- gold_chunks: `['QCOM_10k_2024.pdf::page_57::chunk_2', 'QCOM_10k_2024.pdf::page_61::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['QCOM_10k_2024.pdf::page_57::chunk_2'], 'hop_2': ['QCOM_10k_2024.pdf::page_61::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.103 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['QCOM_10k_2024.pdf::page_3::chunk_1', 'QCOM_10k_2023.pdf::page_3::chunk_1', 'QCOM_10k_2023.pdf::page_56::chunk_1', 'QCOM_10k_2022.pdf::page_3::chunk_1', 'QCOM_10k_2024.pdf::page_65::chunk_1']` |
| graph |  | 2.407 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | 0 | 1 | 1 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['QCOM_10k_2024.pdf::page_13::chunk_1', 'QCOM_10k_2023.pdf::page_41::chunk_7', 'QCOM_10k_2022.pdf::page_83::chunk_3', 'QCOM_10k_2022.pdf::page_43::chunk_3', 'QCOM_10k_2023.pdf::page_17::chunk_1']` |

### FRKG523: `How does the SEC's regulatory framework influence AMD's disclosure of expected volatility assumptions in its stock option valuations?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['sec', 'amd', 'historical volatility']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_10k_2024.pdf::page_2::chunk_1', 'AMD_10k_2024.pdf::page_81::chunk_5']`
- gold_evidence_groups: `{'hop_1': ['AMD_10k_2024.pdf::page_2::chunk_1'], 'hop_2': ['AMD_10k_2024.pdf::page_81::chunk_5']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.087 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2024.pdf::page_96::chunk_1', 'QCOM_10k_2022.pdf::page_36::chunk_1', 'NVDA_10k_2024.pdf::page_32::chunk_1', 'AMD_10k_2022.pdf::page_42::chunk_3', 'TXN_10k_2022.pdf::page_38::chunk_3']` |
| graph |  | 2.278 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['QCOM_10k_2022.pdf::page_57::chunk_1', 'QCOM_10k_2024.pdf::page_48::chunk_1', 'QCOM_10k_2022.pdf::page_3::chunk_2', 'QCOM_10k_2023.pdf::page_3::chunk_2', 'QCOM_10k_2024.pdf::page_3::chunk_2']` |

### FRKG525: `What total Xilinx acquisition costs in 2022 and 2023 demonstrate AMD's compliance with SEC disclosure requirements, and how does the role of attorneys-in-fact facilitate this regulatory alignment?`

- type: `3hop_inter_document_cross_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['attorney-in-fact', 'sec', 'amd', 'xilinx acquisition costs']`
- missing_gold_entities: `['xilinx acquisition costs']`
- gold_chunks: `['AVGO_10k_2023.pdf::page_104::chunk_1', 'AMD_10k_2022.pdf::page_5::chunk_1', 'AMD_10k_2024.pdf::page_73::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['AVGO_10k_2023.pdf::page_104::chunk_1'], 'hop_2': ['AMD_10k_2022.pdf::page_5::chunk_1'], 'hop_3': ['AMD_10k_2024.pdf::page_73::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.104 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['AMD_10k_2023.pdf::page_75::chunk_5', 'AMD_10k_2023.pdf::page_101::chunk_2', 'AMD_10k_2022.pdf::page_6::chunk_1', 'AMD_10k_2023.pdf::page_76::chunk_5', 'AMD_10k_2022.pdf::page_83::chunk_1']` |
| graph |  | 2.353 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['AMD_10k_2022.pdf::page_83::chunk_1', 'AMD_10k_2022.pdf::page_34::chunk_1', 'AMD_10k_2022.pdf::page_35::chunk_1', 'AMD_10k_2022.pdf::page_33::chunk_1', 'AMD_10k_2022.pdf::page_6::chunk_1']` |

### FRKG528: `What was the change in Texas Instruments' U.S. Defined Benefit plan discount rate from 2020 to 2021, and how does this reflect the company's financial reporting under the oversight of its Chief Financial Officer?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['rafael r. lizardi', 'txn', 'discount rate 2.74%']`
- missing_gold_entities: `['discount rate 2.74%']`
- gold_chunks: `['TXN_10k_2022.pdf::page_69::chunk_2', 'TXN_10k_2022.pdf::page_49::chunk_3']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2022.pdf::page_69::chunk_2'], 'hop_2': ['TXN_10k_2022.pdf::page_49::chunk_3']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.102 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2022.pdf::page_60::chunk_1', 'TXN_10k_2024.pdf::page_57::chunk_1', 'QCOM_10k_2022.pdf::page_77::chunk_1', 'TXN_10k_2022.pdf::page_63::chunk_3', 'TXN_10k_2022.pdf::page_57::chunk_1']` |
| graph |  | 2.359 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2022.pdf::page_64::chunk_2', 'TXN_10k_2024.pdf::page_60::chunk_2', 'TXN_10k_2023.pdf::page_44::chunk_1', 'TXN_10k_2022.pdf::page_39::chunk_2', 'TXN_10k_2024.pdf::page_47::chunk_2']` |

### FRKG529: `What role does PricewaterhouseCoopers LLP's audit process play in validating Qualcomm's QCT segment revenue recognition practices, particularly regarding customer incentive arrangements, and how does this relate to the segment's revenue disclosure of $37.7 billion in fiscal 2022?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['pricewaterhousecoopers llp', 'qcom', 'qct segment', 'revenues']`
- missing_gold_entities: `['revenues']`
- gold_chunks: `['QCOM_10k_2022.pdf::page_58::chunk_1', 'QCOM_10k_2024.pdf::page_73::chunk_5']`
- gold_evidence_groups: `{'hop_1': ['QCOM_10k_2022.pdf::page_58::chunk_1'], 'hop_2': ['QCOM_10k_2024.pdf::page_73::chunk_5'], 'hop_3': ['QCOM_10k_2022.pdf::page_58::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.125 | 1 | 0.003 | 0.500 | 0.667 | 0 | 0.500 | 1 | n/a | n/a | n/a | not_applicable | `['QCOM_10k_2022.pdf::page_58::chunk_1']` | `{'hop_1': ['QCOM_10k_2022.pdf::page_58::chunk_1'], 'hop_2': [], 'hop_3': ['QCOM_10k_2022.pdf::page_58::chunk_1']}` | `['QCOM_10k_2023.pdf::page_59::chunk_1', 'QCOM_10k_2022.pdf::page_58::chunk_1', 'QCOM_10k_2024.pdf::page_59::chunk_1', 'QCOM_10k_2023.pdf::page_40::chunk_1', 'QCOM_10k_2024.pdf::page_40::chunk_1']` |
| graph |  | 2.391 | 1 | 0.003 | 0.500 | 0.667 | 0 | 0.200 | 1 | 1 | 1 | 1 | hit_top_k | `['QCOM_10k_2022.pdf::page_58::chunk_1']` | `{'hop_1': ['QCOM_10k_2022.pdf::page_58::chunk_1'], 'hop_2': [], 'hop_3': ['QCOM_10k_2022.pdf::page_58::chunk_1']}` | `['QCOM_10k_2023.pdf::page_44::chunk_3', 'QCOM_10k_2024.pdf::page_44::chunk_3', 'QCOM_10k_2023.pdf::page_50::chunk_1', 'QCOM_10k_2024.pdf::page_50::chunk_1', 'QCOM_10k_2022.pdf::page_58::chunk_1']` |

### FRKG531: `What is the combined total of non-recurring charges and benefits disclosed in both Intel's 'All Other' segment and NVIDIA's 'All Other' category, and how does CDP's role in corporate environmental disclosures contextualize these financial adjustments?`

- type: `3hop_inter_document_cross_company`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['cdp', 'intc', 'all other', 'non-recurring charges and benefits']`
- missing_gold_entities: `['non-recurring charges and benefits']`
- gold_chunks: `['INTC_10k_2024.pdf::page_102::chunk_2', 'INTC_10k_2024.pdf::page_70::chunk_1', 'NVDA_10k_2024.pdf::page_78::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_102::chunk_2'], 'hop_2': ['INTC_10k_2024.pdf::page_70::chunk_1'], 'hop_3': ['NVDA_10k_2024.pdf::page_78::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.123 | 1 | 0.005 | 0.333 | 0.333 | 0 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_10k_2024.pdf::page_78::chunk_1']` | `{'hop_1': [], 'hop_2': [], 'hop_3': ['NVDA_10k_2024.pdf::page_78::chunk_1']}` | `['NVDA_10k_2022.pdf::page_99::chunk_1', 'NVDA_10k_2024.pdf::page_79::chunk_1', 'NVDA_10k_2023.pdf::page_78::chunk_1', 'NVDA_10k_2024.pdf::page_78::chunk_1', 'NVDA_10k_2022.pdf::page_69::chunk_1']` |
| graph |  | 2.375 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['TXN_10k_2022.pdf::page_54::chunk_2', 'INTC_10k_2022.pdf::page_89::chunk_1', 'INTC_10k_2023.pdf::page_43::chunk_1', 'INTC_10k_2023.pdf::page_43::chunk_2', 'INTC_10k_2024.pdf::page_28::chunk_2']` |

### FRKG533: `What is the relationship between AMD's non-cash adjustments of $3.9 billion and its net cash provided by operating activities of $1.7 billion, and how does the involvement of Ernst & Young LLP as long-standing auditor ensure the reliability of these financial disclosures?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `missing_gold_entities`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['ernst & young llp', 'amd', 'non-cash adjustments']`
- missing_gold_entities: `['non-cash adjustments']`
- gold_chunks: `['AMD_10k_2023.pdf::page_94::chunk_3', 'AMD_10k_2023.pdf::page_54::chunk_3']`
- gold_evidence_groups: `{'hop_1': ['AMD_10k_2023.pdf::page_94::chunk_3'], 'hop_2': ['AMD_10k_2023.pdf::page_54::chunk_3']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.131 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2022.pdf::page_43::chunk_1', 'AMD_10k_2024.pdf::page_46::chunk_1', 'AVGO_10k_2023.pdf::page_48::chunk_3', 'AVGO_10k_2024.pdf::page_48::chunk_3', 'NVDA_10k_2023.pdf::page_34::chunk_1']` |
| graph |  | 2.355 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_6::chunk_1', 'INTC_10k_2023.pdf::page_49::chunk_5', 'INTC_10k_2024.pdf::page_31::chunk_3', 'INTC_10k_2022.pdf::page_44::chunk_1', 'INTC_10k_2022.pdf::page_49::chunk_4']` |

### FRKG534: `How does the PCAOB's oversight of AMD's audit process influence the transparency of employee stock-based compensation expenses disclosed in AMD's All Other category?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['pcaob', 'amd', 'all other category', 'employee stock-based compensation']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_10k_2024.pdf::page_90::chunk_1', 'AMD_10k_2024.pdf::page_6::chunk_1', 'AMD_10k_2024.pdf::page_69::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['AMD_10k_2024.pdf::page_90::chunk_1'], 'hop_2': ['AMD_10k_2024.pdf::page_6::chunk_1'], 'hop_3': ['AMD_10k_2024.pdf::page_69::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| vector |  | 0.135 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['AMD_10k_2022.pdf::page_86::chunk_1', 'AMD_10k_2023.pdf::page_93::chunk_1', 'AMD_10k_2023.pdf::page_95::chunk_1', 'AMD_10k_2022.pdf::page_88::chunk_1', 'AMD_10k_2024.pdf::page_96::chunk_1']` |
| graph |  | 2.670 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | 1 | rerank_loss | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1', 'INTC_10k_2022.pdf::page_54::chunk_1', 'INTC_10k_2022.pdf::page_120::chunk_1', 'INTC_10k_2022.pdf::page_23::chunk_1']` |
