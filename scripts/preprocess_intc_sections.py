"""
INTC-specific section extractor.

Intel's 10-K uses a non-standard format (explicitly documented in their filing:
"The order and presentation of content in our Form 10-K differs from the
traditional SEC Form 10-K format."). Standard Item-N patterns don't match.

This script maps Intel's own section headers to the standard Item_N.md
filenames that pipeline.py expects:

  Item 1  (Business)     : Forward-Looking Statements → Management's Discussion
  Item 7  (MD&A)         : Management's Discussion → Risk Factors section
  Item 1A (Risk Factors) : Risk Factors section → post-RF section header

Run:
    conda run -n senior_project python scripts/preprocess_intc_sections.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from semigraph.config import get_config

# Section header exact strings used in INTC's markdown (body, not TOC)
_MDA_HEADER = "Management's Discussion and Analysis|"
_RISK_HEADERS = {
    "Risk Factors and Other Key Information|",
    "Risk Factors|",
}
_RISK_END_MARKERS = {
    "Sales and Marketing",
    "Sales and Marketing|",
    "Cybersecurity",
    "Cybersecurity|",
    "Quantitative and Qualitative Disclosures About Market Risk",
    "Other Key Information|",
}
_FLS_HEADER = "Forward-Looking Statements"


def _find_line(lines: list[str], targets: set[str], start: int = 0, min_gap: int = 0) -> int:
    """Return 0-indexed line number of first match at or after `start + min_gap`."""
    for i in range(start + min_gap, len(lines)):
        if lines[i].strip() in targets:
            return i
    return -1


def extract_intc_sections(full_md_path: Path) -> dict[str, str]:
    """Return {item_name: content} for Item 1, Item 7, Item 1A."""
    lines = full_md_path.read_text(encoding="utf-8").splitlines(keepends=True)

    # --- boundary detection ---
    fls_line = _find_line(lines, {_FLS_HEADER})
    mda_line = _find_line(lines, {_MDA_HEADER})
    risk_line = _find_line(lines, _RISK_HEADERS, start=mda_line if mda_line >= 0 else 0)
    risk_end_line = _find_line(lines, _RISK_END_MARKERS,
                               start=risk_line if risk_line >= 0 else 0, min_gap=100)

    if mda_line < 0:
        raise ValueError(f"Could not find MD&A header in {full_md_path}")
    if risk_line < 0:
        raise ValueError(f"Could not find Risk Factors header in {full_md_path}")

    item1_start = fls_line if fls_line >= 0 else 0
    item7_start = mda_line
    item1a_start = risk_line
    item1a_end = risk_end_line if risk_end_line >= 0 else min(risk_line + 600, len(lines))

    sections = {
        "Item 1":  "".join(lines[item1_start:item7_start]),
        "Item 7":  "".join(lines[item7_start:item1a_start]),
        "Item 1A": "".join(lines[item1a_start:item1a_end]),
    }

    print(f"  Item 1  : lines {item1_start+1}-{item7_start}  "
          f"({len(sections['Item 1']):,} chars)")
    print(f"  Item 7  : lines {item7_start+1}-{item1a_start}  "
          f"({len(sections['Item 7']):,} chars)")
    print(f"  Item 1A : lines {item1a_start+1}-{item1a_end}  "
          f"({len(sections['Item 1A']):,} chars)")
    return sections


def main() -> None:
    cfg = get_config()
    processed_root = cfg.processed_dir

    intc_dirs = sorted((processed_root / "INTC").iterdir()) if (processed_root / "INTC").exists() else []
    if not intc_dirs:
        print("No INTC processed dirs found under", processed_root / "INTC")
        return

    for filing_dir in intc_dirs:
        full_md = filing_dir / "full_10K.md"
        if not full_md.exists():
            print(f"\n[{filing_dir.name}] full_10K.md missing — run preprocess first")
            continue

        print(f"\n[{filing_dir.name}] extracting INTC-specific sections...")
        try:
            sections = extract_intc_sections(full_md)
        except ValueError as e:
            print(f"  ERROR: {e}")
            continue

        for item_name, content in sections.items():
            safe = item_name.replace(" ", "_")
            out_file = filing_dir / f"{safe}.md"
            out_file.write_text(content, encoding="utf-8")
            print(f"  Saved: {out_file.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
