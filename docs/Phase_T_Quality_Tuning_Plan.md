---
tags: [phase-t, quality-tuning, graphrag, ppr, agentic-rag, evaluation]
date: 2026-06-28
status: draft-to-implement
project: SemiGraph
---

# Phase T - Quality Tuning Plan

Backlinks: [[00_INDEX]] · [[Project_Track_Evaluation_Plan]] · [[draft_eval]] · [[Graph_MultiHop_Benchmark_Report]] · [[Linker_Comparison_Report]] · [[Multi-hop Synthesized Evaluation — 3-config (Phase C2-quater)]] · [[Agentic_PhaseD_E2E_Probe_Report_2026-06-25]] · [[Code_Explained_Phase_D_Agent_State]] · [[PPR_explain]] · [[Phase_C1b+_HippoRAG_v2_Alignment]]

## 0. Goal

Phase T คือช่วง Quality Tuning ก่อนเข้า Eval จริง เป้าหมายไม่ใช่แค่ "ทำให้ตอบดูดีขึ้น" แต่ต้องทำให้ claim ของโปรเจกต์ defend ได้:

> Agentic Heterogeneous GraphRAG ที่มี PPR-based graph retrieval ต้องชนะ Vanilla Vector RAG อย่างมีนัยสำคัญ โดยเฉพาะคำถาม multi-hop / supply-chain / risk / cross-company relationship

หลักคิดแบบ First Principles:

1. Vector RAG ชนะเมื่อคำตอบอยู่ใน chunk เดียวและ query คล้ายกับ wording ใน chunk
2. Graph/PPR ควรชนะเมื่อคำตอบต้องเชื่อม entity หลายตัว เช่น supplier -> customer -> risk -> financial impact
3. ถ้า Graph/PPR ไม่ชนะ แปลว่าคอขวดอยู่ที่อย่างน้อยหนึ่งจุด: seed ผิด, graph ไม่มี edge, PPR ไหลผิด, chunk mapping หยิบผิด, agent เลือก tool ผิด, หรือ synthesis ไม่เห็น evidence ที่ถูก
4. ดังนั้น Phase T ต้องเริ่มจาก trace + metric ที่ชี้คอขวดได้ ไม่ใช่ปรับ parameter แบบเดา

## 1. Definition of Done

Phase T จบเมื่อครบเงื่อนไขนี้:

| Area | Exit Criteria |
|---|---|
| Retrieval | Graph/Hybrid ชนะ Vector บน multi-hop subset ทั้ง Hit@5 และ Recall@5 |
| Statistical claim | Wilcoxon หรือ paired bootstrap ได้ p < 0.05 อย่างน้อยบน Recall@5 หรือ answer correctness |
| Agent routing | tool selection accuracy >= 80% บนชุด query ที่ annotate tool intent แล้ว |
| Faithfulness | answer citation ต้อง map กลับ `citation_map` ได้ครบ และไม่มี invalid citation |
| Latency | graph-heavy query หลัง warm start ควรอยู่ในระดับรับได้ ไม่วน graph หลายรอบโดยไม่จำเป็น |
| Debuggability | ทุก query ใน eval มี persisted trace: subqueries, tool calls, retrieved chunk ids, citations, final answer |

## 2. Phase T Workflow

Pipeline การ tune ต้องเป็นรอบสั้น ๆ:

```text
Build benchmark slice
  -> Run baseline
  -> Diagnose bottleneck by stage
  -> Apply one fix
  -> Re-run same slice
  -> Keep only fixes that improve target metric without breaking regression
```

ห้าม tune หลายอย่างพร้อมกันในรอบเดียว เพราะถ้าคะแนนดีขึ้นจะไม่รู้ว่าอะไรเป็นสาเหตุจริง

## 3. T0 - Instrumentation and Baseline Freeze

### Objective

ทำให้ระบบวัดได้ก่อนว่าแพ้ตรงไหน เพราะถ้าไม่มี trace ละเอียด เราจะเห็นแค่ final answer ผิด แต่ไม่รู้ว่า seed ผิดหรือ synthesis ผิด

### Tasks

| Task | Code Target | Output |
|---|---|---|
| T0.1 Create benchmark file | `data/evaluate/phase_t_multihop_queries.yaml` | query, expected evidence, expected answer points, gold tool hint |
| T0.2 Add retrieval evaluator | `scripts/evaluate_retrieval_quality.py` | compare `vector`, `graph`, `hybrid` on same queries |
| T0.3 Add agent trace persistence | extend `scripts/run_agent_trace.py` or new `scripts/evaluate_agent_quality.py` | JSONL trace per query |
| T0.4 Freeze current scores | `analytics/phase_t_baseline_YYYYMMDD.md` | baseline table before tuning |

### Metrics

Retrieval metrics:

| Metric | Meaning |
|---|---|
| `Hit@5` | top-5 มี gold chunk อย่างน้อย 1 ไหม |
| `Recall@5` | จาก gold evidence chunks ทั้งหมด หาเจอกี่ส่วน |
| `MRR@5` | gold chunk แรกมาเร็วแค่ไหน |
| `Oracle@10` | ถ้า top-10 มี gold แต่ top-5 ไม่มี แปลว่า rerank/packing ผิด ไม่ใช่ retrieval ตาย |
| `SeedHit@k` | seed entity/triple มี entity สำคัญของคำถามไหม |
| `PPRHit@k` | หลัง PPR entity สำคัญยังอยู่ไหม |
| `ChunkMapHit@k` | entity ถูกแล้ว แต่ chunk mapping ได้ evidence ถูกไหม |

Agent metrics:

| Metric | Meaning |
|---|---|
| `tool_accuracy` | router เลือก tool ตรง gold intent ไหม |
| `round_count` | ใช้กี่รอบต่อ subquery |
| `irrelevant_retry_count` | retry tool เดิมทั้งที่ observe บอก irrelevant กี่ครั้ง |
| `citation_validity` | `[n]` ใน answer มีใน citation_map ครบไหม |
| `answer_faithfulness` | claim ใน answer support ด้วย cited evidence ไหม |
| `answer_completeness` | answer ครบ expected answer points ไหม |

### Exit Criteria

- มี benchmark slice อย่างน้อย 30 queries: 10 vector-friendly, 15 graph/multi-hop, 5 mixed heterogeneous
- evaluator รันซ้ำแล้วได้ผล deterministic
- trace มีข้อมูลพอไล่ได้ว่าแพ้ที่ stage ไหน

## 4. T1 - Bottleneck Analysis

### Diagnostic Model

ให้มองระบบเหมือนท่อ 7 ช่วง:

```text
User query
  -> planner
  -> router
  -> seed linker
  -> PPR
  -> chunk mapper / reranker
  -> observe / reflect / synthesize
```

ถ้าคำตอบผิด ให้ถามตามลำดับนี้:

| Stage | Question | Failure Signal | Likely Fix |
|---|---|---|---|
| Planner | แตก subquery ถูกไหม | subquery กว้าง/ผิด target | prompt + query type templates |
| Router | เลือก tool ถูกไหม | financial/news/vector ชนะทั้งที่ควร graph | router rules + tool examples |
| Seed linker | seed มี entity สำคัญไหม | `SeedHit=0` | hybrid seeds, entity hints, ticker filter |
| PPR | PPR เดินไป entity ที่เกี่ยวไหม | seed ถูกแต่ PPR top-k หลุด | damping, relation filter, hub penalty |
| Chunk mapping | entity ถูกแต่ chunk ผิดไหม | `PPRHit=1`, `ChunkMapHit=0` | chunk rerank, section/ticker filter, score aggregation |
| Reflect | หยุด/วนถูกไหม | retry ซ้ำ tool เดิมหลายรอบ | repeated-irrelevance stop rule |
| Synthesis | evidence มีแต่ answer ไม่ใช้ไหม | citation ขาด gold chunk | evidence packing / citation context |

### Required Report

ทุก tuning run ต้องมี bottleneck table:

```text
query_id | query | vector_hit | graph_hit | seed_hit | ppr_hit | chunk_hit | router_ok | final_status | bottleneck
```

## 5. T2 - Graph Retrieval Tuning

### T2.1 Seed Linker Tuning

Problem ที่คาดว่าเจอ:

- Query-to-Triple ดีสำหรับ multi-hop แต่บาง query entity-centric อาจหลุด
- `min_similarity=0.6` อาจปล่อย random/off-corpus seed ผ่าน
- expanded query อาจเพิ่ม noise ถ้า LLM ใส่ entity hint กว้างเกิน

Plan:

| Step | Change | Code Target | Metric |
|---|---|---|---|
| T2.1.1 Log top triples | `src/semigraph/online/seed.py` | ดูว่า triple ที่เลือกเกี่ยวไหม |
| T2.1.2 Compare seed modes | `query_to_seeds`, `query_to_triple_seeds`, `query_to_hybrid_seeds` | `SeedHit@k` |
| T2.1.3 Tune `min_similarity` | grid: 0.55, 0.60, 0.65, 0.70 | off-corpus false positive vs recall |
| T2.1.4 Add ticker/entity hint filter | query mentions AMD -> prefer chunks/entities connected to AMD | graph subset recall |
| T2.1.5 Add query type profiles | supply-chain/risk/product/customer/financial | per-type Recall@5 |

Implementation order:

1. เพิ่ม evaluator ที่ expose seed list ก่อน
2. รัน benchmark แล้ว mark query ที่ `SeedHit=0`
3. เฉพาะ query เหล่านั้นค่อยแก้ seed logic

### T2.2 PPR Parameter and Projection Tuning

Problem ที่คาดว่าเจอ:

- PPR อาจไหลเข้า hub เช่น `nvidia`, `intel`, `china`, `united states`
- Damping เดียวอาจไม่เหมาะทุก query type
- Projection สร้างใหม่ทุก call ทำให้ latency สูง

Plan:

| Step | Change | Code Target | Metric |
|---|---|---|---|
| T2.2.1 Grid damping | test 0.55, 0.65, 0.70, 0.75, 0.85 | Recall@5 by query type |
| T2.2.2 Tune `top_k_entities` | 10, 20, 40 | PPRHit vs ChunkMap noise |
| T2.2.3 Relation-type ablation | all informative vs risk/supply-chain subsets | Recall@5, hub leakage |
| T2.2.4 Projection cache | reuse GDS graph if unchanged | latency |
| T2.2.5 Replace deprecated GDS Cypher projection | migrate away from `id()` and `gds.graph.project.cypher` | future compatibility |

Important rule:

- อย่ากลับไปใช้ specificity-weighted teleport เป็น default ทันที เพราะ previous ablation ชี้ว่า uniform ดีกว่าบน corpus นี้
- ถ้าจะใช้ specificity ให้ใช้เป็น per-query optional profile ไม่ใช่ global default

### T2.3 Chunk Mapping and Reranking

Problem ที่คาดว่าเจอ:

- Current `_map_chunks` ใช้ `SUM(PPR mass)` ทำให้ chunk ที่ mention หลาย cluster ชนะ แม้ไม่ตอบคำถามตรง ๆ
- Single-entity query อาจโดน broad chunk แซง
- Chunk ที่ถูกต้องอาจอยู่ top-10 แต่หลุด top-5

Plan:

| Step | Change | Code Target | Metric |
|---|---|---|---|
| T2.3.1 Add debug fields | return `_matched_entities`, `_ppr_score`, `_n_clusters` in debug mode | explain ranking |
| T2.3.2 Add query-chunk cosine rerank | combine PPR score + chunk cosine | `Oracle@10 -> Hit@5` conversion |
| T2.3.3 Add ticker/section prior | prefer same ticker if query mentions ticker; Item_1A for risk | precision |
| T2.3.4 Penalize overly broad chunks | divide by log(1 + n_clusters) or cap contribution | reduce hub/broad chunk bias |
| T2.3.5 Compare aggregators | SUM vs MAX vs SUM+cosine | Recall@5 by type |

Expected winning design:

```text
candidate chunks from PPR top entities
  -> compute graph_score
  -> compute query_chunk_cosine
  -> apply ticker/section priors
  -> final_score = alpha * normalized_graph + beta * normalized_cosine + priors
```

For multi-hop subset, keep graph score important. For simple entity subset, let cosine/ticker prior prevent broad chunk drift.

## 6. T3 - Agentic Layer Tuning

### T3.1 Planner

Problem:

- Planner may split a query into subqueries that are too broad
- It may separate graph and financial parts poorly
- It may generate subquery wording that hurts retrieval

Plan:

| Step | Change | Code Target | Metric |
|---|---|---|---|
| T3.1.1 Add query type labels | planner emits `query_type` per subquery | router accuracy |
| T3.1.2 Limit decomposition | only split when explicit multi-hop or mixed-source | fewer unnecessary rounds |
| T3.1.3 Preserve key entities | planner must not drop ticker/entity names | SeedHit@k |
| T3.1.4 Add templates | supply-chain, risk, financial metric, latest news | retrieval recall |

### T3.2 Router

Problem:

- LLM router can be inconsistent
- Rule override currently handles financial intent, but not all graph/multi-hop intents
- News can return noise and should not be selected unless query has real news intent

Plan:

| Step | Change | Code Target | Metric |
|---|---|---|---|
| T3.2.1 Add deterministic query intent classifier | helper in `nodes.py` or separate router module | tool accuracy |
| T3.2.2 Add graph override patterns | supplier, customer, exposure, dependency, impact, risk, supply chain | graph recall |
| T3.2.3 Add hybrid as fallback tool | if graph/vector ambiguity, use hybrid | mixed query recall |
| T3.2.4 Add news strictness | require announcement/news/press/recent event wording | reduce news noise |
| T3.2.5 Store router decision reason | trace field | debugability |

Suggested tool policy:

| Query Intent | Preferred Tool |
|---|---|
| exact financial metric, annual, FY, revenue, margin, EPS | `financial` |
| supplier/customer/dependency/risk/impact/cross-company | `graph` or `hybrid` |
| broad description inside 10-K | `vector` |
| recent announcement/news/headline/event | `news` |
| mixed graph + text evidence | `hybrid` |

### T3.3 Observe and Reflect

Problem:

- Reflection loop prevents hallucination but can waste calls
- If a backend keeps returning irrelevant chunks, retrying same tool rarely helps

Plan:

| Step | Change | Code Target | Metric |
|---|---|---|---|
| T3.3.1 Add relevance score in observe JSON | `observe_node` prompt/output | irrelevant retry detection |
| T3.3.2 Stop repeated irrelevant tool | if same tool irrelevant 2x -> switch or synthesize insufficient | latency |
| T3.3.3 Tool-switch policy | vector -> graph/hybrid, news -> synthesize/refuse, graph -> hybrid | answer correctness |
| T3.3.4 Graph retry cap | graph max 1 retry unless evidence improves | latency |
| T3.3.5 Reflect with missing evidence type | feedback says missing entity/relation/metric/source | retry quality |

### T3.4 Synthesis

Problem:

- Even if retrieval found good evidence, synthesis can miss it if context packing is poor
- Multi-hop answer needs cite each hop, not just one final chunk

Plan:

| Step | Change | Code Target | Metric |
|---|---|---|---|
| T3.4.1 Evidence packing by subquery | keep top chunks per subquery/tool | completeness |
| T3.4.2 Prefer sufficient round chunks | chunks from round that reflect accepted | faithfulness |
| T3.4.3 Require answer-point coverage | prompt says answer each subquery contribution | completeness |
| T3.4.4 Citation audit | post-check every claim has citation | citation validity |
| T3.4.5 Insufficient evidence mode | explicit refusal/hedge when `max_rounds` | hallucination control |

## 7. T4 - News and Financial Tool Quality

News is not the core PPR claim, but weak news can pollute Agentic Heterogeneous RAG.

### News Tuning

| Problem | Fix | Metric |
|---|---|---|
| Recency beats relevance | lexical + embedding rerank headline/summary | news precision |
| Company appears only tangentially | require ticker/company centrality in headline/summary | irrelevant rate |
| Announcement query returns market commentary | intent filter for announce/launch/partnership/earnings/guidance | answer correctness |
| No good news found | return empty with clear reason, not noisy chunks | safe refusal |

### Financial Tuning

| Problem | Fix | Metric |
|---|---|---|
| API freshness unclear | include retrieval timestamp/source metadata | auditability |
| metric names vary | normalize aliases: revenue/sales, EPS/diluted EPS | metric hit |
| annual vs quarterly ambiguity | router/profile passes period intent | correctness |

## 8. T5 - Benchmark Design

### Query Set

Minimum useful set: 50 queries.

| Subset | Count | Purpose |
|---|---:|---|
| Vector-friendly single chunk | 10 | ensure graph tuning does not break simple QA |
| Graph multi-hop | 20 | primary PPR claim |
| Supply-chain/risk | 8 | semiconductor-specific graph advantage |
| Financial exact metric | 5 | heterogeneous tool sanity |
| News/recent event | 3 | news noise guard |
| Off-corpus / insufficient | 4 | hallucination/refusal test |

Each query should store:

```yaml
- id: T001
  query: "How exposed is AMD to TSMC supply risk?"
  type: graph_multihop
  gold_tools: ["graph", "hybrid"]
  gold_entities: ["amd", "tsmc"]
  gold_chunks:
    - AMD_2026_Item_1A_0008_e84e4130
  answer_points:
    - AMD relies on third-party foundries including TSMC
    - insufficient capacity or wafer supply can materially affect AMD
  notes: "Graph should beat vector because answer requires relationship + risk evidence"
```

### Configurations to Compare

| Config | Description | Why |
|---|---|---|
| `vanilla_vector` | direct vector retrieval + simple synthesis | baseline |
| `graph_only` | graph_search + synthesis | isolate PPR |
| `hybrid` | graph + vector RRF/rerank | expected strongest retriever |
| `agentic_vector` | agent with only vector/financial/news as allowed | isolate agent effect |
| `agentic_heterogeneous` | full current system | final project claim |

## 9. T6 - Implementation Order

Do this order to avoid wasting time:

1. **T0 Trace + evaluator first**
   - Without this, tuning is guessing.

2. **T1 Retrieval stage diagnosis**
   - Run vector/graph/hybrid on same query set.
   - Classify every graph loss as seed loss, PPR loss, chunk mapping loss, or rerank loss.

3. **T2 Chunk rerank before deep PPR changes**
   - If gold chunks are in top-10 but not top-5, rerank is cheaper and safer than changing PPR.

4. **T2 Seed tuning**
   - If seed hit is low, PPR cannot recover. Fix seed before damping.

5. **T2 PPR parameter tuning**
   - Tune damping/top_k_entities/relation projection after seed and chunk mapping are observable.

6. **T3 Agent router and reflection**
   - Once retrievers are better, tune agent to choose them correctly.

7. **T3 Synthesis and citation**
   - Tune final answer after retrieval context is reliable.

8. **T5 full ablation**
   - Run final stats only after local tuning stabilizes.

## 10. Concrete Next Coding Tasks

### Sprint T0.1 - Retrieval Evaluator

Create:

```text
data/evaluate/phase_t_multihop_queries.yaml
scripts/evaluate_retrieval_quality.py
analytics/Report Experiment/baseline_<version>_<timestamp>.md
```

Evaluator behavior:

- load query set
- run `vector_search`, `graph_search`, `hybrid_search`
- collect chunk ids
- compute Hit@k, Recall@k, MRR
- write markdown + JSONL details

### Sprint T0.2 - Trace Persistence

Extend or create:

```text
scripts/evaluate_agent_quality.py
analytics/phase_t_agent_traces.jsonl
analytics/phase_t_agent_baseline.md
```

Trace schema:

```json
{
  "query_id": "T001",
  "query": "...",
  "subqueries": ["..."],
  "tool_call_log": [{"tool": "graph", "query": "...", "n_chunks": 5}],
  "observation_history": [{"tool": "graph", "observation_text": "..."}],
  "reflection_history": [{"sufficient": true, "reason": "..."}],
  "citation_map": [{"citation_index": 1, "chunk_id": "..."}],
  "final_answer": "...",
  "latency_sec": 0.0
}
```

### Sprint T1 - Bottleneck Report

Create:

```text
scripts/analyze_phase_t_bottlenecks.py
analytics/phase_t_bottleneck_report.md
```

Output:

- top graph losses
- top vector losses
- cases where graph top-10 has gold but top-5 misses
- cases where seed hit fails
- cases where agent chooses wrong tool

### Sprint T2 - Retrieval Fixes

Implement in this order:

1. Add debug mode to `graph_search`
2. Add graph chunk rerank with query-chunk cosine
3. Add ticker/section priors
4. Add seed mode comparison and optional hybrid seeds
5. Add PPR config profiles by query type

### Sprint T3 - Agent Fixes

Implement in this order:

1. Add query intent helper
2. Add graph/hybrid deterministic router overrides
3. Add observe relevance score
4. Add repeated-irrelevance stop/switch rule
5. Add final synthesis coverage/citation audit

## 11. Risk Register

| Risk | Why It Matters | Mitigation |
|---|---|---|
| Tuning overfits small query set | final eval may not improve | keep holdout set untouched |
| PPR beats vector only on hand-picked graph queries | claim weak | include mixed and vector-friendly subsets |
| LLM judge variance | answer metric unstable | run judge 3 times or use deterministic rubric first |
| Graph noise from extraction | PPR walks through bad edges | relation filtering + entity alias audit |
| Latency too high | demo/eval impractical | projection cache + graph retry cap |
| News noise hurts full agent | heterogeneous config looks worse | strict news relevance and safe empty result |

## 12. Phase T Tracking Checklist

- [ ] T0 benchmark YAML created
- [ ] T0 retrieval evaluator created
- [ ] T0 agent trace persistence created
- [ ] T0 baseline report written
- [ ] T1 bottleneck report generated
- [ ] T2 seed linker tuning done
- [ ] T2 chunk rerank implemented
- [ ] T2 PPR profile tuning done
- [ ] T3 router overrides done
- [ ] T3 observe/reflect stop rule done
- [ ] T3 synthesis citation audit done
- [ ] T4 news rerank/filter done
- [ ] T5 final 3-config ablation rerun
- [ ] Advisor-ready result table produced

## 13. Advisor-Facing Claim Template

ถ้าผลออกมาดี ให้สรุปแบบนี้:

> We first diagnosed retrieval failures stage-by-stage: seed selection, PPR propagation, chunk mapping, and agent routing. After tuning graph reranking and agent tool selection, Agentic Heterogeneous GraphRAG improved multi-hop Recall@5 over Vanilla Vector RAG, while preserving citation faithfulness through provenance-grounded answer synthesis.

ถ้าผลออกมาไม่ชนะทุก subset ให้พูดให้ถูก:

> Vector RAG remains competitive on single-chunk lexical questions, but Graph/PPR improves evidence discovery on relationship-heavy semiconductor questions. The system contribution is therefore strongest on heterogeneous multi-hop analysis, not generic QA.
