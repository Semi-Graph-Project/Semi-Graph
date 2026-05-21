# SemiGraph — รายงานความคืบหน้า

**โครงงาน:** Agentic GraphRAG สำหรับการวิเคราะห์ปัจจัยพื้นฐานหุ้นเซมิคอนดักเตอร์
**ขอบเขต:** NVDA · AMD · MU · ASML · INTC
**วันที่:** 21 พฤษภาคม 2026

---

## 1. บทคัดย่อ

โครงงานพัฒนาระบบ retrieval ที่ตอบคำถาม multi-hop เกี่ยวกับเอกสาร 10-K ของบริษัท
เซมิคอนดักเตอร์ ในรอบนี้: (ก) เพิ่มบริษัท INTC เข้า corpus ครบทุกชั้น embedding
(ข) ขยายชุดทดสอบเป็น N=50 พร้อมกรอบการวัดผลเชิงสถิติ (ค) สร้าง demo end-to-end RAG
ที่ใช้งานได้จริงทั้งภาษาไทยและอังกฤษ

**ผลหลัก:** Hybrid retrieval (RRF fusion ของ graph + vector) ชนะ Vector baseline
อย่างมีนัยสำคัญทางสถิติ — Recall@5 เพิ่มขึ้น +11.6 percentage point
(Wilcoxon p = 0.0015, ช่วงเชื่อมั่น bootstrap 95% [+4.8, +18.4] pp) ส่วน Graph
retrieval เดี่ยวให้ Recall@5 สูงกว่า Vector +33% เชิงสัดส่วน — ยืนยันว่าการ
retrieve ด้วยโครงสร้าง knowledge graph มีประโยชน์จริงบนคำถาม multi-hop

Retrieval layer ผ่านการ validate แล้ว พร้อมเดินหน้าสู่ agent layer (Phase D)

---

## 2. ระบบปัจจุบัน

### 2.1 สถาปัตยกรรม

ระบบแบ่งเป็น 2 ส่วน:

**Offline (batch):**
```
SEC EDGAR → ingest → preprocess → chunker → kg_extract (DeepSeek) → Neo4j
```

**Online (retrieval — เสร็จแล้ว):**
- `vector_search` — ค้นด้วยความคล้ายของ embedding (BGE-base-en-v1.5, 768 มิติ)
- `graph_search` — Personalized PageRank + query-to-triple linker
- `hybrid_search` — Reciprocal Rank Fusion (RRF, k=60) ของ 2 ตัวข้างบน

### 2.2 สถานะ Corpus

| ตัวชี้วัด | ค่า |
|---|---|
| บริษัท | 5 (NVDA, AMD, MU, ASML, INTC) |
| เอกสาร 10-K | 15 (5 บริษัท × 3 ปีงบประมาณ) |
| Chunks | 742 |
| Entities | 4,856 |
| Relationships | 6,607 |
| Embeddings (chunk / entity / triple) | ครบ 100% |

รอบนี้เพิ่ม **INTC** — 3 filings, 214 chunks, 1,236 entities ใหม่. INTC ใช้
รูปแบบ 10-K ที่ไม่เป็นมาตรฐาน (Intel จัดลำดับหัวข้อเอง) จึงเขียน parser เฉพาะ
(`preprocess_intc_sections.py`) เพื่อ map หัวข้อของ Intel กลับเป็น Item 1 / 1A / 7

---

## 3. การประเมินผล Retrieval

### 3.1 วิธีการ

- **Dev set N=50** — คำถาม multi-hop สังเคราะห์ ทุกข้อ verified ground truth
  จาก graph (ใช้สำหรับปรับจูน — เปิดดูได้)
- **Held-out N=10** — ล็อกไว้ ยังไม่เปิดดู เพื่อวัดผล final แบบ unbiased
- **Metrics:** Hit@5, Recall@5
- **Statistical tests** (paired, α = 0.05): McNemar (Hit@5), Wilcoxon signed-rank
  (Recall@5), bootstrap 95% CI, Cohen's h (effect size)

### 3.2 ผลลัพธ์ 3-config

| Config | Hit@5 | Recall@5 |
|---|---|---|
| Vanilla Vector | 33/50 (66%) | 0.369 |
| Graph (PPR) | 38/50 (76%) | 0.492 |
| **Hybrid (RRF)** | **39/50 (78%)** | **0.485** |

**Statistical significance:**

| คู่เปรียบเทียบ | McNemar (Hit@5) | Wilcoxon (Recall@5) | Bootstrap 95% CI |
|---|---|---|---|
| Hybrid vs Vector | p = 0.031 ✓ | **p = 0.0015 ✓** | [+0.048, +0.184] ✓ |
| Graph vs Vector | p = 0.27 ✗ | p = 0.028 ✓ | [+0.007, +0.233] ✓ |
| Hybrid vs Graph | p = 1.00 ✗ | p = 0.97 ✗ | [−0.078, +0.065] ✗ |

ข้อสรุป: Hybrid ชนะ Vector อย่างมีนัยสำคัญทั้ง 2 metric — เป็นข้อสรุปหลักของ
โครงงาน. Graph เดี่ยวก็ชนะ Vector บน Recall@5 (กำไรมาจากองค์ประกอบ graph ไม่ใช่
จากสูตร RRF — Hybrid กับ Graph ไม่ต่างกันทางสถิติ)

### 3.3 Graph เก่งคำถามชนิดไหน

| ชนิดคำถาม | Vector R@5 | Graph R@5 | Δ |
|---|---|---|---|
| supplier chain | 0.30 | 0.85 | +0.55 |
| subsidiary lookup | 0.00 | 1.00 | +1.00 |
| product-in-segment | 0.40 | 1.00 | +0.60 |
| regulator / topical | 0.87 | 0.27 | −0.60 |

กลไก: คำตอบของคำถาม multi-hop มักอยู่ใน chunk ที่ไม่มีคำในคำถาม (เช่น chunk ที่
พูดถึง SK Hynix ไม่มีคำว่า Hopper) — vector ที่ค้นด้วยความคล้ายข้อความจึงพลาด
ส่วน graph เดินตาม relationship edge ทำให้เข้าถึงได้

### 3.4 บันทึก ablation — specificity-weighted teleport

ทดสอบเทคนิค specificity-weighted PPR teleport (HippoRAG v1) บน corpus นี้ — ผล
**ไม่ดีขึ้น** (Graph Recall@5 ลดจาก 0.492 → 0.448). สาเหตุ: hub entity
(`intel`, `nvidia`) ใน corpus 10-K ทำหน้าที่เป็น routing bridge ของ multi-hop
chain — การลดน้ำหนัก hub ทำลายการ traverse. จึงคงค่า default uniform teleport
ไว้ และบันทึกเป็น ablation finding

---

## 4. Demo

สร้าง demo end-to-end RAG 2 รูปแบบ:

- `scripts/demo_rag.py` — interactive CLI
- `app.py` — Streamlit web UI (dark/light theme)

ความสามารถ:
- รับคำถามทั้ง **ภาษาไทยและอังกฤษ** (Thai auto-translate ก่อน retrieve)
- คำตอบมี citation อ้างอิง ticker + ปีงบประมาณ
- **3-case graded response** — (A) ตอบตรงเมื่อมีข้อมูลชัด, (B) อนุมานพร้อม mark
  `▸` เมื่อต้องใช้การให้เหตุผล, (C) ปฏิเสธเมื่อข้อมูลไม่มีจริง

---

## 5. ข้อจำกัดที่พบ

**คำถามเปรียบเทียบ 2 บริษัท** (เช่น "เทียบ GPU ของ NVDA กับ AMD") ยังตอบได้
ไม่สมดุล — retrieval ดึง chunk เอียงไปบริษัทเดียว (ตัวอย่างที่วัดได้: 4 AMD chunk
ต่อ 1 NVDA chunk) เพราะ top-k มีจำกัดและ chunk 2 บริษัทแย่ง slot กัน

ทางแก้อยู่ใน Phase D — query decomposition: แตกคำถามเป็นคำถามย่อยต่อบริษัท แล้ว
retrieve แยก เพื่อการันตีว่าได้ chunk ครบทั้ง 2 ฝั่ง

---

## 6. แผนงานถัดไป

| Phase | งาน | ผลลัพธ์ที่คาด |
|---|---|---|
| C3 | financial_query | PostgreSQL + SEC XBRL — ตอบคำถามตัวเลขงบการเงิน |
| C4 | news_search | Finnhub — ข่าวและเหตุการณ์ล่าสุด |
| D | LangGraph agent | routing ระหว่าง 3 tool + query decomposition |
| E | Evaluation | Multi-Judge eval + เปิด held-out N=10 วัดผล final |

Retrieval layer (Phase B–C) เสร็จและผ่าน statistical validation แล้ว — งานต่อไป
คือ agent layer ซึ่งเป็นหัวใจของคำว่า "Agentic" ในชื่อโครงงาน

---

*เอกสารอ้างอิงผลการทดสอบฉบับเต็ม: `analytics/multihop_synthesized_eval.md`*
