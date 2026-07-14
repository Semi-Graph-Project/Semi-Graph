from semigraph.config import get_config
from semigraph.online.rerank import rerank_chunks

cfg = get_config()
chunks = [
    {
        "chunk_id": "demo-1",
        "ticker": "TXN",
        "fiscal_year": 2024,
        "section": "Item 7",
        "text": "The Other segment includes restructuring charges.",
    },
    {
        "chunk_id": "demo-2",
        "ticker": "NVDA",
        "fiscal_year": 2024,
        "section": "Item 1",
        "text": "The company designs accelerated computing platforms.",
    },
]

ranked, trace = rerank_chunks(
    "Which TXN segment includes restructuring charges?",
    chunks,
    top_n=1,
    cfg=cfg,
    fail_open=False,
)

print(ranked[0])
print(trace)