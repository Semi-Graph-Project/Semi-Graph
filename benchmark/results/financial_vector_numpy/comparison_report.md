# Financial SQL vs NumPy Vector Retrieval

## Experimental setup

การทดลองนี้เปรียบเทียบ retrieval บนข้อมูลต้นทางเดียวกัน โดย export curated PostgreSQL views ของบริษัทใน Agent scope 14 แห่งเป็น fact documents จำนวน 2,632 documents จากนั้น embed ด้วย `BAAI/bge-base-en-v1.5` และจัดอันดับด้วย NumPy dot product ซึ่งเท่ากับ cosine similarity เมื่อ embeddings ถูก normalize แล้ว

ใช้คำถามชุด `financial_agent_e2e_60.yaml` จำนวน 60 ข้อ โดยวัด retrieval เฉพาะ 48 คำถามที่มีคำตอบและ Gold rows รวม 84 แถว การตรวจสอบก่อนทดลองยืนยันว่า Gold ทั้ง 84 แถวอยู่ใน Vector corpus ครบถ้วน จึงไม่มีความเสียเปรียบจากข้อมูลหายก่อนค้นหา ส่วน SQL reference มาจาก Agent run `20260718_180149` ซึ่งดึง Gold ได้ 84/84 แถวและไม่คืนแถวเกิน Gold

## Main result: top-k = 5

| Metric | NumPy Vector | Financial SQL | SQL - Vector |
|---|---:|---:|---:|
| Gold-row recall | 95.24% (80/84) | 100.00% (84/84) | +4.76 pp |
| Complete evidence rate | 93.75% (45/48) | 100.00% (48/48) | +6.25 pp |
| Precision ของแถวที่คืน | 33.33% (80/240) | 100.00% (84/84) | +66.67 pp |

Vector ดึงหลักฐานครบ 100% สำหรับ single-company lookup, multi-year trend และ derived metric แต่ครบเพียง 75% (9/12 ข้อ) สำหรับ multi-company comparison ข้อที่ไม่ครบคือ `FIN-E2E-015`, `FIN-E2E-016` และ `FIN-E2E-021`

สาเหตุที่พบคือ semantic ranking มักจัดแถวของบริษัทหนึ่งหลายปีไว้เหนือแถวของบริษัทที่สอง เช่น คำถามเปรียบเทียบ AMD กับ INTC คืน AMD หลายปีก่อน INTC และคำถาม R&D intensity คืน reported R&D expense ซึ่งมีคำใกล้เคียงแทน derived metric ที่ถาม

## Top-k sensitivity

| top-k | Gold-row recall | Complete evidence | Precision |
|---:|---:|---:|---:|
| 5 | 95.24% | 93.75% | 33.33% |
| 10 | 95.24% | 93.75% | 16.67% |
| 100 | 100.00% | 100.00% | 1.75% |

การเพิ่มจาก top-5 เป็น top-10 ไม่ทำให้ได้ Gold เพิ่ม แต่ลด precision ลงครึ่งหนึ่ง Gold ที่หายอยู่ที่อันดับ 11, 13, 20 และ 32 จึงต้องเพิ่มถึง candidate pool ขนาดใหญ่เพื่อให้ recall ครบ ซึ่งทำให้ Agent ต้องรับเอกสารรบกวนจำนวนมากกว่า SQL อย่างชัดเจน

## Interpretation

ผลนี้สนับสนุนว่า SQL เหมาะกว่าสำหรับคำถามการเงินเชิงตัวเลขที่ต้องรักษาเงื่อนไขบริษัท metric และ fiscal period พร้อมกัน เนื่องจาก SQL คืนชุดแถวที่ครบและตรงเงื่อนไขโดยไม่ต้องแลกกับ candidate pool ขนาดใหญ่ อย่างไรก็ตาม ผลนี้เป็น retrieval-only evaluation ยังไม่ได้วัด Vector Agent synthesis หรือ abstention และไม่สามารถใช้สรุปว่า SQL เหมาะกว่า Vector สำหรับข้อความเชิงคุณภาพ เช่น กลยุทธ์ ความเสี่ยง หรือข่าว

## Evidence

- Vector corpus: `benchmark/datasets/financial_vector_facts.jsonl`
- Corpus metadata: `benchmark/datasets/financial_vector_facts.meta.json`
- Evaluator: `scripts/evaluate_financial_vector_numpy.py`
- top-5 run: `benchmark/results/financial_vector_numpy/20260718_213616/`
- top-10 run: `benchmark/results/financial_vector_numpy/20260718_213414/`
- top-100 run: `benchmark/results/financial_vector_numpy/20260718_213509/`
- SQL reference: `benchmark/results/financial_agent_e2e/20260718_180149/`

