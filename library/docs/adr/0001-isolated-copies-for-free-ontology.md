---
status: accepted
date: 2026-10-25
---

# Keep compatibility changes in explicit copies under library

ผู้ใช้อนุมัติให้คัดลอกส่วนเดิมที่ติด ontology/config เฉพาะโครงการ แล้วแก้สำเนาให้รองรับ Free Ontology โดยไม่แก้ไฟล์เดิม ส่วนใหม่อยู่ใน `library/` และใช้ namespace `semigraph_sdk`; ส่ง LLM, retriever และ relation hints ผ่าน dependency ที่ชัดเจน แทนการเปลี่ยน global ของโมดูลเดิม จึงไม่ต้องเพิ่ม worker process เพื่อหลีกเลี่ยงการใช้ค่าร่วมกัน รุ่นแรกยังคงขอบเขตหนึ่งชุด config ต่อโปรแกรมตามที่ตกลง

## Consequences

- เก็บที่มาของแต่ละสำเนาและ SHA256 ตั้งต้นใน `../copied-sources.json` เพื่อเทียบการเปลี่ยนแปลงภายหลัง
- การแก้บั๊ก upstream จะไม่ไหลเข้าสำเนาอัตโนมัติ ต้องตรวจความต่างและเลือกย้ายเอง
- คัดลอกเฉพาะส่วนที่จำเป็น ไม่ย้าย application, evaluator หรือผล benchmark เดิม
- การใช้ flow เดิมไม่ได้รับรองว่าคุณภาพการค้น Free Ontology จะเท่ากับ benchmark ด้านการเงิน
- Agent copies ทำแล้ว; การคัดลอก retrieval kernels และสร้าง ingestion ยังต้องผ่าน Spec/Plan ของส่วนนั้น
