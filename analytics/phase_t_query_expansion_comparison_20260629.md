# Phase T Query Expansion Comparison

Generated: 2026-06-29

## Goal

ก่อนเข้า T2 ต้องเช็คก่อนว่า LLM query expansion ช่วย Graph/PPR retrieval จริงไหม หรือปัญหาเกิดจาก PPR/chunk mapping เป็นหลัก

ใช้ชุดคำถามเดียวกัน:

- `data/evaluate/phase_t_multihop_queries.yaml`
- scored queries = 7/16 เพราะ query ที่ไม่มี `gold_chunks` เป็น discovery-only

## Runs

No-expansion baseline:

```bash
HF_HUB_OFFLINE=1 conda run -n senior_project python scripts/evaluate_retrieval_quality.py --tools graph hybrid --top-k 5 --oracle-k 10 --no-llm-expansion
```

Expansion baseline:

```bash
HF_HUB_OFFLINE=1 conda run -n senior_project python scripts/evaluate_retrieval_quality.py --tools graph hybrid --top-k 5 --oracle-k 10
```

Vector reference:

```bash
HF_HUB_OFFLINE=1 conda run -n senior_project python scripts/evaluate_retrieval_quality.py --tools vector --top-k 5 --oracle-k 10
```

## Aggregate Result

| Run | Tool | Hit@5 | Recall@5 | MRR@5 | Oracle Hit@10 | Avg Latency |
|---|---|---:|---:|---:|---:|---:|
| No expansion | Graph | 0.143 | 0.143 | 0.048 | 0.429 | 3.97s |
| Expansion | Graph | 0.429 | 0.400 | 0.314 | 0.429 | 9.97s |
| No expansion | Hybrid | 0.286 | 0.171 | 0.286 | 0.429 | 2.29s |
| Expansion | Hybrid | 0.429 | 0.371 | 0.243 | 0.571 | 6.46s |
| Reference | Vector | 0.429 | 0.314 | 0.357 | 0.571 | 0.93s |

## Main Finding

Query expansion มีผลเชิงบวกชัดเจนกับ Graph/PPR:

- Graph Hit@5 ดีขึ้นจาก 0.143 เป็น 0.429
- Graph Recall@5 ดีขึ้นจาก 0.143 เป็น 0.400
- Hybrid Hit@5 ดีขึ้นจาก 0.286 เป็น 0.429
- Hybrid Recall@5 ดีขึ้นจาก 0.171 เป็น 0.371

แต่ยังพูดว่า "ชนะ Vector อย่างมีนัยสำคัญ" ไม่ได้ เพราะ:

- scored queries มีแค่ 7 ข้อ ยังเล็กเกินสำหรับสรุปทางสถิติ
- Graph+expansion เสมอ Vector ที่ Hit@5 แต่แพ้ Vector ที่ MRR
- Hybrid+expansion เสมอ Vector ที่ Hit@5 และ Oracle Hit@10 แต่แพ้ Vector ที่ MRR
- latency สูงกว่า Vector มาก

สรุปแบบ practical: expansion สำคัญกับ Graph/PPR แต่ยังไม่ใช่คำตอบสุดท้าย

## Per-Query Change

| ID | Type | Graph No Exp | Graph Exp | Hybrid No Exp | Hybrid Exp | Change |
|---|---|---:|---:|---:|---:|---|
| T001 | graph_multihop | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | ไม่ช่วย |
| T002 | supplier_via_product | 0 / 0.0 | 1 / 0.8 | 1 / 0.2 | 1 / 0.6 | ช่วยมาก |
| T003 | supplier_via_product | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | ไม่ช่วย |
| T004 | competitor_product | 0 / 0.0 | 1 / 1.0 | 0 / 0.0 | 1 / 1.0 | ช่วยมาก |
| T010 | vector_friendly | 1 / 1.0 | 1 / 1.0 | 1 / 1.0 | 1 / 1.0 | คงเดิม |
| T011 | vector_friendly | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | ไม่ช่วย |
| T012 | vector_friendly | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | ไม่ช่วย |

## What Expansion Helped

### T002 Hopper -> TSMC/foundry

No expansion:

- Graph top chunks ไป Item 7 / RMBS / MD&A noise
- gold อยู่ oracle@10 แต่ไม่ขึ้น top 5

Expansion hints:

- `NVDA Hopper TSMC foundry architecture`
- `TSMC NVDA Hopper foundry`

ผล:

- Graph ดัน gold ขึ้น top 5 ได้ 4/5 gold chunks
- Hybrid recall ดีขึ้นจาก 0.2 เป็น 0.6

แปลว่า seed stage ต้องการ named entity hints จริง โดยเฉพาะคำที่ query พูดแบบ implicit เช่น Hopper -> NVIDIA -> TSMC

### T004 Intel x86 rival -> AMD Instinct

No expansion:

- Graph เข้า AMD/Intel ได้ แต่ chunk gold `AMD_2026_Item_1_0003_ea53a6a5` ไม่ขึ้น top 10

Expansion hints:

- `AMD Instinct`
- `AMD INTC Ryzen Instinct AI accelerator x86 desktop`

ผล:

- Graph rank gold ขึ้นอันดับ 1
- Hybrid เจอ gold ใน top 5

แปลว่า product/entity hint แบบตรง ๆ ช่วย PPR มากใน query ที่มี implicit reasoning

## What Expansion Did Not Fix

### T001 AMD/TSMC supply risk

Expansion hints ดีแล้ว:

- `AMD TSMC supply risk Taiwan foundry`

แต่ยัง miss gold `AMD_2026_Item_1A_0008_e84e4130`

ผลที่คืนยังเป็น Item 1 supply partner chunks มากกว่า Item 1A risk chunk

สรุป: query expansion ไม่ใช่ปัญหาหลักของ T001 เพราะ seed/PPR เจอ entity ถูกแล้ว ปัญหาอยู่ที่ chunk mapping/rerank ไม่รู้ว่า query เป็น risk question และควร boost Item 1A

### T003 dense memory chips / AI accelerators

Expansion hints ดีขึ้น:

- `MU SK Hynix Samsung HBM NVDA AMD AI training memory`

แต่ยัง miss gold ทั้ง Graph และ Hybrid

สาเหตุที่น่าจะเป็น:

- มี entity hints แต่ graph/chunk mapping ยังไหลไป AMD/NVDA/INTC supply-chain chunks
- gold อยู่ MU Item 1A / NVDA Item 1 แต่ top chunks ยังถูก generic accelerator/supply-chain mentions ครอบ
- ต้องดูว่า `MU`, `HBM`, `high bandwidth memory` มี relation/mentions ใน graph เพียงพอไหม

### T011 Entegris useful-life / gross margin

Expansion ได้แค่ `Entegris` หรือ metric phrase เดิม แต่ยัง miss

สรุป: นี่ไม่ใช่ graph multi-hop problem แต่เป็น exact metric / fiscal-period / section-aware retrieval problem ต้องใช้ vector/financial-style rerank หรือ numeric tool มากกว่า PPR

### T012 Entegris segments

Expansion ไม่ช่วย Graph; Hybrid ยังมี gold ใน oracle@10 แต่ไม่ขึ้น top 5

สรุป: fusion/rerank ยังไม่ดีพอ เพราะ graph leg เอา Item 7/ปี 2024 noise มาดันออก

## Latency Finding

Expansion เพิ่ม latency ชัดเจน:

- Graph no-exp avg 3.97s -> Graph exp avg 9.97s
- Hybrid no-exp avg 2.29s -> Hybrid exp avg 6.46s
- Vector avg 0.93s

บาง query ช้ามาก เช่น:

- T001 graph ~35s
- T009 graph ~34s, hybrid ~22s
- T010 graph ~15s
- T015 graph ~14s

ถ้าจะใช้ expansion ใน production/agentic path ควรมี:

- cache per query
- timeout สั้นกว่า 120s
- deterministic expansion ก่อน LLM
- ใช้ LLM expansion เฉพาะ query ที่ต้องการ multi-hop/entity implicit reasoning

## Decision Before T2

Query expansion มีผลเชิงคุณภาพจริง แต่ยังไม่พอทำให้ GraphRAG/PPR เหนือ Vector

ควรทำ T2 ตามลำดับนี้:

1. ทำ deterministic domain expansion ก่อน LLM
   - `Hopper` -> `NVDA TSMC foundry`
   - `x86 rival of Intel` -> `AMD`
   - `dense memory chips` -> `HBM Micron DRAM SK Hynix Samsung`

2. ทำ section-aware chunk rerank
   - risk query -> boost Item 1A
   - product/business query -> boost Item 1
   - metric/accounting query -> boost Item 7 หรือส่ง financial/numeric path

3. ทำ confidence-aware hybrid
   - ถ้า graph confidence ต่ำ อย่าให้ graph rank แทรก vector มาก
   - ถ้า expansion มี named entity hints และ graph seed confidence สูง ค่อยเพิ่ม graph weight

4. เพิ่ม expansion cache
   - รอบนี้ Graph+Hybrid เรียก expansion ซ้ำต่อ query ทำให้ทั้งช้าและ nondeterministic

## Bottom Line

Expansion ช่วย seed stage อย่างมีนัยเชิงปฏิบัติ โดยเฉพาะ T002/T004

แต่ failure หลักที่เหลือคือ chunk mapping/reranking ไม่ใช่ seed อย่างเดียว โดยเฉพาะ T001/T003/T011/T012
