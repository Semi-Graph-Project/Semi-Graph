---
status: accepted
date: 2026-08-11
---

# Separate the production app from the Streamlit demo

SemiGraph จะสร้าง Production App เป็น web frontend ที่เรียก Agent Core ผ่าน application API และใช้ persistent services สำหรับ Personal Workspace, Thesis Board, User Sources และ background research jobs โดยไม่ต่อยอด Streamlit UI เป็น production surface เพราะ session, routing, asynchronous jobs, responsive Evidence Map และ authorization ของผลิตภัณฑ์จริงต้องการ lifecycle ที่แยกจาก Streamlit rerun model. `app.py` ยังคงเป็น project demo สำหรับ defense, evaluation และ debugging; สอง surface ใช้ Agent Core และ serializable contracts ร่วมกัน แต่ไม่ใช้ UI state หรือ UI code ร่วมกัน

## Consequences

- Agent Core ต้องมี API-safe request, event, result และ citation contracts ที่ไม่ผูกกับ Streamlit
- Production App เป็นเจ้าของ authentication, navigation, background-job UX และ persistent user state
- Streamlit-specific การตั้งค่า locked Agent modes และ technical traces ไม่กลายเป็น production navigation
- การเปลี่ยน production frontend ในอนาคตไม่ต้องรื้อ Agent Core
