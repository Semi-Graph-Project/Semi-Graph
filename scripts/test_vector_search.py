"""
End-to-end validation for Phase C2 `vector_search()`.

Runs the same 17 queries as test_graph_search.py so the two reports diff
directly. Writes a Markdown report to analytics/vector_search_validation.md.

Checks per query:
- Returns 5 chunks (vector RAG has no threshold — always top-k)
- All chunks have provenance fields (ticker, fiscal_year, section)
- No duplicate chunk_ids within a query result
- Deterministic across 2 consecutive runs (identical chunk_id order + scores)

Note vs graph_search: off-corpus queries DO return 5 chunks here (vector
RAG doesn't short-circuit). The diff between this and graph_search behavior
is the ablation signal we want to surface.
"""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

logging.getLogger("neo4j").setLevel("ERROR")

from semigraph.online.vector_search import vector_search


TEST_QUERIES: list[tuple[str, str]] = [
    # (group, query)
    ("Original C3 set",        "AMD"),
    ("Original C3 set",        "TSMC supply chain"),
    ("Original C3 set",        "Compare R&D Alphabet vs Meta 2023"),
    ("Original C3 set",        "china semiconductor ban"),

    ("Single-hop entity",      "NVIDIA Blackwell GPU architecture"),
    ("Single-hop entity",      "Micron HBM memory products"),
    ("Single-hop entity",      "CHIPS Act semiconductor manufacturing"),

    ("Multi-hop financial",    "Hopper data center segment revenue"),
    ("Multi-hop financial",    "Micron bit shipments average selling price"),
    ("Multi-hop financial",    "AMD gross margin trends"),

    ("Multi-hop relational",   "Xilinx acquisition impact on AMD"),
    ("Multi-hop relational",   "adverse economic conditions impact on revenue"),
    ("Multi-hop relational",   "NVIDIA AMD competitive landscape"),

    ("Geographic/regulatory",  "US export controls on AI chips to China"),
    ("Geographic/regulatory",  "Taiwan manufacturing dependency risk"),
    ("Geographic/regulatory",  "EU AI Act compliance requirements"),

    ("Edge case (off-corpus)", "qwerty zzz random nonsense xyz"),
]

TOP_K = 5
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "analytics" / "vector_search_validation.md"
)


def has_dup_chunks(results: list[dict]) -> bool:
    ids = [r["chunk_id"] for r in results]
    return len(ids) != len(set(ids))


def has_provenance(results: list[dict]) -> bool:
    required = {"chunk_id", "text", "ticker", "fiscal_year", "section", "score"}
    return all(required.issubset(r.keys()) for r in results)


def results_signature(results: list[dict]) -> list[tuple]:
    """Tuple (chunk_id, rounded_score) sequence — comparable across runs."""
    return [(r["chunk_id"], round(r["score"], 6)) for r in results]


def main() -> None:
    print(f"Testing vector_search on {len(TEST_QUERIES)} queries (top_k={TOP_K})\n")

    rows: list[dict] = []

    for group, query in TEST_QUERIES:
        print(f"\n--- [{group}] {query!r}")
        run1 = vector_search(query, top_k_chunks=TOP_K)
        run2 = vector_search(query, top_k_chunks=TOP_K)

        deterministic = results_signature(run1) == results_signature(run2)
        dup = has_dup_chunks(run1)
        prov = has_provenance(run1) if run1 else True

        tickers = Counter(r["ticker"] for r in run1)
        sections = Counter(r["section"] for r in run1)

        rows.append({
            "group": group,
            "query": query,
            "n_chunks": len(run1),
            "deterministic": deterministic,
            "dup_chunks": dup,
            "provenance_ok": prov,
            "ticker_dist": dict(tickers),
            "section_dist": dict(sections),
            "top_chunks": run1,
        })

        # Inline summary
        status = []
        status.append("det=YES" if deterministic else "det=NO")
        if dup:    status.append("DUP")
        if not prov and run1: status.append("MISSING_PROV")
        print(f"  → {len(run1)} chunks  ({', '.join(status)})")

    # Build report
    lines: list[str] = []
    lines.append("# vector_search() End-to-End Validation — Phase C2")
    lines.append("")
    lines.append(f"**Queries tested:** {len(TEST_QUERIES)}  ")
    lines.append(f"**top_k_chunks:** {TOP_K}  ")
    lines.append(f"**Pipeline:** query → BGE encode → chunk_embedding cosine top-k")
    lines.append(f"**Baseline:** Homogeneous Vector RAG (no graph signal, no threshold)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary stats
    n_total = len(rows)
    n_det = sum(1 for r in rows if r["deterministic"])
    n_dup = sum(1 for r in rows if r["dup_chunks"])
    n_prov = sum(1 for r in rows if r["provenance_ok"])
    n_empty = sum(1 for r in rows if r["n_chunks"] == 0)

    lines.append("## Acceptance Summary")
    lines.append("")
    lines.append(f"| Check | Pass | Fail | Note |")
    lines.append(f"|---|---|---|---|")
    lines.append(f"| Deterministic across 2 runs | {n_det}/{n_total} | {n_total - n_det} | byte-identical chunk_id + score |")
    lines.append(f"| No duplicate chunk_ids       | {n_total - n_dup}/{n_total} | {n_dup} | within a single query result |")
    lines.append(f"| Provenance fields present    | {n_prov}/{n_total} | {n_total - n_prov} | chunk_id/ticker/fiscal_year/section |")
    lines.append(f"| Non-empty results            | {n_total - n_empty}/{n_total} | {n_empty} | vector RAG returns top-k regardless |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-query detail
    current_group = None
    for r in rows:
        if r["group"] != current_group:
            current_group = r["group"]
            lines.append(f"## Group: {current_group}")
            lines.append("")

        lines.append(f"### `{r['query']}`")
        lines.append("")
        lines.append(f"- **chunks returned:** {r['n_chunks']}")
        lines.append(f"- **deterministic:** {'✓' if r['deterministic'] else '✗ FAIL'}")
        lines.append(f"- **no duplicate ids:** {'✓' if not r['dup_chunks'] else '✗ FAIL'}")
        lines.append(f"- **provenance ok:** {'✓' if r['provenance_ok'] else '✗ FAIL'}")
        lines.append(f"- **ticker distribution:** {r['ticker_dist']}")
        lines.append(f"- **section distribution:** {r['section_dist']}")
        lines.append("")

        if r["top_chunks"]:
            lines.append("| # | score | ticker | FY | section | text preview |")
            lines.append("|---|---|---|---|---|---|")
            for i, ch in enumerate(r["top_chunks"], start=1):
                preview = ch["text"][:90].replace("\n", " ").replace("|", "\\|")
                lines.append(
                    f"| {i} | {ch['score']:.3f} | {ch['ticker']} | "
                    f"{ch['fiscal_year']} | {ch['section']} | {preview}... |"
                )
        else:
            lines.append("_no chunks returned_")
        lines.append("")
        lines.append("---")
        lines.append("")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"Summary: det={n_det}/{n_total}  dup={n_dup}  "
          f"prov_ok={n_prov}/{n_total}  non_empty={n_total - n_empty}/{n_total}")
    print(f"✓ Report saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
