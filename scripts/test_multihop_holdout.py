"""
Held-out test set — Phase C2-ter.

**INTEGRITY RULE**: Do NOT examine the results of this script until ALL
tuning is complete. The 20-query dev set (test_multihop_synthesized.py)
is for parameter tuning; this 10-query held-out set is for FINAL
unbiased evaluation reported in the thesis.

Workflow:
  1. Tune LLM augmentation + PPR params on the dev set (N=20) — peek freely
  2. When tuning is "done" (no more changes), run this script ONCE
  3. Compare dev-set wins vs held-out wins — if held-out drops sharply,
     dev-set was overfit

The 10 queries below were authored without consulting the per-query
breakdown of the dev-set results, to minimize test-set leakage. Patterns
cover the same six axes as the dev set (supplier / partnership / geo /
segment / regulator / topical) so distribution shift is bounded.

Metrics: Hit@5, Recall@5 (same as dev set for direct comparison).
"""
from __future__ import annotations

import logging
from pathlib import Path

logging.getLogger("neo4j").setLevel("ERROR")

from semigraph.config import get_config
from semigraph.connections import get_neo4j_driver
from semigraph.online.graph_search import graph_search
from semigraph.online.hybrid_search import hybrid_search
from semigraph.online.vector_search import vector_search


HOLDOUT_QUERIES: list[dict] = [
    {
        "id": "H1",
        "type": "supplier_via_product",
        "question": "Which Korean memory chip supplier provides components to NVIDIA's data center GPUs?",
        "chain": "NVIDIA <-SUPPLIES- {SK Hynix, Samsung Electronics}",
        "answer_entities": ["sk hynix inc", "samsung electronics co ltd"],
    },
    {
        "id": "H2",
        "type": "product_via_product",
        "question": "What parallel computing software platform comes from the developer of Hopper architecture?",
        "chain": "Hopper -PRODUCES-> NVIDIA -PRODUCES-> CUDA",
        "answer_entities": ["cuda"],
    },
    {
        "id": "H3",
        "type": "partner_via_product",
        "question": "Which generative AI research lab partners with the maker of EPYC processors?",
        "chain": "EPYC -PRODUCES-> AMD -PARTNERS_WITH-> OpenAI",
        "answer_entities": ["openai"],
    },
    {
        "id": "H4",
        "type": "product_via_competitor",
        "question": "What memory storage product types come from the manufacturer competing with SK Hynix in DRAM markets?",
        "chain": "SK Hynix <-COMPETES_WITH- Micron -PRODUCES-> {NAND, DRAM, SSD}",
        "answer_entities": ["dram", "nand", "ssd", "managed nand", "nor"],
    },
    {
        "id": "H5",
        "type": "macro_risk",
        "question": "What political tensions threaten East Asian semiconductor supply chain stability?",
        "chain": "supply chain -IMPACTED_BY-> {geopolitical tensions, China-Taiwan instability}",
        "answer_entities": [
            "geopolitical tensions", "political and economic instability",
            "china", "taiwan", "geopolitical conditions",
        ],
    },
    {
        "id": "H6",
        "type": "topical_business",
        "question": "How does the transition from Hopper to Blackwell architecture affect data center GPU revenue?",
        "chain": "product transition Hopper→Blackwell impacts revenue",
        "answer_entities": [
            "business model transition from hopper hgx to blackwell",
            "hopper architecture", "blackwell architecture", "hopper", "blackwell",
        ],
    },
    {
        "id": "H7",
        "type": "topical_abstract",
        "question": "Why must semiconductor firms maintain large research and development investments?",
        "chain": "abstract — RnD as competitive moat",
        "answer_entities": ["research and development", "r&d expenses", "innovation"],
    },
    {
        "id": "H8",
        "type": "product_in_segment",
        "question": "Which professional workstation graphics product line comes from the Hopper architect?",
        "chain": "Hopper -PRODUCES-> NVIDIA -PRODUCES-> Quadro RTX",
        "answer_entities": ["quadro nvidia rtx gpus"],
    },
    {
        "id": "H9",
        "type": "segment_via_product",
        "question": "What revenue segments does the leading discrete GPU vendor break out in its filings?",
        "chain": "discrete GPU = NVIDIA -HAS_STAKE_IN-> {Compute & Networking, Graphics, Pro Viz, Data Center}",
        "answer_entities": [
            "data center", "compute & networking", "graphics",
            "professional visualization",
        ],
    },
    {
        "id": "H10",
        "type": "regulator_via_topic",
        "question": "Which U.S. federal agency restricts advanced semiconductor sales to specific foreign markets?",
        "chain": "chips -SUBJECT_TO-> BIS / Commerce Dept",
        "answer_entities": [
            "bureau of industry and security", "u.s. department of commerce",
            "export administration regulations",
        ],
    },
]

TOP_K = 5
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "analytics" / "multihop_holdout_eval.md"
)


def fetch_expected_chunks(answer_entities: list[str]) -> set[str]:
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
    returned_ids = {r["chunk_id"] for r in retrieved}
    hits = returned_ids & expected
    n_hits = len(hits)
    return {
        "hit": 1 if n_hits > 0 else 0,
        "n_hits": n_hits,
        "recall": n_hits / min(len(expected), TOP_K) if expected else 0.0,
        "hit_ids": sorted(hits),
        "returned_ids": [r["chunk_id"] for r in retrieved],
    }


def main() -> None:
    print("="*70)
    print("HELD-OUT MULTI-HOP EVALUATION")
    print("DO NOT examine results until tuning on dev set is complete.")
    print("="*70)
    print(f"\n{len(HOLDOUT_QUERIES)} queries · top_k={TOP_K}\n")

    rows: list[dict] = []

    for q in HOLDOUT_QUERIES:
        print(f"\n--- {q['id']}: {q['question']}")
        print(f"    chain: {q['chain']}")

        expected = fetch_expected_chunks(q["answer_entities"])
        print(f"    expected chunks: {len(expected)}")

        if len(expected) == 0:
            print(f"    ⚠ WARNING: zero expected chunks — answer entities not in graph")

        vec_run = vector_search(q["question"], top_k_chunks=TOP_K)
        gph_run = graph_search(q["question"], top_k_chunks=TOP_K)
        hyb_run = hybrid_search(q["question"], top_k_chunks=TOP_K)

        vec_eval = evaluate(vec_run, expected)
        gph_eval = evaluate(gph_run, expected)
        hyb_eval = evaluate(hyb_run, expected)

        scores = {
            "vector": vec_eval["recall"],
            "graph":  gph_eval["recall"],
            "hybrid": hyb_eval["recall"],
        }
        max_recall = max(scores.values())
        top = [t for t, r in scores.items() if r == max_recall]
        winner = top[0] if len(top) == 1 else "tie"

        rows.append({
            "q": q, "expected": expected,
            "vec": vec_eval, "gph": gph_eval, "hyb": hyb_eval,
            "vec_run": vec_run, "gph_run": gph_run, "hyb_run": hyb_run,
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
    n_g = sum(1 for r in rows if r["winner"] == "graph")
    n_v = sum(1 for r in rows if r["winner"] == "vector")
    n_h = sum(1 for r in rows if r["winner"] == "hybrid")
    n_t = sum(1 for r in rows if r["winner"] == "tie")
    hyb_beats_vec  = sum(1 for r in rows if r["hyb"]["recall"] >  r["vec"]["recall"])
    hyb_equals_vec = sum(1 for r in rows if r["hyb"]["recall"] == r["vec"]["recall"])
    hyb_loses_vec  = sum(1 for r in rows if r["hyb"]["recall"] <  r["vec"]["recall"])

    # Report
    lines = [
        "# Held-Out Multi-hop Evaluation — 3-config (Phase C2-quater)",
        "",
        "**Held-out set authored before any tuning to bound test-set leakage.**",
        "Compare these numbers against `multihop_synthesized_eval.md` (dev set N=20)",
        "after tuning — large drop = overfit to dev set.",
        "",
        f"**N queries:** {len(rows)} · **top_k:** {TOP_K}",
        "**Tools:** vector_search, graph_search, hybrid_search (RRF k=60)",
        "",
        "---",
        "",
        "## Aggregate — 3-config",
        "",
        "| Metric | vector | graph | **hybrid** | hyb − vec |",
        "|---|---|---|---|---|",
        f"| Hit@5 | {vec_hits}/{len(rows)} | {gph_hits}/{len(rows)} | **{hyb_hits}/{len(rows)}** | "
        f"{hyb_hits - vec_hits:+d} |",
        f"| Avg Recall@5 | {vec_recall_avg:.3f} | {gph_recall_avg:.3f} | "
        f"**{hyb_recall_avg:.3f}** | {hyb_recall_avg - vec_recall_avg:+.3f} |",
        f"| Best-of-3 wins | {n_v} | {n_g} | **{n_h}** | — (ties: {n_t}) |",
        "",
        "### Pairwise: hybrid vs vector (primary thesis)",
        "",
        f"- **hybrid > vector**: {hyb_beats_vec}/{len(rows)} queries",
        f"- hybrid = vector: {hyb_equals_vec}/{len(rows)} queries",
        f"- hybrid < vector: {hyb_loses_vec}/{len(rows)} queries (RRF floor should give 0)",
        "",
        "**Verdict:** "
        + ("✓ hybrid ≥ vector on all queries (RRF floor holds)"
           if hyb_loses_vec == 0
           else f"⚠ hybrid < vector on {hyb_loses_vec} queries"),
        "",
        "---",
        "",
    ]

    for r in rows:
        q = r["q"]
        lines.append(f"## {q['id']}: `{q['question']}`")
        lines.append("")
        lines.append(f"- **type:** {q['type']}")
        lines.append(f"- **chain:** `{q['chain']}`")
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

    print(f"\n{'='*60}")
    print(f"HELD-OUT: vec hit={vec_hits}/{len(rows)} recall={vec_recall_avg:.3f}")
    print(f"        : gph hit={gph_hits}/{len(rows)} recall={gph_recall_avg:.3f}")
    print(f"        : hyb hit={hyb_hits}/{len(rows)} recall={hyb_recall_avg:.3f}")
    print(f"Best-of-3 wins → graph={n_g}  vector={n_v}  hybrid={n_h}  ties={n_t}")
    print(f"Hybrid vs Vector: beats={hyb_beats_vec} equal={hyb_equals_vec} "
          f"loses={hyb_loses_vec}")
    print(f"\n✓ Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
