# Phase T Retrieval Baseline

Generated: 2026-08-01T21:15:53

## Run Configuration

- script: `scripts/evaluate_retrieval_quality.py`
- command: `scripts/evaluate_retrieval_quality.py --queries benchmark/datasets/finreflectkg_sox_strict20.yaml --output-dir analytics/Report Experiment --tools graph --top-k 9 --oracle-k 20 --no-llm-expansion --graph-seed-mode triple --graph-ppr-mode entity_chunk --graph-triple-filter llm --reextract-tickers AMD,AVGO,INTC,NVDA,QCOM,TXN --ppr-seed-weight-mode uniform --version-name graphonly_strict20_t20_llmfilter_top9_agent_ablation --graph-rerank-mode legacy --final-rerank none --candidate-pool-k 100 --graph-top-k-entities 20 --graph-top-k-triples 20 --graph-damping 0.5`
- query_file: `benchmark/datasets/finreflectkg_sox_strict20.yaml`
- query_count: `20`
- tools: `graph`
- top_k: `9`
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
- version_name: `graphonly_strict20_t20_llmfilter_top9_agent_ablation`
- details_jsonl: `analytics/Report Experiment/details_graphonly_strict20_t20_llmfilter_top9_agent_ablation_20260801_210924.jsonl`
- reextract_tickers_arg: `AMD,AVGO,INTC,NVDA,QCOM,TXN`
- resolved_ticker_scope: `AMD, AVGO, INTC, NVDA, QCOM, TXN`
- known_tickers: `ACLS, ADI, ALAB, AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MCHP, MPWR, MRVL, MU, NVDA, ON, QCOM, RMBS, SWKS, TXN`
- scored_queries: `20`
- unscored_queries: `0`
- existing_gold_entities: `56`
- total_gold_entities: `69`

## Overall

| Tool | Scored Queries | Errors | ChunkHit@k | Random ChunkHit@k | Hit Lift | Hit-Random | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| graph | 20 | 0 | 0.350 | 0.006 | 57.557 | 0.344 | 0.250 | 0.250 | 0.150 | 0.250 | 0.450 |

## By Type

| Type | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable |
|---|---:|---:|---:|---:|
| 2hop_inter_document_same_company | 0.375 | 0.250 | 0.250 | 0.125 |
| 2hop_intra_document | 0.250 | 0.125 | 0.125 | 0.000 |
| 3hop_inter_document_cross_company | 0.000 | 0.000 | 0.000 | 0.000 |
| 3hop_inter_document_same_company | 0.000 | 0.000 | 0.000 | 0.000 |
| 3hop_intra_document | 1.000 | 1.000 | 1.000 | 1.000 |

## By Subset

| Subset | graph ChunkHit | graph ChunkRecall | graph GroupRecall | graph Answerable | graph Oracle |
|---|---:|---:|---:|---:|---:|
| mixed_subset | 0.333 | 0.167 | 0.167 | 0.000 | 0.333 |
| reextract_subset | 0.357 | 0.286 | 0.286 | 0.214 | 0.500 |

## Graph Stage Diagnostics

| Subset | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottlenecks |
|---|---:|---:|---:|---:|---|
| full_mixed | 0.800 | 1.000 | n/a | 0.350 | direct_ppr_chunk_loss=9, hit_top_k=7, seed_loss=4 |
| mixed_subset | 1.000 | 1.000 | n/a | 0.333 | direct_ppr_chunk_loss=4, hit_top_k=2 |
| reextract_subset | 0.714 | 1.000 | n/a | 0.357 | direct_ppr_chunk_loss=5, hit_top_k=5, seed_loss=4 |

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
| graph |  | 60.357 | 0 | 0.008 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['NVDA_10k_2022.pdf::page_80::chunk_5', 'AVGO_10k_2023.pdf::page_63::chunk_1', 'TXN_10k_2023.pdf::page_36::chunk_3', 'TXN_10k_2024.pdf::page_36::chunk_3', 'AVGO_10k_2024.pdf::page_63::chunk_1', 'NVDA_10k_2023.pdf::page_56::chunk_1', 'NVDA_10k_2024.pdf::page_58::chunk_1', 'TXN_10k_2022.pdf::page_37::chunk_3', 'AMD_10k_2022.pdf::page_62::chunk_1']` |

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
| graph |  | 21.322 | 1 | 0.008 | 1.000 | 1.000 | 1 | 1.000 | 1 | 1 | 1 | n/a | 1 | hit_top_k | `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']` | `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_4::chunk_1']}` | `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2023.pdf::page_3::chunk_1', 'TXN_10k_2024.pdf::page_3::chunk_1', 'TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_30::chunk_1', 'TXN_10k_2022.pdf::page_32::chunk_1', 'INTC_10k_2024.pdf::page_22::chunk_3', 'TXN_10k_2022.pdf::page_6::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']` |

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
| graph |  | 22.348 | 0 | 0.008 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | n/a | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': [], 'hop_3': []}` | `['INTC_10k_2023.pdf::page_22::chunk_1', 'INTC_10k_2024.pdf::page_70::chunk_1', 'INTC_10k_2022.pdf::page_27::chunk_4', 'INTC_10k_2023.pdf::page_29::chunk_2', 'AMD_10k_2024.pdf::page_70::chunk_2', 'AMD_10k_2022.pdf::page_77::chunk_1', 'AMD_10k_2024.pdf::page_68::chunk_7', 'INTC_10k_2024.pdf::page_23::chunk_2', 'INTC_10k_2024.pdf::page_72::chunk_1']` |

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
| graph |  | 21.176 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2022.pdf::page_4::chunk_1', 'AMD_10k_2022.pdf::page_37::chunk_1', 'NVDA_10k_2024.pdf::page_31::chunk_1', 'AVGO_10k_2024.pdf::page_52::chunk_1', 'AMD_10k_2024.pdf::page_64::chunk_1', 'QCOM_10k_2022.pdf::page_42::chunk_5', 'AMD_10k_2022.pdf::page_76::chunk_1', 'AMD_10k_2023.pdf::page_59::chunk_2', 'AMD_10k_2024.pdf::page_85::chunk_2']` |

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
| graph |  | 31.476 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2023.pdf::page_40::chunk_1', 'INTC_10k_2024.pdf::page_15::chunk_1', 'INTC_10k_2023.pdf::page_97::chunk_4', 'INTC_10k_2024.pdf::page_25::chunk_3', 'INTC_10k_2022.pdf::page_32::chunk_1', 'INTC_10k_2022.pdf::page_40::chunk_1', 'INTC_10k_2024.pdf::page_23::chunk_3', 'INTC_10k_2022.pdf::page_95::chunk_2', 'INTC_10k_2023.pdf::page_89::chunk_2']` |

### FRKG071: `Which segment includes acquisition, integration and restructuring charges, and what was its reported revenue in 2024?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['acquisition charge', 'acquisition charges', 'other', 'other segment', 'texas instrument', 'texas instrument , inc .', 'texas instrument inc .', 'texas instrument incorporate', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_2': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 27.227 | 1 | 0.006 | 1.000 | 1.000 | 1 | 0.333 | 1 | 1 | 1 | n/a | 1 | hit_top_k | `['TXN_10k_2024.pdf::page_4::chunk_1', 'TXN_10k_2023.pdf::page_30::chunk_1']` | `{'hop_1': ['TXN_10k_2023.pdf::page_30::chunk_1'], 'hop_2': ['TXN_10k_2024.pdf::page_4::chunk_1']}` | `['TXN_10k_2022.pdf::page_32::chunk_1', 'TXN_10k_2024.pdf::page_38::chunk_6', 'TXN_10k_2024.pdf::page_4::chunk_1', 'TXN_10k_2023.pdf::page_30::chunk_1', 'TXN_10k_2023.pdf::page_4::chunk_1', 'TXN_10k_2022.pdf::page_6::chunk_1', 'TXN_10k_2022.pdf::page_21::chunk_1', 'TXN_10k_2024.pdf::page_30::chunk_2', 'TXN_10k_2024.pdf::page_30::chunk_1']` |

### FRKG073: `What was the change in operating losses for the 'All other' segment between 2021 and 2022, and what asset transfer amount into this segment was disclosed in 2023 according to Intel's financial reports?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['all other', 'all other category', 'all other segment', 'intc', 'intel', 'intel corporation', 'operate income', 'operating income', 'operating_income']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2023.pdf::page_97::chunk_2', 'INTC_10k_2022.pdf::page_86::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2023.pdf::page_97::chunk_2'], 'hop_2': ['INTC_10k_2022.pdf::page_86::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 14.174 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | n/a | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2022.pdf::page_55::chunk_2', 'NVDA_10k_2024.pdf::page_41::chunk_5', 'AMD_10k_2022.pdf::page_77::chunk_2', 'NVDA_10k_2022.pdf::page_99::chunk_2', 'AMD_10k_2023.pdf::page_52::chunk_1', 'TXN_10k_2022.pdf::page_29::chunk_1', 'AMD_10k_2024.pdf::page_59::chunk_2', 'AMD_10k_2023.pdf::page_59::chunk_2', 'NVDA_10k_2023.pdf::page_71::chunk_3']` |

### FRKG082: `What was the impact of the All Other segment's operating loss in 2023 on Intel's total operating income, and how does the segment's composition of non-reportable businesses and intersegment allocations contribute to this financial outcome?`

- type: `2hop_inter_document_same_company`
- subset: `mixed_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['all other', 'all other category', 'all other segment', 'intc', 'intel', 'intel corporation', 'total operate income', 'total operating income']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2024.pdf::page_71::chunk_1', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_71::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 18.111 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2023.pdf::page_69::chunk_7', 'INTC_10k_2024.pdf::page_60::chunk_2', 'AMD_10k_2024.pdf::page_19::chunk_1', 'AMD_10k_2022.pdf::page_77::chunk_4', 'AMD_10k_2023.pdf::page_70::chunk_4', 'AMD_10k_2024.pdf::page_68::chunk_7', 'INTC_10k_2023.pdf::page_29::chunk_2', 'AMD_10k_2024.pdf::page_70::chunk_2', 'AMD_10k_2022.pdf::page_77::chunk_1']` |

### FRKG084: `By how many percentage points did the operating income growth rate for AVGO's Infrastructure Software segment exceed its revenue growth rate in fiscal year 2022, and what does this indicate about the segment's operational efficiency?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['avgo', 'broadcom', 'broadcom corp', 'broadcom corporation', 'broadcom inc .', 'broadcom_inc', 'infrastructure software', 'infrastructure software segment', 'operate income', 'operating income', 'operating_income']`
- missing_gold_entities: `[]`
- gold_chunks: `['AVGO_10k_2022.pdf::page_70::chunk_2', 'AVGO_10k_2022.pdf::page_71::chunk_4']`
- gold_evidence_groups: `{'hop_1': ['AVGO_10k_2022.pdf::page_70::chunk_2'], 'hop_2': ['AVGO_10k_2022.pdf::page_71::chunk_4']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 9.966 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 1 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AVGO_10k_2023.pdf::page_42::chunk_1', 'AVGO_10k_2022.pdf::page_98::chunk_3', 'AVGO_10k_2024.pdf::page_90::chunk_2', 'AVGO_10k_2023.pdf::page_90::chunk_2', 'AVGO_10k_2022.pdf::page_123::chunk_2', 'AVGO_10k_2023.pdf::page_37::chunk_1', 'AVGO_10k_2024.pdf::page_37::chunk_1', 'AVGO_10k_2022.pdf::page_59::chunk_1', 'AVGO_10k_2022.pdf::page_61::chunk_1']` |

### FRKG093: `What was the percentage change in the value per percentage point of Mobileye's non-controlling interest from 2022 to 2023, and how does this reflect Intel's stake valuation in the segment?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['$ 989', 'intc', 'intel', 'intel corporation', 'mobileye', 'mobileye group', 'mobileye segment']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2024.pdf::page_70::chunk_1', 'INTC_10k_2023.pdf::page_89::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_70::chunk_1'], 'hop_2': ['INTC_10k_2023.pdf::page_89::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 22.330 | 1 | 0.006 | 0.500 | 0.500 | 0 | 1.000 | 1 | 1 | 1 | n/a | 1 | hit_top_k | `['INTC_10k_2023.pdf::page_89::chunk_2']` | `{'hop_1': [], 'hop_2': ['INTC_10k_2023.pdf::page_89::chunk_2']}` | `['INTC_10k_2023.pdf::page_89::chunk_2', 'INTC_10k_2024.pdf::page_74::chunk_8', 'INTC_10k_2022.pdf::page_84::chunk_1', 'INTC_10k_2023.pdf::page_85::chunk_1', 'INTC_10k_2024.pdf::page_74::chunk_10', 'INTC_10k_2023.pdf::page_80::chunk_2', 'INTC_10k_2024.pdf::page_63::chunk_2', 'INTC_10k_2023.pdf::page_72::chunk_2', 'INTC_10k_2024.pdf::page_61::chunk_2']` |

### FRKG096: `What was the total revenue contribution from Texas Instruments' Other segment in 2024, and which specific non-operational items are explicitly included in this segment's financial reporting?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['asset disposition', 'asset dispositions', 'other', 'other segment', 'texas instrument', 'texas instrument , inc .', 'texas instrument inc .', 'texas instrument incorporate', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2024.pdf::page_30::chunk_1', 'TXN_10k_2024.pdf::page_4::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_30::chunk_1'], 'hop_2': ['TXN_10k_2024.pdf::page_4::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 19.185 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2024.pdf::page_38::chunk_6', 'TXN_10k_2023.pdf::page_20::chunk_7', 'TXN_10k_2022.pdf::page_33::chunk_2', 'TXN_10k_2024.pdf::page_20::chunk_7', 'INTC_10k_2024.pdf::page_94::chunk_2', 'INTC_10k_2023.pdf::page_25::chunk_1', 'INTC_10k_2022.pdf::page_24::chunk_2', 'TXN_10k_2022.pdf::page_22::chunk_7', 'TXN_10k_2023.pdf::page_53::chunk_6']` |

### FRKG098: `How does AMD disclose its executive compensation agreements, such as the sign-on bonus agreement with Jean Hu, to regulatory bodies and the public?`

- type: `2hop_intra_document`
- subset: `mixed_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['advanced micro device , inc .', 'advanced micro device inc .', 'amd', 'sec', 'sign-on bonus agreement with john doe']`
- missing_gold_entities: `[]`
- gold_chunks: `['AMD_10k_2024.pdf::page_16::chunk_1', 'AMD_10k_2024.pdf::page_101::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['AMD_10k_2024.pdf::page_16::chunk_1'], 'hop_2': ['AMD_10k_2024.pdf::page_101::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 12.364 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2022.pdf::page_91::chunk_1', 'AMD_10k_2024.pdf::page_102::chunk_2', 'AMD_10k_2024.pdf::page_3::chunk_2', 'AMD_10k_2022.pdf::page_3::chunk_2', 'QCOM_10k_2023.pdf::page_26::chunk_1', 'INTC_10k_2023.pdf::page_2::chunk_2', 'AMD_10k_2023.pdf::page_108::chunk_2', 'AMD_10k_2024.pdf::page_104::chunk_2', 'AMD_10k_2024.pdf::page_104::chunk_3']` |

### FRKG100: `What was the operating profit contribution from the Embedded Processing segment in 2022, and how does this directly affect Texas Instruments' deferred tax liabilities under their asset and liability accounting approach for income taxes?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['deferred tax asset and liability', 'deferred tax assets and liabilities', 'embed processing', 'embedded processing', 'texas instrument', 'texas instrument , inc .', 'texas instrument inc .', 'texas instrument incorporate', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_32::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_32::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 7.455 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2022.pdf::page_76::chunk_1', 'TXN_10k_2024.pdf::page_62::chunk_1', 'TXN_10k_2023.pdf::page_40::chunk_2', 'TXN_10k_2024.pdf::page_39::chunk_2', 'TXN_10k_2022.pdf::page_41::chunk_2', 'TXN_10k_2023.pdf::page_27::chunk_2', 'TXN_10k_2022.pdf::page_29::chunk_1', 'TXN_10k_2023.pdf::page_32::chunk_1', 'QCOM_10k_2022.pdf::page_76::chunk_1']` |

### FRKG102: `What was the return on assets for Intel's Programmable Solutions Group in 2021, and how does this reflect the segment's efficiency in converting investments into operating income?`

- type: `2hop_intra_document`
- subset: `mixed_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'intel', 'intel corporation', 'net revenue', 'programmable solution group', 'programmable solutions group']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2022.pdf::page_95::chunk_2', 'INTC_10k_2022.pdf::page_86::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2022.pdf::page_95::chunk_2'], 'hop_2': ['INTC_10k_2022.pdf::page_86::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 12.522 | 1 | 0.006 | 0.500 | 0.500 | 0 | 1.000 | 1 | 1 | 1 | n/a | 1 | hit_top_k | `['INTC_10k_2022.pdf::page_86::chunk_2']` | `{'hop_1': [], 'hop_2': ['INTC_10k_2022.pdf::page_86::chunk_2']}` | `['INTC_10k_2022.pdf::page_86::chunk_2', 'INTC_10k_2022.pdf::page_84::chunk_1', 'INTC_10k_2022.pdf::page_95::chunk_4', 'AMD_10k_2024.pdf::page_50::chunk_2', 'AMD_10k_2023.pdf::page_51::chunk_2', 'AMD_10k_2024.pdf::page_40::chunk_1', 'AMD_10k_2022.pdf::page_46::chunk_2', 'INTC_10k_2024.pdf::page_78::chunk_1', 'NVDA_10k_2023.pdf::page_24::chunk_1']` |

### FRKG103: `What percentage of QCT's fiscal 2024 revenue was represented by its accounts receivable balance as of September 29, 2024, and how does this relationship reflect the segment's revenue recognition practices for customer incentives?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['account receivable', 'accounts receivable', 'qcom', 'qct', 'qct segment', 'qualcomm', 'qualcomm inc .', 'qualcomm incorporate', 'qualcomm_incorporated']`
- missing_gold_entities: `[]`
- gold_chunks: `['QCOM_10k_2023.pdf::page_72::chunk_4', 'QCOM_10k_2023.pdf::page_59::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['QCOM_10k_2023.pdf::page_72::chunk_4'], 'hop_2': ['QCOM_10k_2023.pdf::page_59::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 12.518 | 1 | 0.006 | 0.500 | 0.500 | 0 | 0.333 | 1 | 1 | 1 | n/a | 1 | hit_top_k | `['QCOM_10k_2023.pdf::page_59::chunk_1']` | `{'hop_1': [], 'hop_2': ['QCOM_10k_2023.pdf::page_59::chunk_1']}` | `['QCOM_10k_2024.pdf::page_59::chunk_1', 'QCOM_10k_2022.pdf::page_58::chunk_1', 'QCOM_10k_2023.pdf::page_59::chunk_1', 'QCOM_10k_2023.pdf::page_10::chunk_1', 'QCOM_10k_2024.pdf::page_69::chunk_1', 'QCOM_10k_2022.pdf::page_69::chunk_1', 'QCOM_10k_2024.pdf::page_10::chunk_1', 'QCOM_10k_2023.pdf::page_73::chunk_5', 'QCOM_10k_2022.pdf::page_73::chunk_5']` |

### FRKG104: `What was the dollar increase in Intel's consolidated share of Mobileye's operating income between 2022 and 2023, and how did this compare to the overall decline in Intel's total operating income during the same period?`

- type: `2hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['intc', 'intel', 'intel corporation', 'mobileye', 'mobileye group', 'mobileye segment', 'total operate income', 'total operating income']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2023.pdf::page_89::chunk_2', 'INTC_10k_2023.pdf::page_88::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2023.pdf::page_89::chunk_2'], 'hop_2': ['INTC_10k_2023.pdf::page_88::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 7.519 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | n/a | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['AMD_10k_2023.pdf::page_48::chunk_1', 'AMD_10k_2023.pdf::page_6::chunk_1', 'AMD_10k_2024.pdf::page_5::chunk_1', 'AMD_10k_2023.pdf::page_12::chunk_1', 'AMD_10k_2024.pdf::page_10::chunk_1', 'AMD_10k_2023.pdf::page_28::chunk_1', 'AMD_10k_2023.pdf::page_20::chunk_1', 'AMD_10k_2024.pdf::page_51::chunk_3', 'AMD_10k_2022.pdf::page_37::chunk_1']` |

### FRKG105: `What is the ratio of goodwill allocated to the Embedded Processing segment relative to its average operating profit across 2022 and 2023, and how does this compare to the company's total goodwill allocation?`

- type: `3hop_intra_document`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['embed processing', 'embedded processing', 'goodwill', 'texas instrument', 'texas instrument , inc .', 'texas instrument inc .', 'texas instrument incorporate', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_31::chunk_1', 'TXN_10k_2024.pdf::page_52::chunk_8']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_31::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_52::chunk_8']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 13.748 | 1 | 0.008 | 1.000 | 1.000 | 1 | 0.333 | 1 | 1 | 1 | n/a | 1 | hit_top_k | `['TXN_10k_2024.pdf::page_52::chunk_8', 'TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_31::chunk_1']` | `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2024.pdf::page_31::chunk_1'], 'hop_3': ['TXN_10k_2024.pdf::page_52::chunk_8']}` | `['AMD_10k_2023.pdf::page_77::chunk_5', 'TXN_10k_2022.pdf::page_55::chunk_6', 'TXN_10k_2024.pdf::page_52::chunk_8', 'TXN_10k_2023.pdf::page_54::chunk_2', 'TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2024.pdf::page_31::chunk_1', 'AMD_10k_2023.pdf::page_71::chunk_7', 'AMD_10k_2023.pdf::page_74::chunk_3', 'AMD_10k_2024.pdf::page_10::chunk_1']` |

### FRKG107: `What was the percentage change in Mobileye's total equity from 2022 to 2023, based on Intel's non-controlling interest disclosures and ownership percentages?`

- type: `2hop_inter_document_same_company`
- subset: `mixed_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['$ 989', 'intc', 'intel', 'intel corporation', 'mobileye', 'mobileye group', 'mobileye segment']`
- missing_gold_entities: `[]`
- gold_chunks: `['INTC_10k_2024.pdf::page_74::chunk_6', 'INTC_10k_2023.pdf::page_89::chunk_2']`
- gold_evidence_groups: `{'hop_1': ['INTC_10k_2024.pdf::page_74::chunk_6'], 'hop_2': ['INTC_10k_2023.pdf::page_89::chunk_2']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 16.789 | 1 | 0.006 | 0.500 | 0.500 | 0 | 1.000 | 1 | 1 | 1 | n/a | 1 | hit_top_k | `['INTC_10k_2023.pdf::page_89::chunk_2']` | `{'hop_1': [], 'hop_2': ['INTC_10k_2023.pdf::page_89::chunk_2']}` | `['INTC_10k_2023.pdf::page_89::chunk_2', 'INTC_10k_2024.pdf::page_61::chunk_2', 'INTC_10k_2024.pdf::page_57::chunk_1', 'INTC_10k_2024.pdf::page_85::chunk_5', 'INTC_10k_2024.pdf::page_23::chunk_1', 'INTC_10k_2023.pdf::page_89::chunk_3', 'INTC_10k_2022.pdf::page_30::chunk_1', 'QCOM_10k_2024.pdf::page_12::chunk_1', 'INTC_10k_2024.pdf::page_74::chunk_8']` |

### FRKG108: `What was the operating profit per share contributed by Texas Instruments' 'Other' segment in 2022, based on the total shares outstanding as of January 25, 2022?`

- type: `2hop_inter_document_same_company`
- subset: `mixed_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['other', 'other segment', 'share outstanding', 'shares outstanding', 'texas instrument', 'texas instrument , inc .', 'texas instrument inc .', 'texas instrument incorporate', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2022.pdf::page_1::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2022.pdf::page_1::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 13.001 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 0 | 1 | 1 | n/a | 0 | direct_ppr_chunk_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['TXN_10k_2022.pdf::page_33::chunk_2', 'TXN_10k_2024.pdf::page_4::chunk_1', 'TXN_10k_2024.pdf::page_30::chunk_2', 'TXN_10k_2022.pdf::page_35::chunk_1', 'TXN_10k_2023.pdf::page_30::chunk_1', 'INTC_10k_2023.pdf::page_72::chunk_2', 'AMD_10k_2022.pdf::page_69::chunk_3', 'QCOM_10k_2023.pdf::page_47::chunk_2', 'INTC_10k_2022.pdf::page_74::chunk_1']` |

### FRKG111: `What was the ratio of the amortization of capitalized software in 2021 to the operating profit of the 'Other' segment in 2022?`

- type: `2hop_inter_document_same_company`
- subset: `reextract_subset`
- corpus_status: `ready`
- gold_tools: `['vector', 'graph', 'hybrid']`
- gold_entities: `['amort . cap . software', 'amort. cap. software', 'other', 'other segment', 'texas instrument', 'texas instrument , inc .', 'texas instrument inc .', 'texas instrument incorporate', 'txn']`
- missing_gold_entities: `[]`
- gold_chunks: `['TXN_10k_2024.pdf::page_31::chunk_3', 'TXN_10k_2022.pdf::page_30::chunk_1']`
- gold_evidence_groups: `{'hop_1': ['TXN_10k_2024.pdf::page_31::chunk_3'], 'hop_2': ['TXN_10k_2022.pdf::page_30::chunk_1']}`

| Tool | Error | Latency | ChunkHit@k | Random ChunkHit@k | ChunkRecall@k | GroupRecall@k | Answerable@k | MRR@k | Oracle Hit | SeedHit | PPRHit | ChunkMapHit | DirectPPRChunkHit | Bottleneck | Chunk Hits | Group Hits | Returned |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| graph |  | 17.112 | 0 | 0.006 | 0.000 | 0.000 | 0 | 0.000 | 0 | 0 | 1 | n/a | 0 | seed_loss | `[]` | `{'hop_1': [], 'hop_2': []}` | `['INTC_10k_2022.pdf::page_95::chunk_10', 'INTC_10k_2023.pdf::page_3::chunk_1', 'INTC_10k_2023.pdf::page_98::chunk_5', 'INTC_10k_2024.pdf::page_86::chunk_6', 'NVDA_10k_2023.pdf::page_64::chunk_3', 'INTC_10k_2024.pdf::page_42::chunk_1', 'INTC_10k_2023.pdf::page_48::chunk_2', 'INTC_10k_2023.pdf::page_55::chunk_1', 'INTC_10k_2024.pdf::page_38::chunk_1']` |
