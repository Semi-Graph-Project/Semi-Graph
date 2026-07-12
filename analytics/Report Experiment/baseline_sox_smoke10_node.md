# Phase T Retrieval Baseline

Generated: 2026-07-10T19:51:25

## Run Configuration

- script: `scripts/evaluate_retrieval_quality.py`
- command: `scripts/evaluate_retrieval_quality.py --queries data/evaluate/finreflectkg_sox_smoke10.yaml --tools vector graph --top-k 5 --oracle-k 20 --no-llm-expansion --graph-seed-mode node --candidate-pool-k 100 --graph-top-k-entities 40 --graph-damping 0.5 --reextract-tickers AMD,AVGO,INTC,NVDA,QCOM,TXN --version-name finreflectkg_sox_smoke10_node_ppr`
- query_file: `data/evaluate/finreflectkg_sox_smoke10.yaml`
- query_count: `10`
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
- version_name: `finreflectkg_sox_smoke10_node_ppr`
- details_jsonl: `/home/kantinan/programming/project/analytics/Report Experiment/details_sox_smoke10_node.jsonl`
- reextract_tickers_arg: `AMD,AVGO,INTC,NVDA,QCOM,TXN`
- resolved_ticker_scope: `AMD, AVGO, INTC, NVDA, QCOM, TXN`
- known_tickers: `AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN`
- scored_queries: `10`
- unscored_queries: `0`
- existing_gold_entities: `14`
- total_gold_entities: `21`

## Overall

| Tool | Scored Queries | Errors | ChunkHit@k | Random ChunkHit@k | Hit Lift | Hit-Random | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vector | 10 | 0 | 0.300 | 0.004 | 84.881 | 0.296 | 0.117 | 0.117 | 0.000 | 0.078 | 0.400 |
| graph | 10 | 0 | 0.000 | 0.004 | 0.000 | -0.004 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## By Type

| Type | vector ChunkHit | vector ChunkRecall | vector GroupRecall | vector Answerable | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2hop_inter_document_same_company | 0.200 | 0.100 | 0.100 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2hop_intra_document | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3hop_inter_document_cross_company | 1.000 | 0.333 | 0.333 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3hop_inter_document_same_company | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3hop_intra_document | 1.000 | 0.333 | 0.333 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## By Subset

| Subset | vector ChunkHit | vector ChunkRecall | vector GroupRecall | vector Answerable | vector Oracle | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable | graph Oracle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| reextract_subset | 0.300 | 0.117 | 0.117 | 0.000 | 0.400 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | Bottlenecks |
|---|---:|---:|---:|---|
| full_mixed | 0.100 | 1.000 | 0.300 | chunk_mapping_loss=1, corpus_not_ready=7, seed_loss=2 |
| reextract_subset | 0.100 | 1.000 | 0.300 | chunk_mapping_loss=1, corpus_not_ready=7, seed_loss=2 |

## Paired GroupRecall Test vs Vector

| Subset | Tool | n | Mean Delta GroupRecall | One-sided p |
|---|---|---:|---:|---:|
| full_mixed | graph | 10 | -0.117 | 1.000 |
| reextract_subset | graph | 10 | -0.117 | 1.000 |

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
| vector |  | 9.285 | 1 | 0.005 | 0.333 | 0.333 | 0 | 0.250 | 1 | n/a | n/a | n/a | not_applicable | `['NVDA_10k_2024.pdf::page_78::chunk_1']` | `{'hop_1': [], 'hop_2': [], 'hop_3': ['NVDA_10k_2024.pdf::page_78::chunk_1']}` | `['NVDA_10k_2022.pdf::page_99::chunk_1', 'NVDA_10k_2023.pdf::page_78::chunk_1', 'NVDA_10k_2024.pdf::page_79::chunk_1', 'NVDA_10k_2024.pdf::page_78::chunk_1', 'AMD_10k_2023.pdf::page_70::chunk_1']` |
| graph |  | 7.472 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | 0 | chunk_mapping_loss | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2022.pdf::page_54::chunk_1', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1', 'INTC_10k_2022.pdf::page_120::chunk_1', 'INTC_10k_2022.pdf::page_23::chunk_1']` |

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
| vector |  | 0.141 | 1 | 0.005 | 0.333 | 0.333 | 0 | 0.200 | 1 | n/a | n/a | n/a | not_applicable | `['TXN_10k_2023.pdf::page_30::chunk_1']` | `{'hop_1': [], 'hop_2': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_3': []}` | `['TXN_10k_2023.pdf::page_4::chunk_1', 'TXN_10k_2022.pdf::page_6::chunk_1', 'INTC_10k_2024.pdf::page_22::chunk_3', 'TXN_10k_2022.pdf::page_32::chunk_1', 'TXN_10k_2023.pdf::page_30::chunk_1']` |
| graph |  | 2.774 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2023.pdf::page_43::chunk_2', 'INTC_10k_2024.pdf::page_28::chunk_2', 'INTC_10k_2022.pdf::page_43::chunk_2', 'INTC_10k_2023.pdf::page_92::chunk_4']` |

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
| vector |  | 0.151 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 1 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2024.pdf::page_22::chunk_3', 'INTC_10k_2024.pdf::page_16::chunk_1', 'TXN_10k_2022.pdf::page_33::chunk_2', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2024.pdf::page_19::chunk_3']` |
| graph |  | 2.911 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2022.pdf::page_27::chunk_4', 'INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2023.pdf::page_50::chunk_1', 'INTC_10k_2024.pdf::page_17::chunk_1', 'INTC_10k_2022.pdf::page_54::chunk_1']` |

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
| vector |  | 0.142 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2024.pdf::page_85::chunk_3', 'AMD_10k_2023.pdf::page_88::chunk_3', 'NVDA_10k_2024.pdf::page_32::chunk_1', 'AMD_10k_2024.pdf::page_85::chunk_1', 'AMD_10k_2024.pdf::page_73::chunk_5']` |
| graph |  | 2.412 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['NVDA_10k_2024.pdf::page_39::chunk_1', 'NVDA_10k_2023.pdf::page_37::chunk_1', 'NVDA_10k_2024.pdf::page_76::chunk_2', 'NVDA_10k_2022.pdf::page_72::chunk_1', 'NVDA_10k_2022.pdf::page_49::chunk_1']` |

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
| vector |  | 0.119 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2023.pdf::page_20::chunk_4', 'QCOM_10k_2024.pdf::page_73::chunk_6', 'QCOM_10k_2022.pdf::page_40::chunk_3', 'TXN_10k_2023.pdf::page_20::chunk_6', 'TXN_10k_2023.pdf::page_20::chunk_2']` |
| graph |  | 2.560 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_32::chunk_1', 'INTC_10k_2023.pdf::page_97::chunk_4', 'TXN_10k_2024.pdf::page_38::chunk_6', 'INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2022.pdf::page_95::chunk_2']` |

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
| vector |  | 0.150 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_79::chunk_5', 'INTC_10k_2024.pdf::page_28::chunk_3', 'AVGO_10k_2024.pdf::page_93::chunk_3', 'AVGO_10k_2023.pdf::page_93::chunk_3', 'AMD_10k_2024.pdf::page_73::chunk_5']` |
| graph |  | 2.701 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2024.pdf::page_30::chunk_1', 'INTC_10k_2024.pdf::page_27::chunk_1', 'INTC_10k_2024.pdf::page_28::chunk_3']` |

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
| vector |  | 0.129 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2024.pdf::page_26::chunk_1', 'INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2024.pdf::page_22::chunk_3']` |
| graph |  | 2.512 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_73::chunk_4', 'INTC_10k_2023.pdf::page_89::chunk_2', 'INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2023.pdf::page_22::chunk_1', 'INTC_10k_2023.pdf::page_49::chunk_2']` |

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
| vector |  | 0.120 | 1 | 0.003 | 0.500 | 0.500 | 0 | 0.333 | 1 | n/a | n/a | n/a | not_applicable | `['INTC_10k_2024.pdf::page_71::chunk_1']` | `{'hop_1': ['INTC_10k_2024.pdf::page_71::chunk_1'], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_22::chunk_3', 'INTC_10k_2024.pdf::page_19::chunk_3', 'INTC_10k_2024.pdf::page_71::chunk_1', 'INTC_10k_2024.pdf::page_16::chunk_1', 'INTC_10k_2023.pdf::page_32::chunk_2']` |
| graph |  | 2.454 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 1 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2023.pdf::page_49::chunk_2', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2024.pdf::page_76::chunk_2', 'INTC_10k_2024.pdf::page_60::chunk_2']` |

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
| vector |  | 0.115 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AVGO_10k_2022.pdf::page_71::chunk_5', 'AVGO_10k_2024.pdf::page_45::chunk_5', 'AVGO_10k_2023.pdf::page_45::chunk_5', 'NVDA_10k_2024.pdf::page_41::chunk_5', 'INTC_10k_2023.pdf::page_32::chunk_1']` |
| graph |  | 2.330 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | corpus_not_ready | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_27::chunk_4', 'AVGO_10k_2024.pdf::page_90::chunk_2', 'AVGO_10k_2023.pdf::page_90::chunk_2', 'INTC_10k_2023.pdf::page_76::chunk_2', 'INTC_10k_2024.pdf::page_19::chunk_2']` |

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
| vector |  | 0.105 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | n/a | n/a | n/a | not_applicable | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2024.pdf::page_85::chunk_2', 'INTC_10k_2022.pdf::page_41::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2', 'INTC_10k_2024.pdf::page_74::chunk_10', 'QCOM_10k_2022.pdf::page_43::chunk_2']` |
| graph |  | 2.634 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2023.pdf::page_89::chunk_3', 'INTC_10k_2023.pdf::page_46::chunk_1', 'INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2024.pdf::page_74::chunk_8', 'INTC_10k_2023.pdf::page_50::chunk_1']` |
