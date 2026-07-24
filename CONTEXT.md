# SemiGraph Agent Harness

คำศัพท์ร่วมของ Agent Harness ที่ควบคุมการเลือก Retriever การประเมินหลักฐาน และการลองค้นใหม่ใน SemiGraph

## Language

**Retrieval Task**:
หน่วยงานค้นหลักฐานหนึ่งเรื่องที่มีเป้าหมายและ Evidence Requirements ร่วมกัน โดยธรรมชาติของคำถามเป็นตัวกำหนดขอบเขตของ Task
_Avoid_: Subquery step, workflow step

**Graph Task**:
Retrieval Task ที่ต้องรักษา connected relationship chain ไว้เป็นหน่วยเดียว เพื่อไม่ให้สัญญาณ multi-hop ถูกตัดขาด
_Avoid_: Graph hop, split hop

**Evidence Requirement**:
ข้อความระบุว่าหลักฐานต้องรองรับ claim หรือส่วนใดของ Retrieval Task จึงจะถือว่าครบ
_Avoid_: Subquery, answer fragment

**Retrieval Action**:
คำสั่งค้นหนึ่งครั้งที่ระบุ Tool และ query สำหรับ Evidence Requirements เป้าหมาย
_Avoid_: Tool call plan

**Attempt**:
ผลการทำ Retrieval Action หนึ่งครั้ง พร้อมหลักฐานและข้อมูลวินิจฉัยที่เกิดจากการค้นครั้งนั้น
_Avoid_: Round, retry count

**Technical Retry**:
การลอง Retrieval Action เดิมใหม่เพราะระบบภายนอกหรือการเชื่อมต่อล้มเหลว โดยยังไม่มีผลการค้นให้ประเมิน
_Avoid_: Evidence Retry

**Evidence Retry**:
การค้นใหม่หลังผลเดิมไม่พบหลักฐาน พบไม่ครบ ไม่เกี่ยวข้อง หรือซ้ำ โดยใช้ Retrieval Feedback เปลี่ยน action อย่างมีเหตุผล
_Avoid_: Technical Retry, blind retry

**Retry Feedback**:
คำวินิจฉัยแบบมีโครงสร้างที่ระบุสิ่งที่ยังขาด สาเหตุของความล้มเหลว anchors ที่ต้องรักษา และกลยุทธ์สำหรับ Retrieval Action ถัดไป
_Avoid_: Reflection text, free-form feedback

**Tool Retry Profile**:
ข้อตกลงว่า Tool หนึ่งรองรับ Evidence Retry แบบใดสำหรับ failure แต่ละชนิด
_Avoid_: Tool workflow

**Evidence Gain**:
ความคืบหน้าที่เกิดเมื่อ Evidence Requirement มีสถานะดีขึ้นหรือได้รับหลักฐานรองรับใหม่ ไม่ใช่เพียงการพบ chunk ID ใหม่
_Avoid_: New result, new chunk

**Raw Evidence Pool**:
ชุดหลักฐานไม่ซ้ำทั้งหมดจากทุก Attempt ที่เก็บไว้เพื่อ audit, debugging และวัด retrieval coverage
_Avoid_: Answer context

**Accepted Evidence**:
หลักฐานจาก Raw Evidence Pool ที่ถูกจับคู่กับ Evidence Requirement ว่ารองรับโดยตรง
_Avoid_: Retrieved chunks

**Evidence Quality**:
ระดับที่หลักฐานรองรับ Evidence Requirements โดยตรงและเพิ่ม coverage ไม่ใช่ความใหม่ของ Attempt หรือความมั่นใจลอย ๆ ของโมเดล
_Avoid_: LLM confidence, latest result

**Synthesis Context**:
ชุด Accepted Evidence ที่คัดตาม coverage ภายในงบ context เพื่อใช้สร้างคำตอบสุดท้าย
_Avoid_: Raw Evidence Pool
