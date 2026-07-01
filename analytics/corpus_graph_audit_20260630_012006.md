# Corpus Graph Audit - PPR Readiness

Generated: 2026-06-30T01:20:11
Query file: `/home/kantinan/programming/project/data/evaluate/phase_t_multihop_queries.yaml`
Details JSON: `/home/kantinan/programming/project/analytics/corpus_graph_audit_details_20260630_012006.json`

## Executive Summary

Overall readiness: **WARN**

แก่นของผลรอบนี้: graph มีโครงหลักพอให้ PPR เดินได้ แต่ยังมีสัญญาณ noise/orphan ฝั่ง entity และ benchmark entity บางตัวไม่มี node จริง ทำให้ควร audit/clean corpus ก่อนจูน No Expand PPR แบบหนัก ๆ

| Area | Result | Evidence |
|---|---|---|
| Structural health | WARN | 2347 chunks, 13549 entities, 30060 MENTIONS, orphan chunks 46 (2.0%) |
| Entity attachment | WARN | entities without chunk mentions 0 (0.0%), isolated entities 4252 (31.4%) |
| PPR walkability | PASS | informative rels 17559, avg degree 2.592, top-10 hub degree share 21.143% |
| Benchmark readiness | WARN | missing-entity queries 5/30, disconnected queries 0, gold chunks without gold-entity mention 2 |

## 1. Graph Health

### Core Counts

| Metric | Count |
|---|---:|
| nodes_total | 16064 |
| entities | 13549 |
| chunks | 2347 |
| sections | 126 |
| relationships_total | 50190 |
| mentions | 30060 |
| informative_relationships | 17559 |
| synonym_relationships | 196 |

### Relationship Distribution

| Relationship | Count |
|---|---:|
| MENTIONS | 30060 |
| NEGATIVELY_IMPACTS | 4349 |
| DISCLOSES | 2461 |
| HAS_CHUNK | 2347 |
| IMPACTED_BY | 2127 |
| PRODUCES | 2044 |
| FACES | 1842 |
| POSITIVELY_IMPACTS | 1499 |
| OPERATES_IN | 721 |
| INVOLVED_IN | 585 |
| HAS_STAKE_IN | 515 |
| SUBJECT_TO | 343 |
| DEPENDS_ON | 311 |
| INTRODUCES | 194 |
| COMPETES_WITH | 141 |
| ANNOUNCES | 129 |
| HAS_SECTION | 126 |
| INVESTS_IN | 117 |
| SYNONYM_OF | 98 |
| PARTNERS_WITH | 65 |
| CAUSES_SHORTAGE_OF | 39 |
| SUPPLIES | 35 |
| GUIDES_ON | 34 |
| LISTED_ON | 7 |
| IMPACTS | 1 |

### Orphans / Missing Properties

| Check | Count | Rate |
|---|---:|---:|
| Chunk without MENTIONS | 46 | 1.96% |
| Entity without chunk mention | 0 | 0.00% |
| Entity without informative edge | 4252 | 31.38% |
| Entity missing name | 0 | 0.00% |
| Entity missing type | 0 | 0.00% |
| Entity missing specificity | 0 | 0.00% |
| Entity missing embedding | 0 | 0.00% |
| Chunk missing chunk_id | 0 | 0.00% |
| Chunk missing text | 0 | 0.00% |
| Chunk missing embedding | 0 | 0.00% |
| Informative rel missing triple_embedding | 0 | 0.00% |

### Chunk Mention Density

| avg | p50 | p90 | p99 | max |
|---:|---:|---:|---:|---:|
| 12.808 | 11.000 | 25.000 | 40.000 | 106 |

Top broad chunks by number of mentioned entities:

| chunk_id | ticker | section | n_entities |
|---|---|---|---:|
| `KLAC_2024_Item_1A_0000_fe1b81fd` | KLAC | Item_1A | 106 |
| `KLAC_2025_Item_1A_0000_c112c626` | KLAC | Item_1A | 102 |
| `KLAC_2023_Item_1A_0000_4ec1f31e` | KLAC | Item_1A | 77 |
| `KLAC_2025_Item_1A_0002_6d29768d` | KLAC | Item_1A | 77 |
| `KLAC_2024_Item_1A_0002_f46cc9dc` | KLAC | Item_1A | 67 |
| `KLAC_2023_Item_1A_0001_ce65eb6f` | KLAC | Item_1A | 62 |
| `KLAC_2023_Item_1A_0002_349ce6e3` | KLAC | Item_1A | 60 |
| `AVGO_2023_Item_1_0010_68f5ffd4` | AVGO | Item_1 | 53 |
| `KLAC_2025_Item_1A_0001_1d5ddf3c` | KLAC | Item_1A | 52 |
| `ENTG_2025_Item_1A_0000_b352fc26` | ENTG | Item_1A | 51 |
| `KLAC_2023_Item_1_0006_11054457` | KLAC | Item_1 | 48 |
| `KLAC_2024_Item_1_0006_58dbeef6` | KLAC | Item_1 | 48 |
| `RMBS_2026_Item_7_0001_544e4d1d` | RMBS | Item_7 | 46 |
| `KLAC_2024_Item_7_0015_cec8f5c7` | KLAC | Item_7 | 44 |
| `KLAC_2023_Item_7_0016_a39e6fe6` | KLAC | Item_7 | 43 |

## 2. Entity / Relationship Quality Signals

### Generic / Suspicious Entity Names

| name | type | degree | mention_count |
|---|---|---:|---:|
| revenue | FIN_METRIC | 229 | 170 |
| ai | MACRO_CONDITION | 9 | 11 |
| demand | FIN_METRIC | 9 | 6 |
| l4 | PRODUCT | 5 | 7 |
| 5g | PRODUCT | 5 | 3 |
| competition | RISK_FACTOR | 3 | 8 |
| uk | GPE | 3 | 6 |
| ms | SEGMENT | 3 | 5 |
| 5g | MACRO_CONDITION | 3 | 4 |
| sales | FIN_METRIC | 2 | 4 |
| ec | ORG | 2 | 1 |
| ms | PRODUCT | 2 | 1 |
| eu | GPE | 1 | 6 |
| competition | MACRO_CONDITION | 1 | 2 |
| costs | FIN_METRIC | 1 | 2 |
| gf | COMP | 1 | 2 |
| 3g | PRODUCT | 1 | 1 |
| 4g | PRODUCT | 1 | 1 |
| 6g | PRODUCT | 1 | 1 |
| mc | SEGMENT | 1 | 1 |
| mc | PRODUCT | 1 | 1 |
| p3 | PRODUCT | 1 | 1 |
| ts | PRODUCT | 1 | 1 |
| semiconductors | RAW_MATERIAL | 0 | 2 |
| er | RAW_MATERIAL | 0 | 1 |
| m1 | PRODUCT | 0 | 1 |
| m2 | PRODUCT | 0 | 1 |
| nd | RAW_MATERIAL | 0 | 1 |
| pc | SEGMENT | 0 | 1 |
| services | PRODUCT | 0 | 1 |

### Self-Loops and Duplicate Pair Relations

- Self-loop informative relationships: `0`
- Entity pairs with multiple same-type informative relation instances: `1560`

### Key Entity Neighborhood Samples

#### `amd`

| rel | neighbor | neighbor_type |
|---|---|---|
| ANNOUNCES | acquisition of zt systems | EVENT |
| ANNOUNCES | product purchase agreement with openai | EVENT |
| ANNOUNCES | sale of zt manufacturing business to sanmina | EVENT |
| ANNOUNCES | warrant issued to openai | EVENT |
| ANNOUNCES | xilinx acquisition | EVENT |
| COMPETES_WITH | altera | COMP |
| COMPETES_WITH | intel | ORG |
| COMPETES_WITH | intel | ORG |
| COMPETES_WITH | nvidia | ORG |
| COMPETES_WITH | nvidia | ORG |
| COMPETES_WITH | nvidia corporation | ORG |
| DEPENDS_ON | arizona | GPE |

#### `advanced micro devices`

| rel | neighbor | neighbor_type |
|---|---|---|
| ANNOUNCES | 2014 senior notes issuance | EVENT |
| ANNOUNCES | 2019 senior notes issuance | EVENT |
| ANNOUNCES | 2020 senior notes issuance | EVENT |
| ANNOUNCES | 2022 senior notes issuance | EVENT |
| ANNOUNCES | acquisition of mipsology sas | EVENT |
| ANNOUNCES | acquisition of nod inc | EVENT |
| ANNOUNCES | acquisition of zt systems | EVENT |
| ANNOUNCES | revolving credit facility establishment | EVENT |
| ANNOUNCES | unveiling of accelerated amd instinct accelerator roadmap | EVENT |
| COMPETES_WITH | altera | COMP |
| COMPETES_WITH | analog devices | COMP |
| COMPETES_WITH | broadcom corporation | COMP |

#### `nvidia`

| rel | neighbor | neighbor_type |
|---|---|---|
| ANNOUNCES | acquisition of alphawave | EVENT |
| ANNOUNCES | common stock repurchase program approval | EVENT |
| COMPETES_WITH | advanced micro devices | ORG |
| COMPETES_WITH | advanced micro devices | ORG |
| COMPETES_WITH | alibaba group | COMP |
| COMPETES_WITH | alphabet | COMP |
| COMPETES_WITH | amazon | COMP |
| COMPETES_WITH | ambarella | COMP |
| COMPETES_WITH | amd | ORG |
| COMPETES_WITH | amd | ORG |
| COMPETES_WITH | arista networks | COMP |
| COMPETES_WITH | baidu | COMP |

#### `tsmc`

| rel | neighbor | neighbor_type |
|---|---|---|
| DEPENDS_ON | advanced micro devices | ORG |
| DEPENDS_ON | amd | ORG |
| DEPENDS_ON | applied materials | ORG |
| DEPENDS_ON | broadcom | ORG |
| DEPENDS_ON | broadcom | ORG |
| DEPENDS_ON | intel | ORG |
| DEPENDS_ON | intel | ORG |
| DEPENDS_ON | intel | ORG |
| DEPENDS_ON | intel | ORG |
| DEPENDS_ON | lam research | ORG |
| DEPENDS_ON | lam research corporation | ORG |
| DEPENDS_ON | nvidia | ORG |

#### `taiwan`

| rel | neighbor | neighbor_type |
|---|---|---|
| DEPENDS_ON | intel | ORG |
| DEPENDS_ON | micron | ORG |
| DEPENDS_ON | micron technology | ORG |
| DEPENDS_ON | nvidia | ORG |
| DEPENDS_ON | nvidia | ORG |
| DEPENDS_ON | qualcomm | ORG |
| DEPENDS_ON | qualcomm | ORG |
| DEPENDS_ON | texas instruments | ORG |
| DISCLOSES | applied materials | ORG |
| DISCLOSES | applied materials | ORG |
| DISCLOSES | lam research | ORG |
| DISCLOSES | micron technology | ORG |

#### `hbm`

| rel | neighbor | neighbor_type |
|---|---|---|
| POSITIVELY_IMPACTS | ai demand | MACRO_CONDITION |
| POSITIVELY_IMPACTS | gross margin | FIN_METRIC |
| POSITIVELY_IMPACTS | hbm advanced packaging facility groundbreaking | EVENT |
| POSITIVELY_IMPACTS | market demand | MACRO_CONDITION |
| POSITIVELY_IMPACTS | taiwan production capacity modernization | EVENT |
| PRODUCES | micron | ORG |
| PRODUCES | micron technology | ORG |

#### `hbm3e`

| rel | neighbor | neighbor_type |
|---|---|---|
| PRODUCES | micron | ORG |
| PRODUCES | micron technology | ORG |

#### `micron`

| rel | neighbor | neighbor_type |
|---|---|---|
| COMPETES_WITH | changxin memory technologies inc | COMP |
| COMPETES_WITH | cxmt | COMP |
| COMPETES_WITH | kioxia | COMP |
| COMPETES_WITH | kioxia holdings corporation | COMP |
| COMPETES_WITH | samsung electronics | COMP |
| COMPETES_WITH | samsung electronics co ltd | COMP |
| COMPETES_WITH | sandisk | COMP |
| COMPETES_WITH | sk hynix | COMP |
| COMPETES_WITH | sk hynix inc | COMP |
| COMPETES_WITH | western digital corporation | COMP |
| COMPETES_WITH | yangtze memory technologies co ltd | COMP |
| COMPETES_WITH | ymtc | COMP |

#### `blackwell`

| rel | neighbor | neighbor_type |
|---|---|---|
| POSITIVELY_IMPACTS | gaming revenue | FIN_METRIC |
| POSITIVELY_IMPACTS | professional visualization revenue | FIN_METRIC |
| PRODUCES | nvidia | ORG |
| PRODUCES | nvidia corporation | ORG |

#### `hopper`

| rel | neighbor | neighbor_type |
|---|---|---|
| PRODUCES | nvidia corporation | ORG |

#### `intel`

| rel | neighbor | neighbor_type |
|---|---|---|
| ANNOUNCES | 2022 restructuring plan | EVENT |
| ANNOUNCES | 2024 restructuring plan | EVENT |
| ANNOUNCES | 2024 restructuring plan | EVENT |
| ANNOUNCES | 2024 restructuring plan | EVENT |
| ANNOUNCES | 2024 restructuring plan | EVENT |
| ANNOUNCES | 2024 restructuring plan | EVENT |
| ANNOUNCES | 2024 restructuring plan | EVENT |
| ANNOUNCES | 2025 restructuring plan | EVENT |
| ANNOUNCES | 2025 restructuring plan | EVENT |
| ANNOUNCES | 2025 restructuring plan | EVENT |
| ANNOUNCES | accelerated funds from u.s. government | EVENT |
| ANNOUNCES | advanced packaging design wins | EVENT |

#### `intel 18a`

| rel | neighbor | neighbor_type |
|---|---|---|
| DISCLOSES | intel | ORG |
| INTRODUCES | intel | ORG |
| INVESTS_IN | intel | ORG |
| NEGATIVELY_IMPACTS | intersegment inventory reserves | FIN_METRIC |
| POSITIVELY_IMPACTS | intersegment revenue | FIN_METRIC |
| PRODUCES | intel | ORG |
| PRODUCES | intel | ORG |
| PRODUCES | intel | ORG |
| PRODUCES | intel | ORG |
| PRODUCES | intel | ORG |
| PRODUCES | intel | ORG |
| PRODUCES | intel | ORG |

#### `xeon scalable`

No exact entity node found, or no informative neighborhood.

#### `mobileye`

| rel | neighbor | neighbor_type |
|---|---|---|
| DISCLOSES | global vehicle production | MACRO_CONDITION |
| DISCLOSES | intel | ORG |
| DISCLOSES | intel | ORG |
| DISCLOSES | intel | ORG |
| DISCLOSES | intel | ORG |
| DISCLOSES | intel | ORG |
| DISCLOSES | intel | ORG |
| DISCLOSES | intel | ORG |
| DISCLOSES | operating income | FIN_METRIC |
| DISCLOSES | qualcomm | ORG |
| DISCLOSES | revenue | FIN_METRIC |
| FACES | disruption of israel fabrication facility | RISK_FACTOR |

#### `microsoft`

| rel | neighbor | neighbor_type |
|---|---|---|
| COMPETES_WITH | nvidia | ORG |
| DEPENDS_ON | advanced micro devices | ORG |
| DEPENDS_ON | amd | ORG |
| DISCLOSES | intel | ORG |
| DISCLOSES | intel | ORG |
| DISCLOSES | nvidia | ORG |
| DISCLOSES | nvidia corporation | ORG |
| IMPACTED_BY | change in control risk | RISK_FACTOR |
| IMPACTED_BY | change in control risk | RISK_FACTOR |
| IMPACTED_BY | change of control provisions | RISK_FACTOR |
| IMPACTED_BY | delaware law and change in control | RISK_FACTOR |
| IMPACTED_BY | delaware law change in control risk | RISK_FACTOR |

#### `brookfield`

| rel | neighbor | neighbor_type |
|---|---|---|
| PARTNERS_WITH | intel | ORG |

#### `apollo`

| rel | neighbor | neighbor_type |
|---|---|---|
| PARTNERS_WITH | intel | ORG |

#### `chips act`

| rel | neighbor | neighbor_type |
|---|---|---|
| DEPENDS_ON | intel | ORG |
| IMPACTED_BY | amendment to chips act funding agreements | EVENT |
| IMPACTED_BY | announcement clay fab | EVENT |
| IMPACTED_BY | announcement of advanced hbm packaging in u.s. | EVENT |
| IMPACTED_BY | announcement of clay fab | EVENT |
| IMPACTED_BY | announcement of new york memory manufacturing site | EVENT |
| IMPACTED_BY | announcement of second idaho fab | EVENT |
| IMPACTED_BY | capacity expansion risks | RISK_FACTOR |
| IMPACTED_BY | chips act award conditions | RISK_FACTOR |
| IMPACTED_BY | chips act enactment | EVENT |
| IMPACTED_BY | chips act grant applications | EVENT |
| IMPACTED_BY | chips act supply increase risk | RISK_FACTOR |

#### `export controls`

| rel | neighbor | neighbor_type |
|---|---|---|
| IMPACTED_BY | ai regulatory and compliance risks | RISK_FACTOR |
| IMPACTED_BY | changes in demand | RISK_FACTOR |
| IMPACTED_BY | china export controls licensing requirements | RISK_FACTOR |
| IMPACTED_BY | competition from larger competitors and export control disadvantages | RISK_FACTOR |
| IMPACTED_BY | dependence on international factories and trade restrictions | RISK_FACTOR |
| IMPACTED_BY | distributor dependency risk | RISK_FACTOR |
| IMPACTED_BY | export control and sanctions compliance | RISK_FACTOR |
| IMPACTED_BY | export controls and entity list restrictions affecting china sales | RISK_FACTOR |
| IMPACTED_BY | export controls and license restrictions | RISK_FACTOR |
| IMPACTED_BY | export controls compliance risk | RISK_FACTOR |
| IMPACTED_BY | export controls on ai technologies | RISK_FACTOR |
| IMPACTED_BY | impact of export controls economic sanctions and other restrictions | RISK_FACTOR |

#### `china`

| rel | neighbor | neighbor_type |
|---|---|---|
| DEPENDS_ON | advanced micro devices | ORG |
| DEPENDS_ON | intel | ORG |
| DEPENDS_ON | intel | ORG |
| DEPENDS_ON | intel | ORG |
| DEPENDS_ON | kla | ORG |
| DEPENDS_ON | lam research | ORG |
| DEPENDS_ON | nvidia | ORG |
| DEPENDS_ON | nvidia | ORG |
| DEPENDS_ON | qualcomm | ORG |
| DEPENDS_ON | qualcomm | ORG |
| DEPENDS_ON | smic | ORG |
| DEPENDS_ON | texas instruments | ORG |

#### `radeon`

| rel | neighbor | neighbor_type |
|---|---|---|
| PRODUCES | advanced micro devices | ORG |
| PRODUCES | advanced micro devices, inc. | ORG |
| PRODUCES | amd | ORG |

#### `ryzen`

| rel | neighbor | neighbor_type |
|---|---|---|
| PRODUCES | advanced micro devices | ORG |
| PRODUCES | advanced micro devices, inc. | ORG |
| PRODUCES | amd | ORG |

#### `epyc`

| rel | neighbor | neighbor_type |
|---|---|---|
| PRODUCES | advanced micro devices | ORG |
| PRODUCES | advanced micro devices, inc. | ORG |
| PRODUCES | amd | ORG |

## 3. PPR Suitability

### Informative Degree Stats

| avg | p50 | p90 | p99 | max | degree_0 | degree_1 |
|---:|---:|---:|---:|---:|---:|---:|
| 2.592 | 1.000 | 3.000 | 20.000 | 1538 | 4252 | 5076 |

### Top Hubs

| entity | type | degree | specificity |
|---|---|---:|---:|
| intel | ORG | 1538 | 0.136 |
| nvidia | ORG | 1207 | 0.141 |
| coherent | ORG | 790 | 0.150 |
| lam research | ORG | 761 | 0.151 |
| qualcomm | ORG | 613 | 0.156 |
| advanced micro devices | ORG | 599 | 0.156 |
| kla | ORG | 570 | 0.158 |
| nvidia corporation | ORG | 455 | 0.163 |
| amd | ORG | 450 | 0.164 |
| amkor | ORG | 442 | 0.164 |
| broadcom | ORG | 399 | 0.167 |
| applied materials | ORG | 338 | 0.172 |
| united states | GPE | 317 | 0.174 |
| micron technology | ORG | 307 | 0.175 |
| rambus | ORG | 305 | 0.175 |
| china | GPE | 281 | 0.177 |
| entegris | ORG | 273 | 0.178 |
| revenue | FIN_METRIC | 229 | 0.184 |
| texas instruments | ORG | 200 | 0.189 |
| gross margin | FIN_METRIC | 191 | 0.190 |
| amkor technology | ORG | 162 | 0.196 |
| micron | ORG | 157 | 0.198 |
| lam research corporation | ORG | 147 | 0.200 |
| inflation | MACRO_CONDITION | 123 | 0.207 |
| net cash provided by operating activities | FIN_METRIC | 108 | 0.213 |

### Connected Components

- Components: `4162`

| component_rank | size |
|---:|---:|
| 1 | 8347 |
| 2 | 9 |
| 3 | 7 |
| 4 | 7 |
| 5 | 6 |
| 6 | 6 |
| 7 | 6 |
| 8 | 5 |
| 9 | 5 |
| 10 | 5 |

## 4. Benchmark Gold Corpus Audit

| Metric | Value |
|---|---:|
| queries | 30 |
| queries_with_gold_chunks | 21 |
| queries_missing_entity | 5 |
| queries_missing_chunk | 0 |
| queries_disconnected | 0 |
| queries_gold_chunk_no_gold_mention | 2 |
| avg_pair_reachability | 0.982 |

### Top Missing Gold Entities

| entity | query_count |
|---|---:|
| xeon scalable | 3 |
| instinct | 1 |
| rtx | 1 |
| smart capital | 1 |

### Per Query Bottleneck

| id | type | missing_entities | missing_chunks | reachable_pairs | total_pairs | bottleneck |
|---|---|---|---|---:|---:|---|
| T001 | graph_multihop | `[]` | `[]` | 1 | 1 | CORPUS_READY_SIGNAL |
| T002 | supplier_via_product | `[]` | `[]` | 3 | 3 | CORPUS_READY_SIGNAL |
| T003 | supplier_via_product | `[]` | `[]` | 3 | 3 | GOLD_CHUNK_NO_GOLD_ENTITY_MENTION |
| T004 | competitor_product | `['instinct']` | `[]` | 1 | 1 | GOLD_ENTITY_MISSING |
| T005 | geo_via_supplier | `[]` | `[]` | 3 | 3 | CORPUS_READY_SIGNAL |
| T006 | supplier_via_company | `[]` | `[]` | 6 | 6 | CORPUS_READY_SIGNAL |
| T007 | competitor_product | `['rtx']` | `[]` | 3 | 3 | GOLD_ENTITY_MISSING |
| T008 | supplier_via_product | `[]` | `[]` | 15 | 15 | CORPUS_READY_SIGNAL |
| T009 | risk_via_product | `[]` | `[]` | 6 | 6 | CORPUS_READY_SIGNAL |
| T010 | vector_friendly | `[]` | `[]` | 3 | 3 | CORPUS_READY_SIGNAL |
| T011 | vector_friendly | `[]` | `[]` | 3 | 3 | GOLD_CHUNK_NO_GOLD_ENTITY_MENTION |
| T012 | vector_friendly | `[]` | `[]` | 3 | 3 | CORPUS_READY_SIGNAL |
| T013 | financial_exact_metric | `[]` | `[]` | 3 | 3 | CORPUS_READY_SIGNAL |
| T014 | news_recent_event | `[]` | `[]` | 0 | 0 | CORPUS_READY_SIGNAL |
| T015 | graph_multihop | `[]` | `[]` | 10 | 10 | CORPUS_READY_SIGNAL |
| T016 | off_corpus | `[]` | `[]` | 0 | 0 | CORPUS_READY_SIGNAL |
| T017 | supplier_via_company | `[]` | `[]` | 3 | 3 | CORPUS_READY_SIGNAL |
| T018 | partner_via_product | `[]` | `[]` | 10 | 10 | CORPUS_READY_SIGNAL |
| T019 | segment_via_product | `[]` | `[]` | 15 | 15 | CORPUS_READY_SIGNAL |
| T020 | regulation_via_product | `[]` | `[]` | 10 | 10 | CORPUS_READY_SIGNAL |
| T021 | supplier_via_product | `[]` | `[]` | 10 | 10 | CORPUS_READY_SIGNAL |
| T022 | partner_via_product | `['xeon scalable', 'smart capital']` | `[]` | 3 | 3 | GOLD_ENTITY_MISSING |
| T023 | subsidiary_via_product | `[]` | `[]` | 3 | 3 | CORPUS_READY_SIGNAL |
| T024 | partner_via_product | `['xeon scalable']` | `[]` | 3 | 3 | GOLD_ENTITY_MISSING |
| T025 | geo_via_product | `[]` | `[]` | 15 | 15 | CORPUS_READY_SIGNAL |
| T026 | regulator_via_product | `[]` | `[]` | 3 | 3 | CORPUS_READY_SIGNAL |
| T027 | three_hop_subsidiary_product | `['xeon scalable']` | `[]` | 10 | 10 | GOLD_ENTITY_MISSING |
| T028 | product_via_company | `[]` | `[]` | 3 | 3 | CORPUS_READY_SIGNAL |
| T029 | topical_memory | `[]` | `[]` | 5 | 6 | CORPUS_READY_SIGNAL |
| T030 | customer_via_product | `[]` | `[]` | 10 | 15 | CORPUS_READY_SIGNAL |

## 5. Decision Before No-Expand PPR Tuning

ข้อสรุปแบบตรง ๆ: **ยังจูน PPR ต่อได้ แต่ควรทำด้วย mindset ว่า corpus มี warning ไม่ใช่ perfect corpus**

ควรทำก่อนจูนหนัก:

1. เติม/normalize entity alias ที่ benchmark ใช้แต่ graph ไม่มี เช่น entity ใน missing list
2. ตรวจ broad chunks ที่ mention entity เยอะผิดปกติ เพราะ `_map_chunks` แบบ SUM(PPR mass) จะชอบ chunk กว้าง
3. เปิดดู neighborhood ของ key entities ที่ report นี้ list ไว้ แล้ว mark edge ที่ hallucinated/direction ผิด
4. สำหรับ query ที่ `GOLD_ENTITIES_DISCONNECTED` หรือ `GOLD_ENTITY_MISSING` อย่านับเป็น PPR tuning failure จนกว่าจะซ่อม corpus/gold ก่อน
5. หลัง clean corpus ให้ rerun retrieval baseline แบบ `--no-llm-expansion` เพื่อแยกผลของ corpus/PPR ออกจาก query expansion

Interpretation: ถ้า seed/entity ยังไม่มีใน graph หรือ gold entities ไม่มี path ภายใน 3 hops, PPR ไม่มีทางแก้ด้วย parameter อย่างเดียว เพราะ random walk เดินบนถนนที่ไม่มีอยู่จริง

