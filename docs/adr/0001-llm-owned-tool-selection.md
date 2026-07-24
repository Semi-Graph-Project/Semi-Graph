---
status: accepted
date: 2026-07-22
---

# LLM owns Full Agent tool selection

Full Agent ให้ PlanRoute และ Assess LLM เลือก Tool จาก capability contract ของ Tool ที่ลงทะเบียนไว้ และยกเลิก Keyword-Based Financial Override ที่เคยบังคับ Financial Tool จากคำอย่าง revenue, margin หรือ fiscal period เพราะคำเหล่านี้ไม่ได้พิสูจน์ว่าคำถามต้องการ structured financial data; baseline 20 queries พบ Financial 69 จาก 103 calls และ 65 calls คืนศูนย์. Deterministic code มีหน้าที่ตรวจ schema, Tool availability, arguments, budget, action novelty และ Evidence Gain โดยปฏิเสธ action ที่ผิดได้ แต่ห้ามแทนที่ Tool ที่ LLM เลือกใน normal path; Financial Tool ยังคงเป็น Tool ปกติ ส่วน locked Agent+Vector/Agent+Graph modes ยังคงเป็น deliberate evaluator controls.

## Consequences

- Tool capability descriptions และ trace ของเหตุผลเลือก Tool กลายเป็น contract สำคัญของ Planner/Assess.
- Retry หลัง zero result ต้องกลับให้ Assess เสนอ action ใหม่ ไม่ fallback ไป Financial จาก keyword.
- หาก PlanRoute ยัง invalid หลังซ่อมหนึ่งครั้ง ให้ใช้ deterministic error fallback ที่ไม่เรียก Keyword-Based Financial Override และบันทึก `plan_error`/fallback source ชัดเจน.
