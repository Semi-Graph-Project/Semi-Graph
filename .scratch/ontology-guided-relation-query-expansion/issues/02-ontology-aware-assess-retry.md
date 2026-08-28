# 02 — Ontology-aware Assess retry

**What to build:** ทำให้ Assess ใช้ผลค้น Graph รอบก่อนเพื่อเลือก Relation ใหม่หรือปรับ Query รอบถัดไปได้อย่างมีเหตุผล โดยไม่ถือ Graph diagnostics เป็นหลักฐานคำตอบ

**Blocked by:** 01 — Ontology-normalized Graph retrieval

**Status:** ready-for-agent

- [ ] Assess เห็น Ontology queries ที่ใช้, Top Triple candidates, PPR entities, returned chunk IDs และ abort reason แบบกระชับ
- [ ] Diagnostics ใช้เป็น retrieval hint เท่านั้น; Accepted Evidence ต้องมาจาก raw chunks
- [ ] เมื่อ Relation เดิมไม่ตรงกับ Requirement ให้เลือก Relation ใหม่จาก `INFORMATIVE_REL_TYPES` ที่ยังไม่เคยใช้
- [ ] เมื่อ Relation ถูกแต่ Chunk ยังไม่พอ ให้ปรับคำถามโดยรักษา entity และ constraint เดิม
- [ ] ห้ามส่ง Query เดิมซ้ำ และห้ามสร้าง Relation หรือ Entity นอกข้อมูลที่ระบบรู้จัก
- [ ] Retry ยังคงผ่าน budget, novelty และ evidence-gain guard เดิม และไม่เพิ่ม Direct Graph Path lookup
- [ ] ทดสอบกรณี Relation ผิด, Chunk ไม่พอ, no-seeds, Query ซ้ำ และกรณี Accept สำเร็จ
