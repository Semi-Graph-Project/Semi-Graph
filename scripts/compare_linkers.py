"""
Compare Query-to-Node (query_to_seeds) vs Query-to-Triple (query_to_triple_seeds)
linkers on a 4-query suite, computing proxy metrics that don't require ground
truth. Writes a Markdown report to analytics/linker_comparison.md.

Metrics (per query, per mode):
- seed_count          : how many seeds the linker emits
- seed_type_diversity : distinct entity types across seeds
- multi_hop_pct       : fraction of PPR top-10 that wasn't a seed (walk expansion)
- hub_leakage         : PPR mass on known global hubs (china, revenue, ...)
- type_entropy        : Shannon entropy of type distribution in PPR top-10
- top3_concentration  : sum(top-3 scores) / sum(top-10 scores)

For seed_type_diversity / multi_hop_pct / type_entropy: higher = better
For hub_leakage / top3_concentration            : lower  = better
"""
from __future__ import annotations

import logging
import math
from collections import Counter
from pathlib import Path

logging.getLogger("neo4j").setLevel("ERROR")

from semigraph.online.seed import query_to_seeds, query_to_triple_seeds
from semigraph.online.ppr import run_ppr


QUERIES: list[str] = [
    # --- Original 4 (Phase C1b C3 validation set) ---
    "AMD",                                          # 1-hop, ORG anchor
    "TSMC supply chain",                            # multi-hop, COMP + RISK_FACTOR
    "Compare R&D Alphabet vs Meta 2023",            # off-corpus boundary test
    "china semiconductor ban",                      # GPE + EVENT

    # --- NVDA coverage (added 2026-05-17) ---
    "NVIDIA Blackwell GPU architecture",            # 1-hop, PRODUCT
    "Hopper data center segment revenue",           # multi-hop, SEGMENT -> FIN_METRIC

    # --- MU coverage ---
    "Micron HBM memory products",                   # 1-hop, PRODUCT
    "Micron bit shipments average selling price",   # multi-hop, FIN_METRIC chain

    # --- Regulatory anchor ---
    "CHIPS Act semiconductor manufacturing",        # 1-hop, REGULATORY_REQUIREMENT
    "US export controls on AI chips to China",      # multi-hop, EVENT + GPE

    # --- M&A and macro ---
    "Xilinx acquisition impact on AMD",             # multi-hop, EVENT -> ORG
    "adverse economic conditions impact on revenue",  # multi-hop, RISK_FACTOR -> FIN_METRIC
]

# Hubs we've seen dominate vanilla PageRank in prior runs — low score on these
# means personalization is working
HUB_ENTITIES: set[str] = {
    "china",
    "united states",
    "revenue",
    "gross margin",
    "customers",
    "consumer",
    "the_filer",
    "operating expenses",
}

OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "analytics" / "linker_comparison.md"
)

TOP_K_PPR = 10


def shannon_entropy(items: list[str]) -> float:
    """Shannon entropy of a categorical distribution (bits). Higher = more uniform."""
    if not items:
        return 0.0
    counts = Counter(items)
    total = len(items)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def compute_metrics(seeds: list[dict], ppr_top: list[dict]) -> dict:
    seed_names = {s["name"] for s in seeds}
    seed_types = {s.get("type") for s in seeds if s.get("type")}
    top_names = [r["name"] for r in ppr_top]
    top_types = [r["type"] for r in ppr_top]
    top_scores = [r["score"] for r in ppr_top]

    multi_hop = sum(1 for n in top_names if n not in seed_names)
    multi_hop_pct = multi_hop / len(top_names) if top_names else 0.0

    total_mass = sum(top_scores) if top_scores else 1.0
    hub_mass = sum(r["score"] for r in ppr_top if r["name"] in HUB_ENTITIES)
    hub_leakage = hub_mass / total_mass if total_mass > 0 else 0.0

    top3_mass = sum(top_scores[:3])
    concentration = top3_mass / total_mass if total_mass > 0 else 0.0

    return {
        "seed_count": len(seeds),
        "seed_type_diversity": len(seed_types),
        "multi_hop_pct": multi_hop_pct,
        "hub_leakage": hub_leakage,
        "type_entropy": shannon_entropy(top_types),
        "top3_concentration": concentration,
    }


def run_one(query: str, linker_fn, label: str) -> dict:
    print(f"  [{label}] linking...", end=" ", flush=True)
    seeds = linker_fn(query)
    print(f"seeds={len(seeds)}", end=" → ", flush=True)
    if not seeds:
        print("(empty — short-circuit)")
        return {
            "seeds": [],
            "ppr_top": [],
            "metrics": {
                "seed_count": 0,
                "seed_type_diversity": 0,
                "multi_hop_pct": 0.0,
                "hub_leakage": 0.0,
                "type_entropy": 0.0,
                "top3_concentration": 0.0,
            },
        }
    ppr_top = run_ppr(seeds, top_k=TOP_K_PPR)
    print(f"ppr top-{len(ppr_top)}")
    return {
        "seeds": seeds,
        "ppr_top": ppr_top,
        "metrics": compute_metrics(seeds, ppr_top),
    }


# metric_name → (direction, is_int)
# direction: "high" = higher is better, "low" = lower is better
METRIC_SPEC = {
    "seed_count": ("info", True),
    "seed_type_diversity": ("high", True),
    "multi_hop_pct": ("high", False),
    "hub_leakage": ("low", False),
    "type_entropy": ("high", False),
    "top3_concentration": ("low", False),
}


def fmt_metric(name: str, value) -> str:
    _, is_int = METRIC_SPEC[name]
    return f"{value}" if is_int else f"{value:.3f}"


def winner(name: str, n_v, t_v) -> str:
    direction, _ = METRIC_SPEC[name]
    if direction == "info":
        return "—"
    if abs(n_v - t_v) < 1e-9:
        return "tie"
    if direction == "high":
        return "🟢 Triple" if t_v > n_v else "🔵 Node"
    return "🟢 Triple" if t_v < n_v else "🔵 Node"


def format_markdown(results: dict) -> str:
    lines: list[str] = []
    lines.append("# Linker Comparison Report — Query-to-Node vs Query-to-Triple")
    lines.append("")
    lines.append(f"**Method:** {len(QUERIES)}-query suite × 2 linker modes, proxy metrics (no ground truth)  ")
    lines.append("**Reference:** HippoRAG v2 (ICML '25) Table 4 — Query-to-Triple +12.5% R@5 over Query-to-Node  ")
    lines.append(f"**PPR top-k:** {TOP_K_PPR}, damping=0.85, max_iter=20  ")
    lines.append("**Linker defaults:** both use top_k=5, min_similarity=0.6  ")
    lines.append("")
    lines.append("Higher-is-better: `seed_type_diversity`, `multi_hop_pct`, `type_entropy`  ")
    lines.append("Lower-is-better: `hub_leakage`, `top3_concentration`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-query detail
    for query in QUERIES:
        node_r = results[query]["node"]
        triple_r = results[query]["triple"]
        lines.append(f"## Query: `{query}`")
        lines.append("")

        # Seeds
        lines.append("### Seeds")
        lines.append("")
        lines.append("| # | Query-to-Node | Query-to-Triple |")
        lines.append("|---|---|---|")
        max_rows = max(len(node_r["seeds"]), len(triple_r["seeds"]))
        for i in range(max_rows):
            n = ""
            t = ""
            if i < len(node_r["seeds"]):
                s = node_r["seeds"][i]
                n = f"{s['name']} *({s.get('type','?')})*"
            if i < len(triple_r["seeds"]):
                s = triple_r["seeds"][i]
                t = f"{s['name']} *({s.get('type','?')})*"
            lines.append(f"| {i+1} | {n} | {t} |")
        lines.append("")

        # PPR top-10
        lines.append(f"### PPR top-{TOP_K_PPR}")
        lines.append("")
        lines.append("| # | Query-to-Node | Query-to-Triple |")
        lines.append("|---|---|---|")
        max_rows = max(len(node_r["ppr_top"]), len(triple_r["ppr_top"]))
        for i in range(max_rows):
            n = ""
            t = ""
            if i < len(node_r["ppr_top"]):
                r = node_r["ppr_top"][i]
                n = f"{r['name']} *({r['type']})* `{r['score']:.3f}`"
            if i < len(triple_r["ppr_top"]):
                r = triple_r["ppr_top"][i]
                t = f"{r['name']} *({r['type']})* `{r['score']:.3f}`"
            lines.append(f"| {i+1} | {n} | {t} |")
        lines.append("")

        # Metrics
        lines.append("### Metrics")
        lines.append("")
        lines.append("| Metric | Query-to-Node | Query-to-Triple | Winner |")
        lines.append("|---|---|---|---|")
        for m in METRIC_SPEC:
            n_v = node_r["metrics"][m]
            t_v = triple_r["metrics"][m]
            lines.append(
                f"| {m} | {fmt_metric(m, n_v)} | {fmt_metric(m, t_v)} | {winner(m, n_v, t_v)} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")

    # Aggregate
    lines.append(f"## Aggregate (mean across {len(QUERIES)} queries)")
    lines.append("")
    lines.append("| Metric | Query-to-Node | Query-to-Triple | Delta | Winner |")
    lines.append("|---|---|---|---|---|")
    for m in METRIC_SPEC:
        node_vals = [results[q]["node"]["metrics"][m] for q in QUERIES]
        triple_vals = [results[q]["triple"]["metrics"][m] for q in QUERIES]
        node_avg = sum(node_vals) / len(node_vals)
        triple_avg = sum(triple_vals) / len(triple_vals)
        delta = triple_avg - node_avg
        _, is_int = METRIC_SPEC[m]
        # Keep mean as float even for "int" metrics (seed_count avg can be fractional)
        node_s = f"{node_avg:.2f}" if is_int else f"{node_avg:.3f}"
        triple_s = f"{triple_avg:.2f}" if is_int else f"{triple_avg:.3f}"
        delta_s = f"{delta:+.3f}" if not is_int else f"{delta:+.2f}"
        lines.append(
            f"| {m} | {node_s} | {triple_s} | {delta_s} | {winner(m, node_avg, triple_avg)} |"
        )
    lines.append("")

    # Verdict
    wins_triple = 0
    wins_node = 0
    n = len(QUERIES)
    for m, (direction, _) in METRIC_SPEC.items():
        if direction == "info":
            continue
        node_avg = sum(results[q]["node"]["metrics"][m] for q in QUERIES) / n
        triple_avg = sum(results[q]["triple"]["metrics"][m] for q in QUERIES) / n
        w = winner(m, node_avg, triple_avg)
        if w.endswith("Triple"):
            wins_triple += 1
        elif w.endswith("Node"):
            wins_node += 1
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"- Comparable metrics: 5 (excluding `seed_count` info-only)")
    lines.append(f"- Query-to-Triple wins: **{wins_triple}**")
    lines.append(f"- Query-to-Node wins: **{wins_node}**")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    results: dict[str, dict] = {}
    print(f"Comparing linkers across {len(QUERIES)} queries...\n")
    for q in QUERIES:
        print(f"--- {q!r}")
        results[q] = {
            "node": run_one(q, query_to_seeds, "node"),
            "triple": run_one(q, query_to_triple_seeds, "triple"),
        }
        print()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(format_markdown(results), encoding="utf-8")
    print(f"✓ Report saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
