# Multi-hop Synthesized Evaluation — 3-config (Phase C2-quater)

**Primary thesis claim:** Hybrid (RRF graph+vector fusion) > Pure Vector on Hit@5 and Recall@5, with floor guarantee from RRF construction.

**Methodology:** hand-crafted multi-hop questions, each with a verified reasoning chain through the live KG. Expected chunks derived from MENTIONS edges to answer entities (not hand-picked).

**top_k_chunks:** 5 · **Tools tested:** vector_search, graph_search, hybrid_search (RRF k=60)

---

## Aggregate Results — 3-config

| Metric | vector | graph | **hybrid** | hyb − vec |
|---|---|---|---|---|
| Hit@5 | 33/50 | 33/50 | **39/50** | +6 |
| Avg Recall@5 | 0.369 | 0.448 | **0.455** | +0.086 |
| Best-of-3 wins | 8 | 11 | **3** | — (ties: 28) |

### Pairwise: hybrid vs vector (primary thesis)

- **hybrid > vector**: 20/50 queries
- hybrid = vector: 22/50 queries
- hybrid < vector: 8/50 queries (RRF should give 0 — diagnose if any)

**Verdict:** ⚠ hybrid < vector on 8 queries — check fusion noise

---

## Statistical Significance (paired tests, α = 0.05)

N = 50 paired queries. Tests:
- **McNemar** on Hit@5 (paired binary) — discordant pairs only
- **Wilcoxon signed-rank** on Recall@5 (paired ordinal, no normality)
- **Bootstrap 95% CI** on mean Recall@5 difference (10,000 resamples)
- **Cohen's h** on Hit@5 proportions (effect size: 0.2 small / 0.5 medium / 0.8 large)

Legend: p < 0.05 ✓ significant · p < 0.10 · marginal · p ≥ 0.10 ✗ not sig

### hybrid vs vector

- Hit@5: 78.00% vs 66.00%  (Cohen's h = +0.269)
- Recall@5: 0.455 vs 0.369  (Δ = +0.086)

| Test | Statistic | p | Verdict |
|---|---|---|---|
| McNemar (Hit@5) | b=7 c=1 (exact) | 0.0703 | · |
| Wilcoxon signed-rank (Recall@5) | W=87.5 (n≠0=28) | 0.0082 | ✓ |
| Bootstrap 95% CI on mean Δ | [+0.016, +0.156] | — | ✓ excludes 0 |

### graph vs vector

- Hit@5: 66.00% vs 66.00%  (Cohen's h = +0.000)
- Recall@5: 0.448 vs 0.369  (Δ = +0.079)

| Test | Statistic | p | Verdict |
|---|---|---|---|
| McNemar (Hit@5) | b=8 c=8 (exact) | 1.0000 | ✗ |
| Wilcoxon signed-rank (Recall@5) | W=196.5 (n≠0=32) | 0.2057 | ✗ |
| Bootstrap 95% CI on mean Δ | [-0.044, +0.200] | — | ✗ crosses 0 |

### hybrid vs graph

- Hit@5: 78.00% vs 66.00%  (Cohen's h = +0.269)
- Recall@5: 0.455 vs 0.448  (Δ = +0.007)

| Test | Statistic | p | Verdict |
|---|---|---|---|
| McNemar (Hit@5) | b=7 c=1 (exact) | 0.0703 | · |
| Wilcoxon signed-rank (Recall@5) | W=117.5 (n≠0=22) | 0.7687 | ✗ |
| Bootstrap 95% CI on mean Δ | [-0.071, +0.084] | — | ✗ crosses 0 |

---

## Per-Query-Type Breakdown (tuning diagnostic)

If graph/hybrid beats vector on a subset of types, sub-type claim is defensible even when overall test is null.

| Type | n | vec H@5 | gph H@5 | hyb H@5 | vec R@5 | gph R@5 | hyb R@5 |
|---|---|---|---|---|---|---|---|
| geo_via_product | 6 | 0.67 | 0.17 | 0.67 | 0.30 | 0.17 | 0.37 |
| supplier_via_product | 4 | 0.75 | 0.75 | 0.75 | 0.30 | 0.65 | 0.55 |
| customer_via_product | 4 | 0.50 | 0.50 | 0.50 | 0.50 | 0.45 | 0.45 |
| partner_via_product | 3 | 0.33 | 1.00 | 1.00 | 0.27 | 0.53 | 0.47 |
| regulator_via_product | 3 | 1.00 | 0.33 | 1.00 | 0.87 | 0.20 | 0.60 |
| competitor_product | 2 | 0.50 | 0.50 | 0.50 | 0.10 | 0.25 | 0.10 |
| supplier_via_company | 2 | 1.00 | 1.00 | 1.00 | 0.40 | 0.80 | 0.60 |
| segment_via_product | 2 | 1.00 | 1.00 | 1.00 | 0.50 | 0.80 | 0.70 |
| product_line_via_product | 2 | 1.00 | 1.00 | 1.00 | 0.30 | 0.60 | 0.30 |
| competitor_via_product | 2 | 0.00 | 0.50 | 0.50 | 0.00 | 0.10 | 0.10 |
| product_via_company | 2 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| geo_via_supplier | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 0.40 | 0.80 |
| three_hop_supplier | 1 | 1.00 | 1.00 | 1.00 | 0.60 | 0.80 | 0.80 |
| geo_via_competitor | 1 | 1.00 | 1.00 | 1.00 | 0.40 | 0.80 | 0.60 |
| regulation_via_product | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| product_in_segment | 1 | 1.00 | 1.00 | 1.00 | 0.40 | 1.00 | 0.80 |
| regulator_via_topic | 1 | 1.00 | 1.00 | 1.00 | 0.25 | 0.25 | 0.25 |
| macro_risk | 1 | 1.00 | 1.00 | 1.00 | 0.20 | 0.20 | 0.20 |
| geo_via_industry | 1 | 1.00 | 0.00 | 1.00 | 0.60 | 0.00 | 0.40 |
| segment_via_competitor | 1 | 1.00 | 1.00 | 1.00 | 0.40 | 0.60 | 0.60 |
| subsidiary_via_product | 1 | 0.00 | 1.00 | 1.00 | 0.00 | 1.00 | 0.40 |
| three_hop_subsidiary_product | 1 | 0.00 | 1.00 | 1.00 | 0.00 | 0.25 | 0.50 |
| topical_strategy | 1 | 1.00 | 1.00 | 1.00 | 0.20 | 0.80 | 0.80 |
| topical_memory | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| topical_ai_demand | 1 | 0.00 | 1.00 | 1.00 | 0.00 | 0.20 | 0.20 |
| competitor_via_geo | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| risk_via_product | 1 | 1.00 | 1.00 | 1.00 | 0.40 | 0.40 | 0.40 |
| regulator_via_segment | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| topical_capital | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

---

## Q1: `Which foundry partner manufactures the Hopper architecture chips?`

- **type:** supplier_via_product
- **reasoning chain:** `Hopper -PRODUCES-> NVIDIA <-SUPPLIES- TSMC`
- **answer entities:** `['tsmc']`
- **expected chunks in corpus:** 32

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `INTC_2026_Item_1_0008_c74f560f...`, `INTC_2026_Item_1_0013_cb483288...`, `INTC_2026_Item_1_0006_d0f653da...`, `INTC_2024_Item_1_0014_32e0816b...`, `AMD_2024_Item_1_0012_9561038a...` |
| graph  | 1 | 1.00 | 5/5 | `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `INTC_2026_Item_1_0008_c74f560f...`, `NVDA_2025_Item_1_0008_a4407f7e...` |
| **hybrid** | **1** | **1.00** | **5/5** | `INTC_2026_Item_1_0008_c74f560f...`, `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2025_Item_1_0009_c842eea0...`, `INTC_2026_Item_1_0013_cb483288...`, `AMD_2026_Item_1_0010_460dfa17...` |

**Winner:** tie

_vector hits:_ ['AMD_2024_Item_1_0012_9561038a', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0013_cb483288']

_graph hits:_ ['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']

_hybrid hits:_ ['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0013_cb483288', 'NVDA_2024_Item_1_0007_bae70036']

---

## Q2: `Who produces the dense memory chips that power modern AI training accelerators?`

- **type:** supplier_via_product
- **reasoning chain:** `AI accelerators (HBM) -PRODUCES-> Micron`
- **answer entities:** `['micron', 'micron technology']`
- **expected chunks in corpus:** 52

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `AMD_2025_Item_1_0002_6fadf6e4...`, `INTC_2025_Item_7_0003_878f7d25...`, `NVDA_2026_Item_1_0005_9725a5a2...`, `INTC_2026_Item_1_0004_c01224f1...`, `INTC_2025_Item_1_0003_707a268b...` |
| graph  | 1 | 0.60 | 3/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `MU_2023_Item_1A_0003_92be33e3...`, `NVDA_2024_Item_1_0008_20833acc...` |
| **hybrid** | **1** | **0.60** | **3/5** | `AMD_2025_Item_1_0002_6fadf6e4...`, `MU_2023_Item_1A_0003_92be33e3...`, `INTC_2025_Item_7_0003_878f7d25...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...` |

**Winner:** tie

_graph hits:_ ['MU_2023_Item_1A_0003_92be33e3', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']

_hybrid hits:_ ['MU_2023_Item_1A_0003_92be33e3', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']

---

## Q3: `What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?`

- **type:** competitor_product
- **reasoning chain:** `Intel <-COMPETES_WITH- AMD -PRODUCES-> Instinct MI300`
- **answer entities:** `['amd instinct mi300', 'amd instinct mi200', 'mi300', 'mi200', 'amd instinct mi300 series', 'instinct']`
- **expected chunks in corpus:** 2

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `INTC_2025_Item_1_0003_707a268b...`, `INTC_2024_Item_1_0005_bcb431a8...`, `INTC_2026_Item_1_0004_c01224f1...`, `INTC_2025_Item_7_0003_878f7d25...`, `AMD_2026_Item_1_0004_b5e66359...` |
| graph  | 1 | 0.50 | 1/5 | `AMD_2026_Item_1_0003_ea53a6a5...`, `AMD_2024_Item_1_0009_01379c5a...`, `AMD_2026_Item_1_0007_f252541b...`, `AMD_2025_Item_7_0001_223169cf...`, `AMD_2025_Item_1_0006_551768e4...` |
| **hybrid** | **0** | **0.00** | **0/5** | `AMD_2026_Item_1_0004_b5e66359...`, `AMD_2025_Item_1_0006_551768e4...`, `INTC_2025_Item_1_0003_707a268b...`, `AMD_2026_Item_1_0007_f252541b...`, `INTC_2024_Item_1_0005_bcb431a8...` |

**Winner:** graph

_graph hits:_ ['AMD_2026_Item_1_0003_ea53a6a5']

---

## Q4: `What political risks affect the home country of the leading pure-play semiconductor foundry?`

- **type:** geo_via_supplier
- **reasoning chain:** `foundry -> TSMC -OPERATES_IN-> Taiwan`
- **answer entities:** `['taiwan']`
- **expected chunks in corpus:** 51

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `MU_2023_Item_1A_0003_92be33e3...`, `AMD_2025_Item_1A_0032_0a1cf7f3...`, `AMD_2026_Item_1A_0032_c870df0c...`, `AMD_2024_Item_1A_0032_979d78aa...`, `INTC_2025_Item_1A_0011_d28f4e6...` |
| graph  | 1 | 0.40 | 2/5 | `MU_2023_Item_1A_0002_e54b8152...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `MU_2023_Item_1A_0003_92be33e3...` |
| **hybrid** | **1** | **0.80** | **4/5** | `MU_2023_Item_1A_0003_92be33e3...`, `AMD_2026_Item_1A_0032_c870df0c...`, `MU_2023_Item_1A_0002_e54b8152...`, `AMD_2025_Item_1A_0032_0a1cf7f3...`, `NVDA_2024_Item_1_0007_bae70036...` |

**Winner:** vector

_vector hits:_ ['AMD_2024_Item_1A_0032_979d78aa', 'AMD_2025_Item_1A_0032_0a1cf7f3', 'AMD_2026_Item_1A_0032_c870df0c', 'INTC_2025_Item_1A_0011_d28f4e6a', 'MU_2023_Item_1A_0003_92be33e3']

_graph hits:_ ['MU_2023_Item_1A_0002_e54b8152', 'MU_2023_Item_1A_0003_92be33e3']

_hybrid hits:_ ['AMD_2025_Item_1A_0032_0a1cf7f3', 'AMD_2026_Item_1A_0032_c870df0c', 'MU_2023_Item_1A_0002_e54b8152', 'MU_2023_Item_1A_0003_92be33e3']

---

## Q5: `Where is the developer of Ryzen processors headquartered?`

- **type:** geo_via_product
- **reasoning chain:** `Ryzen -PRODUCES-> AMD -OPERATES_IN-> Santa Clara`
- **answer entities:** `['santa clara', 'sunnyvale', 'california']`
- **expected chunks in corpus:** 41

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `AMD_2026_Item_1_0004_b5e66359...`, `AMD_2025_Item_1_0004_7a6fa20c...`, `AMD_2024_Item_7_0001_2f628a3f...`, `AMD_2024_Item_1_0005_7be264c6...`, `AMD_2024_Item_1_0012_9561038a...` |
| graph  | 0 | 0.00 | 0/5 | `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `INTC_2026_Item_1_0008_c74f560f...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...` |
| **hybrid** | **0** | **0.00** | **0/5** | `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0004_b5e66359...`, `AMD_2025_Item_1_0004_7a6fa20c...`, `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2024_Item_7_0001_2f628a3f...` |

**Winner:** tie

---

## Q6: `Which firm produces the memory chips integrated into the H100 accelerator?`

- **type:** three_hop_supplier
- **reasoning chain:** `H100 -PRODUCES-> NVIDIA — uses HBM <-PRODUCES- Micron`
- **answer entities:** `['micron', 'micron technology', 'sk hynix', 'samsung electronics']`
- **expected chunks in corpus:** 60

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `MU_2025_Item_1_0010_ef8bd774...`, `MU_2025_Item_1_0001_b64486b7...`, `MU_2025_Item_1A_0005_edea08b6...`, `AMD_2024_Item_1_0012_9561038a...`, `AMD_2026_Item_1_0008_302d3abf...` |
| graph  | 1 | 0.80 | 4/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `MU_2023_Item_1A_0003_92be33e3...`, `NVDA_2024_Item_1A_0022_b1d57eb...` |
| **hybrid** | **1** | **0.80** | **4/5** | `MU_2025_Item_1_0010_ef8bd774...`, `NVDA_2024_Item_1_0007_bae70036...`, `MU_2025_Item_1_0001_b64486b7...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `MU_2025_Item_1A_0005_edea08b6...` |

**Winner:** tie

_vector hits:_ ['AMD_2024_Item_1_0012_9561038a', 'MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774']

_graph hits:_ ['MU_2023_Item_1A_0003_92be33e3', 'NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']

_hybrid hits:_ ['MU_2025_Item_1_0001_b64486b7', 'MU_2025_Item_1_0010_ef8bd774', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e']

---

## Q7: `In what countries does the GeForce graphics card vendor maintain operations?`

- **type:** geo_via_competitor
- **reasoning chain:** `GeForce -PRODUCES-> NVIDIA -OPERATES_IN-> {China, India, Taiwan, ...}`
- **answer entities:** `['china', 'india', 'taiwan', 'israel']`
- **expected chunks in corpus:** 139

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `NVDA_2025_Item_1_0002_b74647bb...`, `NVDA_2024_Item_1_0002_2ddf2e3b...`, `NVDA_2026_Item_1A_0024_b70c7a1...`, `AMD_2026_Item_1_0005_808c1965...`, `NVDA_2024_Item_1A_0021_3fa26c8...` |
| graph  | 1 | 0.80 | 4/5 | `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2024_Item_1A_0022_b1d57eb...`, `NVDA_2025_Item_1A_0023_67392e5...` |
| **hybrid** | **1** | **0.60** | **3/5** | `NVDA_2026_Item_1A_0023_804c637...`, `NVDA_2025_Item_1A_0020_69d9e1e...`, `NVDA_2025_Item_1_0002_b74647bb...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2024_Item_1_0002_2ddf2e3b...` |

**Winner:** graph

_vector hits:_ ['NVDA_2024_Item_1A_0021_3fa26c8d', 'NVDA_2026_Item_1A_0024_b70c7a18']

_graph hits:_ ['NVDA_2024_Item_1A_0022_b1d57eb9', 'NVDA_2024_Item_1_0008_20833acc', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2025_Item_1_0009_7a56593b']

_hybrid hits:_ ['NVDA_2025_Item_1A_0020_69d9e1ec', 'NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2026_Item_1A_0023_804c637e']

---

## Q8: `What export controls affect AI chip sales from the maker of Blackwell architecture?`

- **type:** regulation_via_product
- **reasoning chain:** `Blackwell -PRODUCES-> NVIDIA -SUBJECT_TO-> Export Administration Regulations (China-bound)`
- **answer entities:** `['export administration regulations', 'china', 'bureau of industry and security']`
- **expected chunks in corpus:** 120

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `AMD_2025_Item_1A_0021_16aa3aa2...`, `NVDA_2025_Item_1A_0019_46eda16...`, `AMD_2026_Item_1A_0021_7fb03412...`, `NVDA_2026_Item_1A_0020_331dc53...`, `NVDA_2025_Item_1A_0023_67392e5...` |
| graph  | 1 | 1.00 | 5/5 | `NVDA_2025_Item_1A_0019_46eda16...`, `NVDA_2024_Item_1A_0019_ea1fd2e...`, `NVDA_2026_Item_1A_0020_331dc53...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...` |
| **hybrid** | **1** | **1.00** | **5/5** | `NVDA_2025_Item_1A_0019_46eda16...`, `NVDA_2026_Item_1A_0020_331dc53...`, `NVDA_2024_Item_1A_0019_ea1fd2e...`, `NVDA_2025_Item_1A_0023_67392e5...`, `AMD_2025_Item_1A_0021_16aa3aa2...` |

**Winner:** tie

_vector hits:_ ['AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537']

_graph hits:_ ['NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2026_Item_1A_0020_331dc537', 'NVDA_2026_Item_1_0008_edf8fe4b']

_hybrid hits:_ ['AMD_2025_Item_1A_0021_16aa3aa2', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537']

---

## Q9: `Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?`

- **type:** supplier_via_company
- **reasoning chain:** `NVIDIA <-SUPPLIES- {TSMC, Samsung, SK Hynix}`
- **answer entities:** `['tsmc', 'samsung electronics co ltd', 'sk hynix inc']`
- **expected chunks in corpus:** 35

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `MU_2024_Item_1A_0025_1809ff3b...`, `AMD_2024_Item_1_0012_9561038a...`, `AMD_2025_Item_1A_0002_2bc1ccc8...`, `NVDA_2025_Item_1_0008_a4407f7e...` |
| graph  | 1 | 1.00 | 5/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `NVDA_2025_Item_1_0008_a4407f7e...` |
| **hybrid** | **1** | **0.80** | **4/5** | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `INTC_2026_Item_1_0008_c74f560f...`, `MU_2024_Item_1A_0025_1809ff3b...` |

**Winner:** graph

_vector hits:_ ['AMD_2024_Item_1_0012_9561038a', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

_graph hits:_ ['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

_hybrid hits:_ ['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

---

## Q10: `Which Taiwanese contract chipmaker fabricates AMD's processors?`

- **type:** supplier_via_company
- **reasoning chain:** `AMD <-SUPPLIES- {TSMC, UMC}`
- **answer entities:** `['tsmc', 'umc']`
- **expected chunks in corpus:** 34

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `AMD_2024_Item_1_0001_84491be9...`, `MU_2024_Item_1A_0025_1809ff3b...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `AMD_2024_Item_1_0013_596acde4...` |
| graph  | 1 | 0.60 | 3/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...` |
| **hybrid** | **1** | **0.40** | **2/5** | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `INTC_2026_Item_1_0008_c74f560f...`, `AMD_2024_Item_1_0001_84491be9...`, `MU_2024_Item_1A_0025_1809ff3b...` |

**Winner:** graph

_vector hits:_ ['NVDA_2026_Item_1_0007_bf6a51b6']

_graph hits:_ ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

_hybrid hits:_ ['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2026_Item_1_0007_bf6a51b6']

---

## Q11: `In what U.S. state does the developer of the CUDA platform operate its headquarters?`

- **type:** geo_via_product
- **reasoning chain:** `CUDA -PRODUCES-> NVIDIA -OPERATES_IN-> {Santa Clara, California}`
- **answer entities:** `['santa clara', 'california']`
- **expected chunks in corpus:** 41

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `NVDA_2024_Item_1_0002_2ddf2e3b...`, `NVDA_2025_Item_1_0002_b74647bb...`, `NVDA_2025_Item_1_0003_ccc9ed65...`, `NVDA_2026_Item_1_0002_b628e1c2...`, `NVDA_2024_Item_1_0003_59fa75a8...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...`, `AMD_2025_Item_1_0009_c842eea0...` |
| **hybrid** | **1** | **0.40** | **2/5** | `NVDA_2024_Item_1_0002_2ddf2e3b...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0002_b74647bb...`, `NVDA_2025_Item_1_0003_ccc9ed65...` |

**Winner:** vector

_vector hits:_ ['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2025_Item_1_0002_b74647bb', 'NVDA_2026_Item_1_0002_b628e1c2']

_hybrid hits:_ ['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2025_Item_1_0002_b74647bb']

---

## Q12: `Which gaming console maker partners with the Ryzen processor company?`

- **type:** partner_via_product
- **reasoning chain:** `Ryzen -PRODUCES-> AMD -PARTNERS_WITH-> {Sony, Microsoft, Valve}`
- **answer entities:** `['sony', 'valve', 'microsoft']`
- **expected chunks in corpus:** 26

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.80 | 4/5 | `AMD_2026_Item_1_0004_b5e66359...`, `AMD_2026_Item_1_0005_808c1965...`, `AMD_2025_Item_1_0004_7a6fa20c...`, `AMD_2024_Item_7_0001_2f628a3f...`, `AMD_2024_Item_1_0006_e41aed21...` |
| graph  | 1 | 0.40 | 2/5 | `AMD_2025_Item_1A_0000_ac2e47a8...`, `INTC_2026_Item_1_0008_c74f560f...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...` |
| **hybrid** | **1** | **0.80** | **4/5** | `AMD_2025_Item_1A_0000_ac2e47a8...`, `AMD_2026_Item_1_0004_b5e66359...`, `AMD_2026_Item_1_0005_808c1965...`, `INTC_2026_Item_1_0008_c74f560f...`, `AMD_2025_Item_1_0004_7a6fa20c...` |

**Winner:** tie

_vector hits:_ ['AMD_2024_Item_1_0006_e41aed21', 'AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2026_Item_1_0005_808c1965']

_graph hits:_ ['INTC_2026_Item_1_0008_c74f560f', 'NVDA_2025_Item_1_0008_a4407f7e']

_hybrid hits:_ ['AMD_2025_Item_1_0004_7a6fa20c', 'AMD_2026_Item_1_0004_b5e66359', 'AMD_2026_Item_1_0005_808c1965', 'INTC_2026_Item_1_0008_c74f560f']

---

## Q13: `What product family does NVIDIA offer for the consumer gaming graphics market?`

- **type:** product_in_segment
- **reasoning chain:** `NVIDIA -PRODUCES-> GeForce (gaming consumer GPU line)`
- **answer entities:** `['geforce', 'geforce rtx', 'geforce now']`
- **expected chunks in corpus:** 9

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `AMD_2025_Item_1A_0002_2bc1ccc8...`, `AMD_2025_Item_1_0005_e788d800...`, `NVDA_2026_Item_1_0004_5a83036d...`, `AMD_2026_Item_1_0005_808c1965...`, `NVDA_2024_Item_1_0002_2ddf2e3b...` |
| graph  | 1 | 1.00 | 5/5 | `NVDA_2024_Item_1_0003_59fa75a8...`, `NVDA_2025_Item_1_0003_ccc9ed65...`, `NVDA_2026_Item_1_0003_0297d539...`, `NVDA_2026_Item_1_0004_5a83036d...`, `NVDA_2024_Item_1_0005_7f985cdb...` |
| **hybrid** | **1** | **0.80** | **4/5** | `NVDA_2026_Item_1_0004_5a83036d...`, `NVDA_2024_Item_1_0003_59fa75a8...`, `NVDA_2024_Item_1_0002_2ddf2e3b...`, `NVDA_2025_Item_1_0004_e3993ed7...`, `NVDA_2025_Item_1_0002_b74647bb...` |

**Winner:** graph

_vector hits:_ ['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2026_Item_1_0004_5a83036d']

_graph hits:_ ['NVDA_2024_Item_1_0003_59fa75a8', 'NVDA_2024_Item_1_0005_7f985cdb', 'NVDA_2025_Item_1_0003_ccc9ed65', 'NVDA_2026_Item_1_0003_0297d539', 'NVDA_2026_Item_1_0004_5a83036d']

_hybrid hits:_ ['NVDA_2024_Item_1_0002_2ddf2e3b', 'NVDA_2024_Item_1_0003_59fa75a8', 'NVDA_2025_Item_1_0002_b74647bb', 'NVDA_2026_Item_1_0004_5a83036d']

---

## Q14: `What revenue segments does the developer of EPYC processors disclose?`

- **type:** segment_via_product
- **reasoning chain:** `EPYC -PRODUCES-> AMD -HAS_STAKE_IN-> {Data Center, Client, Gaming, Embedded}`
- **answer entities:** `['data center', 'client segment', 'gaming segment', 'embedded', 'client and gaming']`
- **expected chunks in corpus:** 52

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `AMD_2024_Item_1_0003_ee436d61...`, `AMD_2025_Item_1_0003_861e4bfa...`, `AMD_2026_Item_1_0003_ea53a6a5...`, `INTC_2026_Item_7_0005_b363106d...`, `AMD_2024_Item_1_0010_842113d9...` |
| graph  | 1 | 1.00 | 5/5 | `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1_0008_db609f8f...`, `AMD_2025_Item_1_0009_c842eea0...`, `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2025_Item_7_0000_16c93d97...` |
| **hybrid** | **1** | **1.00** | **5/5** | `AMD_2024_Item_1_0003_ee436d61...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1_0003_861e4bfa...`, `AMD_2025_Item_1_0008_db609f8f...`, `AMD_2025_Item_1_0009_c842eea0...` |

**Winner:** tie

_vector hits:_ ['AMD_2024_Item_1_0003_ee436d61', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2026_Item_1_0003_ea53a6a5']

_graph hits:_ ['AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2025_Item_1_0009_c842eea0', 'AMD_2025_Item_7_0000_16c93d97', 'NVDA_2024_Item_1_0007_bae70036']

_hybrid hits:_ ['AMD_2024_Item_1_0003_ee436d61', 'AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0003_861e4bfa', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2025_Item_1_0009_c842eea0']

---

## Q15: `What U.S. agency oversees semiconductor export controls to China?`

- **type:** regulator_via_topic
- **reasoning chain:** `semiconductor companies -SUBJECT_TO-> BIS / Commerce Dept`
- **answer entities:** `['bureau of industry and security', 'u.s. department of commerce', 'export administration regulations']`
- **expected chunks in corpus:** 4

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.25 | 1/5 | `AMD_2026_Item_1A_0019_b7fa1437...`, `AMD_2025_Item_1A_0021_16aa3aa2...`, `NVDA_2025_Item_1A_0020_69d9e1e...`, `AMD_2026_Item_1A_0021_7fb03412...`, `AMD_2025_Item_1A_0020_0d19c86e...` |
| graph  | 1 | 0.25 | 1/5 | `INTC_2024_Item_1A_0009_dd11a01...`, `AMD_2026_Item_1A_0019_b7fa1437...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...` |
| **hybrid** | **1** | **0.25** | **1/5** | `AMD_2026_Item_1A_0019_b7fa1437...`, `NVDA_2025_Item_1A_0019_46eda16...`, `INTC_2024_Item_1A_0009_dd11a01...`, `AMD_2025_Item_1A_0021_16aa3aa2...`, `NVDA_2024_Item_1_0008_20833acc...` |

**Winner:** tie

_vector hits:_ ['AMD_2026_Item_1A_0019_b7fa1437']

_graph hits:_ ['AMD_2026_Item_1A_0019_b7fa1437']

_hybrid hits:_ ['AMD_2026_Item_1A_0019_b7fa1437']

---

## Q16: `What macroeconomic conditions create headwinds for chip industry revenue?`

- **type:** macro_risk
- **reasoning chain:** `companies -IMPACTED_BY-> {geopolitical tensions, economic instability}`
- **answer entities:** `['geopolitical tensions', 'political and economic instability', 'geopolitical conditions', 'global business disruptions', 'economic and market uncertainty']`
- **expected chunks in corpus:** 36

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `AMD_2024_Item_1A_0004_eabb01e8...`, `INTC_2024_Item_1A_0008_e11f22f...`, `AMD_2024_Item_1A_0003_cd973f49...`, `AMD_2025_Item_1A_0004_3da97b4d...`, `AMD_2024_Item_1A_0006_16ed3c8d...` |
| graph  | 1 | 0.20 | 1/5 | `INTC_2024_Item_1A_0009_dd11a01...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...`, `AMD_2026_Item_1A_0019_b7fa1437...` |
| **hybrid** | **1** | **0.20** | **1/5** | `AMD_2024_Item_1A_0004_eabb01e8...`, `NVDA_2024_Item_1_0007_bae70036...`, `INTC_2024_Item_1A_0008_e11f22f...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `AMD_2024_Item_1A_0003_cd973f49...` |

**Winner:** tie

_vector hits:_ ['AMD_2024_Item_1A_0003_cd973f49']

_graph hits:_ ['INTC_2024_Item_1A_0009_dd11a01d']

_hybrid hits:_ ['AMD_2024_Item_1A_0003_cd973f49']

---

## Q17: `Which Asian country hosts most semiconductor wafer fabrication capacity?`

- **type:** geo_via_industry
- **reasoning chain:** `wafer fab industry -> {TSMC, UMC} -OPERATES_IN-> Taiwan`
- **answer entities:** `['taiwan']`
- **expected chunks in corpus:** 51

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `MU_2024_Item_1A_0025_1809ff3b...`, `MU_2025_Item_1_0006_0c03fa5d...`, `INTC_2025_Item_1_0010_5c90fb55...`, `MU_2024_Item_1_0006_6b1663cd...`, `NVDA_2026_Item_1_0007_bf6a51b6...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...` |
| **hybrid** | **1** | **0.40** | **2/5** | `NVDA_2026_Item_1_0007_bf6a51b6...`, `MU_2024_Item_1A_0025_1809ff3b...`, `MU_2025_Item_1_0006_0c03fa5d...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `INTC_2025_Item_1_0010_5c90fb55...` |

**Winner:** vector

_vector hits:_ ['MU_2024_Item_1A_0025_1809ff3b', 'MU_2024_Item_1_0006_6b1663cd', 'MU_2025_Item_1_0006_0c03fa5d']

_hybrid hits:_ ['MU_2024_Item_1A_0025_1809ff3b', 'MU_2025_Item_1_0006_0c03fa5d']

---

## Q18: `What data center accelerators come from the developer of Hopper architecture?`

- **type:** product_line_via_product
- **reasoning chain:** `Hopper -PRODUCES-> NVIDIA -PRODUCES-> {H100, H200, A100, Blackwell, GB200}`
- **answer entities:** `['h100', 'h200', 'a100', 'blackwell', 'gb200', 'gb300', 'blackwell architecture']`
- **expected chunks in corpus:** 21

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `INTC_2026_Item_1_0004_c01224f1...`, `INTC_2024_Item_7_0005_d449d027...`, `NVDA_2025_Item_1_0005_85d95b7e...`, `INTC_2026_Item_1_0012_75eaf984...`, `NVDA_2026_Item_1_0003_0297d539...` |
| graph  | 1 | 0.80 | 4/5 | `NVDA_2025_Item_7_0002_b40db6b2...`, `NVDA_2025_Item_7_0001_20eaad59...`, `NVDA_2025_Item_7_0003_d53d3047...`, `NVDA_2026_Item_7_0001_485abbd3...`, `NVDA_2024_Item_7_0003_ba144df9...` |
| **hybrid** | **1** | **0.20** | **1/5** | `INTC_2026_Item_1_0004_c01224f1...`, `NVDA_2024_Item_7_0003_ba144df9...`, `INTC_2024_Item_7_0005_d449d027...`, `NVDA_2024_Item_7_0007_d25e117d...`, `NVDA_2025_Item_1_0003_ccc9ed65...` |

**Winner:** graph

_vector hits:_ ['NVDA_2026_Item_1_0003_0297d539']

_graph hits:_ ['NVDA_2025_Item_7_0001_20eaad59', 'NVDA_2025_Item_7_0002_b40db6b2', 'NVDA_2025_Item_7_0003_d53d3047', 'NVDA_2026_Item_7_0001_485abbd3']

_hybrid hits:_ ['NVDA_2025_Item_1_0003_ccc9ed65']

---

## Q19: `What market segments does Intel's primary CPU competitor pursue for growth?`

- **type:** segment_via_competitor
- **reasoning chain:** `Intel <-COMPETES_WITH- AMD -HAS_STAKE_IN-> {Data Center, Gaming, Client}`
- **answer entities:** `['data center', 'gaming segment', 'client segment', 'embedded', 'client and gaming']`
- **expected chunks in corpus:** 52

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2024_Item_1_0011_49024c2d...`, `INTC_2026_Item_1_0008_c74f560f...`, `INTC_2025_Item_1_0003_707a268b...` |
| graph  | 1 | 0.60 | 3/5 | `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1_0008_db609f8f...`, `AMD_2026_Item_1_0009_ac9cc232...`, `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2025_Item_1A_0001_0fd81b24...` |
| **hybrid** | **1** | **0.60** | **3/5** | `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `INTC_2025_Item_7_0003_878f7d25...`, `AMD_2025_Item_1_0008_db609f8f...` |

**Winner:** tie

_vector hits:_ ['AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0009_c842eea0']

_graph hits:_ ['AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2025_Item_1_0009_c842eea0']

_hybrid hits:_ ['AMD_2024_Item_1_0011_49024c2d', 'AMD_2025_Item_1_0008_db609f8f', 'AMD_2025_Item_1_0009_c842eea0']

---

## Q20: `What graphics product line does AMD offer to compete with NVIDIA's RTX series?`

- **type:** competitor_product
- **reasoning chain:** `NVIDIA -PRODUCES-> RTX, AMD -PRODUCES-> Radeon`
- **answer entities:** `['radeon', 'amd radeon', 'amd radeon pro']`
- **expected chunks in corpus:** 5

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `AMD_2025_Item_1_0005_e788d800...`, `AMD_2026_Item_1_0005_808c1965...`, `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2025_Item_1_0007_0ffd6ad4...`, `AMD_2025_Item_1_0009_c842eea0...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...`, `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2025_Item_1_0009_c842eea0...` |
| **hybrid** | **1** | **0.20** | **1/5** | `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1_0005_e788d800...`, `NVDA_2024_Item_1_0008_20833acc...` |

**Winner:** tie

_vector hits:_ ['AMD_2025_Item_1_0005_e788d800']

_hybrid hits:_ ['AMD_2025_Item_1_0005_e788d800']

---

## Q21: `Which Asian contract chipmakers fabricate older-generation processors for the developer of Intel 18A?`

- **type:** supplier_via_product
- **reasoning chain:** `Intel 18A -PRODUCES-> Intel <-SUPPLIES- {TSMC, UMC, SMIC}`
- **answer entities:** `['tsmc', 'umc', 'smic']`
- **expected chunks in corpus:** 37

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `INTC_2026_Item_7_0003_657be427...`, `INTC_2024_Item_7_0000_e2ea081b...`, `INTC_2026_Item_1_0008_c74f560f...`, `INTC_2026_Item_7_0004_e8790cb8...`, `MU_2024_Item_1A_0025_1809ff3b...` |
| graph  | 1 | 1.00 | 5/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `INTC_2026_Item_1_0008_c74f560f...`, `INTC_2026_Item_1A_0014_753689d...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...` |
| **hybrid** | **1** | **0.60** | **3/5** | `INTC_2026_Item_1_0008_c74f560f...`, `INTC_2026_Item_7_0003_657be427...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `INTC_2024_Item_7_0000_e2ea081b...`, `INTC_2026_Item_1A_0014_753689d...` |

**Winner:** graph

_vector hits:_ ['INTC_2026_Item_1_0008_c74f560f']

_graph hits:_ ['INTC_2026_Item_1A_0014_753689d7', 'INTC_2026_Item_1_0008_c74f560f', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

_hybrid hits:_ ['INTC_2026_Item_1A_0014_753689d7', 'INTC_2026_Item_1_0008_c74f560f', 'NVDA_2026_Item_1_0007_bf6a51b6']

---

## Q22: `Which infrastructure investment firms partner with the maker of Xeon Scalable processors on fab financing?`

- **type:** partner_via_product
- **reasoning chain:** `Xeon -PRODUCES-> Intel -PARTNERS_WITH-> {Brookfield, Apollo}`
- **answer entities:** `['brookfield', 'apollo']`
- **expected chunks in corpus:** 8

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `INTC_2024_Item_1_0004_692d8999...`, `INTC_2025_Item_1_0007_1d4a96e6...`, `INTC_2024_Item_7_0005_d449d027...`, `INTC_2024_Item_7_0008_57402d3f...`, `INTC_2024_Item_1_0008_cca3187e...` |
| graph  | 1 | 1.00 | 5/5 | `INTC_2025_Item_1A_0007_42fef1f...`, `INTC_2026_Item_1A_0006_820d3c6...`, `INTC_2025_Item_1_0011_b8759c99...`, `INTC_2026_Item_1A_0007_7a211a2...`, `INTC_2024_Item_1A_0007_6560bf5...` |
| **hybrid** | **1** | **0.40** | **2/5** | `INTC_2024_Item_1_0004_692d8999...`, `INTC_2025_Item_1A_0007_42fef1f...`, `INTC_2025_Item_1_0007_1d4a96e6...`, `INTC_2026_Item_1A_0006_820d3c6...`, `INTC_2024_Item_7_0005_d449d027...` |

**Winner:** graph

_graph hits:_ ['INTC_2024_Item_1A_0007_6560bf56', 'INTC_2025_Item_1A_0007_42fef1f5', 'INTC_2025_Item_1_0011_b8759c99', 'INTC_2026_Item_1A_0006_820d3c64', 'INTC_2026_Item_1A_0007_7a211a24']

_hybrid hits:_ ['INTC_2025_Item_1A_0007_42fef1f5', 'INTC_2026_Item_1A_0006_820d3c64']

---

## Q23: `Which autonomous driving subsidiary does the developer of Intel Core Ultra operate?`

- **type:** subsidiary_via_product
- **reasoning chain:** `Intel Core Ultra -PRODUCES-> Intel -HAS_STAKE_IN-> Mobileye`
- **answer entities:** `['mobileye']`
- **expected chunks in corpus:** 27

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `NVDA_2024_Item_1_0004_12c02096...`, `INTC_2025_Item_1_0003_707a268b...`, `INTC_2024_Item_1_0005_bcb431a8...`, `INTC_2026_Item_1_0010_4bfc9726...`, `AMD_2025_Item_1_0002_6fadf6e4...` |
| graph  | 1 | 1.00 | 5/5 | `INTC_2024_Item_7_0009_2d5f3afe...`, `INTC_2024_Item_7_0011_0681e088...`, `INTC_2025_Item_7_0011_938c6e10...`, `INTC_2025_Item_7_0012_9777af13...`, `INTC_2026_Item_7_0008_c25889d2...` |
| **hybrid** | **1** | **0.40** | **2/5** | `INTC_2024_Item_7_0009_2d5f3afe...`, `NVDA_2024_Item_1_0004_12c02096...`, `INTC_2024_Item_7_0011_0681e088...`, `INTC_2025_Item_1_0003_707a268b...`, `INTC_2024_Item_1_0005_bcb431a8...` |

**Winner:** graph

_graph hits:_ ['INTC_2024_Item_7_0009_2d5f3afe', 'INTC_2024_Item_7_0011_0681e088', 'INTC_2025_Item_7_0011_938c6e10', 'INTC_2025_Item_7_0012_9777af13', 'INTC_2026_Item_7_0008_c25889d2']

_hybrid hits:_ ['INTC_2024_Item_7_0009_2d5f3afe', 'INTC_2024_Item_7_0011_0681e088']

---

## Q24: `Which operating system maker collaborates with the Xeon Scalable processor developer on AI PC platforms?`

- **type:** partner_via_product
- **reasoning chain:** `Xeon -PRODUCES-> Intel -PARTNERS_WITH-> Microsoft (AI PC)`
- **answer entities:** `['microsoft']`
- **expected chunks in corpus:** 26

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `INTC_2024_Item_7_0005_d449d027...`, `INTC_2026_Item_1_0004_c01224f1...`, `INTC_2025_Item_7_0003_878f7d25...`, `INTC_2025_Item_1_0003_707a268b...`, `INTC_2024_Item_7_0000_e2ea081b...` |
| graph  | 1 | 0.20 | 1/5 | `INTC_2024_Item_7_0005_d449d027...`, `INTC_2024_Item_7_0002_7c82ed88...`, `INTC_2026_Item_1_0006_d0f653da...`, `INTC_2024_Item_1_0002_9b4c4826...`, `INTC_2026_Item_1_0002_ed840c4e...` |
| **hybrid** | **1** | **0.20** | **1/5** | `INTC_2024_Item_7_0005_d449d027...`, `INTC_2025_Item_1_0003_707a268b...`, `INTC_2024_Item_1_0005_bcb431a8...`, `INTC_2024_Item_7_0002_7c82ed88...`, `INTC_2026_Item_1_0004_c01224f1...` |

**Winner:** tie

_graph hits:_ ['INTC_2024_Item_7_0002_7c82ed88']

_hybrid hits:_ ['INTC_2024_Item_7_0002_7c82ed88']

---

## Q25: `In which U.S. states does the developer of the Intel 18A process operate wafer fabrication facilities?`

- **type:** geo_via_product
- **reasoning chain:** `Intel 18A -PRODUCES-> Intel -OPERATES_IN-> {Arizona, Ohio, Oregon, New Mexico}`
- **answer entities:** `['arizona', 'ohio', 'oregon', 'new mexico']`
- **expected chunks in corpus:** 22

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `INTC_2025_Item_1_0010_5c90fb55...`, `INTC_2025_Item_1_0004_c5a12b11...`, `MU_2024_Item_1A_0025_1809ff3b...`, `MU_2025_Item_1_0007_ad907262...`, `MU_2025_Item_1A_0029_541d266d...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...`, `INTC_2026_Item_1_0008_c74f560f...` |
| **hybrid** | **1** | **0.80** | **4/5** | `INTC_2025_Item_1_0004_c5a12b11...`, `INTC_2025_Item_1_0010_5c90fb55...`, `INTC_2025_Item_1_0009_d132a876...`, `INTC_2026_Item_1_0014_5d25166d...`, `MU_2024_Item_1A_0025_1809ff3b...` |

**Winner:** hybrid

_vector hits:_ ['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2025_Item_1_0010_5c90fb55']

_hybrid hits:_ ['INTC_2025_Item_1_0004_c5a12b11', 'INTC_2025_Item_1_0009_d132a876', 'INTC_2025_Item_1_0010_5c90fb55', 'INTC_2026_Item_1_0014_5d25166d']

---

## Q26: `In which Middle Eastern country does the developer of Xeon Scalable processors operate a major fab?`

- **type:** geo_via_product
- **reasoning chain:** `Xeon -PRODUCES-> Intel -OPERATES_IN-> Israel (Kiryat Gat)`
- **answer entities:** `['israel']`
- **expected chunks in corpus:** 38

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `INTC_2024_Item_1_0004_692d8999...`, `INTC_2024_Item_7_0005_d449d027...`, `INTC_2024_Item_7_0000_e2ea081b...`, `INTC_2024_Item_7_0008_57402d3f...`, `INTC_2026_Item_1_0012_75eaf984...` |
| graph  | 1 | 1.00 | 5/5 | `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2026_Item_1_0008_edf8fe4b...`, `INTC_2024_Item_1A_0010_bc6cab8...`, `INTC_2024_Item_1_0001_c6df83d9...`, `INTC_2024_Item_1_0004_692d8999...` |
| **hybrid** | **1** | **0.60** | **3/5** | `INTC_2024_Item_1_0004_692d8999...`, `NVDA_2025_Item_1_0009_7a56593b...`, `INTC_2024_Item_7_0005_d449d027...`, `NVDA_2026_Item_1_0008_edf8fe4b...`, `INTC_2024_Item_7_0000_e2ea081b...` |

**Winner:** graph

_vector hits:_ ['INTC_2024_Item_1_0004_692d8999']

_graph hits:_ ['INTC_2024_Item_1A_0010_bc6cab8d', 'INTC_2024_Item_1_0001_c6df83d9', 'INTC_2024_Item_1_0004_692d8999', 'NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2026_Item_1_0008_edf8fe4b']

_hybrid hits:_ ['INTC_2024_Item_1_0004_692d8999', 'NVDA_2025_Item_1_0009_7a56593b', 'NVDA_2026_Item_1_0008_edf8fe4b']

---

## Q27: `What primary reporting segments does the maker of Xeon Scalable break out in its annual filings?`

- **type:** segment_via_product
- **reasoning chain:** `Xeon -PRODUCES-> Intel -HAS_STAKE_IN-> {DCAI, CCG, Intel Foundry, NEX}`
- **answer entities:** `['dcai', 'ccg', 'intel foundry', 'nex', 'data center and ai', 'client computing group']`
- **expected chunks in corpus:** 49

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `INTC_2024_Item_1_0004_692d8999...`, `INTC_2024_Item_7_0000_e2ea081b...`, `AMD_2024_Item_1_0003_ee436d61...`, `INTC_2024_Item_7_0005_d449d027...`, `AMD_2025_Item_1_0003_861e4bfa...` |
| graph  | 1 | 0.60 | 3/5 | `INTC_2024_Item_7_0008_57402d3f...`, `INTC_2025_Item_7_0005_5c1a235d...`, `INTC_2025_Item_7_0003_878f7d25...`, `INTC_2024_Item_7_0005_d449d027...`, `INTC_2024_Item_7_0000_e2ea081b...` |
| **hybrid** | **1** | **0.40** | **2/5** | `INTC_2024_Item_7_0000_e2ea081b...`, `INTC_2024_Item_7_0005_d449d027...`, `INTC_2024_Item_1_0004_692d8999...`, `INTC_2024_Item_7_0008_57402d3f...`, `INTC_2025_Item_7_0005_5c1a235d...` |

**Winner:** graph

_vector hits:_ ['INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_7_0005_d449d027']

_graph hits:_ ['INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_7_0005_d449d027', 'INTC_2025_Item_7_0003_878f7d25']

_hybrid hits:_ ['INTC_2024_Item_7_0000_e2ea081b', 'INTC_2024_Item_7_0005_d449d027']

---

## Q28: `What U.S. legislative act funds domestic semiconductor manufacturing expansion at the Intel 18A developer?`

- **type:** regulator_via_product
- **reasoning chain:** `Intel 18A -PRODUCES-> Intel -SUBJECT_TO-> CHIPS Act`
- **answer entities:** `['chips act']`
- **expected chunks in corpus:** 16

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `INTC_2026_Item_1A_0008_662b7d4...`, `INTC_2025_Item_1A_0008_80e72e4...`, `MU_2025_Item_7_0006_849b23ef...`, `MU_2025_Item_1A_0029_541d266d...`, `INTC_2026_Item_1_0005_f5ba2220...` |
| graph  | 1 | 0.60 | 3/5 | `INTC_2025_Item_1A_0008_80e72e4...`, `INTC_2025_Item_7_0016_775a205b...`, `INTC_2024_Item_1A_0007_6560bf5...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `INTC_2025_Item_7_0013_1869b003...` |
| **hybrid** | **1** | **0.80** | **4/5** | `INTC_2025_Item_1A_0008_80e72e4...`, `INTC_2026_Item_1A_0008_662b7d4...`, `INTC_2025_Item_7_0016_775a205b...`, `INTC_2024_Item_1A_0007_6560bf5...`, `MU_2025_Item_7_0006_849b23ef...` |

**Winner:** hybrid

_vector hits:_ ['INTC_2025_Item_1A_0008_80e72e45', 'INTC_2026_Item_1A_0008_662b7d4d', 'MU_2025_Item_1A_0029_541d266d']

_graph hits:_ ['INTC_2024_Item_1A_0007_6560bf56', 'INTC_2025_Item_1A_0008_80e72e45', 'INTC_2025_Item_7_0016_775a205b']

_hybrid hits:_ ['INTC_2024_Item_1A_0007_6560bf56', 'INTC_2025_Item_1A_0008_80e72e45', 'INTC_2025_Item_7_0016_775a205b', 'INTC_2026_Item_1A_0008_662b7d4d']

---

## Q29: `Which ARM-based mobile chip companies compete with the developer of x86 processor cores in the client computing market?`

- **type:** competitor_via_product
- **reasoning chain:** `x86 cores -PRODUCES-> Intel <-COMPETES_WITH- {Qualcomm, MediaTek, Apple}`
- **answer entities:** `['qualcomm', 'mediatek', 'apple']`
- **expected chunks in corpus:** 7

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `INTC_2026_Item_1_0004_c01224f1...`, `INTC_2026_Item_1_0008_c74f560f...`, `AMD_2024_Item_1_0011_49024c2d...` |
| graph  | 1 | 0.20 | 1/5 | `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2025_Item_1_0008_a4407f7e...` |
| **hybrid** | **1** | **0.20** | **1/5** | `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2024_Item_1_0011_49024c2d...`, `INTC_2026_Item_1A_0000_268148d...`, `INTC_2026_Item_1_0004_c01224f1...` |

**Winner:** tie

_graph hits:_ ['NVDA_2025_Item_1_0008_a4407f7e']

_hybrid hits:_ ['INTC_2026_Item_1A_0000_268148d2']

---

## Q30: `What advanced driver assistance product lines come from the autonomous driving subsidiary of the Xeon Scalable developer?`

- **type:** three_hop_subsidiary_product
- **reasoning chain:** `Xeon -PRODUCES-> Intel -HAS_STAKE_IN-> Mobileye -PRODUCES-> {SuperVision, Chauffeur, Drive}`
- **answer entities:** `['mobileye supervision', 'mobileye chauffeur', 'mobileye drive']`
- **expected chunks in corpus:** 4

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `INTC_2024_Item_7_0005_d449d027...`, `NVDA_2024_Item_1_0004_12c02096...`, `NVDA_2024_Item_1_0006_f3efd950...`, `NVDA_2025_Item_1_0005_85d95b7e...`, `INTC_2025_Item_7_0003_878f7d25...` |
| graph  | 1 | 0.25 | 1/5 | `INTC_2024_Item_7_0011_0681e088...`, `INTC_2026_Item_7_0017_86b90f80...`, `INTC_2024_Item_7_0005_d449d027...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1A_0000_ac2e47a8...` |
| **hybrid** | **1** | **0.50** | **2/5** | `INTC_2024_Item_7_0005_d449d027...`, `INTC_2024_Item_7_0011_0681e088...`, `INTC_2026_Item_7_0017_86b90f80...`, `NVDA_2024_Item_1_0004_12c02096...`, `INTC_2024_Item_7_0009_2d5f3afe...` |

**Winner:** hybrid

_graph hits:_ ['INTC_2024_Item_7_0011_0681e088']

_hybrid hits:_ ['INTC_2024_Item_7_0009_2d5f3afe', 'INTC_2024_Item_7_0011_0681e088']

---

## Q31: `What U.S. export restrictions affect chip sales by the Intel 18A developer to specific Asian end markets?`

- **type:** regulator_via_product
- **reasoning chain:** `Intel 18A -PRODUCES-> Intel -SUBJECT_TO-> {export controls, EAR, China}`
- **answer entities:** `['export controls', 'export administration regulations', 'china']`
- **expected chunks in corpus:** 125

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `AMD_2025_Item_1A_0021_16aa3aa2...`, `NVDA_2025_Item_1A_0020_69d9e1e...`, `AMD_2026_Item_1A_0019_b7fa1437...`, `NVDA_2024_Item_1A_0020_ac4ad7b...`, `AMD_2026_Item_1A_0021_7fb03412...` |
| graph  | 0 | 0.00 | 0/5 | `AMD_2025_Item_1A_0001_0fd81b24...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1A_0000_ac2e47a8...`, `AMD_2025_Item_1_0008_db609f8f...`, `AMD_2025_Item_1_0009_c842eea0...` |
| **hybrid** | **1** | **0.40** | **2/5** | `AMD_2025_Item_1A_0001_0fd81b24...`, `AMD_2025_Item_1A_0021_16aa3aa2...`, `AMD_2024_Item_1_0011_49024c2d...`, `NVDA_2025_Item_1A_0020_69d9e1e...`, `AMD_2025_Item_1A_0000_ac2e47a8...` |

**Winner:** vector

_vector hits:_ ['AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0019_b7fa1437', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2024_Item_1A_0020_ac4ad7b4', 'NVDA_2025_Item_1A_0020_69d9e1ec']

_hybrid hits:_ ['AMD_2025_Item_1A_0021_16aa3aa2', 'NVDA_2025_Item_1A_0020_69d9e1ec']

---

## Q32: `How does the IDM 2.0 strategy aim to restore U.S. semiconductor manufacturing leadership?`

- **type:** topical_strategy
- **reasoning chain:** `topical — IDM 2.0 + Smart Capital + internal foundry`
- **answer entities:** `['idm 2.0', 'idm 2.0 strategy', 'smart capital initiatives', 'internal foundry operating model', 'idm 2.0 strategy implementation risk']`
- **expected chunks in corpus:** 6

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.20 | 1/5 | `INTC_2024_Item_1_0007_bfb6b7ec...`, `INTC_2024_Item_1A_0006_f838a2b...`, `INTC_2024_Item_1A_0001_f0f6c35...`, `INTC_2026_Item_1_0005_f5ba2220...`, `INTC_2024_Item_1_0014_32e0816b...` |
| graph  | 1 | 0.80 | 4/5 | `INTC_2024_Item_7_0015_575e5365...`, `INTC_2024_Item_1A_0012_4f56bd2...`, `INTC_2024_Item_7_0012_b8db0489...`, `INTC_2026_Item_7_0007_62b94998...`, `INTC_2024_Item_1A_0006_f838a2b...` |
| **hybrid** | **1** | **0.80** | **4/5** | `INTC_2024_Item_1A_0006_f838a2b...`, `INTC_2024_Item_7_0012_b8db0489...`, `INTC_2024_Item_1_0007_bfb6b7ec...`, `INTC_2024_Item_7_0015_575e5365...`, `INTC_2024_Item_1A_0012_4f56bd2...` |

**Winner:** tie

_vector hits:_ ['INTC_2024_Item_1A_0006_f838a2b7']

_graph hits:_ ['INTC_2024_Item_1A_0006_f838a2b7', 'INTC_2024_Item_1A_0012_4f56bd2f', 'INTC_2024_Item_7_0012_b8db0489', 'INTC_2024_Item_7_0015_575e5365']

_hybrid hits:_ ['INTC_2024_Item_1A_0006_f838a2b7', 'INTC_2024_Item_1A_0012_4f56bd2f', 'INTC_2024_Item_7_0012_b8db0489', 'INTC_2024_Item_7_0015_575e5365']

---

## Q33: `What consumer storage and DRAM brand is sold by the U.S. supplier of HBM3E memory?`

- **type:** product_via_company
- **reasoning chain:** `HBM3E -PRODUCES-> Micron -PRODUCES-> Crucial`
- **answer entities:** `['crucial']`
- **expected chunks in corpus:** 5

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `MU_2025_Item_1_0001_b64486b7...`, `MU_2025_Item_1_0010_ef8bd774...`, `MU_2023_Item_1_0002_74d97a0e...`, `MU_2023_Item_1_0003_fb3cb967...`, `MU_2024_Item_1_0001_90ffbd18...` |
| graph  | 0 | 0.00 | 0/5 | `MU_2023_Item_7_0002_c0fab91a...`, `MU_2023_Item_1A_0003_92be33e3...`, `MU_2023_Item_1_0013_c12aeeff...`, `MU_2023_Item_7_0000_e9f96198...`, `MU_2023_Item_1_0001_70be5bda...` |
| **hybrid** | **0** | **0.00** | **0/5** | `MU_2025_Item_1_0001_b64486b7...`, `MU_2023_Item_7_0002_c0fab91a...`, `MU_2023_Item_1A_0003_92be33e3...`, `MU_2025_Item_1_0010_ef8bd774...`, `MU_2023_Item_1_0002_74d97a0e...` |

**Winner:** tie

---

## Q34: `In which Asian countries does the developer of HBM3E memory operate fabrication or assembly facilities?`

- **type:** geo_via_product
- **reasoning chain:** `HBM3E -PRODUCES-> Micron -OPERATES_IN-> {Taiwan, Japan, Malaysia, Singapore}`
- **answer entities:** `['taiwan', 'japan', 'malaysia', 'singapore']`
- **expected chunks in corpus:** 64

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.60 | 3/5 | `MU_2025_Item_1_0010_ef8bd774...`, `MU_2024_Item_1A_0025_1809ff3b...`, `MU_2025_Item_1A_0005_edea08b6...`, `MU_2025_Item_1_0006_0c03fa5d...`, `AMD_2024_Item_1_0013_596acde4...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2025_Item_1_0009_7a56593b...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2024_Item_1_0008_20833acc...` |
| **hybrid** | **1** | **0.40** | **2/5** | `MU_2025_Item_1_0010_ef8bd774...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `MU_2024_Item_1A_0025_1809ff3b...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `MU_2025_Item_1A_0005_edea08b6...` |

**Winner:** vector

_vector hits:_ ['MU_2024_Item_1A_0025_1809ff3b', 'MU_2025_Item_1_0006_0c03fa5d', 'MU_2025_Item_1_0010_ef8bd774']

_hybrid hits:_ ['MU_2024_Item_1A_0025_1809ff3b', 'MU_2025_Item_1_0010_ef8bd774']

---

## Q35: `Which AI accelerator vendor purchases HBM3E from the U.S. memory supplier for its data center GPUs?`

- **type:** customer_via_product
- **reasoning chain:** `HBM3E -PRODUCES-> Micron -SUPPLIES-> NVIDIA`
- **answer entities:** `['nvidia', 'nvidia corporation']`
- **expected chunks in corpus:** 147

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `NVDA_2026_Item_1_0003_0297d539...`, `INTC_2026_Item_1_0004_c01224f1...`, `AMD_2026_Item_1_0009_ac9cc232...`, `NVDA_2026_Item_1_0005_9725a5a2...`, `INTC_2025_Item_7_0003_878f7d25...` |
| graph  | 1 | 1.00 | 5/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `INTC_2025_Item_7_0003_878f7d25...`, `AMD_2024_Item_1_0011_49024c2d...` |
| **hybrid** | **1** | **1.00** | **5/5** | `INTC_2025_Item_7_0003_878f7d25...`, `AMD_2026_Item_1_0009_ac9cc232...`, `AMD_2025_Item_1_0008_db609f8f...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2026_Item_1_0003_0297d539...` |

**Winner:** tie

_vector hits:_ ['AMD_2026_Item_1_0009_ac9cc232', 'INTC_2025_Item_7_0003_878f7d25', 'INTC_2026_Item_1_0004_c01224f1', 'NVDA_2026_Item_1_0003_0297d539', 'NVDA_2026_Item_1_0005_9725a5a2']

_graph hits:_ ['AMD_2024_Item_1_0011_49024c2d', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

_hybrid hits:_ ['AMD_2025_Item_1_0008_db609f8f', 'AMD_2026_Item_1_0009_ac9cc232', 'INTC_2025_Item_7_0003_878f7d25', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_1_0003_0297d539']

---

## Q36: `In what European country is the sole producer of EUV lithography systems headquartered?`

- **type:** geo_via_product
- **reasoning chain:** `EUV -PRODUCES-> ASML -OPERATES_IN-> Netherlands`
- **answer entities:** `['netherlands']`
- **expected chunks in corpus:** 3

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `INTC_2026_Item_1_0017_277e4e1d...`, `INTC_2025_Item_1_0010_5c90fb55...`, `MU_2025_Item_1_0010_ef8bd774...`, `MU_2024_Item_1A_0025_1809ff3b...`, `INTC_2026_Item_1_0005_f5ba2220...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `INTC_2026_Item_1_0017_277e4e1d...`, `NVDA_2024_Item_1_0008_20833acc...` |
| **hybrid** | **0** | **0.00** | **0/5** | `INTC_2026_Item_1_0017_277e4e1d...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `INTC_2025_Item_1_0010_5c90fb55...`, `NVDA_2024_Item_1_0007_bae70036...`, `MU_2025_Item_1_0010_ef8bd774...` |

**Winner:** tie

---

## Q37: `Which leading-edge semiconductor manufacturers are the largest customers of the EUV lithography systems maker?`

- **type:** customer_via_product
- **reasoning chain:** `EUV -PRODUCES-> ASML -SUPPLIES-> {TSMC, Samsung, Intel}`
- **answer entities:** `['tsmc', 'samsung electronics', 'samsung', 'intel']`
- **expected chunks in corpus:** 179

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `INTC_2026_Item_1_0017_277e4e1d...`, `INTC_2026_Item_1_0005_f5ba2220...`, `INTC_2025_Item_1_0010_5c90fb55...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `INTC_2025_Item_1A_0001_65932be...` |
| graph  | 1 | 0.80 | 4/5 | `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1_0009_c842eea0...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0007_bae70036...` |
| **hybrid** | **1** | **0.80** | **4/5** | `NVDA_2026_Item_1_0007_bf6a51b6...`, `INTC_2026_Item_1_0008_c74f560f...`, `AMD_2026_Item_1_0010_460dfa17...`, `INTC_2026_Item_1_0017_277e4e1d...`, `AMD_2024_Item_1_0011_49024c2d...` |

**Winner:** vector

_vector hits:_ ['INTC_2025_Item_1A_0001_65932be2', 'INTC_2025_Item_1_0010_5c90fb55', 'INTC_2026_Item_1_0005_f5ba2220', 'INTC_2026_Item_1_0017_277e4e1d', 'NVDA_2026_Item_1_0007_bf6a51b6']

_graph hits:_ ['AMD_2025_Item_1_0009_c842eea0', 'AMD_2026_Item_1_0010_460dfa17', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_1_0007_bf6a51b6']

_hybrid hits:_ ['AMD_2026_Item_1_0010_460dfa17', 'INTC_2026_Item_1_0008_c74f560f', 'INTC_2026_Item_1_0017_277e4e1d', 'NVDA_2026_Item_1_0007_bf6a51b6']

---

## Q38: `Which export license regime restricts EUV lithography system shipments to Chinese semiconductor manufacturers?`

- **type:** regulator_via_product
- **reasoning chain:** `EUV -PRODUCES-> ASML -SUBJECT_TO-> {export controls, export licenses}`
- **answer entities:** `['export licenses', 'export controls', 'china']`
- **expected chunks in corpus:** 125

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `NVDA_2025_Item_1A_0020_69d9e1e...`, `AMD_2026_Item_1A_0021_7fb03412...`, `AMD_2025_Item_1A_0021_16aa3aa2...`, `NVDA_2026_Item_1A_0023_804c637...`, `AMD_2026_Item_1A_0019_b7fa1437...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `AMD_2025_Item_1A_0001_0fd81b24...`, `AMD_2024_Item_1_0011_49024c2d...` |
| **hybrid** | **1** | **0.60** | **3/5** | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1A_0020_69d9e1e...`, `AMD_2026_Item_1A_0021_7fb03412...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `AMD_2025_Item_1A_0021_16aa3aa2...` |

**Winner:** vector

_vector hits:_ ['AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0019_b7fa1437', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2025_Item_1A_0020_69d9e1ec', 'NVDA_2026_Item_1A_0023_804c637e']

_hybrid hits:_ ['AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2025_Item_1A_0020_69d9e1ec']

---

## Q39: `Why has HBM become critical for modern AI training and inference workloads?`

- **type:** topical_memory
- **reasoning chain:** `topical — HBM as the bandwidth bottleneck-relief technology`
- **answer entities:** `['hbm', 'hbm3e']`
- **expected chunks in corpus:** 16

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `INTC_2025_Item_1A_0012_fd8f7cd...`, `NVDA_2026_Item_1_0005_9725a5a2...`, `NVDA_2024_Item_1_0005_7f985cdb...`, `INTC_2025_Item_7_0003_878f7d25...`, `INTC_2026_Item_1A_0013_4b0422d...` |
| graph  | 0 | 0.00 | 0/5 | `INTC_2025_Item_1A_0000_ac3a3db...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `AMD_2025_Item_7_0001_223169cf...` |
| **hybrid** | **0** | **0.00** | **0/5** | `INTC_2025_Item_1A_0000_ac3a3db...`, `INTC_2025_Item_1A_0012_fd8f7cd...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2026_Item_1_0005_9725a5a2...`, `NVDA_2024_Item_1_0005_7f985cdb...` |

**Winner:** tie

---

## Q40: `How does the rise of generative AI drive demand for accelerated data center computing infrastructure?`

- **type:** topical_ai_demand
- **reasoning chain:** `topical — gen AI inflates data center capex`
- **answer entities:** `['ai', 'generative ai models', 'emergence of generative ai models', 'generative ai adoption risk', 'demand for generative ai may fluctuate']`
- **expected chunks in corpus:** 9

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `NVDA_2026_Item_1_0005_9725a5a2...`, `INTC_2025_Item_7_0003_878f7d25...`, `NVDA_2024_Item_1_0005_7f985cdb...`, `NVDA_2025_Item_1_0005_85d95b7e...`, `INTC_2026_Item_1_0004_c01224f1...` |
| graph  | 1 | 0.20 | 1/5 | `MU_2025_Item_1A_0005_edea08b6...`, `MU_2025_Item_7_0005_9a17157d...`, `MU_2025_Item_7_0002_d6b97c64...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...` |
| **hybrid** | **1** | **0.20** | **1/5** | `MU_2025_Item_1A_0005_edea08b6...`, `NVDA_2026_Item_1_0005_9725a5a2...`, `INTC_2025_Item_7_0003_878f7d25...`, `MU_2025_Item_7_0005_9a17157d...`, `MU_2025_Item_7_0002_d6b97c64...` |

**Winner:** tie

_graph hits:_ ['MU_2025_Item_1A_0005_edea08b6']

_hybrid hits:_ ['MU_2025_Item_1A_0005_edea08b6']

---

## Q41: `Which cloud hyperscalers partner with the EPYC processor maker for server CPU deployments in their data centers?`

- **type:** customer_via_product
- **reasoning chain:** `EPYC -PRODUCES-> AMD -PARTNERS_WITH-> {Microsoft, Amazon, Google, Meta}`
- **answer entities:** `['microsoft', 'amazon', 'google', 'meta']`
- **expected chunks in corpus:** 27

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `AMD_2026_Item_1_0009_ac9cc232...`, `AMD_2025_Item_1_0008_db609f8f...`, `AMD_2024_Item_1_0003_ee436d61...`, `AMD_2024_Item_1_0010_842113d9...`, `INTC_2024_Item_7_0005_d449d027...` |
| graph  | 0 | 0.00 | 0/5 | `AMD_2025_Item_7_0005_36426dd3...`, `AMD_2024_Item_7_0005_86aec648...`, `AMD_2024_Item_7_0002_d4114c99...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1_0008_db609f8f...` |
| **hybrid** | **0** | **0.00** | **0/5** | `AMD_2026_Item_1_0009_ac9cc232...`, `AMD_2025_Item_1_0008_db609f8f...`, `AMD_2025_Item_7_0005_36426dd3...`, `AMD_2024_Item_7_0005_86aec648...`, `AMD_2024_Item_1_0003_ee436d61...` |

**Winner:** tie

---

## Q42: `Which Korean conglomerate competes with the Taiwanese pure-play foundry leader in advanced node foundry services?`

- **type:** competitor_via_geo
- **reasoning chain:** `TSMC <-COMPETES_WITH- Samsung Foundry`
- **answer entities:** `['samsung electronics', 'samsung', 'samsung electronics co ltd']`
- **expected chunks in corpus:** 24

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `INTC_2025_Item_1A_0001_65932be...`, `INTC_2026_Item_1_0008_c74f560f...`, `INTC_2026_Item_1A_0001_7d38664...`, `INTC_2025_Item_7_0010_325410df...`, `INTC_2024_Item_1A_0001_f0f6c35...` |
| graph  | 1 | 1.00 | 5/5 | `NVDA_2025_Item_1_0008_a4407f7e...`, `INTC_2026_Item_1_0008_c74f560f...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `AMD_2025_Item_1_0009_c842eea0...` |
| **hybrid** | **1** | **1.00** | **5/5** | `INTC_2026_Item_1_0008_c74f560f...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `INTC_2025_Item_1A_0001_65932be...`, `INTC_2026_Item_1A_0001_7d38664...` |

**Winner:** tie

_vector hits:_ ['INTC_2024_Item_1A_0001_f0f6c35c', 'INTC_2025_Item_1A_0001_65932be2', 'INTC_2025_Item_7_0010_325410df', 'INTC_2026_Item_1A_0001_7d386648', 'INTC_2026_Item_1_0008_c74f560f']

_graph hits:_ ['AMD_2025_Item_1_0009_c842eea0', 'INTC_2026_Item_1_0008_c74f560f', 'NVDA_2024_Item_1_0007_bae70036', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

_hybrid hits:_ ['INTC_2025_Item_1A_0001_65932be2', 'INTC_2026_Item_1A_0001_7d386648', 'INTC_2026_Item_1_0008_c74f560f', 'NVDA_2025_Item_1_0008_a4407f7e', 'NVDA_2026_Item_1_0007_bf6a51b6']

---

## Q43: `Who supplies the high-bandwidth memory used in NVIDIA's H200 data center accelerator?`

- **type:** supplier_via_product
- **reasoning chain:** `H200 -PRODUCES-> NVIDIA <-SUPPLIES- {Micron, SK Hynix, Samsung}`
- **answer entities:** `['micron', 'micron technology', 'sk hynix inc', 'samsung electronics co ltd']`
- **expected chunks in corpus:** 54

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `NVDA_2024_Item_1_0002_2ddf2e3b...`, `MU_2024_Item_1_0003_acd8d0ff...`, `NVDA_2025_Item_1_0002_b74647bb...`, `MU_2024_Item_1_0001_90ffbd18...`, `MU_2025_Item_1_0001_b64486b7...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2025_Item_7_0002_b40db6b2...`, `NVDA_2026_Item_7_0001_485abbd3...`, `NVDA_2026_Item_1_0008_edf8fe4b...`, `NVDA_2025_Item_7_0001_20eaad59...`, `NVDA_2024_Item_7_0001_e54592ef...` |
| **hybrid** | **0** | **0.00** | **0/5** | `NVDA_2024_Item_1_0002_2ddf2e3b...`, `NVDA_2025_Item_7_0002_b40db6b2...`, `MU_2024_Item_1_0003_acd8d0ff...`, `NVDA_2026_Item_7_0001_485abbd3...`, `NVDA_2025_Item_1_0002_b74647bb...` |

**Winner:** vector

_vector hits:_ ['MU_2024_Item_1_0001_90ffbd18', 'MU_2025_Item_1_0001_b64486b7']

---

## Q44: `Which premium smartphone maker uses leading-edge process node chips fabricated by the Taiwanese pure-play foundry?`

- **type:** customer_via_product
- **reasoning chain:** `TSMC <-PARTNERS_WITH- Apple`
- **answer entities:** `['apple']`
- **expected chunks in corpus:** 6

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `INTC_2025_Item_1A_0001_65932be...`, `INTC_2024_Item_1A_0001_f0f6c35...`, `AMD_2024_Item_1_0012_9561038a...`, `INTC_2024_Item_1_0014_32e0816b...`, `MU_2025_Item_1_0010_ef8bd774...` |
| graph  | 0 | 0.00 | 0/5 | `AMD_2026_Item_1_0010_460dfa17...`, `NVDA_2024_Item_1_0008_20833acc...`, `AMD_2024_Item_1_0011_49024c2d...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2024_Item_1_0007_bae70036...` |
| **hybrid** | **0** | **0.00** | **0/5** | `INTC_2026_Item_1_0008_c74f560f...`, `AMD_2026_Item_1_0010_460dfa17...`, `INTC_2025_Item_1A_0001_65932be...`, `NVDA_2024_Item_1_0008_20833acc...`, `AMD_2024_Item_1_0011_49024c2d...` |

**Winner:** tie

---

## Q45: `Which process node generations define the manufacturing roadmap of the developer of Xeon Scalable processors?`

- **type:** product_via_company
- **reasoning chain:** `Xeon -PRODUCES-> Intel -PRODUCES-> {Intel 7, Intel 4, Intel 3, Intel 18A, Intel 14A}`
- **answer entities:** `['intel 4', 'intel 7', 'intel 3', 'intel 18a', 'intel 14a']`
- **expected chunks in corpus:** 27

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `INTC_2024_Item_1_0004_692d8999...`, `INTC_2024_Item_7_0005_d449d027...`, `INTC_2025_Item_1A_0005_09499ac...`, `INTC_2024_Item_7_0000_e2ea081b...`, `INTC_2025_Item_1_0007_1d4a96e6...` |
| graph  | 0 | 0.00 | 0/5 | `INTC_2026_Item_1_0011_4307b8ad...`, `INTC_2024_Item_7_0005_d449d027...`, `INTC_2024_Item_1_0004_692d8999...`, `INTC_2024_Item_7_0004_63451c7a...`, `INTC_2024_Item_7_0000_e2ea081b...` |
| **hybrid** | **0** | **0.00** | **0/5** | `INTC_2024_Item_1_0004_692d8999...`, `INTC_2024_Item_7_0005_d449d027...`, `INTC_2024_Item_7_0000_e2ea081b...`, `INTC_2025_Item_1_0007_1d4a96e6...`, `INTC_2026_Item_1_0011_4307b8ad...` |

**Winner:** tie

---

## Q46: `What data center accelerator product family drives the largest revenue segment of the CUDA platform developer?`

- **type:** product_line_via_product
- **reasoning chain:** `CUDA -PRODUCES-> NVIDIA -PRODUCES-> {H100, H200, Blackwell, GB200}`
- **answer entities:** `['h100', 'h200', 'blackwell', 'gb200', 'hopper', 'blackwell architecture', 'hgx']`
- **expected chunks in corpus:** 21

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `AMD_2025_Item_1_0003_861e4bfa...`, `NVDA_2026_Item_1_0003_0297d539...`, `NVDA_2025_Item_1_0003_ccc9ed65...`, `NVDA_2025_Item_1_0005_85d95b7e...`, `NVDA_2024_Item_1_0002_2ddf2e3b...` |
| graph  | 1 | 0.40 | 2/5 | `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0008_20833acc...`, `NVDA_2025_Item_1_0009_7a56593b...` |
| **hybrid** | **1** | **0.40** | **2/5** | `AMD_2025_Item_1_0003_861e4bfa...`, `NVDA_2024_Item_1_0007_bae70036...`, `NVDA_2025_Item_1_0008_a4407f7e...`, `NVDA_2026_Item_1_0003_0297d539...`, `NVDA_2025_Item_1_0003_ccc9ed65...` |

**Winner:** tie

_vector hits:_ ['NVDA_2025_Item_1_0003_ccc9ed65', 'NVDA_2026_Item_1_0003_0297d539']

_graph hits:_ ['NVDA_2024_Item_1_0008_20833acc', 'NVDA_2025_Item_1_0009_7a56593b']

_hybrid hits:_ ['NVDA_2025_Item_1_0003_ccc9ed65', 'NVDA_2026_Item_1_0003_0297d539']

---

## Q47: `What ARM-based server CPU competes with AMD's EPYC processors and is developed by the CUDA platform maker?`

- **type:** competitor_via_product
- **reasoning chain:** `EPYC <-COMPETES_WITH- Grace -PRODUCES-> NVIDIA`
- **answer entities:** `['grace', 'grace cpu']`
- **expected chunks in corpus:** 3

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2026_Item_1_0006_9061ffe7...`, `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2025_Item_1_0003_861e4bfa...`, `AMD_2024_Item_1_0003_ee436d61...` |
| graph  | 0 | 0.00 | 0/5 | `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2024_Item_1_0011_49024c2d...`, `AMD_2025_Item_1A_0000_ac2e47a8...`, `AMD_2025_Item_1A_0001_0fd81b24...`, `AMD_2025_Item_1_0008_db609f8f...` |
| **hybrid** | **0** | **0.00** | **0/5** | `AMD_2026_Item_1_0010_460dfa17...`, `AMD_2025_Item_1_0009_c842eea0...`, `INTC_2024_Item_7_0005_d449d027...`, `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2024_Item_1_0011_49024c2d...` |

**Winner:** tie

---

## Q48: `On which Taiwanese foundry does the GeForce graphics card vendor concentrate its wafer supply?`

- **type:** risk_via_product
- **reasoning chain:** `GeForce -PRODUCES-> NVIDIA -DEPENDS_ON-> TSMC (single-source)`
- **answer entities:** `['tsmc']`
- **expected chunks in corpus:** 32

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 0.40 | 2/5 | `MU_2024_Item_1A_0025_1809ff3b...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `AMD_2026_Item_1_0005_808c1965...`, `NVDA_2024_Item_1_0007_bae70036...`, `AMD_2025_Item_1_0010_7450880a...` |
| graph  | 1 | 0.40 | 2/5 | `NVDA_2024_Item_1A_0022_b1d57eb...`, `NVDA_2025_Item_1A_0024_d1a5b50...`, `NVDA_2026_Item_1A_0025_fb3ee78...`, `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0007_bae70036...` |
| **hybrid** | **1** | **0.40** | **2/5** | `NVDA_2026_Item_1_0007_bf6a51b6...`, `NVDA_2024_Item_1_0007_bae70036...`, `MU_2024_Item_1A_0025_1809ff3b...`, `NVDA_2024_Item_1A_0022_b1d57eb...`, `NVDA_2025_Item_1A_0024_d1a5b50...` |

**Winner:** tie

_vector hits:_ ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_1_0007_bf6a51b6']

_graph hits:_ ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_1_0007_bf6a51b6']

_hybrid hits:_ ['NVDA_2024_Item_1_0007_bae70036', 'NVDA_2026_Item_1_0007_bf6a51b6']

---

## Q49: `What U.S. export policy restricts advanced AI data center chip sales by the CUDA developer to specific foreign markets?`

- **type:** regulator_via_segment
- **reasoning chain:** `CUDA -PRODUCES-> NVIDIA -SUBJECT_TO-> EAR (DC products → China)`
- **answer entities:** `['export administration regulations', 'export controls', 'china']`
- **expected chunks in corpus:** 125

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 1 | 1.00 | 5/5 | `AMD_2025_Item_1A_0021_16aa3aa2...`, `NVDA_2025_Item_1A_0019_46eda16...`, `AMD_2026_Item_1A_0021_7fb03412...`, `NVDA_2025_Item_1A_0023_67392e5...`, `NVDA_2026_Item_1A_0024_b70c7a1...` |
| graph  | 1 | 1.00 | 5/5 | `INTC_2024_Item_1A_0009_dd11a01...`, `NVDA_2024_Item_1A_0019_ea1fd2e...`, `NVDA_2026_Item_1A_0020_331dc53...`, `NVDA_2025_Item_1A_0019_46eda16...`, `AMD_2026_Item_1A_0032_c870df0c...` |
| **hybrid** | **1** | **1.00** | **5/5** | `NVDA_2025_Item_1A_0019_46eda16...`, `NVDA_2024_Item_1A_0019_ea1fd2e...`, `NVDA_2025_Item_1A_0023_67392e5...`, `NVDA_2026_Item_1A_0020_331dc53...`, `AMD_2025_Item_1A_0021_16aa3aa2...` |

**Winner:** tie

_vector hits:_ ['AMD_2025_Item_1A_0021_16aa3aa2', 'AMD_2026_Item_1A_0021_7fb03412', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0024_b70c7a18']

_graph hits:_ ['AMD_2026_Item_1A_0032_c870df0c', 'INTC_2024_Item_1A_0009_dd11a01d', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2026_Item_1A_0020_331dc537']

_hybrid hits:_ ['AMD_2025_Item_1A_0021_16aa3aa2', 'NVDA_2024_Item_1A_0019_ea1fd2e4', 'NVDA_2025_Item_1A_0019_46eda166', 'NVDA_2025_Item_1A_0023_67392e5b', 'NVDA_2026_Item_1A_0020_331dc537']

---

## Q50: `What capital intensity challenges face leading-edge semiconductor wafer fabrication?`

- **type:** topical_capital
- **reasoning chain:** `topical — capex burden of advanced-node fabs`
- **answer entities:** `['capital expenditures']`
- **expected chunks in corpus:** 20

| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |
|---|---|---|---|---|
| vector | 0 | 0.00 | 0/5 | `INTC_2026_Item_1A_0005_46d4d92...`, `INTC_2024_Item_1A_0004_64e4feb...`, `INTC_2025_Item_1A_0004_5c93084...`, `MU_2024_Item_1_0006_6b1663cd...`, `MU_2024_Item_1A_0004_6b8d5aad...` |
| graph  | 0 | 0.00 | 0/5 | `INTC_2026_Item_7_0005_b363106d...`, `INTC_2024_Item_7_0005_d449d027...`, `AMD_2025_Item_1_0009_c842eea0...`, `AMD_2026_Item_1_0010_460dfa17...`, `INTC_2026_Item_1_0008_c74f560f...` |
| **hybrid** | **0** | **0.00** | **0/5** | `INTC_2026_Item_1A_0005_46d4d92...`, `NVDA_2024_Item_1_0008_20833acc...`, `INTC_2024_Item_1A_0004_64e4feb...`, `NVDA_2025_Item_1_0009_7a56593b...`, `INTC_2025_Item_1A_0004_5c93084...` |

**Winner:** tie

---

