# Phase T Retrieval Baseline

Generated: 2026-08-01T22:18:59

## Run Configuration

- script: `scripts/evaluate_retrieval_quality.py`
- command: `scripts/evaluate_retrieval_quality.py --queries benchmark/datasets/finreflectkg_sox_strict20.yaml --output-dir analytics/Report Experiment --tools graph --top-k 5 --oracle-k 20 --limit 5 --no-llm-expansion --graph-seed-mode triple --graph-ppr-mode entity_chunk --graph-triple-filter llm --reextract-tickers AMD,AVGO,INTC,NVDA,QCOM,TXN --ppr-seed-weight-mode uniform --version-name graphonly_strict5_t20_recall_safe_runtime --graph-rerank-mode legacy --final-rerank none --candidate-pool-k 100 --graph-top-k-entities 20 --graph-top-k-triples 20 --graph-damping 0.5`
- query_file: `benchmark/datasets/finreflectkg_sox_strict20.yaml`
- query_count: `5`
- tools: `graph`
- top_k: `5`
- oracle_k: `20`
- dry_run: `False`
- corpus_chunks: `3251`
- graph_use_expansion: `False`
- graph_seed_mode: `triple`
- graph_rerank_mode: `legacy`
- candidate_pool_k: `100`
- graph_top_k_entities: `20`
- graph_top_k_triples: `20`
- graph_damping: `0.5`
- ppr_seed_weight_mode: `uniform`
- graph_ppr_mode: `entity_chunk`
- graph_triple_filter: `llm`
- final_rerank: `none`
- metadata_rerank_params: `{'risk_section_boost': 1.35, 'business_section_boost': 1.18, 'financial_section_boost': 1.28, 'ticker_boost': 1.2, 'cluster_boost_per_extra': 0.04, 'cluster_boost_cap': 1.05, 'latest_year_boost': 1.08, 'latest_year_min': 2025, 'lexical_match_weight': 0.1, 'lexical_boost_cap': 0.55, 'broad_penalty_enabled': True, 'broad_penalty_floor': 0.92, 'broad_penalty_step': 0.97, 'broad_penalty_zero_match': 0.98, 'broad_penalty_short_token_cutoff': 80, 'broad_penalty_mid_token_cutoff': 140, 'broad_penalty_long_token_cutoff': 220}`
- version_name: `graphonly_strict5_t20_recall_safe_runtime`
- details_jsonl: `analytics/Report Experiment/details_graphonly_strict5_t20_recall_safe_runtime_20260801_221703.jsonl`
- reextract_tickers_arg: `AMD,AVGO,INTC,NVDA,QCOM,TXN`
- resolved_ticker_scope: `AMD, AVGO, INTC, NVDA, QCOM, TXN`
- known_tickers: `ACLS, ADI, ALAB, AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MCHP, MPWR, MRVL, MU, NVDA, ON, QCOM, RMBS, SWKS, TXN`
- scored_queries: `5`
- unscored_queries: `0`
- existing_gold_entities: `27`
- total_gold_entities: `31`

## Overall

| Tool | Scored Queries | Errors | ChunkHit@k | Random ChunkHit@k | Hit Lift | Hit-Random | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| graph | 5 | 0 | 0.200 | 0.004 | 50.068 | 0.196 | 0.133 | 0.133 | 0.000 | 0.100 | 0.600 |

## By Type

| Type | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable |
|---|---:|---:|---:|---:|
| 2hop_inter_document_same_company | 0.000 | 0.000 | 0.000 | 0.000 |
| 2hop_intra_document | 0.000 | 0.000 | 0.000 | 0.000 |
| 3hop_inter_document_cross_company | 0.000 | 0.000 | 0.000 | 0.000 |
| 3hop_inter_document_same_company | 0.000 | 0.000 | 0.000 | 0.000 |
| 3hop_intra_document | 1.000 | 0.667 | 0.667 | 0.000 |

## By Subset

| Subset | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable | graph Oracle |
|---|---:|---:|---:|---:|---:|
| mixed_subset | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| reextract_subset | 0.250 | 0.167 | 0.167 | 0.000 | 0.750 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottlenecks |
|---|---:|---:|---:|---:|---|
| full_mixed | 0.800 | 1.000 | n/a | 0.200 | direct_ppr_chunk_loss=3, hit_top_k=1, seed_loss=1 |
| mixed_subset | 1.000 | 1.000 | n/a | 0.000 | direct_ppr_chunk_loss=1 |
| reextract_subset | 0.750 | 1.000 | n/a | 0.250 | direct_ppr_chunk_loss=2, hit_top_k=1, seed_loss=1 |

## Per Query

### FRKG003: `Based on the segment disclosures and term definitions in their 2024 10-K filings, how do Intel and NVIDIA differ in the treatment of stock-based compensation expenses within their 'All Other' categories, and what does this reveal about their corporate expense allocation practices?`

- type: `3hop_inter_document_cross_company`
- subset: `mixed_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['all other', 'all other category', 'all other segment', 'cdp', 'intc', 'intel', 'intel corporation', 'stock-based compensation expense']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2024.pdf::page_102::chunk_2', 'INTC_10k_2024.pdf::page_71::chunk_1', 'NVDA_10k_2024.pdf::page_78::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_102::chunk_2'], 'hop_2': ['INTC_10k_2024.pdf::page_71::chunk_1'], 'hop_3': ['NVDA_10k_2024.pdf::page_78::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 55.762 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['NVDA_10k_2022.pdf::page_80::chunk_5', 'AMD_10k_2023.pdf::page_67::chunk_1', 'NVDA_10k_2022.pdf::page_71::chunk_1', 'AMD_10k_2023.pdf::page_92::chunk_1', 'AMD_10k_2024.pdf::page_66::chunk_1']` |

### FRKG009: `What percentage of Texas Instruments' 2022 total revenue was represented by restructuring charges disclosed in the Other segment, and how does the company's segment reporting structure explain the separation of these charges from operating segments like Embedded Processing?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embed processing', 'embedded processing', 'other', 'other segment', 'restructuring charge', 'restructuring charges', 'texas instrument', 'texas instrument , inc .', 'texas instrument inc .', 'texas instrument incorporate', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 14.823 | 1 | 0.005 | 0.667 | 0.667 | 0 | 0.500 | 1 | 1 | 1 | n/a | 1 | hit_top_k | `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2023.pdf::page_30::chunk_1']` | `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_3': []}` | `['TXN_10k_2023.pdf::page_3::chunk_1', 'TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_3::chunk_1', 'TXN_10k_2022.pdf::page_32::chunk_1']` |

### FRKG010: `What was the total operating profit contribution from the Embedded Processing and Other segments in 2022 compared to 2023, considering that the Other segment includes restructuring charges and gains/losses from other activities as disclosed in the prior year's filing?`

- type: `3hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embed processing', 'embedded processing', 'gain and loss from other activity', 'gains and losses from other activities', 'other', 'other segment', 'texas instrument', 'texas instrument , inc .', 'texas instrument inc .', 'texas instrument incorporate', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_31::chunk_1', 'TXN_10k_2022.pdf::page_6::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_31::chunk_1'], 'hop_3': ['TXN_10k_2022.pdf::page_6::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 15.284 | 0 | 0.005 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | n/a | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2023.pdf::page_22::chunk_1', 'INTC_10k_2022.pdf::page_27::chunk_4', 'INTC_10k_2023.pdf::page_3::chunk_1', 'INTC_10k_2024.pdf::page_5::chunk_1', 'INTC_10k_2024.pdf::page_42::chunk_1']` |

### FRKG011: `What was the change in AMD's deferred tax liability related to acquired intangibles from 2022 to 2023, and how might the company's increasing compliance costs associated with SEC regulations influence this financial metric?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['acquire intangible', 'acquired intangibles', 'advanced micro device , inc .', 'advanced micro device inc .', 'amd', 'sec']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_10k_2023.pdf::page_36::chunk_1', 'AMD_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['AMD_10k_2023.pdf::page_36::chunk_1'], 'hop_2': ['AMD_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 17.137 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2022.pdf::page_4::chunk_1', 'AMD_10k_2022.pdf::page_37::chunk_1', 'NVDA_10k_2024.pdf::page_31::chunk_1', 'AMD_10k_2023.pdf::page_88::chunk_3', 'AVGO_10k_2024.pdf::page_88::chunk_3']` |

### FRKG070: `Calculate the total percentage growth in Mobileye's revenue from 2021 to 2023 and explain how the strategic initiatives outlined in the 2022 filing contributed to this increase.`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'intel', 'intel corporation', 'mobileye', 'mobileye group', 'mobileye segment', 'revenue']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2022.pdf::page_30::chunk_1', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2022.pdf::page_30::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 11.628 | 0 | 0.003 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2023.pdf::page_40::chunk_1', 'TXN_10k_2024.pdf::page_38::chunk_6', 'INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2024.pdf::page_25::chunk_3']` |
