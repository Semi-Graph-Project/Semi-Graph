# graph_search() End-to-End Validation — Phase C1c

**Queries tested:** 17  
**top_k_chunks:** 5  
**Pipeline:** triple_seeds → run_ppr → cluster → map_chunks

---

## Acceptance Summary

| Check | Pass | Fail | Note |
|---|---|---|---|
| Deterministic across 2 runs | 17/17 | 0 | byte-identical chunk_id + score |
| No duplicate chunk_ids       | 17/17 | 0 | within a single query result |
| Provenance fields present    | 17/17 | 0 | chunk_id/ticker/fiscal_year/section |
| Non-empty results            | 17/17 | 0 | off-corpus queries may be 0 |

---

## Group: Original C3 set

### `AMD`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 5}
- **section distribution:** {'Item_1': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 2.893 | NVDA | 2026 | Item_1 | We have expanded our supplier relationships to build redundancy and resilience in our oper... |
| 2 | 2.865 | NVDA | 2024 | Item_1 | Our current competitors include:  •suppliers and licensors of hardware and software for di... |
| 3 | 2.839 | NVDA | 2024 | Item_1 | •Providing training and education to managers and peers on fostering supportive environmen... |
| 4 | 2.679 | NVDA | 2025 | Item_1 | 8  * * *  Table of Contents  of growth, we may place non-cancellable inventory orders for ... |
| 5 | 2.671 | NVDA | 2025 | Item_1 | •networking products consisting of switches, network adapters \(including DPUs\), and cabl... |

---

### `TSMC supply chain`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 3, 'AMD': 2}
- **section distribution:** {'Item_1': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 2.474 | NVDA | 2025 | Item_1 | 8  * * *  Table of Contents  of growth, we may place non-cancellable inventory orders for ... |
| 2 | 2.463 | AMD | 2025 | Item_1 | Competition in Client Segment  Our primary competitor in the supply of CPUs and APUs is In... |
| 3 | 2.455 | NVDA | 2024 | Item_1 | Seasonality  Our computing platforms serve a diverse set of markets such as data centers, ... |
| 4 | 2.455 | NVDA | 2026 | Item_1 | We have expanded our supplier relationships to build redundancy and resilience in our oper... |
| 5 | 2.444 | AMD | 2026 | Item_1 | Competition in Client and Gaming Segment  Our primary competitor in the supply of CPUs and... |

---

### `Compare R&D Alphabet vs Meta 2023`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 3, 'AMD': 2}
- **section distribution:** {'Item_1': 4, 'Item_1A': 1}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 2.458 | NVDA | 2024 | Item_1 | Seasonality  Our computing platforms serve a diverse set of markets such as data centers, ... |
| 2 | 2.458 | NVDA | 2025 | Item_1 | 8  * * *  Table of Contents  of growth, we may place non-cancellable inventory orders for ... |
| 3 | 2.458 | NVDA | 2026 | Item_1 | We have expanded our supplier relationships to build redundancy and resilience in our oper... |
| 4 | 2.267 | AMD | 2026 | Item_1 | Competition in Client and Gaming Segment  Our primary competitor in the supply of CPUs and... |
| 5 | 2.191 | AMD | 2026 | Item_1A | Our ability to design and introduce new products in a timely manner includes the use of th... |

---

### `china semiconductor ban`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'MU': 3, 'NVDA': 2}
- **section distribution:** {'Item_1A': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 1.690 | MU | 2023 | Item_1A | Political, economic, or other actions may adversely affect our operations in Taiwan. A maj... |
| 2 | 1.630 | NVDA | 2025 | Item_1A | In addition to export controls, the USG may impose restrictions on the import and sale of ... |
| 3 | 1.507 | NVDA | 2024 | Item_1A | Given the increasing strategic importance of AI and rising geopolitical tensions, the USG ... |
| 4 | 1.507 | MU | 2023 | Item_1A | Our inability to prevent deterioration of or improve gross margins could have a material a... |
| 5 | 1.447 | MU | 2025 | Item_1A | In addition, the U.S. government has in the past and continues to restrict American firms,... |

---

## Group: Single-hop entity

### `NVIDIA Blackwell GPU architecture`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 5}
- **section distribution:** {'Item_7': 3, 'Item_1': 2}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 2.356 | NVDA | 2025 | Item_7 | 37  * * *  Table of Contents  Israel and Regional Conflicts  We are monitoring the impact ... |
| 2 | 2.352 | NVDA | 2026 | Item_7 | Contracts with Multiple Performance Obligations  Our contracts may contain more than one p... |
| 3 | 2.344 | NVDA | 2026 | Item_7 | Graphics revenue – The year over year increase was driven by sales of our Blackwell archit... |
| 4 | 2.329 | NVDA | 2025 | Item_1 | •networking products consisting of switches, network adapters \(including DPUs\), and cabl... |
| 5 | 2.301 | NVDA | 2025 | Item_1 | industry standard servers from every major cloud provider and server maker. Beyond GPUs, o... |

---

### `Micron HBM memory products`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'MU': 5}
- **section distribution:** {'Item_1A': 1, 'Item_1': 3, 'Item_7': 1}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 1.954 | MU | 2023 | Item_1A | Political, economic, or other actions may adversely affect our operations in Taiwan. A maj... |
| 2 | 1.876 | MU | 2023 | Item_1 | 18  * * *  Table of Contents    \| \| \| \| \| \| \| \| \| \| \| ---\|---\|---\|---\|---\|---\|---\|---\|---\|... |
| 3 | 1.408 | MU | 2025 | Item_7 | ITEM 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATI... |
| 4 | 1.363 | MU | 2023 | Item_1 | 7 \| 2023 10-K  * * *  Table of Contents    NAND: NAND products are non-volatile, re-writea... |
| 5 | 1.363 | MU | 2025 | Item_1 | DRAM: DRAM products are dynamic random access memory semiconductor devices with low latenc... |

---

### `CHIPS Act semiconductor manufacturing`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 3, 'MU': 2}
- **section distribution:** {'Item_1': 3, 'Item_7': 1, 'Item_1A': 1}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 1.697 | NVDA | 2026 | Item_1 | We have expanded our supplier relationships to build redundancy and resilience in our oper... |
| 2 | 1.669 | NVDA | 2024 | Item_1 | Seasonality  Our computing platforms serve a diverse set of markets such as data centers, ... |
| 3 | 1.669 | NVDA | 2025 | Item_1 | 8  * * *  Table of Contents  of growth, we may place non-cancellable inventory orders for ... |
| 4 | 1.425 | MU | 2023 | Item_7 | Other: Further information can be found in the following notes contained in “Item 8. Finan... |
| 5 | 1.086 | MU | 2024 | Item_1A | \| \| \| \| \| ---\|---\|---\|---\|---\|--- Location\| Principal Operations \| Taiwan\| R&D, wafer fabr... |

---

## Group: Multi-hop financial

### `Hopper data center segment revenue`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 5}
- **section distribution:** {'Item_7': 4, 'Item_1': 1}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 1.911 | NVDA | 2025 | Item_7 | 37  * * *  Table of Contents  Israel and Regional Conflicts  We are monitoring the impact ... |
| 2 | 1.884 | NVDA | 2026 | Item_7 | Revenue for fiscal year 2026 was $215.9 billion, up 65% from a year ago.  Data Center reve... |
| 3 | 1.766 | NVDA | 2024 | Item_7 | Operating Income by Reportable Segments  \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| ---... |
| 4 | 1.748 | NVDA | 2024 | Item_1 | Seasonality  Our computing platforms serve a diverse set of markets such as data centers, ... |
| 5 | 1.744 | NVDA | 2024 | Item_7 | 35  * * *  Table of Contents  Fiscal Year 2024 Summary  \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| ... |

---

### `Micron bit shipments average selling price`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'MU': 4, 'NVDA': 1}
- **section distribution:** {'Item_7': 4, 'Item_1': 1}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 1.953 | MU | 2023 | Item_7 | Total Revenue: Total revenue for 2023 was adversely impacted by the factors described in t... |
| 2 | 1.856 | MU | 2023 | Item_7 | ITEM 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATI... |
| 3 | 1.298 | MU | 2025 | Item_7 | ITEM 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATI... |
| 4 | 1.179 | MU | 2023 | Item_7 | Other: Further information can be found in the following notes contained in “Item 8. Finan... |
| 5 | 1.134 | NVDA | 2024 | Item_1 | Seasonality  Our computing platforms serve a diverse set of markets such as data centers, ... |

---

### `AMD gross margin trends`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 5}
- **section distribution:** {'Item_1': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 2.367 | NVDA | 2024 | Item_1 | Seasonality  Our computing platforms serve a diverse set of markets such as data centers, ... |
| 2 | 2.317 | NVDA | 2025 | Item_1 | 8  * * *  Table of Contents  of growth, we may place non-cancellable inventory orders for ... |
| 3 | 2.317 | NVDA | 2026 | Item_1 | We have expanded our supplier relationships to build redundancy and resilience in our oper... |
| 4 | 1.977 | NVDA | 2024 | Item_1 | Our current competitors include:  •suppliers and licensors of hardware and software for di... |
| 5 | 1.977 | NVDA | 2025 | Item_1 | •networking products consisting of switches, network adapters \(including DPUs\), and cabl... |

---

## Group: Multi-hop relational

### `Xilinx acquisition impact on AMD`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'AMD': 5}
- **section distribution:** {'Item_1A': 3, 'Item_7': 2}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 2.479 | AMD | 2024 | Item_1A | Furthermore, we may at times invest in private companies to further our strategic objectiv... |
| 2 | 2.470 | AMD | 2025 | Item_1A | We intend to seek a strategic partner to acquire ZT Systems' manufacturing business, and w... |
| 3 | 2.439 | AMD | 2025 | Item_1A | ◦Costs related to defective products could have a material adverse effect on us.  ◦We may ... |
| 4 | 2.414 | AMD | 2024 | Item_7 | Against the backdrop of a mixed demand environment, net revenue for 2023 was $22.7 billion... |
| 5 | 2.388 | AMD | 2024 | Item_7 | Client  Client net revenue of $4.7 billion in 2023 decreased by 25%, compared to net reven... |

---

### `adverse economic conditions impact on revenue`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 5}
- **section distribution:** {'Item_7': 3, 'Item_1A': 2}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 1.102 | NVDA | 2025 | Item_7 | Direct Customers – Sales to direct customers which represented 10% or more of total revenu... |
| 2 | 1.092 | NVDA | 2024 | Item_1A | 18  * * *  Table of Contents  training data that may originate from third parties and new ... |
| 3 | 1.092 | NVDA | 2025 | Item_1A | For example, in fiscal year 2023, a defect was identified in a third-party component embed... |
| 4 | 1.003 | NVDA | 2025 | Item_7 | We expanded our Data Center product portfolio to offer new solutions, including those for ... |
| 5 | 1.003 | NVDA | 2026 | Item_7 | In February 2026, the USG granted a license that would allow us to ship small amounts of H... |

---

### `NVIDIA AMD competitive landscape`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 5}
- **section distribution:** {'Item_1': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 1.686 | NVDA | 2024 | Item_1 | Seasonality  Our computing platforms serve a diverse set of markets such as data centers, ... |
| 2 | 1.686 | NVDA | 2026 | Item_1 | We have expanded our supplier relationships to build redundancy and resilience in our oper... |
| 3 | 1.680 | NVDA | 2024 | Item_1 | Our current competitors include:  •suppliers and licensors of hardware and software for di... |
| 4 | 1.675 | NVDA | 2025 | Item_1 | 8  * * *  Table of Contents  of growth, we may place non-cancellable inventory orders for ... |
| 5 | 1.672 | NVDA | 2025 | Item_1 | •networking products consisting of switches, network adapters \(including DPUs\), and cabl... |

---

## Group: Geographic/regulatory

### `US export controls on AI chips to China`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 5}
- **section distribution:** {'Item_1': 4, 'Item_1A': 1}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 2.177 | NVDA | 2024 | Item_1 | Our current competitors include:  •suppliers and licensors of hardware and software for di... |
| 2 | 2.177 | NVDA | 2025 | Item_1 | •networking products consisting of switches, network adapters \(including DPUs\), and cabl... |
| 3 | 2.177 | NVDA | 2026 | Item_1 | •networking products consisting of switches, network adapters \(including DPUs\), and cabl... |
| 4 | 1.961 | NVDA | 2025 | Item_1A | Such restrictions could include additional unilateral or multilateral export controls on c... |
| 5 | 1.945 | NVDA | 2026 | Item_1 | We have expanded our supplier relationships to build redundancy and resilience in our oper... |

---

### `Taiwan manufacturing dependency risk`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'MU': 4, 'AMD': 1}
- **section distribution:** {'Item_1A': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 3.729 | MU | 2023 | Item_1A | Increases in sales of system solutions may increase our dependency upon specific customers... |
| 2 | 1.063 | MU | 2023 | Item_1A | Our inability to prevent deterioration of or improve gross margins could have a material a... |
| 3 | 1.015 | MU | 2023 | Item_1A | Political, economic, or other actions may adversely affect our operations in Taiwan. A maj... |
| 4 | 1.009 | AMD | 2024 | Item_1A | Failure to achieve expected manufacturing yields for our products could negatively impact ... |
| 5 | 0.881 | MU | 2025 | Item_1A | In addition, the U.S. government has in the past and continues to restrict American firms,... |

---

### `EU AI Act compliance requirements`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 3, 'AMD': 2}
- **section distribution:** {'Item_1A': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 2.004 | NVDA | 2025 | Item_1A | In the United States, federal, state and local authorities have enacted numerous data priv... |
| 2 | 1.931 | NVDA | 2026 | Item_1A | 24  * * *  Table of Contents  we may face increased compliance costs as a result of change... |
| 3 | 1.738 | NVDA | 2024 | Item_1A | 28  * * *  Table of Contents  to the collection, use, retention, security or disclosure of... |
| 4 | 1.543 | AMD | 2024 | Item_1A | In addition, many governments have enacted laws around PII, such as the GDPR and the CCPA,... |
| 5 | 1.531 | AMD | 2025 | Item_1A | In addition, many governments have enacted laws around PII, such as the GDPR and the CCPA,... |

---

## Group: Edge case (off-corpus)

### `qwerty zzz random nonsense xyz`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'AMD': 5}
- **section distribution:** {'Item_1': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.941 | AMD | 2024 | Item_1 | Our four reportable segments are:  •the Data Center segment, which primarily includes serv... |
| 2 | 0.941 | AMD | 2025 | Item_1 | •the Embedded segment, which primarily includes embedded CPUs, GPUs, APUs, FPGAs, SOMs, an... |
| 3 | 0.941 | AMD | 2026 | Item_1 | •the Client and Gaming segment, which primarily includes CPUs, APUs, chipsets for desktops... |
| 4 | 0.937 | AMD | 2026 | Item_1 | To address anticipated future remediation costs under the orders, we have computed and rec... |
| 5 | 0.929 | AMD | 2024 | Item_1 | References in this Annual Report on Form 10-K to “AMD,” “we,” “us,” “management,” “our” or... |

---

