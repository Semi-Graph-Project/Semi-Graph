# 05 — Production Cutover and Paired 20-Query Pilot

**What to build:** สลับ Full Agent production และ evaluator มาใช้ Four-Node Harness เพียงชุดเดียว ลบ contract เดิมที่ไม่ใช้ และพิสูจน์ผลบน Query IDs เดียวกับ frozen baseline โดยไม่เปลี่ยน Retriever

**Blocked by:** 04 — Sequential Tasks, Grounded Synthesis, and Trace.

**Status:** ready-for-agent

- [ ] Full Agent ใช้ harness ใหม่เป็นค่าเริ่มต้น ขณะที่ Agent+Vector และ Agent+Graph ยังคงเป็น locked-tool ablation controls
- [ ] evaluator อ่าน Attempt Ledger, Evidence Pool, stop reasons, stage traces และ final answer ได้ พร้อม checkpoint/resume และ RAGAS-ready projection เดิม
- [ ] state, nodes, prompts และ histories แบบ Observe/Reflect เดิมที่ไม่มีผู้ใช้ถูกนำออก โดยไม่เหลือ Full Agent สองชุดให้ดูแล
- [ ] unit tests และ graph tests ครอบคลุม happy path, connected Graph Task, minimal plan validation, plan repair/fallback, technical/evidence retry separation, same-tool hint, compatible Tool switching, retry guards, coverage-first selection, fail-open, citations และ bounded context
- [ ] รัน paired pilot ด้วย 20 Query IDs, model, top-k และ Retriever configuration เดียวกับ baseline พร้อมรายงาน aggregate และ regression ราย Query
- [ ] Hard regression gate เทียบ frozen Full Agent: Recall@All ไม่ต่ำกว่า 0.233, Synthesis GroupRecall ไม่ต่ำกว่า 0.217 และ Hit@All ไม่ต่ำกว่า frozen baseline
- [ ] Graph promotion target เทียบ frozen Agent+Graph: Recall@All อย่างน้อย 0.408 และ Synthesis GroupRecall อย่างน้อย 0.367; pilot เป็น engineering target ส่วน statistical conclusion ใช้ strict 74
- [ ] latency เฉลี่ยลดอย่างน้อย 25% และ orchestration LLM calls ลดอย่างน้อย 30% เทียบ frozen Full Agent
- [ ] exact repeated actions และ runtime errors เป็นศูนย์ และ invalid plans หลัง repair ต่ำกว่า 5%
