---
status: accepted
date: 2026-10-25
---

# Accept plain text chunks with normalized content-derived identity

ผู้ใช้เลือกส่ง `list[str]` โดยไม่ต้องตั้ง ID ระบบจึง normalize ข้อความเป็น Unicode NFC แล้วคำนวณ SHA256 แบบ namespaced จาก UTF-8 เป็น Chunk Identity ภายในฐานความรู้เดียวกัน ข้อความที่เทียบเท่ากันหลัง NFC จะมี ID เดียวกันและใช้ข้อความ normalized นี้ตลอด pipeline ทั้งตอนสกัด เก็บ แก้ตำแหน่งหลักฐาน และสร้าง embedding ข้อความที่เปลี่ยนหลัง normalize ถือเป็น chunk ใหม่ วิธีนี้ทำให้การเริ่มใช้งานและการส่งงานซ้ำง่าย โดยแลกกับการที่ระบบไม่สามารถรู้ว่า chunk ใหม่ตั้งใจแทนฉบับเก่า

## Consequences

- ช่องว่างและการขึ้นบรรทัดใหม่ยังเป็นส่วนหนึ่งของ identity; NFC เปลี่ยนเฉพาะ Unicode representation ที่เทียบเท่ากัน
- ข้อความเหมือนกันจากสองเอกสารมี identity เดียวกัน การอ้างถึงเอกสารหลายแหล่งต้องมี source/metadata เพิ่ม ไม่สามารถอนุมานจาก `list[str]`
- การนำเข้าใหม่ไม่ลบฉบับเก่า การแทนที่/ลบต้องเป็น API แยกที่มีขอบเขตชัดเจนในภายหลัง
- สถานะงานสำเร็จและ checkpoint ต้องผูกกับ pipeline/model fingerprint ด้วย เพื่อไม่ข้ามงานที่ทำด้วย config ที่เข้ากันไม่ได้
