# Non-AMD/NVDA Corpus Graph Baseline

Generated: `2026-07-01T12:56:27`
Excluded tickers: `AMD, NVDA`
Scope tickers: `AMAT, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, QCOM, RMBS, TXN`
Details JSON: `/home/kantinan/programming/project/analytics/non_amd_nvda_corpus_baseline_20260701_125623.json`

## Scope Summary

| Metric | Value |
|---|---:|
| chunks | 1983 |
| mentions | 24918 |
| distinct_entities | 11358 |
| isolated | 3635 |
| isolated_pct | 32.0 |
| informative_rels | 14531 |
| entities_missing_embedding | 0 |
| entities_missing_specificity | 0 |
| chunks_missing_embedding | 0 |
| informative_rels_missing_triple_embedding | 0 |

## Chunk / Relation Density

| Metric | Value |
|---|---:|
| p50_mentions | 11.0 |
| p90_mentions | 25.0 |
| p95_mentions | 30.0 |
| p99_mentions | 40.0 |
| max_mentions | 48 |
| chunks_mentions_gte35 | 60 |
| chunks_mentions_gte40 | 28 |
| chunks_mentions_gt40 | 5 |
| p50_rels | 4.0 |
| p90_rels | 19.0 |
| p95_rels | 25.0 |
| p99_rels | 37.0 |
| max_rels | 67 |
| chunks_rels_gte35 | 28 |
| chunks_rels_gte40 | 9 |
| chunks_rels_gt40 | 8 |

## By Ticker

| Ticker | Chunks | Entities | Isolated | Isolated % | Mentions | Rels | Max Mentions | Max Rels | M>=40 | R>=40 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AMAT | 132 | 832 | 227 | 27.28 | 1454 | 830 | 30 | 28 | 0 | 0 |
| AMKR | 150 | 1021 | 234 | 22.92 | 1904 | 1051 | 40 | 35 | 1 | 0 |
| AVGO | 163 | 1178 | 521 | 44.23 | 2037 | 876 | 40 | 30 | 3 | 0 |
| COHR | 189 | 1287 | 347 | 26.96 | 2263 | 1374 | 40 | 39 | 2 | 0 |
| ENTG | 176 | 1189 | 399 | 33.56 | 2318 | 955 | 40 | 36 | 1 | 0 |
| INTC | 214 | 1413 | 151 | 10.69 | 2694 | 2235 | 35 | 41 | 0 | 1 |
| KLAC | 202 | 2219 | 708 | 31.91 | 3826 | 2202 | 48 | 67 | 15 | 6 |
| LRCX | 144 | 688 | 52 | 7.56 | 1412 | 1203 | 40 | 33 | 1 | 0 |
| MU | 164 | 1281 | 359 | 28.02 | 2323 | 1246 | 40 | 50 | 2 | 1 |
| QCOM | 202 | 959 | 237 | 24.71 | 1765 | 1153 | 30 | 38 | 0 | 0 |
| RMBS | 185 | 1258 | 464 | 36.88 | 2380 | 1054 | 43 | 42 | 3 | 1 |
| TXN | 62 | 274 | 37 | 13.5 | 542 | 352 | 27 | 23 | 0 | 0 |

## Worst Filings By Isolated %

| Ticker | FY | Chunks | Entities | Isolated | Isolated % | Mentions | Rels |
|---|---:|---:|---:|---:|---:|---:|---:|
| AVGO | 2023 | 57 | 521 | 211 | 40.5 | 672 | 275 |
| AVGO | 2024 | 54 | 558 | 223 | 39.96 | 716 | 302 |
| AVGO | 2025 | 52 | 512 | 184 | 35.94 | 649 | 299 |
| RMBS | 2026 | 61 | 745 | 233 | 31.28 | 991 | 531 |
| ENTG | 2025 | 57 | 585 | 183 | 31.28 | 777 | 255 |
| RMBS | 2024 | 64 | 521 | 162 | 31.09 | 693 | 268 |
| MU | 2024 | 54 | 523 | 160 | 30.59 | 677 | 285 |
| RMBS | 2025 | 60 | 501 | 153 | 30.54 | 696 | 255 |
| COHR | 2023 | 65 | 638 | 187 | 29.31 | 822 | 460 |
| ENTG | 2024 | 62 | 557 | 163 | 29.26 | 794 | 340 |
| KLAC | 2023 | 69 | 1034 | 293 | 28.34 | 1269 | 670 |
| KLAC | 2024 | 69 | 1023 | 277 | 27.08 | 1243 | 691 |
| AMAT | 2024 | 44 | 355 | 92 | 25.92 | 467 | 222 |
| ENTG | 2026 | 57 | 558 | 141 | 25.27 | 747 | 360 |
| AMAT | 2023 | 47 | 426 | 103 | 24.18 | 574 | 363 |

## Isolated By Type

| Type | Total | Isolated | Isolated % |
|---|---:|---:|---:|
| RISK_FACTOR | 4222 | 1952 | 46.23 |
| FIN_METRIC | 1447 | 365 | 25.22 |
| PRODUCT | 1420 | 321 | 22.61 |
| ORG | 361 | 180 | 49.86 |
| ACCOUNTING_POLICY | 304 | 170 | 55.92 |
| EVENT | 1348 | 151 | 11.2 |
| MACRO_CONDITION | 903 | 123 | 13.62 |
| COMP | 219 | 106 | 48.4 |
| SEGMENT | 333 | 84 | 25.23 |
| GPE | 209 | 70 | 33.49 |
| RAW_MATERIAL | 175 | 64 | 36.57 |
| REGULATORY_REQUIREMENT | 405 | 43 | 10.62 |
| ESG_TOPIC | 10 | 6 | 60.0 |
| FIN_MARKET | 2 | 0 | 0.0 |

## Item 1A Schema Signal

| Ticker | FY | Chunks | Risk Mentions | Product | Segment | Fin Metric | Risk Bridge Edges |
|---|---:|---:|---:|---:|---:|---:|---:|
| AMAT | 2023 | 20 | 164 | 0 | 0 | 0 | 0 |
| AMAT | 2024 | 23 | 157 | 0 | 0 | 0 | 0 |
| AMAT | 2025 | 21 | 103 | 0 | 0 | 0 | 0 |
| AMKR | 2024 | 23 | 159 | 0 | 0 | 0 | 0 |
| AMKR | 2025 | 22 | 161 | 0 | 0 | 0 | 0 |
| AMKR | 2026 | 24 | 169 | 0 | 0 | 0 | 0 |
| AVGO | 2023 | 29 | 169 | 0 | 0 | 0 | 0 |
| AVGO | 2024 | 24 | 148 | 0 | 0 | 0 | 0 |
| AVGO | 2025 | 26 | 160 | 0 | 0 | 0 | 0 |
| COHR | 2023 | 29 | 113 | 0 | 0 | 0 | 0 |
| COHR | 2024 | 34 | 113 | 0 | 0 | 0 | 0 |
| COHR | 2025 | 26 | 107 | 0 | 0 | 0 | 0 |
| ENTG | 2024 | 22 | 93 | 0 | 0 | 0 | 0 |
| ENTG | 2025 | 22 | 134 | 0 | 0 | 0 | 0 |
| ENTG | 2026 | 26 | 169 | 0 | 0 | 0 | 0 |
| INTC | 2024 | 28 | 116 | 0 | 0 | 0 | 0 |
| INTC | 2025 | 28 | 124 | 0 | 0 | 0 | 0 |
| INTC | 2026 | 26 | 104 | 0 | 0 | 0 | 0 |
| KLAC | 2023 | 30 | 360 | 0 | 0 | 0 | 0 |
| KLAC | 2024 | 35 | 412 | 0 | 0 | 0 | 0 |
| KLAC | 2025 | 34 | 395 | 0 | 0 | 0 | 0 |
| LRCX | 2023 | 21 | 86 | 0 | 0 | 0 | 0 |
| LRCX | 2024 | 23 | 89 | 0 | 0 | 0 | 0 |
| LRCX | 2025 | 24 | 100 | 0 | 0 | 0 | 0 |
| MU | 2023 | 23 | 198 | 0 | 0 | 0 | 0 |
| MU | 2024 | 27 | 182 | 0 | 0 | 0 | 0 |
| MU | 2025 | 31 | 176 | 0 | 0 | 0 | 0 |
| QCOM | 2023 | 35 | 133 | 0 | 0 | 0 | 0 |
| QCOM | 2024 | 37 | 138 | 0 | 0 | 0 | 0 |
| QCOM | 2025 | 38 | 169 | 0 | 0 | 0 | 0 |
| RMBS | 2024 | 34 | 167 | 0 | 0 | 0 | 0 |
| RMBS | 2025 | 33 | 181 | 0 | 0 | 0 | 0 |
| RMBS | 2026 | 35 | 315 | 0 | 0 | 0 | 0 |
| TXN | 2024 | 9 | 31 | 0 | 0 | 0 | 0 |
| TXN | 2025 | 9 | 34 | 0 | 0 | 0 | 0 |
| TXN | 2026 | 9 | 29 | 0 | 0 | 0 | 0 |

## Dense / Cap-Risk Chunks

| Chunk | Ticker | FY | Section | Mentions | Rels |
|---|---|---:|---|---:|---:|
| `KLAC_2023_Item_1_0006_11054457` | KLAC | 2023 | Item_1 | 48 | 47 |
| `KLAC_2024_Item_1_0006_58dbeef6` | KLAC | 2024 | Item_1 | 48 | 47 |
| `RMBS_2026_Item_1_0001_bc3d8a01` | RMBS | 2026 | Item_1 | 43 | 42 |
| `KLAC_2024_Item_1_0005_f2fc0653` | KLAC | 2024 | Item_1 | 42 | 67 |
| `KLAC_2025_Item_1A_0002_6d29768d` | KLAC | 2025 | Item_1A | 41 | 40 |
| `KLAC_2025_Item_1A_0006_7aa995a7` | KLAC | 2025 | Item_1A | 40 | 54 |
| `COHR_2024_Item_1_0002_29277790` | COHR | 2024 | Item_1 | 40 | 39 |
| `MU_2023_Item_7_0007_812b0ead` | MU | 2023 | Item_7 | 40 | 34 |
| `LRCX_2024_Item_1A_0005_11e69e9e` | LRCX | 2024 | Item_1A | 40 | 33 |
| `KLAC_2023_Item_1A_0002_349ce6e3` | KLAC | 2023 | Item_1A | 40 | 32 |
| `RMBS_2026_Item_7_0001_544e4d1d` | RMBS | 2026 | Item_7 | 40 | 31 |
| `KLAC_2023_Item_7_0016_a39e6fe6` | KLAC | 2023 | Item_7 | 40 | 30 |
| `KLAC_2023_Item_1A_0001_ce65eb6f` | KLAC | 2023 | Item_1A | 40 | 28 |
| `KLAC_2024_Item_1A_0002_f46cc9dc` | KLAC | 2024 | Item_1A | 40 | 26 |
| `KLAC_2024_Item_1A_0000_fe1b81fd` | KLAC | 2024 | Item_1A | 40 | 23 |
| `KLAC_2025_Item_1A_0000_c112c626` | KLAC | 2025 | Item_1A | 40 | 23 |
| `ENTG_2025_Item_1A_0000_b352fc26` | ENTG | 2025 | Item_1A | 40 | 19 |
| `KLAC_2023_Item_1A_0000_4ec1f31e` | KLAC | 2023 | Item_1A | 40 | 19 |
| `KLAC_2024_Item_7_0015_cec8f5c7` | KLAC | 2024 | Item_7 | 40 | 15 |
| `KLAC_2025_Item_1A_0001_1d5ddf3c` | KLAC | 2025 | Item_1A | 40 | 13 |
| `COHR_2023_Item_1_0014_7a4d6843` | COHR | 2023 | Item_1 | 40 | 12 |
| `AMKR_2025_Item_1A_0003_a68b7182` | AMKR | 2025 | Item_1A | 40 | 10 |
| `RMBS_2026_Item_1A_0000_4ada9712` | RMBS | 2026 | Item_1A | 40 | 5 |
| `AVGO_2024_Item_1A_0001_2912e409` | AVGO | 2024 | Item_1A | 40 | 3 |
| `MU_2023_Item_1A_0000_426cfeaa` | MU | 2023 | Item_1A | 40 | 1 |
| `AVGO_2023_Item_1_0010_68f5ffd4` | AVGO | 2023 | Item_1 | 40 | 0 |
| `AVGO_2024_Item_1_0012_88739b41` | AVGO | 2024 | Item_1 | 40 | 0 |
| `KLAC_2023_Item_1_0005_ec4a6eeb` | KLAC | 2023 | Item_1 | 40 | 0 |
| `COHR_2025_Item_1_0003_5bd035b4` | COHR | 2025 | Item_1 | 39 | 37 |
| `AMKR_2026_Item_1A_0003_a2e1fdfd` | AMKR | 2026 | Item_1A | 39 | 35 |
| `RMBS_2024_Item_7_0001_274d79f5` | RMBS | 2024 | Item_7 | 39 | 32 |
| `RMBS_2026_Item_1A_0012_fc15d907` | RMBS | 2026 | Item_1A | 39 | 27 |
| `KLAC_2025_Item_7_0010_59f65799` | KLAC | 2025 | Item_7 | 39 | 25 |
| `RMBS_2025_Item_1_0001_479b0c1e` | RMBS | 2025 | Item_1 | 39 | 13 |
| `ENTG_2026_Item_1A_0000_8e7f7fe6` | ENTG | 2026 | Item_1A | 39 | 9 |
| `KLAC_2024_Item_1A_0018_02110cff` | KLAC | 2024 | Item_1A | 39 | 4 |
| `KLAC_2023_Item_7_0007_3e68a30e` | KLAC | 2023 | Item_7 | 39 | 0 |
| `KLAC_2025_Item_1A_0004_8b3ac9dd` | KLAC | 2025 | Item_1A | 38 | 38 |
| `RMBS_2026_Item_1A_0022_ffcb3e7f` | RMBS | 2026 | Item_1A | 38 | 25 |
| `ENTG_2024_Item_1A_0003_5fc9814b` | ENTG | 2024 | Item_1A | 38 | 16 |
| `ENTG_2025_Item_7_0001_3a9ac738` | ENTG | 2025 | Item_7 | 38 | 2 |
| `KLAC_2024_Item_1A_0013_2d62bad9` | KLAC | 2024 | Item_1A | 38 | 2 |
| `KLAC_2025_Item_7_0004_2efd7f3b` | KLAC | 2025 | Item_7 | 37 | 38 |
| `KLAC_2025_Item_1_0006_1266d968` | KLAC | 2025 | Item_1 | 37 | 36 |
| `KLAC_2024_Item_1A_0006_561ebde5` | KLAC | 2024 | Item_1A | 37 | 26 |
| `KLAC_2023_Item_7_0014_b049560e` | KLAC | 2023 | Item_7 | 37 | 23 |
| `MU_2023_Item_7_0002_c0fab91a` | MU | 2023 | Item_7 | 36 | 38 |
| `KLAC_2024_Item_1A_0014_7ec8fd84` | KLAC | 2024 | Item_1A | 36 | 36 |
| `AVGO_2024_Item_1A_0010_1319c01d` | AVGO | 2024 | Item_1A | 36 | 30 |
| `AVGO_2025_Item_7_0010_b0cadb20` | AVGO | 2025 | Item_7 | 36 | 25 |
| `KLAC_2023_Item_1A_0015_4b24f876` | KLAC | 2023 | Item_1A | 36 | 15 |
| `KLAC_2023_Item_7_0013_293f577a` | KLAC | 2023 | Item_7 | 36 | 15 |
| `KLAC_2025_Item_1A_0013_028844f8` | KLAC | 2025 | Item_1A | 35 | 39 |
| `KLAC_2023_Item_7_0015_ac9caa87` | KLAC | 2023 | Item_7 | 35 | 29 |
| `KLAC_2025_Item_7_0007_ac4e023a` | KLAC | 2025 | Item_7 | 35 | 27 |
| `INTC_2024_Item_7_0009_2d5f3afe` | INTC | 2024 | Item_7 | 35 | 24 |
| `MU_2023_Item_1A_0003_92be33e3` | MU | 2023 | Item_1A | 35 | 20 |
| `KLAC_2025_Item_7_0014_d593e781` | KLAC | 2025 | Item_7 | 35 | 14 |
| `AVGO_2024_Item_1_0001_e8632ebb` | AVGO | 2024 | Item_1 | 35 | 0 |
| `AVGO_2025_Item_7_0006_878eca08` | AVGO | 2025 | Item_7 | 35 | 0 |
| `MU_2023_Item_7_0003_2574b2e1` | MU | 2023 | Item_7 | 33 | 50 |
| `INTC_2024_Item_7_0012_b8db0489` | INTC | 2024 | Item_7 | 33 | 35 |
| `MU_2023_Item_7_0004_abbaac03` | MU | 2023 | Item_7 | 32 | 35 |
| `INTC_2025_Item_7_0007_d11026fc` | INTC | 2025 | Item_7 | 31 | 39 |
| `KLAC_2023_Item_1A_0011_63d83463` | KLAC | 2023 | Item_1A | 31 | 38 |
| `KLAC_2025_Item_1A_0016_e7a6c3d1` | KLAC | 2025 | Item_1A | 30 | 43 |
| `INTC_2025_Item_7_0000_d16d1424` | INTC | 2025 | Item_7 | 30 | 41 |
| `QCOM_2025_Item_7_0004_88c32f0a` | QCOM | 2025 | Item_7 | 30 | 37 |
| `ENTG_2024_Item_7_0018_b0a46a7f` | ENTG | 2024 | Item_7 | 27 | 36 |
| `INTC_2026_Item_7_0005_b363106d` | INTC | 2026 | Item_7 | 26 | 38 |
| `QCOM_2023_Item_7_0001_89cb7e39` | QCOM | 2023 | Item_7 | 26 | 38 |
| `QCOM_2025_Item_7_0003_e17edcd4` | QCOM | 2025 | Item_7 | 24 | 37 |
| `INTC_2024_Item_7_0025_0cdc7b7c` | INTC | 2024 | Item_7 | 23 | 39 |

