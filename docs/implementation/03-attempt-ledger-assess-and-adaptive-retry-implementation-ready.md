---
title: "03 — Attempt Ledger, Assess, and Adaptive Retry — Implementation Navigator"
source_ticket: ".scratch/agent-harness-evidence-adaptive/issues/03-attempt-ledger-assess-and-adaptive-retry.md"
readiness: "implementation-ready"
code_snapshot: "92eea8facd749ecfa3c5d9473a6e518d1d08d637; dirty worktree มี Ticket 02, baseline และ docs ที่ยังไม่ commit; targeted Agent regression 76 tests ผ่าน"
---

# 03 — Attempt Ledger, Assess, and Adaptive Retry — Implementation Navigator

## Navigator status

**Status:** `implementation-ready`

**Final outcome:** หลังจบ Step 6 จะมี component `Execute Attempt → Assess → deterministic retry controller` ที่เก็บทุก retrieval เป็น Attempt เดียว ประเมิน Requirement coverage ใน LLM call เดียว ลองซ่อม Assessment ได้หนึ่งครั้ง และอนุญาต retry ได้ไม่เกินสาม Attempts โดยยังไม่สลับ production graph ก่อน Ticket 04/05

**First blocker:** `None`

## Route overview

**Request starts at:** [graph.py::build_agent](/home/kantinan/programming/project/src/semigraph/agent/graph.py:17) รับ `{"original_query": str}` ผ่าน `graph.invoke()`; boundary ที่ Ticket 03 รับช่วงจริงคือผลจาก [nodes.py::plan_route_node](/home/kantinan/programming/project/src/semigraph/agent/nodes.py:184) ซึ่งมี `tasks`, `current_task_index` และ `current_action`

**Current flow:**

```text
graph.invoke(original_query)
  → plan_node                         # LLM แยก subqueries
  → tool_select_node                  # LLM เลือก Tool + keyword Financial override
  → execute_node                      # กระจายข้อมูลไป chunks/tool log/retrieval trace
  → observe_node                      # LLM สรุป chunks
  → reflect_node                      # LLM ตัดสิน sufficient/retry
      ├─ retry → tool_select_node
      ├─ next subquery → advance_subquery_node
      └─ synthesize_node

Failure ปัจจุบัน:
- Retriever exception ถูกแปลงเป็น empty latest_chunks แต่ไม่มี Technical Retry แยก
- max rounds ถูกตีเป็น sufficient=True
- action/chunks/trace/assessment อยู่คนละ histories จึงจับคู่รอบยาก
```

**Target flowของ Ticket 03:**

```text
plan_route_node output: current Task + validated current_action
  → execute_attempt_node
      ├─ transient failure → Technical Retry ภายใน action เดิม (ไม่เพิ่ม Agent Attempt)
      └─ append Attempt หนึ่ง record + union Raw Evidence Pool
  → assess_node
      ├─ parse/Pydantic/context validate Assessment
      ├─ invalid → repair ได้หนึ่งครั้ง
      ├─ valid → merge coverage + accepted evidence + Evidence Gain
      ├─ controller allow → current_action ใหม่ → Execute รอบถัดไป
      ├─ controller stop/accept → terminal state ของ Task
      └─ repair fail → fail-open latest unique chunks + assessment_error

Ticket 03 จบที่ component boundary; Ticket 04 จึงต่อ graph edge, เดิน Task ถัดไป และ synthesis
```

**Global guardrails:**

- ใช้เฉพาะ Full Agent ใหม่; locked `agent_vector` และ `agent_graph` ยังเป็น evaluator controls เดิม
- LLM เป็นผู้เสนอ retry Tool; deterministic code ตรวจ schema, availability, novelty, profile และ budget แต่ห้าม keyword override หรือแอบเลือก Tool แทน
- `original_query`, PlanRoute Task และ Requirements คงเดิม; coverage เปลี่ยนได้ทาง `missing → partial → covered` เท่านั้น
- Raw chunks ทุก Attempt เก็บแบบ append/union; accepted evidence แยกต่างหากและไม่มี Attempt แรก/ล่าสุดได้ priority
- ไม่แก้ Graph/Vector/Financial/News retriever, Phase T profile, triple filter, `top_k`, PPR, GDS projection หรือ external reranker
- Generic HyDE, parallel Tasks, synthesis selection, production graph wiring และ evaluator projection อยู่นอก Ticket 03
- ค่าปฏิบัติการเริ่มต้น: Agent Attempt สูงสุด `3`, Assessment call สูงสุด `2` (initial + repair), Technical Retry `1` ครั้งหลัง initial transport failure และ Assess context สูงสุด `12000` characters; ทั้งหมดอ่านจาก `Config`

---

## Step 1 — ล็อก Assessment และ Attempt contracts ก่อนเขียน control logic

**Problem** — ปัจจุบันมี Pydantic เฉพาะ PlanRoute ส่วน `AgentState` ยังไม่มี Attempt Ledger, coverage หรือ accepted evidence ทำให้ Execute/Assess ต้องเดา shape ระหว่างเขียน

**Goal** — มี Assessment output contract ที่ reject รูปผิดอย่างชัดเจน และมี state owner เดียวที่บอก shape ของ Attempt/coverage/evidence โดยยังเก็บเป็น JSON-serializable dict/list

**Methology and why use this design** — ใช้ Pydantic เฉพาะขอบเขต output จาก Assess LLM ตาม Spec ส่วน Attempt Ledger ใช้ `TypedDict` ธรรมดา เพราะข้อมูล retrieval ไม่ต้อง parse ผ่าน LLM boundary วิธีนี้จับ schema drift ในจุดเสี่ยงโดยไม่เปลี่ยน `AgentState` เป็น BaseModel และไม่เพิ่ม runtime abstraction ที่ไม่จำเป็น

**Files and symbols**

- **Existing** [contracts.py::ToolName/RetrievalAction](/home/kantinan/programming/project/src/semigraph/agent/contracts.py:15) — reuse Tool enum และ action shape จาก Ticket 02
- **Proposed** `contracts.py::CoverageStatus`, `AssessmentDecision`, `FailureType`, `RetryStrategy`, `AssessmentStopReason`, `RequirementCoverage`, `RetryFeedback`, `AssessmentOutput` — owner ของ structured Assess LLM output
- **Existing** [contracts.py::AgentState](/home/kantinan/programming/project/src/semigraph/agent/contracts.py:94) — duplicate owner ที่ต้องลบ; production owner อยู่ `state.py`
- **Existing** [state.py::AgentState](/home/kantinan/programming/project/src/semigraph/agent/state.py:4) — owner จริงของ LangGraph state
- **Proposed** `state.py::AttemptRecord` และ state fields `attempts`, `evidence_pool`, `accepted_evidence`, `requirement_coverage`
- **Proposed** `tests/test_agent_attempt_retry.py::contract/state tests` — test seam ใหม่ของ Ticket 03
- **Existing** `tests/test_finreflectkg_agent_evaluator.py::AgentState import` — เปลี่ยน test import จาก `contracts` เป็น `state` เพื่อไม่พึ่ง duplicate type; ห้ามเปลี่ยน evaluator runtime

**Implement (ลงมือแก้)**

1. `src/semigraph/agent/contracts.py::enums` — เพิ่มค่าคงที่ดังนี้: coverage=`missing|partial|covered`; decision=`accept|retry|stop`; failure=`zero_results|partial_coverage|irrelevant_results|duplicate_results|tool_mismatch`; strategy=`anchor_enrichment|focus_missing|bridge_hint|constraint_repair|news_query_refinement|switch_tool`; stop=`no_evidence_gain|budget_exhausted|unsupported|assessment_error`
2. `src/semigraph/agent/contracts.py::RequirementCoverage` — require `requirement_id`, `status`, `supporting_chunk_ids`; IDs ต้องไม่ว่างและไม่ซ้ำ; `missing` ต้องไม่มี supporting IDs ส่วน `partial/covered` ต้องมีอย่างน้อยหนึ่ง ID
3. `src/semigraph/agent/contracts.py::RetryFeedback` — require `target_requirement_ids`, `failure_type`, `preserved_anchors`, `diagnostic_summary`, `retry_strategy`; target IDs ต้องไม่ว่างและไม่ซ้ำ; จำกัดข้อความ diagnosis ไม่เกิน 500 characters
4. `src/semigraph/agent/contracts.py::AssessmentOutput` — require `reason`, coverage ครบอย่างน้อยหนึ่งรายการ, `accepted_chunk_ids`, `decision`, `missing_evidence`; optional `retry_feedback`, `next_action`, `stop_reason`; `extra="forbid"` ทุก model
5. `src/semigraph/agent/contracts.py::AssessmentOutput cross-field validator` — `retry` ต้องมี feedback + next action + missing evidence และไม่มี stop reason; `accept` ต้อง coverage ทุกข้อเป็น covered, ไม่มี missing evidence/feedback/next action/stop reason; `stop` ต้องมี stop reasonและไม่มี next action; accepted ID ทุกตัวต้องปรากฏใน supporting IDs อย่างน้อยหนึ่ง Requirement
6. `src/semigraph/agent/contracts.py::AgentState` — ลบ duplicate `AgentState`; contract models อยู่ไฟล์นี้ แต่ shared runtime state มี owner เดียวใน `state.py`
7. `src/semigraph/agent/state.py::AttemptRecord` — เพิ่ม TypedDict สำหรับ `attempt_id`, `task_id`, `attempt_number`, `action`, `retrieval_status`, `chunks`, `retrieval_trace`, `assessment`; `assessment` เริ่มเป็น `None` หลัง Execute และถูกเติมโดย Assess เฉพาะ record ล่าสุด
8. `src/semigraph/agent/state.py::AgentState` — เพิ่ม `attempts: list[AttemptRecord]`, `evidence_pool: list[dict]`, `accepted_evidence: list[dict]`, `requirement_coverage: dict[str, dict]`; คง legacy histories จน Ticket 05
9. `tests/test_finreflectkg_agent_evaluator.py::AgentState import` — import จาก `semigraph.agent.state`; ไม่เปลี่ยน test data หรือ evaluator output contract

**Code shape**

```python
class CoverageStatus(str, Enum):
    missing = "missing"
    partial = "partial"
    covered = "covered"

class AssessmentDecision(str, Enum):
    accept = "accept"
    retry = "retry"
    stop = "stop"

class RequirementCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requirement_id: NonEmptyText
    status: CoverageStatus
    supporting_chunk_ids: list[NonEmptyText] = []
    # missing → IDs ว่าง; partial/covered → IDs ไม่ว่าง; IDs unique

class RetryFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_requirement_ids: list[NonEmptyText] = Field(min_length=1)
    failure_type: FailureType
    preserved_anchors: list[NonEmptyText]
    diagnostic_summary: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    retry_strategy: RetryStrategy

class AssessmentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: NonEmptyText
    requirement_coverage: list[RequirementCoverage] = Field(min_length=1)
    accepted_chunk_ids: list[NonEmptyText]
    decision: AssessmentDecision
    missing_evidence: list[NonEmptyText]
    retry_feedback: RetryFeedback | None = None
    next_action: RetrievalAction | None = None
    stop_reason: AssessmentStopReason | None = None
    # after-validator ใช้ decision matrix ข้างบน

class AttemptRecord(TypedDict):
    attempt_id: str                  # เช่น T1-A1
    task_id: str
    attempt_number: int              # 1..3 ภายใน Task
    action: dict                     # RetrievalAction.model_dump(mode="json")
    retrieval_status: str            # ok | tool_error
    chunks: list[dict]               # raw chunks ของ action นี้
    retrieval_trace: dict            # รวม technical tries + retriever trace
    assessment: dict | None           # validated envelope หรือ fail-open error
```

**Contract after this step**

- Input: raw Assessment JSON ยังไม่ถูกเรียกใช้; models รับ Python dict สำหรับ unit tests
- Output/state: validated `AssessmentOutput`; AgentState fields เป็น ordinary serializable containers
- Errors: unknown fields, invalid enum/type, contradictory decision และ duplicate IDs เป็น Pydantic `ValidationError`
- Invariants: Pydantic อยู่เฉพาะ PlanRoute/Assessment boundaries; Attempt raw chunks ไม่ถูกแปลงหรือตัดทิ้ง

**Tests**

- `tests/test_agent_attempt_retry.py::test_assessment_output_accepts_covered_requirements` — Setup: covered Requirement + known-looking chunk ID; Action: `model_validate`; Assert: decision/IDs serialize เหมือน input
- `tests/test_agent_attempt_retry.py::test_retry_requires_feedback_action_and_missing_evidence` — Setup: ลบทีละ field; Assert: ทุกกรณี raise `ValidationError`
- `tests/test_agent_attempt_retry.py::test_accept_rejects_missing_or_partial_coverage` — Setup: decision accept แต่มี missing/partial; Assert: reject
- `tests/test_agent_attempt_retry.py::test_stop_requires_stop_reason_and_forbids_next_action` — Assert cross-field ทั้งสองด้าน
- `tests/test_agent_attempt_retry.py::test_assessment_rejects_unknown_fields_and_duplicate_ids` — Assert `extra="forbid"` และ unique IDs
- `tests/test_agent_attempt_retry.py::test_agent_state_owner_declares_ticket03_fields` — import `AgentState` จาก `state.py`; Assert annotations มีสี่ field ใหม่และ `contracts.py` ไม่มี duplicate state owner

**Verify**

```bash
conda run -n senior_project pytest tests/test_agent_attempt_retry.py -k 'assessment_output or requires or state_owner' -v
```

**Done when**

- [ ] valid accept/retry/stop ทั้งสาม shape ผ่าน
- [ ] contradiction/unknown field/duplicate ID fail ที่ Pydantic boundary
- [ ] AgentState มี owner เดียวและ legacy evaluator compile test ยัง import ได้

**Do not change**

- `PlanRouteOutput`, `RetrievalAction`, Prompt และ `plan_route_node` ที่ Ticket 02 ใช้งานได้แล้ว
- `graph.py`, evaluator runtime และ Retriever code

---

## Step 2 — สร้าง pure Evidence Gain และ Retry Policy ที่ทดสอบแยกจาก LLM ได้

**Problem** — Spec บอกกฎ retry ชัดในระดับแนวคิด แต่โค้ดยังไม่มีจุดเดียวที่ตัดสิน coverage progress, repeated action, duplicate result, Tool Retry Profile และ attempt budget

**Goal** — มี pure policy module หนึ่งไฟล์ที่รับ validated data แล้วคืน controller decision แบบ deterministic โดยไม่เรียก LLM/Network และไม่เปลี่ยน Tool แทน Assess

**Methology and why use this design** — แยก policy จาก `nodes.py` ซึ่งปัจจุบันยาวและรวมหลายหน้าที่อยู่แล้ว Pure functions ทำให้ bug เรื่อง Attempt ที่สามหรือ Evidence Gain แก้และทดลองได้โดยไม่ตั้ง LangGraph ส่วน Tool-specific behavior เก็บเป็น declarative data ไม่แตกเป็น workflow ต่อ Tool

**Files and symbols**

- **Proposed** `src/semigraph/agent/retry_policy.py::ToolRetryProfile`, `TOOL_RETRY_PROFILES`, `build_tool_retry_capability_summary`, `validate_assessment_context`, `merge_coverage_and_measure_gain`, `decide_retry`
- **Existing** [config/default.yaml::agent_retrieval](/home/kantinan/programming/project/config/default.yaml:86) — เพิ่ม sibling `agent_harness`; ห้ามเปลี่ยน retriever profile เดิม
- **Existing** [config.py::Config](/home/kantinan/programming/project/src/semigraph/config.py:46) — owner ของ operational budgets
- **Proposed** `tests/test_agent_attempt_retry.py::policy tests`

**Implement (ลงมือแก้)**

1. `config/default.yaml::agent_harness` — เพิ่ม `max_attempts_per_task: 3`, `max_assessment_attempts: 2`, `max_technical_retries: 1`, `assess_context_max_chars: 12000`; ไม่วางค่าพวกนี้ใน Prompt อย่างเดียว
2. `src/semigraph/config.py::Config.__init__` — expose `agent_max_attempts_per_task`, `agent_max_assessment_attempts`, `agent_max_technical_retries`, `agent_assess_context_max_chars`; validate attempts `1..3`, assessment `1..2`, technical retries `0..3`, context chars `>=2000`
3. `retry_policy.py::TOOL_RETRY_PROFILES` — Graph รองรับ `anchor_enrichment/focus_missing/bridge_hint`; Vector รองรับ `focus_missing`; Financial รองรับ `constraint_repair`; News รองรับ `news_query_refinement`; `switch_tool` ใช้เมื่อ next Tool ต่างและมี profile ที่ลงทะเบียน
4. `retry_policy.py::build_tool_retry_capability_summary` — สร้าง prompt-facing text จาก profiles เดียวกันเพื่อกัน Prompt/policy drift; ระบุว่า Graph ไม่ใช้ generic HyDE และ Financial repair ห้ามเพิ่ม ticker/metric/period ที่ไม่มีใน intent
5. `retry_policy.py::validate_assessment_context` — require coverage Requirement IDs เท่ากับ current Task IDs; supporting IDs ต้องอยู่ใน `current attempt chunks ∪ previously accepted IDs`; accepted IDs ต้องอยู่ใน current attempt chunks; RetryFeedback target IDs ต้องอยู่ใน Task; next Tool ต้องมี profile
6. `retry_policy.py::merge_coverage_and_measure_gain` — merge status ด้วย rank `missing=0, partial=1, covered=2`, union supporting IDs โดยไม่ลบของเดิม; gain=true เมื่อ status สูงขึ้น หรือ current accepted ID ใหม่ถูกเพิ่มเป็น support ให้ Requirement เท่านั้น
7. `retry_policy.py::decide_retry` — Accept/Stop ผ่านตาม validated output; Retry ตรวจ budget, action novelty, zero/duplicate result, same-tool profile, Tool switch และ conditional third attempt ตามลำดับคงที่
8. `retry_policy.py::_normalized_action_identity` — private one-line helper: `(tool, punctuation/whitespace-normalized casefold query, top_k)`; top-k changeอย่างเดียวไม่ถือเป็น material change หลัง zero result
9. `retry_policy.py::_result_id_set` — private trivial helper: unique non-empty chunk IDs ของ Attempt; non-empty set ที่เท่ากับรอบก่อนคือ duplicate result set

**Code shape**

```python
class ToolRetryProfile(TypedDict):
    same_tool_strategies: dict[FailureType, frozenset[RetryStrategy]]

TOOL_RETRY_PROFILES: dict[ToolName, ToolRetryProfile] = {
    ToolName.graph: {
        "same_tool_strategies": {
            FailureType.zero_results: {anchor_enrichment, bridge_hint},
            FailureType.partial_coverage: {focus_missing, bridge_hint},
            FailureType.irrelevant_results: {anchor_enrichment, focus_missing},
            FailureType.duplicate_results: {focus_missing, bridge_hint},
        }
    },
    ToolName.vector: {"same_tool_strategies": {
        FailureType.zero_results: {focus_missing},
        FailureType.partial_coverage: {focus_missing},
        FailureType.irrelevant_results: {focus_missing},
        FailureType.duplicate_results: {focus_missing},
    }},
    ToolName.financial: {"same_tool_strategies": {
        FailureType.zero_results: {constraint_repair},
        FailureType.partial_coverage: {constraint_repair},
        FailureType.irrelevant_results: {constraint_repair},
        FailureType.duplicate_results: {constraint_repair},
    }},
    ToolName.news: {"same_tool_strategies": {
        FailureType.zero_results: {news_query_refinement},
        FailureType.partial_coverage: {news_query_refinement},
        FailureType.irrelevant_results: {news_query_refinement},
        FailureType.duplicate_results: {news_query_refinement},
    }},
}

def validate_assessment_context(
    assessment: AssessmentOutput,
    task: dict,
    current_chunk_ids: set[str],
    previously_accepted_ids: set[str],
) -> list[dict]:
    # คืน [{code, field, value}] เฉพาะ provable ID/profile errors; [] = valid

def merge_coverage_and_measure_gain(
    previous: dict[str, dict],
    assessment: AssessmentOutput,
) -> tuple[dict[str, dict], dict]:
    # merged coverage ไม่ regress
    # gain trace = {has_gain, improved_requirement_ids, new_support_by_requirement}

def decide_retry(
    assessment: AssessmentOutput,
    attempts: list[dict],
    evidence_gain: dict,
    max_attempts: int,
) -> dict:
    # decision != retry → accept/stop ตาม assessment
    # len(attempts) >= max → stop/budget_exhausted
    # exact normalized action ซ้ำ → stop/no_evidence_gain
    # latest zero + เปลี่ยนเพียง top_k/punctuation → stop/no_evidence_gain
    # duplicate result + same Tool/strategy เดิม → stop/no_evidence_gain
    # same Tool → require failure/strategy อยู่ใน source profile
    # different Tool → require strategy=switch_tool และ target Tool มี profile
    # next attempt == 3 → allow เมื่อ attempt 2 gain หรือเป็น compatible registered switch หลัง adaptation no-gain
    # return {decision, allowed, reason, stop_reason, next_action, warnings, profile}
```

Semantic Tool fit ของ switch ยังคงเป็นของ Assess LLM ตาม ADR 0001; deterministic compatibility ในรุ่นนี้หมายถึง target Tool ลงทะเบียน, action ผ่าน contract, มี Retry Profile และเป็น Tool ใหม่ ส่วนความกำกวมทาง semantic บันทึก warning ไม่ hard-reject เพื่อรักษา Recall

**Contract after this step**

- Input: validated `AssessmentOutput`, current Task, Attempts และ config limits
- Output/state: pure dict decision + monotonic coverage/gain trace; ไม่มี state mutation
- Errors: context ID/profile errors คืนเป็น structured list เพื่อส่ง repair; policy rejection คืน explicit stop reason ไม่ raise
- Invariants: new irrelevant chunk ID ไม่ใช่ gain; exact repeat เป็นศูนย์; Attempt ที่สี่ไม่มีทางผ่าน

**Tests**

- `tests/test_agent_attempt_retry.py::test_context_validator_rejects_unknown_requirement_and_chunk_ids` — current/prior ID sets แบบกำหนดเอง; Assert error codes/values
- `tests/test_agent_attempt_retry.py::test_evidence_gain_requires_status_progress_or_new_accepted_support` — Assert status improvement และ new accepted support เป็น gain
- `tests/test_agent_attempt_retry.py::test_new_irrelevant_chunk_id_is_not_evidence_gain` — new raw ID ไม่อยู่ accepted/supporting; Assert `has_gain=False`
- `tests/test_agent_attempt_retry.py::test_coverage_merge_never_regresses_or_drops_support` — covered ก่อน, LLM ส่ง partial; Assert ยังคง covered และ union IDs
- `tests/test_agent_attempt_retry.py::test_retry_rejects_exact_or_punctuation_only_repeat` — Assert `no_evidence_gain`
- `tests/test_agent_attempt_retry.py::test_same_tool_retry_requires_profile_strategy` — Graph bridge ผ่าน, Graph constraint repair ถูก reject
- `tests/test_agent_attempt_retry.py::test_tool_mismatch_allows_registered_switch_without_keyword_override` — different registered Tool + switch strategy ผ่านตรงตาม LLM proposal
- `tests/test_agent_attempt_retry.py::test_third_attempt_requires_second_gain_or_registered_switch` — ครบทั้ง gain path, fallback path และ reject path
- `tests/test_agent_attempt_retry.py::test_fourth_attempt_is_always_budget_exhausted` — Attempts=3; Assert no next action

**Verify**

```bash
conda run -n senior_project pytest tests/test_agent_attempt_retry.py -k 'context_validator or evidence_gain or coverage_merge or retry or attempt' -v
```

**Done when**

- [ ] Profiles ทั้ง 4 Tools มาจาก registry เดียวที่ Prompt ใช้อธิบายได้
- [ ] gain/repeat/duplicate/budget branches ให้ผล deterministic ตาม tests
- [ ] controller ไม่สร้างหรือเปลี่ยน next Tool เอง

**Do not change**

- `RETRIEVERS`, `TOOL_SCHEMAS`, Graph/Vector profile และ Financial metric registry
- ห้ามเพิ่ม semantic keyword router, fallback matrix ที่บังคับ Tool หรือ HyDE

---

## Step 3 — ให้ Execute สร้าง Attempt record เดียวและแยก Technical Retry

**Problem** — `execute_node` เดิมกระจาย action/chunks/trace ไปหลาย histories และจับ exception เป็น empty result ทันที จึงแยก transport failure ออกจาก evidence miss ไม่ได้

**Goal** — Retrieval Action หนึ่งรายการสร้าง Attempt หนึ่ง record เสมอ; transient calls ที่ลองใหม่อยู่ภายใน record เดิมและไม่เพิ่ม Agent Attempt budget

**Methology and why use this design** — เพิ่ม node ใหม่ชั่วคราวชื่อชัดเจนเพื่อไม่ทำ legacy production graph พังระหว่าง Ticket 03 แล้ว reuse `RETRIEVERS` และ compact traces เดิมทั้งหมด Technical Retry ครอบเฉพาะ exception ที่พิสูจน์ว่าเป็น transport/transient; programming/validation errors ไม่ retry แบบกว้าง

**Files and symbols**

- **Existing** [nodes.py::execute_node](/home/kantinan/programming/project/src/semigraph/agent/nodes.py:415) — legacy node ที่ต้องคงจน Ticket 05
- **Proposed** `nodes.py::execute_attempt_node`, `_is_transient_retrieval_error`
- **Existing** [tools.py::RETRIEVERS](/home/kantinan/programming/project/src/semigraph/agent/tools.py:245) — dispatch registry และ Phase T adapters ที่ต้อง reuse
- **Existing** [nodes.py::_dedupe_chunks_for_synthesis](/home/kantinan/programming/project/src/semigraph/agent/nodes.py:1098) — reuse identity-preserving dedupe สำหรับ `evidence_pool`
- **Proposed** `tests/test_agent_attempt_retry.py::execute attempt tests`

**Implement (ลงมือแก้)**

1. `nodes.py::_is_transient_retrieval_error` — true สำหรับ built-in `TimeoutError/ConnectionError` และ transport class names `ServiceUnavailable`, `SessionExpired`, `ReadTimeout`, `ConnectTimeout`, `TimeoutException`, `ConnectError`, `RemoteProtocolError`; false สำหรับ `ValueError`, `KeyError`, schema/programming error
2. `nodes.py::execute_attempt_node/input` — อ่าน current Task จาก `tasks[current_task_index]`, validate `current_action` ด้วย `RetrievalAction.model_validate`, คำนวณ `attempt_number` จาก Attempts ที่มี `task_id` เดียวกัน + 1; invalid/missing state จบ `unsupported` โดยไม่เรียก Retriever
3. `nodes.py::execute_attempt_node/dispatch` — ใช้ `get_config()` และ `RETRIEVERS[action.tool.value]`; ส่ง `query`, `top_k_chunks`, `cfg` เหมือน adapter เดิมทุกประการ
4. `nodes.py::execute_attempt_node/technical loop` — initial call + `cfg.agent_max_technical_retries`; แต่ละ technical try เก็บ `{technical_try, status, latency_sec, error_type}`; transient exception จึงลองซ้ำ; non-transient หรือ exhausted จบ `tool_error`
5. `nodes.py::execute_attempt_node/result normalization` — รองรับทั้ง `{"chunks", "trace"}` และ legacy `list[dict]`; filter เฉพาะ dict; retain raw chunk dict โดยไม่ annotate/ตัด field
6. `nodes.py::execute_attempt_node/append` — สร้าง `attempt_id=f"{task_id}-A{attempt_number}"`, action serialized, retrieval status, raw chunks, merged retriever/technical trace, `assessment=None`; return `attempts=[*old, new]`
7. `nodes.py::execute_attempt_node/evidence pool` — success รวม `old evidence_pool + raw chunks` แล้ว dedupe แบบ preserve first occurrence; zero result ยัง append Attempt แต่ pool ไม่เปลี่ยน
8. `nodes.py::execute_attempt_node/tool error` — append Attempt หนึ่ง recordที่ chunks ว่าง, assessment None, trace terminal; return `current_action={}`, `stop_reason="tool_error"`; ห้ามส่ง transport failure เข้า Assess เหมือน evidence miss

**Code shape**

```python
def _is_transient_retrieval_error(exc: Exception) -> bool:
    # isinstance TimeoutError/ConnectionError หรือ class name ใน allowlist เท่านั้น

def execute_attempt_node(state: AgentState) -> dict:
    task = state["tasks"][state["current_task_index"]]
    action = RetrievalAction.model_validate(state["current_action"])
    attempt_number = 1 + sum(a["task_id"] == task["task_id"] for a in state.get("attempts", []))

    technical_tries = []
    for technical_try in range(1, cfg.agent_max_technical_retries + 2):
        try:
            result = retriever(query=action.query, top_k_chunks=action.top_k_chunks, cfg=cfg)
            technical_tries.append(status="ok")
            break
        except transient as exc:
            technical_tries.append(status="error", error_type=type(exc).__name__)
            if technical_try <= cfg.agent_max_technical_retries: continue
            return terminal update containing old Attempts plus one tool_error Attempt
        except Exception as exc:
            return terminal update containing old Attempts plus one tool_error Attempt

    attempt = {
        "attempt_id": f"{task_id}-A{attempt_number}",
        "task_id": task_id,
        "attempt_number": attempt_number,
        "action": action.model_dump(mode="json"),
        "retrieval_status": "ok",
        "chunks": chunks,
        "retrieval_trace": {**retriever_trace, "technical_attempts": technical_tries},
        "assessment": None,
    }
    return {
        "attempts": old_attempts + [attempt],
        "evidence_pool": _dedupe_chunks_for_synthesis(old_pool + chunks),
    }
```

**Contract after this step**

- Input: Ticket 02 state มี valid current Task/action; Attempts/evidence pool อาจว่าง
- Output/state: exactly one appended Attempt ต่อ Agent action และ append/union raw pool
- Errors: transient retry อยู่ใน trace; terminal tool error มี empty chunks และ explicit stop; exception ไม่หลุดจาก node
- Invariants: technical call เพิ่มไม่เปลี่ยน `attempt_number`; adapter config/query/top-k ไม่ถูก override

**Tests**

- `tests/test_agent_attempt_retry.py::test_execute_appends_one_cohesive_attempt_and_raw_pool` — Fake retriever คืน chunks+trace; Assert action/chunks/trace/assessment อยู่ record เดียว
- `tests/test_agent_attempt_retry.py::test_execute_retry_appends_instead_of_overwriting_previous_attempt` — Seed T1-A1 แล้ว Execute อีกครั้ง; Assert two records และ A1 unchanged
- `tests/test_agent_attempt_retry.py::test_transient_failure_then_success_uses_one_agent_attempt` — Fake raises `TimeoutError` แล้ว success; Assert two technical entries แต่ Attempt เดียว
- `tests/test_agent_attempt_retry.py::test_exhausted_transient_failure_records_terminal_tool_error` — always timeout; Assert calls=2, one Attempt, stop=`tool_error`
- `tests/test_agent_attempt_retry.py::test_non_transient_programming_error_is_not_retried` — raises `ValueError`; Assert calls=1
- `tests/test_agent_attempt_retry.py::test_zero_result_is_valid_evidence_attempt_not_tool_error` — returns empty list; Assert retrieval status ok เพื่อให้ Assess วินิจฉัย
- `tests/test_agent_attempt_retry.py::test_execute_preserves_phase_t_trace_and_deduplicates_pool` — compact Graph trace และ duplicate chunk; Assert trace keysเดิมอยู่และ pool unique

**Verify**

```bash
conda run -n senior_project pytest tests/test_agent_attempt_retry.py -k 'execute or transient or tool_error or zero_result' -v
```

**Done when**

- [ ] success/zero/error ทุกแบบ append Attempt shape เดียวกัน
- [ ] Technical Retry ไม่เพิ่ม Agent Attempt และไม่เกิน config
- [ ] Raw evidence เก่าไม่หายและ Retriever arguments ไม่เปลี่ยน

**Do not change**

- legacy `execute_node` และ histories ที่ production/evaluator ยังใช้
- Retriever internal retry/config และ Graph triple-filter trace

---

## Step 4 — สร้าง Assess Prompt, bounded Working Context และ validation seam

**Problem** — Observe/Reflect prompts เดิมไม่มี Requirement coverage, chunk-ID selection, Tool Retry Profile หรือ output schema ที่ controller ตรวจได้ และส่ง history คนละก้อน

**Goal** — Assess เห็นข้อมูลจำเป็นใน context ที่มีขอบเขตชัด และตอบ `AssessmentOutput` ที่ parse/context-validate ได้โดยไม่เพิ่ม separate reranker/Hint call

**Methology and why use this design** — รวม Observe, Reflect, evidence selection, feedback, hint และ next actionไว้ใน Prompt เดียว แต่แยก prompt building/parsing เป็น deterministic helpers เพื่อทดสอบขนาดและข้อมูลรั่วได้ Assess เห็น raw text เฉพาะ latest batch; ประวัติเก่าเห็นเพียง accepted previews, actions, IDs และ diagnostics

**Files and symbols**

- **Existing** [prompts.py::PLAN_ROUTE_SYSTEM_PROMPT](/home/kantinan/programming/project/src/semigraph/agent/prompts.py:17) — รูปแบบ capability-first prompt ที่ต้องรักษา
- **Proposed** `prompts.py::_ASSESS_SYSTEM_PROMPT_TEMPLATE`, `ASSESS_SYSTEM_PROMPT`
- **Proposed** `nodes.py::_chunk_preview`, `_compact_assess_diagnostics`, `_build_assess_context`, `_parse_assessment_response`, `_normalize_assessment_error`
- **Existing** `retry_policy.py::build_tool_retry_capability_summary`, `validate_assessment_context` จาก Step 2
- **Proposed** `tests/test_agent_attempt_retry.py::prompt/context/parser tests`

**Implement (ลงมือแก้)**

1. `prompts.py::_ASSESS_SYSTEM_PROMPT_TEMPLATE` — ระบุหน้าที่ map chunks→Requirements, coverage status, accepted IDs, decision, missing evidence, Retry Feedback และ next action; ห้ามตอบ final answer/ใช้ outside knowledge/สร้าง chunk ID
2. `prompts.py::Assess decision rules` — accept เฉพาะทุก Requirement covered; retry ต้องระบุ missing, feedback และ action; stop เมื่อ unsupported/no useful strategy; Tool selectionเป็นของ LLM ตาม registered capabilities; no Financial keyword force
3. `prompts.py::Tool retry rules` — inject summary จาก profiles; Graph hint ต้อง anchor/bridge/focus และไม่ใช่ HyDE; Financial เปลี่ยนเฉพาะ constraints จาก intent; Tool switch ใช้ `switch_tool`
4. `prompts.py::output schema` — field names/enum valuesตรง `AssessmentOutput` ทุกตัว; JSON only, unknown fields forbidden
5. `nodes.py::_chunk_preview` — current batch เก็บ ID/rank/metadataและ text จำกัด 800 charsต่อ chunk; accepted historical preview เก็บ ID/metadataและ text จำกัด 240 chars; ไม่แก้ raw chunksใน state
6. `nodes.py::_compact_assess_diagnostics` — whitelist `status`, `reason`, `abort_reason`, `returned_chunk_ids`, `seed_count`, seeds สูงสุด 5, triple-filter reason และ selected triples สูงสุด 5, candidate count, error type; ไม่ส่ง full candidate rankings/projection blob
7. `nodes.py::_build_assess_context` — include Original Query, current Task/Requirements/action, latest chunk previews, current coverage, accepted previewsสูงสุด 9, summaries ของ prior actions/result IDs, compact latest diagnostics; enforce `cfg.agent_assess_context_max_chars`; ห้ามส่ง full old raw chunks
8. `nodes.py::_parse_assessment_response` — strip optional fenceหนึ่งชั้น, require root dict, `json.loads`, `AssessmentOutput.model_validate`; ไม่เติม default semantic fieldและไม่ fallback
9. `nodes.py::_normalize_assessment_error` — JSON error→`invalid_json`; Pydantic error→loc/type เท่านั้น; context error→structured codesเดิม; Type/Value root error→`invalid_assessment_root`; ห้ามใส่ raw model outputใน trace

**Code shape**

```python
ASSESS_SYSTEM_PROMPT = _ASSESS_SYSTEM_PROMPT_TEMPLATE.replace(
    "{{TOOL_RETRY_CAPABILITIES}}",
    build_tool_retry_capability_summary(TOOL_RETRY_PROFILES),
)

def _chunk_preview(chunk: dict, text_limit: int) -> dict:
    # {chunk_id, rank?, ticker?, fiscal_year?, section?, score?, text[:limit]}

def _compact_assess_diagnostics(trace: dict) -> dict:
    # whitelist + bounded seeds/triples เท่านั้น

def _build_assess_context(state: AgentState, cfg: Config) -> str:
    # latest = attempts[-1]
    # prior attempts = action + retrieval_status + returned IDs เท่านั้น
    # accepted previews bounded; assert/trim section จน len <= max chars

def _parse_assessment_response(raw: str) -> AssessmentOutput:
    # JSON root dict → Pydantic; raise เฉพาะ parse/validation error

def _normalize_assessment_error(exc: Exception | list[dict]) -> list[dict]:
    # safe [{code, field?, type?}], ไม่มี input_value/raw output
```

**Contract after this step**

- Input: latest successful Attempt, current Task/action, previous coverage/accepted evidence
- Output/state: prompt string ≤ configured bound หรือ validated Assessment object; helpersไม่แก้ state
- Errors: parse/schema/context errorsแยก code เพื่อนำไป repair
- Invariants: current raw chunksมองเห็นได้; old raw chunk textไม่เข้า prompt; raw LLM responseไม่เข้า trace

**Tests**

- `tests/test_agent_attempt_retry.py::test_assess_prompt_matches_contract_and_retry_profiles` — Assert fields/enums/tools/strategiesครบและไม่มี hybrid/HyDE instruction
- `tests/test_agent_attempt_retry.py::test_working_context_contains_latest_chunks_and_compact_diagnostics` — Fake Graph trace; Assert anchors/abort/seeds/triplesที่จำเป็นอยู่
- `tests/test_agent_attempt_retry.py::test_working_context_excludes_full_prior_raw_chunks_and_is_bounded` — old chunk markerยาว; Assert markerปลายไม่อยู่และ length≤config
- `tests/test_agent_attempt_retry.py::test_assessment_parser_rejects_extra_or_malformed_output` — Assert JSON/Pydantic failure
- `tests/test_agent_attempt_retry.py::test_normalized_errors_never_contain_raw_model_output` — secret markerใน invalid response; Assertไม่อยู่ errors

**Verify**

```bash
conda run -n senior_project pytest tests/test_agent_attempt_retry.py -k 'prompt or working_context or parser or normalized_errors' -v
```

**Done when**

- [ ] Prompt schemaตรง Pydantic contract/profile registry
- [ ] context มี latest evidenceและ diagnostics แต่ไม่มี full old raw history
- [ ] parse/context errorsพร้อม repairโดย traceไม่รั่ว raw output

**Do not change**

- `OBSERVE_SYSTEM_PROMPT`/`REFLECT_SYSTEM_PROMPT` และ legacy formatter จน Ticket 05
- synthesis prompt/budget/citation logic ซึ่งเป็น Ticket 04

---

## Step 5 — รวม Assess, Evidence Selection และ controller เป็นหนึ่ง node

**Problem** — มี contracts/policy/Attempt แล้วแต่ยังไม่มี owner ที่เรียก Assess LLM หนึ่งครั้ง อัปเดต Attempt ล่าสุด และส่ง retry actionที่ controller อนุมัติ

**Goal** — `assess_node` ทำ happy path, one-repair path, retry/accept/stop และ fail-open pathครบ โดยทุกการตัดสินใจตรวจย้อนหลังจาก latest Attempt ได้

**Methology and why use this design** — Node ทำ orchestration เท่านั้น: build context → call/repair → validate → pure merge/policy → state update การแยก pure policyจาก LLM I/O ทำให้ controllerไม่ขึ้นกับ prompt wording และทำให้ fail-open deterministic ไม่มี random fallback retrieval

**Files and symbols**

- **Proposed** `nodes.py::assess_node`, `_assessment_error_update`
- **Existing** `nodes.py::_build_assess_context`, `_parse_assessment_response`, `_normalize_assessment_error` จาก Step 4
- **Existing** `retry_policy.py::validate_assessment_context`, `merge_coverage_and_measure_gain`, `decide_retry`
- **Existing** [connections.py::get_llm](/home/kantinan/programming/project/src/semigraph/connections.py) — monkeypatch seam เดิม
- **Proposed** `tests/test_agent_attempt_retry.py::assess node tests`

**Implement (ลงมือแก้)**

1. `nodes.py::assess_node/precondition` — require latest Attempt belongs current Task, `retrieval_status="ok"` และ `assessment is None`; invariantผิดจบ `assessment_error` โดยไม่เรียก LLM
2. `nodes.py::assess_node/invoke` — `cfg=get_config()`, `llm=get_llm(cfg)`, system=`ASSESS_SYSTEM_PROMPT`, user=`_build_assess_context`; count call/latencyจริง
3. `nodes.py::assess_node/validation loop` — สูงสุด `cfg.agent_max_assessment_attempts=2`; parse Pydanticแล้ว `validate_assessment_context`; invalid รอบแรกส่ง Original Query, current Task, previous invalid output และ normalized errors พร้อมสั่ง JSON schemaเดิม; invalid รอบสอง fail-open
4. `nodes.py::assess_node/provider error` — ไม่มี model outputให้ซ่อม จึง fail-openทันที; assessment trace ระบุ `fallback_source="provider_error"`
5. `nodes.py::assess_node/valid evidence` — merge monotonic coverage, compute gain, union accepted evidenceเฉพาะ raw chunksใน latest Attemptที่ IDs อยู่ `accepted_chunk_ids`; previous accepted chunksไม่หาย
6. `nodes.py::assess_node/controller` — ส่ง validated Assessment, Attemptsรวม latest, gain และ configให้ `decide_retry`; ห้ามแก้ Tool/queryหลัง controller return
7. `nodes.py::assess_node/store assessment` — copy Attempts listและ latest record ก่อนเติม envelope; earlier records byte-for-byteไม่เปลี่ยน; envelopeมี `status`, `output`, `validation_attempts`, `llm_calls`, `latency_sec`, `evidence_gain`, `controller`, `fail_open=False`
8. `nodes.py::assess_node/state result` — controller retry→return approved `current_action`; accept→`current_action={}`, `stop_reason="sufficient"`; stop/reject→actionว่างและ explicit stop reason; ทุก branchคืน attempts/accepted evidence/coverage
9. `nodes.py::_assessment_error_update` — union latest unique chunksเข้า accepted evidenceตาม Retriever order, เติม latest assessment envelope status error/fail_open true, preserve coverageเดิม, clear action, set `stop_reason="assessment_error"`; ห้ามสร้าง next action

**Code shape**

```python
def _assessment_error_update(
    state: AgentState,
    *,
    validation_attempts: list[dict],
    llm_calls: int,
    latency_sec: float,
    fallback_source: str,
) -> dict:
    # copy latest Attempt แล้วเติม assessment ที่มี status/error,
    # output=None, validation_attempts, llm_calls, latency_sec,
    # fallback_source และ fail_open=True
    # accepted_evidence = dedupe(old accepted + latest chunks)
    # current_action={}, stop_reason=assessment_error

def assess_node(state: AgentState) -> dict:
    context = _build_assess_context(state, cfg)
    for assessment_try in range(1, cfg.agent_max_assessment_attempts + 1):
        response = llm.invoke(system=ASSESS_SYSTEM_PROMPT, user=context_or_repair)
        try:
            assessment = _parse_assessment_response(response.content)
            context_errors = validate_assessment_context(
                assessment,
                task=current_task,
                current_chunk_ids=current_chunk_ids,
                previously_accepted_ids=previously_accepted_ids,
            )
            if context_errors:
                validation_errors = context_errors
            else:
                validation_errors = []
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            validation_errors = _normalize_assessment_error(exc)

        if validation_errors:
            validation_attempts.append({
                "assessment_try": assessment_try,
                "status": "invalid",
                "errors": validation_errors,
            })
            if assessment_try == cfg.agent_max_assessment_attempts:
                return _assessment_error_update(
                    state,
                    validation_attempts=validation_attempts,
                    llm_calls=llm_calls,
                    latency_sec=time.perf_counter() - started_at,
                    fallback_source="validation_failed_after_repair",
                )
            context_or_repair = repair message containing raw output + validation_errors
            continue

        merged_coverage, gain = merge_coverage_and_measure_gain(
            state.get("requirement_coverage", {}),
            assessment,
        )
        accepted = _dedupe_chunks_for_synthesis([
            *state.get("accepted_evidence", []),
            *(chunk for chunk in latest["chunks"] if chunk["chunk_id"] in assessment.accepted_chunk_ids),
        ])
        controller = decide_retry(assessment, attempts, gain, cfg.agent_max_attempts_per_task)
        stored_attempts = prior Attempts + copied latest Attempt with assessment envelope
        if controller["decision"] == "retry":
            return attempts/coverage/accepted + approved current_action
        if controller["decision"] == "accept":
            return attempts/coverage/accepted + empty action + stop_reason sufficient
        return attempts/coverage/accepted + empty action + controller stop_reason
```

**Contract after this step**

- Input: latest successful unassessed Attempt และ Ticket 02 Task/action state
- Output/state: assessed latest record, monotonic coverage, accepted evidence union และ approved next actionหรือ terminal reason
- Errors: invalid output repairหนึ่งครั้ง; second invalid/provider/invariant failure fail-open + `assessment_error`; ไม่มี blind retry
- Invariants: normal Assess=1 orchestration LLM call; repair path≤2; accepted IDs verified; raw model responseไม่ถูกเก็บ

**Tests**

- `tests/test_agent_attempt_retry.py::test_assess_accepts_covered_task_and_updates_latest_attempt` — Fake valid JSON; Assert one LLM call, coverage/accepted/envelope/stop sufficient
- `tests/test_agent_attempt_retry.py::test_assess_returns_controller_approved_same_tool_retry` — partial Graph + bridge action; Assert `current_action`ตรง LLM proposalและ attempt countยังไม่เพิ่มจน Execute
- `tests/test_agent_attempt_retry.py::test_assess_repairs_unknown_chunk_id_once` — invalid context IDแล้ว valid; Assert calls=2/status repaired
- `tests/test_agent_attempt_retry.py::test_assess_second_invalid_fails_open_and_stops` — Assert latest raw chunksเข้า accepted, stop assessment_error, no action
- `tests/test_agent_attempt_retry.py::test_assess_provider_error_fails_open_without_repair` — invoke raises; Assert one callและ fallback source
- `tests/test_agent_attempt_retry.py::test_assess_never_overwrites_prior_attempt_or_accepted_evidence` — Seed A1/acceptedแล้ว assess A2; Assert A1เดิมและ union
- `tests/test_agent_attempt_retry.py::test_assess_retry_rejection_records_controller_reason` — repeated action; Assert no action, no_evidence_gain, decision trace

**Verify**

```bash
conda run -n senior_project pytest tests/test_agent_attempt_retry.py -k 'assess_' -v
```

**Done when**

- [ ] valid/repaired/fail-open/provider branchesมี bounded callsและ traceครบ
- [ ] accepted evidence/coverage/Attemptsเก่าไม่ถูกลบ
- [ ] retry actionเกิดจาก LLM proposalที่ controllerอนุมัติเท่านั้น

**Do not change**

- ห้ามเรียก `tool_select_node`, `_should_force_financial_tool`, `observe_node` หรือ `reflect_node`
- ห้ามทำ evidence selectionเป็น LLM callแยกหรือเรียก Retrieverจาก Assess

---

## Step 6 — พิสูจน์ Ticket 03 เป็น component ที่ loop ได้โดยยังไม่ cutover production

**Problem** — Node tests แยกส่วนอาจผ่านแต่ state transition ระหว่าง Execute/Assess ยังอาจ append ผิด record, เรียกเกิน budget หรือส่ง actionผิดเมื่อวนจริง

**Goal** — มี test-only mini graph และ regression gate ที่พิสูจน์ one-Task adaptive loopครบ โดย production graph/evaluator/retrieversยังไม่มี diffจาก Ticket 03

**Methology and why use this design** — ใช้ `StateGraph` เฉพาะใน test ต่อ `execute_attempt_node → assess_node` และ routeจากผล `current_action/stop_reason` จึงทดสอบ LangGraph merge semanticsจริงโดยไม่แย่ง ownershipของ Ticket 04 ซึ่งต้องต่อ multi-TaskและSynthesize

**Files and symbols**

- **Proposed** `tests/test_agent_attempt_retry.py::_build_ticket03_component_graph` — test-only harness ไม่ exportเข้า production
- **Proposed** `tests/test_agent_attempt_retry.py::component integration tests`
- **Existing/inspect only** [graph.py::build_agent](/home/kantinan/programming/project/src/semigraph/agent/graph.py:17)
- **Existing/inspect only** [evaluate_finreflectkg_agent.py::build_evaluation_agent](/home/kantinan/programming/project/scripts/evaluate_finreflectkg_agent.py:128)
- **Existing regression** `test_agent_plan_route.py`, `test_agent_nodes.py`, `test_agent_graph_phase_d.py`, `test_finreflectkg_agent_evaluator.py`

**Implement (ลงมือแก้)**

1. `tests/test_agent_attempt_retry.py::_build_ticket03_component_graph` — compile test StateGraphที่ START→execute_attempt→assess; conditionalหลัง Assess: มี valid non-empty current_actionและไม่มี terminal stop→execute_attempt, ไม่เช่นนั้น→END; recursion limitต่ำกว่า production
2. `tests/test_agent_attempt_retry.py::Graph same-tool recovery fixture` — startจาก one Graph Task; A1 zero; Assess เสนอ Graph anchor enrichment queryใหม่; A2 ได้ supporting chunkและ Accept; Assert Attempts=2, accepted ID, sufficient และ no exact repeat
3. `tests/test_agent_attempt_retry.py::compatible switch fixture` — A1 Tool mismatch/no gain; Assess เสนอ registered different Toolด้วย strategy switch_tool; second Toolได้ evidence; Assertไม่มี keyword Financial forceและ called Toolsตรง LLM outputs
4. `tests/test_agent_attempt_retry.py::budget fixture` — A1→A2 no gain, A3 pathไม่เข้าเงื่อนไข; Assertหยุด no_evidence_gainก่อน Retriever callที่สาม; แยก fixture A2 gainที่อนุญาต A3
5. ตรวจ `git diff` ว่า Ticket 03 ไม่แก้ `graph.py`, evaluator script, `tools.py` retriever adapters, online retrievers หรือ Phase T config values; การเพิ่ม `agent_harness` configไม่ถือว่าแก้ retrieval algorithm
6. รัน focused + legacy regression; หาก legacy fail ให้แก้เฉพาะ Ticket 03 seam ห้ามเปลี่ยน Retriever/benchmarkเพื่อกลบผล

**Code shape**

```python
def _build_ticket03_component_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("execute_attempt", nodes.execute_attempt_node)
    workflow.add_node("assess", nodes.assess_node)
    workflow.add_edge(START, "execute_attempt")
    workflow.add_edge("execute_attempt", "assess")
    workflow.add_conditional_edges(
        "assess",
        lambda state: "retry" if state.get("current_action") and not state.get("stop_reason") else "end",
        {"retry": "execute_attempt", "end": END},
    )
    return workflow.compile()
```

Test helperนี้ไม่ใช่ proposed production router; Ticket 04 จะเป็น ownerของ `_route_after_assess`, sequential Task advance และ Synthesize edge

**Contract after this step**

- Input: prepared one-Task stateจาก valid PlanRoute shape + FakeLLM/FakeRetrievers
- Output/state: bounded Attempts, assessed records, raw/accepted pools, coverageและ terminal reason
- Errors: loopจบด้วย explicit policy/error reason; LangGraph recursion errorต้องไม่เกิดใน fixtures
- Invariants: production graph/evaluator modesและ Retriever outputsเดิมไม่เปลี่ยน

**Tests**

- `tests/test_agent_attempt_retry.py::test_component_graph_recovers_with_same_graph_tool_hint` — Assert zero→new Graph query→covered ใน 2 Attempts
- `tests/test_agent_attempt_retry.py::test_component_graph_switches_only_to_llm_proposed_registered_tool` — Assert action/tool sequenceตรง fake Assess JSON
- `tests/test_agent_attempt_retry.py::test_component_graph_blocks_unproductive_third_attempt` — Assert retriever call count=2และ stop no_evidence_gain
- `tests/test_agent_attempt_retry.py::test_component_graph_allows_third_attempt_after_second_gain` — Assert call count=3และไม่เกิน
- Existing compile/regression tests — Assert legacy Full Agentและ evaluatorทั้งสาม modesยัง compile/run unit fixtures

**Verify**

```bash
conda run -n senior_project pytest tests/test_agent_attempt_retry.py -v
conda run -n senior_project pytest tests/test_agent_plan_route.py tests/test_agent_nodes.py tests/test_agent_graph_phase_d.py tests/test_finreflectkg_agent_evaluator.py -v
git diff -- src/semigraph/agent/graph.py scripts/evaluate_finreflectkg_agent.py src/semigraph/agent/tools.py src/semigraph/online config/default.yaml
```

ตรวจ diff บรรทัดสุดท้ายต้องมีได้เฉพาะ `config/default.yaml::agent_harness`; `agent_retrieval` valuesต้องเหมือนเดิม

**Done when**

- [ ] mini graphผ่าน same-tool recovery, Tool switch และทั้งสอง Attempt-3 branches
- [ ] ไม่มี exact repeated action, fourth Attempt หรือ random fallback
- [ ] legacy targeted regressionผ่านและ production wiringไม่มี Ticket 03 diff

**Do not change**

- ห้ามต่อ PlanRoute/ExecuteAttempt/Assessเข้า `build_agent()` หรือ evaluatorใน Ticketนี้
- ห้ามลบ legacy nodes/historiesก่อน production cutover Ticket 05
- ห้ามรัน/ตีความ paired 20-query benchmarkก่อน Ticket 04 สร้าง four-node harnessครบ

---

## Owner decisions

`None` — ADR 0001/0002, Spec และ Ticket ล็อก Tool ownership, Evidence Gain, retry guards, Attempt cap, fail-open และ Ticket boundariesแล้ว Navigator ใช้ค่า Technical Retryเริ่มต้นหนึ่งครั้งตาม KISS และเก็บเป็น config เพื่อปรับภายหลังโดยไม่เปลี่ยน interface หรือ evaluation semantics ค่า compatibility ของ Tool switchตั้งใจ conservative: deterministic codeยืนยัน registered/profile/shape/novelty ส่วน semantic fitเป็นของ Assess LLMและ trace warningตาม ADR

## Final regression gate

```bash
conda run -n senior_project pytest tests/test_agent_attempt_retry.py -v
conda run -n senior_project pytest tests/test_agent_plan_route.py tests/test_agent_nodes.py tests/test_agent_graph_phase_d.py tests/test_finreflectkg_agent_evaluator.py -v
conda run -n senior_project pytest tests/ -v
git diff --check
git diff -- src/semigraph/agent/graph.py scripts/evaluate_finreflectkg_agent.py src/semigraph/agent/tools.py src/semigraph/online config/default.yaml
```

Final Definition of Done:

- [ ] Retrieval Actionหนึ่งรายการกลายเป็น cohesive Attemptหนึ่ง record และ Technical Retryไม่กิน Agent Attempt
- [ ] Assessment valid/repaired/error paths boundedที่ 1/2 calls พร้อม known-ID validationและไม่มี raw outputใน trace
- [ ] Evidence Gainนับเฉพาะ status progressหรือ accepted supportใหม่; raw evidence/accepted evidence/coverageไม่ regress
- [ ] repeated action, duplicate result, zero no-change, unsupported profileและ budgetถูก controllerหยุดด้วย reasonชัดเจน
- [ ] Attemptที่สามผ่านเฉพาะ second-gainหรือ registered Tool switchหลัง adaptation no-gain; Attemptที่สี่เป็นศูนย์
- [ ] ไม่มี keyword Financial override, generic HyDE, separate reranker/Hint call หรือ Retriever config change
- [ ] production/evaluator graphยังเป็น legacyจน Ticket 04/05 และ targeted/full unit regressionผ่าน

## Evidence used

| Evidence | Source | Verified fact |
|---|---|---|
| ADR | [0001 LLM-owned Tool selection](/home/kantinan/programming/project/docs/adr/0001-llm-owned-tool-selection.md) | Assess LLMเสนอ Tool; deterministic codeปฏิเสธได้แต่ห้าม keyword overrideหรือเลือก Toolแทน |
| ADR | [0002 Evidence-adaptive Tool-aware retry](/home/kantinan/programming/project/docs/adr/0002-evidence-adaptive-tool-aware-retry.md) | same-tool/profile retry, conditional third Attempt, no generic HyDE, append-only evidence |
| Spec | [Evidence-Adaptive Full Agent Harness](/home/kantinan/programming/project/docs/spec_agent_harness_evidence_adaptive.md) | Four-node target, contracts, context, Evidence Gain, fail-open, testsและ out-of-scope |
| Ticket | [03 Attempt Ledger, Assess, Adaptive Retry](/home/kantinan/programming/project/.scratch/agent-harness-evidence-adaptive/issues/03-attempt-ledger-assess-and-adaptive-retry.md) | cohesive Attempt, technical/evidence retry separation, profiles, max 3, repairหนึ่งครั้ง |
| Dependency ticket | [02 PlanRoute and Plan Validator](/home/kantinan/programming/project/.scratch/agent-harness-evidence-adaptive/issues/02-planroute-and-plan-validator.md) | Task/Requirement/current_action contractที่ Ticket 03รับต่อ |
| Domain language | [CONTEXT.md](/home/kantinan/programming/project/CONTEXT.md) | นิยาม Attempt, Technical Retry, Evidence Retry, Retry Feedback, Evidence Gain, pools |
| Repository tree | `src/semigraph/agent`, `tests/test_agent_*`, evaluator, config | owners, direct consumers, test seamsและ protected wiring |
| Relevant code | [graph.py](/home/kantinan/programming/project/src/semigraph/agent/graph.py:17), [nodes.py](/home/kantinan/programming/project/src/semigraph/agent/nodes.py:184), [state.py](/home/kantinan/programming/project/src/semigraph/agent/state.py:4), [contracts.py](/home/kantinan/programming/project/src/semigraph/agent/contracts.py:15), [tools.py](/home/kantinan/programming/project/src/semigraph/agent/tools.py:245), [prompts.py](/home/kantinan/programming/project/src/semigraph/agent/prompts.py:17) | productionยัง legacy; PlanRoute boundaryมีแล้ว; historiesกระจาย; RETRIEVERS/trace adapters reuseได้ |
| Existing tests | `test_agent_plan_route.py`, `test_agent_nodes.py`, `test_agent_graph_phase_d.py`, `test_finreflectkg_agent_evaluator.py` | monkeypatch seams, LangGraph fixtures, retriever traceและ evaluator compatibility; snapshotผ่าน 76 tests |
| Frozen baseline | `benchmark/results/finreflectkg_agent/freeze_baseline_first20/summary.json` | Full Agent 20: Recall@All 0.233, Synthesis GroupRecall 0.217, 5.15 calls, 88.08s |
| Graph target | `benchmark/results/finreflectkg_agent/freeze_baseline_first20_graph/summary.json` | Agent+Graph: Recall@All 0.408, Synthesis GroupRecall 0.367 |

เอกสารนี้ตรวจความพร้อมของเส้นทางเขียนโค้ดจาก snapshot ปัจจุบันเท่านั้น การตรวจเอกสารไม่ใช่หลักฐานว่า source codeในอนาคตจะผ่าน testsจนกว่าจะลงมือครบทั้ง 6 Stepsและรัน Final regression gate
