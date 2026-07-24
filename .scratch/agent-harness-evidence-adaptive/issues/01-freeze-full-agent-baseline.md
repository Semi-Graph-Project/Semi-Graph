# 01 — Freeze Full Agent Baseline 20 Queries

**What to build:** สร้าง baseline ของ Full Agent เดิมที่ทำซ้ำได้บนชุดพัฒนา 20 queries แบบ stratified เพื่อให้การปรับ harness ทุกครั้งมีจุดเปรียบเทียบแบบ paired ที่เชื่อถือได้ โดยเก็บผลตอบสุดท้าย หลักฐาน trace การตั้งค่า dataset fingerprint และ code identity ครบถ้วน

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] เลือก Query IDs แบบ deterministic จำนวน 20 ข้อ กระจายตาม metadata ที่ dataset มี และต้องรวม FRKG003 กับ FRKG009
- [ ] ล็อก dataset, model, Retriever configuration, top-k, evaluator contract และบันทึก dataset fingerprint กับ code identity
- [ ] การรันรองรับ checkpoint/resume และเก็บ final answer, retrieved evidence, Tool calls, retrieval traces, run configuration และข้อผิดพลาดราย Query
- [ ] รายงาน baseline มี Hit, Recall, GroupRecall ทั้ง @K, All และ synthesis context รวมถึง latency และจำนวน Tool calls ทั้งราย Query และค่าเฉลี่ย
