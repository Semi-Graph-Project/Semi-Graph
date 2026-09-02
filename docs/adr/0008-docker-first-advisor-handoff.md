# Docker-first advisor handoff

SemiGraph จะส่งต่อให้อาจารย์ผ่าน Docker-based Reference Runtime เพื่อให้เปิดบริการ รัน Smoke/Demo และรัน Full Evaluation ได้โดยไม่ต้องสร้าง Python และ Neo4j environment บนเครื่องใหม่เอง ส่วน Unit Test เดิมยังคงเป็นเครื่องมือของผู้พัฒนา แต่ไม่ใช่ขั้นตอนบังคับของผู้รับช่วง วิธีนี้เลือกแทน source-only archive ที่สร้างสถานะเดิมซ้ำได้ยาก และแทน virtual-machine image ที่มีขนาดใหญ่และผูกกับเครื่องมากกว่า

ชุดส่งมอบต้องไม่ฝังหรือส่งต่อ API key เดิม อาจารย์เป็นผู้ใส่ `OPENROUTER_API_KEY` ของตนเองสำหรับ Full Evaluation โดย Smoke ที่ไม่ใช้ LLM ต้องรันได้ก่อนมี key และคำสั่ง Full Evaluation ต้องตรวจ key พร้อมแจ้งข้อผิดพลาดที่แก้ตามได้ก่อนเริ่มงานที่มีค่าใช้จ่าย

เครื่องเป้าหมายเป็น Windows และให้อาจารย์สั่งงานผ่าน PowerShell โดย Docker Desktop จัดการ Linux-container backend ภายใน Source code อยู่ใน private GitHub repository และ mount เข้า application container เพื่อให้แก้แล้วรันใหม่ได้โดยไม่ต้องสร้าง image ทุกครั้ง ส่วน application image อยู่ใน private GitHub Container Registry และฐานข้อมูลใช้ Docker named volumes แทน path เฉพาะเครื่อง
