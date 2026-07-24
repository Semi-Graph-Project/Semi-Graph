# 03 — Attempt Ledger, Assess, and Adaptive Retry

**What to build:** ทำให้ Full Agent ประเมินผลการค้นหาและตัดสิน retry จากหลักฐานจริง โดยหนึ่ง retrieval attempt ถูกเก็บเป็น record เดียว Assess รวม Observe, Reflect, Evidence Selection, Retry Feedback และ next action ใน LLM call เดียว ส่วน controller ใช้ Tool Retry Profiles ป้องกันการวนซ้ำและเลือก same-tool retry หรือ compatible fallback ตาม failure จริง

**Blocked by:** 02 — PlanRoute and Plan Validator.

**Status:** ready-for-agent

- [ ] ทุก Execute append Attempt ที่รวม Task/attempt identity, action, raw chunks, retrieval trace และ Assessment โดยไม่ overwrite รอบก่อน
- [ ] Technical Retry สำหรับ network/API/Neo4j/transport failure แยกจาก Evidence Retry และไม่กิน Agent Attempt budget; เมื่อ retry ทางเทคนิคหมดจึงบันทึก terminal tool error ที่ตรวจสอบได้
- [ ] Assess คืน Requirement coverage แบบ missing/partial/covered พร้อม supporting chunk IDs, accepted chunk IDs, decision และ structured Retry Feedback
- [ ] Retry Feedback ระบุ target Requirement IDs, failure type, preserved anchors, compact retrieval diagnostics, retry strategy และ optional next action
- [ ] Assess เห็น compact diagnostics ที่จำเป็น เช่น abort reason, selected seeds/triples, returned chunk IDs และ duplicate/zero-result signal โดยไม่รับ raw history ทั้งหมด
- [ ] accepted chunk IDs และ Requirement IDs ถูกตรวจเทียบกับข้อมูลจริง และ Assessment ที่ผิดซ่อมได้ไม่เกินหนึ่งครั้ง
- [ ] Evidence Gain เกิดเมื่อ coverage ดีขึ้นหรือ Requirement ได้ accepted supporting chunk ใหม่ ไม่ใช่เพียงได้ chunk ID ใหม่
- [ ] controller กลางใช้ declarative Tool Retry Profiles เพื่อยืนยันว่า failure type นั้นแก้ด้วย Tool เดิมได้จริง โดยไม่สร้าง workflow แยกต่อ Tool
- [ ] Graph retry ใช้ evidence-aware anchor enrichment, focus-missing หรือ bridge hint; Vector ใช้ focus-missing reformulation; Financial แก้เฉพาะ ticker/metric/period ที่มีใน intent; News retry query เฉพาะเมื่อ ticker/news intent ขาด
- [ ] Generic HyDE ไม่อยู่ในรุ่นแรก และ Graph/Vector/Financial/News Retriever configuration เดิมไม่ถูกเปลี่ยนโดย retry
- [ ] controller ปฏิเสธ exact repeated action, duplicate result set และ zero-result retry ที่ไม่เปลี่ยน action อย่างมีสาระ; semantic hints ที่กำกวมเป็น warning ไม่ใช่ hard rejection
- [ ] Same-tool-first ใช้เมื่อ Tool fit และ profile รองรับ strategy; tool mismatch เปลี่ยน Tool ได้ทันที ส่วน Tool เดิมที่ลองปรับแล้วไม่ gain เปลี่ยนได้เฉพาะ compatible fallback
- [ ] แต่ละ Task มีไม่เกินสาม Attempts; Attempt ที่สามเกิดได้เมื่อ Attempt ที่สองมี Evidence Gain หรือเมื่อ Tool เดิมไม่เพิ่มหลักฐานและมี compatible fallback Tool
- [ ] Raw Evidence Pool และ Accepted Evidence append/union แบบ deduplicate; retry ห้ามทำหลักฐานเดิมหาย และ coverage เปลี่ยนได้ทาง missing → partial → covered
- [ ] เมื่อ Assessment ซ่อมไม่สำเร็จ ระบบเก็บ latest unique chunks แบบ fail-open แล้วหยุดด้วย assessment_error โดยไม่ retry แบบเดาสุ่ม
