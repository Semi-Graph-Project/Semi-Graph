---
status: accepted
date: 2026-08-11
---

# Keep user evidence private and federate it at retrieval time

SemiGraph จะเก็บ User Sources และ assertions ที่สกัดได้ใน Personal Workspace ที่แยกและบังคับ owner scope โดยไม่ MERGE เข้า shared FinReflectKG Base Graph. User Evidence ใช้ Open Ontology ที่เปิด entity type และ predicate ใหม่ได้ แต่ทุก assertion ต้องมี provenance ขั้นต่ำกลับไปยัง source document และ exact source span. รุ่นแรกเปิดใช้ผลสกัดทันทีพร้อม `AI-extracted · unreviewed` label. ขณะค้น Agent เรียก System และ Personal retrievers แยกกัน เชื่อม entity candidates และรวมผลที่ Evidence Layer แทนการรัน PPR บน topology รวม เพราะ relation semantics และคุณภาพของ Open Ontology ยังไม่สม่ำเสมอพอที่จะแพร่คะแนนร่วมกับ Base Graph

## Consequences

- ทุก User Evidence record ต้องบังคับ `workspace_id`, source identity, exact provenance และ review status
- Company Workspace แสดง System Evidence, User Evidence และความขัดแย้งแยกกัน; User Evidence ห้าม overwrite System Evidence
- Path ที่ประกอบข้าม System และ Personal results ต้องแสดง `Agent-assembled path` ไม่ใช่ Disclosed Relationship
- บริษัทนอก Base Corpus สร้าง Company Workspace ได้ด้วย `Personal Evidence Only` coverage marker
- การลบ Source ถาวรต้องลบ raw และ derived data ทั้งหมดของ Source นั้นและคำนวณ Evidence Status ที่ได้รับผลใหม่
- Unified workspace-scoped graph projection เป็น future option หลังพิสูจน์ entity linking และ relation normalization แล้ว
