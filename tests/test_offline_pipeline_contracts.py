"""Characterization tests for stable offline-pipeline contracts."""
from __future__ import annotations

from types import SimpleNamespace

from semigraph.offline.chunker import chunk_section
from semigraph.offline.kg_store import _doc_key
from semigraph.offline.pipeline import _filing_key
from semigraph.offline.preprocess import (
    _year_from_accession,
    extract_documents_streaming,
    extract_sections_10k,
)


def test_accession_year_drives_processed_filing_year():
    assert _year_from_accession("0001045810-26-000021") == "2026"
    assert _year_from_accession("unexpected") == "unknown"


def test_document_stream_keeps_only_supported_filing_types(tmp_path):
    submission = tmp_path / "full-submission.txt"
    submission.write_text(
        """<DOCUMENT>
<TYPE>10-K
<TEXT>
annual filing
</TEXT>
</DOCUMENT>
<DOCUMENT>
<TYPE>GRAPHIC
<TEXT>
ignored image data
</TEXT>
</DOCUMENT>
<DOCUMENT>
<TYPE>10-Q
<TEXT>
quarterly filing
</TEXT>
</DOCUMENT>
""",
        encoding="utf-8",
    )

    documents = list(extract_documents_streaming(str(submission)))

    assert documents == [
        ("10-K", "annual filing\n"),
        ("10-Q", "quarterly filing\n"),
    ]


def test_section_extraction_ignores_toc_and_preserves_boundaries():
    markdown = """Table of Contents
| Item 1. Business | 3 |

ITEM 1. BUSINESS
Business body.
ITEM 1A. RISK FACTORS
Risk body.
ITEM 5. MARKET FOR REGISTRANT'S COMMON EQUITY
Market body.
"""

    sections = extract_sections_10k(markdown)

    assert sections == {
        "Item 1": "ITEM 1. BUSINESS\nBusiness body.",
        "Item 1A": "ITEM 1A. RISK FACTORS\nRisk body.",
        "Item 5": (
            "ITEM 5. MARKET FOR REGISTRANT'S COMMON EQUITY\nMarket body."
        ),
    }


def test_chunk_contract_keeps_deterministic_id_and_derived_counts():
    cfg = SimpleNamespace(chunk_size=100, chunk_overlap=0)

    chunks = chunk_section(
        text="NVIDIA builds accelerated computing platforms.",
        ticker="NVDA",
        fiscal_year="2026",
        section="Item_1A",
        cfg=cfg,
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "NVDA_2026_Item_1A_0000_7a51fdaa"
    assert chunks[0].char_count == len(chunks[0].text)
    assert chunks[0].token_estimate == len(chunks[0].text) // 4
    assert chunks[0].filing_type == "10-K"


def test_filing_and_document_keys_share_the_existing_format():
    assert _filing_key("NVDA", "2026", "10K") == "NVDA_2026_10K"
    assert _doc_key("NVDA", "2026", "10K") == "NVDA_2026_10K"
