# 01 — Ontology-normalized Graph retrieval

**What to build:** ทำให้ Graph Task ค้นด้วยคำถามที่ใช้คำความสัมพันธ์ตรงกับ `INFORMATIVE_REL_TYPES` โดยยังคง Task เดิมและเก็บ Original Query เป็น fallback

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ / ] PlanRoute สร้าง Graph query เพิ่มได้ไม่เกิน `MAX_NUM_ONTOLOGY` โดยเปลี่ยนเฉพาะถ้อยคำความสัมพันธ์ และคง entity, ปี, metric และ constraint เดิม
- [ ] Relation ที่เลือกต้องมาจาก `INFORMATIVE_REL_TYPES` และเขียนเป็นภาษาธรรมชาติ เช่น `has stake in`
- [ ] Original Query ถูกค้นร่วมด้วยเสมอ และไม่ถูกนับรวมใน `MAX_NUM_ONTOLOGY`
- [ ] Query แต่ละรูปถูกค้นแยกกัน ไม่รวมหลาย Relation ไว้ในประโยคเดียว
- [ ] รวม Triple candidates จากทุก Query, dedupe Triple เดิม, ใช้คะแนนสูงสุด และตัดกลับเหลือ `top_k_triples` เดิมก่อนรัน PPR ครั้งเดียว
- [ ] Relation ที่ใช้ไม่ได้ถูกทิ้งโดยไม่ทำให้ Plan ล้ม และ Trace ระบุ Query ที่ใช้จริง
- [ ] ทดสอบ Graph flow และยืนยันว่า Vector, Financial และ News ยังใช้พฤติกรรมเดิม
