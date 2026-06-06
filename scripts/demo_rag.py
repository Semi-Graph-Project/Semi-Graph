"""
Interactive end-to-end RAG demo — Phase D pre-prototype.

REPL loop: user types a question (or picks a numbered suggestion) → system
runs hybrid_search → DeepSeek generates a grounded answer → results print
to console.

Workflow during a live demo:
  1. Open this script. The suggested-queries menu prints first.
  2. Advisor picks (or you pick) by number for quick highlight queries,
     OR advisor types their own question for an unscripted test.
  3. System returns retrieved chunks + generated answer.
  4. Loop until 'q' / 'quit' / 'exit'.

Run:
    conda run -n senior_project python scripts/demo_rag.py

Scope of temporal demo:
  Chunks carry `fiscal_year` (FY2023–2026). EVENT entities sometimes embed
  the year in their name ("2024 restructuring plan"). This is enough for
  event-evolution questions ("what changed between FY2024 and FY2026?").
  Financial-statement trends (revenue, margin) are NOT supported — Item 8
  / Item 5 are excluded from extraction on purpose; numeric data arrives
  via the `financial_query` tool in Phase C3 (PostgreSQL + SEC XBRL).
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

logging.getLogger("neo4j").setLevel("ERROR")
logging.getLogger("httpx").setLevel("WARNING")

from semigraph.config import get_config
from semigraph.connections import get_llm
from semigraph.online.vector_search import vector_search
from semigraph.online.graph_search import graph_search
from semigraph.online.hybrid_search import hybrid_search
from semigraph.online.financial_search import financial_search
from semigraph.online.news_search import news_search


# Retrieval-engine dispatch. All five return the same chunk-dict shape
# ({chunk_id, text, ticker, fiscal_year, section, score}), so they are
# interchangeable behind rag_answer() with no downstream change.
# Financial is Phase F.v1 (Finnhub financials/quotes); News is Phase E.v1
# (Finnhub real-time company news). Each emits a distinct `section` prefix
# so the LLM can attribute the source.
RETRIEVERS = {
    "vector": vector_search,
    "graph": graph_search,
    "hybrid": hybrid_search,
    "financial": financial_search,
    "news": news_search,
}


SYSTEM_PROMPT = """You are a financial analyst answering questions about semiconductor companies.

You must use ONLY the CONTEXT provided. Never use prior knowledge or outside
facts. The CONTEXT may come from three source kinds, distinguishable by the
chunk's `section` tag:
  • SEC 10-K filings — sections "Item_1" (Business), "Item_1A" (Risk Factors),
    "Item_7" (MD&A). Narrative + qualitative.
  • Finnhub API snapshots — sections starting with "Financial_" (e.g.
    "Financial_financials_annual", "Financial_key_metrics", "Financial_quote").
    Real-time / latest-period numeric snapshots. These ARE authoritative for
    revenue figures, margins, P/E, current price, etc. — treat them with the
    same trust as 10-K text.
  • Finnhub real-time news — section "News_finnhub". Company news headlines +
    summaries from the last 90 days (or full article body when depth=full).
    These ARE authoritative for recent events, announcements, and market
    reactions that 10-K filings cannot contain because of their annual cadence.

Classify the question into ONE of three cases and respond accordingly. When
unsure between cases, PREFER A over B, and B over C — only fall to C as a
last resort.

── CASE A — the answer is stated EXPLICITLY in the context ──
One or more chunks state the answer in words. Give it directly, grounded,
with citations.

── CASE B — the answer is NOT stated verbatim, but CAN be reasoned from the context ──
This is the DEFAULT whenever reasoning is needed. It covers:
  • hypothetical / counterfactual ("what happens if...", "what if...")
  • relational ("are X and Y competitors?", "is X a supplier of Y?")
  • comparison ("compare R&D of X vs Y")
  • implication / significance ("why does X matter to Y", "how would X affect Y")
Trigger Case B whenever the context DESCRIBES the entities, products,
segments, risk factors, competition, or strategy involved — even if it never
states the exact answer sentence. 10-K Business / Risk Factor / MD&A passages
ARE valid material to reason from. Example: if the context says Micron is a
memory company and Intel Foundry competes with foundries, you CAN reason that
Intel and Micron operate in different segments.
Respond in TWO parts:
  1. First, ONE sentence stating the filings do not state this explicitly.
  2. Then a new line with EXACTLY this header (translated to the answer's
     language) followed by the reasoned answer:
        English:  "▸ Inference (reasoned from related 10-K context):"
        Thai:     "▸ อนุมานจากข้อมูลที่เกี่ยวข้องในเอกสาร 10-K:"
     Under the header, give a grounded inference — every claim must trace to
     a retrieved chunk, with citations. Do NOT invent facts; only connect
     what the context actually states.

── CASE C — the answer is categorically absent ──
Use ONLY when (a) the question asks for a concrete fact that no reasoning over
the context could produce — an exact figure never mentioned, a specific
name/date absent from every chunk — OR (b) every chunk is about entirely
unrelated companies/topics. If the context describes the entities in the
question at all, it is Case B, NOT Case C. Note: real-time stock prices and
recent financial metrics MAY appear in "Financial_*" chunks — check those
before declaring Case C for numeric questions.
Reply with ONLY this line (no inference section):
  English:  "The provided context does not contain information to answer this question."
  Thai:     "บริบทที่ให้มาไม่มีข้อมูลเพียงพอสำหรับตอบคำถามนี้"

GENERAL RULES (all cases):
- Cite ticker + fiscal year / data source for every claim. For 10-K chunks use
  "Intel FY2024 10-K reports...". For Financial_* chunks use "AMD Finnhub
  snapshot shows..." or "NVDA latest quarter (Finnhub) reports...". For
  News_finnhub chunks use "AMD recent news (Finnhub, <year>) reports..." and
  prefer the most recent article when multiple chunks address the same topic.
- Match the question's language: Thai question → Thai answer; English → English.
- Keep ticker symbols, product names, and technical terms in English even in a
  Thai answer (e.g. "Mobileye", "Intel 18A", "EPYC" — do NOT transliterate).
- Be concise — 3 to 5 sentences per section.
"""


TRANSLATE_PROMPT = """You are a translator specialized in semiconductor and financial domain.

Translate the following Thai question to English so it can be matched against U.S. SEC 10-K filings from NVIDIA, AMD, Micron, ASML, and Intel.

Rules:
- Output ONLY the English translation. No commentary, no quotes, no "Here is the translation".
- Preserve technical terms in English (e.g., "ซับซิเดียรี่" → "subsidiary", "พาร์ทเนอร์โรงงานหล่อ" → "foundry partner").
- Keep ticker symbols and product names as-is (Intel, NVIDIA, Mobileye, Xeon, etc.).
- Keep fiscal-year references in English form ("ปี 2024" → "FY2024").

THAI QUESTION:
{thai_query}

ENGLISH TRANSLATION:"""


# Pre-canned queries selected to exercise different retrieval patterns.
# Each is tagged with its dev-set metric when applicable, so during the
# demo you can connect "shown answer" to "measured Recall@5".
SUGGESTED_QUERIES = [
    {
        "label": "Graph-favoring multi-hop (subsidiary lookup)",
        "query": "Which autonomous driving subsidiary does Intel operate, and what products does it make?",
        "dev_note": "Dev-set Q23 · Hybrid R@5=0.40, Graph R@5=1.00",
    },
    {
        "label": "Vector-favoring topical (geo + macro risk)",
        "query": "What political risks affect the home country of the leading pure-play semiconductor foundry?",
        "dev_note": "Dev-set Q4 · Hybrid R@5=0.80, Vector R@5=1.00",
    },
    {
        "label": "Open-ended cross-company (NOT in dev set)",
        "query": "Compare the R&D investment priorities between Intel and AMD as disclosed in their recent 10-K filings.",
        "dev_note": "Free-form — tests generalization beyond dev set",
    },
    {
        "label": "Temporal — event evolution across fiscal years",
        "query": "What major restructuring plans, divestitures, or strategic events has Intel announced across its FY2024 to FY2026 10-K filings?",
        "dev_note": "Temporal — uses fiscal_year on chunks (no revenue trends — those need Phase C3)",
    },
    {
        "label": "Out-of-corpus refusal test (should refuse)",
        "query": "What is the current stock price of NVIDIA and how did it perform last week?",
        "dev_note": "Stress test — real-time price not in static 10-K filings; system should refuse",
    },
    {
        "label": "Thai input — same Q23 in Thai",
        "query": "บริษัทลูกด้าน autonomous driving ของ Intel คือบริษัทอะไร และทำผลิตภัณฑ์อะไรบ้าง",
        "dev_note": "Thai entry point — auto-translated to English for retrieval, LLM answers in Thai",
    },
    {
        "label": "Thai input — subsidiary's products",
        "query": "บริษัทลูกด้านการขับขี่อัตโนมัติของ Intel มีผลิตภัณฑ์ระบบช่วยเหลือผู้ขับขี่ (ADAS) อะไรบ้าง",
        "dev_note": "Dev-set Q30 · stability-tested: graph answers 3/3; vector inconsistent — contrast not guaranteed",
    },
    {
        "label": "Thai input — consumer brand lookup (Graph wins)",
        "query": "บริษัทผู้ผลิตชิปหน่วยความจำสัญชาติอเมริกันที่ผลิต HBM3E ขายผลิตภัณฑ์หน่วยความจำและสตอเรจสำหรับผู้บริโภคทั่วไปภายใต้แบรนด์ชื่ออะไร",
        "dev_note": "Dev-set Q33 · stability-tested: vector refuses, graph answers 3/3 (Crucial)",
    },
    {
        "label": "Thai input — fab locations (Graph more complete)",
        "query": "Intel มีโรงงานผลิตเวเฟอร์ (wafer fab) ตั้งอยู่ในรัฐใดบ้างของสหรัฐอเมริกา",
        "dev_note": "Dev-set Q25 · stability-tested: graph answers 3/3 (3-4 states), vector ~2 — completeness contrast",
    },
    # ── Financial mode (Phase F.v1 — Finnhub direct API) ────────────────────
    {
        "label": "Financial — NVDA latest revenue + margins",
        "query": "What is NVDA's latest annual revenue and gross/operating margins?",
        "dev_note": "Financial v1 · Finnhub financials_annual snapshot",
    },
    {
        "label": "Financial — AMD current price + P/E",
        "query": "What is AMD's current stock price and P/E ratio?",
        "dev_note": "Financial v1 · Finnhub quote + key_metrics",
    },
    {
        "label": "Financial — INTC operating margin",
        "query": "Show INTC operating margin and net income for the latest fiscal year.",
        "dev_note": "Financial v1 · single-year only (v2 will support multi-year via SQL)",
    },
    # ── News mode (Phase E.v1 — Finnhub News API) ───────────────────────────
    {
        "label": "News — latest NVDA news",
        "query": "What is the latest news about NVDA this week?",
        "dev_note": "News v1 · Finnhub company_news (90-day window, headline depth)",
    },
    {
        "label": "News — AMD recent announcements",
        "query": "What has AMD announced recently?",
        "dev_note": "News v1 · headline+summary; switch depth='full' for body text",
    },
    {
        "label": "News — Thai query (LLM expansion → QCOM)",
        "query": "ข่าวล่าสุดของ Qualcomm มีอะไรบ้าง",
        "dev_note": "News v1 · Thai intent gate + LLM ticker resolution",
    },
]


def _detect_thai(text: str) -> bool:
    """Return True if text contains at least one Thai-script character.

    Thai Unicode block: U+0E00 .. U+0E7F. We require ≥1 char in this range
    rather than a percentage threshold because mixed Thai/English questions
    ("Intel มี subsidiary อะไรบ้าง") should still trigger translation.
    """
    return any("฀" <= c <= "๿" for c in text)


def _translate_to_en(thai_query: str, llm) -> str:
    """Translate Thai query to English via the same DeepSeek LLM client.

    One extra round-trip (~1s) — accepted because BGE-base-en-v1.5 does not
    handle Thai input (English-only training corpus), so retrieval requires
    English regardless.
    """
    response = llm.invoke([
        ("human", TRANSLATE_PROMPT.format(thai_query=thai_query)),
    ])
    return response.content.strip()


def format_context(chunks: list[dict], max_chars_per_chunk: int = 1200) -> str:
    """Concatenate top-k chunks with citation headers for LLM grounding."""
    parts = []
    for i, c in enumerate(chunks, 1):
        header = (
            f"[{i}] {c['ticker']} FY{c['fiscal_year']} {c['section']} "
            f"(score={c['score']:.3f})"
        )
        body = c["text"][:max_chars_per_chunk]
        if len(c["text"]) > max_chars_per_chunk:
            body += "...[truncated]"
        parts.append(f"{header}\n{body}")
    return "\n\n---\n\n".join(parts)


def rag_answer(query: str, top_k: int, cfg, llm, mode: str = "hybrid") -> dict:
    """One end-to-end RAG call. Returns retrieval + answer + timings.

    `mode` picks the retrieval engine — "vector", "graph", or "hybrid"
    (default). All three return the same chunk-dict shape, so generation
    downstream is identical regardless of which engine ran.

    If `query` contains Thai script, an extra translation step converts it
    to English for retrieval (BGE-en cannot embed Thai). The ORIGINAL
    Thai query is still sent to the generation LLM along with the English
    context — DeepSeek-V4 is multilingual and answers in the question's
    language directly, so we avoid an output-translation round-trip.
    """
    is_thai = _detect_thai(query)

    t_translate = 0.0
    if is_thai:
        t0 = time.time()
        query_for_retrieval = _translate_to_en(query, llm)
        t_translate = time.time() - t0
    else:
        query_for_retrieval = query

    retriever = RETRIEVERS.get(mode, hybrid_search)
    t0 = time.time()
    chunks = retriever(query_for_retrieval, top_k_chunks=top_k, cfg=cfg)
    t_retrieve = time.time() - t0

    if not chunks:
        return {
            "is_thai": is_thai,
            "mode": mode,
            "query_original": query,
            "query_translated": query_for_retrieval if is_thai else None,
            "chunks": [],
            "answer": "[Retrieval returned 0 chunks — query may be too far from corpus.]",
            "t_translate_s": t_translate,
            "t_retrieve_s": t_retrieve,
            "t_generate_s": 0.0,
        }

    context = format_context(chunks)
    lang_tag = "Thai" if is_thai else "English"
    user_msg = (
        f"CONTEXT (excerpts from 10-K filings, English):\n{context}\n\n"
        f"QUESTION ({lang_tag}): {query}\n\n"
        f"ANSWER (in {lang_tag}, following the rules above):"
    )

    t0 = time.time()
    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", user_msg),
    ])
    t_generate = time.time() - t0

    return {
        "is_thai": is_thai,
        "mode": mode,
        "query_original": query,
        "query_translated": query_for_retrieval if is_thai else None,
        "chunks": chunks,
        "answer": response.content,
        "t_translate_s": t_translate,
        "t_retrieve_s": t_retrieve,
        "t_generate_s": t_generate,
    }


def print_result(query: str, result: dict, dev_note: str | None = None) -> None:
    print(f"\n{'=' * 72}")
    print(f"Q: {query}")
    if result.get("is_thai"):
        print(f"   ↳ translated for retrieval ({result['t_translate_s']:.2f}s): "
              f"{result['query_translated']}")
    print('=' * 72)

    print(f"\n[Retrieved {len(result['chunks'])} chunks in {result['t_retrieve_s']:.2f}s]")
    for i, c in enumerate(result["chunks"], 1):
        preview = c["text"][:120].replace("\n", " ")
        print(f"  [{i}] {c['ticker']} FY{c['fiscal_year']} {c['section']:<10} "
              f"score={c['score']:.3f}")
        print(f"      {preview}...")

    print(f"\n[Answer (generated in {result['t_generate_s']:.2f}s)]")
    print(result["answer"])

    if dev_note:
        print(f"\n[{dev_note}]")


def print_menu() -> None:
    print("\n" + "─" * 72)
    print("SUGGESTED QUERIES (type the number, or type a free-form question)")
    print("─" * 72)
    for i, q in enumerate(SUGGESTED_QUERIES, 1):
        print(f"  {i}. [{q['label']}]")
        print(f"     {q['query']}")
    print("\n  m → show this menu again")
    print("  q → quit")
    print("─" * 72)


def main() -> None:
    print("Loading config + LLM client...")
    cfg = get_config()
    llm = get_llm(cfg)

    print(f"\nSemiGraph RAG demo")
    print(f"  Retriever : hybrid_search (RRF k=60, top-5)")
    print(f"  Generator : {cfg.llm_model} @ {cfg.llm_base_url}")
    print(f"  Corpus    : 5 companies × 3 fiscal years = 742 chunks")

    print_menu()

    while True:
        try:
            user_in = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            break

        if not user_in:
            continue

        # ----- control commands -----
        if user_in.lower() in {"q", "quit", "exit"}:
            print("bye.")
            break
        if user_in.lower() == "m":
            print_menu()
            continue

        # ----- numbered suggestion -----
        if user_in.isdigit():
            idx = int(user_in) - 1
            if 0 <= idx < len(SUGGESTED_QUERIES):
                q_spec = SUGGESTED_QUERIES[idx]
                query = q_spec["query"]
                dev_note = q_spec["dev_note"]
            else:
                print(f"  ! index out of range (1..{len(SUGGESTED_QUERIES)})")
                continue
        # ----- free-form query -----
        else:
            query = user_in
            dev_note = None

        try:
            result = rag_answer(query, top_k=8, cfg=cfg, llm=llm)
        except Exception as e:
            print(f"  ! error during retrieval/generation: {e}")
            continue

        print_result(query, result, dev_note)


if __name__ == "__main__":
    main()
