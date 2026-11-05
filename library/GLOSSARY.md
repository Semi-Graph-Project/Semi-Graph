# SemiGraph Library Glossary

คำศัพท์ของ library สำหรับสร้างฐานความรู้จากข้อความของผู้ใช้และค้นหลักฐานจากฐานนั้น

## Language

**Free Ontology**:
ชนิด entity และความสัมพันธ์ที่สกัดตามข้อความ โดยผู้ใช้ไม่ต้องเตรียมรายการชนิดล่วงหน้า โครงสร้างข้อมูลและข้อกำหนดเรื่องแหล่งหลักฐานยังคงตายตัว
_Avoid_: ไม่มี schema, ไม่มี validation

**Input Chunk**:
ข้อความหนึ่งก้อนที่ผู้ใช้แบ่งมาแล้ว และต้องเก็บข้อความต้นฉบับไว้เพื่อค้นและอ้างอิง
_Avoid_: เอกสารต้นฉบับทั้งฉบับ, extracted fact

**Chunk Identity**:
ตัวระบุที่สร้างจากข้อความ Input Chunk แบบตรงตัว ข้อความเหมือนกันถือเป็น chunk เดียวกันในฐานความรู้เดียวกัน
_Avoid_: document identity, ลำดับในรายการนำเข้า

**Observed Relations**:
รายการชนิดความสัมพันธ์ที่พบในฐานความรู้แล้ว พร้อมคำอธิบายสำหรับช่วยค้น รายการนี้ไม่จำกัดชนิดใหม่ที่การสกัดจะสร้างได้
_Avoid_: allowed ontology, fixed catalog

**Evidence Assertion**:
ข้อเท็จจริงรูป entity–relation–entity ที่สกัดจากข้อความ พร้อมตำแหน่งข้อความที่รองรับและ Chunk Identity ต้นทาง
_Avoid_: verified truth, inference without evidence

**Knowledge Base**:
ชุดข้อความและข้อมูลอนุพันธ์ที่ใช้ค้นร่วมกัน อยู่ภายใต้การตั้งค่าการสกัดและ embedding ที่ตรวจความเข้ากันได้แล้ว
_Avoid_: shared project database, user account

**Ingestion Report**:
ผลการนำเข้าหนึ่งชุดที่แสดงว่าแต่ละ chunk สำเร็จ ถูกข้าม หรือล้มเหลว และฐานความรู้พร้อมค้นหรือไม่
_Avoid_: success boolean

**Retrieval Result**:
หลักฐานที่เลือกให้คำถามหนึ่ง พร้อมคำตอบเมื่อร้องขอ และข้อมูลติดตามการค้นที่มีจริง
_Avoid_: all attempted chunks, guaranteed correct answer

**Retrieve Only**:
การคืนหลักฐานโดยข้ามการสร้างคำตอบสุดท้าย หากเลือก Agent ยังอาจใช้ LLM วางแผนและประเมินหลักฐาน
_Avoid_: no LLM, vector-only

**Task-specific Agent**:
ตัวควบคุมการค้นที่แบ่งคำถามเป็นงาน วนค้นและประเมินหลักฐานของแต่ละงาน แล้วรวบรวมหลักฐานตามงบที่กำหนด
_Avoid_: DeepAgent, single-pass retrieval
