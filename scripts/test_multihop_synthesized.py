"""
Synthesized multi-hop dev set — Phase C2-bis → C2-quinque (N=50 expansion).

The 17-query topical test set in test_graph_search.py / test_vector_search.py
contains the surface terms of its answer chunks — vector search has unfair
advantage there. This dev set tests the structural advantage graph_search
should provide:

1. The question references a SUBJECT entity (e.g. "Hopper", "Ryzen", "Xeon").
2. The ANSWER entity (e.g. "TSMC", "Mobileye", "Israel") is NEVER surfaced
   in the question — it must be inferred by traversing an edge.
3. The bridge entity may or may not appear; the question is phrased so the
   answer is one (or more) hops past the bridge.

Every answer_entities list is pre-verified against the live graph (≥1
chunk via MENTIONS edge — most have ≥5 chunks; exceptions documented inline).
Held-out test (test_multihop_holdout.py, N=10) is kept locked; this dev set
is for **tuning only** — peek freely.

Test set composition (5 tickers × 6 axes, N=50):
  Q1-Q8   original smoke set       (NVDA/AMD heavy)
  Q9-Q20  Phase C2-bis extension   (NVDA/AMD/TSMC/MU)
  Q21-Q32 INTC-anchored            (12 questions — supplier/partner/geo/
                                    segment/regulator/3-hop/topical)
  Q33-Q40 MU + ASML broadening     (8 questions — fills cross-corpus coverage)
  Q41-Q50 cross-company chains     (10 questions — hyperscaler/foundry/
                                    process node / risk / topical)

Statistical power at N=50:
  - McNemar paired test on Hit@5 detects ≥7-query delta at p<0.05 between
    any two configs (≈14% absolute) — enough to discriminate graph/hybrid
    from vector if the structural advantage is real.
  - Per-ticker N≥8 enables sub-population analysis (regression check when
    tuning weights).

Metrics:
- Hit@5: 1 if any expected chunk appears in top-5, else 0
- Recall@5: |returned ∩ expected| / min(|expected|, 5)
"""
from __future__ import annotations

import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.stats import binomtest, chi2, wilcoxon

logging.getLogger("neo4j").setLevel("ERROR")

from semigraph.config import get_config
from semigraph.connections import get_neo4j_driver
from semigraph.online.graph_search import graph_search
from semigraph.online.hybrid_search import hybrid_search
from semigraph.online.vector_search import vector_search


# Each question has a verified reasoning chain. `answer_entities` is the
# set of entity names that, when mentioned by a chunk, mark that chunk as
# a correct answer. Expected chunks are derived at runtime from the live
# graph (chunks MENTIONS any answer entity).
#
# Test set composition (intentional balance — NOT engineered for graph wins):
#   Q1-Q8   original — 3 graph-favorable, 3 vector-favorable, 2 mixed
#   Q9-Q20  extension — 5 graph-favorable (supplier/partner chains),
#                       4 vector-favorable (topical/abstract descriptors),
#                       3 mixed (3-hop or narrow entities)
MULTIHOP_QUERIES: list[dict] = [
    # ----- Original 8 (smoke set) -----
    {
        "id": "Q1",
        "type": "supplier_via_product",
        "question": "Which foundry partner manufactures the Hopper architecture chips?",
        "chain": "Hopper -PRODUCES-> NVIDIA <-SUPPLIES- TSMC",
        "surface_terms": ["foundry", "partner", "Hopper", "architecture", "chips"],
        "answer_entities": ["tsmc"],
    },
    {
        "id": "Q2",
        "type": "supplier_via_product",
        "question": "Who produces the dense memory chips that power modern AI training accelerators?",
        "chain": "AI accelerators (HBM) -PRODUCES-> Micron",
        "surface_terms": ["dense", "memory", "chips", "AI", "training", "accelerators"],
        "answer_entities": ["micron", "micron technology"],
    },
    {
        "id": "Q3",
        "type": "competitor_product",
        "question": "What AI accelerator product line does the main x86 desktop CPU rival of Intel offer?",
        "chain": "Intel <-COMPETES_WITH- AMD -PRODUCES-> Instinct MI300",
        "surface_terms": ["AI", "accelerator", "x86", "desktop", "CPU", "rival", "Intel"],
        "answer_entities": [
            "amd instinct mi300", "amd instinct mi200", "mi300", "mi200",
            "amd instinct mi300 series", "instinct"
        ],
    },
    {
        "id": "Q4",
        "type": "geo_via_supplier",
        "question": "What political risks affect the home country of the leading pure-play semiconductor foundry?",
        "chain": "foundry -> TSMC -OPERATES_IN-> Taiwan",
        "surface_terms": ["political", "risks", "country", "semiconductor", "foundry", "leading"],
        "answer_entities": ["taiwan"],
    },
    {
        "id": "Q5",
        "type": "geo_via_product",
        "question": "Where is the developer of Ryzen processors headquartered?",
        "chain": "Ryzen -PRODUCES-> AMD -OPERATES_IN-> Santa Clara",
        "surface_terms": ["developer", "Ryzen", "processors", "headquartered"],
        "answer_entities": ["santa clara", "sunnyvale", "california"],
    },
    {
        "id": "Q6",
        "type": "three_hop_supplier",
        "question": "Which firm produces the memory chips integrated into the H100 accelerator?",
        "chain": "H100 -PRODUCES-> NVIDIA — uses HBM <-PRODUCES- Micron",
        "surface_terms": ["firm", "memory", "chips", "H100", "accelerator"],
        "answer_entities": ["micron", "micron technology", "sk hynix", "samsung electronics"],
    },
    {
        "id": "Q7",
        "type": "geo_via_competitor",
        "question": "In what countries does the GeForce graphics card vendor maintain operations?",
        "chain": "GeForce -PRODUCES-> NVIDIA -OPERATES_IN-> {China, India, Taiwan, ...}",
        "surface_terms": ["countries", "GeForce", "graphics", "card", "vendor", "operations"],
        "answer_entities": ["china", "india", "taiwan", "israel"],
    },
    {
        "id": "Q8",
        "type": "regulation_via_product",
        "question": "What export controls affect AI chip sales from the maker of Blackwell architecture?",
        "chain": "Blackwell -PRODUCES-> NVIDIA -SUBJECT_TO-> Export Administration Regulations (China-bound)",
        "surface_terms": ["export", "controls", "AI", "chip", "sales", "Blackwell", "architecture", "maker"],
        "answer_entities": ["export administration regulations", "china", "bureau of industry and security"],
    },

    # ----- Extension (Q9-Q20) — 12 more, balanced -----
    {
        "id": "Q9",
        "type": "supplier_via_company",
        "question": "Which Asian semiconductor manufacturer supplies wafers to NVIDIA's GPU production?",
        "chain": "NVIDIA <-SUPPLIES- {TSMC, Samsung, SK Hynix}",
        "surface_terms": ["Asian", "semiconductor", "manufacturer", "wafers", "NVIDIA", "GPU"],
        "answer_entities": ["tsmc", "samsung electronics co ltd", "sk hynix inc"],
    },
    {
        "id": "Q10",
        "type": "supplier_via_company",
        "question": "Which Taiwanese contract chipmaker fabricates AMD's processors?",
        "chain": "AMD <-SUPPLIES- {TSMC, UMC}",
        "surface_terms": ["Taiwanese", "contract", "chipmaker", "fabricates", "AMD", "processors"],
        "answer_entities": ["tsmc", "umc"],
    },
    {
        "id": "Q11",
        "type": "geo_via_product",
        "question": "In what U.S. state does the developer of the CUDA platform operate its headquarters?",
        "chain": "CUDA -PRODUCES-> NVIDIA -OPERATES_IN-> {Santa Clara, California}",
        "surface_terms": ["U.S.", "state", "developer", "CUDA", "platform", "headquarters"],
        "answer_entities": ["santa clara", "california"],
    },
    {
        "id": "Q12",
        "type": "partner_via_product",
        "question": "Which gaming console maker partners with the Ryzen processor company?",
        "chain": "Ryzen -PRODUCES-> AMD -PARTNERS_WITH-> {Sony, Microsoft, Valve}",
        "surface_terms": ["gaming", "console", "maker", "partners", "Ryzen", "processor"],
        "answer_entities": ["sony", "valve", "microsoft"],
    },
    {
        "id": "Q13",
        "type": "product_in_segment",
        "question": "What product family does NVIDIA offer for the consumer gaming graphics market?",
        "chain": "NVIDIA -PRODUCES-> GeForce (gaming consumer GPU line)",
        "surface_terms": ["product", "family", "NVIDIA", "consumer", "gaming", "graphics"],
        "answer_entities": ["geforce", "geforce rtx", "geforce now"],
    },
    {
        "id": "Q14",
        "type": "segment_via_product",
        "question": "What revenue segments does the developer of EPYC processors disclose?",
        "chain": "EPYC -PRODUCES-> AMD -HAS_STAKE_IN-> {Data Center, Client, Gaming, Embedded}",
        "surface_terms": ["revenue", "segments", "developer", "EPYC", "processors", "disclose"],
        "answer_entities": ["data center", "client segment", "gaming segment", "embedded", "client and gaming"],
    },
    {
        "id": "Q15",
        "type": "regulator_via_topic",
        "question": "What U.S. agency oversees semiconductor export controls to China?",
        "chain": "semiconductor companies -SUBJECT_TO-> BIS / Commerce Dept",
        "surface_terms": ["U.S.", "agency", "oversees", "semiconductor", "export", "controls", "China"],
        "answer_entities": ["bureau of industry and security", "u.s. department of commerce", "export administration regulations"],
    },
    {
        "id": "Q16",
        "type": "macro_risk",
        "question": "What macroeconomic conditions create headwinds for chip industry revenue?",
        "chain": "companies -IMPACTED_BY-> {geopolitical tensions, economic instability}",
        "surface_terms": ["macroeconomic", "conditions", "headwinds", "chip", "industry", "revenue"],
        "answer_entities": [
            "geopolitical tensions", "political and economic instability",
            "geopolitical conditions", "global business disruptions",
            "economic and market uncertainty"
        ],
    },
    {
        "id": "Q17",
        "type": "geo_via_industry",
        "question": "Which Asian country hosts most semiconductor wafer fabrication capacity?",
        "chain": "wafer fab industry -> {TSMC, UMC} -OPERATES_IN-> Taiwan",
        "surface_terms": ["Asian", "country", "hosts", "semiconductor", "wafer", "fabrication", "capacity"],
        "answer_entities": ["taiwan"],
    },
    {
        "id": "Q18",
        "type": "product_line_via_product",
        "question": "What data center accelerators come from the developer of Hopper architecture?",
        "chain": "Hopper -PRODUCES-> NVIDIA -PRODUCES-> {H100, H200, A100, Blackwell, GB200}",
        "surface_terms": ["data center", "accelerators", "developer", "Hopper", "architecture"],
        "answer_entities": ["h100", "h200", "a100", "blackwell", "gb200", "gb300", "blackwell architecture"],
    },
    {
        "id": "Q19",
        "type": "segment_via_competitor",
        "question": "What market segments does Intel's primary CPU competitor pursue for growth?",
        "chain": "Intel <-COMPETES_WITH- AMD -HAS_STAKE_IN-> {Data Center, Gaming, Client}",
        "surface_terms": ["market", "segments", "Intel", "primary", "CPU", "competitor", "growth"],
        "answer_entities": ["data center", "gaming segment", "client segment", "embedded", "client and gaming"],
    },
    {
        "id": "Q20",
        "type": "competitor_product",
        "question": "What graphics product line does AMD offer to compete with NVIDIA's RTX series?",
        "chain": "NVIDIA -PRODUCES-> RTX, AMD -PRODUCES-> Radeon",
        "surface_terms": ["graphics", "product", "line", "AMD", "compete", "NVIDIA", "RTX", "series"],
        "answer_entities": ["radeon", "amd radeon", "amd radeon pro"],
    },

    # ----- INTC-anchored (Q21-Q32) — added after INTC ingest, expand from N=20→N=50 -----
    # Each chain bridges through "intel" or a related INTC product. Answer entities
    # verified to exist with ≥3 chunks in the graph (one exception noted) and avoid
    # surface-leakage of the answer name in the question text.
    {
        "id": "Q21",
        "type": "supplier_via_product",
        "question": "Which Asian contract chipmakers fabricate older-generation processors for the developer of Intel 18A?",
        "chain": "Intel 18A -PRODUCES-> Intel <-SUPPLIES- {TSMC, UMC, SMIC}",
        "surface_terms": ["Asian", "contract", "chipmakers", "fabricate", "older-generation", "Intel 18A"],
        "answer_entities": ["tsmc", "umc", "smic"],
    },
    {
        "id": "Q22",
        "type": "partner_via_product",
        "question": "Which infrastructure investment firms partner with the maker of Xeon Scalable processors on fab financing?",
        "chain": "Xeon -PRODUCES-> Intel -PARTNERS_WITH-> {Brookfield, Apollo}",
        "surface_terms": ["infrastructure", "investment", "firms", "partner", "Xeon", "Scalable", "fab", "financing"],
        "answer_entities": ["brookfield", "apollo"],
    },
    {
        "id": "Q23",
        "type": "subsidiary_via_product",
        "question": "Which autonomous driving subsidiary does the developer of Intel Core Ultra operate?",
        "chain": "Intel Core Ultra -PRODUCES-> Intel -HAS_STAKE_IN-> Mobileye",
        "surface_terms": ["autonomous", "driving", "subsidiary", "Intel Core Ultra"],
        "answer_entities": ["mobileye"],
    },
    {
        "id": "Q24",
        "type": "partner_via_product",
        "question": "Which operating system maker collaborates with the Xeon Scalable processor developer on AI PC platforms?",
        "chain": "Xeon -PRODUCES-> Intel -PARTNERS_WITH-> Microsoft (AI PC)",
        "surface_terms": ["operating", "system", "maker", "collaborates", "Xeon", "Scalable", "AI PC"],
        "answer_entities": ["microsoft"],
    },
    {
        "id": "Q25",
        "type": "geo_via_product",
        "question": "In which U.S. states does the developer of the Intel 18A process operate wafer fabrication facilities?",
        "chain": "Intel 18A -PRODUCES-> Intel -OPERATES_IN-> {Arizona, Ohio, Oregon, New Mexico}",
        "surface_terms": ["U.S.", "states", "Intel 18A", "process", "wafer", "fabrication", "facilities"],
        "answer_entities": ["arizona", "ohio", "oregon", "new mexico"],
    },
    {
        "id": "Q26",
        "type": "geo_via_product",
        "question": "In which Middle Eastern country does the developer of Xeon Scalable processors operate a major fab?",
        "chain": "Xeon -PRODUCES-> Intel -OPERATES_IN-> Israel (Kiryat Gat)",
        "surface_terms": ["Middle Eastern", "country", "Xeon", "Scalable", "major", "fab"],
        "answer_entities": ["israel"],
    },
    {
        "id": "Q27",
        "type": "segment_via_product",
        "question": "What primary reporting segments does the maker of Xeon Scalable break out in its annual filings?",
        "chain": "Xeon -PRODUCES-> Intel -HAS_STAKE_IN-> {DCAI, CCG, Intel Foundry, NEX}",
        "surface_terms": ["primary", "reporting", "segments", "Xeon", "Scalable", "annual", "filings"],
        "answer_entities": ["dcai", "ccg", "intel foundry", "nex", "data center and ai", "client computing group"],
    },
    {
        "id": "Q28",
        "type": "regulator_via_product",
        "question": "What U.S. legislative act funds domestic semiconductor manufacturing expansion at the Intel 18A developer?",
        "chain": "Intel 18A -PRODUCES-> Intel -SUBJECT_TO-> CHIPS Act",
        "surface_terms": ["U.S.", "legislative", "act", "funds", "domestic", "manufacturing", "expansion", "Intel 18A"],
        "answer_entities": ["chips act"],
    },
    {
        "id": "Q29",
        "type": "competitor_via_product",
        "question": "Which ARM-based mobile chip companies compete with the developer of x86 processor cores in the client computing market?",
        "chain": "x86 cores -PRODUCES-> Intel <-COMPETES_WITH- {Qualcomm, MediaTek, Apple}",
        "surface_terms": ["ARM-based", "mobile", "chip", "companies", "compete", "x86", "processor", "cores", "client", "computing"],
        "answer_entities": ["qualcomm", "mediatek", "apple"],
    },
    {
        "id": "Q30",
        "type": "three_hop_subsidiary_product",
        "question": "What advanced driver assistance product lines come from the autonomous driving subsidiary of the Xeon Scalable developer?",
        "chain": "Xeon -PRODUCES-> Intel -HAS_STAKE_IN-> Mobileye -PRODUCES-> {SuperVision, Chauffeur, Drive}",
        "surface_terms": ["advanced", "driver", "assistance", "product", "autonomous", "driving", "subsidiary", "Xeon"],
        "answer_entities": ["mobileye supervision", "mobileye chauffeur", "mobileye drive"],
    },
    {
        "id": "Q31",
        "type": "regulator_via_product",
        "question": "What U.S. export restrictions affect chip sales by the Intel 18A developer to specific Asian end markets?",
        "chain": "Intel 18A -PRODUCES-> Intel -SUBJECT_TO-> {export controls, EAR, China}",
        "surface_terms": ["U.S.", "export", "restrictions", "chip", "sales", "Intel 18A", "Asian", "end", "markets"],
        "answer_entities": ["export controls", "export administration regulations", "china"],
    },
    {
        "id": "Q32",
        "type": "topical_strategy",
        "question": "How does the IDM 2.0 strategy aim to restore U.S. semiconductor manufacturing leadership?",
        "chain": "topical — IDM 2.0 + Smart Capital + internal foundry",
        "surface_terms": ["IDM 2.0", "strategy", "restore", "U.S.", "semiconductor", "manufacturing", "leadership"],
        "answer_entities": [
            "idm 2.0", "idm 2.0 strategy", "smart capital initiatives",
            "internal foundry operating model", "idm 2.0 strategy implementation risk",
        ],
    },

    # ----- MU / ASML coverage broadening (Q33-Q40) -----
    {
        "id": "Q33",
        "type": "product_via_company",
        "question": "What consumer storage and DRAM brand is sold by the U.S. supplier of HBM3E memory?",
        "chain": "HBM3E -PRODUCES-> Micron -PRODUCES-> Crucial",
        "surface_terms": ["consumer", "storage", "DRAM", "brand", "U.S.", "supplier", "HBM3E", "memory"],
        "answer_entities": ["crucial"],
    },
    {
        "id": "Q34",
        "type": "geo_via_product",
        "question": "In which Asian countries does the developer of HBM3E memory operate fabrication or assembly facilities?",
        "chain": "HBM3E -PRODUCES-> Micron -OPERATES_IN-> {Taiwan, Japan, Malaysia, Singapore}",
        "surface_terms": ["Asian", "countries", "HBM3E", "memory", "fabrication", "assembly", "facilities"],
        "answer_entities": ["taiwan", "japan", "malaysia", "singapore"],
    },
    {
        "id": "Q35",
        "type": "customer_via_product",
        "question": "Which AI accelerator vendor purchases HBM3E from the U.S. memory supplier for its data center GPUs?",
        "chain": "HBM3E -PRODUCES-> Micron -SUPPLIES-> NVIDIA",
        "surface_terms": ["AI", "accelerator", "vendor", "purchases", "HBM3E", "U.S.", "memory", "supplier", "data center", "GPUs"],
        "answer_entities": ["nvidia", "nvidia corporation"],
    },
    {
        "id": "Q36",
        "type": "geo_via_product",
        "question": "In what European country is the sole producer of EUV lithography systems headquartered?",
        "chain": "EUV -PRODUCES-> ASML -OPERATES_IN-> Netherlands",
        "surface_terms": ["European", "country", "sole", "producer", "EUV", "lithography", "headquartered"],
        "answer_entities": ["netherlands"],
    },
    {
        "id": "Q37",
        "type": "customer_via_product",
        "question": "Which leading-edge semiconductor manufacturers are the largest customers of the EUV lithography systems maker?",
        "chain": "EUV -PRODUCES-> ASML -SUPPLIES-> {TSMC, Samsung, Intel}",
        "surface_terms": ["leading-edge", "semiconductor", "manufacturers", "largest", "customers", "EUV", "lithography"],
        "answer_entities": ["tsmc", "samsung electronics", "samsung", "intel"],
    },
    {
        "id": "Q38",
        "type": "regulator_via_product",
        "question": "Which export license regime restricts EUV lithography system shipments to Chinese semiconductor manufacturers?",
        "chain": "EUV -PRODUCES-> ASML -SUBJECT_TO-> {export controls, export licenses}",
        "surface_terms": ["export", "license", "regime", "restricts", "EUV", "lithography", "shipments", "Chinese", "manufacturers"],
        "answer_entities": ["export licenses", "export controls", "china"],
    },
    {
        "id": "Q39",
        "type": "topical_memory",
        "question": "Why has HBM become critical for modern AI training and inference workloads?",
        "chain": "topical — HBM as the bandwidth bottleneck-relief technology",
        "surface_terms": ["HBM", "critical", "modern", "AI", "training", "inference", "workloads"],
        "answer_entities": ["hbm", "hbm3e"],
    },
    {
        "id": "Q40",
        "type": "topical_ai_demand",
        "question": "How does the rise of generative AI drive demand for accelerated data center computing infrastructure?",
        "chain": "topical — gen AI inflates data center capex",
        "surface_terms": ["rise", "generative", "AI", "drive", "demand", "accelerated", "data center", "computing", "infrastructure"],
        "answer_entities": [
            "ai", "generative ai models", "emergence of generative ai models",
            "generative ai adoption risk", "demand for generative ai may fluctuate",
        ],
    },

    # ----- Cross-company chains (Q41-Q50) -----
    {
        "id": "Q41",
        "type": "customer_via_product",
        "question": "Which cloud hyperscalers partner with the EPYC processor maker for server CPU deployments in their data centers?",
        "chain": "EPYC -PRODUCES-> AMD -PARTNERS_WITH-> {Microsoft, Amazon, Google, Meta}",
        "surface_terms": ["cloud", "hyperscalers", "partner", "EPYC", "processor", "server", "CPU", "deployments"],
        "answer_entities": ["microsoft", "amazon", "google", "meta"],
    },
    {
        "id": "Q42",
        "type": "competitor_via_geo",
        "question": "Which Korean conglomerate competes with the Taiwanese pure-play foundry leader in advanced node foundry services?",
        "chain": "TSMC <-COMPETES_WITH- Samsung Foundry",
        "surface_terms": ["Korean", "conglomerate", "competes", "Taiwanese", "pure-play", "foundry", "advanced", "node"],
        "answer_entities": ["samsung electronics", "samsung", "samsung electronics co ltd"],
    },
    {
        "id": "Q43",
        "type": "supplier_via_product",
        "question": "Who supplies the high-bandwidth memory used in NVIDIA's H200 data center accelerator?",
        "chain": "H200 -PRODUCES-> NVIDIA <-SUPPLIES- {Micron, SK Hynix, Samsung}",
        "surface_terms": ["supplies", "high-bandwidth", "memory", "NVIDIA", "H200", "data center", "accelerator"],
        "answer_entities": ["micron", "micron technology", "sk hynix inc", "samsung electronics co ltd"],
    },
    {
        "id": "Q44",
        "type": "customer_via_product",
        "question": "Which premium smartphone maker uses leading-edge process node chips fabricated by the Taiwanese pure-play foundry?",
        "chain": "TSMC <-PARTNERS_WITH- Apple",
        "surface_terms": ["premium", "smartphone", "maker", "leading-edge", "process", "node", "fabricated", "Taiwanese", "foundry"],
        "answer_entities": ["apple"],
    },
    {
        "id": "Q45",
        "type": "product_via_company",
        "question": "Which process node generations define the manufacturing roadmap of the developer of Xeon Scalable processors?",
        "chain": "Xeon -PRODUCES-> Intel -PRODUCES-> {Intel 7, Intel 4, Intel 3, Intel 18A, Intel 14A}",
        "surface_terms": ["process", "node", "generations", "manufacturing", "roadmap", "Xeon", "Scalable"],
        "answer_entities": ["intel 4", "intel 7", "intel 3", "intel 18a", "intel 14a"],
    },
    {
        "id": "Q46",
        "type": "product_line_via_product",
        "question": "What data center accelerator product family drives the largest revenue segment of the CUDA platform developer?",
        "chain": "CUDA -PRODUCES-> NVIDIA -PRODUCES-> {H100, H200, Blackwell, GB200}",
        "surface_terms": ["data center", "accelerator", "product", "family", "drives", "largest", "revenue", "segment", "CUDA", "platform"],
        "answer_entities": ["h100", "h200", "blackwell", "gb200", "hopper", "blackwell architecture", "hgx"],
    },
    {
        "id": "Q47",
        "type": "competitor_via_product",
        "question": "What ARM-based server CPU competes with AMD's EPYC processors and is developed by the CUDA platform maker?",
        "chain": "EPYC <-COMPETES_WITH- Grace -PRODUCES-> NVIDIA",
        "surface_terms": ["ARM-based", "server", "CPU", "competes", "AMD", "EPYC", "developed", "CUDA", "platform"],
        "answer_entities": ["grace", "grace cpu"],
    },
    {
        "id": "Q48",
        "type": "risk_via_product",
        "question": "On which Taiwanese foundry does the GeForce graphics card vendor concentrate its wafer supply?",
        "chain": "GeForce -PRODUCES-> NVIDIA -DEPENDS_ON-> TSMC (single-source)",
        "surface_terms": ["Taiwanese", "foundry", "GeForce", "graphics", "card", "vendor", "concentrate", "wafer", "supply"],
        "answer_entities": ["tsmc"],
    },
    {
        "id": "Q49",
        "type": "regulator_via_segment",
        "question": "What U.S. export policy restricts advanced AI data center chip sales by the CUDA developer to specific foreign markets?",
        "chain": "CUDA -PRODUCES-> NVIDIA -SUBJECT_TO-> EAR (DC products → China)",
        "surface_terms": ["U.S.", "export", "policy", "restricts", "advanced", "AI", "data center", "chip", "sales", "CUDA"],
        "answer_entities": ["export administration regulations", "export controls", "china"],
    },
    {
        "id": "Q50",
        "type": "topical_capital",
        "question": "What capital intensity challenges face leading-edge semiconductor wafer fabrication?",
        "chain": "topical — capex burden of advanced-node fabs",
        "surface_terms": ["capital", "intensity", "challenges", "leading-edge", "semiconductor", "wafer", "fabrication"],
        "answer_entities": ["capital expenditures"],
    },
]

TOP_K = 5
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "analytics" / "multihop_synthesized_eval.md"
)


def fetch_expected_chunks(answer_entities: list[str]) -> set[str]:
    """Return chunk_ids that MENTION any of the answer entities."""
    cfg = get_config()
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session() as session:
            r = session.run(
                """
                MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
                WHERE e.name IN $names
                RETURN DISTINCT c.chunk_id AS id
                """,
                names=answer_entities,
            )
            return {row["id"] for row in r}
    finally:
        driver.close()


def evaluate(retrieved: list[dict], expected: set[str]) -> dict:
    """Hit@5 + Recall@5 + count of matches."""
    returned_ids = {r["chunk_id"] for r in retrieved}
    hits = returned_ids & expected
    n_hits = len(hits)
    hit_at_5 = 1 if n_hits > 0 else 0
    recall = n_hits / min(len(expected), TOP_K) if expected else 0.0
    return {
        "hit": hit_at_5,
        "n_hits": n_hits,
        "recall": recall,
        "hit_ids": sorted(hits),
        "returned_ids": [r["chunk_id"] for r in retrieved],
    }


# ===================== Statistical tests (paper-level) =====================
#
# Why these tests:
# - Hit@5 is paired binary across same N=50 queries with two systems →
#   McNemar's test (off-diagonal disagreements only — diagonal cells carry
#   no signal about which system is better).
# - Recall@5 is paired ordinal-continuous → Wilcoxon signed-rank (no
#   normality assumption; paired t-test would require it and N=50 is too
#   small to invoke CLT robustly for bounded [0,1] data).
# - Mean-recall delta CI via bootstrap (10k resamples) — gives a frequentist
#   uncertainty band that papers can quote alongside the point estimate.
# - Cohen's h on Hit@5 proportions — effect size in addition to p-value,
#   because at N=50 a "significant" tiny effect is still operationally weak.


def _mcnemar(hits_a: list[int], hits_b: list[int]) -> dict:
    """Paired binary test. Returns b, c, χ², p (continuity-corrected when
    b+c≥25, exact binomial otherwise — APA-standard cutoff)."""
    b = sum(1 for ha, hb in zip(hits_a, hits_b) if ha == 1 and hb == 0)
    c = sum(1 for ha, hb in zip(hits_a, hits_b) if ha == 0 and hb == 1)
    n_disc = b + c
    if n_disc == 0:
        return {"b": 0, "c": 0, "stat": 0.0, "p": 1.0, "method": "no_discordant"}
    if n_disc < 25:
        # Exact: min(b,c) under Binomial(n_disc, 0.5) — two-sided
        p = binomtest(min(b, c), n_disc, p=0.5, alternative="two-sided").pvalue
        return {"b": b, "c": c, "stat": float(min(b, c)), "p": float(p), "method": "exact"}
    # Chi-square with continuity correction (Edwards 1948)
    chi2_stat = (abs(b - c) - 1) ** 2 / n_disc
    p = float(1.0 - chi2.cdf(chi2_stat, df=1))
    return {"b": b, "c": c, "stat": float(chi2_stat), "p": p, "method": "chi2_cc"}


def _wilcoxon(recalls_a: list[float], recalls_b: list[float]) -> dict:
    """Paired signed-rank on (a − b) recall diffs. Drops zero-diffs
    (Wilcoxon's standard handling — scipy default `zero_method='wilcox'`)."""
    diffs = np.array(recalls_a) - np.array(recalls_b)
    non_zero = diffs[diffs != 0]
    if len(non_zero) == 0:
        return {"stat": 0.0, "p": 1.0, "n_nonzero": 0}
    res = wilcoxon(non_zero, alternative="two-sided", zero_method="wilcox")
    return {"stat": float(res.statistic), "p": float(res.pvalue), "n_nonzero": len(non_zero)}


def _bootstrap_ci(diffs: list[float], n_boot: int = 10_000, seed: int = 42) -> dict:
    """Percentile-bootstrap 95% CI on mean(diffs). Excluding 0 ⇒ robust."""
    rng = np.random.default_rng(seed)
    arr = np.array(diffs)
    if len(arr) == 0:
        return {"mean": 0.0, "lo": 0.0, "hi": 0.0, "excludes_zero": False}
    idx = rng.integers(0, len(arr), size=(n_boot, len(arr)))
    boot_means = arr[idx].mean(axis=1)
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    return {
        "mean": float(arr.mean()),
        "lo": float(lo),
        "hi": float(hi),
        "excludes_zero": bool(lo > 0 or hi < 0),
    }


def _cohens_h(p1: float, p2: float) -> float:
    """Effect size for two proportions. |h|: 0.2 small, 0.5 medium, 0.8 large."""
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


def _pairwise_block(name_a: str, name_b: str, rows: list[dict],
                    key_a: str, key_b: str) -> dict:
    """Run all 4 tests + effect size for one pair (e.g. hybrid vs vector)."""
    hits_a = [r[key_a]["hit"] for r in rows]
    hits_b = [r[key_b]["hit"] for r in rows]
    rec_a = [r[key_a]["recall"] for r in rows]
    rec_b = [r[key_b]["recall"] for r in rows]
    diffs = [a - b for a, b in zip(rec_a, rec_b)]
    p_a, p_b = sum(hits_a) / len(hits_a), sum(hits_b) / len(hits_b)
    return {
        "label": f"{name_a} vs {name_b}",
        "mcnemar": _mcnemar(hits_a, hits_b),
        "wilcoxon": _wilcoxon(rec_a, rec_b),
        "bootstrap": _bootstrap_ci(diffs),
        "cohens_h": _cohens_h(p_a, p_b),
        "hit_rate_a": p_a, "hit_rate_b": p_b,
        "recall_a": float(np.mean(rec_a)), "recall_b": float(np.mean(rec_b)),
    }


def _format_pairwise(block: dict) -> list[str]:
    """Markdown lines for one pairwise block."""
    m, w, bo = block["mcnemar"], block["wilcoxon"], block["bootstrap"]
    sig = lambda p: "✓" if p < 0.05 else ("·" if p < 0.10 else "✗")
    excl = "✓ excludes 0" if bo["excludes_zero"] else "✗ crosses 0"
    return [
        f"### {block['label']}",
        "",
        f"- Hit@5: {block['hit_rate_a']:.2%} vs {block['hit_rate_b']:.2%}  "
        f"(Cohen's h = {block['cohens_h']:+.3f})",
        f"- Recall@5: {block['recall_a']:.3f} vs {block['recall_b']:.3f}  "
        f"(Δ = {block['recall_a'] - block['recall_b']:+.3f})",
        "",
        f"| Test | Statistic | p | Verdict |",
        f"|---|---|---|---|",
        f"| McNemar (Hit@5) | b={m['b']} c={m['c']} ({m['method']}) | "
        f"{m['p']:.4f} | {sig(m['p'])} |",
        f"| Wilcoxon signed-rank (Recall@5) | W={w['stat']:.1f} (n≠0={w['n_nonzero']}) | "
        f"{w['p']:.4f} | {sig(w['p'])} |",
        f"| Bootstrap 95% CI on mean Δ | [{bo['lo']:+.3f}, {bo['hi']:+.3f}] | — | {excl} |",
        "",
    ]


def _per_type_breakdown(rows: list[dict]) -> dict[str, dict]:
    """Group by query type → aggregate Hit/Recall per tool. Useful for
    identifying which question types graph/hybrid actually beats vector on."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["q"]["type"]].append(r)
    out: dict[str, dict] = {}
    for qtype, grp in groups.items():
        n = len(grp)
        out[qtype] = {
            "n": n,
            "vec_hit": sum(r["vec"]["hit"] for r in grp) / n,
            "gph_hit": sum(r["gph"]["hit"] for r in grp) / n,
            "hyb_hit": sum(r["hyb"]["hit"] for r in grp) / n,
            "vec_rec": sum(r["vec"]["recall"] for r in grp) / n,
            "gph_rec": sum(r["gph"]["recall"] for r in grp) / n,
            "hyb_rec": sum(r["hyb"]["recall"] for r in grp) / n,
        }
    return out


def main() -> None:
    print(f"Multi-hop synthesized eval — {len(MULTIHOP_QUERIES)} queries (top_k={TOP_K})\n")

    rows: list[dict] = []

    for q in MULTIHOP_QUERIES:
        print(f"\n--- {q['id']}: {q['question']}")
        print(f"    chain: {q['chain']}")

        expected = fetch_expected_chunks(q["answer_entities"])
        print(f"    expected chunks: {len(expected)} (mentioning {q['answer_entities']})")

        vec_run = vector_search(q["question"], top_k_chunks=TOP_K)
        gph_run = graph_search(q["question"], top_k_chunks=TOP_K)
        hyb_run = hybrid_search(q["question"], top_k_chunks=TOP_K)

        vec_eval = evaluate(vec_run, expected)
        gph_eval = evaluate(gph_run, expected)
        hyb_eval = evaluate(hyb_run, expected)

        # Winner = tool with strictly highest recall; ties broken by Hit@5
        # then alphabetically (graph < hybrid < vector) for determinism.
        scores = {
            "vector": vec_eval["recall"],
            "graph":  gph_eval["recall"],
            "hybrid": hyb_eval["recall"],
        }
        max_recall = max(scores.values())
        top = [t for t, r in scores.items() if r == max_recall]
        winner = top[0] if len(top) == 1 else "tie"

        rows.append({
            "q": q,
            "expected": expected,
            "vec": vec_eval,
            "gph": gph_eval,
            "hyb": hyb_eval,
            "vec_run": vec_run,
            "gph_run": gph_run,
            "hyb_run": hyb_run,
            "winner": winner,
        })

        print(f"    vector: hit={vec_eval['hit']}  recall={vec_eval['recall']:.2f}  "
              f"({vec_eval['n_hits']}/{TOP_K} hits)")
        print(f"    graph:  hit={gph_eval['hit']}  recall={gph_eval['recall']:.2f}  "
              f"({gph_eval['n_hits']}/{TOP_K} hits)")
        print(f"    hybrid: hit={hyb_eval['hit']}  recall={hyb_eval['recall']:.2f}  "
              f"({hyb_eval['n_hits']}/{TOP_K} hits)  winner={winner}")

    # Aggregate
    vec_hits = sum(r["vec"]["hit"] for r in rows)
    gph_hits = sum(r["gph"]["hit"] for r in rows)
    hyb_hits = sum(r["hyb"]["hit"] for r in rows)
    vec_recall_avg = sum(r["vec"]["recall"] for r in rows) / len(rows)
    gph_recall_avg = sum(r["gph"]["recall"] for r in rows) / len(rows)
    hyb_recall_avg = sum(r["hyb"]["recall"] for r in rows) / len(rows)
    n_graph_wins  = sum(1 for r in rows if r["winner"] == "graph")
    n_vec_wins    = sum(1 for r in rows if r["winner"] == "vector")
    n_hyb_wins    = sum(1 for r in rows if r["winner"] == "hybrid")
    n_ties        = sum(1 for r in rows if r["winner"] == "tie")
    # Pairwise hybrid vs vector — primary thesis claim
    hyb_beats_vec  = sum(1 for r in rows if r["hyb"]["recall"] >  r["vec"]["recall"])
    hyb_equals_vec = sum(1 for r in rows if r["hyb"]["recall"] == r["vec"]["recall"])
    hyb_loses_vec  = sum(1 for r in rows if r["hyb"]["recall"] <  r["vec"]["recall"])

    # Build report
    lines: list[str] = []
    lines.append("# Multi-hop Synthesized Evaluation — 3-config (Phase C2-quater)")
    lines.append("")
    lines.append("**Primary thesis claim:** Hybrid (RRF graph+vector fusion) > Pure Vector "
                 "on Hit@5 and Recall@5, with floor guarantee from RRF construction.")
    lines.append("")
    lines.append("**Methodology:** hand-crafted multi-hop questions, each with a verified "
                 "reasoning chain through the live KG. Expected chunks derived from "
                 "MENTIONS edges to answer entities (not hand-picked).")
    lines.append("")
    lines.append(f"**top_k_chunks:** {TOP_K} · **Tools tested:** vector_search, graph_search, hybrid_search (RRF k=60)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Aggregate Results — 3-config")
    lines.append("")
    lines.append("| Metric | vector | graph | **hybrid** | hyb − vec |")
    lines.append("|---|---|---|---|---|")
    lines.append(f"| Hit@5 | {vec_hits}/{len(rows)} | {gph_hits}/{len(rows)} | **{hyb_hits}/{len(rows)}** | "
                 f"{hyb_hits - vec_hits:+d} |")
    lines.append(f"| Avg Recall@5 | {vec_recall_avg:.3f} | {gph_recall_avg:.3f} | "
                 f"**{hyb_recall_avg:.3f}** | {hyb_recall_avg - vec_recall_avg:+.3f} |")
    lines.append(f"| Best-of-3 wins | {n_vec_wins} | {n_graph_wins} | **{n_hyb_wins}** | "
                 f"— (ties: {n_ties}) |")
    lines.append("")
    lines.append("### Pairwise: hybrid vs vector (primary thesis)")
    lines.append("")
    lines.append(f"- **hybrid > vector**: {hyb_beats_vec}/{len(rows)} queries")
    lines.append(f"- hybrid = vector: {hyb_equals_vec}/{len(rows)} queries")
    lines.append(f"- hybrid < vector: {hyb_loses_vec}/{len(rows)} queries (RRF should give 0 — diagnose if any)")
    lines.append("")
    lines.append("**Verdict:** "
                 + ("✓ hybrid ≥ vector on all queries (RRF floor holds)"
                    if hyb_loses_vec == 0
                    else f"⚠ hybrid < vector on {hyb_loses_vec} queries — check fusion noise"))
    lines.append("")
    lines.append("---")
    lines.append("")

    # ===== Statistical Significance — paper-defensible block =====
    pair_hv = _pairwise_block("hybrid", "vector", rows, "hyb", "vec")
    pair_gv = _pairwise_block("graph",  "vector", rows, "gph", "vec")
    pair_hg = _pairwise_block("hybrid", "graph",  rows, "hyb", "gph")

    lines.append("## Statistical Significance (paired tests, α = 0.05)")
    lines.append("")
    lines.append(f"N = {len(rows)} paired queries. Tests:")
    lines.append("- **McNemar** on Hit@5 (paired binary) — discordant pairs only")
    lines.append("- **Wilcoxon signed-rank** on Recall@5 (paired ordinal, no normality)")
    lines.append("- **Bootstrap 95% CI** on mean Recall@5 difference (10,000 resamples)")
    lines.append("- **Cohen's h** on Hit@5 proportions (effect size: 0.2 small / 0.5 medium / 0.8 large)")
    lines.append("")
    lines.append("Legend: p < 0.05 ✓ significant · p < 0.10 · marginal · p ≥ 0.10 ✗ not sig")
    lines.append("")
    lines += _format_pairwise(pair_hv)
    lines += _format_pairwise(pair_gv)
    lines += _format_pairwise(pair_hg)
    lines.append("---")
    lines.append("")

    # ===== Per-type breakdown (tuning diagnostic) =====
    types = _per_type_breakdown(rows)
    lines.append("## Per-Query-Type Breakdown (tuning diagnostic)")
    lines.append("")
    lines.append("If graph/hybrid beats vector on a subset of types, sub-type claim "
                 "is defensible even when overall test is null.")
    lines.append("")
    lines.append("| Type | n | vec H@5 | gph H@5 | hyb H@5 | vec R@5 | gph R@5 | hyb R@5 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for qtype, s in sorted(types.items(), key=lambda x: -x[1]["n"]):
        lines.append(
            f"| {qtype} | {s['n']} | {s['vec_hit']:.2f} | {s['gph_hit']:.2f} | "
            f"{s['hyb_hit']:.2f} | {s['vec_rec']:.2f} | {s['gph_rec']:.2f} | {s['hyb_rec']:.2f} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-query detail
    for i, r in enumerate(rows, start=1):
        q = r["q"]
        lines.append(f"## {q['id']}: `{q['question']}`")
        lines.append("")
        lines.append(f"- **type:** {q['type']}")
        lines.append(f"- **reasoning chain:** `{q['chain']}`")
        lines.append(f"- **answer entities:** `{q['answer_entities']}`")
        lines.append(f"- **expected chunks in corpus:** {len(r['expected'])}")
        lines.append("")

        lines.append("| Tool | Hit@5 | Recall@5 | Hits | Returned chunk_ids |")
        lines.append("|---|---|---|---|---|")
        vec_ret = ", ".join(f"`{cid[:30]}...`" for cid in r["vec"]["returned_ids"])
        gph_ret = ", ".join(f"`{cid[:30]}...`" for cid in r["gph"]["returned_ids"])
        hyb_ret = ", ".join(f"`{cid[:30]}...`" for cid in r["hyb"]["returned_ids"])
        lines.append(f"| vector | {r['vec']['hit']} | {r['vec']['recall']:.2f} | "
                     f"{r['vec']['n_hits']}/{TOP_K} | {vec_ret} |")
        lines.append(f"| graph  | {r['gph']['hit']} | {r['gph']['recall']:.2f} | "
                     f"{r['gph']['n_hits']}/{TOP_K} | {gph_ret} |")
        lines.append(f"| **hybrid** | **{r['hyb']['hit']}** | **{r['hyb']['recall']:.2f}** | "
                     f"**{r['hyb']['n_hits']}/{TOP_K}** | {hyb_ret} |")
        lines.append("")
        lines.append(f"**Winner:** {r['winner']}")
        lines.append("")

        if r["vec"]["hit_ids"]:
            lines.append(f"_vector hits:_ {r['vec']['hit_ids']}")
            lines.append("")
        if r["gph"]["hit_ids"]:
            lines.append(f"_graph hits:_ {r['gph']['hit_ids']}")
            lines.append("")
        if r["hyb"]["hit_ids"]:
            lines.append(f"_hybrid hits:_ {r['hyb']['hit_ids']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"Vector: hit={vec_hits}/{len(rows)}  recall_avg={vec_recall_avg:.3f}")
    print(f"Graph:  hit={gph_hits}/{len(rows)}  recall_avg={gph_recall_avg:.3f}")
    print(f"Hybrid: hit={hyb_hits}/{len(rows)}  recall_avg={hyb_recall_avg:.3f}")
    print(f"Best-of-3 wins → graph={n_graph_wins} vector={n_vec_wins} "
          f"hybrid={n_hyb_wins} ties={n_ties}")
    print(f"Hybrid vs Vector: beats={hyb_beats_vec} equal={hyb_equals_vec} "
          f"loses={hyb_loses_vec}")

    # Compact stat summary on console (full block in markdown)
    print(f"\n{'-' * 60}")
    print("Statistical significance (paired, α=0.05)")
    print(f"{'-' * 60}")
    for blk in (pair_hv, pair_gv, pair_hg):
        m, w, bo = blk["mcnemar"], blk["wilcoxon"], blk["bootstrap"]
        mark = lambda p: "✓" if p < 0.05 else ("·" if p < 0.10 else "✗")
        print(f"  {blk['label']:>18s}: "
              f"McNemar p={m['p']:.4f}{mark(m['p'])}  "
              f"Wilcoxon p={w['p']:.4f}{mark(w['p'])}  "
              f"Δ̄ R@5={bo['mean']:+.3f} [{bo['lo']:+.3f},{bo['hi']:+.3f}]"
              f"{' ✓' if bo['excludes_zero'] else ''}")

    print(f"\n✓ Report saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
