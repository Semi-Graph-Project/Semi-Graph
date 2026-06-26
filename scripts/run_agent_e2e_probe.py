from __future__ import annotations

import time

from semigraph.agent.graph import build_agent


QUERIES = [
    (
        "multihop_equipment_to_downstream_benefit",
        "When equipment manufacturers like Applied Materials, Lam Research, or KLA enable factories to increase yields or shrink manufacturing processes, how do downstream companies like AMD or NVIDIA benefit commercially?"
    ),
    (
        "multihop_intel_mobileye_products",
        "Which autonomous driving subsidiary does Intel operate, and what products does it make?",
    ),
    (
        "multihop_foundry_country_political_risk",
        "What political risks affect the home country of the leading pure-play semiconductor foundry?",
    ),
    (
        "multihop_memory_hbm_consumer_brand",
        "Which American memory chip company produces HBM3E, and what consumer brand does it use for memory and storage products?",
    ),
]


def summarize_update(node_name: str, update: dict) -> str:
    if "next_tool" in update:
        return f"next_tool={update['next_tool']}"
    if "subqueries" in update:
        return f"subqueries={update['subqueries']}"
    if "latest_chunks" in update:
        log = (update.get("tool_call_log") or [{}])[-1]
        return (
            f"tool={log.get('tool')} n_chunks={len(update.get('latest_chunks') or [])} "
            f"status={log.get('status')} query={log.get('query')!r}"
        )
    if "observation_text" in update:
        return f"observation={update['observation_text'][:180]!r}"
    if "sufficient" in update:
        return (
            f"sufficient={update.get('sufficient')} stop_reason={update.get('stop_reason')} "
            f"retry_query={update.get('retry_query')!r}"
        )
    if "completed_subqueries" in update and "final_answer" not in update:
        return f"completed_subqueries={update['completed_subqueries']}"
    if "final_answer" in update:
        return (
            f"final_answer={update.get('final_answer', '')[:220]!r} "
            f"citations={len(update.get('citation_map') or [])}"
        )
    return str(update)[:220]


def summarize_citation_map(citations: list[dict]) -> list[dict]:
    compact = []
    for item in citations:
        text = str(item.get("text") or "").replace("\n", " ")
        compact.append({
            "citation_index": item.get("citation_index"),
            "chunk_id": item.get("chunk_id"),
            "ticker": item.get("ticker"),
            "fiscal_year": item.get("fiscal_year"),
            "section": item.get("section"),
            "score": item.get("score"),
            "preview": text[:260],
        })
    return compact


def main() -> None:
    graph = build_agent()

    for label, query in QUERIES:
        print(f"\n=== {label} ===", flush=True)
        print(f"QUERY: {query}", flush=True)
        t0 = time.time()
        try:
            final_state = None
            for event in graph.stream(
                {"original_query": query},
                stream_mode="updates",
                config={"recursion_limit": 50},
            ):
                for node_name, update in event.items():
                    final_state = update
                    elapsed = round(time.time() - t0, 2)
                    print(
                        f"[{elapsed:>6.2f}s] {node_name}: {summarize_update(node_name, update)}",
                        flush=True,
                    )

            print(f"--- completed in {time.time() - t0:.2f}s ---", flush=True)
            if final_state:
                print(f"FINAL_ANSWER: {final_state.get('final_answer', '')}", flush=True)
                print(
                    f"CITATION_MAP: {summarize_citation_map(final_state.get('citation_map', []))}",
                    flush=True,
                )
        except Exception as exc:
            print(
                f"ERROR after {time.time() - t0:.2f}s: {type(exc).__name__}: {exc}",
                flush=True,
            )


if __name__ == "__main__":
    main()
