# SemiGraph

คำศัพท์ร่วมของ Agent Harness และ Production Research Experience ที่ใช้ค้น เชื่อม และตรวจสอบหลักฐานสำหรับการวิเคราะห์ปัจจัยพื้นฐานบริษัท semiconductor

## Agent Harness Language

**Agentic GraphRAG**:
ระบบหลักของ SemiGraph ที่ให้ Agent วางแผน ค้น และประเมินหลักฐานจาก Knowledge Graph/PPR โดยใช้ Vector RAG และการค้นที่ไม่มี Agent เป็นตัวควบคุมในการเปรียบเทียบ
_Avoid_: Full Agent, generic Agentic RAG

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

**Question Point**:
ส่วนหนึ่งของ Original Query ที่สามารถตรวจคำตอบแยกจากส่วนอื่นได้ โดยต้องดึงจากคำถามเท่านั้น ไม่ใช่จาก Gold Answer หรือแผนของ Agent
_Avoid_: Evidence Requirement, Gold Answer Point

**Draft Answer**:
คำตอบจากการอ่าน Original Query และหลักฐานที่ค้นได้รอบแรก ซึ่งยังไม่ถือเป็นคำตอบสุดท้ายจนกว่าจะผ่าน Evidence Audit
_Avoid_: Final Answer

**Evidence Audit**:
การตรวจ Draft Answer เทียบกับ Original Query และหลักฐานทั้งหมดอีกครั้ง เพื่อเติม Question Point ที่มีหลักฐานรองรับแต่ตกหล่น และแก้รายละเอียดที่ผิดก่อนสร้าง Final Answer
_Avoid_: Agent Assess, Answer reranking

## Production Research Language

**Personal Workspace**:
พื้นที่ส่วนตัวของผู้ใช้หนึ่งคน ซึ่งเป็นเจ้าของ Company Workspaces, Theses, Evidence Snapshots, User Sources และ Chat Threads ของตน
_Avoid_: Account data, user session

**Company Workspace**:
พื้นที่วิจัยบริษัทหนึ่งแห่งภายใน Personal Workspace ที่รวม Research Lenses, Evidence Maps, Thesis Board และ Source Scope ของบริษัทนั้น
_Avoid_: Company dashboard, ticker page

**Coverage Mode**:
ขอบเขตแหล่งข้อมูลที่ Company Workspace ใช้ได้ เช่น System + Personal Evidence หรือ Personal Evidence Only
_Avoid_: Data completeness, confidence level

**Research Lens**:
มุมมองการวิจัยบริษัทที่มีเป้าหมายหลักฐานเฉพาะ โดย SemiGraph ใช้ห้า Lens คือ Core Business, Growth Thesis, Dependencies, Risks และ MOAT
_Avoid_: Report section, analysis tab

**Thesis**:
ข้อความสมมติฐานที่ผู้ใช้เป็นเจ้าของและต้องการตรวจสอบด้วยหลักฐาน Agent เสนอหรือแนะนำการแก้ได้ แต่เปลี่ยนข้อความไม่ได้หากผู้ใช้ไม่ยืนยัน
_Avoid_: Agent conclusion, investment recommendation

**Growth Thesis**:
Thesis ที่ระบุเส้นทางซึ่งอาจทำให้ธุรกิจเติบโต พร้อมตัวขับเคลื่อน เงื่อนไข หลักฐานท้าทาย และสิ่งที่ยังไม่รู้ โดยไม่ใช่ forecast
_Avoid_: Growth prediction, revenue forecast

**Evidence Map**:
แผนที่ขนาดเล็กที่คัดเฉพาะข้ออ้าง ความสัมพันธ์ และหลักฐานที่เกี่ยวกับคำถามหรือ Research Lens ปัจจุบัน ไม่ใช่การแสดง Knowledge Graph ทั้งหมด
_Avoid_: Knowledge Graph viewer, reasoning graph

**Evidence Path**:
ลำดับของ entity และ relationship ใน Evidence Map ที่แต่ละช่วงย้อนกลับไปยังหลักฐานต้นทางได้ แต่ไม่ได้พิสูจน์เหตุและผลโดยอัตโนมัติ
_Avoid_: Causal chain, chain-of-thought

**Disclosed Relationship**:
ความสัมพันธ์ที่มีแหล่งข้อมูลยืนยันโดยตรงว่า entity สองตัวเกี่ยวข้องกันตาม relationship นั้น
_Avoid_: Proven relationship, causal fact

**Agent-Assembled Path**:
Evidence Path ที่ Agent ประกอบจากหลาย Disclosed Relationships หรือหลายแหล่ง จึงเป็นข้ออนุมานที่ต้องแสดงต่างจากความสัมพันธ์ที่เปิดเผยโดยตรง
_Avoid_: Disclosed Relationship, causal conclusion

**Evidence Status**:
สถานะความครบและสมดุลของหลักฐานต่อ Thesis โดยใช้ Evidence Supported, Evidence Mixed, Insufficient Evidence หรือ Review Due
_Avoid_: Confidence score, bullish/bearish rating

**Evidence Snapshot**:
บันทึกผลประเมินที่แก้ย้อนหลังไม่ได้ของ Thesis version, Evidence Status, Evidence mappings และ source watermarks ณ เวลาที่ตรวจสอบรอบหนึ่ง โดยอนุญาตให้ redact เนื้อหาของ Source ที่ผู้ใช้ลบถาวรได้
_Avoid_: Chat history, latest result

**System Evidence**:
หลักฐานจาก corpus และแหล่งข้อมูลที่ SemiGraph ดูแล ซึ่งแสดงแยกจากหลักฐานที่ผู้ใช้เพิ่ม
_Avoid_: Trusted truth, default answer

**User Source**:
ไฟล์หรือเอกสารต้นทางที่ผู้ใช้อัปโหลดเข้า Personal Workspace ซึ่งยังไม่ถือเป็นหลักฐานจนกว่าจะสกัดข้อความหรือข้อเท็จจริงที่อ้างย้อนได้
_Avoid_: User Evidence, uploaded evidence

**User Evidence**:
ข้อความ ข้อเท็จจริง หรือความสัมพันธ์ที่สกัดจาก User Source และมี provenance กลับไปยังตำแหน่งต้นทาง โดยรุ่นแรกติดสถานะ AI-extracted และ unreviewed
_Avoid_: System Evidence, User Source

**Source Scope**:
ชุด System Evidence และ User Sources ที่อนุญาตให้ Agent ใช้กับคำถาม Company Workspace หรือ Chat Thread หนึ่ง
_Avoid_: Search filter, corpus
