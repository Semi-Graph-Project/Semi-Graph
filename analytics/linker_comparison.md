# Linker Comparison Report — Query-to-Node vs Query-to-Triple

**Method:** 12-query suite × 2 linker modes, proxy metrics (no ground truth)  
**Reference:** HippoRAG v2 (ICML '25) Table 4 — Query-to-Triple +12.5% R@5 over Query-to-Node  
**PPR top-k:** 10, damping=0.85, max_iter=20  
**Linker defaults:** both use top_k=5, min_similarity=0.6  

Higher-is-better: `seed_type_diversity`, `multi_hop_pct`, `type_entropy`  
Lower-is-better: `hub_leakage`, `top3_concentration`

---

## Query: `AMD`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | amd *(ORG)* | amd *(ORG)* |
| 2 | amd ryzen *(PRODUCT)* | radeon *(PRODUCT)* |
| 3 | amd athlon *(PRODUCT)* | united states *(GPE)* |
| 4 | amd instinct *(PRODUCT)* | advanced micro devices *(ORG)* |
| 5 | amd pensando *(PRODUCT)* | amd versal *(PRODUCT)* |
| 6 |  | microsoft *(COMP)* |
| 7 |  | amd athlon *(PRODUCT)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | amd *(ORG)* `1.064` | advanced micro devices *(ORG)* `1.097` |
| 2 | advanced micro devices *(ORG)* `0.655` | amd *(ORG)* `0.826` |
| 3 | amd instinct *(PRODUCT)* `0.156` | nvidia *(ORG)* `0.238` |
| 4 | amd ryzen *(PRODUCT)* `0.153` | united states *(GPE)* `0.214` |
| 5 | amd athlon *(PRODUCT)* `0.153` | microsoft *(COMP)* `0.194` |
| 6 | amd pensando *(PRODUCT)* `0.152` | nvidia corporation *(ORG)* `0.169` |
| 7 | advanced micro devices, inc. *(ORG)* `0.097` | radeon *(PRODUCT)* `0.156` |
| 8 | nvidia *(ORG)* `0.087` | amd athlon *(PRODUCT)* `0.153` |
| 9 | nvidia corporation *(ORG)* `0.059` | amd versal *(PRODUCT)* `0.152` |
| 10 | gross margin *(FIN_METRIC)* `0.023` | advanced micro devices, inc. *(ORG)* `0.100` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 7 | — |
| seed_type_diversity | 2 | 4 | 🟢 Triple |
| multi_hop_pct | 0.500 | 0.300 | 🔵 Node |
| hub_leakage | 0.009 | 0.065 | 🔵 Node |
| type_entropy | 1.361 | 1.685 | 🟢 Triple |
| top3_concentration | 0.721 | 0.655 | 🟢 Triple |

---

## Query: `TSMC supply chain`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | tsmc *(COMP)* | tsmc *(COMP)* |
| 2 | tsmc supply dependency *(RISK_FACTOR)* | advanced micro devices *(ORG)* |
| 3 | tsmc manufacturing dependency *(RISK_FACTOR)* | tsmc_supply_dependency *(RISK_FACTOR)* |
| 4 | tsmc_supply_dependency *(RISK_FACTOR)* | nvidia corporation *(ORG)* |
| 5 | outsourcing supply chain logistics *(RISK_FACTOR)* | nvidia *(ORG)* |
| 6 |  | tsmc 7nm supply constraint *(RISK_FACTOR)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | advanced micro devices *(ORG)* `0.979` | nvidia *(ORG)* `0.610` |
| 2 | tsmc *(COMP)* `0.268` | advanced micro devices *(ORG)* `0.582` |
| 3 | amd *(ORG)* `0.261` | nvidia corporation *(ORG)* `0.570` |
| 4 | nvidia *(ORG)* `0.190` | tsmc *(COMP)* `0.416` |
| 5 | tsmc_supply_dependency *(RISK_FACTOR)* `0.187` | amd *(ORG)* `0.231` |
| 6 | the_filer *(ORG)* `0.182` | the_filer *(ORG)* `0.215` |
| 7 | nvidia corporation *(ORG)* `0.162` | tsmc_supply_dependency *(RISK_FACTOR)* `0.202` |
| 8 | outsourcing supply chain logistics *(RISK_FACTOR)* `0.152` | tsmc 7nm supply constraint *(RISK_FACTOR)* `0.185` |
| 9 | tsmc supply dependency *(RISK_FACTOR)* `0.152` | currency_exchange_rate_fluctuations *(RISK_FACTOR)* `0.046` |
| 10 | tsmc manufacturing dependency *(RISK_FACTOR)* `0.152` | us_dollar_appreciation *(MACRO_CONDITION)* `0.030` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 6 | — |
| seed_type_diversity | 2 | 3 | 🟢 Triple |
| multi_hop_pct | 0.500 | 0.400 | 🔵 Node |
| hub_leakage | 0.068 | 0.070 | 🔵 Node |
| type_entropy | 1.361 | 1.685 | 🟢 Triple |
| top3_concentration | 0.562 | 0.571 | 🔵 Node |

---

## Query: `Compare R&D Alphabet vs Meta 2023`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | r&d *(FIN_METRIC)* | competition and technological change *(RISK_FACTOR)* |
| 2 | product specification decisions years in advance *(RISK_FACTOR)* | product roadmap execution *(RISK_FACTOR)* |
| 3 | 2023 restructure plan *(EVENT)* | micron technology *(ORG)* |
| 4 | product incompatibility with industry standards *(RISK_FACTOR)* | 2023 restructure plan *(EVENT)* |
| 5 | competitive pressures on r&d spending *(RISK_FACTOR)* | advanced micro devices *(ORG)* |
| 6 |  | analog devices *(COMP)* |
| 7 |  | third-party intellectual property dependency *(RISK_FACTOR)* |
| 8 |  | ability to introduce new products timely *(RISK_FACTOR)* |
| 9 |  | altera *(COMP)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | product specification decisions years in advance *(RISK_FACTOR)* `0.520` | advanced micro devices *(ORG)* `1.321` |
| 2 | reliance on customer demand forecasts *(RISK_FACTOR)* `0.442` | product roadmap execution *(RISK_FACTOR)* `0.651` |
| 3 | micron technology *(ORG)* `0.438` | micron technology *(ORG)* `0.496` |
| 4 | nvidia corporation *(ORG)* `0.286` | third-party intellectual property dependency *(RISK_FACTOR)* `0.438` |
| 5 | 2023 restructure plan *(EVENT)* `0.211` | amd *(ORG)* `0.399` |
| 6 | r&d *(FIN_METRIC)* `0.151` | ability to introduce new products timely *(RISK_FACTOR)* `0.336` |
| 7 | product incompatibility with industry standards *(RISK_FACTOR)* `0.151` | competition and technological change *(RISK_FACTOR)* `0.288` |
| 8 | competitive pressures on r&d spending *(RISK_FACTOR)* `0.150` | 2023 restructure plan *(EVENT)* `0.212` |
| 9 | nvidia *(ORG)* `0.087` | competitive positioning *(RISK_FACTOR)* `0.190` |
| 10 | micron *(ORG)* `0.051` | altera *(COMP)* `0.153` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 9 | — |
| seed_type_diversity | 3 | 4 | 🟢 Triple |
| multi_hop_pct | 0.500 | 0.200 | 🔵 Node |
| hub_leakage | 0.000 | 0.000 | tie |
| type_entropy | 1.722 | 1.685 | 🔵 Node |
| top3_concentration | 0.563 | 0.550 | 🟢 Triple |

---

## Query: `china semiconductor ban`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | cac ban on micron products in china *(RISK_FACTOR)* | restrictions on materials in electronic products *(RISK_FACTOR)* |
| 2 | new us export restrictions on semiconductors to china *(EVENT)* | china *(GPE)* |
| 3 | chinese restrictions on micron products *(EVENT)* | micron technology *(ORG)* |
| 4 | cac ban on micron products *(EVENT)* | cac ban on micron products in china *(RISK_FACTOR)* |
| 5 | china restrictions on lead and other materials *(REGULATORY_REQUIREMENT)* | cac cybersecurity review decision *(EVENT)* |
| 6 |  | export controls on ai semiconductors *(RISK_FACTOR)* |
| 7 |  | chinese restrictions on micron products *(EVENT)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | micron *(ORG)* `0.530` | micron technology *(ORG)* `0.677` |
| 2 | amd *(ORG)* `0.260` | china *(GPE)* `0.449` |
| 3 | micron technology *(ORG)* `0.254` | micron *(ORG)* `0.428` |
| 4 | china restrictions on lead and other materials *(REGULATORY_REQUIREMENT)* `0.240` | nvidia *(ORG)* `0.341` |
| 5 | new us export restrictions on semiconductors to china *(EVENT)* `0.184` | restrictions on materials in electronic products *(RISK_FACTOR)* `0.249` |
| 6 | cac ban on micron products in china *(RISK_FACTOR)* `0.165` | cac cybersecurity review decision *(EVENT)* `0.224` |
| 7 | cac ban on micron products *(EVENT)* `0.156` | export controls on ai semiconductors *(RISK_FACTOR)* `0.216` |
| 8 | chinese restrictions on micron products *(EVENT)* `0.155` | cac ban on micron products in china *(RISK_FACTOR)* `0.185` |
| 9 | china *(GPE)* `0.154` | nvidia corporation *(ORG)* `0.164` |
| 10 | lead material restrictions risk *(RISK_FACTOR)* `0.144` | chinese restrictions on micron products *(EVENT)* `0.158` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 7 | — |
| seed_type_diversity | 3 | 4 | 🟢 Triple |
| multi_hop_pct | 0.500 | 0.300 | 🔵 Node |
| hub_leakage | 0.069 | 0.145 | 🔵 Node |
| type_entropy | 2.171 | 1.846 | 🔵 Node |
| top3_concentration | 0.466 | 0.503 | 🔵 Node |

---

## Query: `NVIDIA Blackwell GPU architecture`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | blackwell gpus *(PRODUCT)* | nvidia *(ORG)* |
| 2 | blackwell architectures *(PRODUCT)* | blackwell architecture *(PRODUCT)* |
| 3 | introduction of nvidia rtx ada lovelace architecture gpus *(EVENT)* | nvidia corporation *(ORG)* |
| 4 | gpu accelerators *(PRODUCT)* | blackwell architectures *(PRODUCT)* |
| 5 | nvidia *(ORG)* | blackwell gpus *(PRODUCT)* |
| 6 |  | blackwell *(PRODUCT)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | nvidia corporation *(ORG)* `0.858` | nvidia corporation *(ORG)* `1.178` |
| 2 | nvidia *(ORG)* `0.501` | nvidia *(ORG)* `0.755` |
| 3 | amd *(ORG)* `0.317` | blackwell architecture *(PRODUCT)* `0.178` |
| 4 | blackwell gpus *(PRODUCT)* `0.152` | blackwell *(PRODUCT)* `0.174` |
| 5 | blackwell architectures *(PRODUCT)* `0.152` | blackwell gpus *(PRODUCT)* `0.152` |
| 6 | introduction of nvidia rtx ada lovelace architecture gpus *(EVENT)* `0.152` | blackwell architectures *(PRODUCT)* `0.152` |
| 7 | gpu accelerators *(PRODUCT)* `0.151` | advanced micro devices *(ORG)* `0.101` |
| 8 | advanced micro devices *(ORG)* `0.137` | amd *(ORG)* `0.068` |
| 9 | micron technology *(ORG)* `0.028` | graphics revenue *(FIN_METRIC)* `0.058` |
| 10 | china *(GPE)* `0.025` | professional visualization revenue *(FIN_METRIC)* `0.045` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 6 | — |
| seed_type_diversity | 3 | 2 | 🔵 Node |
| multi_hop_pct | 0.500 | 0.400 | 🔵 Node |
| hub_leakage | 0.010 | 0.000 | 🟢 Triple |
| type_entropy | 1.685 | 1.522 | 🔵 Node |
| top3_concentration | 0.678 | 0.738 | 🔵 Node |

---

## Query: `Hopper data center segment revenue`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | data center revenue *(FIN_METRIC)* | hopper computing platform *(PRODUCT)* |
| 2 | compute & networking segment revenue *(FIN_METRIC)* | revenue *(FIN_METRIC)* |
| 3 | compute & networking revenue *(FIN_METRIC)* | hopper architecture *(PRODUCT)* |
| 4 | data center segment *(SEGMENT)* | data center segment *(SEGMENT)* |
| 5 | compute & networking segment operating income *(FIN_METRIC)* | data center *(SEGMENT)* |
| 6 |  | data center revenue *(FIN_METRIC)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | nvidia corporation *(ORG)* `0.546` | nvidia *(ORG)* `0.522` |
| 2 | nvidia *(ORG)* `0.379` | revenue *(FIN_METRIC)* `0.520` |
| 3 | compute & networking revenue *(FIN_METRIC)* `0.266` | advanced micro devices *(ORG)* `0.357` |
| 4 | compute & networking segment operating income *(FIN_METRIC)* `0.258` | nvidia corporation *(ORG)* `0.323` |
| 5 | compute & networking segment revenue *(FIN_METRIC)* `0.224` | amd *(ORG)* `0.315` |
| 6 | advanced micro devices *(ORG)* `0.193` | data center *(SEGMENT)* `0.299` |
| 7 | amd *(ORG)* `0.169` | gross margin *(FIN_METRIC)* `0.188` |
| 8 | data center revenue *(FIN_METRIC)* `0.167` | data center segment *(SEGMENT)* `0.177` |
| 9 | data center segment *(SEGMENT)* `0.166` | data center revenue *(FIN_METRIC)* `0.176` |
| 10 | h20 excess inventory and purchase obligations charge *(EVENT)* `0.098` | hopper architecture *(PRODUCT)* `0.167` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 6 | — |
| seed_type_diversity | 2 | 3 | 🟢 Triple |
| multi_hop_pct | 0.500 | 0.500 | tie |
| hub_leakage | 0.000 | 0.232 | 🔵 Node |
| type_entropy | 1.722 | 1.846 | 🟢 Triple |
| top3_concentration | 0.483 | 0.460 | 🟢 Triple |

---

## Query: `Micron HBM memory products`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | dram products *(PRODUCT)* | micron technology *(ORG)* |
| 2 | advanced hbm packaging *(PRODUCT)* | hbm *(PRODUCT)* |
| 3 | memory and storage products *(PRODUCT)* | advanced hbm packaging *(PRODUCT)* |
| 4 | micron technology *(ORG)* | micron *(ORG)* |
| 5 | micron technology inc *(ORG)* | memory and storage products *(PRODUCT)* |
| 6 |  | memory modules *(PRODUCT)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | micron technology *(ORG)* `0.758` | micron technology *(ORG)* `1.103` |
| 2 | micron *(ORG)* `0.377` | micron *(ORG)* `0.747` |
| 3 | micron technology inc *(ORG)* `0.279` | hbm *(PRODUCT)* `0.210` |
| 4 | dram products *(PRODUCT)* `0.156` | memory and storage products *(PRODUCT)* `0.154` |
| 5 | memory and storage products *(PRODUCT)* `0.152` | memory modules *(PRODUCT)* `0.153` |
| 6 | advanced hbm packaging *(PRODUCT)* `0.152` | advanced hbm packaging *(PRODUCT)* `0.153` |
| 7 | nvidia corporation *(ORG)* `0.124` | nvidia *(ORG)* `0.089` |
| 8 | nvidia *(ORG)* `0.090` | nvidia corporation *(ORG)* `0.058` |
| 9 | bit shipments *(FIN_METRIC)* `0.076` | dram *(PRODUCT)* `0.050` |
| 10 | revenue *(FIN_METRIC)* `0.066` | gross margin *(FIN_METRIC)* `0.045` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 6 | — |
| seed_type_diversity | 2 | 2 | tie |
| multi_hop_pct | 0.500 | 0.400 | 🔵 Node |
| hub_leakage | 0.029 | 0.016 | 🟢 Triple |
| type_entropy | 1.485 | 1.361 | 🔵 Node |
| top3_concentration | 0.635 | 0.746 | 🔵 Node |

---

## Query: `Micron bit shipments average selling price`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | bit shipments *(FIN_METRIC)* | micron technology *(ORG)* |
| 2 | average selling price *(FIN_METRIC)* | average selling price *(FIN_METRIC)* |
| 3 | average selling prices *(FIN_METRIC)* | average selling prices *(FIN_METRIC)* |
| 4 | dram average selling price *(FIN_METRIC)* | bit shipments *(FIN_METRIC)* |
| 5 | dram bit shipments *(FIN_METRIC)* | selling prices *(FIN_METRIC)* |
| 6 |  | bit shipment *(FIN_METRIC)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | bit shipments *(FIN_METRIC)* `0.402` | micron technology *(ORG)* `0.940` |
| 2 | average selling prices *(FIN_METRIC)* `0.261` | bit shipments *(FIN_METRIC)* `0.351` |
| 3 | dram average selling price *(FIN_METRIC)* `0.260` | average selling prices *(FIN_METRIC)* `0.257` |
| 4 | average selling price *(FIN_METRIC)* `0.259` | average selling price *(FIN_METRIC)* `0.251` |
| 5 | dram bit shipments *(FIN_METRIC)* `0.208` | selling prices *(FIN_METRIC)* `0.239` |
| 6 | micron technology *(ORG)* `0.176` | bit shipment *(FIN_METRIC)* `0.153` |
| 7 | ai demand *(MACRO_CONDITION)* `0.115` | micron *(ORG)* `0.115` |
| 8 | aebu *(SEGMENT)* `0.109` | cash from operations *(FIN_METRIC)* `0.102` |
| 9 | mcb u *(SEGMENT)* `0.108` | cnbu operating income *(FIN_METRIC)* `0.081` |
| 10 | micron *(ORG)* `0.105` | nvidia *(ORG)* `0.079` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 6 | — |
| seed_type_diversity | 1 | 2 | 🟢 Triple |
| multi_hop_pct | 0.500 | 0.400 | 🔵 Node |
| hub_leakage | 0.000 | 0.000 | tie |
| type_entropy | 1.761 | 0.881 | 🔵 Node |
| top3_concentration | 0.461 | 0.603 | 🔵 Node |

---

## Query: `CHIPS Act semiconductor manufacturing`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | chips act *(REGULATORY_REQUIREMENT)* | micron technology *(ORG)* |
| 2 | chips act *(EVENT)* | chips act *(REGULATORY_REQUIREMENT)* |
| 3 | u.s. chips and science act *(REGULATORY_REQUIREMENT)* | chips act enactment *(EVENT)* |
| 4 | submission of chips act applications *(EVENT)* | advanced micro devices *(ORG)* |
| 5 | chips act enactment *(EVENT)* | chipsets *(PRODUCT)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | micron technology *(ORG)* `0.722` | micron technology *(ORG)* `0.778` |
| 2 | chips act *(REGULATORY_REQUIREMENT)* `0.503` | advanced micro devices *(ORG)* `0.621` |
| 3 | chips act *(EVENT)* `0.236` | chips act *(REGULATORY_REQUIREMENT)* `0.505` |
| 4 | announcement of us memory fabs *(EVENT)* `0.203` | chips act *(EVENT)* `0.236` |
| 5 | chips act enactment *(EVENT)* `0.170` | announcement of us memory fabs *(EVENT)* `0.203` |
| 6 | submission of chips act applications *(EVENT)* `0.152` | chips act enactment *(EVENT)* `0.170` |
| 7 | u.s. chips and science act *(REGULATORY_REQUIREMENT)* `0.150` | chipsets *(PRODUCT)* `0.151` |
| 8 | micron *(ORG)* `0.079` | amd *(ORG)* `0.134` |
| 9 | nvidia *(ORG)* `0.039` | micron *(ORG)* `0.087` |
| 10 | capacity expansion risks *(RISK_FACTOR)* `0.039` | nvidia *(ORG)* `0.082` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 5 | — |
| seed_type_diversity | 2 | 4 | 🟢 Triple |
| multi_hop_pct | 0.500 | 0.400 | 🔵 Node |
| hub_leakage | 0.000 | 0.000 | tie |
| type_entropy | 1.846 | 1.685 | 🔵 Node |
| top3_concentration | 0.637 | 0.642 | 🔵 Node |

---

## Query: `US export controls on AI chips to China`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | us export controls on ai technologies *(RISK_FACTOR)* | advanced micro devices *(ORG)* |
| 2 | export controls on ai semiconductors *(RISK_FACTOR)* | us export controls on ai technologies *(RISK_FACTOR)* |
| 3 | potential new export controls on ai products *(EVENT)* | export controls on ai semiconductors *(RISK_FACTOR)* |
| 4 | us export controls on semiconductors *(RISK_FACTOR)* | export control regulations *(REGULATORY_REQUIREMENT)* |
| 5 | new us export restrictions on semiconductors to china *(EVENT)* | china *(GPE)* |
| 6 |  | china regulatory inquiries *(RISK_FACTOR)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | amd *(ORG)* `0.401` | advanced micro devices *(ORG)* `0.772` |
| 2 | micron technology *(ORG)* `0.312` | nvidia *(ORG)* `0.563` |
| 3 | advanced micro devices *(ORG)* `0.298` | export controls on ai semiconductors *(RISK_FACTOR)* `0.391` |
| 4 | nvidia *(ORG)* `0.239` | china *(GPE)* `0.326` |
| 5 | export controls on ai semiconductors *(RISK_FACTOR)* `0.210` | amd *(ORG)* `0.197` |
| 6 | us export controls on semiconductors *(RISK_FACTOR)* `0.195` | export control regulations *(REGULATORY_REQUIREMENT)* `0.194` |
| 7 | new us export restrictions on semiconductors to china *(EVENT)* `0.184` | china regulatory inquiries *(RISK_FACTOR)* `0.192` |
| 8 | us export controls on ai technologies *(RISK_FACTOR)* `0.153` | nvidia corporation *(ORG)* `0.184` |
| 9 | potential new export controls on ai products *(EVENT)* `0.151` | export control regulations *(RISK_FACTOR)* `0.166` |
| 10 | china *(GPE)* `0.128` | us export controls on ai technologies *(RISK_FACTOR)* `0.157` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 6 | — |
| seed_type_diversity | 2 | 4 | 🟢 Triple |
| multi_hop_pct | 0.500 | 0.300 | 🔵 Node |
| hub_leakage | 0.056 | 0.104 | 🔵 Node |
| type_entropy | 1.846 | 1.722 | 🔵 Node |
| top3_concentration | 0.445 | 0.549 | 🔵 Node |

---

## Query: `Xilinx acquisition impact on AMD`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | xilinx acquisition *(EVENT)* | amd *(ORG)* |
| 2 | acquisition of xilinx *(EVENT)* | acquisition of xilinx *(EVENT)* |
| 3 | cash acquired from acquisition of xilinx *(FIN_METRIC)* | xilinx acquisition *(EVENT)* |
| 4 | xilinx *(COMP)* | advanced micro devices *(ORG)* |
| 5 | xilinx *(PRODUCT)* | xilinx *(COMP)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | amd *(ORG)* `0.748` | amd *(ORG)* `1.063` |
| 2 | advanced micro devices *(ORG)* `0.745` | advanced micro devices *(ORG)* `0.940` |
| 3 | acquisition of xilinx *(EVENT)* `0.243` | xilinx acquisition *(EVENT)* `0.178` |
| 4 | cash acquired from acquisition of xilinx *(FIN_METRIC)* `0.192` | acquisition of xilinx *(EVENT)* `0.174` |
| 5 | xilinx acquisition *(EVENT)* `0.177` | xilinx *(PRODUCT)* `0.156` |
| 6 | xilinx *(PRODUCT)* `0.155` | xilinx *(COMP)* `0.152` |
| 7 | xilinx *(COMP)* `0.152` | nvidia *(ORG)* `0.107` |
| 8 | advanced micro devices, inc. *(ORG)* `0.091` | advanced micro devices, inc. *(ORG)* `0.102` |
| 9 | nvidia *(ORG)* `0.082` | nvidia corporation *(ORG)* `0.074` |
| 10 | embedded segment *(SEGMENT)* `0.073` | embedded segment *(SEGMENT)* `0.064` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 5 | — |
| seed_type_diversity | 4 | 3 | 🔵 Node |
| multi_hop_pct | 0.500 | 0.400 | 🔵 Node |
| hub_leakage | 0.000 | 0.000 | tie |
| type_entropy | 2.322 | 1.961 | 🔵 Node |
| top3_concentration | 0.653 | 0.724 | 🔵 Node |

---

## Query: `adverse economic conditions impact on revenue`

### Seeds

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | adverse economic conditions *(MACRO_CONDITION)* | adverse economic conditions *(MACRO_CONDITION)* |
| 2 | adverse economic conditions *(RISK_FACTOR)* | customer cash flow problems *(RISK_FACTOR)* |
| 3 | adverse economic and industry conditions *(MACRO_CONDITION)* | industry conditions *(MACRO_CONDITION)* |
| 4 | adverse impacts on manufacturing and sales *(RISK_FACTOR)* | total revenue *(FIN_METRIC)* |
| 5 | economic conditions *(MACRO_CONDITION)* | global macroeconomic challenges *(MACRO_CONDITION)* |
| 6 |  | revenue *(FIN_METRIC)* |
| 7 |  | adverse economic conditions *(RISK_FACTOR)* |
| 8 |  | recession *(MACRO_CONDITION)* |

### PPR top-10

| # | Query-to-Node | Query-to-Triple |
|---|---|---|
| 1 | adverse economic and industry conditions *(MACRO_CONDITION)* `0.300` | revenue *(FIN_METRIC)* `0.421` |
| 2 | adverse economic conditions *(RISK_FACTOR)* `0.240` | adverse economic conditions *(RISK_FACTOR)* `0.347` |
| 3 | economic conditions *(MACRO_CONDITION)* `0.219` | adverse economic conditions *(MACRO_CONDITION)* `0.290` |
| 4 | adverse economic conditions *(MACRO_CONDITION)* `0.193` | marvell technology *(ORG)* `0.277` |
| 5 | debt obligations *(RISK_FACTOR)* `0.168` | nvidia *(ORG)* `0.272` |
| 6 | adverse impacts on manufacturing and sales *(RISK_FACTOR)* `0.150` | customer cash flow problems *(RISK_FACTOR)* `0.256` |
| 7 | filer *(ORG)* `0.132` | industry conditions *(MACRO_CONDITION)* `0.221` |
| 8 | marvell technology *(ORG)* `0.119` | recession *(MACRO_CONDITION)* `0.220` |
| 9 | insufficient cash flows to fund operations *(RISK_FACTOR)* `0.102` | total revenue *(FIN_METRIC)* `0.208` |
| 10 | rising interest rates *(MACRO_CONDITION)* `0.101` | nvidia corporation *(ORG)* `0.201` |

### Metrics

| Metric | Query-to-Node | Query-to-Triple | Winner |
|---|---|---|---|
| seed_count | 5 | 8 | — |
| seed_type_diversity | 2 | 3 | 🟢 Triple |
| multi_hop_pct | 0.500 | 0.300 | 🔵 Node |
| hub_leakage | 0.000 | 0.155 | 🔵 Node |
| type_entropy | 1.522 | 1.971 | 🟢 Triple |
| top3_concentration | 0.440 | 0.390 | 🟢 Triple |

---

## Aggregate (mean across 12 queries)

| Metric | Query-to-Node | Query-to-Triple | Delta | Winner |
|---|---|---|---|---|
| seed_count | 5.00 | 6.42 | +1.42 | — |
| seed_type_diversity | 2.33 | 3.17 | +0.83 | 🟢 Triple |
| multi_hop_pct | 0.500 | 0.358 | -0.142 | 🔵 Node |
| hub_leakage | 0.020 | 0.066 | +0.046 | 🔵 Node |
| type_entropy | 1.734 | 1.654 | -0.079 | 🔵 Node |
| top3_concentration | 0.562 | 0.594 | +0.032 | 🔵 Node |

## Verdict

- Comparable metrics: 5 (excluding `seed_count` info-only)
- Query-to-Triple wins: **1**
- Query-to-Node wins: **4**

