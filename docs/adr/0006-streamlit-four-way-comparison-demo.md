---
status: accepted
date: 2026-08-21
---

# Build the four-way comparison as a separate Streamlit demo

SemiGraph จะสร้าง `Four-Way Comparison Demo` เป็น Streamlit surface ใหม่ที่แยกจาก Production App และใช้ Agent Core กับ Retriever เดิมร่วมกันตามขอบเขตของ ADR 0003. หน้านี้มีไว้สาธิต `2 × 2 Ablation` ให้กรรมการเห็นผลของการเพิ่ม Agent Controller และ Graph Retrieval ผ่านสี่ Configurations คือ `Vector-only RAG`, `Graph-only RAG`, `Agentic Vector RAG` และ `Agentic GraphRAG`.

หนึ่ง `Comparison Run` รับคำถามแบบ single-turn หนึ่งครั้งแล้ว fan out ไปยังทั้งสี่ Configurations พร้อมกันจริง โดยแต่ละ Run ย่อยสำเร็จ ล้มเหลว หมดเวลา หรือถูกยกเลิกได้อย่างอิสระ. เพื่อให้เปรียบเทียบอย่างยุติธรรม ทั้งสี่ใช้คำถาม, Main Corpus snapshot, LLM, answer prompt, evidence budget และ citation format เดียวกัน และต่างกันเฉพาะ Retriever กับการมีหรือไม่มี Agent Controller. Demo อ่าน Main SemiGraph Corpus ผ่าน Config เท่านั้น ห้าม hard-code Controlled Evaluation Corpus หรือ `gold_chunk_embedding`.

## Consequences

- Streamlit Demo ไม่มี authentication, persistent workspace, background-job infrastructure หรือ Production navigation และ UI code ของ Demo ไม่ถูกนำไปใช้เป็น Production surface.
- รุ่นแรกไม่รองรับ multi-turn memory; คำถามใหม่สร้าง Comparison Run ใหม่ แม้ UI จะเก็บผล Run ก่อนหน้าไว้ดูย้อนหลังได้.
- ทั้งสี่ผลลัพธ์แสดงสถานะ คำตอบ Citation และ technical trace แยกกัน โดยความล้มเหลวของ Configuration หนึ่งต้องไม่ยกเลิกอีกสาม Configuration.
- Live latency ใช้อธิบายเวลาของ Run นั้นเท่านั้น เพราะการรันพร้อมกันมี resource contention; ข้อสรุปด้านคุณภาพและประสิทธิภาพเชิงวิจัยต้องอ้างอิง Controlled Offline Benchmark.
- Shared answer generation ต้องเป็นไปตาม ADR 0005 เพื่อไม่ให้ความต่างของ Answer Prompt กลายเป็นตัวแปรแทรกในการเปรียบเทียบ.
