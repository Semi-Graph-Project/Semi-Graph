# Phase T2.1 Retrieval Rerank Report

Generated: 2026-06-29

## What Changed

T2.1 แก้คอขวดหลัง PPR: เดิม Graph Search หา entity ได้ แต่ตอน map entity กลับไปเป็น chunk ยังเลือกหลักฐานกว้างเกินไป เช่น risk query ไปติด `Item_1` หรือ product query ไปติด chunk AMD ทั่วไปแทน chunk ที่มีคำตอบจริง

เพิ่มใน `src/semigraph/online/graph_search.py`:

- ดึง candidate กว้างขึ้นก่อนตัด top-k: `candidate_k = min(top_k * 4, 40)`
- เพิ่ม section-aware rerank:
  - risk/supply/exposure/geopolitical → boost `Item_1A`
  - product/supplier/foundry/segment → boost `Item_1`
  - revenue/gross margin/FY/EPS → boost `Item_7`
- เพิ่ม ticker boost เมื่อ query มี ticker ตรง ๆ เช่น `AMD`, `NVDA`, `ENTG`
- เพิ่ม lexical evidence boost จากคำสำคัญใน query/effective query เช่น `Instinct`, `Hopper`, `HBM`, `TSMC`
- ใช้ `effective_query` หลัง query expansion ตอน rerank เพื่อให้ LLM hint เช่น `AMD Instinct MI` มีผลกับการจัดอันดับ chunk

เพิ่ม regression tests:

- `tests/test_graph_search_rerank.py`
- ครอบคลุม risk section boost, business section boost, lexical answer-bearing boost, deterministic order

## Metric Comparison

Scored queries = 7 queries ที่มี `gold_chunks` ใน `data/evaluate/phase_t_multihop_queries.yaml`

| Run | Graph Hit@5 | Graph Recall@5 | Graph MRR@5 | Graph Oracle@10 | Hybrid Hit@5 | Hybrid Recall@5 | Hybrid MRR@5 | Hybrid Oracle@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline no expansion `140019` | 0.143 | 0.143 | 0.048 | 0.429 | 0.286 | 0.171 | 0.286 | 0.429 |
| T2.1 no expansion `154627` | 0.429 | 0.207 | 0.226 | 0.714 | 0.571 | 0.457 | 0.464 | 0.714 |
| Baseline expansion `151532` | 0.429 | 0.400 | 0.314 | 0.429 | 0.429 | 0.371 | 0.243 | 0.571 |
| T2.1 expansion `154002` | 0.571 | 0.471 | 0.350 | 0.714 | 0.714 | 0.557 | 0.571 | 0.714 |

Bottom line: T2.1 ทำให้ Graph/PPR เริ่มมี advantage เหนือ vector baseline เดิมในชุดเล็กนี้ โดยเฉพาะ Hybrid หลัง rerank+expansion ได้ `Hit@5 = 0.714` และ `MRR@5 = 0.571`

## Query-Level Notes

### T004: Intel rival → AMD Instinct

ก่อนแก้ lexical/effective-query rerank, Graph เคยได้ AMD chunks แต่ไม่ใช่ chunk ที่มีคำตอบ `Instinct`

หลังแก้:

- Graph rank 1: `AMD_2026_Item_1_0003_ea53a6a5`
- Hybrid rank 1: `AMD_2026_Item_1_0003_ea53a6a5`

นี่คือสัญญาณว่า PPR หา neighborhood ถูกแล้ว และ rerank ช่วยเลือก evidence ที่ตอบคำถามจริง

### T003: dense memory chips / AI accelerators

หลัง T2.1 expansion:

- Graph hit ด้วย `NVDA_2024_Item_1_0007_bae70036` และ `NVDA_2025_Item_1_0008_a4407f7e`
- Hybrid hit rank สูงขึ้น

แต่ยังไม่ดึง MU Item 1A ได้ดีพอ แปลว่า memory/HBM path ใน graph ยังน่าจะไหลไป NVDA/RMBS/INTC มากกว่า MU ต้อง trace ต่อใน T2.2

### T001: AMD → TSMC supply risk

ยังเป็นเคสยาก:

- Graph no-expansion เจอ gold ใน Oracle@10 แต่ยังไม่ติด top-5
- Hybrid no-expansion ติด gold rank 1
- Expansion บางรอบกลับทำให้ T001 miss เพราะ LLM hint ไม่เสถียรและทำให้ graph side ดัน risk chunks จากบริษัทอื่น

ข้อสรุป: ต้องเพิ่ม confidence-aware hybrid หรือ ticker/year-aware boost เพิ่ม ไม่ใช่พึ่ง LLM expansion อย่างเดียว

## Current Problems After T2.1

1. LLM query expansion ไม่ deterministic
   - query เดียวกันบางรอบได้ hint ต่างกัน
   - บางรอบ invalid hint shape แล้ว fallback
   - ทำให้ evaluation noise สูง

2. Hybrid RRF ยังไม่รู้ confidence
   - ถ้า graph candidate ดีมาก ควรให้ graph ชนะ
   - ถ้า graph drift ไปบริษัทอื่น ควรลดน้ำหนัก graph
   - ตอนนี้ RRF รวม rank แบบเท่ากัน

3. Graph chunk mapping ยังไม่ใช้ fiscal-year/latest preference
   - T001 ยังติด AMD 2025 risk ก่อน AMD 2026 risk
   - ถ้า query ไม่ระบุปี ควรมี policy ว่า latest filing มี boost เล็กน้อยหรือไม่

4. Off-corpus guard ยังอ่อน
   - query noise ยังสร้าง seeds ได้
   - ต้องเพิ่ม seed confidence threshold / reject policy

## Verification

Commands run:

```bash
python -m py_compile src/semigraph/online/graph_search.py
pytest tests/test_graph_search_rerank.py -q
HF_HUB_OFFLINE=1 conda run -n senior_project python scripts/evaluate_retrieval_quality.py --tools graph hybrid --top-k 5 --oracle-k 10
HF_HUB_OFFLINE=1 conda run -n senior_project python scripts/evaluate_retrieval_quality.py --tools graph hybrid --top-k 5 --oracle-k 10 --no-llm-expansion
```

Results:

- `pytest`: 5 passed
- Latest expansion report: `analytics/phase_t_retrieval_baseline_20260629_154002.md`
- Latest no-expansion report: `analytics/phase_t_retrieval_baseline_20260629_154627.md`

## Next Step

T2.2 ควรทำ deterministic expansion + expansion cache ก่อน เพราะถ้า query expansion ยังแกว่ง การวัด tuning แต่ละรอบจะไม่ค่อยน่าเชื่อถือ

ลำดับแนะนำ:

1. เพิ่ม rule-based domain expansion ก่อน LLM เช่น `x86 rival -> AMD`, `AI accelerator AMD -> Instinct`, `foundry partner -> TSMC`
2. cache LLM expansion ตาม normalized query
3. เพิ่ม metadata ใน result ว่า expansion ใช้ hint อะไร
4. rerun benchmark แบบ deterministic กว่านี้
5. ค่อยทำ confidence-aware Hybrid ต่อ
