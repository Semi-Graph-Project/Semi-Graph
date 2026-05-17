# vector_search() End-to-End Validation — Phase C2

**Queries tested:** 17  
**top_k_chunks:** 5  
**Pipeline:** query → BGE encode → chunk_embedding cosine top-k
**Baseline:** Homogeneous Vector RAG (no graph signal, no threshold)

---

## Acceptance Summary

| Check | Pass | Fail | Note |
|---|---|---|---|
| Deterministic across 2 runs | 17/17 | 0 | byte-identical chunk_id + score |
| No duplicate chunk_ids       | 17/17 | 0 | within a single query result |
| Provenance fields present    | 17/17 | 0 | chunk_id/ticker/fiscal_year/section |
| Non-empty results            | 17/17 | 0 | vector RAG returns top-k regardless |

---

## Group: Original C3 set

### `AMD`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'AMD': 5}
- **section distribution:** {'Item_1': 4, 'Item_7': 1}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.888 | AMD | 2024 | Item_1 | References in this Annual Report on Form 10-K to “AMD,” “we,” “us,” “management,” “our” or... |
| 2 | 0.873 | AMD | 2024 | Item_7 | We continued to expand our Client product portfolio by launching our Ryzen 7000 Series Mob... |
| 3 | 0.871 | AMD | 2025 | Item_1 | Our Strategy  We believe that AI is defining the next era of computing and that the full p... |
| 4 | 0.870 | AMD | 2025 | Item_1 | Professional GPUs. Our AMD Radeon PRO family of professional graphics products are designe... |
| 5 | 0.868 | AMD | 2025 | Item_1 | Client Products  Desktop CPUs. Our CPUs and APUs for desktop platforms currently include t... |

---

### `TSMC supply chain`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'MU': 2, 'NVDA': 2, 'AMD': 1}
- **section distribution:** {'Item_1': 3, 'Item_1A': 2}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.855 | MU | 2025 | Item_1 | Resources    Supply Chain, Materials, and Third-Party Service Providers    Our supply chai... |
| 2 | 0.846 | NVDA | 2025 | Item_1 | 8  * * *  Table of Contents  of growth, we may place non-cancellable inventory orders for ... |
| 3 | 0.845 | NVDA | 2026 | Item_1 | We have expanded our supplier relationships to build redundancy and resilience in our oper... |
| 4 | 0.843 | AMD | 2026 | Item_1A | We cannot guarantee that these manufacturers or our other third-party manufacturing suppli... |
| 5 | 0.841 | MU | 2025 | Item_1A | We operate in a dynamic and rapidly evolving industry where the timeframes for product tra... |

---

### `Compare R&D Alphabet vs Meta 2023`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'MU': 2, 'AMD': 1, 'NVDA': 2}
- **section distribution:** {'Item_1': 2, 'Item_7': 2, 'Item_1A': 1}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.809 | MU | 2025 | Item_1 | 15 \| 2025 10-K  * * *  Table of Contents    Research and Development    Our R&D efforts ar... |
| 2 | 0.804 | AMD | 2025 | Item_7 | Research and development expenses of $6.5 billion in 2024 increased by $584 million, or 10... |
| 3 | 0.804 | NVDA | 2025 | Item_7 | Product Transitions and New Product Introductions  Product transitions are complex and we ... |
| 4 | 0.803 | MU | 2024 | Item_1 | 14  * * *  Table of Contents    R&D expenses vary primarily with the number of development... |
| 5 | 0.800 | NVDA | 2026 | Item_1A | We are increasing our U.S.-based manufacturing and investing in specialized equipment and ... |

---

### `china semiconductor ban`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'AMD': 3, 'NVDA': 2}
- **section distribution:** {'Item_1A': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.872 | AMD | 2026 | Item_1A | We are subject to U.S. laws and regulations, including the Export Administration Regulatio... |
| 2 | 0.870 | NVDA | 2025 | Item_1A | 26  * * *  Table of Contents  Over the past three years, we have been subject to a series ... |
| 3 | 0.869 | AMD | 2026 | Item_1A | The United States and other countries’ export control regulations continue to focus on tar... |
| 4 | 0.864 | NVDA | 2024 | Item_1A | Export controls could disrupt our supply chain and distribution channels, negatively impac... |
| 5 | 0.863 | AMD | 2025 | Item_1A | United States export control regulations include restrictions or prohibitions on the sale ... |

---

## Group: Single-hop entity

### `NVIDIA Blackwell GPU architecture`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 5}
- **section distribution:** {'Item_1': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.912 | NVDA | 2026 | Item_1 | In fiscal year 2025, we announced the NVIDIA Blackwell GeForce RTX 50 Series family of des... |
| 2 | 0.890 | NVDA | 2025 | Item_1 | In fiscal year 2025, we launched the NVIDIA Blackwell GeForce RTX 50 Series family of desk... |
| 3 | 0.847 | NVDA | 2026 | Item_1 | Item 1. Business  Our Company  NVIDIA pioneered accelerated computing to help solve the mo... |
| 4 | 0.844 | NVDA | 2025 | Item_1 | In addition, we offer a scalable data center-based simulation solution based on NVIDIA Omn... |
| 5 | 0.840 | NVDA | 2024 | Item_1 | Item 1. Business  Our Company  NVIDIA pioneered accelerated computing to help solve the mo... |

---

### `Micron HBM memory products`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'MU': 5}
- **section distribution:** {'Item_1': 4, 'Item_1A': 1}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.872 | MU | 2023 | Item_1 | ITEM 1. BUSINESS      Overview    We are an industry leader in innovative memory and stora... |
| 2 | 0.870 | MU | 2025 | Item_1 | ITEM 1. BUSINESS      Overview    We are an industry leader in innovative memory and stora... |
| 3 | 0.869 | MU | 2024 | Item_1 | ITEM 1. BUSINESS      Overview    We are an industry leader in innovative memory and stora... |
| 4 | 0.864 | MU | 2025 | Item_1A | The competitive nature of our industry could have a material adverse effect on our busines... |
| 5 | 0.861 | MU | 2025 | Item_1 | 15 \| 2025 10-K  * * *  Table of Contents    Research and Development    Our R&D efforts ar... |

---

### `CHIPS Act semiconductor manufacturing`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'MU': 5}
- **section distribution:** {'Item_7': 1, 'Item_1A': 2, 'Item_1': 2}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.882 | MU | 2025 | Item_7 | 56  * * *  Table of Contents    In addition to the CHIPS Act direct funding, we receive a ... |
| 2 | 0.877 | MU | 2024 | Item_1A | \| \| \| \| \| ---\|---\|---\|---\|---\|--- Location\| Principal Operations \| Taiwan\| R&D, wafer fabr... |
| 3 | 0.866 | MU | 2025 | Item_1A | We believe that our existing facilities are suitable and adequate for our present purposes... |
| 4 | 0.866 | MU | 2023 | Item_1 | Wafer fabrication occurs in a highly-controlled clean environment to minimize yield loss f... |
| 5 | 0.866 | MU | 2025 | Item_1 | Wafer fabrication occurs in a highly controlled clean environment to minimize yield loss f... |

---

## Group: Multi-hop financial

### `Hopper data center segment revenue`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 3, 'MU': 1, 'AMD': 1}
- **section distribution:** {'Item_7': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.860 | NVDA | 2024 | Item_7 | Operating Income by Reportable Segments  \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| ---... |
| 2 | 0.857 | NVDA | 2026 | Item_7 | Graphics revenue – The year over year increase was driven by sales of our Blackwell archit... |
| 3 | 0.854 | MU | 2025 | Item_7 | Percentages of total revenue may not total 100% due to rounding.    Changes in revenue for... |
| 4 | 0.852 | AMD | 2025 | Item_7 | Data Center  Data Center net revenue of $12.6 billion in 2024 increased by 94%, compared t... |
| 5 | 0.844 | NVDA | 2026 | Item_7 | Gross margins decreased to 71.1% in fiscal year 2026 from 75.0% in fiscal year 2025 as our... |

---

### `Micron bit shipments average selling price`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'MU': 5}
- **section distribution:** {'Item_1A': 2, 'Item_7': 1, 'Item_1': 2}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.843 | MU | 2024 | Item_1A | •our debt obligations;  •changes in foreign currency exchange rates;  •counterparty defaul... |
| 2 | 0.836 | MU | 2025 | Item_7 | Total Revenue: Total revenue was impacted by the factors described in the section titled “... |
| 3 | 0.831 | MU | 2025 | Item_1 | ITEM 1. BUSINESS      Overview    We are an industry leader in innovative memory and stora... |
| 4 | 0.830 | MU | 2025 | Item_1A | •our ability to generate sufficient cash flows or obtain access to external financing;  •o... |
| 5 | 0.829 | MU | 2023 | Item_1 | ITEM 1. BUSINESS      Overview    We are an industry leader in innovative memory and stora... |

---

### `AMD gross margin trends`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'MU': 2, 'AMD': 2, 'NVDA': 1}
- **section distribution:** {'Item_7': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.857 | MU | 2024 | Item_7 | Our consolidated gross margin percentage decreased to negative 9% for 2023 from 45% for 20... |
| 2 | 0.843 | AMD | 2025 | Item_7 | ITEM 7\. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERAT... |
| 3 | 0.843 | AMD | 2024 | Item_7 | Against the backdrop of a mixed demand environment, net revenue for 2023 was $22.7 billion... |
| 4 | 0.842 | NVDA | 2024 | Item_7 | Operating Income by Reportable Segments  \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| \| ---... |
| 5 | 0.841 | MU | 2025 | Item_7 | Total Revenue: Total revenue was impacted by the factors described in the section titled “... |

---

## Group: Multi-hop relational

### `Xilinx acquisition impact on AMD`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'AMD': 5}
- **section distribution:** {'Item_7': 4, 'Item_1A': 1}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.884 | AMD | 2024 | Item_7 | Against the backdrop of a mixed demand environment, net revenue for 2023 was $22.7 billion... |
| 2 | 0.860 | AMD | 2024 | Item_7 | Client  Client net revenue of $4.7 billion in 2023 decreased by 25%, compared to net reven... |
| 3 | 0.847 | AMD | 2026 | Item_7 | In October 2025, we entered into a product purchase agreement with OpenAI OpCo, LLC, \(Ope... |
| 4 | 0.845 | AMD | 2026 | Item_7 | In 2025, we returned a total of $1.3 billion to shareholders through the repurchase of 12.... |
| 5 | 0.845 | AMD | 2025 | Item_1A | The demand for our products depends in part on the market conditions in the industries int... |

---

### `adverse economic conditions impact on revenue`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'AMD': 3, 'MU': 2}
- **section distribution:** {'Item_1A': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.888 | AMD | 2025 | Item_1A | Economic and market uncertainty may adversely impact our business and operating results.  ... |
| 2 | 0.888 | AMD | 2024 | Item_1A | Economic and market uncertainty may adversely impact our business and operating results.  ... |
| 3 | 0.882 | AMD | 2026 | Item_1A | Economic and market uncertainty may adversely impact our business and operating results.  ... |
| 4 | 0.878 | MU | 2024 | Item_1A | 28  * * *  Table of Contents    Our inability to source materials, supplies, capital equip... |
| 5 | 0.877 | MU | 2025 | Item_1A | If production is disrupted for any reason, manufacturing yields may be adversely affected,... |

---

### `NVIDIA AMD competitive landscape`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'AMD': 5}
- **section distribution:** {'Item_1A': 2, 'Item_1': 3}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.908 | AMD | 2025 | Item_1A | Nvidia’s dominance in the graphics processing unit market and its aggressive business prac... |
| 2 | 0.893 | AMD | 2024 | Item_1 | Competition  The markets in which our products are sold are highly competitive and deliver... |
| 3 | 0.883 | AMD | 2026 | Item_1 | Competition in Client and Gaming Segment  Our primary competitor in the supply of CPUs and... |
| 4 | 0.880 | AMD | 2025 | Item_1 | Competition in Client Segment  Our primary competitor in the supply of CPUs and APUs is In... |
| 5 | 0.868 | AMD | 2026 | Item_1A | Our competitors may use their market position and financial resources to market and price ... |

---

## Group: Geographic/regulatory

### `US export controls on AI chips to China`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'AMD': 3, 'NVDA': 2}
- **section distribution:** {'Item_1A': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.930 | AMD | 2025 | Item_1A | United States export control regulations include restrictions or prohibitions on the sale ... |
| 2 | 0.920 | AMD | 2026 | Item_1A | The United States and other countries’ export control regulations continue to focus on tar... |
| 3 | 0.911 | NVDA | 2025 | Item_1A | Such restrictions could include additional unilateral or multilateral export controls on c... |
| 4 | 0.909 | AMD | 2026 | Item_1A | We are subject to U.S. laws and regulations, including the Export Administration Regulatio... |
| 5 | 0.902 | NVDA | 2025 | Item_1A | 26  * * *  Table of Contents  Over the past three years, we have been subject to a series ... |

---

### `Taiwan manufacturing dependency risk`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'AMD': 4, 'MU': 1}
- **section distribution:** {'Item_1A': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.864 | AMD | 2026 | Item_1A | 40  * * *  Table of Contents    General Risks  Our worldwide operations are subject to pol... |
| 2 | 0.864 | AMD | 2025 | Item_1A | General Risks  Our worldwide operations are subject to political, legal and economic risks... |
| 3 | 0.863 | AMD | 2024 | Item_1A | General Risks  Our worldwide operations are subject to political, legal and economic risks... |
| 4 | 0.860 | AMD | 2024 | Item_1A | Other risks associated with our dependence on third-party manufacturers include limited co... |
| 5 | 0.860 | MU | 2023 | Item_1A | 27 \| 2023 10-K  * * *  Table of Contents    Our operations are dependent on our ability to... |

---

### `EU AI Act compliance requirements`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 2, 'AMD': 3}
- **section distribution:** {'Item_1A': 5}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.892 | NVDA | 2025 | Item_1A | Governments and regulators are also considering, and in certain cases, have imposed restri... |
| 2 | 0.892 | NVDA | 2026 | Item_1A | 24  * * *  Table of Contents  we may face increased compliance costs as a result of change... |
| 3 | 0.891 | AMD | 2026 | Item_1A | In addition, many governments have enacted laws around PII, such as the GDPR and the CCPA,... |
| 4 | 0.891 | AMD | 2025 | Item_1A | In addition, many governments have enacted laws around PII, such as the GDPR and the CCPA,... |
| 5 | 0.886 | AMD | 2024 | Item_1A | In addition, many governments have enacted laws around PII, such as the GDPR and the CCPA,... |

---

## Group: Edge case (off-corpus)

### `qwerty zzz random nonsense xyz`

- **chunks returned:** 5
- **deterministic:** ✓
- **no duplicate ids:** ✓
- **provenance ok:** ✓
- **ticker distribution:** {'NVDA': 1, 'MU': 3, 'AMD': 1}
- **section distribution:** {'Item_7': 1, 'Item_1': 4}

| # | score | ticker | FY | section | text preview |
|---|---|---|---|---|---|
| 1 | 0.755 | NVDA | 2025 | Item_7 | The following table sets forth, for the periods indicated, certain items in our Consolidat... |
| 2 | 0.750 | MU | 2023 | Item_1 | 18  * * *  Table of Contents    \| \| \| \| \| \| \| \| \| \| \| ---\|---\|---\|---\|---\|---\|---\|---\|---\|... |
| 3 | 0.748 | MU | 2024 | Item_1 | 18  * * *  Table of Contents    \| \| \| \| \| \| \| \| \| \| \| ---\|---\|---\|---\|---\|---\|---\|---\|---\|... |
| 4 | 0.747 | MU | 2024 | Item_1 | Investors and others should note that we announce material financial information about our... |
| 5 | 0.741 | AMD | 2026 | Item_1 | On the Investor Relations pages of our website, http://ir.amd.com, we post links to our fi... |

---

