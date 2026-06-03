# Slide images — progress_slides.html

`progress_slides.html` อ้างอิงรูป 3 ไฟล์ในโฟลเดอร์นี้ บันทึกรูปที่ส่งให้ Claude
เป็นไฟล์ตามชื่อด้านล่าง (เป็น .png) แล้วสไลด์จะแสดงรูปอัตโนมัติ:

| ไฟล์ | คือรูป |
|---|---|
| `architecture.png` | สถาปัตยกรรมระบบเต็ม — User / Agent / Tools layer |
| `offline_pipeline.png` | Ingestion pipeline — SEC 10-K + Financial data → Neo4j / PostgreSQL |
| `graph_ppr.png` | Graph Retrieval Engine — Personalized PageRank |

## ⚠️ รูปบางส่วนไม่ตรงระบบปัจจุบัน — ควร regenerate ก่อนนำเสนอจริง

`offline_pipeline.png` และ `graph_ppr.png` มีองค์ประกอบที่ขัดกับระบบจริง:

- **GLiNER** — ตัดออกแล้ว ปัจจุบันสกัด entity + relation ด้วย LLM (DeepSeek) ในการเรียกครั้งเดียว
- **Yahoo Finance** (ในรูป offline) — Pipeline 2 ใช้ข้อมูล SEC XBRL
- **bge-large-en** (ในรูป offline) — โมเดล embedding จริงคือ `BAAI/bge-base-en-v1.5` (768 มิติ)
