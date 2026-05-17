# Multi-hop Synthesized Evaluation — Phase C2-bis

**Hypothesis tested:** graph_search outperforms vector_search on multi-hop questions where the answer entity is NOT a surface term of the question (i.e. requires graph traversal).

**Methodology:** 8 hand-crafted questions, each with a verified reasoning chain through the live KG. Expected chunks are derived from MENTIONS edges to the answer entity, not hand-picked.

**top_k_chunks:** 5

---

## Aggregate Results

| Metric | vector_search | graph_search | Δ |
|---|---|---|---|
| Hit@5 (binary) | 17/20 | 11/20 | -6 |
| Avg Recall@5  | 0.432 | 0.320 | -0.112 |
| Per-query wins | 10 | 6 | -4 (ties: 4) |

**Hypothesis verdict:** ✗ not supported — gap < 2 queries

---

## Q1: `Which foundry partner manufactures the Hopper architecture chips?`

- **type:** supplier_via_product
- **reasoning chain:** `Hopper -PRODUCES-> NVIDIA <-SUPPLIES- TSMC`
- **answer entities:** `['tsmc']`
- **expected chunks in corpus:** 14

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `AMD_2024_Item_1_0012_9561038a...`, `MU_2025_Item_1_0010_ef8bd774...`, `AMD_2024_Item_1_0013_596acde4...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `AMD_2026_Item_1_0008_302d3abf...` |
| graph  | 1 | 0.80 | 4/5 | `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `NVDA_2025_Item_1_0008_a4407f7e...` |

**Winner:** graph

_vector hits:_ ['AMD_2024_Item_1_0012_9561038a', 'NVDA_2026_Item_1_0007_bf6a51b6']

_graph hits:_ ['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']

---

## Q2: `Who produces the dense memory chips that power modern AI training accelerators?`

- **type:** supplier_via_product
- **reasoning chain:** `AI accelerators (HBM) -PRODUCES-> Micron`
- **answer entities:** `['micron', 'micron technology']`
- **expected chunks in corpus:** 52

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `AMD_2025_Item_1_0002_6fadf6e4...`, `NVDA_2026_Item_1_0005_9725a5a2...`, `NVDA_2024_Item_1_0005_7f985cdb...`, `MU_2024_Item_1_0003_acd8d0ff...`, `NVDA_2025_Item_1_0001_dbfd59e1...` |
| graph  | 1 | 0.40 | 2/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1_0009_c842eea0...` |

**Winner:** graph

_graph hits:_ ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']

---

## Q3: `What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?`

- **type:** competitor_product
- **reasoning chain:** `Intel <-COMPETES_WITH- AMD -PRODUCES-> Instinct MI300`
- **answer entities:** `['amd instinct mi300', 'amd instinct mi200', 'mi300', 'mi200', 'amd instinct mi300 series', 'instinct']`
- **expected chunks in corpus:** 2

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `AMD_2026_Item_1_0004_b5e66359...`, `NVDA_2026_Item_1_0005_9725a5a2...`, `AMD_2025_Item_1_0002_6fadf6e4...`, `AMD_2025_Item_1_0004_7a6fa20c...`, `AMD_2026_Item_1_0010_460dfa17...` |
| graph  | 0 | 0.00 | 0/5 | `AMD_2025_Item_1_0006_551768e4...`, `AMD_2026_Item_1_0007_f252541b...`, `AMD_2024_Item_1_0009_01379c5a...`, `AMD_2025_Item_1_0007_0ffd6ad4...`, `AMD_2026_Item_1_0008_302d3abf...` |

**Winner:** tie

---

## Q4: `What political risks affect the home country of the leading pure-play semiconductor foundry?`

- **type:** geo_via_supplier
- **reasoning chain:** `foundry -> TSMC -OPERATES_IN-> Taiwan`
- **answer entities:** `['taiwan']`
- **expected chunks in corpus:** 42

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.80 | 4/5 | `MU_2023_Item_1A_0003_92be33e3...`, `AMD_2025_Item_1A_0032_0a1cf7f3...`, `AMD_2026_Item_1A_0032_c870df0c...`, `AMD_2024_Item_1A_0032_979d78aa...`, `NVDA_2026_Item_1A_0023_804c637...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...` |

**Winner:** vector

_vector hits:_ ['AMD_2024_Item_1A_0032_979d78aa', 'AMD_2025_Item_1A_0032_0a1cf7f3', 'AMD_2026_Item_1A_0032_c870df0c', 'MU_2023_Item_1A_0003_92be33e3']

---

## Q5: `Where is the developer of Ryzen processors headquartered?`

- **type:** geo_via_product
- **reasoning chain:** `Ryzen -PRODUCES-> AMD -OPERATES_IN-> Santa Clara`
- **answer entities:** `['santa clara', 'sunnyvale', 'california']`
- **expected chunks in corpus:** 37

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `AMD_2026_Item_1_0004_b5e66359...`, `AMD_2025_Item_1_0004_7a6fa20c...`, `AMD_2024_Item_7_0001_2f628a3f...`, `AMD_2024_Item_1_0005_7be264c6...`, `AMD_2024_Item_1_0012_9561038a...` |
| graph  | 0 | 0.00 | 0/5 | `AMD_2024_Item_7_0006_b8de17a3...`, `AMD_2026_Item_7_0000_6b145a7b...`, `AMD_2026_Item_7_0006_2b606b28...`, `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2024_Item_1_0011_49024c2d...` |

**Winner:** tie

---

## Q6: `Which firm produces the memory chips integrated into the H100 accelerator?`

- **type:** three_hop_supplier
- **reasoning chain:** `H100 -PRODUCES-> NVIDIA — uses HBM <-PRODUCES- Micron`
- **answer entities:** `['micron', 'micron technology', 'sk hynix', 'samsung electronics']`
- **expected chunks in corpus:** 57

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `MU_2025_Item_1_0010_ef8bd774...`, `MU_2025_Item_1_0001_b64486b7...`, `MU_2025_Item_1A_0005_edea08b6...`, `AMD_2024_Item_1_0012_9561038a...`, `AMD_2026_Item_1_0008_302d3abf...` |
| graph  | 1 | 0.40 | 2/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...` |

**Winner:** vector

_vector hits:_ ['AMD_2024_Item_1_0012_9561038a', 'MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774']

_graph hits:_ ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']

---

## Q7: `In what countries does the GeForce graphics card vendor maintain operations?`

- **type:** geo_via_competitor
- **reasoning chain:** `GeForce -PRODUCES-> NVIDIA -OPERATES_IN-> {China, India, Taiwan, ...}`
- **answer entities:** `['china', 'india', 'taiwan', 'israel']`
- **expected chunks in corpus:** 109

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `NVDA_2025_Item_1_0002_b74647bb...`, `NVDA_2024_Item_1_0002_2ddf2e3b...`, `NVDA_2026_Item_1A_0024_b70c7a1...`, `AMD_2026_Item_1_0005_808c1965...`, `NVDA_2024_Item_1A_0021_3fa26c8...` |
| graph  | 1 | 0.80 | 4/5 | `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1A_0022_b1d57eb...`, `NVDA_2026_Item_1A_0023_804c637...` |

**Winner:** graph

_vector hits:_ ['NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2026_Item_1A_0024_b70c7a18']

_graph hits:_ ['NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2026_Item_1A_0023_804c637e']

---

## Q8: `What export controls affect AI chip sales from the maker of Blackwell architecture?`

- **type:** regulation_via_product
- **reasoning chain:** `Blackwell -PRODUCES-> NVIDIA -SUBJECT_TO-> Export Administration Regulations (China-bound)`
- **answer entities:** `['export administration regulations', 'china', 'bureau of industry and security']`
- **expected chunks in corpus:** 101

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `AMD_2025_Item_1A_0021_16aa3aa2...`, `NVDA_2025_Item_1A_0019_46eda16...`, `AMD_2026_Item_1A_0021_7fb03412...`, `NVDA_2026_Item_1A_0020_331dc53...`, `NVDA_2025_Item_1A_0023_67392e5...` |
| graph  | 1 | 1.00 | 5/5 | `NVDA_2025_Item_1A_0019_46eda16...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2024_Item_1A_0019_ea1fd2e...` |

**Winner:** tie

_vector hits:_ ['AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537']

_graph hits:_ ['NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2026_Item_1_0008_edf8fe4b']

---

## Q9: `Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?`

- **type:** supplier_via_company
- **reasoning chain:** `NVIDIA <-SUPPLIES- {TSMC, Samsung, SK Hynix}`
- **answer entities:** `['tsmc', 'samsung electronics co ltd', 'sk hynix inc']`
- **expected chunks in corpus:** 17

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `MU_2024_Item_1A_0025_1809ff3b...`, `AMD_2024_Item_1_0012_9561038a...`, `AMD_2025_Item_1A_0002_2bc1ccc8...`, `NVDA_2025_Item_1_0008_a4407f7e...` |
| graph  | 1 | 0.60 | 3/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2024_Item_1A_0022_b1d57eb...` |

**Winner:** tie

_vector hits:_ ['AMD_2024_Item_1_0012_9561038a', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

_graph hits:_ ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

---

## Q10: `Which Taiwanese contract chipmaker fabricates AMD's processors?`

- **type:** supplier_via_company
- **reasoning chain:** `AMD <-SUPPLIES- {TSMC, UMC}`
- **answer entities:** `['tsmc', 'umc']`
- **expected chunks in corpus:** 14

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `AMD_2024_Item_1_0001_84491be9...`, `MU_2024_Item_1A_0025_1809ff3b...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `AMD_2024_Item_1_0013_596acde4...` |
| graph  | 1 | 0.60 | 3/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...` |

**Winner:** graph

_vector hits:_ ['NVDA_2026_Item_1_0007_bf6a51b6']

_graph hits:_ ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

---

## Q11: `In what U.S. state does the developer of the CUDA platform operate its headquarters?`

- **type:** geo_via_product
- **reasoning chain:** `CUDA -PRODUCES-> NVIDIA -OPERATES_IN-> {Santa Clara, California}`
- **answer entities:** `['santa clara', 'california']`
- **expected chunks in corpus:** 37

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `NVDA_2024_Item_1_0002_2ddf2e3b...`, `NVDA_2025_Item_1_0002_b74647bb...`, `NVDA_2025_Item_1_0003_ccc9ed65...`, `NVDA_2026_Item_1_0002_b628e1c2...`, `NVDA_2024_Item_1_0003_59fa75a8...` |
| graph  | 1 | 0.20 | 1/5 | `NVDA_2024_Item_1_0002_2ddf2e3b...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...` |

**Winner:** vector

_vector hits:_ ['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2025_Item_1_0002_b74647bb', 'NVDA_2026_Item_1_0002_b628e1c2']

_graph hits:_ ['NVDA_2024_Item_1_0002_2ddf2e3b']

---

## Q12: `Which gaming console maker partners with the Ryzen processor company?`

- **type:** partner_via_product
- **reasoning chain:** `Ryzen -PRODUCES-> AMD -PARTNERS_WITH-> {Sony, Microsoft, Valve}`
- **answer entities:** `['sony', 'valve', 'microsoft']`
- **expected chunks in corpus:** 22

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.80 | 4/5 | `AMD_2026_Item_1_0004_b5e66359...`, `AMD_2026_Item_1_0005_808c1965...`, `AMD_2025_Item_1_0004_7a6fa20c...`, `AMD_2024_Item_7_0001_2f628a3f...`, `AMD_2024_Item_1_0006_e41aed21...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2024_Item_7_0006_b8de17a3...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1_0008_db609f8f...`, `AMD_2025_Item_1_0009_c842eea0...` |

**Winner:** vector

_vector hits:_ ['AMD_2024_Item_1_0006_e41aed21', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2026_Item_1_0005_808c1965']

---

## Q13: `What product family does NVIDIA offer for the consumer gaming graphics market?`

- **type:** product_in_segment
- **reasoning chain:** `NVIDIA -PRODUCES-> GeForce (gaming consumer GPU line)`
- **answer entities:** `['geforce', 'geforce rtx', 'geforce now']`
- **expected chunks in corpus:** 9

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `AMD_2025_Item_1A_0002_2bc1ccc8...`, `AMD_2025_Item_1_0005_e788d800...`, `NVDA_2026_Item_1_0004_5a83036d...`, `AMD_2026_Item_1_0005_808c1965...`, `NVDA_2024_Item_1_0002_2ddf2e3b...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_1A_0003_3aa8850...`, `NVDA_2026_Item_7_0000_5e8ec6e5...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...` |

**Winner:** vector

_vector hits:_ ['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2026_Item_1_0004_5a83036d']

---

## Q14: `What revenue segments does the developer of EPYC processors disclose?`

- **type:** segment_via_product
- **reasoning chain:** `EPYC -PRODUCES-> AMD -HAS_STAKE_IN-> {Data Center, Client, Gaming, Embedded}`
- **answer entities:** `['data center', 'client segment', 'gaming segment', 'embedded', 'client and gaming']`
- **expected chunks in corpus:** 52

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `AMD_2024_Item_1_0003_ee436d61...`, `AMD_2025_Item_1_0003_861e4bfa...`, `AMD_2026_Item_1_0003_ea53a6a5...`, `AMD_2024_Item_1_0010_842113d9...`, `AMD_2026_Item_1_0006_9061ffe7...` |
| graph  | 1 | 1.00 | 5/5 | `AMD_2025_Item_7_0005_36426dd3...`, `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2025_Item_7_0000_16c93d97...`, `AMD_2025_Item_7_0004_58e0bdd2...`, `AMD_2026_Item_7_0005_8ab9ed73...` |

**Winner:** graph

_vector hits:_ ['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2026_Item_1_0003_ea53a6a5']

_graph hits:_ ['AMD_2025_Item_7_0000_16c93d97', 'AMD_2025_Item_7_0004_58e0bdd2', 'AMD_2025_Item_7_0005_36426dd3', 'AMD_2026_Item_7_0005_8ab9ed73', 'NVDA_2024_Item_1_0007_bae70036']

---

## Q15: `What U.S. agency oversees semiconductor export controls to China?`

- **type:** regulator_via_topic
- **reasoning chain:** `semiconductor companies -SUBJECT_TO-> BIS / Commerce Dept`
- **answer entities:** `['bureau of industry and security', 'u.s. department of commerce', 'export administration regulations']`
- **expected chunks in corpus:** 4

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.25 | 1/5 | `AMD_2026_Item_1A_0019_b7fa1437...`, `AMD_2025_Item_1A_0021_16aa3aa2...`, `NVDA_2025_Item_1A_0020_69d9e1e...`, `AMD_2026_Item_1A_0021_7fb03412...`, `AMD_2025_Item_1A_0020_0d19c86e...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...`, `NVDA_2025_Item_1A_0019_46eda16...`, `NVDA_2026_Item_1_0007_bf6a51b6...` |

**Winner:** vector

_vector hits:_ ['AMD_2026_Item_1A_0019_b7fa1437']

---

## Q16: `What macroeconomic conditions create headwinds for chip industry revenue?`

- **type:** macro_risk
- **reasoning chain:** `companies -IMPACTED_BY-> {geopolitical tensions, economic instability}`
- **answer entities:** `['geopolitical tensions', 'political and economic instability', 'geopolitical conditions', 'global business disruptions', 'economic and market uncertainty']`
- **expected chunks in corpus:** 27

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `AMD_2024_Item_1A_0004_eabb01e8...`, `AMD_2024_Item_1A_0003_cd973f49...`, `AMD_2025_Item_1A_0004_3da97b4d...`, `AMD_2024_Item_1A_0006_16ed3c8d...`, `MU_2024_Item_1A_0001_703555bd...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_7_0004_5f9dd035...`, `AMD_2026_Item_1A_0002_72e02a77...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...` |

**Winner:** vector

_vector hits:_ ['AMD_2024_Item_1A_0003_cd973f49']

---

## Q17: `Which Asian country hosts most semiconductor wafer fabrication capacity?`

- **type:** geo_via_industry
- **reasoning chain:** `wafer fab industry -> {TSMC, UMC} -OPERATES_IN-> Taiwan`
- **answer entities:** `['taiwan']`
- **expected chunks in corpus:** 42

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.80 | 4/5 | `MU_2024_Item_1A_0025_1809ff3b...`, `MU_2025_Item_1_0006_0c03fa5d...`, `MU_2024_Item_1_0006_6b1663cd...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `MU_2023_Item_1_0005_91e3e192...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2024_Item_1_0008_20833acc...` |

**Winner:** vector

_vector hits:_ ['MU_2023_Item_1_0005_91e3e192', 'MU_2024_Item_1A_0025_1809ff3b', 'MU_2024_Item_1_0006_6b1663cd', 'MU_2025_Item_1_0006_0c03fa5d']

---

## Q18: `What data center accelerators come from the developer of Hopper architecture?`

- **type:** product_line_via_product
- **reasoning chain:** `Hopper -PRODUCES-> NVIDIA -PRODUCES-> {H100, H200, A100, Blackwell, GB200}`
- **answer entities:** `['h100', 'h200', 'a100', 'blackwell', 'gb200', 'gb300', 'blackwell architecture']`
- **expected chunks in corpus:** 21

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `NVDA_2025_Item_1_0005_85d95b7e...`, `NVDA_2026_Item_1_0003_0297d539...`, `AMD_2024_Item_1_0003_ee436d61...`, `AMD_2025_Item_1_0003_861e4bfa...`, `AMD_2024_Item_1_0004_281905c9...` |
| graph  | 1 | 0.40 | 2/5 | `NVDA_2024_Item_7_0007_d25e117d...`, `NVDA_2025_Item_7_0007_81d515b2...`, `NVDA_2025_Item_7_0003_d53d3047...`, `NVDA_2025_Item_7_0000_78a2a641...`, `NVDA_2024_Item_1_0007_bae70036...` |

**Winner:** graph

_vector hits:_ ['NVDA_2026_Item_1_0003_0297d539']

_graph hits:_ ['NVDA_2025_Item_7_0000_78a2a641', 'NVDA_2025_Item_7_0003_d53d3047']

---

## Q19: `What market segments does Intel's primary CPU competitor pursue for growth?`

- **type:** segment_via_competitor
- **reasoning chain:** `Intel <-COMPETES_WITH- AMD -HAS_STAKE_IN-> {Data Center, Gaming, Client}`
- **answer entities:** `['data center', 'gaming segment', 'client segment', 'embedded', 'client and gaming']`
- **expected chunks in corpus:** 52

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2024_Item_1_0011_49024c2d...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `AMD_2025_Item_1_0003_861e4bfa...` |
| graph  | 1 | 0.20 | 1/5 | `AMD_2025_Item_1A_0001_0fd81b24...`, `AMD_2025_Item_1A_0000_ac2e47a8...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...` |

**Winner:** vector

_vector hits:_ ['AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2025_Item_1_0009_c842eea0']

_graph hits:_ ['NVDA_2024_Item_1_0007_bae70036']

---

## Q20: `What graphics product line does AMD offer to compete with NVIDIA's RTX series?`

- **type:** competitor_product
- **reasoning chain:** `NVIDIA -PRODUCES-> RTX, AMD -PRODUCES-> Radeon`
- **answer entities:** `['radeon', 'amd radeon', 'amd radeon pro']`
- **expected chunks in corpus:** 5

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `AMD_2025_Item_1_0005_e788d800...`, `AMD_2026_Item_1_0005_808c1965...`, `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2025_Item_1_0007_0ffd6ad4...`, `AMD_2025_Item_1_0009_c842eea0...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2025_Item_1_0009_7a56593b...` |

**Winner:** vector

_vector hits:_ ['AMD_2025_Item_1_0005_e788d800']

---

