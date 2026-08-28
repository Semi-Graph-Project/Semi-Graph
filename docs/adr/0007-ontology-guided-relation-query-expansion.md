---
status: accepted
date: 2026-08-27
---

# Use ontology-guided relation query expansion for Graph retrieval

Graph Triple embeddings ใช้ข้อความรูปแบบ `head + humanized relation + tail` ทำให้คำถามทั่วไปอาจใกล้ Triple ที่มีคำคล้ายกันแต่ใช้ความสัมพันธ์ผิด SemiGraph จึงให้ PlanRoute แตก Retrieval Tasks ตามเดิม แต่สำหรับ Graph Task จะสร้างคำถามเพิ่ม 1–`MAX_NUM_ONTOLOGY` รูป โดยเปลี่ยนเฉพาะถ้อยคำความสัมพันธ์ให้เป็นภาษาธรรมชาติของ `INFORMATIVE_REL_TYPES` และรักษา entity, period, metric และ constraints เดิมทั้งหมด Original Task Query ต้องถูกค้นร่วมด้วยเป็น safety fallback และไม่นับรวมในเพดานดังกล่าว

GraphSearch จะค้น Triple candidates ของแต่ละ Query แยกกัน จากนั้น dedupe ด้วยตัวตนของ Triple ใช้ similarity สูงสุดของแต่ละ Triple และตัดกลับสู่ `top_k_triples` เดิมก่อนรัน PPR เพียงครั้งเดียว Relation ที่ไม่อยู่ใน Informative Relations จะถูกทิ้งโดยไม่ทำให้ Plan ล้ม

Assess จะได้รับเฉพาะ diagnostics แบบกระชับ ได้แก่ Ontology queries ที่ใช้, Top Triple candidates, Top PPR entities, returned chunk IDs และ abort reason ข้อมูลเหล่านี้เป็น retrieval hints ไม่ใช่หลักฐานตอบคำถาม Assess สามารถเลือก Informative Relation ใหม่สำหรับ Retry ได้ แต่มีเพียง retrieved chunks เท่านั้นที่เป็น Accepted Evidence รุ่นแรกไม่เพิ่ม Direct Graph Path lookup หรือ Bridge Cypher; ความสามารถดังกล่าวจะพิจารณาหลังวัดผลว่า relation normalization ยังแก้การขาดทอดกลางไม่ได้

## Consequences

- Query หลาย Relation ต้องค้นแยกกัน เพราะการรวม Relation ด้วย `or` อาจทำให้ Relation หนึ่งกลบอีก Relation ใน embedding ranking
- Candidate budget และ PPR call count คงเดิม จึงจำกัดผลกระทบต่อ latency
- ต้องวัดผลแบบ paired ablation ก่อนอ้างว่าคุณภาพ Graph retrieval ดีขึ้น ผลตรวจเฉพาะ NVIDIA เป็นเพียงหลักฐานเบื้องต้นของกลไก
