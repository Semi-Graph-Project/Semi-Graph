---
title: "02 — PlanRoute and Plan Validator — Implementation Navigator"
source_ticket: "/home/kantinan/programming/project/.scratch/agent-harness-evidence-adaptive/issues/02-planroute-and-plan-validator.md"
readiness: "implementation-ready"
code_snapshot: "92eea8facd749ecfa3c5d9473a6e518d1d08d637; prompts.py modified, contracts.py untracked/partial, design and baseline artifacts untracked; inspected 2026-07-24"
---

# 02 — PlanRoute and Plan Validator — Implementation Navigator

## Navigator status

**Status:** `implementation-ready`

**ผลลัพธ์สุดท้าย:** มี `plan_route_node` ที่เปลี่ยน Original Query เป็น 1–3 sequential Tasks พร้อม Tool แรกใน orchestration LLM call เดียว ตรวจด้วย Pydantic, ซ่อมแผนผิดได้หนึ่งครั้ง และจบแบบ traceable `plan_error` เมื่อซ่อมไม่สำเร็จ

**Blocker แรก:** ไม่มี — baseline 20 queries ถูก freeze แล้วตามที่เจ้าของระบบยืนยัน และ artifact อยู่ครบ แม้ `run_config.json` เดิมไม่ได้บันทึก commit identity

**สถานะโค้ดที่ต้องรู้ก่อนเริ่ม:**

- [PLAN_ROUTE_SYSTEM_PROMPT](/home/kantinan/programming/project/src/semigraph/agent/prompts.py:113) มีแล้วและ import ได้
- [contracts.py](/home/kantinan/programming/project/src/semigraph/agent/contracts.py:1) มีโค้ดเริ่มต้นแล้ว แต่ valid payload ยังล้มด้วย `AttributeError` ที่บรรทัด 91 และชื่อ `top_k` ไม่ตรง Prompt/Tool ที่ใช้ `top_k_chunks`
- ยังไม่มี `plan_route_node`, PlanRoute state fields ใน owner ที่ถูกต้อง หรือ `tests/test_agent_plan_route.py`

## Route overview

**Request เข้าระบบที่:** [ws.py::graph](/home/kantinan/programming/project/src/semigraph/agent/ws.py:6) สำหรับ production และ [evaluate_finreflectkg_agent.py::run_agent](/home/kantinan/programming/project/scripts/evaluate_finreflectkg_agent.py:667) สำหรับ evaluator โดยทั้งคู่เริ่มจาก `{"original_query": query}`

**Flow ปัจจุบัน:**

```text
original_query
  → plan_node                 # LLM call 1: query → subqueries
  → tool_select_node          # LLM call 2: subquery → Tool/query
       └─ keyword rule อาจบังคับ Financial ทับคำตอบ LLM
  → execute → observe → reflect → ... → synthesize
```

**Flow เป้าหมายเฉพาะ Ticket 02:**

```text
original_query
  → plan_route_node           # normal path = LLM call 1 ครั้ง
       → parse + Pydantic structural validation
       ├─ valid   → tasks + current_action + plan_trace
       └─ invalid → repair 1 ครั้ง
                      ├─ valid   → repaired tasks + trace
                      └─ invalid → stop_reason=plan_error
```

Ticket 02 สร้างและทดสอบ component seam นี้โดยตรงก่อน ยังไม่เปลี่ยน edge ใน production/evaluator graph; Attempt Ledger เป็น Ticket 03, sequential four-node wiring เป็น Ticket 04 และ production cutover เป็น Ticket 05

**กฎกลางที่ห้ามพัง:**

- `original_query` เป็น intent สูงสุดและห้ามแก้ค่า
- connected multi-hop chain ต้องอยู่ใน Graph Task เดียว โดยแต่ละ hop/claim เป็น Evidence Requirement
- Tool ที่ PlanRoute เลือกได้มี `graph`, `vector`, `financial`, `news`; ไม่มี `hybrid`
- hard validation ตรวจเฉพาะ shape, non-empty, type, enum, positive top-k, cardinality และ unique IDs
- ticker/period/metric ที่อาจตกหล่นเป็น warning เท่านั้น ไม่ทำให้ plan fail
- `plan_route_node` ห้ามเรียก `tool_select_node` และห้ามใช้ `_should_force_financial_tool`
- ห้ามแก้ Retriever, Phase T configuration, Graph triple filter, synthesis หรือ evaluator mode ใน Ticket นี้

---

## Step 1 — ทำให้ PlanRoute Contract รับ valid plan ได้จริง

**เป้าหมาย (Goal)**

ทำให้ Pydantic models เป็น single contract ที่ชื่อ field ตรงกับ Prompt และ Retriever พร้อมปฏิเสธเฉพาะ structural error ตาม ADR/Spec

**ทำไมทำตอนนี้**

Node ยังเขียนอย่างปลอดภัยไม่ได้จนกว่า input boundary จะนิ่ง ปัจจุบัน plan ที่ถูกต้องก็ล้ม เพราะ `validate_unique_ids()` อ่าน `req.retrieval_action.query` ซึ่งไม่มีใน `EvidenceRequirement`

**ไฟล์และ Symbol**

- **Existing/partial** [contracts.py::ToolName](/home/kantinan/programming/project/src/semigraph/agent/contracts.py:38) ถึง `PlanRouteOutput` — owner ของ typed LLM boundary
- **Existing** [tools.py::DEFAULT_TOP_K](/home/kantinan/programming/project/src/semigraph/agent/tools.py:12) — ค่า default ปัจจุบันของ retrieval call
- **Proposed** `tests/test_agent_plan_route.py` — test seam ใหม่ที่ไม่ใช้ LLM/network/Neo4j

**ลงมือแก้**

1. `tests/test_agent_plan_route.py::test_plan_route_output_accepts_one_graph_task` — เขียน test แรกให้แดงด้วย Graph Task หนึ่งงาน มี `T1`, `T1-R1`, query และ `initial_action={tool, query, top_k_chunks}` ก่อนแก้ Model
2. `tests/test_agent_plan_route.py::_valid_plan_payload` — หลัง test แรกแดงแล้วจึง extract payload เป็น fixture function เพื่อใช้ซ้ำใน invalid cases
3. `src/semigraph/agent/contracts.py::module imports` — ลบ planning essay ด้านบน, `Any`, `TypedDict` และ `AgentState`; state มี owner อยู่ที่ `state.py` เท่านั้น เพิ่ม `DEFAULT_TOP_K` จาก `semigraph.agent.tools`
4. `src/semigraph/agent/contracts.py::NonEmptyText` — สร้าง alias ด้วย `Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, strict=True)]` แล้วใช้กับ ID, query และ description ทุกจุด ไม่คง max-length 500/1000 ที่ ADR/Spec ไม่ได้กำหนด
5. `src/semigraph/agent/contracts.py::RetrievalAction` — เปลี่ยน `top_k` เป็น `top_k_chunks: int = Field(default=DEFAULT_TOP_K, gt=0, strict=True)` ให้ตรง [Prompt schema](/home/kantinan/programming/project/src/semigraph/agent/prompts.py:71) และไม่ coerce string เป็นเลข
6. `src/semigraph/agent/contracts.py::EvidenceRequirement` — คงไว้เฉพาะ `requirement_id` และ `description`; ทั้งคู่ non-empty และ `extra="forbid"`
7. `src/semigraph/agent/contracts.py::PlannedTask` — กำหนด `task_id`, `query`, `requirements(min_length=1)`, `initial_action`; ห้ามเพิ่ม semantic score หรือ task status ใน Ticket นี้
8. `src/semigraph/agent/contracts.py::PlanRouteOutput.validate_unique_ids` — ตรวจ `task.task_id` และ `requirement.requirement_id` จากทุก Task; error ต้องบอกชนิดและค่าของ ID ที่ซ้ำ
9. `tests/test_agent_plan_route.py` — เติม invalid cases แบบ parametrize: 0/4 tasks, blank text, extra field, wrong JSON type, `hybrid`/unknown Tool, `top_k_chunks <= 0`, task ID ซ้ำ และ requirement ID ซ้ำข้าม Tasks

**บรรทัดแรกที่เขียน**

```python
def test_plan_route_output_accepts_one_graph_task():
```

**รูปทรงโค้ด**

```python
NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, strict=True),
]

class RetrievalAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: ToolName
    query: NonEmptyText
    top_k_chunks: int = Field(default=DEFAULT_TOP_K, gt=0, strict=True)

class PlanRouteOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tasks: list[PlannedTask] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "PlanRouteOutput":
        # reject duplicate task_id and requirement_id
        return self
```

**Contract หลังจบ Step**

- Input: Python dict ที่ root มี `tasks` 1–3 รายการ
- Output: validated `PlanRouteOutput`; `model_dump(mode="json")` ต้องคืน plain JSON values และ Tool เป็น string value
- Error: Pydantic `ValidationError` สำหรับ missing/extra/wrong type/blank/unknown Tool/non-positive top-k/duplicate ID
- Invariant: Requirement อย่างน้อยหนึ่งรายการต่อ Task; IDs ไม่ซ้ำทั้ง plan; ไม่มี semantic hard rejection

**Tests**

- `tests/test_agent_plan_route.py::test_plan_route_output_accepts_one_graph_task` — validate แล้ว assert `tool == ToolName.graph` และ `top_k_chunks == DEFAULT_TOP_K`
- `tests/test_agent_plan_route.py::test_plan_route_output_rejects_structural_errors` — parametrize malformed payload และ assert `ValidationError`
- `tests/test_agent_plan_route.py::test_plan_route_output_rejects_duplicate_requirement_ids_across_tasks` — ยืนยัน global uniqueness

**ตรวจทันที**

```bash
conda run -n senior_project pytest tests/test_agent_plan_route.py -k plan_route_output -v
```

**จบ Step เมื่อ**

- [ ] valid Graph Task ไม่เกิด `AttributeError`
- [ ] serialized action ใช้ key `top_k_chunks` ไม่ใช่ `top_k`
- [ ] structural invalid cases ทั้งหมด fail ด้วย `ValidationError`
- [ ] semantic wording ที่กำกวมแต่ shape ถูกยัง validate ผ่าน

**ห้ามแตะ**

- `AgentState` ใน `contracts.py` ต้องถูกลบ ไม่สร้าง state owner ตัวที่สอง
- ห้ามเพิ่ม Attempt/Assessment contracts ซึ่งเป็น Ticket 03

---

## Step 2 — ล็อก Prompt ที่มีแล้วและเตรียม State รับผล PlanRoute

**เป้าหมาย (Goal)**

ทำให้ Prompt contract ที่เขียนแล้วมี regression test และให้ `AgentState` owner ตัวจริงรองรับ validated plan โดยไม่ลบ legacy state ก่อน cutover

**ทำไมทำตอนนี้**

หลัง Model นิ่ง เราจึงระบุ state shape ได้ตรงกัน และป้องกันไม่ให้ Prompt เปลี่ยนกลับไปแยก Graph hops หรือใช้ field คนละชื่อในอนาคต

**ไฟล์และ Symbol**

- **Existing/complete** [prompts.py::PLAN_ROUTE_SYSTEM_PROMPT](/home/kantinan/programming/project/src/semigraph/agent/prompts.py:113) — Prompt มี four-tool policy, connected Graph rule, JSON schema และ examples แล้ว
- **Existing** [state.py::AgentState](/home/kantinan/programming/project/src/semigraph/agent/state.py:4) — owner เดียวของ LangGraph state
- **Proposed** `tests/test_agent_plan_route.py::prompt contract tests`

**ลงมือแก้**

1. `tests/test_agent_plan_route.py::test_plan_route_prompt_keeps_connected_graph_chain_in_one_task` — assert Prompt มีคำสั่ง one Graph task, Evidence Requirements และตัวอย่าง Graph Task ที่มี requirements มากกว่าหนึ่งรายการ
2. `tests/test_agent_plan_route.py::test_plan_route_prompt_matches_contract_and_registry` — assert มี Tool ทั้งสี่, ห้าม `hybrid`, schema ใช้ `top_k_chunks`, และ registered derived metric เช่น `revenue_growth_yoy` ถูกเติมจาก `build_financial_capability_summary()`
3. `src/semigraph/agent/state.py::AgentState` — เพิ่ม `tasks: list[dict]`, `current_task_index: int`, `current_action: dict`, `plan_trace: dict` หลัง `original_query`
4. `src/semigraph/agent/state.py::AgentState docstring` — เพิ่มตัวอย่าง PlanRoute shape แบบสั้น หรือ comment กลุ่ม field; ไม่ต้อง rewrite legacy example ทั้งก้อนใน Ticket นี้
5. `src/semigraph/agent/prompts.py::PLAN_ROUTE_SYSTEM_PROMPT` — ไม่เขียนใหม่ หาก tests ผ่าน; แก้เฉพาะข้อความที่ test พบว่า contract ไม่ตรง ห้ามเพิ่ม Prompt อีกชุดที่ประกาศชื่อซ้ำ

**รูปทรงโค้ด**

```python
class AgentState(TypedDict, total=False):
    original_query: str

    # Ticket 02: validated PlanRoute state
    tasks: list[dict]
    current_task_index: int
    current_action: dict
    plan_trace: dict

    # Legacy fields stay until Ticket 05 cutover.
    subqueries: list[str]
    ...
```

**Contract หลังจบ Step**

- Input: `original_query: str` ยังคงเป็น public graph input เดิม
- Output/state: PlanRoute จะเขียน serialized dict/list เท่านั้น ไม่เก็บ Pydantic object ลง LangGraph state
- Error: ไม่มี error behavior ใหม่ใน Step นี้
- Invariant: เพิ่ม field แบบ backward-compatible เพราะ `TypedDict(total=False)`; legacy nodes/tests ยัง compile

**Tests**

- `tests/test_agent_plan_route.py::test_plan_route_prompt_keeps_connected_graph_chain_in_one_task` — ป้องกัน Graph signal regression
- `tests/test_agent_plan_route.py::test_plan_route_prompt_matches_contract_and_registry` — ป้องกัน Prompt/Model field drift
- `tests/test_finreflectkg_agent_evaluator.py::test_all_evaluation_modes_compile_without_running_external_services` — state extension ต้องไม่ทำ evaluator modes พัง

**ตรวจทันที**

```bash
conda run -n senior_project pytest tests/test_agent_plan_route.py -k prompt -v
conda run -n senior_project pytest tests/test_finreflectkg_agent_evaluator.py::test_all_evaluation_modes_compile_without_running_external_services -v
```

**จบ Step เมื่อ**

- [ ] Prompt regression tests ยืนยัน Graph Task และ four-tool contract
- [ ] `AgentState` มี PlanRoute fields เพียง owner เดียว
- [ ] evaluator graph เดิมยัง compile

**ห้ามแตะ**

- ห้ามลบ `subqueries`, `next_tool`, histories หรือ legacy Prompt ใน Step นี้
- ห้ามเปลี่ยน `graph.py` หรือ evaluator wiring

---

## Step 3 — เขียน PlanRoute happy path ให้ใช้ LLM ครั้งเดียว

**เป้าหมาย (Goal)**

เมื่อ LLM คืน valid JSON ระบบต้อง validate, serialize และคืน Task แรกพร้อม trace โดยใช้ orchestration LLM call หนึ่งครั้งเท่านั้น

**ทำไมทำตอนนี้**

Step 1 ล็อกข้อมูลและ Step 2 ล็อก Prompt/State แล้ว Node จึงไม่ต้องเดา field หรือ error shape ระหว่างเขียน

**ไฟล์และ Symbol**

- **Existing** [nodes.py::module imports](/home/kantinan/programming/project/src/semigraph/agent/nodes.py:1) — owner ปัจจุบันของ Agent nodes
- **Proposed** `nodes.py::MAX_PLAN_ROUTE_ATTEMPTS`, `_parse_plan_route_response`, `_collect_plan_warnings`, `plan_route_node`
- **Proposed** `tests/test_agent_plan_route.py::TestPlanRouteNode`

**ลงมือแก้**

1. `src/semigraph/agent/nodes.py::imports` — import `ValidationError`, `PlanRouteOutput`, `PLAN_ROUTE_SYSTEM_PROMPT`; คง imports legacy ไว้เพราะ graph เดิมยังใช้
2. `src/semigraph/agent/nodes.py::MAX_PLAN_ROUTE_ATTEMPTS` — กำหนด `2` เพื่อสื่อว่า initial call + repair call; ห้าม reuse `MAX_REFLECTION_ROUNDS`
3. `src/semigraph/agent/nodes.py::_parse_plan_route_response` — รับ string, strip whitespace และ optional JSON fence หนึ่งชั้น, `json.loads`, require root dict แล้ว `PlanRouteOutput.model_validate(payload)`; ห้ามเติม field หรือสร้าง fallback plan
4. `src/semigraph/agent/nodes.py::_collect_plan_warnings` — ตรวจเฉพาะ explicit anchors ที่ดึงแบบ deterministic ได้: ticker จาก `cfg.tickers`, period token (`FY2025`, `2025`, `Q1`–`Q4`) และ metric จาก `cfg.financial_metric_registry`; ถ้า anchor อยู่ใน Original Query แต่ไม่ปรากฏใน task/requirement/action text ให้คืน warning `{code, anchor_type, value}` โดยไม่ reject plan
5. `src/semigraph/agent/nodes.py::plan_route_node` — signature ต้องสอดคล้อง nodes เดิม: `def plan_route_node(state: AgentState) -> dict`; ใช้ `cfg=get_config()` และ `llm=get_llm(cfg)` เพื่อให้ tests monkeypatch seam เดิมได้
6. `src/semigraph/agent/nodes.py::plan_route_node` — invoke ด้วย system=`PLAN_ROUTE_SYSTEM_PROMPT`, user=`original_query`; valid response ให้ `model_dump(mode="json")` เพียงครั้งเดียว
7. `src/semigraph/agent/nodes.py::plan_route_node` — คืน `tasks`, `current_task_index=0`, `current_action=tasks[0]["initial_action"]` และ `plan_trace`; อย่าคืน `original_query` เพื่อไม่เสี่ยงเขียนทับ
8. `src/semigraph/agent/nodes.py::plan_trace` — happy path ต้องมี `status="ok"`, `validation_mode="structural_only_v1"`, attempt 1=`valid`, `warnings`, `llm_calls=1`, `latency_sec`, `fallback_source=None`
9. `tests/test_agent_plan_route.py::TestPlanRouteNode` — ใช้ `monkeypatch` กับ `nodes.get_config/get_llm` แบบเดียวกับ test nodes เดิม และ FakeLLM ที่นับ `invoke()` calls

**รูปทรงโค้ด**

```text
plan_route_node(state):
    original_query = state["original_query"].strip()
    cfg, llm = get_config(), get_llm(cfg)
    raw = llm.invoke([
        {"role": "system", "content": PLAN_ROUTE_SYSTEM_PROMPT},
        {"role": "user", "content": original_query},
    ])
    plan = _parse_plan_route_response(raw.content)
    serialized = plan.model_dump(mode="json")
    warnings = _collect_plan_warnings(original_query, plan, cfg)
    return {
        tasks: serialized["tasks"],
        current_task_index: 0,
        current_action: serialized["tasks"][0]["initial_action"],
        plan_trace: status=ok, attempts=[valid], warnings, llm_calls=1,
    }
```

**Contract หลังจบ Step**

- Input: state ต้องมี non-blank `original_query`
- Output/state: 1–3 serialized Tasks, index 0, action ของ Task แรก และ JSON-serializable trace
- Error: malformed JSON/Pydantic ยังถูกส่งต่อให้ Step 4 จัดการ; happy path ห้าม fallback
- Invariant: normal path = 1 LLM call; LLM เป็นเจ้าของ Tool; warning ไม่เปลี่ยน Tool/Task และไม่ทำให้ plan fail

**Tests**

- `tests/test_agent_plan_route.py::test_plan_route_node_valid_plan_uses_one_llm_call` — assert call count 1, tasks/action/trace ครบ
- `tests/test_agent_plan_route.py::test_plan_route_node_keeps_multihop_graph_as_one_task` — Fake response มี Graph Task เดียวและ requirements สองรายการ; assert shape ไม่ถูกแปลง
- `tests/test_agent_plan_route.py::test_plan_route_node_allows_independent_graph_and_financial_tasks` — assert task order และ actions คงตาม LLM
- `tests/test_agent_plan_route.py::test_plan_route_node_warnings_do_not_reject_valid_plan` — ตัด FY2025 ออกจาก fake plan แล้ว assert status ยัง `ok` แต่ trace มี `missing_explicit_anchor`
- `tests/test_agent_plan_route.py::test_plan_route_node_does_not_return_original_query_update` — assert key นี้ไม่อยู่ใน node update

**ตรวจทันที**

```bash
conda run -n senior_project pytest tests/test_agent_plan_route.py -k 'valid_plan or multihop or warnings' -v
```

**จบ Step เมื่อ**

- [ ] valid response ใช้ LLM ครั้งเดียว
- [ ] Graph multi-hop shape และ Tool ที่ LLM เลือกถูกเก็บตรง ๆ
- [ ] `current_action` ใช้ `{tool, query, top_k_chunks}`
- [ ] explicit-anchor omission เกิด warning แต่ไม่เกิด repair/failure
- [ ] trace ไม่มี raw LLM response

**ห้ามแตะ**

- ห้ามเรียก `tool_select_node`, `_should_force_financial_tool` หรือ `bind_tools()` จาก PlanRoute
- ห้ามต่อ `plan_route_node` เข้า `build_agent()` ใน Ticket 02

---

## Step 4 — ซ่อม invalid plan หนึ่งครั้งแล้วจบอย่างปลอดภัย

**เป้าหมาย (Goal)**

แผนที่ผิดรูปแบบต้องมีโอกาสซ่อมหนึ่งครั้ง แต่ต้องไม่เกิด loop, ไม่เดา Tool fallback และไม่ส่ง malformed action ไป Retriever

**ทำไมทำตอนนี้**

Happy path ผ่านแล้วจึงเติม error branches โดยไม่ปะปนกับ logic ปกติ และสามารถยืนยันจำนวน LLM calls ของแต่ละกรณีได้ชัด

**ไฟล์และ Symbol**

- **Proposed** `nodes.py::_plan_error_update` — สร้าง terminal update รูปเดียวกันทุก failure
- **Proposed/จาก Step 3** `nodes.py::plan_route_node` — เติม repair loop ที่ bounded
- **Proposed** `tests/test_agent_plan_route.py::repair/error tests`

**ลงมือแก้**

1. `src/semigraph/agent/nodes.py::_plan_error_update` — คืน `tasks=[]`, `current_task_index=0`, `current_action={}`, `stop_reason="plan_error"` และ trace ที่ระบุ attempts, LLM calls, latency, fallback source
2. `src/semigraph/agent/nodes.py::plan_route_node/empty query` — blank/missing Original Query ไม่เรียก LLM; fallback source=`empty_query`, `llm_calls=0`
3. `src/semigraph/agent/nodes.py::plan_route_node/first invalid` — catch `json.JSONDecodeError`, `ValidationError`, `TypeError` และ `ValueError` จาก parser/validator เท่านั้น, normalize เป็นข้อความสั้นใน `attempts[0].errors`, แล้ว invoke LLM อีกครั้งด้วย system prompt เดิม
4. `src/semigraph/agent/nodes.py::repair user message` — ใส่ Original Query, previous invalid output และ normalized validation errors พร้อมคำสั่งให้คืน JSON schema เดิมเท่านั้น; ข้อมูลนี้ใช้ซ่อมแต่ไม่ถูกเก็บเป็น raw trace
5. `src/semigraph/agent/nodes.py::plan_route_node/repaired valid` — คืน plan ตาม Step 3 แต่ `status="repaired"`, attempts=`[invalid, valid]`, `llm_calls=2`
6. `src/semigraph/agent/nodes.py::plan_route_node/second invalid` — ห้าม call ครั้งที่สาม; คืน `_plan_error_update(... fallback_source="validation_failed_after_repair")`
7. `src/semigraph/agent/nodes.py::plan_route_node/provider exception` — ถ้า initial หรือ repair invoke ล้ม ให้ terminal `plan_error` พร้อม source=`provider_error`; ไม่ใช้ repair กับกรณีที่ไม่มี model output ให้ซ่อม
8. `src/semigraph/agent/nodes.py::trace attempts` — แต่ละ attempt เก็บ `{attempt, status, errors}` เท่านั้น; statuses คือ `valid`, `invalid`, `provider_error`

**รูปทรงโค้ด**

```text
if original_query is blank:
    return plan_error(empty_query, llm_calls=0)

invoke initial response
for attempt in [1, 2]:
    try parse + validate
        return valid update(status = ok or repaired)
    catch parse/validation error
        append invalid trace
        if attempt == 2:
            return plan_error(validation_failed_after_repair)
        invoke one repair response with original query + errors

provider exception at either invoke:
    return plan_error(provider_error)
```

**Contract หลังจบ Step**

- Input: Original Query และ LLM response 0–2 ครั้ง
- Output/state: valid/repaired plan หรือ terminal empty plan พร้อม `stop_reason="plan_error"`
- Error: parse/validation retryable หนึ่งครั้ง; provider error และ blank input terminal; exception ไม่หลุดออกจาก node
- Invariant: ไม่เกิน 2 orchestration LLM calls; failure ไม่มี Tool action; ไม่มี keyword fallback

**Tests**

- `tests/test_agent_plan_route.py::test_plan_route_node_repairs_once_then_accepts_valid_plan` — FakeLLM คืน invalid แล้ว valid; assert 2 calls และ status `repaired`
- `tests/test_agent_plan_route.py::test_plan_route_node_stops_after_two_invalid_responses` — assert 2 calls, empty action และ source `validation_failed_after_repair`
- `tests/test_agent_plan_route.py::test_plan_route_node_empty_query_does_not_call_llm` — FakeLLM ที่ห้ามถูกเรียก; assert source `empty_query`
- `tests/test_agent_plan_route.py::test_plan_route_node_provider_error_is_terminal` — assert source `provider_error`, action ว่าง
- `tests/test_agent_plan_route.py::test_plan_trace_never_contains_raw_model_output` — recursive scan trace แล้วไม่พบ invalid response text

**ตรวจทันที**

```bash
conda run -n senior_project pytest tests/test_agent_plan_route.py -k 'repair or invalid or empty_query or provider_error or raw_model' -v
```

**จบ Step เมื่อ**

- [ ] valid first response = 1 call
- [ ] invalid→valid = 2 calls และใช้ repaired plan
- [ ] invalid→invalid = 2 calls แล้ว terminal `plan_error`
- [ ] failure ทุกแบบมี `fallback_source` ชัดเจนและ action ว่าง
- [ ] ไม่มี exception หรือ malformed plan หลุดไป Retriever

**ห้ามแตะ**

- ห้าม fallback เป็น `vector`, `financial` หรือ Original Query action
- ห้าม reuse legacy planner fallback เพราะมันไม่มี Requirements/validated action

---

## Step 5 — ปิด Ticket 02 โดยไม่ cutover ก่อนเวลา

**เป้าหมาย (Goal)**

ยืนยันว่า PlanRoute component พร้อมเป็น dependency ของ Ticket 03 ขณะที่ production Agent, evaluator ablation และ Retrievers ยังทำงานตามเดิม

**ทำไมทำตอนนี้**

Ticket 02 จบที่ validated planning boundary เท่านั้น การรีบเปลี่ยน graph edge จะทำให้ Execute/Assess/Attempt Ledger ยังรับ state คนละ contract และสร้างระบบครึ่งเก่าครึ่งใหม่

**ไฟล์และ Symbol**

- **Existing/inspect only** [graph.py::build_agent](/home/kantinan/programming/project/src/semigraph/agent/graph.py:17)
- **Existing/inspect only** [evaluate_finreflectkg_agent.py::build_evaluation_agent](/home/kantinan/programming/project/scripts/evaluate_finreflectkg_agent.py:129)
- **Existing/inspect only** [tools.py::RETRIEVERS](/home/kantinan/programming/project/src/semigraph/agent/tools.py:247)
- **Existing tests** `test_agent_nodes.py`, `test_agent_graph_phase_d.py`, `test_finreflectkg_agent_evaluator.py`

**ลงมือแก้**

1. ไม่มี source edit ใน Step นี้ ตรวจ `git diff` ว่า `graph.py`, evaluator, `tools.py`, online retrievers และ `config/default.yaml` ไม่ถูกเปลี่ยนจากงาน Ticket 02
2. รัน dedicated PlanRoute tests ทั้งไฟล์
3. รัน legacy Agent node/graph/evaluator tests เพื่อยืนยัน backward compatibility
4. รัน unit suite ทั้งหมด หาก regression เกิด ให้แก้เฉพาะ contract/node/state/prompt seam ของ Ticket 02; ห้ามปรับ Retriever เพื่อกลบ test
5. บันทึกใน handoff ว่า Ticket 03 สามารถ consume `tasks`, `current_task_index`, `current_action`, `plan_trace` ได้ แต่ production graph ยังไม่เรียก PlanRoute

**รูปทรงโค้ด**

```text
No code shape change.
This step verifies boundaries and hands validated state to Ticket 03.
```

**Contract หลังจบ Step**

- Input: ไม่มี public input change; callers ยังส่ง `{"original_query": query}`
- Output/state: PlanRoute component contract พร้อมใช้ แต่ production graph output ยังเป็น legacy contract
- Error: ไม่มี runtime path ใหม่ใน production จนกว่า Ticket 04/05 จะ wire
- Invariant: locked Agent+Vector/Agent+Graph evaluator modes และ Phase T retriever profiles ไม่เปลี่ยน

**Tests**

- `tests/test_agent_plan_route.py` — contract, happy path, warning, repair และ terminal error ครบ
- `tests/test_agent_nodes.py` — legacy nodes ยังทำงาน
- `tests/test_agent_graph_phase_d.py` — compiled production flow เดิมยังผ่าน
- `tests/test_finreflectkg_agent_evaluator.py` — evaluator modes/checkpoint contracts ยังผ่าน

**ตรวจทันที**

```bash
conda run -n senior_project pytest tests/test_agent_plan_route.py -v
conda run -n senior_project pytest tests/test_agent_nodes.py tests/test_agent_graph_phase_d.py tests/test_finreflectkg_agent_evaluator.py -v
conda run -n senior_project pytest tests/ -v
git diff -- src/semigraph/agent/graph.py src/semigraph/agent/tools.py scripts/evaluate_finreflectkg_agent.py config/default.yaml
```

**จบ Step เมื่อ**

- [ ] dedicated และ regression tests ผ่าน
- [ ] production/evaluator graph wiring ไม่มี diff จาก Ticket 02
- [ ] Retriever code/config ไม่มี diff จาก Ticket 02
- [ ] handoff ระบุชัดว่า Ticket 03 เป็น consumer ถัดไปและ Ticket 05 เป็น cutover

**ห้ามแตะ**

- ห้ามลบ legacy node/state/prompt ก่อน Ticket 05
- ห้ามรัน paired 20-query comparison เป็น acceptance ของ Ticket 02; ทำหลัง four-node harness พร้อมใน Ticket 05

## Owner decisions

`None` — ADR 0001/0002, Spec และ Ticket ล็อก Tool ownership, validation strictness, repair budget, fallback และ cutover boundary แล้ว

ข้อสังเกตที่ไม่ block การเขียน: baseline artifact มี dataset fingerprint และผลครบ แต่ไม่มี commit identity ใน `run_config.json`; ห้ามย้อนแก้ผลเดิม ให้บันทึก recovered repository snapshot แยกในการเปรียบเทียบครั้งถัดไป

## Final regression gate

```bash
conda run -n senior_project pytest tests/test_agent_plan_route.py -v
conda run -n senior_project pytest tests/test_agent_nodes.py tests/test_agent_graph_phase_d.py tests/test_finreflectkg_agent_evaluator.py -v
conda run -n senior_project pytest tests/ -v
```

Final Definition of Done:

- [ ] 1–3 Tasks, Requirements และ initial actions ผ่าน Pydantic contract
- [ ] connected multi-hop fixture อยู่ใน Graph Task เดียว
- [ ] normal plan ใช้ LLM 1 call; repair path ไม่เกิน 2 calls
- [ ] second invalid result จบด้วย traceable `plan_error` และไม่มี Tool fallback
- [ ] semantic omissions เป็น warnings ไม่ใช่ hard failure
- [ ] `original_query` ไม่ถูกเขียนทับ
- [ ] production graph, evaluator modes และ Retrievers ยังไม่เปลี่ยน

## Evidence used

| Evidence | Source | ข้อเท็จจริงที่ยืนยัน |
|---|---|---|
| ADR | [0001 LLM-owned Tool selection](/home/kantinan/programming/project/docs/adr/0001-llm-owned-tool-selection.md) | LLM เลือก Tool; validator ปฏิเสธได้แต่ห้าม keyword override/fallback Tool |
| ADR | [0002 evidence-adaptive retry](/home/kantinan/programming/project/docs/adr/0002-evidence-adaptive-tool-aware-retry.md) | Graph chain อยู่ Task เดียว; structural validation conservative; Attempt logic อยู่ Ticket ถัดไป |
| Spec | [Agent Harness Evidence-Adaptive Spec](/home/kantinan/programming/project/docs/spec_agent_harness_evidence_adaptive.md) | Four-node target, Pydantic boundary, repair หนึ่งครั้ง, TypedDict state และ Ticket boundaries |
| Ticket | [02 PlanRoute and Plan Validator](/home/kantinan/programming/project/.scratch/agent-harness-evidence-adaptive/issues/02-planroute-and-plan-validator.md) | Acceptance criteria ของ planning, validation, warnings, repair และ immutable query |
| Domain language | [CONTEXT.md](/home/kantinan/programming/project/CONTEXT.md) | Retrieval Task, Graph Task, Evidence Requirement และ Retrieval Action |
| Repository tree | `src/semigraph/agent`, `tests`, evaluator, config | Request entrypoint, owners, consumers, tests และ protected boundaries |
| Relevant code | [contracts.py](/home/kantinan/programming/project/src/semigraph/agent/contracts.py:38), [prompts.py](/home/kantinan/programming/project/src/semigraph/agent/prompts.py:28), [nodes.py](/home/kantinan/programming/project/src/semigraph/agent/nodes.py:66), [state.py](/home/kantinan/programming/project/src/semigraph/agent/state.py:4) | Prompt ทำแล้ว; contract partial/broken; node/state/tests ยังขาด |
| Baseline | `benchmark/results/finreflectkg_agent/freeze_baseline_first20/summary.json` | Full Agent 20 queries: Hit@All 0.450, Recall@All 0.233, Synthesis GroupRecall 0.217, 5.15 calls, 88.08s |
| Graph target | `benchmark/results/finreflectkg_agent/freeze_baseline_first20_graph/summary.json` | Agent+Graph: Hit@All 0.700, Recall@All 0.408, Synthesis GroupRecall 0.367 |

เอกสารนี้ตรวจความพร้อมของเส้นทางการเขียนโค้ดเท่านั้น การตรวจเอกสารไม่ใช่หลักฐานว่า source code ในอนาคตจะผ่าน tests จนกว่าจะลงมือครบทั้ง 5 Steps และรัน Final regression gate
