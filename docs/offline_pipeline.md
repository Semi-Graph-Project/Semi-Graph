# Offline Pipeline — Flow & Architecture

Offline pipeline คือส่วนที่ทำงานล่วงหน้า (batch) ก่อนที่ Agent จะถูกเรียกใช้งาน  
หน้าที่หลักคือ **ดึงข้อมูลจาก SEC EDGAR → แปลงเป็น Markdown → แยก Section → เตรียมพร้อมสำหรับ KG Extraction (Step 3)**

---

## Full Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        OFFLINE PIPELINE                         │
└─────────────────────────────────────────────────────────────────┘

  Config (config/default.yaml + .env)
       │
       │  tickers: [NVDA, AMD, MU, ...]
       │  filing_type: 10-K
       │  limit: 3
       ▼
┌─────────────────┐
│   ingest.py     │  Phase 1: Download
│                 │
│  download_      │  SEC EDGAR API
│  filings()      │──────────────────►  data/raw/sec-edgar-filings/
│                 │                      NVDA/10-K/
│  get_filing_    │                        0001045810-26-000021/
│  paths()        │                          full-submission.txt  (10-11 MB)
└────────┬────────┘                        0001045810-25-000023/
         │                                   full-submission.txt
         │  List[Path]  (full-submission.txt per filing)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│   preprocess.py     Phase 2: Convert & Extract                  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Step 2.1 — Stream Documents                            │   │
│  │                                                         │   │
│  │  extract_documents_streaming()                          │   │
│  │                                                         │   │
│  │  full-submission.txt มี <DOCUMENT> หลายบล็อก           │   │
│  │  ├── <TYPE>10-K  ← เอาอันนี้                          │   │
│  │  ├── <TYPE>EX-31 (exhibit) ← ข้าม                     │   │
│  │  └── <TYPE>GRAPHIC ← ข้าม                             │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                          │  raw HTML text (10-K block only)     │
│  ┌───────────────────────▼─────────────────────────────────┐   │
│  │  Step 2.2 — Clean & Convert                             │   │
│  │                                                         │   │
│  │  remove_uuencode()     ลบ binary ที่ฝังมา             │   │
│  │       ↓                                                 │   │
│  │  html_to_markdown()    HTML → Markdown (html2text)     │   │
│  │       ↓                                                 │   │
│  │  clean_markdown()      normalize whitespace             │   │
│  │       ↓                                                 │   │
│  │  _HEADER_PATTERN.sub() ลบ boilerplate header           │   │
│  │                        ก่อน "UNITED STATES"            │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                          │  clean Markdown text (~350 KB)       │
│  ┌───────────────────────▼─────────────────────────────────┐   │
│  │  Step 2.3 — Section Extraction                          │   │
│  │                                                         │   │
│  │  extract_sections_10k()   (primary)                    │   │
│  │                                                         │   │
│  │  อ่านทีละบรรทัด:                                       │   │
│  │  ├── _is_toc_line()  → ข้าม TOC entries               │   │
│  │  ├── _clean_markdown_artifacts()  → ลบ * _ # ออก      │   │
│  │  └── match _SECTION_PATTERNS                           │   │
│  │       ├── Item 1   r"item\s*1(?:\\?[.\:\-])?\s*business"   │   │
│  │       ├── Item 1A  r"item\s*1a(?:\\?[.\:\-])?\s*risk"      │   │
│  │       ├── Item 7   r"item\s*7(?:\\?[.\:\-])?\s*management" │   │
│  │       ├── Item 8   r"item\s*8(?:\\?[.\:\-])?\s*financial"  │   │
│  │       ├── Item 10  r"item\s*10(?:\\?[.\:\-])?\s*directors" │   │
│  │       └── ...                                          │   │
│  │                                                         │   │
│  │  ถ้า primary ไม่เจอ section → fallback                │   │
│  │  extract_sections_fallback()  (full-doc regex)         │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                          │  Dict[section_name → content]        │
│  ┌───────────────────────▼─────────────────────────────────┐   │
│  │  Step 2.4 — Save Output                                 │   │
│  │                                                         │   │
│  │  save_sections()                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
  data/processed/
    NVDA/
      FY2026-10K/
        full_10K.md       ← full Markdown (สำหรับ debug)
        Item_1.md         ← Business (~50 KB)
        Item_1A.md        ← Risk Factors (~120 KB)
        Item_7.md         ← MD&A (~48 KB)
        Item_10.md        ← Directors (~2 KB)
        ...
      FY2025-10K/
        ...
    AMD/
      FY2026-10K/
        ...
```

---

## Naming Convention

```
Accession Number:  0001045810 - 26 - 000021
                   └─ CIK ──┘  └┘  └─ seq ─┘
                                 └── ปีที่ยื่น = 2026

Output directory:  data/processed/{TICKER}/FY{YEAR}-{TYPE}/
                   data/processed/NVDA/FY2026-10K/
```

`_year_from_accession()` แปลง `"26"` → `"2026"` อัตโนมัติ

---

## Section Pattern — ทำไมต้องมี `(?:\\?[.\:\-])?`

html2text แปลง HTML table cell ที่มีข้อความ `ITEM 7.` ให้กลายเป็น `ITEM 7\.`  
(escape จุด เพื่อป้องกัน Markdown อ่านเป็น ordered list)

```
NVDA (div/p layout):  ITEM 7.  Management's Discussion...   → จุดธรรมดา
AMD  (table layout):  ITEM 7\. MANAGEMENT'S DISCUSSION...   → backslash + จุด
```

Regex `(?:\\?[.\:\-])?` รองรับทั้งสองรูปแบบ:
- `\\?`  = backslash หรือไม่มีก็ได้
- `[.\:\-]` = ตามด้วย `.` `:` หรือ `-`

---

## Primary vs Fallback Extraction

```
extract_sections_10k()   ← อ่านทีละบรรทัด, เร็ว, แม่นยำกว่า
        │
        │  ถ้าไม่พบ section ใดเลย
        ▼
extract_sections_fallback()  ← regex บน full-doc, ช้ากว่า แต่ permissive กว่า
```

Fallback ใช้ `re.search()` แบบ `(?si)` (dotall + ignorecase)  
จับทุกอย่างระหว่าง section header จนถึง section ถัดไป

---

## สิ่งที่ยังไม่มี (Step 3 ต่อจากนี้)

```
data/processed/NVDA/FY2026-10K/Item_1.md
        │
        │  ← จุดที่ pipeline หยุดอยู่ตอนนี้
        ▼
  [ chunker.py ]      ตัด section เป็น chunks (token-aware)
        ↓
  [ kg_extract.py ]   LLM (DeepSeek) → GraphExtractionResult
        ↓
  [ kg_store.py ]     MERGE nodes/relationships → Neo4j
```
