# Held-Out Multi-hop Evaluation — 3-config (Phase C2-quater)

**Held-out set authored before any tuning to bound test-set leakage.**
Compare these numbers against `multihop_synthesized_eval.md` (dev set N=20)
after tuning — large drop = overfit to dev set.

**N queries:** 10 · **top_k:** 5
**Tools:** vector_search, graph_search, hybrid_search (RRF k=60)

---

## Aggregate — 3-config

| Metric | vector | graph | **hybrid** | hyb − vec |
|---|---|---|---|---|
| Hit@5 | 7/10 | 7/10 | **8/10** | +1 |
| Avg Recall@5 | 0.390 | 0.420 | **0.450** | +0.060 |
| Best-of-3 wins | 3 | 2 | **0** | — (ties: 5) |

### Pairwise: hybrid vs vector (primary thesis)

- **hybrid > vector**: 3/10 queries
- hybrid = vector: 4/10 queries
- hybrid < vector: 3/10 queries (RRF floor should give 0)

**Verdict:** ⚠ hybrid < vector on 3 queries

---

## H1: `Which Korean memory chip supplier provides components to NVIDIA's data center GPUs?`

- **type:** supplier_via_product
- **chain:** `NVIDIA <-SUPPLIES- {SK Hynix, Samsung Electronics}`
- **answer entities:** `['sk hynix inc', 'samsung electronics co ltd']`
- **expected chunks in corpus:** 4

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.25 | 1/5 | `AMD_2026_Item_1_0003_ea53a6a5...`, `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2025_Item_1_0003_861e4bfa...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `AMD_2025_Item_1_0009_c842eea0...` |
| graph  | 1 | 0.25 | 1/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...` |
| **hybrid** | **1** | **0.25** | **1/5** | `NVDA_2026_Item_1_0007_bf6a51b6...`, `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2025_Item_1_0009_c842eea0...`, `NVDA_2025_Item_1_0002_b74647bb...`, `NVDA_2024_Item_1_0002_2ddf2e3b...` |

**Winner:** tie

_vector hits:_ ['NVDA_2026_Item_1_0007_bf6a51b6']

_graph hits:_ ['NVDA_2026_Item_1_0007_bf6a51b6']

_hybrid hits:_ ['NVDA_2026_Item_1_0007_bf6a51b6']

---

## H2: `What parallel computing software platform comes from the developer of Hopper architecture?`

- **type:** product_via_product
- **chain:** `Hopper -PRODUCES-> NVIDIA -PRODUCES-> CUDA`
- **answer entities:** `['cuda']`
- **expected chunks in corpus:** 17

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `NVDA_2025_Item_1_0003_ccc9ed65...`, `NVDA_2025_Item_1_0005_85d95b7e...`, `NVDA_2024_Item_1_0003_59fa75a8...`, `NVDA_2026_Item_1_0005_9725a5a2...`, `NVDA_2024_Item_1_0005_7f985cdb...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_7_0007_d25e117d...`, `NVDA_2025_Item_7_0000_78a2a641...`, `NVDA_2024_Item_7_0003_ba144df9...`, `NVDA_2024_Item_7_0000_fb7753f5...`, `NVDA_2025_Item_7_0007_81d515b2...` |
| **hybrid** | **1** | **0.80** | **4/5** | `NVDA_2025_Item_1_0003_ccc9ed65...`, `NVDA_2024_Item_1_0003_59fa75a8...`, `NVDA_2026_Item_1_0003_0297d539...`, `NVDA_2024_Item_7_0007_d25e117d...`, `NVDA_2025_Item_1_0005_85d95b7e...` |

**Winner:** vector

_vector hits:_ ['NVDA_2024_Item_1_0003_59fa75a8', 'NVDA_2024_Item_1_0005_7f985cdb', 'NVDA_2025_Item_1_0003_ccc9ed65', 'NVDA_2025_Item_1_0005_85d95b7e', 'NVDA_2026_Item_1_0005_9725a5a2']

_hybrid hits:_ ['NVDA_2024_Item_1_0003_59fa75a8', 'NVDA_2025_Item_1_0003_ccc9ed65', 'NVDA_2025_Item_1_0005_85d95b7e', 'NVDA_2026_Item_1_0003_0297d539']

---

## H3: `Which generative AI research lab partners with the maker of EPYC processors?`

- **type:** partner_via_product
- **chain:** `EPYC -PRODUCES-> AMD -PARTNERS_WITH-> OpenAI`
- **answer entities:** `['openai']`
- **expected chunks in corpus:** 2

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `NVDA_2026_Item_1_0005_9725a5a2...`, `NVDA_2024_Item_1_0005_7f985cdb...`, `NVDA_2026_Item_1_0003_0297d539...`, `AMD_2026_Item_1_0003_ea53a6a5...`, `NVDA_2024_Item_1_0001_ee051c1b...` |
| graph  | 1 | 0.50 | 1/5 | `AMD_2025_Item_1_0003_861e4bfa...`, `AMD_2026_Item_1_0003_ea53a6a5...`, `AMD_2026_Item_7_0005_8ab9ed73...`, `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2026_Item_1_0002_9bce02c2...` |
| **hybrid** | **0** | **0.00** | **0/5** | `AMD_2026_Item_1_0003_ea53a6a5...`, `AMD_2025_Item_1_0003_861e4bfa...`, `NVDA_2026_Item_1_0005_9725a5a2...`, `NVDA_2024_Item_1_0005_7f985cdb...`, `AMD_2026_Item_7_0005_8ab9ed73...` |

**Winner:** graph

_graph hits:_ ['AMD_2026_Item_1_0002_9bce02c2']

---

## H4: `What memory storage product types come from the manufacturer competing with SK Hynix in DRAM markets?`

- **type:** product_via_competitor
- **chain:** `SK Hynix <-COMPETES_WITH- Micron -PRODUCES-> {NAND, DRAM, SSD}`
- **answer entities:** `['dram', 'nand', 'ssd', 'managed nand', 'nor']`
- **expected chunks in corpus:** 36

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `MU_2025_Item_1A_0005_edea08b6...`, `MU_2025_Item_1_0010_ef8bd774...`, `MU_2025_Item_1_0001_b64486b7...`, `MU_2024_Item_1A_0004_6b8d5aad...`, `MU_2024_Item_1_0001_90ffbd18...` |
| graph  | 0 | 0.00 | 0/5 | `MU_2023_Item_1A_0003_92be33e3...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `MU_2023_Item_1_0013_c12aeeff...` |
| **hybrid** | **1** | **0.20** | **1/5** | `NVDA_2026_Item_1_0007_bf6a51b6...`, `MU_2023_Item_1A_0003_92be33e3...`, `MU_2025_Item_1A_0005_edea08b6...`, `MU_2025_Item_1_0010_ef8bd774...`, `NVDA_2024_Item_1_0007_bae70036...` |

**Winner:** vector

_vector hits:_ ['MU_2024_Item_1_0001_90ffbd18', 'MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774']

_hybrid hits:_ ['MU_2025_Item_1_0010_ef8bd774']

---

## H5: `What political tensions threaten East Asian semiconductor supply chain stability?`

- **type:** macro_risk
- **chain:** `supply chain -IMPACTED_BY-> {geopolitical tensions, China-Taiwan instability}`
- **answer entities:** `['geopolitical tensions', 'political and economic instability', 'china', 'taiwan', 'geopolitical conditions']`
- **expected chunks in corpus:** 114

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `MU_2025_Item_1_0006_0c03fa5d...`, `MU_2023_Item_1_0005_91e3e192...`, `MU_2023_Item_1A_0003_92be33e3...`, `MU_2024_Item_1_0008_545cb750...`, `MU_2023_Item_1_0007_3d1e6086...` |
| graph  | 1 | 0.40 | 2/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2025_Item_1A_0019_46eda16...`, `NVDA_2025_Item_1_0009_7a56593b...` |
| **hybrid** | **1** | **0.40** | **2/5** | `NVDA_2026_Item_1_0007_bf6a51b6...`, `MU_2025_Item_1_0006_0c03fa5d...`, `NVDA_2024_Item_1_0007_bae70036...`, `MU_2023_Item_1_0005_91e3e192...`, `NVDA_2025_Item_1_0008_a4407f7e...` |

**Winner:** vector

_vector hits:_ ['MU_2023_Item_1A_0003_92be33e3', 'MU_2023_Item_1_0005_91e3e192', 'MU_2023_Item_1_0007_3d1e6086', 'MU_2024_Item_1_0008_545cb750', 'MU_2025_Item_1_0006_0c03fa5d']

_graph hits:_ ['NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1_0009_7a56593b']

_hybrid hits:_ ['MU_2023_Item_1_0005_91e3e192', 'MU_2025_Item_1_0006_0c03fa5d']

---

## H6: `How does the transition from Hopper to Blackwell architecture affect data center GPU revenue?`

- **type:** topical_business
- **chain:** `product transition Hopper→Blackwell impacts revenue`
- **answer entities:** `['business model transition from hopper hgx to blackwell', 'hopper architecture', 'blackwell architecture', 'hopper', 'blackwell']`
- **expected chunks in corpus:** 14

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `NVDA_2026_Item_7_0005_ca41c60b...`, `NVDA_2025_Item_1A_0004_68f8bb3...`, `NVDA_2026_Item_7_0000_5e8ec6e5...`, `NVDA_2026_Item_1_0003_0297d539...`, `NVDA_2026_Item_1A_0005_dd7a422...` |
| graph  | 1 | 1.00 | 5/5 | `NVDA_2026_Item_7_0002_74a3c132...`, `NVDA_2025_Item_7_0003_d53d3047...`, `NVDA_2026_Item_7_0005_ca41c60b...`, `NVDA_2026_Item_7_0004_02456737...`, `NVDA_2025_Item_1_0003_ccc9ed65...` |
| **hybrid** | **1** | **0.80** | **4/5** | `NVDA_2026_Item_7_0005_ca41c60b...`, `NVDA_2026_Item_1_0003_0297d539...`, `NVDA_2025_Item_1_0003_ccc9ed65...`, `NVDA_2026_Item_7_0000_5e8ec6e5...`, `NVDA_2026_Item_7_0002_74a3c132...` |

**Winner:** graph

_vector hits:_ ['NVDA_2026_Item_1_0003_0297d539', 'NVDA_2026_Item_7_0005_ca41c60b']

_graph hits:_ ['NVDA_2025_Item_1_0003_ccc9ed65', 'NVDA_2025_Item_7_0003_d53d3047', 'NVDA_2026_Item_7_0002_74a3c132', 'NVDA_2026_Item_7_0004_02456737', 'NVDA_2026_Item_7_0005_ca41c60b']

_hybrid hits:_ ['NVDA_2025_Item_1_0003_ccc9ed65', 'NVDA_2026_Item_1_0003_0297d539', 'NVDA_2026_Item_7_0002_74a3c132', 'NVDA_2026_Item_7_0005_ca41c60b']

---

## H7: `Why must semiconductor firms maintain large research and development investments?`

- **type:** topical_abstract
- **chain:** `abstract — RnD as competitive moat`
- **answer entities:** `['research and development', 'r&d expenses', 'innovation']`
- **expected chunks in corpus:** 8

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `MU_2023_Item_1A_0004_d5ebe913...`, `MU_2025_Item_1A_0005_edea08b6...`, `MU_2025_Item_1A_0006_576afa0c...`, `MU_2024_Item_1A_0004_6b8d5aad...`, `MU_2024_Item_1A_0005_fa3f9f52...` |
| graph  | 0 | 0.00 | 0/5 | `AMD_2025_Item_1A_0000_ac2e47a8...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1A_0001_0fd81b24...`, `AMD_2025_Item_1_0008_db609f8f...`, `AMD_2025_Item_1_0009_c842eea0...` |
| **hybrid** | **0** | **0.00** | **0/5** | `AMD_2025_Item_1A_0000_ac2e47a8...`, `MU_2023_Item_1A_0004_d5ebe913...`, `AMD_2024_Item_1_0011_49024c2d...`, `MU_2025_Item_1A_0005_edea08b6...`, `AMD_2025_Item_1A_0001_0fd81b24...` |

**Winner:** tie

---

## H8: `Which professional workstation graphics product line comes from the Hopper architect?`

- **type:** product_in_segment
- **chain:** `Hopper -PRODUCES-> NVIDIA -PRODUCES-> Quadro RTX`
- **answer entities:** `['quadro nvidia rtx gpus']`
- **expected chunks in corpus:** 1

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `AMD_2025_Item_1_0007_0ffd6ad4...`, `AMD_2025_Item_1_0005_e788d800...`, `AMD_2025_Item_1_0004_7a6fa20c...`, `AMD_2026_Item_1_0005_808c1965...`, `AMD_2024_Item_1_0005_7be264c6...` |
| graph  | 1 | 1.00 | 1/5 | `NVDA_2024_Item_7_0003_ba144df9...`, `NVDA_2026_Item_1_0002_b628e1c2...`, `NVDA_2025_Item_1_0002_b74647bb...`, `NVDA_2024_Item_7_0007_d25e117d...`, `NVDA_2025_Item_7_0003_d53d3047...` |
| **hybrid** | **1** | **1.00** | **1/5** | `AMD_2025_Item_1_0007_0ffd6ad4...`, `NVDA_2024_Item_7_0003_ba144df9...`, `AMD_2025_Item_1_0005_e788d800...`, `NVDA_2026_Item_1_0002_b628e1c2...`, `AMD_2025_Item_1_0004_7a6fa20c...` |

**Winner:** tie

_graph hits:_ ['NVDA_2026_Item_1_0002_b628e1c2']

_hybrid hits:_ ['NVDA_2026_Item_1_0002_b628e1c2']

---

## H9: `What revenue segments does the leading discrete GPU vendor break out in its filings?`

- **type:** segment_via_product
- **chain:** `discrete GPU = NVIDIA -HAS_STAKE_IN-> {Compute & Networking, Graphics, Pro Viz, Data Center}`
- **answer entities:** `['data center', 'compute & networking', 'graphics', 'professional visualization']`
- **expected chunks in corpus:** 50

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `NVDA_2026_Item_7_0005_ca41c60b...`, `NVDA_2026_Item_7_0004_02456737...`, `AMD_2025_Item_1A_0002_2bc1ccc8...`, `NVDA_2024_Item_7_0006_e75426d0...`, `AMD_2024_Item_1A_0002_0a71f57a...` |
| graph  | 1 | 0.80 | 4/5 | `NVDA_2026_Item_7_0002_74a3c132...`, `NVDA_2026_Item_7_0005_ca41c60b...`, `NVDA_2025_Item_7_0003_d53d3047...`, `NVDA_2026_Item_7_0004_02456737...`, `NVDA_2025_Item_7_0007_81d515b2...` |
| **hybrid** | **1** | **0.80** | **4/5** | `NVDA_2026_Item_7_0005_ca41c60b...`, `NVDA_2026_Item_7_0004_02456737...`, `NVDA_2024_Item_7_0007_d25e117d...`, `NVDA_2026_Item_7_0002_74a3c132...`, `NVDA_2025_Item_7_0003_d53d3047...` |

**Winner:** tie

_vector hits:_ ['NVDA_2024_Item_7_0006_e75426d0', 'NVDA_2026_Item_7_0004_02456737']

_graph hits:_ ['NVDA_2025_Item_7_0003_d53d3047', 'NVDA_2025_Item_7_0007_81d515b2', 'NVDA_2026_Item_7_0002_74a3c132', 'NVDA_2026_Item_7_0004_02456737']

_hybrid hits:_ ['NVDA_2024_Item_7_0007_d25e117d', 'NVDA_2025_Item_7_0003_d53d3047', 'NVDA_2026_Item_7_0002_74a3c132', 'NVDA_2026_Item_7_0004_02456737']

---

## H10: `Which U.S. federal agency restricts advanced semiconductor sales to specific foreign markets?`

- **type:** regulator_via_topic
- **chain:** `chips -SUBJECT_TO-> BIS / Commerce Dept`
- **answer entities:** `['bureau of industry and security', 'u.s. department of commerce', 'export administration regulations']`
- **expected chunks in corpus:** 4

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.25 | 1/5 | `AMD_2026_Item_1A_0019_b7fa1437...`, `AMD_2025_Item_1A_0021_16aa3aa2...`, `AMD_2026_Item_1A_0021_7fb03412...`, `AMD_2024_Item_1A_0021_614fbf7c...`, `NVDA_2025_Item_1A_0020_69d9e1e...` |
| graph  | 1 | 0.25 | 1/5 | `AMD_2025_Item_1A_0020_0d19c86e...`, `AMD_2026_Item_1A_0019_b7fa1437...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...` |
| **hybrid** | **1** | **0.25** | **1/5** | `AMD_2026_Item_1A_0019_b7fa1437...`, `AMD_2025_Item_1A_0020_0d19c86e...`, `AMD_2024_Item_1A_0021_614fbf7c...`, `NVDA_2026_Item_1_0008_edf8fe4b...`, `AMD_2025_Item_1A_0021_16aa3aa2...` |

**Winner:** tie

_vector hits:_ ['AMD_2026_Item_1A_0019_b7fa1437']

_graph hits:_ ['AMD_2026_Item_1A_0019_b7fa1437']

_hybrid hits:_ ['AMD_2026_Item_1A_0019_b7fa1437']

---

