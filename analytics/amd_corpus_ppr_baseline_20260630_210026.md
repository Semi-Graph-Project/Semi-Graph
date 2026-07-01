# AMD Corpus/PPR Baseline Before Re-Extract

Generated: `2026-06-30T21:05:22`
Snapshot: `backups/neo4j/20260630_200944`
Details JSON: `/home/kantinan/programming/project/analytics/amd_corpus_ppr_baseline_20260630_210026.json`

## PPR Parameters

- `top_k_chunks`: `5`
- `oracle_k`: `20`
- `top_k_entities`: `20`
- `top_k_triples`: `8`
- `damping`: `0.7`
- `use_expansion`: `True`
- `seed_mode`: `query_to_triple_seeds`
- `teleport`: `uniform`

## Corpus Health

| Metric | Value |
|---|---:|
| nodes_total | 15863 |
| entities | 13348 |
| chunks | 2347 |
| sections | 126 |
| relationships_total | 49929 |
| mentions | 29789 |
| informative_relationships | 17567 |
| isolated_entities | 4047 / 13348 (30.32%) |
| orphan_chunks | 0 |
| broad_chunks_gt40 | 5 |
| max_mentions_per_chunk | 48 |
| entities_missing_embedding | 0 |
| entities_missing_specificity | 0 |
| chunks_missing_embedding | 0 |
| informative_rels_missing_triple_embedding | 0 |

## Isolated By Type

| Type | Total | Isolated | % |
|---|---:|---:|---:|
| RISK_FACTOR | 5028 | 2204 | 43.83 |
| FIN_METRIC | 1564 | 401 | 25.64 |
| PRODUCT | 1907 | 336 | 17.62 |
| ORG | 370 | 184 | 49.73 |
| ACCOUNTING_POLICY | 331 | 172 | 51.96 |
| EVENT | 1537 | 171 | 11.13 |
| MACRO_CONDITION | 993 | 138 | 13.9 |
| COMP | 322 | 137 | 42.55 |
| GPE | 236 | 86 | 36.44 |
| SEGMENT | 352 | 84 | 23.86 |
| RAW_MATERIAL | 181 | 67 | 37.02 |
| REGULATORY_REQUIREMENT | 511 | 57 | 11.15 |
| ESG_TOPIC | 14 | 10 | 71.43 |
| FIN_MARKET | 2 | 0 | 0.0 |

## AMD / Item 1A Focus

| Metric | Value |
|---|---:|
| chunks | 191 |
| mentioned_entities | 1356 |
| amd_source_chunk_relationships | 1546 |
| all_Item_1A_PRODUCT_mentions | 0 |
| AMD_Item_1A_PRODUCT_mentions | 0 |
| risk_to_product_segment_metric_edges | 0 |

### AMD Isolated By Section/Type

| Section | Type | Total | Isolated | % |
|---|---|---:|---:|---:|
| Item_1 | PRODUCT | 297 | 11 | 3.7 |
| Item_1 | COMP | 39 | 9 | 23.08 |
| Item_1 | GPE | 14 | 1 | 7.14 |
| Item_1 | ORG | 7 | 0 | 0.0 |
| Item_1 | SEGMENT | 15 | 0 | 0.0 |
| Item_1 | RAW_MATERIAL | 1 | 0 | 0.0 |
| Item_1 | FIN_MARKET | 1 | 0 | 0.0 |
| Item_1A | RISK_FACTOR | 449 | 127 | 28.29 |
| Item_1A | REGULATORY_REQUIREMENT | 86 | 10 | 11.63 |
| Item_1A | GPE | 41 | 10 | 24.39 |
| Item_1A | COMP | 28 | 7 | 25.0 |
| Item_1A | EVENT | 60 | 3 | 5.0 |
| Item_1A | MACRO_CONDITION | 46 | 2 | 4.35 |
| Item_1A | RAW_MATERIAL | 14 | 1 | 7.14 |
| Item_1A | ORG | 10 | 0 | 0.0 |
| Item_7 | FIN_METRIC | 119 | 19 | 15.97 |
| Item_7 | EVENT | 44 | 9 | 20.45 |
| Item_7 | MACRO_CONDITION | 22 | 8 | 36.36 |
| Item_7 | ACCOUNTING_POLICY | 25 | 3 | 12.0 |
| Item_7 | COMP | 4 | 3 | 75.0 |
| Item_7 | PRODUCT | 77 | 2 | 2.6 |
| Item_7 | ORG | 3 | 0 | 0.0 |
| Item_7 | SEGMENT | 12 | 0 | 0.0 |

### AMD Relationship Distribution By Section

| Section | Relationship | Count |
|---|---|---:|
| Item_1 | PRODUCES | 408 |
| Item_1 | HAS_STAKE_IN | 24 |
| Item_1 | COMPETES_WITH | 19 |
| Item_1 | OPERATES_IN | 15 |
| Item_1 | PARTNERS_WITH | 13 |
| Item_1 | SUPPLIES | 11 |
| Item_1 | LISTED_ON | 3 |
| Item_1 | DEPENDS_ON | 1 |
| Item_1A | FACES | 221 |
| Item_1A | NEGATIVELY_IMPACTS | 200 |
| Item_1A | IMPACTED_BY | 182 |
| Item_1A | SUBJECT_TO | 35 |
| Item_1A | DEPENDS_ON | 24 |
| Item_1A | DISCLOSES | 15 |
| Item_1A | CAUSES_SHORTAGE_OF | 2 |
| Item_7 | DISCLOSES | 146 |
| Item_7 | POSITIVELY_IMPACTS | 83 |
| Item_7 | INTRODUCES | 57 |
| Item_7 | NEGATIVELY_IMPACTS | 55 |
| Item_7 | INVOLVED_IN | 18 |
| Item_7 | ANNOUNCES | 9 |
| Item_7 | INVESTS_IN | 5 |

## AMD Graph/PPR Query Baseline

| Metric | Value |
|---|---:|
| n_queries | 9 |
| n_scored | 7 |
| hit_at_5 | 0.5714285714285714 |
| recall_at_5 | 0.39999999999999997 |
| mrr_at_5 | 0.42857142857142855 |
| oracle_hit_at_20 | 0.8571428571428571 |
| oracle_recall_at_20 | 0.6428571428571429 |
| errors | 0 |

| ID | Type | Hit@5 | Recall@5 | MRR@5 | Gold rank <=20 | Top-5 chunks |
|---|---|---:|---:|---:|---:|---|
| T001 | graph_multihop | 0 | 0.0 | 0.0 | 6 | AMD_2025_Item_1A_0000_ac2e47a8<br>AMD_2025_Item_1A_0001_0fd81b24<br>AMD_2025_Item_1A_0011_10eec6d1<br>AMD_2025_Item_1_0009_c842eea0<br>AMD_2026_Item_1_0010_460dfa17 |
| T002 | supplier_via_product | 1 | 0.8 | 1.0 | 1 | NVDA_2025_Item_1_0008_a4407f7e<br>NVDA_2026_Item_1_0007_bf6a51b6<br>NVDA_2024_Item_1_0007_bae70036<br>INTC_2026_Item_1_0008_c74f560f<br>AMD_2025_Item_1_0009_c842eea0 |
| T004 | competitor_product | 1 | 1.0 | 0.5 | 2 | AMD_2026_Item_1_0007_f252541b<br>AMD_2026_Item_1_0003_ea53a6a5<br>AMD_2024_Item_1_0009_01379c5a<br>AMD_2025_Item_1_0006_551768e4<br>AMD_2025_Item_1_0007_0ffd6ad4 |
| T007 | competitor_product | None | None | None | None | NVDA_2025_Item_1_0009_7a56593b<br>NVDA_2026_Item_1_0008_edf8fe4b<br>AMD_2024_Item_1_0011_49024c2d<br>AMD_2025_Item_1_0008_db609f8f<br>AMD_2026_Item_1_0009_ac9cc232 |
| T015 | graph_multihop | None | None | None | None | MU_2025_Item_1A_0001_8d660135<br>KLAC_2023_Item_7_0009_9b5b651f<br>KLAC_2024_Item_7_0006_313cb934<br>AMD_2025_Item_1_0009_c842eea0<br>AMD_2026_Item_1_0010_460dfa17 |
| T017 | supplier_via_company | 1 | 0.5 | 0.5 | 2 | RMBS_2025_Item_1_0001_479b0c1e<br>AMD_2025_Item_1_0009_c842eea0<br>AMD_2026_Item_1_0010_460dfa17<br>NVDA_2025_Item_1_0008_a4407f7e<br>NVDA_2024_Item_1_0007_bae70036 |
| T018 | partner_via_product | 1 | 0.5 | 1.0 | 1 | AMD_2024_Item_1_0006_e41aed21<br>AMD_2025_Item_1_0009_c842eea0<br>AMD_2026_Item_1_0010_460dfa17<br>AMD_2024_Item_1_0011_49024c2d<br>AMD_2024_Item_1_0005_7be264c6 |
| T019 | segment_via_product | 0 | 0.0 | 0.0 | 11 | AMD_2025_Item_7_0000_16c93d97<br>AMD_2026_Item_7_0000_6b145a7b<br>AMD_2026_Item_7_0005_8ab9ed73<br>AMD_2025_Item_7_0005_36426dd3<br>AMD_2025_Item_7_0004_58e0bdd2 |
| T030 | customer_via_product | 0 | 0.0 | 0.0 | None | AMD_2025_Item_7_0005_36426dd3<br>AMD_2024_Item_1_0011_49024c2d<br>AMD_2025_Item_1_0008_db609f8f<br>AMD_2026_Item_1_0009_ac9cc232<br>AMD_2024_Item_7_0005_86aec648 |

## Per-Query Top Evidence

### T001: How exposed is AMD to TSMC supply risk?

- Error: `None`
- Gold chunks: `['AMD_2026_Item_1A_0008_e84e4130']`
- Hits@5: `[]`; Hits@20: `['AMD_2026_Item_1A_0008_e84e4130']`
- Top PPR entities: amd (ORG), advanced micro devices (ORG), tsmc (COMP), investment portfolio risk (RISK_FACTOR), intel (ORG), tsmc 7nm supply constraint (RISK_FACTOR), tsmc (ORG), supply chain disruption risk (RISK_FACTOR)

| Rank | Chunk | Ticker | FY | Section | Score | Preview |
|---:|---|---|---:|---|---:|---|
| 1 | `AMD_2025_Item_1A_0000_ac2e47a8` | AMD | 2025 | Item_1A | 4.295129 | ITEM 1A. RISK FACTORS  The risks and uncertainties described below are not the only ones we face. If any of the following risks actually occurs, our business, financial condition or results of operations could be materially adversely affected. In addition, you |
| 2 | `AMD_2025_Item_1A_0001_0fd81b24` | AMD | 2025 | Item_1A | 4.295129 | ◦Costs related to defective products could have a material adverse effect on us.  ◦We may fail to maintain the efficiency of our supply chain as we respond to changes in customer demand.  ◦We outsource to third parties certain supply-chain logistics functions. |
| 3 | `AMD_2025_Item_1A_0011_10eec6d1` | AMD | 2025 | Item_1A | 4.105264 | Failure to achieve expected manufacturing yields for our products could negatively impact our results of operations.  Semiconductor manufacturing yields are a result of product design, process technology and packaging technology, which is typically proprietary |
| 4 | `AMD_2025_Item_1_0009_c842eea0` | AMD | 2025 | Item_1 | 3.886717 | Competition in Client Segment  Our primary competitor in the supply of CPUs and APUs is Intel. A variety of companies provide or have developed Arm-based microprocessors and platforms which could lead to further adoption of Arm-based PC solutions.  Competition |
| 5 | `AMD_2026_Item_1_0010_460dfa17` | AMD | 2026 | Item_1 | 3.886717 | Competition in Client and Gaming Segment  Our primary competitor in the supply of CPUs and APUs is Intel. A variety of companies provide or have developed Arm-based microprocessors and platforms which could lead to further adoption of Arm-based PC solutions.   |

### T002: Which foundry partner manufactures the Hopper architecture chips?

- Error: `None`
- Gold chunks: `['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f']`
- Hits@5: `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0007_bae70036', 'INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0']`; Hits@20: `['NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2024_Item_1_0007_bae70036', 'INTC_2026_Item_1_0008_c74f560f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17']`
- Top PPR entities: nvidia corporation (ORG), nvidia (ORG), advanced micro devices (ORG), tsmc (COMP), tsmc (ORG), nvidia hopper gpu (PRODUCT), hopper architecture (PRODUCT), hopper (PRODUCT)

| Rank | Chunk | Ticker | FY | Section | Score | Preview |
|---:|---|---|---:|---|---:|---|
| 1 | `NVDA_2025_Item_1_0008_a4407f7e` | NVDA | 2025 | Item_1 | 7.072363 | 8  * * *  Table of Contents  of growth, we may place non-cancellable inventory orders for certain product components in advance of our historical lead times, pay premiums, or provide deposits to secure future supply and capacity and may need to continue to do  |
| 2 | `NVDA_2026_Item_1_0007_bf6a51b6` | NVDA | 2026 | Item_1 | 6.589209 | We have expanded our supplier relationships to build redundancy and resilience in our operations to provide long-term manufacturing capacity aligned with growing customer demand. While currently our supply chain is mainly concentrated in Asia, we are expanding |
| 3 | `NVDA_2024_Item_1_0007_bae70036` | NVDA | 2024 | Item_1 | 6.588164 | Seasonality  Our computing platforms serve a diverse set of markets such as data centers, gaming, professional visualization, and automotive. Our desktop gaming products typically see stronger revenue in the second half of our fiscal year. Historical seasonali |
| 4 | `INTC_2026_Item_1_0008_c74f560f` | INTC | 2026 | Item_1 | 5.590844 | Competition  DCAI competitors include AMD, which utilizes the x86 architecture and competes with us across the full spectrum of CPUs, GPUs, accelerators and other products; providers of GPU systems such as NVIDIA, whose GPU systems have experienced the highest |
| 5 | `AMD_2025_Item_1_0009_c842eea0` | AMD | 2025 | Item_1 | 5.271367 | Competition in Client Segment  Our primary competitor in the supply of CPUs and APUs is Intel. A variety of companies provide or have developed Arm-based microprocessors and platforms which could lead to further adoption of Arm-based PC solutions.  Competition |

### T004: What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?

- Error: `None`
- Gold chunks: `['AMD_2026_Item_1_0003_ea53a6a5']`
- Hits@5: `['AMD_2026_Item_1_0003_ea53a6a5']`; Hits@20: `['AMD_2026_Item_1_0003_ea53a6a5']`
- Top PPR entities: amd (ORG), advanced micro devices (ORG), amd instinct accelerators (PRODUCT), versal ai core (PRODUCT), versal ai edge (PRODUCT), amd ryzen ai (PRODUCT), amd instinct mi325 (PRODUCT), amd instinct mi350 (PRODUCT)

| Rank | Chunk | Ticker | FY | Section | Score | Preview |
|---:|---|---|---:|---|---:|---|
| 1 | `AMD_2026_Item_1_0007_f252541b` | AMD | 2026 | Item_1 | 5.736169 | 6  * * *  Table of Contents    Design Platforms and Services  Adaptable Platforms. We offer two types of platforms that support our customers' designs and reduce their development efforts: FPGAs and adaptive SoCs. FPGAs feature reconfigurable hardware as well  |
| 2 | `AMD_2026_Item_1_0003_ea53a6a5` | AMD | 2026 | Item_1 | 5.548820 | •the Client and Gaming segment, which primarily includes CPUs, APUs, chipsets for desktops and notebooks, discrete GPUs, and semi-custom SoC products and development services; and  •the Embedded segment, which primarily includes embedded CPUs, APUs, FPGAs, SOM |
| 3 | `AMD_2024_Item_1_0009_01379c5a` | AMD | 2024 | Item_1 | 5.107313 | We generally warrant that our products sold to our customers will conform to our approved specifications and be free from defects in material and workmanship under normal use and conditions for one year. We offer up to three-year limited warranties for certain |
| 4 | `AMD_2025_Item_1_0006_551768e4` | AMD | 2025 | Item_1 | 4.928182 | Legacy Product Families. We offer prior generation high-end Virtex™ and low-end Spartan™ FPGA families as well as the original Virtex and Spartan families. Our prior generations of Complex Programmable Logic Devices \(CPLD\) include the CoolRunner™ and XC9500  |
| 5 | `AMD_2025_Item_1_0007_0ffd6ad4` | AMD | 2025 | Item_1 | 4.053651 | 6  * * *  Table of Contents  Our product brand for professional graphics products is AMD Radeon PRO graphics.  We also market and sell our chipsets under AMD trademarks.  Our FPGA products are Virtex™-6, Virtex-7, Virtex UltraScale+, Kintex™-7, Kintex UltraSca |

### T007: What graphics product line does AMD offer to compete with NVIDIA's RTX series?

- Error: `None`
- Gold chunks: `[]`
- Hits@5: `[]`; Hits@20: `[]`
- Top PPR entities: amd (ORG), advanced micro devices (ORG), nvidia (ORG), nvidia corporation (ORG), rambus (ORG), amd radeon graphics (PRODUCT), amd radeon pro graphics (PRODUCT), amd rdna 3 graphics (PRODUCT)

| Rank | Chunk | Ticker | FY | Section | Score | Preview |
|---:|---|---|---:|---|---:|---|
| 1 | `NVDA_2025_Item_1_0009_7a56593b` | NVDA | 2025 | Item_1 | 4.518428 | •networking products consisting of switches, network adapters \(including DPUs\), and cable solutions \(including optical modules\) include such as AMD, Arista Networks, Broadcom, Cisco Systems, Inc., Hewlett Packard Enterprise Company, Huawei, Intel, Lumentum |
| 2 | `NVDA_2026_Item_1_0008_edf8fe4b` | NVDA | 2026 | Item_1 | 4.518428 | •networking products consisting of switches, network adapters \(including DPUs\), and cable solutions \(including optical modules\) include such as AMD, Arista Networks, Broadcom, Cisco Systems, Inc., Hewlett Packard Enterprise Company, Huawei, Intel, Lumentum |
| 3 | `AMD_2024_Item_1_0011_49024c2d` | AMD | 2024 | Item_1 | 4.384322 | Competition  The markets in which our products are sold are highly competitive and delivering the latest and best products to market on a timely basis is critical to achieving revenue growth. We believe that the main factors that determine our product competit |
| 4 | `AMD_2025_Item_1_0008_db609f8f` | AMD | 2025 | Item_1 | 4.384322 | Hyperscale Data Centers  Large multi-national public cloud service providers and hyperscale private data centers directly and indirectly purchase a substantial portion of our data center-focused products, including server CPUs, GPU accelerators, DPUs, FPGAs an |
| 5 | `AMD_2026_Item_1_0009_ac9cc232` | AMD | 2026 | Item_1 | 4.384322 | 8  * * *  Table of Contents    Hyperscale Data Centers  Large multi-national public cloud service providers and hyperscale private data centers directly and indirectly purchase a substantial portion of our data center-focused products, including server CPUs, G |

### T015: What is the relationship between KLA yield improvement tools and downstream AMD gross margin risk?

- Error: `None`
- Gold chunks: `[]`
- Hits@5: `[]`; Hits@20: `[]`
- Top PPR entities: kla (ORG), texas instruments (ORG), gross margin risk (RISK_FACTOR), geopolitical and trade restrictions (RISK_FACTOR), micron technology (ORG), amd (ORG), nvidia (ORG), tariffs (REGULATORY_REQUIREMENT)

| Rank | Chunk | Ticker | FY | Section | Score | Preview |
|---:|---|---|---:|---|---:|---|
| 1 | `MU_2025_Item_1A_0001_8d660135` | MU | 2025 | Item_1A | 3.864991 | •our ability to generate sufficient cash flows or obtain access to external financing;  •our debt obligations;  •changes in foreign currency exchange rates;  •counterparty default risk;  •volatility in the trading price of our common stock; and  •fluctuations  |
| 2 | `KLAC_2023_Item_7_0009_9b5b651f` | KLAC | 2023 | Item_7 | 3.379713 | Recent Accounting Pronouncements  For a description of recent accounting pronouncements, including those recently adopted and the expected dates of adoption as well as estimated effects, if any, on our Consolidated Financial Statements of those not yet adopted |
| 3 | `KLAC_2024_Item_7_0006_313cb934` | KLAC | 2024 | Item_7 | 3.379713 | Recent Accounting Pronouncements  For a description of recent accounting pronouncements, including those recently adopted and the expected dates of adoption as well as estimated effects, if any, on our Consolidated Financial Statements of those not yet adopted |
| 4 | `AMD_2025_Item_1_0009_c842eea0` | AMD | 2025 | Item_1 | 3.113024 | Competition in Client Segment  Our primary competitor in the supply of CPUs and APUs is Intel. A variety of companies provide or have developed Arm-based microprocessors and platforms which could lead to further adoption of Arm-based PC solutions.  Competition |
| 5 | `AMD_2026_Item_1_0010_460dfa17` | AMD | 2026 | Item_1 | 3.113024 | Competition in Client and Gaming Segment  Our primary competitor in the supply of CPUs and APUs is Intel. A variety of companies provide or have developed Arm-based microprocessors and platforms which could lead to further adoption of Arm-based PC solutions.   |

### T017: Which Taiwanese contract chipmaker fabricates AMD's processors?

- Error: `None`
- Gold chunks: `['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1A_0008_e84e4130']`
- Hits@5: `['AMD_2025_Item_1_0009_c842eea0']`; Hits@20: `['AMD_2025_Item_1_0009_c842eea0']`
- Top PPR entities: intel (ORG), amd (ORG), texas instruments (ORG), micron technology (ORG), china (GPE), rambus (ORG), taiwan (GPE), tsmc (ORG)

| Rank | Chunk | Ticker | FY | Section | Score | Preview |
|---:|---|---|---:|---|---:|---|
| 1 | `RMBS_2025_Item_1_0001_479b0c1e` | RMBS | 2025 | Item_1 | 3.300620 | We sell memory interface chips directly and indirectly to memory module manufacturers, OEMs and hyperscalers worldwide through multiple channels, including our direct sales force and distributors, and we employ sales personnel to support such operations in the |
| 2 | `AMD_2025_Item_1_0009_c842eea0` | AMD | 2025 | Item_1 | 3.267663 | Competition in Client Segment  Our primary competitor in the supply of CPUs and APUs is Intel. A variety of companies provide or have developed Arm-based microprocessors and platforms which could lead to further adoption of Arm-based PC solutions.  Competition |
| 3 | `AMD_2026_Item_1_0010_460dfa17` | AMD | 2026 | Item_1 | 3.267663 | Competition in Client and Gaming Segment  Our primary competitor in the supply of CPUs and APUs is Intel. A variety of companies provide or have developed Arm-based microprocessors and platforms which could lead to further adoption of Arm-based PC solutions.   |
| 4 | `NVDA_2025_Item_1_0008_a4407f7e` | NVDA | 2025 | Item_1 | 3.181618 | 8  * * *  Table of Contents  of growth, we may place non-cancellable inventory orders for certain product components in advance of our historical lead times, pay premiums, or provide deposits to secure future supply and capacity and may need to continue to do  |
| 5 | `NVDA_2024_Item_1_0007_bae70036` | NVDA | 2024 | Item_1 | 2.745429 | Seasonality  Our computing platforms serve a diverse set of markets such as data centers, gaming, professional visualization, and automotive. Our desktop gaming products typically see stronger revenue in the second half of our fiscal year. Historical seasonali |

### T018: Which gaming console makers partner with the Ryzen processor company?

- Error: `None`
- Gold chunks: `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359']`
- Hits@5: `['AMD_2024_Item_1_0006_e41aed21']`; Hits@20: `['AMD_2024_Item_1_0006_e41aed21']`
- Top PPR entities: amd (ORG), advanced micro devices (ORG), advanced micro devices inc (ORG), intel (ORG), microsoft (COMP), ryzen processors (PRODUCT), amd ryzen processors (PRODUCT), microsoft (ORG)

| Rank | Chunk | Ticker | FY | Section | Score | Preview |
|---:|---|---|---:|---|---:|---|
| 1 | `AMD_2024_Item_1_0006_e41aed21` | AMD | 2024 | Item_1 | 6.135224 | Gaming Products  Semi-Custom Products. Our semi-custom products are tailored, high-performance, customer-specific solutions based on our CPU, GPU and multi-media technologies. We work closely with our customers to define solutions to precisely match the requir |
| 2 | `AMD_2025_Item_1_0009_c842eea0` | AMD | 2025 | Item_1 | 5.860131 | Competition in Client Segment  Our primary competitor in the supply of CPUs and APUs is Intel. A variety of companies provide or have developed Arm-based microprocessors and platforms which could lead to further adoption of Arm-based PC solutions.  Competition |
| 3 | `AMD_2026_Item_1_0010_460dfa17` | AMD | 2026 | Item_1 | 5.860131 | Competition in Client and Gaming Segment  Our primary competitor in the supply of CPUs and APUs is Intel. A variety of companies provide or have developed Arm-based microprocessors and platforms which could lead to further adoption of Arm-based PC solutions.   |
| 4 | `AMD_2024_Item_1_0011_49024c2d` | AMD | 2024 | Item_1 | 5.525266 | Competition  The markets in which our products are sold are highly competitive and delivering the latest and best products to market on a timely basis is critical to achieving revenue growth. We believe that the main factors that determine our product competit |
| 5 | `AMD_2024_Item_1_0005_7be264c6` | AMD | 2024 | Item_1 | 5.511715 | Commercial CPUs. We offer enterprise-class desktop and mobile PC solutions sold as AMD PRO Mobile and AMD PRO desktop processors with Radeon™ graphics for the commercial market. AMD Ryzen PRO, AMD Threadripper PRO and AMD Athlon PRO processors solutions are de |

### T019: What revenue segments does the developer of EPYC processors disclose?

- Error: `None`
- Gold chunks: `['AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_7_0002_d4114c99']`
- Hits@5: `[]`; Hits@20: `['AMD_2024_Item_7_0002_d4114c99']`
- Top PPR entities: amd (ORG), advanced micro devices (ORG), advanced micro devices inc (ORG), advanced micro devices, inc. (ORG), revenue (FIN_METRIC), 5th generation amd epyc processors (PRODUCT), amd epyc cpus (PRODUCT), epyc (PRODUCT)

| Rank | Chunk | Ticker | FY | Section | Score | Preview |
|---:|---|---|---:|---|---:|---|
| 1 | `AMD_2025_Item_7_0000_16c93d97` | AMD | 2025 | Item_7 | 7.721698 | ITEM 7\. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  The following discussion should be read in conjunction with the Consolidated Financial Statements as of December 28, 2024 and December 30, 2023 and for each of the  |
| 2 | `AMD_2026_Item_7_0000_6b145a7b` | AMD | 2026 | Item_7 | 7.230604 | ITEM 7\. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  The following discussion should be read in conjunction with the Consolidated Financial Statements as of December 27, 2025 and December 28, 2024 and for each of the  |
| 3 | `AMD_2026_Item_7_0005_8ab9ed73` | AMD | 2026 | Item_7 | 6.948201 | 50  * * *  Table of Contents    Income Taxes. In determining taxable income for financial statement reporting purposes, we must make certain estimates and judgments. These estimates and judgments are applied in the calculation of certain tax liabilities and in |
| 4 | `AMD_2025_Item_7_0005_36426dd3` | AMD | 2025 | Item_7 | 6.802374 | Data Center  Data Center net revenue of $12.6 billion in 2024 increased by 94%, compared to net revenue of $6.5 billion in 2023. The increase was primarily driven by higher sales of AMD Instinct GPUs and AMD EPYC CPUs.  Data Center operating income was $3.5 bi |
| 5 | `AMD_2025_Item_7_0004_58e0bdd2` | AMD | 2025 | Item_7 | 6.579435 | 45  * * *  Table of Contents  Long-Lived and Intangible Assets. Long-lived and intangible assets to be held and used are reviewed for impairment if indicators of potential impairment exist and at least annually for indefinite-lived intangible assets. Impairmen |

### T030: Which cloud hyperscalers partner with the EPYC processor maker for server CPU deployments in their data centers?

- Error: `None`
- Gold chunks: `['AMD_2024_Item_1_0006_e41aed21', 'AMD_2026_Item_1_0004_b5e66359']`
- Hits@5: `[]`; Hits@20: `[]`
- Top PPR entities: advanced micro devices (ORG), amd (ORG), data center (SEGMENT), data center net revenue (FIN_METRIC), data center segment (SEGMENT), 4th gen amd epyc cpus (PRODUCT), amd epyc cpus (PRODUCT), amd epyc processors (PRODUCT)

| Rank | Chunk | Ticker | FY | Section | Score | Preview |
|---:|---|---|---:|---|---:|---|
| 1 | `AMD_2025_Item_7_0005_36426dd3` | AMD | 2025 | Item_7 | 5.703321 | Data Center  Data Center net revenue of $12.6 billion in 2024 increased by 94%, compared to net revenue of $6.5 billion in 2023. The increase was primarily driven by higher sales of AMD Instinct GPUs and AMD EPYC CPUs.  Data Center operating income was $3.5 bi |
| 2 | `AMD_2024_Item_1_0011_49024c2d` | AMD | 2024 | Item_1 | 5.297910 | Competition  The markets in which our products are sold are highly competitive and delivering the latest and best products to market on a timely basis is critical to achieving revenue growth. We believe that the main factors that determine our product competit |
| 3 | `AMD_2025_Item_1_0008_db609f8f` | AMD | 2025 | Item_1 | 5.297910 | Hyperscale Data Centers  Large multi-national public cloud service providers and hyperscale private data centers directly and indirectly purchase a substantial portion of our data center-focused products, including server CPUs, GPU accelerators, DPUs, FPGAs an |
| 4 | `AMD_2026_Item_1_0009_ac9cc232` | AMD | 2026 | Item_1 | 5.297910 | 8  * * *  Table of Contents    Hyperscale Data Centers  Large multi-national public cloud service providers and hyperscale private data centers directly and indirectly purchase a substantial portion of our data center-focused products, including server CPUs, G |
| 5 | `AMD_2024_Item_7_0005_86aec648` | AMD | 2024 | Item_7 | 5.261595 | Income Taxes. In determining taxable income for financial statement reporting purposes, we must make certain estimates and judgments. These estimates and judgments are applied in the calculation of certain tax liabilities and in the determination of the recove |
