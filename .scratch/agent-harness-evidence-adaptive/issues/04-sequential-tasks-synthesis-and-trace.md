# 04 — Sequential Tasks, Grounded Synthesis, and Trace

**What to build:** ทำให้ Four-Node Harness ทำหลาย Tasks ตามลำดับจนจบ แล้วสังเคราะห์คำตอบครั้งเดียวจาก accepted raw evidence ที่จัดสรรอย่างสมดุล พร้อม trace ที่อธิบายทุกการตัดสินใจและต้นทุนเวลาได้

**Blocked by:** 03 — Attempt Ledger, Assess, and Adaptive Retry.

**Status:** ready-for-agent

- [ ] Tasks ทำงานตามลำดับและจบเป็น completed, partial หรือ failed พร้อม stop reason ที่ไม่ปะปนกับความหมายว่า evidence เพียงพอ
- [ ] Attempt Ledger และ Raw Evidence Pool เก็บ audit เต็มแบบ append-only, Accepted Evidence เก็บ supporting chunks แบบ union และ Working Context ส่งให้ Assess เฉพาะข้อมูลย่อที่จำเป็นโดยขนาดไม่โตตาม raw history
- [ ] Assess ทำ semantic mapping ว่า chunk รองรับ Requirement ใด แล้ว deterministic selector เลือก coverage-first ภายใน synthesis budget เริ่มต้นราวเก้า unique chunks
- [ ] Attempt แรกและ Attempt ล่าสุดไม่มี priority โดยตัวมันเอง; retry chunks ที่ครอบคลุม Requirements มากกว่าสามารถแทนผลรอบแรกใน Synthesis Context ได้ทั้งหมด
- [ ] เมื่อ coverage เท่ากันจึงใช้ direct-support strength และ Retriever rank เป็น tie-breaker; Retriever order ใช้เป็น fail-open fallback เมื่อ Assessment ใช้งานไม่ได้
- [ ] Final Answer อ้างอิง accepted raw chunks ด้วย citation IDs ที่ตรวจสอบได้ และยังเก็บ raw evidence ทั้งหมดสำหรับ Recall@All
- [ ] graph ทำงานเป็น PlanRoute → Execute → Assess → Synthesize โดย Assess วนกลับ Execute หรือเดิน Task ถัดไปตาม controller
- [ ] trace แยก PlanRoute, validation/repair, Technical Retry, Retriever, Assess, Retry Feedback, Tool Retry Profile decision, evidence selection และ Synthesize รวม latency กับ orchestration/Retriever-internal LLM calls
- [ ] ไม่มี external reranker เพิ่ม และ Retriever configuration/algorithm รวมถึง Graph triple filtering ไม่เปลี่ยน
