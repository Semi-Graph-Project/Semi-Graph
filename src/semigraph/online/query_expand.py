"""
Phase C1c-bis — LLM Query Expansion (Tier 1 fix for seed-step failure).

Problem (diagnosed from multi-hop benchmark, Phase C2-bis):
  BGE embeddings cannot bridge abstract query descriptors ("leading
  pure-play foundry") to short entity names ("tsmc"). Cosine similarity
  is low even though the answer is structurally reachable in the KG via
  a SUPPLIES/PRODUCES edge.

Fix:
  Pre-process query with DeepSeek. LLM uses world knowledge of the
  semiconductor industry to surface specific entity names that the
  semantic search should hit (TSMC, Taiwan, Santa Clara, etc.). The
  hints are appended to the original query so both abstract and
  specific signals reach the BGE encoder.

Cost: 1 DeepSeek call per query (~100 input + 30 output tokens ≈ $0.0005).
"""
from __future__ import annotations

from typing import Optional

from semigraph.config import Config, get_config
from semigraph.connections import get_llm


_SYSTEM_PROMPT = """You are a semiconductor industry expert helping a retrieval system.

Given a user query, identify specific named entities (companies, products, places, regulations) that are IMPLICITLY referenced but not stated by name. Use only entities likely to appear in 10-K filings of NVDA, AMD, MU.

Output ONLY the entity names as a space-separated list. No explanations, no preamble, no quotes.

Examples:
Query: What political risks affect the home country of the leading pure-play semiconductor foundry?
Output: TSMC Taiwan pure-play foundry geopolitical

Query: Which AI lab partners with the EPYC processor maker?
Output: AMD OpenAI Microsoft Sony

Query: Where is the developer of Ryzen processors headquartered?
Output: AMD Santa Clara California Sunnyvale

Query: What graphics product line does AMD offer to compete with NVIDIA RTX?
Output: AMD Radeon RDNA NVIDIA RTX GeForce

Query: Which memory supplier provides HBM to data center GPUs?
Output: Micron SK Hynix Samsung HBM NVIDIA"""


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
