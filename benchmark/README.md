# Benchmark Data and Results

โฟลเดอร์นี้เก็บทั้งชุดข้อมูลที่ใช้ทดลองและผลรันที่บันทึกไว้ โดยแยกตามชื่อ
version เพื่อให้ตรวจ trace และย้อนดูค่าที่ใช้คำนวณได้

## Datasets

| File | Purpose |
|---|---|
| `finreflectkg_sox_strict74.yaml` | ชุดหลัก FinReflectKG multi-hop จำนวน 74 ข้อ |
| `finreflectkg_sox_smoke10.yaml` | ชุด smoke test ขนาดเล็ก |
| `phase_t_multihop_queries.yaml` | ชุดคำถาม multi-hop ที่สร้างและ audit ภายในโครงการ |
| `financebench_open_source.jsonl` | FinanceBench open-source questions |
| `financebench_document_information.jsonl` | Metadata ของเอกสาร FinanceBench |
| `financial_agent_e2e_60.yaml` | Financial Agent E2E จำนวน 60 ข้อ พร้อม Gold จาก PostgreSQL |
| `results/` | Trace จาก `eval_scripts/evaluate.py` และผล Retrieval/Answer ที่บันทึกไว้ |
| `results2/` | Trace จาก `eval_scripts/evaluate_new_agent.py` |
| `human_verify_2/`, `human_verify_2_fast/` | ผล `full_answer` ของคำถาม 50 ข้อสำหรับเปรียบเทียบ Human Verify |

## Dataset Contract

Benchmark YAML ที่ใช้กับ retrieval evaluator ควรเก็บข้อมูลต่อข้อดังนี้:

- `id` และ `query`
- `type` และ `subset`
- `gold_chunks`
- `gold_evidence_groups`
- `reference_gold_entities`
- `answer_points` ถ้ามี
- `corpus_status` เพื่อแยกข้อที่ corpus พร้อมจากข้อที่ยังไม่ครอบคลุม

`gold_chunks` ใช้ตรวจว่า evidence chunk ถูกค้นพบหรือไม่ ส่วน `gold_evidence_groups` ใช้วัด multi-hop coverage และ `Answerable@K`

## Reproducibility

Evaluator ที่ใช้งานอยู่ใน `eval_scripts/`:

```bash
# Retrieval evaluator; ผลลัพธ์ไปที่ benchmark/results/
conda run -n senior_project python eval_scripts/evaluate.py \
  --tool vector \
  --version_name vector_v1 \
  --mode retrieve_only

# New Agent evaluator; ผลลัพธ์ไปที่ benchmark/results2/
conda run -n senior_project python eval_scripts/evaluate_new_agent.py \
  --tool agent_vector \
  --version_name agent_vector_v1 \
  --mode full_answer
```

เปลี่ยน `--tool` ตาม configuration ที่ต้องการ (`vector`, `graph`,
`agent_vector`, `agent_graph`) และเก็บไฟล์ YAML/JSONL ที่ได้ไว้คู่กัน

`evaluate.py` บันทึกผลลง `benchmark/results/`; `evaluate_new_agent.py` บันทึกลง
`benchmark/results2/`. ไฟล์ YAML สรุป metric และ trace ส่วน JSONL เก็บผลรายข้อ
สำหรับตรวจสอบย้อนหลัง ห้าม commit secret, Neo4j dump, embedding หรือ checkpoint
runtime ลงใน benchmark

## ผลรันล่าสุดที่บันทึกไว้ (2026-09-26)

### SOX74 แบบ retrieval-only (74 ข้อ)

| Configuration | Chunk Hit | Recall | MRR | Avg. retrieval latency |
|---|---:|---:|---:|---:|
| Vector v1 | 0.635 | 0.358 | 0.326 | 10.16 s |
| Graph v1 | 0.757 | 0.439 | 0.368 | 3.57 s |

### Human Verify แบบ full-answer: 50 ข้อแรก

ทั้ง 8 รอบใช้ query ID 50 ข้อชุดเดียวกัน โหมด `full_answer` และปิด audit
ค่า Retrieval แสดง Hit/Recall/MRR ส่วนคะแนน Answer คำนวณจาก preset จุดคำตอบที่
บันทึกไว้ใน [`../docs/answer-review/index.html`](../docs/answer-review/index.html)

| Run | Retrieval Hit / Recall / MRR | Answer Hit | Answer-point Recall | Main-point Recall | Fully Correct |
|---|---:|---:|---:|---:|---:|
| Human Verify — Vector | 0.640 / 0.380 / 0.348 | 24/50 (48.0%) | 35/159 (22.0%) | 28/111 (25.2%) | 1/50 (2%) |
| Human Verify — Graph (`cross_enc_llm`) | 0.840 / 0.557 / 0.570 | 28/50 (56.0%) | 48/159 (30.2%) | 33/111 (29.7%) | 4/50 (8%) |
| Human Verify — Agent + Vector | 0.900 / 0.637 / 0.763 | 35/50 (70.0%) | 54/159 (34.0%) | 42/111 (37.8%) | 3/50 (6%) |
| Human Verify — Agent + Graph | 0.960 / 0.773 / 0.811 | 35/50 (70.0%) | 50/159 (31.4%) | 40/111 (36.0%) | 3/50 (6%) |
| Human Verify Fast — Vector | 0.640 / 0.380 / 0.365 | 23/50 (46.0%) | 36/159 (22.6%) | 28/111 (25.2%) | 1/50 (2%) |
| Human Verify Fast — Graph | 0.760 / 0.443 / 0.355 | 22/50 (44.0%) | 39/159 (24.5%) | 26/111 (23.4%) | 2/50 (4%) |
| Human Verify Fast — Agent + Vector | 0.860 / 0.600 / 0.728 | 36/50 (72.0%) | 53/159 (33.3%) | 43/111 (38.7%) | 3/50 (6%) |
| Human Verify Fast — Agent + Graph | 0.940 / 0.683 / 0.786 | 38/50 (76.0%) | 64/159 (40.3%) | 44/111 (39.6%) | 6/50 (12%) |

| Run | Avg. retrieval | Avg. answer | Avg. total | Tokens incl. warm-up |
|---|---:|---:|---:|---:|
| Human Verify — Vector | 2.80 s | 27.57 s | 30.37 s | 401,812 |
| Human Verify — Graph (`cross_enc_llm`) | 56.29 s | 86.13 s | 142.42 s | 542,063 |
| Human Verify — Agent + Vector | 97.04 s | 18.42 s | 115.46 s | 3,043,348 |
| Human Verify — Agent + Graph | 184.93 s | 21.65 s | 206.58 s | 4,551,238 |
| Human Verify Fast — Vector | 0.36 s | 17.06 s | 17.42 s | 374,668 |
| Human Verify Fast — Graph | 2.02 s | 19.14 s | 21.16 s | 432,799 |
| Human Verify Fast — Agent + Vector | 30.83 s | 19.50 s | 50.33 s | 2,485,673 |
| Human Verify Fast — Agent + Graph | 37.32 s | 16.97 s | 54.29 s | 3,050,290 |

Latency เป็นค่าเฉลี่ยต่อข้อจากสรุปผลแต่ละรอบ โดยไม่รวมช่วง warm-up ส่วนจำนวน
token ใช้ค่า `token_usage_including_warmup`

### วิธีอ่านคะแนน Answer

- Checklist จะนับจุดที่อยู่ใน preset เป็นถูก และตั้งจุดอ้างอิงที่เหลือเป็นผิด
  คะแนนนี้จึงเป็น rubric แบบ answer point ไม่ใช่คะแนนจาก LLM judge อิสระ
- `Answer Hit` หมายถึงมี answer point ที่ถูกอย่างน้อยหนึ่งข้อ ส่วน `Fully Correct`
  หมายถึง answer point อ้างอิงถูกครบทุกข้อ แต่ไม่ได้ตรวจข้ออ้างเกินจาก rubric
  ที่ปรากฏในคำตอบ
- คะแนน Retrieval ของ Agent ใช้ evidence ชุดสุดท้าย ซึ่งจำนวน chunk เปลี่ยนได้
  จึงไม่ใช่การเทียบ top-10 คงที่กับ Vector/Graph แบบเดี่ยว
- อย่าตีความ Human Verify เทียบกับ Fast ว่าเป็นการวัดความเร็วเพียงตัวแปรเดียว:
  Graph รอบแรกใช้ `cross_enc_llm` และการตั้งค่า worker/runtime ของ Agent ต่างกัน
  อีกทั้งผล full-answer 50 ข้อเป็นคนละชุดประเมินกับ retrieval-only 74 ข้อ
