# 03 — Regression tests and paired ablation

**What to build:** พิสูจน์ว่า Ontology-guided Relation Query Expansion ช่วย Graph retrieval โดยไม่ทำให้คุณภาพ, Latency หรือ Tool อื่นเสีย และมีหลักฐานเปรียบเทียบที่ทำซ้ำได้

**Blocked by:** 01 — Ontology-normalized Graph retrieval; 02 — Ontology-aware Assess retry

**Status:** ready-for-agent

- [ ] ใช้ชุด Query, corpus, embedding model, `top_k` และ Graph configuration เดียวกับ Baseline
- [ ] เก็บผลราย Query และค่า aggregate ของ Retriever Hit/Recall รวมถึง Latency
- [ ] ตรวจว่า Original Query fallback ยังทำงานเมื่อไม่มี Relation ที่ใช้ได้
- [ ] ตรวจว่า Query หลายรูปถูกรวม candidates ก่อน PPR และ PPR call count ไม่เพิ่มเกินหนึ่งครั้งต่อ Graph Attempt
- [ ] ตรวจว่า Planner/Assess Trace อธิบาย Relation และ Query ที่ใช้จริงได้
- [ ] รัน legacy regression และยืนยันว่า Vector, Financial, News และ locked-tool controls ไม่เปลี่ยน
- [ ] ไม่สร้าง Evaluator ใหม่ และไม่สรุปว่า Improve จนกว่าจะมีผล paired ablation รองรับ
