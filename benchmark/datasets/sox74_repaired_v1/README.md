# SOX74 Repaired v1

ชุดคำถาม–Gold Chunk–เฉลยฉบับแก้ไข จำนวน **74 ข้อ / 206 Answer Points / 79 chunks**

- `queries.yaml` เป็นข้อมูลหลัก: คำถาม เฉลยรายประเด็น และ mapping ของแต่ละประเด็นไปยังหลักฐาน
- `gold_chunks.jsonl` มีข้อความหลักฐานจริงแบบไม่แก้ถ้อยคำ และไม่มี embedding/เฉลยปนอยู่ในข้อความ
- `reference_review.yaml` กับ `review.html` ใช้ตรวจคำตอบด้วยเฉลยฉบับเดียวกัน
- `changes.yaml` บันทึกคำถาม/เฉลย/Gold เดิมเทียบกับฉบับแก้ครบ 74 ข้อ
- `manifest.json` บันทึก hash, ตารางตัวเลขที่อ่านตรวจ และรายการหลักฐานที่เพิ่ม

## การใช้กับ Oracle

```bash
conda run -n senior_project_py312 python eval_scripts/oracle_bench.py \
  --dataset benchmark/datasets/sox74_repaired_v1/queries.yaml \
  --gold-chunks benchmark/datasets/sox74_repaired_v1/gold_chunks.jsonl
```

ค่าเริ่มต้นยังเลือก 50 ข้อแรก ใช้ `--limit 74` เมื่อต้องการครบชุด ผลมี `dataset_revision: sox74_repaired_v1`
เปิด `review.html` แล้วเลือกไฟล์ผล Oracle ฉบับนี้ หน้าใหม่ปฏิเสธไฟล์ผลที่ไม่ระบุ revision เพื่อป้องกันนำผลคำถามเก่ามาตรวจด้วยเฉลยใหม่

## ขอบเขตและการเปรียบเทียบ

นี่คือชุดที่แก้ไขต่อจาก FinReflectKG SOX74 จึงต้องระบุชื่อ revision ในรายงาน ไม่ใช่การทดสอบคำถามต้นฉบับโดยไม่เปลี่ยนแปลง
คำถามที่หลักฐานไม่รองรับถูกเปลี่ยนประเด็นหรือปรับเงื่อนไขให้ตอบได้ มีประวัติการเปลี่ยนใน `changes.yaml`
เฉลยใช้เฉพาะสิ่งที่ถาม ไม่มีข้อความอ้างเหตุผลหรือหน้าที่ส่วนบุคคลที่หลักฐานไม่ให้ หากถามขอบเขตข้อมูล คำตอบอาจระบุว่า excerpt ไม่ได้ให้ข้อมูลส่วนนั้นตามคำถามอย่างชัดเจน

ในชุดที่จัดใหม่นี้มี 16 ข้อที่ใช้ content chunk เดียว และ 58 ข้อที่ใช้หลาย content chunks ตามแพ็กหลักฐานที่ให้
จำนวนนี้ไม่ใช่การรับรอง minimum reasoning hops เมื่อค้นทั้ง corpus และไม่ใช้ label 2-hop/3-hop เดิมเป็นข้อสรุป
หน่วย/หัวข้อ/วันที่ที่ขาดได้รับการเพิ่มเป็น context chunks จริง ปีใน `fiscal_year` ของ corpus ฉบับนี้อิงช่วงงบตามเนื้อหา ส่วน canonical IDs คงชื่อไฟล์ในชุดต้นทางไว้เพื่อสอบย้อนกลับ

## ก่อนทดสอบ retrieval

มี **18 chunk IDs ใหม่** เทียบกับ Gold เดิม 82 ชิ้น ต้องตรวจว่า benchmark database มีข้อความและ embedding ที่ตรงกับ corpus ฉบับนี้ รวมทั้ง document-year metadata ก่อนเปรียบเทียบ Vector/Graph หาก IDs ใดมีอยู่แล้วพร้อมข้อความและ embedding model เดียวกัน ไม่จำเป็นต้องสร้าง embedding ซ้ำ
งานนี้สร้างไฟล์ข้อมูล ยังไม่ได้เปลี่ยน Neo4j หรือรัน API 74 ข้อ และ `evaluate_new_agent.py` ยังชี้ชุด frozen เดิม
ต้องรันทุก architecture บน revision และ corpus เดียวกัน ไม่เทียบคะแนนใหม่กับคะแนนเดิมโดยตรง

สถานะ: assistant-curated พร้อมการตรวจข้อความต้นทาง สูตร และโครงสร้างข้อมูล ยังไม่มีการรับรองจากผู้ตรวจมนุษย์อิสระ
