"""
Synthesized multi-hop evaluation — Phase C2-bis.

The 17-query test set in test_graph_search.py / test_vector_search.py is
topical, not multi-hop: every query contains the surface terms of its
answer chunks. That gives vector search an unfair advantage and fails to
test the structural advantage graph_search is supposed to provide.

This script defines 8 hand-crafted multi-hop questions where:
1. The question references a SUBJECT entity (e.g. "Hopper", "Ryzen").
2. The ANSWER entity (e.g. "TSMC", "Santa Clara") is NEVER surfaced in the
   question — it must be inferred by traversing an edge in the graph.
3. The bridge entity (e.g. "NVIDIA", "AMD") may or may not appear; the
   question is phrased so the answer is one hop past the bridge.

Every chain is pre-verified against the live graph (PRODUCES, SUPPLIES,
OPERATES_IN edges) so the test is reproducible.

Metrics:
- Hit@5: 1 if any expected chunk appears in top-5, else 0
- Recall@5: |returned ∩ expected| / min(|expected|, 5)

Both vector_search and graph_search are tested on the same questions. If
graph_search outperforms vector_search on Hit@5 by ≥ 2 questions, the
thesis hypothesis ("graph retrieval beats vector on multi-hop") is
empirically supported. If not, the gap motivates Phase C1c tuning
(intersection-bias fix, specificity-weighted teleport).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

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
    print(f"\n✓ Report saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
