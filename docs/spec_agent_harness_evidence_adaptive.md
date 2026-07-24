---
title: Evidence-Adaptive Full Agent Harness Redesign
status: ready-for-agent
issue_tracker_publish_status: blocked-github-app-403
created: 2026-07-22
---

## Problem Statement

ในมุมของผู้พัฒนา SemiGraph นั้น Full Agent ปัจจุบันทำงานได้ แต่ยังมีลักษณะเป็น workflow ที่มี LLM call และ state ซ้ำซ้อนมากกว่าจะเป็น harness ที่ปรับตัวตามหลักฐานอย่างมีวินัย Planner สร้าง subquery แล้ว Router ใช้ LLM อีกครั้งเพื่อจำแนก Tool ทั้งที่ Planner มี capability contract ของ Tool อยู่แล้ว จากนั้น Observe และ Reflect ใช้ LLM แยกสองครั้งเพื่อสรุปและตัดสินหลักฐานชุดเดียวกัน

State ของ Agent กระจาย retrieval รอบเดียวกันไปยังหลาย parallel histories เช่น chunks, tool calls, retrieval traces, observations และ reflections ทำให้ trace จับคู่ยากและเพิ่มความเสี่ยงที่ข้อมูลเหลื่อมกัน Retry policy ยังยอมให้เรียก Tool/query เดิมหรือได้หลักฐานเดิมซ้ำ และการครบจำนวนรอบถูกปะปนกับความหมายว่า evidence เพียงพอ

Smoke benchmark ปัจจุบันมีเพียง 2 queries จึงยังไม่ใช่ข้อสรุปเชิงสถิติ แต่แสดงปัญหาเชิงวิศวกรรมชัดเจน: Full Agent มี latency เฉลี่ยประมาณ 187.56 วินาทีและ 4.5 tool calls ต่อ query; หนึ่ง query ใช้ 6 retrieval attempts โดย Financial Tool คืน 0 chunks หลายรอบ และอีก query เรียก Vector 3 รอบก่อนหยุดเพราะครบงบ

Frozen baseline 20 queries ยืนยัน routing defect เพิ่มเติม: Financial Tool ถูกเรียก 69 จาก 103 calls และ 65 calls คืน 0 chunks ขณะที่ Graph Tool ถูกเรียกเพียง 2 calls สาเหตุหนึ่งคือ Keyword-Based Financial Override ใช้คำกว้าง เช่น revenue หรือ margin เป็นเหตุผลแทนที่ Tool ที่ LLM เลือก ทั้งที่คำถามอาจต้องการ filing prose หรือ graph relationship

ปัญหาของ locked-tool modes ไม่อยู่ในขอบเขตนี้ Agent Vector และ Agent Graph ถูกบังคับ Tool โดยตั้งใจเพื่อทำ ablation ส่วน redesign นี้พิจารณาเฉพาะ Full Agent ซึ่งอนุญาตให้เปลี่ยน Tool ได้

## Solution

ปรับ Full Agent เป็น evidence-adaptive harness แบบ KISS ที่มี 4 nodes หลัก:

```text
START → PlanRoute → Execute → Assess
                       ▲         │
                       └─────────┤ retry หรือ task ถัดไป
                                 └→ Synthesize → END
```

PlanRoute จะรวมการวางแผนและ initial routing ไว้ใน LLM call เดียว โดยคืน Task ที่มี query, Evidence Requirements และ initial action การค้นรอบแรกต้องรักษารูปทรงของคำถามตาม Tool: connected multi-hop chain อยู่ใน Graph Task เดียวและแทนแต่ละ hop/claim เป็น Requirements ส่วน Tool อื่นแบ่ง Task ตาม capability ของตน จากนั้น Plan Validator แบบ conservative จะตรวจเฉพาะ non-null/non-empty, type, enum, Tool/action shape, จำนวน Task/Requirement, unique IDs และ positive top-k ประเด็น semantic เช่น entity/relation completeness เป็น warning เท่านั้นเพื่อลดความเสี่ยงที่ validator ทำ Recall ตก

LLM เป็นเจ้าของ Tool selection ใน normal path ตาม ADR 0001: deterministic validator ตรวจและปฏิเสธ action ที่ผิดได้ แต่ไม่แทนที่ Tool จาก keyword rule และไม่มี Financial force เหลืออยู่ Financial Tool ยังคงอยู่ใน registry และถูกเลือกได้เมื่อ LLM เห็นว่า capability ตรงกับ Evidence Requirement

Execute จะบันทึก retrieval รอบหนึ่งเป็น Attempt record เดียวแทนการกระจายข้อมูลไปหลาย histories และแยก Technical Retry สำหรับ network/API/Neo4j failure ออกจาก Evidence Retry โดย Technical Retry ไม่ใช้งบ Agent Attempt ส่วน Assess จะรวม Observe, Reflect, Evidence Selection, structured Retry Feedback, Hint และ next action ใน LLM call เดียว Assess จะตัดสิน requirement coverage, เลือก supporting chunks และระบุสิ่งที่ขาด แต่ deterministic controller จะอนุมัติ Retry ตาม budget, previous actions, Tool Retry Profile, capability และ Evidence Gain

Agent จะทำ Tasks แบบ sequential ก่อนเพื่อรักษาความเรียบง่ายและ traceability โดยเก็บ memory สามมุม: Attempt Ledger/Raw Evidence Pool สำหรับ audit/debug, Accepted Evidence สำหรับ synthesis และ compact Working Context สำหรับ Assess Raw evidence และ accepted evidence เพิ่มแบบ append/union โดยไม่ overwrite รอบก่อน ระบบจะไม่มี LLM reranker call แยก; Assess ทำ semantic mapping ระหว่าง chunks กับ Requirements แล้ว deterministic selector เลือก coverage-first ภายใน synthesis budget โดยไม่ให้สิทธิ์ Attempt แรกหรือ Attempt ล่าสุดเป็นพิเศษ

ก่อน redesign ต้อง freeze Full Agent baseline บน fixed stratified pilot 20 queries และเก็บ result/config/commit hash จากนั้นจึงแก้ in-place เพื่อให้ปลายทางเหลือ harness ชุดเดียว เมื่อ pilot ผ่าน acceptance gates จึงรัน 74-query final benchmark เพื่อใช้เป็นผลสรุป

## User Stories

1. As a SemiGraph user, I want the Full Agent to avoid repeated retrieval that yields no new evidence, so that answers arrive faster.
2. As a SemiGraph user, I want the Agent to distinguish sufficient evidence from a forced stop, so that uncertainty is communicated honestly.
3. As a SemiGraph user, I want final answers to remain grounded in accepted raw chunks, so that citations remain auditable.
4. As a thesis evaluator, I want Full Agent retrieval Recall and synthesis GroupRecall to remain no lower than the frozen baseline, so that speed improvements do not trade away evidence quality.
5. As a thesis evaluator, I want latency and LLM-call counts reported per query, so that performance gains are measurable.
6. As a thesis evaluator, I want paired before/after results for the same query IDs, so that aggregate metrics do not hide regressions.
7. As a thesis evaluator, I want a fixed stratified 20-query development pilot, so that iteration is affordable and reproducible.
8. As a thesis evaluator, I want the final result confirmed on all 74 strict queries, so that the thesis conclusion does not rely on the pilot sample.
9. As an Agent maintainer, I want planning and initial routing combined, so that the same classification is not paid for twice.
10. As an Agent maintainer, I want every planned Task to contain explicit Evidence Requirements, so that sufficiency has a stable checklist.
11. As an Agent maintainer, I want the Original Query to remain the highest-level contract, so that Planner omissions cannot redefine the user's intent.
12. As an Agent maintainer, I want deterministic Plan validation limited to structural facts, so that malformed plans are caught without semantic false rejections that may lower Recall.
13. As an Agent maintainer, I want invalid plans repaired at most once, so that malformed output can recover without creating an unbounded loop.
14. As an Agent maintainer, I want a deterministic fallback after failed Plan repair, so that the Agent still terminates safely.
15. As an Agent maintainer, I want Pydantic validation at LLM-output boundaries, so that missing, malformed and unexpected fields fail clearly.
16. As an Agent maintainer, I want context validation for known IDs and Tool capabilities plus warnings for ambiguous semantics, so that invalid references are rejected without treating uncertain anchors as hard failures.
17. As an Agent maintainer, I want AgentState to remain a TypedDict, so that LangGraph integration stays simple.
18. As an Agent maintainer, I want one Attempt Ledger record per retrieval attempt, so that action, chunks, trace and assessment cannot drift across parallel histories.
19. As an Agent maintainer, I want raw retrieval output retained in the Attempt Ledger, so that Recall@All and debugging remain possible even when chunks are not selected for synthesis.
20. As an Agent maintainer, I want accepted evidence stored separately from raw attempts, so that synthesis context is relevant and bounded.
21. As an Agent maintainer, I want Assess prompts to receive compact Working Context rather than the entire history, so that prompt size does not grow without bound.
22. As an Agent maintainer, I want Observe and Reflect merged into one Assess call, so that each retrieval result is summarized and judged once.
23. As an Agent maintainer, I want Assess to map supporting chunk IDs to Requirement coverage, so that progress is traceable.
24. As an Agent maintainer, I want Requirement status represented as missing, partial or covered, so that progress is more precise than a single sufficient boolean.
25. As an Agent maintainer, I want accepted chunk IDs validated against actual retrieved chunks, so that the LLM cannot invent evidence references.
26. As an Agent maintainer, I want Assess to propose a next Tool and query directly, so that Retry does not require another Router LLM call.
27. As an Agent maintainer, I want deterministic Retry guards to reject exact repeated actions, so that the Agent cannot loop on the same Tool/query.
28. As an Agent maintainer, I want duplicate chunk sets and zero-result repeats detected, so that new attempts require a meaningful change.
29. As an Agent maintainer, I want a hard cap of three attempts per Task, so that runtime remains bounded.
30. As an Agent maintainer, I want the third attempt reserved for useful progress or one compatible fallback after the prior Tool is exhausted, so that the final budget is productive without blocking recovery from a failed same-Tool retry.
31. As an Agent maintainer, I want a Task to end as completed, partial or failed, so that termination and sufficiency are not conflated.
32. As an Agent maintainer, I want explicit stop reasons such as sufficient, no_evidence_gain, budget_exhausted, unsupported and assessment_error, so that traces explain control decisions.
33. As an Agent maintainer, I want malformed Assess output repaired at most once, so that occasional JSON failure does not discard a useful retrieval.
34. As an Agent maintainer, I want failed Assess repair to preserve latest chunks in a fail-open evidence path and stop safely, so that the Agent neither loses evidence nor retries blindly.
35. As an Agent maintainer, I want Evidence Selection inside Assess rather than a separate LLM reranker, so that filtering does not add another normal-path call.
36. As an Agent maintainer, I want deterministic deduplication before synthesis, so that repeated retrieval does not consume prompt budget.
37. As an Agent maintainer, I want evidence allocation across subqueries before global filling, so that one noisy Task cannot crowd out another.
38. As an Agent maintainer, I want raw chunks rather than LLM summaries sent to Synthesis, so that final claims remain grounded.
39. As an Agent maintainer, I want trace data for Plan validation, repairs, attempts, assessments, guards and synthesis selection, so that failures can be diagnosed from one run.
40. As an Agent maintainer, I want stage latency and LLM-call counts separated, so that bottlenecks such as Graph triple filtering are not misattributed to the harness.
41. As an Agent maintainer, I want Retriever configuration and algorithms unchanged during this redesign, so that benchmark differences isolate the Agentic layer.
42. As an Agent maintainer, I want independent Tasks executed sequentially in the first version, so that correctness and state transitions remain easy to verify.
43. As a future maintainer, I want parallel execution explicitly deferred, so that it can be introduced later only when supported by benchmark evidence.
44. As a future maintainer, I want the baseline implementation frozen before in-place redesign, so that the repository does not carry two diverging Agent implementations.
45. As a project owner, I want the final harness to be readable and maintainable using small pure validators and controller functions, so that minor bugs can be quick-edited without understanding the entire graph.
46. As an Agent maintainer, I want normal-path Tool selection to remain LLM-owned without keyword-based Financial overrides, so that financial vocabulary does not force unsupported structured retrieval.
47. As an Agent maintainer, I want a connected multi-hop chain preserved as one initial Graph Task, so that decomposition does not remove joint Graph retrieval signals.
48. As an Agent maintainer, I want semantic plan checks to remain warnings in the first version, so that conservative validation does not lower Recall.
49. As an Agent maintainer, I want technical transport retries separated from evidence retries, so that temporary infrastructure failures do not consume the reasoning budget.
50. As an Agent maintainer, I want Retry Feedback to identify the failure, missing Requirements, preserved anchors, diagnostics and strategy, so that retries respond to evidence rather than paraphrase blindly.
51. As an Agent maintainer, I want Tool-specific retry capabilities represented as data used by one controller, so that Tools adapt appropriately without separate workflows.
52. As an Agent maintainer, I want Graph retries to use evidence-aware hints rather than generic HyDE in the first version, so that retry queries remain aligned with entity-relation triple retrieval.
53. As an Agent maintainer, I want accepted evidence selected by Requirement coverage regardless of attempt order, so that a productive retry can replace an irrelevant first result.

## Implementation Decisions

- The redesign applies only to Full Agent. Locked Vector-only and Graph-only evaluator modes remain deliberate ablation controls and are not interpreted as routing defects.
- The architectural shape is a four-node graph: PlanRoute, Execute, Assess and Synthesize. Deterministic validation and guard logic remain pure helper functions rather than additional graph nodes.
- PlanRoute combines decomposition and initial Tool selection in one LLM call. It produces one to three sequential Tasks.
- PlanRoute LLM owns initial Tool selection, and Assess LLM owns retry Tool proposals, using the registered Tool capability contracts.
- Keyword-Based Financial Override is removed from Full Agent. Financial vocabulary, fiscal periods or metric names must not deterministically replace the Tool selected by the LLM.
- Deterministic validators and retry guards may reject malformed, unavailable, repeated or unsupported actions, but they do not substitute another Tool in the normal path.
- Financial Tool remains registered and available; this decision removes only the forced override, not the Tool itself.
- Each Task contains a stable task ID, a self-contained query, one or more Evidence Requirements, and an initial retrieval action.
- A connected multi-hop relationship chain remains one Graph Task for the initial retrieval. Its hops or claims are represented as Evidence Requirements rather than independent Graph subqueries.
- Vector, Financial and News Tasks retain their tool-native unit of work; decomposition occurs for independent evidence needs or different Tool capabilities, not mechanically per clause.
- Evidence Requirements are execution checklists, while the immutable Original Query remains the highest-level intent contract.
- Tasks execute sequentially in the first version. Parallel fan-out, branch merging and concurrent Tool execution are deferred.
- Plan output is validated with Pydantic for structure and with deterministic domain checks for context.
- Initial deterministic validation covers only non-null/non-empty values, expected types, allowed enum/Tool names, action shape, positive top-k, Task/Requirement cardinality and unique IDs.
- Company/ticker aliases, fiscal periods, metrics, product entities, relationship semantics, chain completeness and subjective Requirement quality initially produce warnings rather than hard failures because deterministic extraction would have false-positive risk and may lower Recall.
- A valid plan incurs no additional validation LLM call. An invalid plan may be repaired once with validation errors; a second failure uses a deterministic error fallback that does not invoke Keyword-Based Financial Override and records its fallback source explicitly.
- Pydantic is limited to PlanRoute and Assessment output boundaries. AgentState remains a TypedDict and stores validated data as ordinary serializable values.
- Unknown output fields are forbidden. Cross-field validation requires Retry decisions to include a next action, Accept decisions to have no missing requirements, and Stop decisions to include a stop reason.
- Context-dependent validation confirms that referenced Requirement IDs belong to the current Task, accepted chunk IDs belong to retrieved chunks, and proposed Tool/action fields are supported.
- Attempt Ledger replaces parallel retrieval, observation and reflection histories as the canonical audit structure.
- The following decision-rich state shape was agreed during the design session:

```text
AgentState
├── original_query
├── tasks + current_task_index
├── current_action
├── attempts[]
│   ├── task/attempt identity
│   ├── action
│   ├── chunks
│   ├── retrieval_trace
│   └── assessment
├── evidence_pool
├── completed_tasks
├── final_answer
└── citation_map
```

- Each Attempt is a cohesive record of the retrieval action, raw chunks, retrieval trace and validated assessment.
- Memory has three views: Attempt Ledger for full audit/debug state, Evidence Pool for accepted raw chunks, and compact Working Context for the current Assess prompt.
- Assess receives the Original Query, current Task and Requirements, current action, latest retrieval batch, current Requirement coverage, compact accepted-evidence previews and summaries of prior actions/chunk IDs. It does not receive all historical raw chunks.
- Assess also receives compact Tool diagnostics needed to explain failure, including abort reason, selected seed/triple summaries, returned chunk IDs and duplicate/zero-result signals when available.
- Assess merges Observe, Reflect, Evidence Selection, Retry Feedback, Hint generation and next-action proposal into one normal-path LLM call.
- Assess output includes a concise reason, Requirement coverage, accepted/supporting chunk IDs, decision, missing evidence, structured Retry Feedback and an optional next action.
- Retry Feedback contains target Requirement IDs, failure type, preserved anchors, compact retrieval diagnostics and retry strategy.
- Requirement coverage is represented as a map from Requirement ID to status (missing, partial or covered) and supporting chunk IDs.
- Evidence Gain is represented through changes in this coverage map. Gain occurs when status improves or a Requirement gains a new accepted supporting chunk.
- Merely returning new but irrelevant chunk IDs, repeating existing chunks, changing prose or returning zero chunks does not constitute Evidence Gain.
- Technical Retry handles transient network/API/Neo4j/transport failures before an evidence result exists and does not consume Agent Attempt budget. Evidence Retry begins only after a valid zero, irrelevant, partial or duplicate result can be assessed.
- Retry is a Hybrid Control Policy: Assess proposes a next action and deterministic code validates shape, novelty, budget, capability, Tool Retry Profile and Evidence Gain before execution.
- One generic controller uses declarative Tool Retry Profiles rather than separate Tool-specific workflows. A profile states which strategies are meaningful for each Tool and failure type.
- Graph supports evidence-aware anchor enrichment, focus-missing and bridge hints; Vector supports focus-missing query reformulation; Financial may repair only ticker/metric/period constraints present in the intent; News query retry is meaningful only for missing ticker or news-intent guards with its current Retriever contract.
- Generic HyDE is deferred. In the first version Graph hints must remain query reformulations aligned with entity-relation triple retrieval and may use only the Original Query, accepted evidence or compact Retriever diagnostics as context.
- Exact normalized Tool/query repeats are forbidden. Repeating a Tool after zero results requires a materially changed action; duplicate result sets cannot trigger the same retrieval strategy again.
- Same-tool-first applies when Tool fit is correct or uncertain and its profile supports a meaningful strategy. A Tool mismatch may switch immediately; after one same-tool adaptation produces no gain, a compatible fallback Tool may be proposed.
- Every Task has at most three Attempts. Attempt one is always allowed; Attempt two requires a valid new action; Attempt three requires either Evidence Gain from Attempt two or a compatible fallback after the prior Tool has been adapted without gain.
- When no novel same-tool strategy or compatible fallback exists, the Task stops rather than looping.
- Completing the attempt budget never sets evidence sufficiency to true. Termination state and evidence coverage remain separate.
- Task outcomes are completed, partial or failed, with explicit stop reasons.
- Invalid Assessment output may be repaired once. If repair also fails, latest unique chunks are retained through the agreed fail-open path and the Task stops with assessment_error instead of blindly retrieving again.
- Evidence Selection is not a separate global reranker. It is performed conservatively inside Assess, and deterministic fallback preserves Retriever order when selection output cannot be trusted.
- Retrieval top-k remains the number returned per Tool call and is distinct from the accumulated raw pool and synthesis budget.
- Raw unique chunks from all Attempts remain append-only for tracing and Recall@All. Accepted Evidence is a deduplicated union and Requirement coverage may progress missing → partial → covered without a later Attempt silently deleting prior support.
- Assess maps chunks to supported Requirement IDs. A deterministic coverage-first selector chooses the smallest useful set that maximizes Requirement coverage within an initial overall budget around nine chunks.
- Attempt order is not a quality signal: a later retry may replace all first-attempt chunks in Synthesis Context when it provides better coverage. Retriever rank is used only as a tie-breaker or deterministic fail-open fallback.
- Synthesis runs once after all sequential Tasks terminate and keeps the existing grounded-answer and citation behavior.
- Full Agent prompt/context must not contain raw prior attempts beyond the compact Working Context, preventing prompt growth with each loop.
- The first version retains existing Retriever implementations, winning Graph/Vector configuration, Graph triple filter behavior and no external final reranker.
- Retriever-internal LLM calls, including Graph triple filtering, remain independently traced and are not counted as removed Agent orchestration calls.
- A simple query that succeeds on the first retrieval is expected to move from approximately five orchestration LLM calls (Plan, Route, Observe, Reflect, Synthesize) to three (PlanRoute, Assess, Synthesize).
- Operational limits and budgets are configuration values rather than prompt-only constants.
- The migration strategy is Freeze Baseline then In-place Redesign. Two long-lived Agent implementations will not be maintained.
- No Agent code rewrite begins until the fixed paired baseline has been captured with result files, configuration and commit identity.

## Testing Decisions

- The highest primary test seam is the compiled Full Agent graph with fake LLM responses and fake Retrievers. Tests assert externally visible state transitions, Tool actions, attempt records, accepted evidence and final citations rather than internal helper call order.
- Existing end-to-end Agent graph phase tests provide prior art for simulating Planner, Router, retrieval, reflection and synthesis behavior. These tests should be adapted to the four-node contract instead of replaced by many node-internal tests.
- Existing Agent node tests provide prior art for Retriever dispatch, fallback behavior, deduplication, synthesis grounding and citation sanitization.
- Pydantic boundary tests cover valid output, missing required fields, unknown fields, invalid enum values and cross-field contradictions.
- Validator tests cover null/empty fields, wrong types, unknown Tools/enums, non-positive top-k, duplicate IDs and accepted chunk IDs not present in the current batch; missing or ambiguous semantic anchors produce warnings rather than hard failures.
- Plan tests verify that a valid Plan proceeds without repair, an invalid Plan repairs once, and a second invalid result uses deterministic fallback.
- Routing tests verify that financial vocabulary alone never overrides the LLM-selected Graph/Vector/News action, while an explicit LLM-selected Financial action remains executable.
- Retry tests verify that a zero-result Financial attempt returns control to Assess for a new proposal and is never repeated or forced by keyword fallback.
- Planning tests verify that a connected multi-hop chain remains one initial Graph Task while independent evidence types may become separate tool-native Tasks.
- Conservative-validator tests verify structural failures are rejected while ambiguous entity/relation completeness produces warnings rather than hard failure.
- Technical-retry tests verify transient failures do not consume Agent Attempt budget or trigger evidence-driven Tool switching.
- Attempt Ledger tests verify that action, raw chunks, trace and assessment for one retrieval remain in one record and that retries append rather than overwrite prior attempts.
- Assess tests verify missing/partial/covered transitions and mapping of supporting chunks to known Requirements.
- Retry-controller tests verify no exact repeated action, zero-result handling, duplicate-result handling, Tool Retry Profile enforcement, same-tool hints, compatible Tool switching, hard Attempt cap and both conditional third-Attempt paths.
- Termination tests verify that budget_exhausted and no_evidence_gain never imply sufficient coverage.
- Memory tests verify that Attempt Ledger retains full raw evidence while Working Context remains bounded and excludes old full chunk text.
- Evidence Selection tests verify fail-open behavior, deterministic deduplication, append-only raw/accepted evidence and coverage-first selection regardless of Attempt order.
- Synthesis tests verify per-subquery evidence representation, global budget behavior, raw-chunk grounding, valid citation IDs and no leakage of internal Attempt metadata.
- Error-path tests verify one Assessment repair, fail-open retention and deterministic termination after repeated invalid output.
- Trace tests verify stage-specific latency and LLM-call fields for PlanRoute, Retriever, Assess, repair, Synthesize and Retriever-internal LLM stages.
- The development evaluation seam is a fixed stratified paired 20-query pilot selected from the strict 74-query dataset. It must include the already-observed problematic FRKG003 and FRKG009 cases.
- The same 20 query IDs, model, Retriever configuration, top-k and evaluation code are used before and after redesign.
- The pilot is an engineering gate only. It is not used as the final thesis conclusion.
- The final acceptance seam is the full 74-query paired benchmark after the pilot passes.
- Hard pilot regression gates compare with the frozen Full Agent: Recall@All no lower than 0.233, Synthesis GroupRecall no lower than 0.217, Hit@All no lower than its frozen baseline, average latency at least 25% lower, average orchestration LLM calls per query at least 30% lower, zero exact repeated actions, invalid plans after repair below 5%, and zero runtime errors.
- The frozen Agent+Graph result is a Graph-promotion engineering target: Recall@All at least 0.408 and Synthesis GroupRecall at least 0.367. The 20-query pilot is not used for statistical significance; the strict-74 run remains the final conclusion seam.
- Results are inspected per query in addition to aggregate metrics, including regressions, wins, stop reasons, attempts, selected evidence and stage latency.
- Final answers continue to be persisted for later RAGAS evaluation, but this spec's primary quality gate is retrieval/synthesis evidence coverage and operational performance.

## Out of Scope

- Redesigning Agent Vector or Agent Graph locked-tool ablation modes.
- Removing Financial Tool from the Full Agent registry; only the keyword-based forced override is removed.
- Changing Graph Search, Vector Search, Financial Search, News Search or Hybrid Search algorithms.
- Changing the winning Phase T Graph/Vector Retriever configuration.
- Removing or redesigning Graph triple filtering.
- Adding an external reranker or a separate LLM Agent-rerank call.
- Adding generic HyDE or a separate Hint-generation LLM call in the first version.
- Changing PPR topology, damping, seed weighting or reusable GDS projection behavior.
- Parallel Task execution, dynamic fan-out or state merging.
- Multi-Agent architecture.
- A general message-history ReAct rewrite.
- Fine-tuning, reinforcement learning or learned routing policies.
- Adding hard semantic Plan validation for companies, periods, metrics, product entities, relationship completeness or arbitrary relationship semantics in the first Plan Validator.
- Changing synthesis budget before the redesigned harness baseline is measured.
- Running RAGAS scoring as part of this implementation; the evaluator only preserves the required final-answer/context records.
- Maintaining V1 and V2 Agent implementations indefinitely.

## Further Notes

- “Agentic intelligence” in this decision means evidence-adaptive control behavior, not a large number of nodes or a visually non-linear graph.
- The Original Query is authoritative. Planner Requirements are validated execution checklists, not a replacement for user intent.
- Deterministic validators should reject only provable structural/capability errors. Ambiguous semantic judgments remain warnings to avoid false rejection and Recall loss.
- Tool selection ownership follows ADR 0001: LLM proposes and deterministic code validates; deterministic code never silently changes the Tool in the normal path.
- The 20-query pilot should be sampled deterministically and stratified by available query metadata such as hop count/type. The selected IDs must be stored with the baseline artifacts.
- Smoke results from two queries are useful diagnostics but cannot establish the acceptance baseline.
- Baseline artifacts must include evaluator configuration and code identity so later comparison remains reproducible.
- If the redesigned Agent misses a quality gate, inspect paired query regressions and stage traces before changing Retriever parameters. The purpose of this spec is to isolate Agentic-layer effects.
- Publishing this spec to the configured GitHub issue tracker is pending because the connected GitHub App returned HTTP 403 for issue creation. Apply the `ready-for-agent` label when tracker write permission is available.
