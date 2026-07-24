---
status: accepted
date: 2026-07-23
---

# Use evidence-adaptive, tool-aware retry

Full Agent จะรักษา connected multi-hop chain เป็น Graph Task เดียวใน retrieval ครั้งแรก แล้วให้ Assess ประเมิน Requirement coverage สร้าง structured Retry Feedback และเสนอ Hint กับ next action ใน LLM call เดียว Retry ใช้ controller กลางร่วมกับ Tool Retry Profiles: ใช้ Tool เดิมก่อนเมื่อ failure นั้นแก้ด้วย query ใหม่ได้ เปลี่ยน Tool เมื่อ capability ไม่ตรงหรือ Tool เดิมหมดทาง และไม่ใช้ generic HyDE ในรุ่นแรก เพราะ Graph ต้องการ query ที่สอดคล้องกับ entity-relation triples มากกว่า hypothetical passage

Raw evidence จากทุก Attempt เป็น append-only แต่ Synthesis เลือกหลักฐานตาม Evidence Quality โดยไม่ให้สิทธิ์ Attempt แรกหรือ Attempt ล่าสุดเป็นพิเศษ Technical Retry ถูกแยกจาก Evidence Retry และไม่ใช้งบ Agent Attempt ส่วน deterministic validation ตรวจเพียงโครงสร้างที่พิสูจน์ได้ เช่น non-null, type, enum, unique IDs และ positive limits เพื่อไม่ให้ semantic guard ทำ Recall ตก

## Consequences

- Assess เป็นเจ้าของ semantic mapping, Retry Feedback, Hint และ next action โดยไม่เพิ่ม Hint node หรือ LLM call
- Attempt ที่สามใช้ได้เมื่อ Attempt ที่สองมี Evidence Gain หรือเมื่อ Tool เดิมไม่เพิ่มหลักฐานและมี compatible fallback Tool
- Tool/query ซ้ำและ duplicate result sets ถูกปฏิเสธ แต่ semantic hints ที่กำกวมไม่ถูก hard-reject
- Synthesis ใช้ deterministic coverage-first selection จาก Accepted Evidence; Retriever rank เป็นเพียง tie-breaker หรือ fail-open fallback
