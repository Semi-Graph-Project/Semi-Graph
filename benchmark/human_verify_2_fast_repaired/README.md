# Human Verify 2 Fast — คะแนน Retrieval เทียบ Gold Repair

คำนวณ Hit, Recall และ MRR จากผลค้นเดิมใน `../human_verify_2_fast/` ครบ 5 การทดลอง
การทดลองละ 50 ข้อ รวม 250 ผลรายข้อ โดยเทียบกับ `gold_chunks` ของ
`../datasets/sox74_repaired_v1/queries.yaml`

| การทดลอง | ข้อ | Hit | Recall | MRR |
|---|---:|---:|---:|---:|
| Vector | 50 | 0.680 | 0.355 | 0.352 |
| Graph | 50 | 0.700 | 0.391 | 0.344 |
| Agent + Vector | 50 | 0.820 | 0.548 | 0.648 |
| Agent + Graph | 50 | 0.920 | 0.621 | 0.785 |
| Text-to-Cypher | 50 | 0.660 | 0.466 | 0.429 |

## วิธีคำนวณ

- ใช้ `top_chunk_ids` ทุกตัวตามลำดับที่บันทึกไว้เดิม ไม่มีการตัด @5 จัดอันดับใหม่ หรือเรียก retrieval ใหม่
- Gold คือเซต `gold_chunks` เต็มของ Repair แต่ละข้อ รวม context chunks
- Hit = 1 เมื่อพบ Gold อย่างน้อยหนึ่ง chunk มิฉะนั้นเป็น 0
- Recall = จำนวน Gold ที่พบ / จำนวน Gold ทั้งหมด
- Reciprocal Rank = 1 / อันดับของ Gold ตัวแรก ถ้าไม่พบเป็น 0
- Hit และ Recall สรุปเป็นค่าเฉลี่ยรายข้อ; MRR คือค่าเฉลี่ย Reciprocal Rank รายข้อ
- นับครบทุก 50 ข้อ รวมกรณีไม่พบ chunk และข้อที่โจทย์เปลี่ยนไปมาก
- สำหรับ Agent อันดับที่ใช้เป็นลำดับชุดหลักฐานสุดท้ายที่บันทึก ไม่ได้ยืนยันว่าเป็นอันดับจากคะแนนกลางเดียวกัน

นี่คือการคำนวณคะแนนผลค้นจากคำถามเดิมเทียบ Gold ใหม่ ไม่ใช่การรันระบบด้วยคำถาม Repair
หรือการปรับฐานข้อมูลให้ตรงกับ corpus ใหม่ จึงไม่ควรเรียกว่าเป็นผลทดลองใหม่บน Dataset Repair
มี 36 จาก 50 ข้อที่ชุด Gold เปลี่ยน ซึ่งอาจรวมการเพิ่มหน่วย/หัวตารางที่เป็น context
และการเปลี่ยนหลักฐานให้ตรงกับโจทย์ใหม่

## ไฟล์ผล

- YAML ทั้ง 5 ไฟล์ใช้ชื่อเดียวกับต้นฉบับในโฟลเดอร์แยกนี้ คงโครงสร้าง `summary`, `results`, `measurement`
- `gold_chunks`, `answer_points`, `hit`, `recall`, `reciprocal_rank` ใช้ชุด Repair
- `query` เป็นคำถามที่ส่งเข้า retrieval รอบเดิมจริง ส่วน `reference_query` เป็นคำถาม Repair
- `source_reference` เก็บ Gold และ Answer Points เดิม; `source_retrieval_metrics` เก็บคะแนนเดิมรายข้อ
- `source_summary` เก็บ summary เดิม; `evaluation` บันทึกวิธีคำนวณและ SHA-256 ของต้นทางกับชุด Repair
- `matched_gold_chunk_ids` และ `missing_gold_chunk_ids` ใช้ตรวจคะแนนรายข้อย้อนกลับ
- `summary.yaml` รวม 5 การทดลอง พร้อมค่าก่อนปัดเศษและคะแนนเดิม
- `per_query_metrics.yaml` รวมคะแนนรายข้อครบ 250 แถว
- ค่าใน `summary` ของ YAML ปัดทศนิยม 3 ตำแหน่งตามรูปแบบเดิม; คะแนนรายข้อไม่ปัดเศษ

`final_answer`, traces, เวลา, token, `mode` และ `measurement` เป็นข้อมูลรอบเดิม
ยังไม่ได้ตรวจหรือให้คะแนนคำตอบสุดท้าย และไม่ได้คำนวณ RAGAS Faithfulness ใหม่
ไฟล์ JSON Faithfulness ในโฟลเดอร์ต้นทางจึงไม่ได้รวมเป็นการทดลอง retrieval เพิ่ม

ไฟล์ต้นฉบับใน `human_verify_2_fast` และ Dataset Repair ไม่ถูกแก้ไข

## คำนวณซ้ำ

จากรากโครงการ ใช้ Python ที่มี PyYAML:

```bash
python benchmark/human_verify_2_fast_repaired/recompute.py
```

สคริปต์ตรวจ ID จำนวนข้อ ลำดับคำถาม Gold เดิม และคะแนนเดิมก่อนเขียนผล
แล้วคำนวณจากรายการที่บันทึกไว้โดยไม่เรียก Neo4j หรือ LLM
