# 06 — Strict-74 Final Evaluation

**What to build:** ยืนยันผล Full Agent harness บน FinReflectKG strict 74 queries หลัง pilot ผ่านเกณฑ์ เพื่อสร้างผลสรุปงานวิจัยที่ทำซ้ำได้และแยกผลของ Agentic layer ออกจาก Retriever อย่างชัดเจน

**Blocked by:** 05 — Production Cutover and Paired 20-Query Pilot; acceptance gates must pass.

**Status:** ready-for-agent

- [ ] ล็อก model, dataset fingerprint, Retriever configuration, top-k, evaluator contract และ code identity ก่อนเริ่ม final run
- [ ] รันครบ 74 Queries แบบ checkpointed และ idempotent โดย network interruption ไม่ทำให้ผลสำเร็จเดิมสูญหายหรือรันซ้ำ
- [ ] เก็บ final answers, RAGAS-ready contexts, citations, Attempt Ledger, stop reasons, stage latency และ LLM-call counts ครบทุก Query
- [ ] รายงาน Hit, Recall, GroupRecall, answerable rate, latency, calls, errors และ paired regression/win ราย Query เทียบ frozen baseline
- [ ] ยืนยันว่าไม่มีการเปลี่ยน Graph Search, Vector Search, Financial Search, News Search, PPR, triple filter หรือ external reranker ระหว่างการทดลอง
- [ ] ผลชุดนี้ใช้เป็นข้อสรุป final benchmark ส่วน RAGAS judging ยังคงแยกออกไปตามขอบเขตของ Spec
