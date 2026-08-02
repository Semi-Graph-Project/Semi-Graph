
from __future__ import annotations

from typing import Optional

from semigraph.config import Config, get_config
from semigraph.connections import get_llm


_SYSTEM_PROMPT = """You are a semiconductor industry expert helping a retrieval system.

Given a user query, identify specific named entities (companies, products, places, regulations) that are IMPLICITLY referenced but not stated by name. Use only entities likely to appear in 10-K filings of the semiconductor corpus.

Corpus companies — when ANY of these is mentioned by full name, common name, product, or implicit description, ALWAYS emit its STOCK TICKER as one of the hint tokens (in addition to readable names):

  NVDA = NVIDIA  (GeForce / RTX / Hopper / Blackwell / data center GPUs)
  AMD  = Advanced Micro Devices  (Ryzen / EPYC / Radeon / Instinct MI)
  MU   = Micron Technology  (HBM / DRAM / NAND / Crucial)
  INTC = Intel  (Xeon / Core / Mobileye / Intel Foundry / Altera)
  AVGO = Broadcom  (custom ASIC / VMware / networking switches)
  QCOM = Qualcomm  (Snapdragon / 5G modems / mobile SoC)
  AMAT = Applied Materials  (deposition / etch equipment)
  LRCX = Lam Research  (etch / strip / clean equipment)
  KLAC = KLA  (inspection / metrology equipment)
  TXN  = Texas Instruments  (analog / embedded processors)

External entities (TSMC, ASML, Samsung, SK Hynix, Apple, Microsoft, customers, regulators, geographies) — emit the readable name as-is, not as a ticker.

Output ONLY a space-separated list of hint tokens. No explanations, no preamble, no quotes, no newlines.

Examples:
Query: What political risks affect the home country of the leading pure-play semiconductor foundry?
Output: TSMC Taiwan pure-play foundry geopolitical

Query: Which AI lab partners with the EPYC processor maker?
Output: AMD OpenAI Microsoft Sony EPYC

Query: Where is the developer of Ryzen processors headquartered?
Output: AMD Santa Clara California Ryzen

Query: What graphics product line does NVIDIA offer to compete with AMD's Radeon?
Output: NVDA AMD GeForce RTX Radeon RDNA

Query: Compare Intel's and Broadcom's R&D spending.
Output: INTC AVGO research development semiconductor

Query: What is Nvidia's current stock price?
Output: NVDA stock price quote

Query: Which memory supplier provides HBM to data center GPUs?
Output: MU Micron SK Hynix Samsung HBM NVDA

Query: ราคาหุ้น Qualcomm ตอนนี้
Output: QCOM Qualcomm stock price quote

Query: บริษัทผลิตเครื่อง EUV lithography
Output: ASML EUV lithography equipment"""


def expand_query(query: str, cfg: Optional[Config] = None) -> str:
    """Expand query with implicit entity hints via LLM world knowledge.

    Args:
        query: Original natural-language query.
        cfg:   Optional Config; defaults to cached singleton.

    Returns:
        `f"{query} {hints}"` — original preserved + entity hints appended.
        Falls back to original query on LLM error or invalid output, so a
        call site can drop-in replace `query` without extra guards.
    """
    if not query.strip():
        return query

    cfg = cfg or get_config()
    llm = get_llm(cfg)
    try:
        response = llm.invoke([
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\nOutput:"},
        ])
        hints = (response.content if hasattr(response, "content") else str(response)).strip()
        # Sanity guard: drop noise / refusals / runaway outputs
        if len(hints) < 2 or len(hints) > 200 or "\n" in hints:
            print(f"[expand] WARN: invalid hint shape ({len(hints)} chars), using original")
            return query
        expanded = f"{query} {hints}"
        print(f"[expand] hints={hints!r}")
        return expanded
    except Exception as e:
        print(f"[expand] WARN: LLM failed ({type(e).__name__}: {e}), using original")
        return query


if __name__ == "__main__":
    test_queries = [
        "What political risks affect the home country of the leading pure-play semiconductor foundry?",
        "Where is the developer of Ryzen processors headquartered?",
        "Which gaming console maker partners with the Ryzen processor company?",
        "What graphics product line does AMD offer to compete with NVIDIA's RTX series?",
        "AMD",  # short query — see how LLM handles
    ]
    for q in test_queries:
        print(f"\n--- Original: {q}")
        print(f"    Expanded: {expand_query(q)}")
