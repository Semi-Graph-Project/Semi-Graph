# Benchmark Datasets

โฟลเดอร์นี้เก็บเฉพาะ input ที่ใช้สร้างผลการทดลองซ้ำได้ ไม่เก็บ trace หรือผลลัพธ์ของแต่ละรอบ

## Datasets

| File | Purpose |
|---|---|
| `finreflectkg_sox_strict74.yaml` | ชุดหลัก FinReflectKG multi-hop จำนวน 74 ข้อ |
| `finreflectkg_sox_smoke10.yaml` | ชุด smoke test ขนาดเล็ก |
| `phase_t_multihop_queries.yaml` | ชุดคำถาม multi-hop ที่สร้างและ audit ภายในโครงการ |
| `financebench_open_source.jsonl` | FinanceBench open-source questions |
| `financebench_document_information.jsonl` | Metadata ของเอกสาร FinanceBench |
| `financial_agent_e2e_60.yaml` | Financial Agent E2E จำนวน 60 ข้อ พร้อม Gold จาก PostgreSQL |

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

คำสั่ง evaluator จะใช้ `benchmark/datasets/phase_t_multihop_queries.yaml` เป็น default query file เมื่อไม่ส่ง `--queries` เพิ่มเอง:

```bash
conda run -n senior_project python scripts/evaluate_retrieval_quality.py \
  --tools vector graph hybrid \
  --top-k 5 \
  --oracle-k 20
```

ผลลัพธ์ของแต่ละรอบเก็บที่ `analytics/Report Experiment/` ส่วน secret, Neo4j dump, embedding และไฟล์ชั่วคราวต้องอยู่นอก benchmark dataset
