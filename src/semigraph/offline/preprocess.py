"""
Document pre-processing pipeline.
Converts SEC filing HTML to Markdown and extracts standard 10-K sections.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

from bs4 import BeautifulSoup
import html2text as _html2text

from semigraph.config import get_config


# ---------------------------------------------------------------------------
# 0. Helpers
# ---------------------------------------------------------------------------

def _year_from_accession(accession: str) -> str:
    """
    Extract 4-digit filing year from an SEC accession number.

    Example: '0001045810-26-000021' → '2026'
    Falls back to 'unknown' if the format is unexpected.
    """
    parts = accession.split("-")
    if len(parts) >= 2 and len(parts[1]) == 2 and parts[1].isdigit():
        return f"20{parts[1]}"
    return "unknown"


# ---------------------------------------------------------------------------
# 1. Document streaming
# ---------------------------------------------------------------------------

VALID_TYPES = {"10-K", "10-Q", "8-K"}


def extract_documents_streaming(filepath: str) -> Generator[Tuple[str, str], None, None]:
    """
    Stream <DOCUMENT> blocks from a full-submission.txt file.

    Yields:
        (doc_type, text_content) for each valid document type found.
    """
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        in_document = False
        in_text = False
        current_type = None
        text_buffer: List[str] = []

        for line in f:
            if "<DOCUMENT>" in line:
                in_document = True
                current_type = None
                text_buffer = []
                continue

            if "</DOCUMENT>" in line:
                if in_document and current_type in VALID_TYPES and text_buffer:
                    yield (current_type, "".join(text_buffer))
                in_document = False
                in_text = False
                text_buffer = []
                continue

            if in_document:
                type_match = re.search(r"<TYPE>(.+)", line)
                if type_match:
                    current_type = type_match.group(1).strip()
                    if current_type in {"GRAPHIC", "ZIP", "EXCEL", "XML", "JSON"}:
                        in_document = False
                    continue

                if "<TEXT>" in line:
                    in_text = True
                    continue

                if "</TEXT>" in line:
                    in_text = False
                    continue

                if in_text and current_type in VALID_TYPES:
                    text_buffer.append(line)


# ---------------------------------------------------------------------------
# 2. HTML → Markdown conversion
# ---------------------------------------------------------------------------

def html_to_markdown(html_content: str, method: str = "html2text") -> str:
    """
    Convert HTML content to Markdown.

    Args:
        html_content: Raw HTML string
        method: Conversion backend — "html2text" | "markitdown" | "beautifulsoup"

    Returns:
        Markdown string
    """
    if method == "html2text":
        h = _html2text.HTML2Text()
        h.body_width = 0
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        h.skip_internal_links = True
        h.single_line_break = False
        h.mark_code = True
        h.wrap_links = False
        h.unicode_snob = True
        h.escape_snob = True
        return h.handle(html_content)

    elif method == "markitdown":
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            result = md.convert_string(html_content, file_extension=".html")
            return result.text_content
        except ImportError:
            print("MarkItDown not found, falling back to html2text")
            return html_to_markdown(html_content, method="html2text")

    elif method == "beautifulsoup":
        soup = BeautifulSoup(html_content, "lxml")
        for tag in soup(["script", "style", "meta", "link"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return re.sub(r"\n{3,}", "\n\n", text)

    else:
        raise ValueError(f"Unknown conversion method: {method}")


def clean_markdown(markdown: str) -> str:
    """Normalize whitespace, remove HTML comments and unicode artifacts."""
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    lines = [line.rstrip() for line in markdown.split("\n")]
    markdown = "\n".join(lines)
    markdown = re.sub(r"(-{3,}\n){2,}", "---\n", markdown)
    markdown = re.sub(r"<!--.*?-->", "", markdown, flags=re.DOTALL)
    markdown = re.sub(r"\xa0", " ", markdown)   # non-breaking space
    markdown = re.sub(r"\u200b", "", markdown)  # zero-width space
    return markdown.strip()


def remove_uuencode(text: str) -> str:
    """Strip UUencoded binary blocks from EDGAR filings."""
    return re.sub(r"begin \d{3} .+?\n.+?\nend", "", text, flags=re.DOTALL)


# ---------------------------------------------------------------------------
# 3. Section extraction
# ---------------------------------------------------------------------------

_SEP = r"(?:\\?[\.\:\-])?"   # matches  .  \.  :  -  or nothing  (html2text escapes dots)

_SECTION_PATTERNS = {
    "Item 1":   rf"(?i)(?m)^[\*_#\s]*item\s*1{_SEP}\s*business",
    "Item 1A":  rf"(?i)(?m)^[\*_#\s]*item\s*1a{_SEP}\s*risk",
    "Item 5":   rf"(?i)(?m)^[\*_#\s]*item\s*5{_SEP}\s*market",
    "Item 7":   rf"(?i)(?m)^[\*_#\s]*item\s*7{_SEP}\s*(?:management|md&a)",
    "Item 8":   rf"(?i)(?m)^[\*_#\s]*item\s*8{_SEP}\s*financial",
    "Item 10":  rf"(?i)(?m)^[\*_#\s]*item\s*10{_SEP}\s*directors",
    "Item 11":  rf"(?i)(?m)^[\*_#\s]*item\s*11{_SEP}\s*executive",
    "Item 15":  rf"(?i)(?m)^[\*_#\s]*item\s*15{_SEP}\s*exhibits",
    "Signatures": r"(?i)(?m)^[\*_#\s]*signatures",
}


def _clean_markdown_artifacts(text: str) -> str:
    text = re.sub(r"[\*_#]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_toc_line(line: str) -> bool:
    """Return True if the line looks like a Table of Contents entry."""
    if "|" in line:
        clean = line.replace("|", "").strip()
        if re.search(r"\d{1,3}$", clean):
            return True
    if re.search(r"\.{3,}\s*\d{1,3}", line):
        return True
    return False


def extract_sections_10k(markdown_text: str) -> Dict[str, str]:
    """
    Extract standard 10-K sections from a Markdown document.

    Returns:
        Dict mapping section name (e.g. "Item 1") to section content.
    """
    sections: Dict[str, str] = {}
    lines = markdown_text.split("\n")
    section_starts: Dict[str, int] = {}

    for i, line in enumerate(lines):
        if _is_toc_line(line):
            continue
        clean_line = _clean_markdown_artifacts(line)

        for section_name, pattern in _SECTION_PATTERNS.items():
            simple_pattern = pattern.replace("(?m)^", "^").replace(r"[\*_#\s]*", "")
            if re.search(simple_pattern, clean_line, re.IGNORECASE):
                if section_name not in section_starts:
                    section_starts[section_name] = i
                    print(f"  Found {section_name} at line {i}: {clean_line.strip()[:80]}")
                    break

    sorted_sections = sorted(section_starts.items(), key=lambda x: x[1])
    for idx, (section_name, start_line) in enumerate(sorted_sections):
        end_line = sorted_sections[idx + 1][1] if idx + 1 < len(sorted_sections) else len(lines)
        content = "\n".join(lines[start_line:end_line]).strip()
        sections[section_name] = content
        print(f"  Extracted {section_name}: {len(content):,} chars")

    return sections


def extract_sections_fallback(markdown_text: str) -> Dict[str, str]:
    """
    Fallback section extraction using full-document regex (slower but more permissive).

    Returns:
        Dict mapping section name to section content.
    """
    _s = r"(?:\\?[\.\:\-])?"   # same escaped-dot-aware separator as primary extraction
    sections: Dict[str, str] = {}
    patterns = {
        "Item 1":   rf"(?si)(item\s*1{_s}\s+business.*?)(?=item\s*1a|item\s*2{_s}|\Z)",
        "Item 1A":  rf"(?si)(item\s*1a{_s}\s+risk\s+factors?.*?)(?=item\s*1b|item\s*2{_s}|\Z)",
        "Item 5":   rf"(?si)(item\s*5{_s}\s+market.*?)(?=item\s*6{_s}|\Z)",
        "Item 7":   rf"(?si)(item\s*7{_s}\s+.*?)(?=item\s*7a|item\s*8{_s}|\Z)",
        "Item 8":   rf"(?si)(item\s*8{_s}\s+financial.*?)(?=item\s*9{_s}|\Z)",
        "Item 10":  rf"(?si)(item\s*10{_s}\s+.*?)(?=item\s*11{_s}|\Z)",
        "Item 11":  rf"(?si)(item\s*11{_s}\s+.*?)(?=item\s*12{_s}|\Z)",
    }
    for section_name, pattern in patterns.items():
        match = re.search(pattern, markdown_text)
        if match:
            sections[section_name] = match.group(1).strip()
            print(f"  Extracted (fallback) {section_name}: {len(sections[section_name]):,} chars")
    return sections


# ---------------------------------------------------------------------------
# 4. Save sections to disk
# ---------------------------------------------------------------------------

def save_sections(
    sections: Dict[str, str],
    output_dir: Path,
) -> None:
    """
    Save each section as a separate .md file directly inside output_dir.

    Args:
        sections: Dict of {section_name: content}
        output_dir: Target directory (already dated, e.g. data/processed/NVDA/FY2026/)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for section_name, content in sections.items():
        if not content:
            continue
        safe_name = section_name.replace(" ", "_")
        section_file = output_dir / f"{safe_name}.md"
        section_file.write_text(content, encoding="utf-8")
        print(f"  Saved: {section_file.name}")


# ---------------------------------------------------------------------------
# 5. Main pipeline function
# ---------------------------------------------------------------------------

_HEADER_PATTERN = re.compile(r"(?s)\A.*?(?=UNITED STATES)")


def clean_and_save_documents(
    input_file: str,
    ticker: str,
    filing_id: str,
    output_dir: Optional[str] = None,
    convert_to_markdown: bool = True,
    markdown_method: Optional[str] = None,
    extract_sections: Optional[bool] = None,
    use_fallback_extraction: Optional[bool] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Full pre-processing pipeline: stream documents → clean → convert → extract sections.

    Args:
        input_file: Path to full-submission.txt
        ticker: Stock ticker (e.g. "NVDA")
        filing_id: Unique accession id (e.g. "0001045810-24-000029")
        output_dir: Override output directory (defaults to config processed_dir)
        convert_to_markdown: Whether to convert HTML to Markdown
        markdown_method: Override config markdown method
        extract_sections: Override config extract_sections
        use_fallback_extraction: Override config fallback setting

    Returns:
        Dict mapping doc_type -> {section_name: content}
    """
    cfg = get_config()
    out_path = Path(output_dir) if output_dir else cfg.processed_dir
    out_path.mkdir(parents=True, exist_ok=True)

    method = markdown_method or cfg.markdown_method
    do_extract = extract_sections if extract_sections is not None else cfg.extract_sections
    do_fallback = use_fallback_extraction if use_fallback_extraction is not None else cfg.use_fallback_extraction

    filing_year = _year_from_accession(filing_id)
    dated_dir = out_path / ticker / f"FY{filing_year}"
    dated_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nProcessing: {input_file}")
    print(f"  Ticker: {ticker} | Filing: {filing_id} | Year: FY{filing_year} | Method: {method}")
    print(f"  Output: {dated_dir}")

    all_sections: Dict[str, Dict[str, str]] = {}
    found_10k = False

    for doc_type, text_content in extract_documents_streaming(input_file):
        if doc_type != "10-K":
            continue  # skip embedded exhibits, only process the main 10-K document

        cleaned_text = remove_uuencode(text_content)

        if convert_to_markdown:
            markdown_text = html_to_markdown(cleaned_text, method=method)
            final_text = clean_markdown(markdown_text)
        else:
            final_text = cleaned_text

        # Strip boilerplate header before "UNITED STATES"
        cleaned_final = _HEADER_PATTERN.sub("", final_text).strip()

        # Save full document (useful for debugging)
        ext = ".md" if convert_to_markdown else ".txt"
        full_doc_file = dated_dir / f"full_10K{ext}"
        full_doc_file.write_text(cleaned_final, encoding="utf-8")
        print(f"  Saved full doc: {full_doc_file.name} ({len(cleaned_final):,} chars)")

        found_10k = True

        if do_extract:
            print(f"\n  Extracting sections...")
            sections = extract_sections_10k(cleaned_final)

            if not sections and do_fallback:
                print("  Primary extraction found no sections, trying fallback...")
                sections = extract_sections_fallback(cleaned_final)

            if sections:
                save_sections(sections, dated_dir)
                all_sections[doc_type] = sections
                print(f"  Extracted {len(sections)} section(s)")
            else:
                print("  Warning: No sections found")

        break  # only process the first 10-K document block

    if not found_10k:
        print("  Warning: No 10-K document block found in file")

    print(f"\nDone. Output: {dated_dir}")
    return all_sections
