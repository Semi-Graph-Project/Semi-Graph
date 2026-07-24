# 02 — PlanRoute and Plan Validator

**What to build:** ทำให้ Full Agent แปลง Original Query เป็นแผนที่พร้อมเรียก Retriever ได้ใน LLM call เดียว โดยรักษารูปทรงคำถามตามธรรมชาติของแต่ละ Tool: connected multi-hop chain อยู่ใน Graph Task เดียวในครั้งแรก ส่วน Financial, Vector และ News แบ่ง Task ตาม capability ของตัวเอง แต่ละ Task มี Evidence Requirements และ initial action ที่ผ่าน structural validation แบบ KISS ก่อนค้นหา

**Blocked by:** 01 — Freeze Full Agent Baseline 20 Queries.

**Status:** ready-for-agent

- [ ] PlanRoute สร้าง Task แบบ sequential จำนวน 1–3 งาน โดยแต่ละ Task และ Requirement มี ID ไม่ซ้ำและ initial action ที่เรียกใช้ได้
- [ ] Connected multi-hop chain ไม่ถูกแยกเป็น independent Graph hops ใน initial plan; hops/claims ถูกแทนเป็น Evidence Requirements ภายใน Graph Task เดียว
- [ ] Tool อื่นรักษา retrieval intent ที่เหมาะกับ capability ของตน เช่น Financial comparison ที่รองรับยังเป็น Task เดียว และ independent evidence types จึงค่อยแยก Task
- [ ] Pydantic ปฏิเสธ field ที่ไม่รู้จัก shape ผิด enum ผิด และ cross-field contradiction ที่ขอบเขต output ของ LLM
- [ ] ตัวตรวจ deterministic ตรวจเฉพาะ non-null/non-empty, type, enum, action shape, positive top-k, cardinality และ unique IDs
- [ ] Entity, relation, product, period, metric และ semantic chain ที่อาจตกหล่นเป็น trace warning เท่านั้นในรุ่นแรก ไม่เป็น hard failure ที่อาจลด Recall
- [ ] แผนที่ถูกต้องไม่เสีย LLM call เพิ่ม ส่วนแผนผิดซ่อมได้หนึ่งครั้งและใช้ deterministic fallback เมื่อผลซ่อมยังผิด
- [ ] Original Query คงเดิมและ immutable เป็นสัญญาสูงสุด; fallback ไม่ใช้ plan ที่ทำ query ว่างหรือ shape เสีย และ trace แสดง validation, warning, repair และ fallback ได้
