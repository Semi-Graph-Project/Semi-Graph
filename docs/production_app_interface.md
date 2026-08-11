---
title: SemiGraph Production App Interface
status: accepted-design
created: 2026-08-11
---

# SemiGraph Production App Interface

## 1. Product Outcome

SemiGraph Production App เป็นพื้นที่วิจัยปัจจัยพื้นฐานบริษัท semiconductor สำหรับนักลงทุนรายย่อย โดยเปลี่ยน Full Agent จาก backend ตอบคำถามให้กลายเป็น workflow ที่ผู้ใช้สำรวจบริษัท เชื่อมความสัมพันธ์ ตรวจสอบสมมติฐาน และย้อนกลับไปหาหลักฐานต้นทางได้

Core interaction มีสองส่วน:

1. `Explore Companies` — Company-first Guided Exploration ผ่าน Research Lenses, Evidence Maps และ Thesis Boards
2. `Ask SemiGraph` — Chat สำหรับคำถามอิสระพร้อม citation และ explicit context handoff จาก Company Workspace

ระบบไม่สร้างคำแนะนำซื้อขาย, Bullish/Bearish rating, confidence percentage, valuation verdict หรือผลทำนายการเติบโต

## 2. Target User and Design Principles

### Target User

นักลงทุนรายย่อยสาย fundamental ตั้งแต่มือใหม่ที่ยังตั้งคำถามไม่เก่ง ถึงผู้ใช้ที่มี Thesis และต้องการตรวจหาหลักฐานสนับสนุน หลักฐานท้าทาย และช่องว่างที่ยังไม่รู้

### Principles

- **Company first**: ผู้ใช้เริ่มจากชื่อบริษัทหรือ ticker ไม่ต้องรู้ว่าควรถามอะไร
- **Progressive disclosure**: เริ่มด้วยคำอธิบายภาษาคนและ Evidence Map ขนาดเล็ก แล้วค่อยเปิดหลักฐานและ technical trace
- **Evidence before verdict**: แสดง supporting, challenging และ unknown evidence แทนการฟันธงการลงทุน
- **Inference is visible**: ข้อมูลที่เปิดเผยโดยตรงแสดงต่างจาก Agent-assembled path
- **Source and time are first-class**: ทุกข้ออ้างแสดงแหล่ง, fiscal period หรือวันที่ และ exact passage
- **User remains the thesis owner**: Agent ห้ามแก้ Thesis โดยไม่ขอคำยืนยัน

## 3. Information Architecture

### Top-Level Navigation

```text
SemiGraph
├─ Explore Companies
└─ Ask SemiGraph

Global action: + Add Source
```

`My Research` เป็น subview ภายใน `Explore Companies` ไม่ใช่ top-level destination และรวม saved companies, Thesis Boards, Evidence Snapshots และ User Sources

### Company Selection

- ค้นด้วยชื่อบริษัทหรือ ticker เท่านั้น
- แสดงชื่อในรูป `NVIDIA Corporation [NVDA]`
- บริษัทที่ไม่มี Base Corpus ยังเปิด Company Workspace ได้ตามปกติ แต่แสดง `Coverage: Personal Evidence Only`

## 4. Company Workspace

### Research Lenses

| Lens | คำถามหลัก | ผลลัพธ์หลัก |
|---|---|---|
| `Core Business` | ปัจจุบันบริษัททำอะไรและให้ใคร | Segment, Product, Customer/Market และ value-chain position |
| `Growth Thesis` | อะไรอาจทำให้ธุรกิจเติบโตต่อ | Driver, mechanism, conditions, challenges, signals to watch และ unknowns |
| `Dependencies` | บริษัทต้องพึ่งพาอะไร | Disclosed dependencies และ indirect exposures ที่ Agent เชื่อม |
| `Risks` | อะไรอาจทำให้ธุรกิจเสียหาย | Disclosed risk, latest signal และ possible impact path |
| `MOAT` | อะไรอาจทำให้ความได้เปรียบคงอยู่ | Supporting evidence, challenging evidence และ missing evidence |

`Growth Thesis` ไม่ใช่ forecast; `Risks` ไม่สร้าง risk score; `MOAT` ไม่สร้าง moat score หรือ verdict

### Time Model

Company Workspace ใช้ `Latest Available` เป็น default และแสดง source watermarks แยกกัน:

```text
Business             FY2026 10-K
Financial            Q2 FY2027
Recent signals       Aug 3, 2026
```

ผู้ใช้เปิด `Compare with previous period` เพื่อดูรายการที่เพิ่ม หาย เปลี่ยนถ้อยคำ หรือยังเหมือนเดิมได้ ห้ามรวมข้อมูลต่างช่วงเวลาโดยไม่แสดงวันที่หรือ period

### Company Comparison

- `Compare with...` เป็น contextual action ภายในทุก Lens ไม่ใช่ Lens ที่หก
- รุ่นแรกเทียบครั้งละสองบริษัท
- แสดงความเหมือน ความต่าง shared dependencies และสิ่งที่ยังเทียบไม่ได้
- ไม่จัดอันดับผู้ชนะ และต้องแจ้งเมื่อ Coverage Mode ของสองบริษัทไม่เท่ากัน

## 5. Evidence Map and Citation Experience

### Progressive Evidence Map

- เริ่มด้วย node ที่คัดแล้วประมาณ 5–8 nodes
- เส้นทึบแสดง Disclosed Relationship
- เส้นประแสดง Agent-Assembled Path และใช้ถ้อยคำว่า “may be exposed through...”
- กด node เพื่อดูคำอธิบายภาษาง่าย; กด edge เพื่อดู citation
- ผู้ใช้สั่ง `Expand path`, `Ask about this path` หรือ `Save to Thesis Board` ได้
- ซ่อน PPR, embedding, reranker และ LangGraph internals ไว้ใน technical trace

Desktop/Tablet ใช้ interactive map; mobile ใช้ vertical Evidence Path Cards ที่กดขยายทีละขั้น

### Evidence Drawer

การกด citation เปิด drawer โดยไม่พาออกจาก Map และแสดง:

- exact passage ที่ใช้
- source type, ticker, section, date/fiscal period และ source label
- claim, node หรือ edge ที่หลักฐานรองรับ
- surrounding context และปุ่มเปิดเอกสารเต็ม
- `Save to Thesis Board`

Financial evidence แสดง metric, value, period, unit และ lineage/formula; News แสดง title, publisher, date และ source link; User Evidence แสดง filename, page/text span และ `AI-extracted · unreviewed`

## 6. Thesis Board

### Thesis Ownership

- ผู้ใช้เขียน Thesis เองหรือบันทึกจาก Agent suggestion
- หลังบันทึก Thesis เป็น user-owned statement
- Agent เพิ่มหลักฐาน เปลี่ยน Evidence Status หรือเสนอ wording diff ได้ แต่ห้ามแก้ข้อความเอง
- การยอมรับ wording ใหม่สร้าง Thesis Version ใหม่

### Evidence Status

Agent จับคู่หลักฐานกับ Requirements และจำแนก supporting, challenging หรือ unknown ส่วน deterministic controller คำนวณ badge:

| Status | เงื่อนไข |
|---|---|
| `Review Due` | Source Watermark หรือ Thesis Version เปลี่ยนหลัง Snapshot ล่าสุด |
| `Insufficient Evidence` | Requirement สำคัญยังไม่มีหลักฐานครอบคลุม |
| `Evidence Mixed` | มีทั้ง supporting และ challenging evidence ที่เกี่ยวข้อง |
| `Evidence Supported` | Requirements สำคัญครบและไม่มี challenging evidence ที่เกี่ยวข้อง |

Status ใดที่มาจาก User Evidence เท่านั้นต้องมี modifier `Personal Evidence Only` หรือ `Supported by your sources`

### Evidence Snapshot

Snapshot เป็น immutable record ของ:

- Thesis ID และ Thesis Version
- Evidence Status
- Supporting/Challenging/Unknown mappings
- Evidence IDs และ source watermarks
- assessment time และ Agent run ID

การแก้ Thesis สร้าง version ใหม่; Snapshot เก่ายังผูกกับ version เดิม ส่วนโน้ตส่วนตัวแก้ได้โดยไม่แก้ Snapshot. ข้อยกเว้นเดียวคือ privacy deletion: เมื่อผู้ใช้ลบ Source ถาวร ระบบต้อง redact source payload และเหลือ tombstone โดยไม่คำนวณผลประเมินเก่าย้อนหลัง

`Review Due` เกิดเมื่อมี filing/financial period/news/User Source ใหม่, source เดิมถูกลบ หรือ Thesis เปลี่ยน ไม่ใช่เพราะครบจำนวนวันคงที่

## 7. User Sources and Personal Evidence

### Upload Entry Points and Formats

`+ Add Source` อยู่ระดับ global และแสดงซ้ำในสถานะที่หลักฐานไม่พอ รุ่นแรกรองรับ:

- PDF ที่มี text layer
- DOCX
- TXT
- Markdown
- HTML

ยังไม่รองรับ scanned PDF/OCR, image, spreadsheet/CSV, audio, video หรือ archive

### Extraction and Activation

```text
Upload
  → Parse and chunk
  → Extract open entities/relations
  → Attach provenance
  → Link entities to Base Graph candidates
  → Activate in Personal Workspace
```

รุ่นแรกไม่มี Lightweight Review gate; ผลสกัดใช้ได้ทันทีแต่ต้องติด `AI-extracted · unreviewed` และผู้ใช้สั่งสกัดใหม่หรือลบได้

Open Ontology เปิดให้สร้าง entity type และ predicate ใหม่ แต่ทุก assertion ต้องมี subject, predicate, object/value, source document, exact source span, document date, workspace owner และ review status

### Company Association

- Upload จาก Company Workspace ใช้บริษัทนั้นเป็น default
- ระบบตรวจหาบริษัทอื่นในเอกสารและผูก Source ได้หลายบริษัท
- ผู้ใช้แก้ company links ภายหลังได้
- เอกสารที่ไม่ผูกบริษัทอยู่ใน General Evidence และใช้เมื่อเลือกใน Source Scope

### Source Scope

- Company Workspace ใช้ System Evidence และ User Sources ที่ผูกกับบริษัทนั้นโดย default
- General Chat ใช้ System Evidence เท่านั้นจนกว่าผู้ใช้จะเพิ่ม My Evidence
- UI ต้องแสดงและให้ถอด Source Scope ได้เสมอ

### Conflict and Deletion

- User Evidence มีผลต่อคำตอบและ Evidence Status แต่ห้าม overwrite System Evidence
- หากแหล่งขัดแย้งกัน ต้องแสดงทั้งสองด้านและใช้ `Evidence Mixed`
- `Remove from Company` ถอด Source จากบริษัทหนึ่งโดยไม่ลบ Source
- `Delete Source Permanently` ลบ raw file, parsed text, chunks, embeddings, extracted assertions และ source text จาก citations แล้วคำนวณ Evidence Status ที่ได้รับผลใหม่
- Snapshot เก่าเหลือเพียง tombstone `Source removed` โดยไม่เก็บข้อความที่ถูกลบ

## 8. Retrieval Across System and Personal Evidence

Production App ใช้ Federated Retrieval ในรุ่นแรก:

```text
Query
  ├─ System Graph / Financial / News retrieval
  └─ Personal Open-Ontology retrieval
          ↓
    Entity links and source labels
          ↓
    Evidence-layer merge
          ↓
    Assessment, Evidence Map, Synthesis
```

ห้ามรวม Open-Ontology relations เข้า PPR topology ของ Base Graph ในรุ่นแรก Path ที่เชื่อมข้ามแหล่งใน UI ต้องระบุ `Agent-assembled path`

## 9. Chat and Agent Runtime

### Explicit Context Handoff

General Chat ไม่รับ Company Context โดยอัตโนมัติ แต่เมื่อผู้ใช้กด `Ask about this path` จาก Workspace ให้ส่ง company, lens, path, snapshot และ source scope เข้า Chat Thread พร้อม context chip ที่ถอดได้

Chat output ไม่เข้า Thesis Board อัตโนมัติ; ผู้ใช้ต้องกด `Save claim`, `Save evidence` หรือ `Open in Evidence Map`

### Background Research Jobs

- Lens แสดง Snapshot เดิมทันที และเรียก Agent เมื่อยังไม่มี Snapshot หรือผู้ใช้กด `Check Again`
- Agent รันเป็น background job; ผู้ใช้เปลี่ยหน้า ดู Snapshot เดิม หรือ cancel ได้
- ห้ามรัน job ซ้ำสำหรับ company + lens + source watermark เดียวกัน
- progress แสดงขั้นตอนภาษาคน; `View Research Trace` แสดง tasks, tools, queries, accepted/rejected evidence และ latency โดยไม่แสดง chain-of-thought

## 10. Empty and Failure States

ห้ามตีความ “ค้นไม่พบ” ว่า “ไม่มี” และต้องแยก:

1. `No evidence found`
2. `Related information found, but not stated explicitly`
3. `Outside available coverage`
4. `Retrieval system error`

สถานะที่เกิดจากหลักฐานขาดมี actions อย่างน้อย `Try another query`, `Explore indirect relationships`, `See searched sources`, `Add Source` และ `Save as Unknown`

## 11. Language and Responsive Behavior

- Production UI เป็น English-first
- ผู้ใช้ถามได้ภาษาไทยหรืออังกฤษ และ Agent ตอบตามภาษาคำถาม
- ชื่อบริษัท, product, metric และ citation ใช้ภาษาต้นฉบับ
- Responsive Web รองรับ desktop, tablet และ mobile; รุ่นแรกไม่สร้าง native mobile app

## 12. Production Boundary

Production App และ Streamlit Demo เป็นคนละ surface:

```text
Production Web Frontend
        ↓
Application API and Background Jobs
        ↓
SemiGraph Agent Core and Retrieval Tools

Streamlit Demo
        ↓
SemiGraph Agent Core and Retrieval Tools
```

Production ห้ามพึ่ง Streamlit session state หรือ UI code; Streamlit คงอยู่สำหรับ project demo, defense, evaluation และ debugging เท่านั้น รายละเอียดการตัดสินใจอยู่ใน [ADR 0003](adr/0003-separate-production-app-from-streamlit-demo.md)

Personal Evidence อยู่แยกจาก shared Base Graph และรวมผลที่ Evidence Layer ตาม [ADR 0004](adr/0004-private-open-ontology-user-evidence.md)

## 13. Out of Scope for the First Production Version

- Buy/sell recommendation, stock ranking, valuation verdict และ portfolio management
- Bullish/Bearish labels, risk/moat scores และ model confidence percentages
- Team Workspace, sharing, public links และ collaborative editing
- Automatic thesis rewriting
- Automatic Agent re-analysis without a user `Check Again` action
- PPR ข้าม Base Graph และ Personal Open-Ontology Graph
- Lightweight Review workflow ก่อนเปิดใช้ User Evidence
- OCR, spreadsheet, image, audio และ video ingestion
- Native mobile application

## 14. Product Acceptance Signals

ตัวชี้วัดรุ่นแรกวัดว่าผู้ใช้ทำงานวิจัยได้สำเร็จ ไม่ได้วัดผลตอบแทนการลงทุน:

- เวลาจากเลือกบริษัทถึงเห็น Snapshot แรก
- อัตราเปิด citation และอัตราย้อนกลับไป exact source
- อัตราบันทึก claim/evidence เข้า Thesis Board
- อัตรากลับมา `Check Again` เมื่อมี `Review Due`
- ความถูกต้องของ source labels, dates, Evidence Status และ delete isolation
- อัตรา background job completion, cancellation และ duplicate-job prevention
