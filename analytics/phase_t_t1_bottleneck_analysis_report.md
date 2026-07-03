# Phase T T1 Bottleneck Analysis

Generated: 2026-06-29

## Scope

ใช้ชุดคำถามใน `data/evaluate/phase_t_multihop_queries.yaml` รุ่น v0.1 เป็น diagnostic benchmark ก่อน ยังไม่ใช้ FinReflectKG MultiHopQA 555 ชุดในรอบนี้

รัน retrieval-only baseline:

```bash
HF_HUB_OFFLINE=1 conda run -n senior_project python scripts/evaluate_retrieval_quality.py --tools vector --top-k 5 --oracle-k 10
HF_HUB_OFFLINE=1 conda run -n senior_project python scripts/evaluate_retrieval_quality.py --tools graph hybrid --top-k 5 --oracle-k 10 --no-llm-expansion
```

รายงานที่เกี่ยวข้อง:

- `analytics/phase_t_t1_vector_baseline_16q.md`
- `analytics/phase_t_t1_vector_baseline_16q_details.jsonl`
- `analytics/phase_t_t1_graph_hybrid_no_expansion_baseline_16q.md`
- `analytics/phase_t_t1_graph_hybrid_no_expansion_baseline_16q_details.jsonl`

หมายเหตุ: รันรวม `vector graph hybrid` แบบเปิด LLM expansion ติดค้างนาน จึงเพิ่ม diagnostic flag `--no-llm-expansion` เพื่อแยกปัญหา Graph/PPR ออกจาก LLM query expansion latency

## Aggregate Result

มี scored queries 7 ข้อจากทั้งหมด 16 ข้อ เพราะ query ที่ยังไม่มี `gold_chunks` ถูกใช้เป็น discovery-only

| Tool | Hit@5 | Recall@5 | MRR@5 | Oracle Hit@10 | Error |
|---|---:|---:|---:|---:|---:|
| Vector | 0.429 | 0.314 | 0.357 | 0.571 | 0 |
| Graph, no LLM expansion | 0.143 | 0.143 | 0.048 | 0.429 | 0 |
| Hybrid, no LLM expansion | 0.286 | 0.171 | 0.286 | 0.429 | 0 |

สรุปหลัก: ตอนนี้ Graph/PPR ยังไม่ได้ชนะ Vector บนชุด diagnostic นี้ และ Hybrid ยังไม่ช่วยพอ เพราะ Graph leg มี noise สูง

## Per-Query Diagnosis

| ID | Type | Vector | Graph | Hybrid | Diagnosis |
|---|---|---:|---:|---:|---|
| T001 | graph_multihop | miss@5, hit@10 | miss | miss | Graph ได้ entity ถูก เช่น AMD/TSMC แต่ chunk mapping ดันไป Item 1 supply partner narrative แทน Item 1A risk gold |
| T002 | supplier_via_product | hit | miss@5, hit@10 | hit | Graph มี gold ใน top 10 แต่ rank ต่ำกว่า top 5; Hybrid ช่วยเพราะ vector เจอ gold |
| T003 | supplier_via_product | miss | miss@5, hit@10 | miss | Seed ผิดทิศไป AMD/Intel/AI accelerator มากกว่า Micron/HBM; PPR ไม่ดัน MU/NVDA gold ขึ้น top 5 |
| T004 | competitor_product | miss | miss | miss | Seed/PPR เข้า AMD/Intel ได้ แต่ chunk ที่ต้องการ `AMD_2026_Item_1_0003` ไม่ขึ้น top 10; gold อาจ strict เกินหรือ chunk mapping ยังไม่ focus product line |
| T010 | vector_friendly | hit | hit | hit | ทั้งสาม tool ใช้ได้กับ query ที่ entity/prose ตรง |
| T011 | vector_friendly | miss | miss | miss | Query มี exact metric/useful-life/gross margin แต่ retriever ไปหา Item 7 ปีอื่น/บริษัทอื่น; ต้องมี fiscal-year/metric-aware rerank |
| T012 | vector_friendly | hit | miss | miss@5, hit@10 | Hybrid มี gold ใน top 10 แต่ RRF ดันไม่ขึ้น top 5 เพราะ graph noise แทรก |

## Bottlenecks

### 1. Graph Seed Is Too Permissive

ตัวอย่าง T016 off-corpus:

query `qwerty zzz random semiconductor nonsense` ยังได้ seed 10 ตัว เช่น `amd`, `micron`, `zynq`, `qlc nand`

แปลว่า threshold `min_similarity=0.6` ต่ำเกินสำหรับ triple seed search หรืออย่างน้อยต้องมี off-corpus guard เช่น max similarity / entropy / ticker intent check ก่อน PPR

ผลกระทบ:

- off-corpus query ยังได้คำตอบเหมือนมี evidence
- Agentic layer เสี่ยง hallucinate เพราะ retriever คืน chunks เสมอ
- PPR ไม่มี notion ของ "ไม่รู้" ตอน seed ยังไม่มั่นใจ

### 2. Graph Chunk Mapping Over-Rewards Generic Entity Mentions

ตัวอย่าง T001:

Seed/PPR ดีมาก มี `amd`, `advanced micro devices`, `tsmc`, `supply chain disruption risk`

แต่ top chunks เป็น:

- `NVDA_2025_Item_1_0008_a4407f7e`
- `AMD_2025_Item_1_0009_c842eea0`
- `AMD_2026_Item_1_0010_460dfa17`
- `INTC_2026_Item_1_0008_c74f560f`

gold คือ `AMD_2026_Item_1A_0008_e84e4130`

แปลว่า mapping ตอนนี้ใช้ SUM(PPR score) จาก entity mentions อย่างเดียว จึงชอบ chunk ที่ mention supply partner/entity เยอะใน Item 1 มากกว่า risk chunk ใน Item 1A ที่ตอบคำถามจริงกว่า

ผลกระทบ:

- PPR เจอ neighborhood ถูก แต่ final chunk ผิด
- multi-hop relationship signal ยังไม่พอ ต้องมี query-chunk relevance หรือ section-aware rerank

### 3. PPR Walk Leaks Toward Hubs And Neighboring Companies

ตัวอย่าง T003:

คำถามถาม memory chips for AI accelerators แต่ seed top คือ `advanced micro devices`, `ai accelerators`, `intel`, `ryzen ai`, ไม่ใช่ `micron` หรือ `hbm`

ผลคือ PPR top เป็น AMD/Intel/Broadcom และ chunk top เป็น AMD/NVDA/INTC supply partner chunks

แปลว่า query-to-triple seed ยังจับ "AI accelerator" ได้มากกว่า "memory supplier/HBM" และ PPR ขยายจาก seed นั้นต่อ จึงไม่กลับไปหา Micron evidence

### 4. Hybrid Fusion Currently Adds Noise Instead Of Correcting It

Hybrid ดีขึ้นจาก Graph บางข้อ เช่น T002 เพราะ vector เจอ gold แต่ overall ยังต่ำกว่า Vector:

- Vector Hit@5 = 0.429
- Hybrid Hit@5 = 0.286

เหตุผลคือ RRF ให้ graph top ranks มีสิทธิ์แทรก vector results แม้ graph leg noisy เช่น T012 gold อยู่ hybrid oracle@10 แต่ไม่ขึ้น top 5

### 5. Query Set Still Has Sparse Gold

มี scored query แค่ 7/16 ข้อ จึงใช้สรุปเชิง tuning ได้ แต่ยังไม่ควร claim final performance

หลายข้อ discovery-only มี output น่าสนใจ เช่น:

- T007 vector คืน AMD Radeon-like chunks ดี
- T009 vector/hybrid คืน NVIDIA export-control risk chunks ดี
- T015 graph คืน KLA/MU risk-related chunks แต่ยังไม่มี gold

ควร pin gold เพิ่มก่อนใช้เป็น benchmark หลัก

## Immediate Tuning Plan

### T2.1 Add Seed Diagnostics And Off-Corpus Guard

เพิ่มข้อมูลใน evaluator/details:

- top seed names
- top seed similarity
- number of seeds above threshold
- max similarity
- PPR top entities

เพิ่ม rule:

- ถ้า max triple similarity ต่ำกว่า threshold ที่สูงขึ้น เช่น 0.72 หรือ seed entropy กระจายเกิน ให้ return low-confidence/no evidence
- ทดสอบ threshold 0.60, 0.65, 0.70, 0.75

### T2.2 Add Section-Aware Chunk Rerank

หลัง `_map_chunks` ให้ rerank ด้วย feature:

- query-token overlap / BGE query-chunk similarity
- section boost: risk query -> Item 1A, business/product query -> Item 1, metric/financial query -> Item 7
- ticker/year intent boost ถ้า query มี ticker/company/year

เป้าหมายแรก: ดัน T001 gold Item 1A ให้ขึ้น top 5 โดยไม่ทำให้ T010/T012 แย่

### T2.3 Improve Query-to-Triple Seed For Supplier/Memory Questions

สำหรับ query ที่มีคำเช่น `memory`, `HBM`, `high-bandwidth memory`, `supplier`, `produces` ควร expand/query rewrite ไปทาง `Micron`, `HBM`, `DRAM`, `NVIDIA data center`

ทำเป็น deterministic domain synonym expansion ก่อน LLM:

- `dense memory chips` -> `HBM high-bandwidth memory DRAM Micron`
- `foundry partner` -> `TSMC Samsung foundry wafer manufacturing`
- `x86 rival of Intel` -> `AMD Advanced Micro Devices`

### T2.4 Make Hybrid Confidence-Aware

อย่าให้ Graph leg แทรก Vector เสมอ ถ้า graph confidence ต่ำ

แนวทาง:

- graph confidence = max seed similarity + top PPR concentration + overlap with vector top chunks
- ถ้า graph confidence ต่ำ ให้ใช้ vector-biased RRF หรือไม่ใช้ graph leg
- ถ้า query type เป็น graph_multi_hop และ graph confidence สูง ค่อยเพิ่ม graph weight

### T2.5 Pin More Gold Chunks

เพิ่ม gold ให้ discovery queries อย่างน้อย:

- T005 Taiwan/TSMC political risk
- T006 NVIDIA wafer supplier
- T007 AMD Radeon vs NVIDIA RTX
- T008 HBM supplier for NVIDIA H200
- T009 NVIDIA export controls
- T015 KLA/yield/AMD margin chain

## Decision

Phase T v1 ควรเริ่มแก้ที่ retrieval engine ก่อน Agentic:

1. seed threshold/off-corpus guard
2. deterministic query expansion for semiconductor synonyms
3. section-aware + query-sim chunk rerank
4. confidence-aware hybrid

เหตุผล: จาก trace ตอนนี้ Agentic ยังไม่ได้เข้ามาเกี่ยว ปัญหาเกิดก่อนถึง answer synthesis แล้ว คือ retrieval layer ส่ง evidence ที่ยังไม่ดีพอ
