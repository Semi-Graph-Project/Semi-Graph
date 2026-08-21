"use strict";

const NS = "http://www.w3.org/2000/svg";

const LAYERS = {
  user:      { label: "User I/O", color: "#edf5f2" },
  agent:     { label: "Agent", color: "#64e0d4" },
  retrieval: { label: "Retrieval", color: "#ffb95c" },
  data:      { label: "Data store", color: "#b5a0ff" },
  offline:   { label: "Data factory", color: "#7cb8ff" },
  guard:     { label: "Validation", color: "#8ddf8a" },
  shared:    { label: "Shared", color: "#ff8e9e" },
  contract:  { label: "Contract", color: "#d58cff" },
};

const FILE = (path, symbol = "") => symbol ? `${path} :: ${symbol}` : path;

const runtimeNodes = [
  {
    id: "query", x: 35, y: 305, w: 170, h: 112, layer: "user", kicker: "INPUT / 00",
    title: "User query", subtitle: "Thai or English", chip: "original_query",
    description: "คำถามต้นฉบับเข้าสู่ Parent AgentState และเป็น anchor ร่วมที่ Worker ทุกตัวได้รับเหมือนกัน",
    contract: "AgentState.original_query: str",
    points: ["ยังไม่มี Task หรือ Attempt", "Planner และ Synthesis อ่าน query ก้อนเดียวกัน", "Worker ได้สำเนาค่านี้ผ่าน Send payload"],
    files: [FILE("src/semigraph/agent/state.py", "AgentState.original_query")],
    note: "กด Next เพื่อดู State เปลี่ยนทีละ node; กล่อง Runtime State แสดงตัวอย่างข้อมูลจริงตาม contract",
  },
  {
    id: "plan", x: 250, y: 305, w: 180, h: 112, layer: "agent", kicker: "LANGGRAPH / 01",
    title: "PlanRoute", subtitle: "atomic evidence tasks", chip: "LLM + Pydantic",
    description: "สร้าง Tasks ที่ค้นแยกกันได้ โดย connected Graph chain ยังคงอยู่ Task เดียวเพื่อรักษา multi-hop signal",
    contract: "original_query → PlanRouteOutput{tasks[1..5]}",
    points: ["คืน tasks และ initial_action", "locked-tool policy ถูกใช้กับทุก Task", "Plan ยังไม่เริ่ม Retriever"],
    files: [FILE("src/semigraph/agent/nodes.py", "plan_route_node"), FILE("src/semigraph/agent/contracts.py", "PlanRouteOutput"), FILE("src/semigraph/agent/prompts.py", "PLAN_ROUTE_SYSTEM_PROMPT")],
    note: "Tasks อิสระกันใน runtime ปัจจุบัน; ถ้า Task ต้องใช้ผลจาก Task อื่น ต้องเพิ่ม dependency contract ก่อน",
  },
  {
    id: "dispatcher", x: 475, y: 305, w: 190, h: 112, layer: "agent", kicker: "LANGGRAPH / 02",
    title: "Task dispatcher", subtitle: "dynamic fan-out", chip: "list[Send]",
    description: "อ่าน Parent tasks แล้วคืน Send หนึ่งใบต่อ Task ให้ LangGraph สร้าง task_worker หลาย instance ใน superstep เดียวกัน",
    contract: "AgentState.tasks → list[Send('task_worker', payload)]",
    points: ["Dispatcher ไม่แก้ AgentState", "Send ระบุ node ปลายทางและ payload", "ไม่มี Tasks จะส่งเส้นทางตรงไป Collector"],
    files: [FILE("src/semigraph/agent/graph.py", "_dispatch_tasks / Send")],
    note: "Send เป็น control instruction ของ LangGraph ไม่ใช่ dict update ที่ถูก merge เข้า AgentState",
  },
  {
    id: "worker_t1", x: 725, y: 65, w: 205, h: 112, layer: "agent", kicker: "WORKER / T1",
    title: "Single-task worker", subtitle: "Graph evidence", chip: "Execute ↔ Assess",
    description: "Worker T1 สร้าง Local AgentState ที่มี tasks=[T1], index=0 และ Ledger ของตัวเอง แล้ววน Retry ภายใน Task เดิม",
    contract: "Send{task:T1} → TaskResult{attempts, completion}",
    points: ["ใช้ execute_attempt_node เดิม", "ใช้ assess_node และ retry policy เดิม", "ไม่เขียน Attempts กลางพร้อม Worker อื่น"],
    files: [FILE("src/semigraph/agent/graph.py", "task_worker / task_workflow"), FILE("src/semigraph/agent/nodes.py", "execute_attempt_node / assess_node")],
    note: "connected Graph chain ทั้งก้อนอยู่ใน T1 และ Retry ตาม feedback แบบ sequential ภายใน Worker",
  },
  {
    id: "worker_t2", x: 725, y: 305, w: 205, h: 112, layer: "agent", kicker: "WORKER / T2",
    title: "Single-task worker", subtitle: "Financial evidence", chip: "Execute ↔ Assess",
    description: "Worker T2 ทำงานพร้อม T1 แต่มี current_action, attempts และ completion แยกจากกันทั้งหมด",
    contract: "Send{task:T2} → TaskResult{attempts, completion}",
    points: ["เริ่มจาก T2.initial_action", "Tool error ของ T2 ไม่หยุด T1/T3", "จบแล้วคืน TaskResult หนึ่งก้อน"],
    files: [FILE("src/semigraph/agent/graph.py", "task_worker"), FILE("src/semigraph/agent/nodes.py", "_complete_current_task")],
    note: "Worker-local current_task_index เป็น 0 เสมอ เพราะ Local State มีเพียง Task เดียว",
  },
  {
    id: "worker_t3", x: 725, y: 545, w: 205, h: 112, layer: "agent", kicker: "WORKER / T3",
    title: "Single-task worker", subtitle: "News evidence", chip: "Execute ↔ Assess",
    description: "Worker T3 เป็น instance ของ node เดียวกัน ไม่ใช่ source function คนละตัว; กล่องสามใบทำให้เห็น runtime fan-out",
    contract: "Send{task:T3} → TaskResult{attempts, completion}",
    points: ["ทำพร้อม Worker อื่นได้", "Retry ยังอยู่ใน T3 เท่านั้น", "completion เก็บ sufficient และ stop_reason"],
    files: [FILE("src/semigraph/agent/graph.py", "task_worker")],
    note: "จำนวน Worker จริงเท่ากับจำนวน Planned Tasks ตั้งแต่ 1 ถึง 5",
  },
  {
    id: "reducer", x: 1010, y: 305, w: 205, h: 112, layer: "shared", kicker: "STATE REDUCER / 03",
    title: "task_results reducer", subtitle: "fan-in append", chip: "Annotated[list, add]",
    description: "LangGraph รวม TaskResult จาก Worker ทุกตัวด้วย reducer add โดยไม่ให้ branches เขียน Attempts กลางชนกัน",
    contract: "TaskResult + TaskResult → AgentState.task_results",
    points: ["แต่ละ Worker คืน list หนึ่งสมาชิก", "Reducer รวมผลเมื่อ superstep จบ", "ลำดับเสร็จยังไม่ใช่ลำดับ Plan"],
    files: [FILE("src/semigraph/agent/state.py", "TaskResult / AgentState.task_results")],
    note: "Reducer มีหน้าที่รวมเท่านั้น; Collector เป็นคนจัดลำดับและเปลี่ยนกลับเป็น runtime fields หลัก",
  },
  {
    id: "collector", x: 1260, y: 305, w: 205, h: 112, layer: "agent", kicker: "LANGGRAPH / 04",
    title: "Task collector", subtitle: "restore Plan order", chip: "attempts + completions",
    description: "อ่าน task_results แล้วเรียงตาม tasks จาก Plan ก่อน flatten Attempts และ completion กลับเข้าสู่ Parent AgentState",
    contract: "tasks + task_results → attempts + completed_tasks",
    points: ["ไม่ใช้ลำดับที่ Worker เสร็จ", "รักษาลำดับ Attempt ภายใน Task", "clear current_action ก่อน Synthesis"],
    files: [FILE("src/semigraph/agent/graph.py", "_collect_task_results")],
    note: "การเรียงแบบ deterministic กันผล Synthesis และ Recall เปลี่ยนเพราะ race order",
  },
  {
    id: "ledger", x: 1260, y: 535, w: 205, h: 112, layer: "shared", kicker: "PARENT STATE",
    title: "Attempt ledger", subtitle: "append-only evidence log", chip: "trace + lineage",
    description: "Collector รวม Worker-local Ledgers เป็น attempts กลางหลังทุก Task เสร็จแล้ว จึงไม่มี concurrent write บน field นี้",
    contract: "AttemptRecord[] → retrieved_chunks / tool_calls / traces",
    points: ["เรียง Task ตาม Plan", "เรียง Attempt ตาม A1→A2→A3 ภายใน Task", "Synthesis derive evidence จาก Ledger นี้"],
    files: [FILE("src/semigraph/agent/ledger.py", "retrieved_chunks / tool_calls / retrieval_traces"), FILE("src/semigraph/agent/contracts.py", "AttemptRecord")],
    note: "task_results เป็น fan-in buffer; attempts คือ public ledger ที่ evaluator และ Synthesis ใช้ต่อ",
  },
  {
    id: "synthesize", x: 1530, y: 305, w: 205, h: 112, layer: "agent", kicker: "LANGGRAPH / 05",
    title: "Grounded synthesis", subtitle: "accepted → raw fallback", chip: "max 9 chunks",
    description: "ถูกเรียกครั้งเดียวหลัง Collector รวมทุก Task แล้ว เลือก evidence สูงสุด 9 chunks และสร้างคำตอบพร้อม citation",
    contract: "selected evidence + task outcomes → answer + citation_map",
    points: ["accepted มาก่อน raw fallback", "กระจายหลักฐานข้าม Task", "ไม่มี evidence จะไม่เรียก LLM"],
    files: [FILE("src/semigraph/agent/nodes.py", "_select_synthesis_chunks / synthesize_attempts_node"), FILE("src/semigraph/agent/prompts.py", "SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT")],
    note: "Synthesis ไม่เห็น Worker-local State โดยตรง; มันอ่าน attempts และ completed_tasks ที่ Collector เตรียมไว้",
  },
  {
    id: "answer", x: 1795, y: 305, w: 180, h: 112, layer: "user", kicker: "OUTPUT / 06",
    title: "Answer to user", subtitle: "grounded + cited", chip: "final_answer",
    description: "ผลลัพธ์สุดท้ายประกอบด้วยข้อความตอบ, citation map, synthesis trace และ Attempt Ledger ที่ UI/evaluator ใช้ตรวจย้อนกลับได้",
    contract: "{final_answer, citation_map, synthesis_trace, attempts}",
    points: ["ตอบได้บางส่วนและระบุ evidence gap", "citation map ชี้กลับ chunk_id/source metadata", "เหมาะกับการแสดง reasoning trace โดยไม่เปิด hidden chain-of-thought"],
    files: [FILE("src/semigraph/agent/state.py", "final_answer / citation_map"), FILE("src/semigraph/agent/ws.py", "graph = build_agent()")],
    note: "output เป็น evidence trace ไม่ใช่คำแนะนำซื้อขาย — contribution ของโครงงานอยู่ที่ retrieval engineering",
  },
];

const runtimeEdges = [
  { id: "q-plan", from: "query", to: "plan", label: "query" },
  { id: "plan-dispatch", from: "plan", to: "dispatcher", label: "tasks" },
  { id: "send-t1", from: "dispatcher", to: "worker_t1", label: "Send(T1)", curve: "top" },
  { id: "send-t2", from: "dispatcher", to: "worker_t2", label: "Send(T2)" },
  { id: "send-t3", from: "dispatcher", to: "worker_t3", label: "Send(T3)", curve: "bottom" },
  { id: "t1-reducer", from: "worker_t1", to: "reducer", label: "TaskResult", curve: "top", data: true },
  { id: "t2-reducer", from: "worker_t2", to: "reducer", label: "TaskResult", data: true },
  { id: "t3-reducer", from: "worker_t3", to: "reducer", label: "TaskResult", curve: "bottom", data: true },
  { id: "reducer-collector", from: "reducer", to: "collector", label: "task_results" },
  { id: "collector-synth", from: "collector", to: "synthesize", label: "all tasks done" },
  { id: "collector-ledger", from: "collector", to: "ledger", label: "ordered attempts", data: true, fromAnchor: "bottom", toAnchor: "top" },
  { id: "ledger-synth", from: "ledger", to: "synthesize", label: "selected evidence", data: true, curve: "bottom" },
  { id: "synth-answer", from: "synthesize", to: "answer", label: "answer + citations" },
];

const interfaceNodes = [
  {
    id: "i_query", x: 30, y: 290, w: 205, h: 122, layer: "user", kicker: "INPUT / 00",
    title: "Original Query", subtitle: "AgentState entry", chip: "str",
    description: "จุดเริ่มของระบบและ anchor กลางที่ต้องคงความหมายเดิมตลอดทั้งรอบค้นหา",
    contract: "AgentState\n{ original_query: str }",
    points: ["รับจาก: build_agent entry", "ส่งต่อให้: PlanRoute, Worker และ Synthesis", "ห้าม: retry เปลี่ยนความต้องการเดิมแบบอิสระ"],
    files: [FILE("src/semigraph/agent/state.py", "AgentState.original_query"), FILE("src/semigraph/agent/graph.py", "build_agent")],
    note: "เวลา debug ให้เริ่มจาก query นี้ แล้วตรวจว่า Task และ action ยังรักษา ticker, period และ relationship anchor ครบหรือไม่",
  },
  {
    id: "i_plan", x: 275, y: 290, w: 220, h: 122, layer: "agent", kicker: "PLAN / 01",
    title: "PlanRouteOutput", subtitle: "evidence needs", chip: "Pydantic",
    description: "Planner แตกคำถามเป็น Task ที่ค้นได้จริง; connected Graph chain ต้องอยู่ Task เดียวเพื่อไม่เสีย multi-hop signal",
    contract: "PlanRouteOutput\n{ tasks: list[PlannedTask] }\nPlannedTask = { task_id, query, requirements, initial_action }",
    points: ["รับจาก: original_query + Planner LLM", "ส่งต่อให้: dispatcher", "ตรวจ: 1–5 Tasks และ ID ไม่ซ้ำ"],
    files: [FILE("src/semigraph/agent/contracts.py", "PlanRouteOutput / PlannedTask"), FILE("src/semigraph/agent/nodes.py", "plan_route_node")],
    note: "ถ้า Plan ผิด ให้ debug ที่ requirement/action ก่อนดู Retriever เพราะ Worker จะทำตามสัญญานี้",
  },
  {
    id: "i_action", x: 535, y: 290, w: 220, h: 122, layer: "contract", kicker: "ACTION / 02",
    title: "RetrievalAction", subtitle: "tool call request", chip: "strict model",
    description: "สัญญากลางที่บอกว่า Worker จะเรียก Tool ไหน ด้วย query อะไร และต้องการกี่ chunks",
    contract: "RetrievalAction\n{ tool: vector|graph|financial|news,\n  query: str, top_k_chunks: 1..100 }",
    points: ["รับจาก: PlannedTask.initial_action หรือ Assess.next_action", "ส่งต่อให้: execute_attempt_node", "ห้าม: field นอก schema และ query ว่าง"],
    files: [FILE("src/semigraph/agent/contracts.py", "RetrievalAction"), FILE("src/semigraph/agent/nodes.py", "execute_attempt_node")],
    note: "Retry ที่ดีแก้ action ตาม evidence gap เช่น bridge_hint หรือ focus_missing โดยไม่ลบ Attempt เก่า",
  },
  {
    id: "i_attempt", x: 795, y: 290, w: 220, h: 122, layer: "shared", kicker: "LEDGER / 03",
    title: "AttemptRecord", subtitle: "one retrieval try", chip: "TypedDict",
    description: "บันทึกการเรียก Tool หนึ่งครั้งแบบ append-only; รอบใหม่เพิ่ม record ไม่ overwrite รอบเก่า",
    contract: "AttemptRecord\n{ attempt_id, task_id, action,\n  retrieval_status, chunks, retrieval_trace,\n  assessment: dict | None }",
    points: ["รับจาก: execute_attempt_node", "ส่งต่อให้: assess_node, Collector และ evaluator", "เก็บ: raw chunks + trace เดิมครบ"],
    files: [FILE("src/semigraph/agent/contracts.py", "AttemptRecord"), FILE("src/semigraph/agent/nodes.py", "execute_attempt_node")],
    note: "ถ้า retrieval error ให้เก็บ Attempt ที่ chunks ว่างและ terminal status; อย่าปลอมเป็น evidence miss",
  },
  {
    id: "i_assess", x: 1055, y: 290, w: 235, h: 122, layer: "guard", kicker: "ASSESS / 04",
    title: "AssessmentOutput", subtitle: "evidence decision", chip: "Pydantic",
    description: "ตรวจว่า chunks ครอบคลุม Requirement หรือยัง แล้วเลือก accept, retry หรือ stop",
    contract: "AssessmentOutput\n{ accepted_chunk_ids, covered_requirement_ids,\n  decision: accept|retry|stop,\n  retry_strategy?: anchor_enrichment|focus_missing|bridge_hint|\n    constraint_repair|news_query_refinement|switch_tool,\n  next_action?: RetrievalAction }",
    points: ["รับจาก: latest Attempt + current Task", "ส่งต่อ: retry controller หรือ TaskResult", "retry ต้องมี strategy และ next_action"],
    files: [FILE("src/semigraph/agent/contracts.py", "AssessmentOutput"), FILE("src/semigraph/agent/nodes.py", "assess_node")],
    note: "Assessment ไม่สร้าง chunk ID เอง; ID ทุกตัวต้องมาจาก Attempt ปัจจุบันหรือ evidence ที่ยอมรับแล้ว",
  },
  {
    id: "i_result", x: 1330, y: 290, w: 220, h: 122, layer: "contract", kicker: "WORKER OUTPUT / 05",
    title: "TaskResult", subtitle: "worker boundary", chip: "TypedDict",
    description: "ขอบเขตระหว่าง Worker ที่ทำงานแบบ isolated กับ Parent State ที่รอรวมผล",
    contract: "TaskResult\n{ task_id: str,\n  attempts: list[AttemptRecord],\n  completion: { task_id, sufficient, stop_reason } }",
    points: ["รับจาก: task_worker หลัง Task จบ", "ส่งต่อให้: task_results reducer", "ไม่รวม: evidence ซ้ำใน completion"],
    files: [FILE("src/semigraph/agent/state.py", "TaskResult"), FILE("src/semigraph/agent/graph.py", "task_worker")],
    note: "Worker หนึ่งตัวคืน TaskResult หนึ่งก้อน; Task error ไม่ควรหยุด Worker ของ Task อื่น",
  },
  {
    id: "i_state", x: 1590, y: 290, w: 235, h: 122, layer: "contract", kicker: "PARENT STATE / 06",
    title: "AgentState", subtitle: "shared runtime state", chip: "TypedDict",
    description: "State เจ้าของจริงหลัง Collector รวมผลตาม Plan order แล้ว พร้อมส่งให้ Synthesis และ evaluator",
    contract: "AgentState (total=False)\n{ original_query: str, tasks: list[dict],\n  current_task_index: int, current_action: dict,\n  plan_trace: dict,\n  task_results: Annotated[list[TaskResult], add],\n  attempts: list[AttemptRecord], completed_tasks: list[dict],\n  synthesis_trace: dict, stop_reason: str,\n  final_answer: str, citation_map: list[dict] }",
    points: ["รับจาก: Collector และ Synthesis", "ส่งต่อให้: synthesize_node, checkpoint และ evaluator", "task_results ใช้ reducer add; attempts รวมหลัง fan-in"],
    files: [FILE("src/semigraph/agent/state.py", "AgentState"), FILE("src/semigraph/agent/graph.py", "_collect_task_results")],
    note: "เวลา debug ให้แยก Worker-local state ออกจาก Parent AgentState; ห้ามคิดว่า task_results เรียงตามเวลาที่เสร็จ",
  },
  {
    id: "i_output", x: 1865, y: 290, w: 235, h: 122, layer: "user", kicker: "OUTPUT / 07",
    title: "Synthesis result", subtitle: "grounded response", chip: "final contract",
    description: "คำตอบที่สร้างจาก selected raw chunks เท่านั้น พร้อม citation map และ trace ที่ตรวจสอบย้อนหลังได้",
    contract: "AgentState output\n{ final_answer: str, citation_map: list[dict],\n  synthesis_trace: dict, attempts: list[AttemptRecord] }",
    points: ["รับจาก: completed_tasks + selected evidence", "ส่งให้: User, UI และ RAGAS projection", "citation ต้องชี้เฉพาะ selected chunk IDs"],
    files: [FILE("src/semigraph/agent/nodes.py", "synthesize_attempts_node"), FILE("src/semigraph/agent/state.py", "final_answer / citation_map")],
    note: "นี่คือ public answer contract; Attempt Ledger และ synthesis_trace ทำให้คำตอบ audit ได้โดยไม่เปิด hidden chain-of-thought",
  },
];

const interfaceEdges = [
  { id: "iq-plan", from: "i_query", to: "i_plan", label: "original_query" },
  { id: "iplan-action", from: "i_plan", to: "i_action", label: "initial_action" },
  { id: "ia-attempt", from: "i_action", to: "i_attempt", label: "execute" },
  { id: "iattempt-assess", from: "i_attempt", to: "i_assess", label: "latest attempt", data: true },
  { id: "iassess-retry", from: "i_assess", to: "i_action", label: "retry / next_action", retry: true, curve: "top" },
  { id: "iassess-result", from: "i_assess", to: "i_result", label: "accept / stop", data: true },
  { id: "iresult-state", from: "i_result", to: "i_state", label: "task_results reducer", data: true },
  { id: "istate-output", from: "i_state", to: "i_output", label: "selected evidence" },
];

const graphNodes = [
  {
    id: "g_query", x: 35, y: 300, w: 170, h: 112, layer: "user", kicker: "QUERY / 00", title: "Graph query", subtitle: "relationship intent", chip: "natural language",
    description: "Graph Search รับ query ที่คง entity และ relationship anchor จาก task ของ Planner", contract: "query: str + top_k_chunks", points: ["production profile ปิด query expansion", "รองรับ node, triple และ hybrid seed modes", "trace ทุกขั้นเพื่อใช้ evaluation"], files: [FILE("src/semigraph/online/graph_search.py", "trace_graph_search")], note: "Agent profile ปัจจุบันใช้ triple mode เพราะ relational text จับ intent หลายทอดได้ดีกว่า entity name เดี่ยว",
  },
  {
    id: "g_expand", x: 250, y: 90, w: 180, h: 112, layer: "agent", kicker: "OPTIONAL", title: "Query expansion", subtitle: "implicit entity hints", chip: "LLM fail-open",
    description: "LLM เติม named entity ที่ถูกอ้างโดยนัย เช่น Ryzen maker → AMD แต่เก็บ query เดิมไว้เสมอ", contract: "query → query + hint tokens", points: ["ตรวจความยาวและ newline", "เมื่อ provider error คืน query เดิม", "production graph profile use_expansion=false"], files: [FILE("src/semigraph/online/query_expand.py", "expand_query")], note: "เป็น optional path ใน graph experiments และ ticker resolution fallback ไม่ใช่ default ของ Agent Graph profile",
  },
  {
    id: "g_embed", x: 250, y: 300, w: 180, h: 112, layer: "retrieval", kicker: "SEMANTIC / 01", title: "Query embedding", subtitle: "BGE base EN v1.5", chip: "768 dimensions",
    description: "แปลง query เป็นเวกเตอร์ L2-normalized ด้วย sentence-transformers local model", contract: "str[] → ndarray[n, 768]", points: ["โหลด model ครั้งเดียวด้วย lru_cache", "device จาก config; ปัจจุบัน CPU", "ใช้ model เดียวกับ offline indexes"], files: [FILE("src/semigraph/offline/embeddings.py", "EmbeddingModel / get_embedding_model")], note: "ใช้ embedding model เดียวกันทั้ง query และ corpus เพื่อให้ dot product เท่ากับ cosine หลัง normalize",
  },
  {
    id: "g_triple_index", x: 475, y: 300, w: 190, h: 112, layer: "data", kicker: "NEO4J / 02", title: "Triple index", subtitle: "head–relation–tail text", chip: "in-memory matrix",
    description: "โหลด triple_embedding จาก domain relationships ใน Neo4j เป็น NumPy matrix แล้ว cache ต่อ process", contract: "relationship.triple_embedding → vectors + metadata", points: ["ตัด provenance edges ออกจาก index", "metadata เก็บ head/tail type และ specificity", "threshold เริ่มต้น 0.6"], files: [FILE("src/semigraph/online/seed.py", "_load_triple_index / query_to_triple_candidates"), FILE("src/semigraph/offline/embed_triples.py", "embed_triples")], note: "Query-to-Triple จับ relational context ได้ เช่น ‘supplier dependency’ แม้ entity name เองไม่คล้าย query",
  },
  {
    id: "g_candidates", x: 710, y: 300, w: 190, h: 112, layer: "retrieval", kicker: "SEEDING / 03", title: "Top triple candidates", subtitle: "cosine-ranked triples", chip: "top 10",
    description: "คูณ query vector กับ triple matrix, sort descending, ตัดต่ำกว่า threshold และ deduplicate triple", contract: "q_vec × triple_vectors → TripleCandidate[]", points: ["candidate_id เป็น index ที่ LLM filter เลือกได้", "เก็บ similarity และ endpoint specificity", "ไม่สร้าง triple ใหม่ในขั้น online"], files: [FILE("src/semigraph/online/seed.py", "TripleCandidate / query_to_triple_candidates")], note: "candidate set คือขอบเขต anti-hallucination ของขั้น LLM filter",
  },
  {
    id: "g_filter", x: 945, y: 300, w: 190, h: 112, layer: "guard", kicker: "RECOGNITION / 04", title: "LLM triple filter", subtitle: "select IDs only", chip: "2 attempts",
    description: "ให้ LLM เลือกเฉพาะ candidate IDs ที่สัมพันธ์กับ query เพื่อเอา embedding false positives ออก", contract: "query + candidates → selected_candidate_ids", points: ["ห้ามแก้หรือสร้าง triple", "invalid/empty output fallback เป็นอันดับ embedding", "trace เก็บ selected, rejected, latency และ fallback reason"], files: [FILE("src/semigraph/online/triple_filter.py", "filter_triple_candidates")], note: "production profile เปิด graph_triple_filter=llm และ fail-open เพื่อไม่ให้ graph retrieval กลายเป็นศูนย์เพราะ filter ล้ม",
  },
  {
    id: "g_seeds", x: 1180, y: 300, w: 180, h: 112, layer: "retrieval", kicker: "SEEDING / 05", title: "Entity seeds", subtitle: "triple endpoints", chip: "uniform weights",
    description: "แปลง head และ tail ของ triple ที่เลือกเป็น Entity seeds พร้อม similarity/specificity แล้ว deduplicate", contract: "TripleCandidate[] → {name,type,similarity,specificity}[]", points: ["เลือก similarity สูงสุดต่อ entity", "profile ปัจจุบันใช้ uniform PPR weight", "node/hybrid modes เป็นตัวเลือกงานทดลอง"], files: [FILE("src/semigraph/online/seed.py", "triple_candidates_to_seeds")], note: "seed คือจุด teleport เริ่มต้นของ Personalized PageRank ไม่ใช่คำตอบสุดท้าย",
  },
  {
    id: "g_projection", x: 1410, y: 90, w: 205, h: 112, layer: "data", kicker: "NEO4J GDS", title: "Named projection", subtitle: "Entity + Chunk topology", chip: "create once / reuse",
    description: "สร้าง GDS Cypher projection ที่มี Entity และ Chunk พร้อม weighted domain/provenance edges แล้ว reuse ข้าม query", contract: "Neo4j stored graph → semigraph_ppr_entity_chunk", points: ["prepare/reuse/refresh/drop แยกชัดเจน", "ไม่ drop projection หลังทุก query", "ต้อง refresh เมื่อ stored graph เปลี่ยน"], files: [FILE("src/semigraph/online/ppr.py", "ensure_projection / manage_projection")], note: "GDS plugin เป็น dependency หลัก; Neo4j Community core อย่างเดียวรัน gds.pageRank.stream ไม่ได้",
  },
  {
    id: "g_ppr", x: 1410, y: 300, w: 205, h: 112, layer: "retrieval", kicker: "RANKING / 06", title: "Personalized PageRank", subtitle: "walk from seed entities", chip: "damping 0.5",
    description: "กระจาย probability mass จาก seed ผ่าน graph เพื่อยก entity และ passage ที่เชื่อมสัมพันธ์กับคำถามหลายทอด", contract: "sourceNodes + graph → PPR score per node", points: ["gds.pageRank.stream, max 20 iterations", "entity_chunk mode คืน Chunk score โดยตรง", "projection และ PPR latency อยู่ใน trace"], files: [FILE("src/semigraph/online/ppr.py", "run_passage_ppr / _run_ppr_rows")], note: "ความหมายง่าย ๆ: node ที่เดินถึงบ่อยจากสิ่งที่ query สนใจจะได้คะแนนสูง โดยยังมีโอกาส teleport กลับ seed",
  },
  {
    id: "g_chunks", x: 1660, y: 300, w: 195, h: 112, layer: "retrieval", kicker: "PASSAGES / 07", title: "Chunk candidates", subtitle: "PPR-ranked evidence", chip: "pool 100",
    description: "แยก Chunk nodes ออกจากผล PPR, ดึง text/metadata กลับจาก Neo4j และจัดตาม PPR score", contract: "PPR node scores → SEC chunk contract[]", points: ["candidate pool ปัจจุบัน 100", "Entity ranking ถูกเก็บคู่กันใน trace", "entity_only legacy path ยังรองรับ alias cluster + MENTIONS aggregation"], files: [FILE("src/semigraph/online/ppr.py", "_top_chunk_score_rows / run_passage_ppr"), FILE("src/semigraph/online/graph_search.py", "_cluster_aliases / _map_chunks")], note: "entity_chunk topology ทำให้ passage เป็นส่วนหนึ่งของ random walk แทนการ map entity ไป passage ภายหลัง",
  },
  {
    id: "g_rerank", x: 1900, y: 300, w: 185, h: 112, layer: "retrieval", kicker: "OPTIONAL / 08", title: "Final reranker", subtitle: "Cohere or none", chip: "fail-open",
    description: "เลือกส่ง candidate สูงสุด 20 รายการไป external reranker หรือใช้ลำดับ PPR เดิม", contract: "candidate chunks → top-k chunks", points: ["production profile final_rerank=none", "HTTP retry สำหรับ timeout/5xx/429", "fail-open กลับ original order"], files: [FILE("src/semigraph/online/rerank.py", "rerank_chunks"), FILE("src/semigraph/online/graph_search.py", "_apply_final_rerank")], note: "แยก reranker เป็น option เพื่อให้งาน ablation วัด graph signal ได้โดยไม่ปน model ภายนอก",
  },
  {
    id: "g_output", x: 2130, y: 300, w: 185, h: 112, layer: "shared", kicker: "OUTPUT / 09", title: "Graph evidence", subtitle: "chunks + compact trace", chip: "agent adapter",
    description: "Agent adapter คืน chunk และย่อ trace ให้พอสำหรับ Assess/evaluation โดยไม่คัดลอกข้อความซ้ำ", contract: "{chunks, trace{seeds,PPR,candidates,projection}}", points: ["returned_chunk_ids เชื่อม trace กับ raw chunks", "abort_reason บอก no_seeds หรือ empty_ppr", "parameters ระบุ profile ที่รันจริง"], files: [FILE("src/semigraph/agent/tools.py", "_compact_graph_trace / agent_graph_search")], note: "trace ที่ compact แล้วช่วยให้ assessment context ไม่โตเกินงบ แต่ยัง audit retrieval ได้",
  },
  {
    id: "g_neo4j", x: 710, y: 540, w: 420, h: 112, layer: "data", kicker: "PERSISTED GRAPH", title: "Neo4j knowledge + provenance", subtitle: "Document → Section → Chunk → Entity · domain edges · embeddings", chip: "APOC + GDS",
    description: "ฐานเดียวเก็บทั้งข้อความ SEC, entity graph, provenance hierarchy, synonymy/specificity และ vector properties", contract: "Document/Section/Chunk/Entity + 29 relationship types", points: ["Entity unique ด้วย (name,type)", "domain relationship ผูก source_chunk", "Chunk, Entity และ triple embeddings ถูกสร้าง offline"], files: [FILE("src/semigraph/offline/kg_store.py", "KGStore"), FILE("src/semigraph/ontology/schema.py", "NODE_CATALOG / RELATIONSHIP_CATALOG")], note: "Neo4j รองรับทั้ง Vector RAG และ GraphRAG จาก corpus เดียวกัน ทำให้เทียบ retrieval ได้ยุติธรรม",
  },
  {
    id: "g_seed_modes", x: 1180, y: 540, w: 255, h: 112, layer: "shared", kicker: "ABLATION SWITCH", title: "Node / Triple / Hybrid seeds", subtitle: "same downstream PPR", chip: "seed_mode",
    description: "Graph Search เปิดให้เปลี่ยนเฉพาะวิธีสร้าง seed เพื่อทดสอบผลโดยคง PPR และ output contract เดิม", contract: "seed_mode ∈ {node, triple, hybrid}", points: ["node: Neo4j entity vector index", "triple: in-memory triple embeddings", "hybrid: union แล้ว deduplicate"], files: [FILE("src/semigraph/online/seed.py", "query_to_seeds / query_to_triple_seeds / query_to_hybrid_seeds")], note: "Agent production profile ใช้ triple; node/hybrid อยู่เพื่อการทดลองและวิเคราะห์ failure mode",
  },
];

const graphEdges = [
  { id: "gq-embed", from: "g_query", to: "g_embed", label: "production path" },
  { id: "gq-expand", from: "g_query", to: "g_expand", label: "if enabled", optional: true },
  { id: "expand-embed", from: "g_expand", to: "g_embed", label: "effective_query", optional: true },
  { id: "embed-index", from: "g_embed", to: "g_triple_index", label: "q vector" },
  { id: "index-candidates", from: "g_triple_index", to: "g_candidates", label: "cosine ≥ .6" },
  { id: "candidates-filter", from: "g_candidates", to: "g_filter", label: "bounded IDs" },
  { id: "filter-seeds", from: "g_filter", to: "g_seeds", label: "head + tail" },
  { id: "seeds-ppr", from: "g_seeds", to: "g_ppr", label: "sourceNodes" },
  { id: "projection-ppr", from: "g_projection", to: "g_ppr", label: "reuse", data: true, fromAnchor: "bottom", toAnchor: "top" },
  { id: "ppr-chunks", from: "g_ppr", to: "g_chunks", label: "ranked nodes" },
  { id: "chunks-rerank", from: "g_chunks", to: "g_rerank", label: "top candidates" },
  { id: "rerank-output", from: "g_rerank", to: "g_output", label: "top-k" },
  { id: "neo-index", from: "g_neo4j", to: "g_triple_index", label: "triple embeddings", data: true, curve: "top" },
  { id: "neo-projection", from: "g_neo4j", to: "g_projection", label: "project topology", data: true, curve: "bottom" },
  { id: "neo-chunks", from: "g_neo4j", to: "g_chunks", label: "chunk properties", data: true, curve: "bottom" },
  { id: "modes-seeds", from: "g_seed_modes", to: "g_seeds", label: "alternative", optional: true, fromAnchor: "top", toAnchor: "bottom" },
];

const factoryNodes = [
  { id: "f_sec", x: 30, y: 100, w: 160, h: 108, layer: "offline", kicker: "NARRATIVE / 01", title: "SEC EDGAR", subtitle: "10-K filings", chip: "remote source", description: "ต้นทาง narrative disclosures ของบริษัทใน corpus", contract: "ticker + filing type → submissions", points: ["sec-edgar-downloader สำหรับ batch", "RSS check สำหรับ filing ใหม่", "เก็บ full-submission.txt ต่อ accession"], files: [FILE("src/semigraph/offline/ingest.py", "download_filings / check_rss_feed")], note: "ASML เป็น 20-F จึงต้อง parser แยกจาก section pattern 10-K ปัจจุบัน" },
  { id: "f_raw", x: 230, y: 100, w: 170, h: 108, layer: "data", kicker: "FILESYSTEM / 02", title: "Raw filings", subtitle: "full submission text", chip: "data/raw", description: "เก็บต้นฉบับที่มี DOCUMENT หลายชนิดก่อนทำความสะอาด", contract: "data/raw/sec-edgar-filings/{ticker}/{type}/...", points: ["ใช้ path deterministic", "exhibit/graphic ยังอยู่ในต้นฉบับ", "preprocess เลือกเฉพาะ filing document ที่ต้องการ"], files: [FILE("src/semigraph/offline/ingest.py", "get_filing_paths")], note: "raw layer ทำให้รัน preprocess ใหม่ได้โดยไม่ดาวน์โหลดซ้ำ" },
  { id: "f_pre", x: 440, y: 100, w: 185, h: 108, layer: "offline", kicker: "CLEAN / 03", title: "Preprocess filing", subtitle: "HTML → Markdown", chip: "stream + sections", description: "stream DOCUMENT blocks, ลบ uuencode/boilerplate, แปลง HTML และดึง section 10-K", contract: "full-submission.txt → Item 1 / 1A / 7 Markdown", points: ["primary line parser + regex fallback", "ข้าม TOC lines", "target sections มาจาก config"], files: [FILE("src/semigraph/offline/preprocess.py", "clean_and_save_documents / extract_sections_10k")], note: "Item 8 ตัวเลขไม่เข้า KG เพราะ numerical truth ถูกแยกไป PostgreSQL" },
  { id: "f_sections", x: 665, y: 100, w: 175, h: 108, layer: "data", kicker: "FILESYSTEM / 04", title: "Processed sections", subtitle: "clean Markdown", chip: "data/processed", description: "ข้อความสะอาดราย filing/section พร้อม checkpoint และ error log", contract: "FY{year}-{type}/Item_*.md", points: ["Item 1: business", "Item 1A: risk", "Item 7: MD&A"], files: [FILE("src/semigraph/offline/preprocess.py", "save_sections"), FILE("src/semigraph/offline/pipeline.py", "Checkpoint")], note: "checkpoint ปัจจุบันเป็น JSON ระดับ filing และ save แบบ temp-file rename" },
  { id: "f_chunk", x: 880, y: 100, w: 180, h: 108, layer: "offline", kicker: "SPLIT / 05", title: "Chunker", subtitle: "recursive characters", chip: "4500 / 600", description: "ตัด section เป็น Chunk model พร้อม deterministic ID และ metadata", contract: "section text → Chunk[]", points: ["RecursiveCharacterTextSplitter", "chunk_size 4500 chars", "overlap 600 chars"], files: [FILE("src/semigraph/offline/chunker.py", "Chunk / chunk_filing")], note: "ค่า chunk สะท้อน trade-off ระหว่าง embedding context และ extraction recall" },
  { id: "f_extract", x: 1100, y: 100, w: 190, h: 108, layer: "offline", kicker: "EXTRACT / 06", title: "KG extraction", subtitle: "one LLM call / chunk", chip: "DeepSeek", description: "ส่ง chunk + section-specific ontology prompt ให้ LLM สกัด node และ relationship ใน call เดียว", contract: "Chunk.text + schema → raw JSON graph", points: ["สูงสุด 60 nodes / 80 relations", "ขอเฉพาะ fact ที่ระบุชัด", "ThreadPool parallel ระดับ chunk"], files: [FILE("src/semigraph/offline/kg_extract.py", "extract_chunk"), FILE("src/semigraph/offline/pipeline.py", "_process_one_chunk")], note: "GLiNER ถูกถอดออกจาก active extraction path; ปัจจุบันเป็น single LLM call ตาม source จริง" },
  { id: "f_validate", x: 1330, y: 100, w: 195, h: 108, layer: "guard", kicker: "GUARD / 07", title: "Ontology validation", subtitle: "24 nodes · 29 relations", chip: "Pydantic", description: "normalize ชื่อ, ตัด pronoun/generic entity, เช็ก endpoint type และ semantic direction", contract: "raw JSON → GraphExtractionResult", points: ["schema.py เป็น single source of truth", "section config จำกัด schema ที่เห็น", "invalid output ถูก drop ก่อนแตะฐานข้อมูล"], files: [FILE("src/semigraph/ontology/schema.py", "OntologyRegistry"), FILE("src/semigraph/ontology/nodes.py", "GraphExtractionResult"), FILE("src/semigraph/ontology/normalization.py", "normalize_entity_name")], note: "ontology ใช้ FinReflectKG เป็นฐานและเพิ่ม provenance/document types สำหรับ pipeline" },
  { id: "f_store", x: 1565, y: 100, w: 185, h: 108, layer: "data", kicker: "NEO4J / 08", title: "KG store", subtitle: "idempotent MERGE", chip: "APOC", description: "เขียน provenance hierarchy, mentions และ domain edges ใน transaction ต่อ chunk", contract: "GraphExtractionResult → Neo4j graph", points: ["Document→Section→Chunk→Entity", "relationship เก็บ source_chunk", "reset ต่อ filing ก่อน overwrite"], files: [FILE("src/semigraph/offline/kg_store.py", "KGStore / init_schema")], note: "Entity ใช้ composite uniqueness (name,type); dynamic relationship type ใช้ APOC" },
  { id: "f_repair", x: 1790, y: 100, w: 190, h: 108, layer: "offline", kicker: "QUALITY / 09", title: "Graph repair", subtitle: "evidence-grounded", chip: "LLM batches", description: "เติม relationship ที่ evidence sentence รองรับและ prune entity ที่เหลือเพียง mention-only", contract: "stored filing graph → repaired domain edges", points: ["ทำหลัง extraction ต่อ filing", "validate relation compatibility", "เก็บ rejection reasons และ stats"], files: [FILE("src/semigraph/offline/graph_repair.py", "repair_filing_graph")], note: "repair ไม่ควรสร้าง fact จาก world knowledge; ต้องมี evidence ที่อยู่ใน chunk" },
  { id: "f_features", x: 2020, y: 100, w: 210, h: 108, layer: "offline", kicker: "INDEX / 10", title: "Retrieval features", subtitle: "embed + synonym + specificity", chip: "BGE / rules", description: "สร้าง Chunk/Entity/Triple embeddings, synonym edges และ node specificity ที่ Graph/Vector Search ต้องใช้", contract: "stored graph → vector properties + retrieval edges", points: ["chunk_embedding / entity_embedding", "triple_embedding บน domain edges", "specificity = inverse degree signal"], files: [FILE("src/semigraph/offline/embed_chunks.py", "embed_chunks"), FILE("src/semigraph/offline/embed_nodes.py", "embed_entities"), FILE("src/semigraph/offline/embed_triples.py", "embed_triples"), FILE("src/semigraph/offline/synonymy.py", "build_synonymy"), FILE("src/semigraph/offline/specificity.py", "compute_specificity")], note: "embedding wrapper เดียวกันถูกใช้ online เพื่อให้เวกเตอร์อยู่ space เดียวกัน" },
  { id: "f_neo", x: 2270, y: 100, w: 190, h: 108, layer: "data", kicker: "READY STORE / 11", title: "Neo4j retrieval store", subtitle: "KG + vectors + provenance", chip: "APOC + GDS", description: "ผลลัพธ์ narrative factory ที่พร้อมให้ Graph และ Vector tools ใช้ตอน query", contract: "graph topology + chunk/entity/triple vectors", points: ["vector indexes สำหรับ Chunk/Entity", "named GDS projection สร้างภายหลัง", "provenance ย้อนถึง filing section/chunk"], files: [FILE("src/semigraph/connections.py", "get_neo4j / get_neo4j_driver")], note: "LangChain Neo4jGraph ใช้งาน high-level ได้ ส่วน retrieval ใช้ raw driver เพื่อควบคุม Cypher/GDS" },

  { id: "f_universe", x: 30, y: 440, w: 190, h: 108, layer: "shared", kicker: "NUMERIC / 01", title: "Ticker universe", subtitle: "Neo4j ↔ config preflight", chip: "validated set", description: "อ่าน ticker จาก graph แล้วเทียบจำนวน/รายชื่อกับ config ก่อนเริ่ม financial ETL", contract: "Neo4j Company set + config → target tickers", points: ["default ยึด graph universe", "only_tickers ใช้สำหรับ explicit onboard", "แยก failure ต่อ ticker"], files: [FILE("src/semigraph/financial/etl.py", "load_graph_tickers / validate_universe")], note: "กัน numerical store กับ graph corpus หลุด scope กันโดยไม่รู้ตัว" },
  { id: "f_finnhub", x: 270, y: 440, w: 190, h: 108, layer: "offline", kicker: "FETCH / 02", title: "Finnhub staging", subtitle: "4 endpoints / ticker", chip: "retry + throttle", description: "ดึง annual, quarterly, basic financials และ quote พร้อม retry/backoff", contract: "ticker → four vendor payloads", points: ["protocol ทำให้ mock ใน tests ได้", "hash payload เพื่อ deduplicate", "request interval จาก config"], files: [FILE("src/semigraph/financial/finnhub_client.py", "FinnhubStagingClient")], note: "client นี้อยู่ data factory; runtime financial tool อ่าน local PostgreSQL เป็นค่าเริ่มต้น" },
  { id: "f_payload", x: 510, y: 440, w: 190, h: 108, layer: "data", kicker: "STAGING / 03", title: "Raw payload ledger", subtitle: "immutable lineage", chip: "SHA-256", description: "เก็บ payload ดิบและ metadata ของ ETL run เพื่อย้อน provenance และ rerun normalization", contract: "vendor JSON → financial.raw_payloads", points: ["payload_sha256 ป้องกัน duplicate", "ผูก run_id/ticker/endpoint/frequency", "commit company/run ก่อน FK payload"], files: [FILE("src/semigraph/financial/repository.py", "upsert_raw_payload"), FILE("src/semigraph/financial/finnhub_client.py", "payload_sha256")], note: "raw ledger แยกสิ่งที่ vendor ส่งจริงออกจากค่าที่ระบบ normalize/derive" },
  { id: "f_normalize", x: 750, y: 440, w: 190, h: 108, layer: "offline", kicker: "CURATE / 04", title: "Canonical facts", subtitle: "reported metrics", chip: "aliases → registry", description: "เลือก report ล่าสุดต่อ period และ map vendor concepts เป็น metric registry กลาง", contract: "reported data → CanonicalFact[]", points: ["annual + quarterly", "เก็บ source_concept/accession", "ใช้ Decimal สำหรับ numerical precision"], files: [FILE("src/semigraph/financial/normalize.py", "select_latest_reports / normalize_report"), FILE("src/semigraph/financial/metrics.py", "MetricDefinition / ALIAS_TO_METRIC"), FILE("src/semigraph/financial/models.py", "CanonicalFact")], note: "metric registry ใน config เป็น capability boundary ร่วมของ ETL, query spec และ Planner" },
  { id: "f_derive", x: 990, y: 440, w: 190, h: 108, layer: "guard", kicker: "DERIVE / 05", title: "Derived metrics", subtitle: "deterministic formulas", chip: "provenance kept", description: "คำนวณ margin, growth, FCF, ratios, ROA/ROE จาก canonical facts ด้วยสูตรที่กำหนดในโค้ด", contract: "FactValue inputs → DerivedMetric", points: ["ไม่มี LLM คำนวณเลข", "safe ratio และ missing status", "เก็บ input_fact_ids + formula_version"], files: [FILE("src/semigraph/financial/derive.py", "derive_annual_metrics"), FILE("src/semigraph/financial/models.py", "DerivedMetric")], note: "การ derive แบบ deterministic ทำให้ตรวจสูตรและ reproduce ตัวเลขได้" },
  { id: "f_pg", x: 1230, y: 440, w: 205, h: 108, layer: "data", kicker: "READY STORE / 06", title: "PostgreSQL financial", subtitle: "facts · metrics · snapshots", chip: "curated views", description: "เก็บ raw, canonical, derived, vendor metrics และ market snapshots พร้อม agent-facing read views", contract: "agent_periodic_metrics + agent_market_metrics", points: ["transaction ต่อ ticker", "read-only connection สำหรับ Agent", "ทุก row มี evidence_id/provenance"], files: [FILE("src/semigraph/financial/db.py", "financial_connection"), FILE("src/semigraph/financial/etl.py", "run_financial_etl"), FILE("src/semigraph/financial/query_repository.py", "query_periodic_metrics / query_market_metrics")], note: "PostgreSQL เป็น numerical truth plane ที่แยกจาก narrative KG โดยตั้งใจ" },
  { id: "f_spec", x: 1510, y: 440, w: 205, h: 108, layer: "guard", kicker: "RUNTIME / 07", title: "Typed query gate", subtitle: "intent → safe SQL", chip: "no LLM SQL", description: "ตอน query LLM ระบุ intent fields, Pydantic validate combination แล้ว compiler เลือก allowlisted SQL template", contract: "query → FinancialQuerySpec → CompiledFinancialQuery", points: ["operations 5 แบบ", "period/snapshot rules", "bound parameters แยกจาก SQL text"], files: [FILE("src/semigraph/online/financial_search.py", "_build_financial_query_spec"), FILE("src/semigraph/financial/query_spec.py", "FinancialQuerySpec"), FILE("src/semigraph/financial/sql_compiler.py", "compile_financial_query")], note: "นี่คือ security/reproducibility boundary: LLM เลือกความหมาย แต่ไม่ได้สร้างคำสั่งฐานข้อมูล" },
  { id: "f_fin_chunks", x: 1760, y: 440, w: 195, h: 108, layer: "shared", kicker: "RUNTIME / 08", title: "Financial evidence", subtitle: "typed chunks", chip: "value + provenance", description: "แปลง query rows เป็น common chunk contract พร้อม field ตัวเลขที่ synthesis จัดรูปแบบได้โดยไม่เสีย precision", contract: "PostgreSQL rows → financial chunk[]", points: ["metric/value/unit/frequency", "period_end/observed_at", "provenance สำหรับ citation/eval"], files: [FILE("src/semigraph/financial/backend.py", "row_to_financial_chunk / PostgreSQLBackend"), FILE("src/semigraph/agent/nodes.py", "_financial_chunk_lines")], note: "text field ช่วย LLM อ่าน ส่วน structured fields ช่วย evaluator/UI ไม่ต้อง parse ข้อความกลับ" },
  { id: "f_config", x: 2020, y: 440, w: 210, h: 108, layer: "shared", kicker: "CROSS-CUTTING", title: "Config + connections", subtitle: "YAML params · env secrets", chip: "cached factories", description: "รวม parameter, path, secrets และ factory ของ Neo4j/LLM/embedding โดยห้าม module อ่าน env ตรง", contract: "default.yaml + .env → Config singleton", points: ["lru_cache get_config", "OpenRouter ChatOpenAI", "Neo4j high/low-level factories"], files: [FILE("src/semigraph/config.py", "Config / get_config"), FILE("src/semigraph/connections.py", "get_neo4j / get_neo4j_driver / get_llm")], note: "cross-cutting configuration ทำให้ production profile และ evaluation override แยกจาก algorithm code" },
  { id: "f_benchmark", x: 2270, y: 440, w: 190, h: 108, layer: "shared", kicker: "EVALUATION", title: "FinReflectKG adapter", subtitle: "gold path conventions", chip: "benchmark only", description: "normalize external benchmark entity/relation aliases, hop evidence, ticker scope และ chunk IDs เพื่อวัด retrieval reproducibly", contract: "FinReflectKG records → canonical benchmark questions", points: ["conservative alias matching", "reference type normalization", "strict ticker question filter"], files: [FILE("src/semigraph/benchmark/finreflectkg.py", "convert_question / gold_entity_aliases")], note: "ไม่ได้อยู่ runtime answer path แต่เป็นส่วนของ evaluation surface ใน src" },
];

const factoryEdges = [
  { id: "sec-raw", from: "f_sec", to: "f_raw", label: "download" },
  { id: "raw-pre", from: "f_raw", to: "f_pre", label: "stream documents" },
  { id: "pre-sections", from: "f_pre", to: "f_sections", label: "clean sections" },
  { id: "sections-chunk", from: "f_sections", to: "f_chunk", label: "Item 1/1A/7" },
  { id: "chunk-extract", from: "f_chunk", to: "f_extract", label: "parallel chunks" },
  { id: "extract-validate", from: "f_extract", to: "f_validate", label: "raw JSON" },
  { id: "validate-store", from: "f_validate", to: "f_store", label: "valid graph" },
  { id: "store-repair", from: "f_store", to: "f_repair", label: "per filing" },
  { id: "repair-features", from: "f_repair", to: "f_features", label: "quality graph" },
  { id: "features-neo", from: "f_features", to: "f_neo", label: "retrieval ready" },
  { id: "universe-finn", from: "f_universe", to: "f_finnhub", label: "targets" },
  { id: "finn-payload", from: "f_finnhub", to: "f_payload", label: "4 payloads" },
  { id: "payload-normalize", from: "f_payload", to: "f_normalize", label: "reported data" },
  { id: "normalize-derive", from: "f_normalize", to: "f_derive", label: "fact inputs" },
  { id: "derive-pg", from: "f_derive", to: "f_pg", label: "upsert metrics" },
  { id: "pg-spec", from: "f_pg", to: "f_spec", label: "read-only views", data: true },
  { id: "spec-chunks", from: "f_spec", to: "f_fin_chunks", label: "bound SQL" },
  { id: "config-factory", from: "f_config", to: "f_features", label: "models + params", optional: true, curve: "top" },
  { id: "config-spec", from: "f_config", to: "f_spec", label: "metric registry", optional: true, curve: "bottom" },
  { id: "neo-universe", from: "f_neo", to: "f_universe", label: "ticker truth", data: true, curve: "bottom" },
  { id: "neo-bench", from: "f_neo", to: "f_benchmark", label: "retrieval corpus", optional: true, curve: "bottom" },
];

const DEMO_QUERY = "Compare AMD supply-chain exposure, FY2025 margin, and recent risk news.";

const DEMO_TASKS = [
  {
    task_id: "T1", query: "Trace AMD → TSMC capacity exposure",
    requirements: [{ requirement_id: "T1-R1", description: "AMD–TSMC capacity evidence" }],
    initial_action: { tool: "graph", query: "Trace AMD → TSMC capacity exposure", top_k_chunks: 5 },
  },
  {
    task_id: "T2", query: "Find AMD FY2025 gross margin",
    requirements: [{ requirement_id: "T2-R1", description: "AMD FY2025 gross margin" }],
    initial_action: { tool: "financial", query: "Find AMD FY2025 gross margin", top_k_chunks: 5 },
  },
  {
    task_id: "T3", query: "Find recent AMD supply risk news",
    requirements: [{ requirement_id: "T3-R1", description: "Recent AMD supply risk" }],
    initial_action: { tool: "news", query: "Find recent AMD supply risk news", top_k_chunks: 5 },
  },
];

const DEMO_ATTEMPTS = {
  T1: [
    {
      attempt_id: "T1-A1", task_id: "T1",
      action: { tool: "graph", query: "Trace AMD → TSMC capacity exposure", top_k_chunks: 5 },
      retrieval_status: "ok", chunks: [{ chunk_id: "G-101", text: "AMD relies on third-party foundries…" }],
      retrieval_trace: { status: "ok", seeds: 4 },
      assessment: { status: "valid", output: { accepted_chunk_ids: ["G-101"], decision: "retry", retry_strategy: "bridge_hint" } },
    },
    {
      attempt_id: "T1-A2", task_id: "T1",
      action: { tool: "graph", query: "AMD TSMC wafer capacity bridge", top_k_chunks: 5 },
      retrieval_status: "ok", chunks: [{ chunk_id: "G-205", text: "TSMC provides advanced-node wafer capacity…" }],
      retrieval_trace: { status: "ok", seeds: 6 },
      assessment: { status: "valid", output: { accepted_chunk_ids: ["G-205"], covered_requirement_ids: ["T1-R1"], decision: "accept" } },
    },
  ],
  T2: [{
    attempt_id: "T2-A1", task_id: "T2",
    action: { tool: "financial", query: "Find AMD FY2025 gross margin", top_k_chunks: 5 },
    retrieval_status: "ok", chunks: [{ chunk_id: "F-301", text: "AMD gross margin FY2025: 53%" }],
    retrieval_trace: { status: "ok", row_count: 1 },
    assessment: { status: "valid", output: { accepted_chunk_ids: ["F-301"], covered_requirement_ids: ["T2-R1"], decision: "accept" } },
  }],
  T3: [{
    attempt_id: "T3-A1", task_id: "T3",
    action: { tool: "news", query: "Find recent AMD supply risk news", top_k_chunks: 5 },
    retrieval_status: "ok", chunks: [{ chunk_id: "N-401", text: "Recent supply-chain risk update…" }],
    retrieval_trace: { status: "ok", returned_chunk_ids: ["N-401"] },
    assessment: { status: "valid", output: { accepted_chunk_ids: ["N-401"], covered_requirement_ids: ["T3-R1"], decision: "accept" } },
  }],
};

const DEMO_COMPLETIONS = ["T1", "T2", "T3"].map(taskId => ({
  task_id: taskId, sufficient: true, stop_reason: "sufficient",
}));

const taskResult = (taskId, index) => ({
  task_id: taskId,
  attempts: DEMO_ATTEMPTS[taskId],
  completion: DEMO_COMPLETIONS[index],
});

const runtimeStateSnapshots = {
  query: {
    scope: "Parent AgentState · graph input",
    fields: { original_query: DEMO_QUERY },
  },
  plan: {
    scope: "Parent AgentState · after PlanRoute",
    fields: {
      original_query: DEMO_QUERY,
      tasks: DEMO_TASKS,
      plan_trace: { status: "ok", llm_calls: 1, warnings: [] },
    },
  },
  dispatch: {
    scope: "Dispatcher return · LangGraph control output, not AgentState",
    fields: {
      send_commands: DEMO_TASKS.map(task => ({
        node: "task_worker",
        arg: { original_query: DEMO_QUERY, task },
      })),
    },
  },
  workerT1: {
    scope: "Worker T1 · isolated local AgentState",
    fields: {
      original_query: DEMO_QUERY, tasks: [DEMO_TASKS[0]], current_task_index: 0,
      current_action: {}, attempts: DEMO_ATTEMPTS.T1,
      completed_tasks: [DEMO_COMPLETIONS[0]], stop_reason: "sufficient",
    },
  },
  workerT2: {
    scope: "Worker T2 · isolated local AgentState",
    fields: {
      original_query: DEMO_QUERY, tasks: [DEMO_TASKS[1]], current_task_index: 0,
      current_action: {}, attempts: DEMO_ATTEMPTS.T2,
      completed_tasks: [DEMO_COMPLETIONS[1]], stop_reason: "sufficient",
    },
  },
  workerT3: {
    scope: "Worker T3 · isolated local AgentState",
    fields: {
      original_query: DEMO_QUERY, tasks: [DEMO_TASKS[2]], current_task_index: 0,
      current_action: {}, attempts: DEMO_ATTEMPTS.T3,
      completed_tasks: [DEMO_COMPLETIONS[2]], stop_reason: "sufficient",
    },
  },
  reduced: {
    scope: "Parent AgentState · after task_results reducer",
    fields: {
      original_query: DEMO_QUERY, tasks: DEMO_TASKS,
      task_results: [taskResult("T2", 1), taskResult("T1", 0), taskResult("T3", 2)],
    },
  },
  collected: {
    scope: "Parent AgentState · after Collector restores Plan order",
    fields: {
      original_query: DEMO_QUERY, tasks: DEMO_TASKS,
      attempts: [...DEMO_ATTEMPTS.T1, ...DEMO_ATTEMPTS.T2, ...DEMO_ATTEMPTS.T3],
      completed_tasks: DEMO_COMPLETIONS, current_action: {}, stop_reason: "sufficient",
    },
  },
  synthesized: {
    scope: "Parent AgentState · final output",
    fields: {
      original_query: DEMO_QUERY,
      attempts: [...DEMO_ATTEMPTS.T1, ...DEMO_ATTEMPTS.T2, ...DEMO_ATTEMPTS.T3],
      completed_tasks: DEMO_COMPLETIONS,
      final_answer: "AMD's exposure, FY2025 margin, and recent risk are supported by [1]–[3].",
      citation_map: [
        { citation_index: 1, chunk_id: "G-205" },
        { citation_index: 2, chunk_id: "F-301" },
        { citation_index: 3, chunk_id: "N-401" },
      ],
      synthesis_trace: { status: "ok", llm_calls: 1, selected_chunk_ids_by_task: { T1: ["G-205"], T2: ["F-301"], T3: ["N-401"] } },
    },
  },
};

const VIEWS = {
  runtime: {
    title: "AgentState: Plan → Send fan-out → isolated Task workers → reducer → Collector → one Synthesis",
    width: 2020, height: 720, nodes: runtimeNodes, edges: runtimeEdges,
    scenarios: {
      parallelTasks: {
        label: "Parallel Tasks · State walkthrough",
        steps: [
          ["query", null, "รับ Original Query", "Parent State เริ่มจาก original_query เพียง field เดียว", "query"],
          ["plan", "q-plan", "PlanRoute สร้างสาม Tasks", "T1=Graph, T2=Financial และ T3=News; แต่ละ Task มี initial_action ของตัวเอง", "plan"],
          ["dispatcher", "plan-dispatch", "Dispatcher อ่าน tasks", "Node นี้ไม่แก้ State แต่เตรียม Send control instructions ให้ LangGraph", "dispatch"],
          [["worker_t1", "worker_t2", "worker_t3"], ["send-t1", "send-t2", "send-t3"], "Fan-out พร้อมกัน", "LangGraph เรียก task_worker สาม instance ด้วย payload คนละ Task", "dispatch"],
          ["worker_t1", "send-t1", "T1 ทำ Graph และ Retry ภายใน", "A1 ได้ partial evidence แล้ว A2 ใช้ bridge_hint ก่อนปิด sufficient", "workerT1"],
          ["worker_t2", "send-t2", "T2 ทำ Financial แยกจาก T1", "Local State มี tasks=[T2] และ Ledger ของ T2 เท่านั้น", "workerT2"],
          ["worker_t3", "send-t3", "T3 ทำ News แยกจาก Task อื่น", "Worker ทุกตัวคืน TaskResult หนึ่งก้อน ไม่เขียน Attempts กลาง", "workerT3"],
          ["reducer", ["t1-reducer", "t2-reducer", "t3-reducer"], "Reducer รวม TaskResult", "ตัวอย่างจงใจให้ T2 เสร็จก่อน T1 เพื่อแสดงว่า task_results อาจไม่เรียงตาม Plan", "reduced"],
          ["collector", "reducer-collector", "Collector คืนลำดับ T1 → T2 → T3", "Flatten Attempts และ completion ตาม Plan order แล้ว clear current_action", "collected"],
          ["ledger", "collector-ledger", "Parent Attempt Ledger พร้อมใช้", "Evaluator และ Synthesis เห็น Attempt ครบทุก Task โดยไม่มี concurrent write", "collected"],
          ["synthesize", ["collector-synth", "ledger-synth"], "Synthesis เรียกครั้งเดียว", "เลือก accepted evidence ก่อน เติม raw fallback และจำกัดรวมไม่เกิน 9 chunks", "synthesized"],
          ["answer", "synth-answer", "คืน Final AgentState", "คำตอบ, citation map และ synthesis trace อยู่ร่วมกับ Ledger ที่ตรวจย้อนหลังได้", "synthesized"],
        ],
      },
    },
  },
  interfaces: {
    title: "Interface literacy: อ่าน input/output และ Contract ของแต่ละ boundary",
    width: 2140, height: 680, nodes: interfaceNodes, edges: interfaceEdges,
    scenarios: {
      contractFlow: {
        label: "Contract flow · เริ่มจาก Query จนถึง Answer",
        steps: [
          ["i_query", null, "1. เริ่มจาก Original Query", "นี่คือความต้องการต้นฉบับที่ทุก Node ต้องรักษาความหมายไว้"],
          ["i_plan", "iq-plan", "2. อ่าน PlanRouteOutput", "ตรวจว่า Task แยกเป็น evidence need และ Graph chain ยังอยู่ Task เดียวหรือไม่"],
          ["i_action", "iplan-action", "3. อ่าน RetrievalAction", "ก่อน debug Retriever ให้ตรวจ tool, query และ top_k ที่ Worker ได้รับก่อน"],
          ["i_attempt", "ia-attempt", "4. อ่าน AttemptRecord", "หนึ่ง record = หนึ่ง Tool call; รอบ Retry ต้อง append record ใหม่"],
          ["i_assess", "iattempt-assess", "5. อ่าน AssessmentOutput", "Assessment ตัดสินจาก chunks ที่มีจริง ไม่สร้าง chunk ID ใหม่"],
          ["i_action", "iassess-retry", "6. ถ้า Retry ให้ดู next_action", "ตรวจ strategy และ query ว่าแก้ evidence gap จริง ไม่ใช่ repeat เดิม"],
          ["i_result", "iassess-result", "7. Worker คืน TaskResult", "completion เก็บเฉพาะสถานะจบ ไม่ copy evidence ซ้ำ"],
          ["i_state", "iresult-state", "8. Collector รวมเป็น AgentState", "task_results อาจมาถึงไม่เรียงเวลา แต่ Collector คืนลำดับตาม Plan"],
          ["i_output", "istate-output", "9. Synthesis คืน Public Output", "Final answer อ้างเฉพาะ selected chunks และมี trace ให้ตรวจย้อนหลัง"],
        ],
      },
      debugOrder: {
        label: "Debug order · ไล่ Bug จาก Interface ด้านนอกเข้าไป",
        steps: [
          ["i_output", null, "เริ่มดู Output ที่ผิด", "แยกว่า Answer ผิดเพราะ citation, evidence selection หรือ retrieval"],
          ["i_state", "istate-output", "ตรวจ Parent AgentState", "ดู attempts, completed_tasks และ synthesis_trace ที่ Collector เตรียมให้"],
          ["i_result", "iresult-state", "ตรวจ TaskResult", "ดูว่า Task ใดจบด้วย sufficient, no_evidence_gain หรือ tool_error"],
          ["i_assess", "iassess-result", "ตรวจ AssessmentOutput", "ดู decision, accepted IDs และ covered requirement IDs"],
          ["i_attempt", "iattempt-assess", "ตรวจ AttemptRecord", "ดู raw chunks, retrieval_status และ retrieval_trace ของรอบล่าสุด"],
          ["i_action", "ia-attempt", "ตรวจ RetrievalAction", "ถ้า query/tool ผิด ให้แก้ที่ Planner หรือ retry policy ก่อนแก้ Retriever"],
          ["i_plan", "iplan-action", "ตรวจ PlanRouteOutput", "ย้อนดู requirement และ initial_action ว่ากำหนด evidence need ถูกหรือไม่"],
          ["i_query", "iq-plan", "สุดท้ายตรวจ Original Query", "ห้ามแก้ต้นเหตุด้วยการเปลี่ยนความหมายของคำถาม"],
        ],
      },
    },
  },
  graph: {
    title: "เจาะ Graph Search: query embedding → triple recognition → Entity–Chunk PPR",
    width: 2350, height: 720, nodes: graphNodes, edges: graphEdges,
    scenarios: {
      production: {
        label: "Production Phase-T profile",
        steps: [
          ["g_query", null, "รับ relational query", "ใช้ query จาก Graph task โดย production profile ไม่ขยายคำ"],
          ["g_embed", "gq-embed", "ฝัง query", "BGE สร้างเวกเตอร์ 768 มิติใน space เดียวกับ triple index"],
          ["g_triple_index", "embed-index", "เทียบกับ triple ทั้ง graph", "โหลด matrix ที่ cache ไว้แล้วคำนวณ cosine similarity"],
          ["g_candidates", "index-candidates", "เลือก top 10 candidates", "ตัดต่ำกว่า 0.6 และ deduplicate"],
          ["g_filter", "candidates-filter", "LLM recognition filter", "เลือก candidate IDs ที่สัมพันธ์จริง; fallback ถ้า output ใช้ไม่ได้"],
          ["g_seeds", "filter-seeds", "เปลี่ยน triple เป็น seeds", "รวม head/tail ที่เลือกและใช้ uniform weights"],
          ["g_projection", null, "เตรียม GDS projection", "reuse semigraph_ppr_entity_chunk ถ้ามีอยู่แล้ว"],
          ["g_ppr", "seeds-ppr", "รัน Personalized PageRank", "กระจายมวลจาก sourceNodes ด้วย damping 0.5"],
          ["g_chunks", "ppr-chunks", "อ่าน top passage nodes", "ดึง text และ metadata ของ Chunk ที่คะแนนสูง"],
          ["g_rerank", "chunks-rerank", "ใช้ลำดับ PPR", "production ปิด external reranker จึงตัด top-k โดยตรง"],
          ["g_output", "rerank-output", "คืน evidence + trace", "Agent adapter compact รายละเอียดโดยไม่ทิ้ง lineage"],
        ],
      },
      expanded: {
        label: "Optional query expansion path",
        steps: [
          ["g_query", null, "รับ query ที่อ้าง entity โดยนัย", "เช่น ‘maker of EPYC’ โดยไม่ระบุ AMD"],
          ["g_expand", "gq-expand", "เติม entity hints", "LLM เติม AMD/EPYC และ fail-open เป็น query เดิมเมื่อผิด"],
          ["g_embed", "expand-embed", "ฝัง effective query", "original query ยังอยู่ด้านหน้า hints"],
          ["g_triple_index", "embed-index", "ค้น triple semantic", "entity hints เพิ่มโอกาสเจอ relation ที่ตรง"],
          ["g_candidates", "index-candidates", "สร้าง candidate set", "candidate IDs จำกัดสิ่งที่ filter เลือกได้"],
          ["g_filter", "candidates-filter", "คัด false positives", "LLM ทำ recognition ไม่ได้สร้าง fact"],
          ["g_seeds", "filter-seeds", "สร้าง seeds", "endpoint ของ triple เป็นจุดเริ่ม PPR"],
          ["g_ppr", "seeds-ppr", "เดิน Entity–Chunk graph", "เชื่อม relational evidence หลายทอด"],
          ["g_chunks", "ppr-chunks", "คืน passage", "ข้อความ SEC พร้อม PPR score"],
          ["g_output", "rerank-output", "ส่งเข้า Agent", "contract เหมือนเดิมไม่ว่า expansion เปิดหรือปิด"],
        ],
      },
    },
  },
  factory: {
    title: "สอง data planes: SEC narrative → Neo4j และ Finnhub numerics → PostgreSQL",
    width: 2500, height: 690, nodes: factoryNodes, edges: factoryEdges,
    scenarios: {
      narrative: {
        label: "SEC → Neo4j retrieval store",
        steps: [
          ["f_sec", null, "ดาวน์โหลด filing", "ingest รับ ticker/type จาก config แล้วเก็บ submission ต้นฉบับ"],
          ["f_raw", "sec-raw", "รักษา raw source", "ต้นฉบับทำให้แปลงใหม่ได้โดยไม่เสีย lineage"],
          ["f_pre", "raw-pre", "ทำความสะอาดและหา section", "stream เฉพาะ filing document, แปลง Markdown และตัด TOC"],
          ["f_sections", "pre-sections", "เก็บ Item 1 / 1A / 7", "narrative-rich sections พร้อมเข้า KG"],
          ["f_chunk", "sections-chunk", "ตัดข้อความ", "4500 chars, overlap 600 พร้อม deterministic chunk_id"],
          ["f_extract", "chunk-extract", "สกัด graph ต่อ chunk", "DeepSeek call เดียวคืน node + relationship"],
          ["f_validate", "extract-validate", "กัน output ผิด ontology", "normalize, Pydantic, type constraints และ semantic guards"],
          ["f_store", "validate-store", "MERGE พร้อม provenance", "เขียน transaction ต่อ chunk"],
          ["f_repair", "store-repair", "ซ่อม graph จาก evidence", "เติม relationship ที่รองรับและ prune mention-only nodes"],
          ["f_features", "repair-features", "สร้าง retrieval features", "ฝัง chunk/entity/triple และสร้าง synonym/specificity"],
          ["f_neo", "features-neo", "พร้อมค้นออนไลน์", "Graph Search และ Vector Search อ่าน corpus เดียวกัน"],
        ],
      },
      financial: {
        label: "Finnhub → PostgreSQL truth plane",
        steps: [
          ["f_universe", null, "ตรวจ universe", "เทียบ Neo4j tickers กับ config ก่อนดึงตัวเลข"],
          ["f_finnhub", "universe-finn", "ดึง 4 endpoint", "annual, quarterly, basic financials และ quote"],
          ["f_payload", "finn-payload", "เก็บ raw lineage", "hash payload และผูก ETL run"],
          ["f_normalize", "payload-normalize", "สร้าง canonical facts", "map source concept ไป metric registry"],
          ["f_derive", "normalize-derive", "คำนวณ deterministic metrics", "สูตรคำนวณเก็บ input fact IDs"],
          ["f_pg", "derive-pg", "commit PostgreSQL", "curated views แยก periodic กับ market snapshot"],
          ["f_spec", "pg-spec", "runtime typed query", "LLM intent ผ่าน validation และ allowlisted compiler"],
          ["f_fin_chunks", "spec-chunks", "คืน evidence ที่ cite ได้", "value/unit/period/provenance อยู่คู่ text"],
        ],
      },
    },
  },
};

const MODULE_GROUPS = [
  {
    id: "root", label: "Foundation", color: "#ff8e9e",
    modules: [
      ["src/semigraph/__init__.py", 4, "Package identity ของ SemiGraph", "package metadata"],
      ["src/semigraph/config.py", 262, "โหลด YAML parameters, resolve env secrets และ expose cached Config properties", "Config · get_config"],
      ["src/semigraph/connections.py", 46, "Factory กลางของ Neo4jGraph, raw Neo4j driver และ ChatOpenAI", "get_neo4j · get_neo4j_driver · get_llm"],
      ["src/semigraph/main.py", 5, "Minimal package entry placeholder", "main"],
    ],
  },
  {
    id: "agent", label: "Agent harness", color: "#64e0d4",
    modules: [
      ["src/semigraph/agent/__init__.py", 0, "Agent package marker", "—"],
      ["src/semigraph/agent/contracts.py", 155, "Strict Pydantic/TypedDict contracts ของ plan, action, assessment และ attempt", "PlanRouteOutput · RetrievalAction · AssessmentOutput · AttemptRecord"],
      ["src/semigraph/agent/graph.py", 197, "ประกอบ Plan, Send fan-out, isolated Task workers, deterministic Collector และ Synthesis", "build_agent · _dispatch_tasks · _collect_task_results"],
      ["src/semigraph/agent/ledger.py", 49, "Read-only views จาก Attempt Ledger สำหรับ chunks, tool calls และ traces", "retrieved_chunks · tool_calls · retrieval_traces"],
      ["src/semigraph/agent/nodes.py", 1226, "Logic ของ PlanRoute, Execute, Assess, task advance และ grounded synthesis", "plan_route_node · execute_attempt_node · assess_node · synthesize_attempts_node"],
      ["src/semigraph/agent/prompts.py", 192, "Prompt contracts ของ Planner, Assessor และ Synthesis ที่ผูก metric/retry registry", "PLAN_ROUTE_SYSTEM_PROMPT · ASSESS_SYSTEM_PROMPT"],
      ["src/semigraph/agent/retry_policy.py", 241, "Deterministic guard สำหรับ assessment context, evidence gain และ retry budget", "validate_assessment_context · decide_retry"],
      ["src/semigraph/agent/state.py", 29, "Serializable shared state พร้อม reducer สำหรับ parallel Task results", "TaskResult · AgentState"],
      ["src/semigraph/agent/tools.py", 337, "Agent adapters, compact traces, retriever registry และ tool schemas", "agent_graph_search · agent_vector_search · agent_financial_search · RETRIEVERS"],
      ["src/semigraph/agent/ws.py", 6, "LangGraph dev workspace entrypoint", "graph = build_agent()"],
    ],
  },
  {
    id: "online", label: "Online retrieval", color: "#ffb95c",
    modules: [
      ["src/semigraph/online/__init__.py", 0, "Online retrieval package marker", "—"],
      ["src/semigraph/online/_ticker.py", 95, "Regex-first ticker resolution พร้อม LLM expansion fallback และ out-of-corpus guard", "extract_tickers · resolve_tickers"],
      ["src/semigraph/online/financial_search.py", 650, "Natural-language financial intent → validated spec → configured backend", "financial_search · _build_financial_query_spec · FinnhubAPIBackend"],
      ["src/semigraph/online/graph_search.py", 1044, "Orchestrate graph seeds, PPR, legacy alias mapping, candidate rerank และ trace", "trace_graph_search · graph_search · MetadataRerankParams"],
      ["src/semigraph/online/hybrid_search.py", 164, "Fuse Vector และ Graph rankings ด้วย Reciprocal Rank Fusion", "hybrid_search"],
      ["src/semigraph/online/news_search.py", 365, "Finnhub company-news retriever, intent guards, recency ranking และ optional cache/full text", "news_search · FinnhubNewsBackend"],
      ["src/semigraph/online/ppr.py", 691, "จัดการ GDS projections และ Personalized PageRank แบบ entity-only/entity-chunk", "ensure_projection · run_passage_ppr · run_ppr"],
      ["src/semigraph/online/query_expand.py", 105, "LLM entity-hint expansion แบบรักษา original query และ fail-open", "expand_query"],
      ["src/semigraph/online/rerank.py", 117, "OpenRouter reranker client พร้อม retry และ original-order fallback", "rerank_chunks"],
      ["src/semigraph/online/seed.py", 325, "สร้าง node/triple/hybrid semantic seeds จาก BGE และ Neo4j indexes", "query_to_seeds · query_to_triple_candidates · query_to_hybrid_seeds"],
      ["src/semigraph/online/triple_filter.py", 206, "LLM recognition filter ที่เลือกได้เฉพาะ triple candidate IDs", "filter_triple_candidates"],
      ["src/semigraph/online/vector_search.py", 162, "Vanilla Neo4j chunk-vector retrieval และ optional rerank trace", "trace_vector_search · vector_search"],
    ],
  },
  {
    id: "financial", label: "Financial truth plane", color: "#b5a0ff",
    modules: [
      ["src/semigraph/financial/__init__.py", 0, "Financial package marker", "—"],
      ["src/semigraph/financial/backend.py", 149, "Read-only PostgreSQL backend และ row-to-chunk adapter", "FinancialBackend · PostgreSQLBackend · row_to_financial_chunk"],
      ["src/semigraph/financial/db.py", 32, "Context-managed psycopg connection พร้อม readonly transaction mode", "financial_connection"],
      ["src/semigraph/financial/derive.py", 557, "สูตร derived metrics แบบ deterministic และรักษา provenance/missing status", "safe_ratio · derive_fcf · derive_annual_metrics"],
      ["src/semigraph/financial/etl.py", 843, "Orchestrate financial staging, normalize, derive, persist และ isolate failure ต่อ ticker", "run_financial_etl · FinancialETLSummary"],
      ["src/semigraph/financial/finnhub_client.py", 212, "Testable Finnhub adapter พร้อม retry, throttle และ payload hashing", "FinnhubStagingClient · payload_sha256"],
      ["src/semigraph/financial/metrics.py", 112, "Metric definitions และ vendor-concept alias registry", "MetricDefinition · ALIAS_TO_METRIC"],
      ["src/semigraph/financial/models.py", 44, "Pydantic models ของ canonical facts และ derived metrics", "CanonicalFact · DerivedMetric"],
      ["src/semigraph/financial/normalize.py", 100, "เลือก latest reports และ map vendor report fields เป็น canonical facts", "select_latest_reports · normalize_report"],
      ["src/semigraph/financial/query_repository.py", 154, "Small read repository บน curated PostgreSQL views", "query_periodic_metrics · query_market_metrics"],
      ["src/semigraph/financial/query_spec.py", 181, "Validated contract ของ ticker/metric/frequency/operation/period", "FinancialQuerySpec · Frequency · Operation"],
      ["src/semigraph/financial/repository.py", 119, "Persistence helper ของ raw Finnhub payloads และ dimensions", "upsert_raw_payload"],
      ["src/semigraph/financial/sql_compiler.py", 341, "เลือก allowlisted SQL template และ bound parameters จาก validated spec", "CompiledFinancialQuery · compile_financial_query"],
    ],
  },
  {
    id: "offline", label: "Offline narrative factory", color: "#7cb8ff",
    modules: [
      ["src/semigraph/offline/__init__.py", 0, "Offline package marker", "—"],
      ["src/semigraph/offline/chunker.py", 228, "Chunk model และ recursive split ราย section/filing/corpus", "Chunk · chunk_section · chunk_filing"],
      ["src/semigraph/offline/embed_chunks.py", 130, "ฝัง Chunk nodes และสร้าง chunk_embedding vector index", "embed_chunks · ensure_chunk_vector_index"],
      ["src/semigraph/offline/embed_nodes.py", 142, "ฝัง Entity nodes และสร้าง entity_embedding vector index", "embed_entities · ensure_entity_vector_index"],
      ["src/semigraph/offline/embed_triples.py", 146, "สร้าง humanized relationship text แล้วเก็บ triple_embedding", "embed_triples"],
      ["src/semigraph/offline/embeddings.py", 62, "Cached SentenceTransformer wrapper สำหรับ BGE", "EmbeddingModel · get_embedding_model"],
      ["src/semigraph/offline/graph_repair.py", 935, "Evidence-grounded graph repair, relation validation และ unresolved-node pruning", "repair_filing_graph · repair_current_graph · GraphRepairStats"],
      ["src/semigraph/offline/ingest.py", 168, "SEC download, batch ingest, RSS check และ raw filing discovery", "download_filings · check_rss_feed · get_filing_paths"],
      ["src/semigraph/offline/kg_extract.py", 403, "Single-call LLM KG extraction พร้อม JSON/Pydantic/ontology/semantic validation", "extract_chunk"],
      ["src/semigraph/offline/kg_store.py", 404, "Idempotent Neo4j persistence ของ provenance hierarchy, mentions และ domain edges", "KGStore · init_schema · store_chunks"],
      ["src/semigraph/offline/pipeline.py", 357, "Threaded chunk→extract→store orchestrator พร้อม filing checkpoint/error isolation/repair", "process_filing · process_corpus · Checkpoint"],
      ["src/semigraph/offline/preprocess.py", 378, "Stream SEC documents, clean HTML/Markdown และ extract 10-K sections", "clean_and_save_documents · extract_sections_10k"],
      ["src/semigraph/offline/specificity.py", 87, "คำนวณ Node Specificity จาก informative graph degree", "compute_specificity"],
      ["src/semigraph/offline/synonymy.py", 437, "สร้าง validated SYNONYM_OF edges ด้วย string/alias/cosine composite rules", "build_synonymy"],
    ],
  },
  {
    id: "ontology", label: "Ontology", color: "#8ddf8a",
    modules: [
      ["src/semigraph/ontology/__init__.py", 21, "Public ontology API exports", "GraphNode · GraphRelationship · OntologyRegistry"],
      ["src/semigraph/ontology/nodes.py", 48, "Pydantic graph extraction models และ automatic name property", "GraphNode · GraphRelationship · GraphExtractionResult"],
      ["src/semigraph/ontology/normalization.py", 144, "Deterministic entity normalization และ product-name guard", "normalize_entity_name · is_known_product_name"],
      ["src/semigraph/ontology/schema.py", 582, "Single source of truth ของ 24 node types, 29 relations และ section-specific prompt", "NODE_CATALOG · RELATIONSHIP_CATALOG · SECTION_CONFIG · OntologyRegistry"],
    ],
  },
  {
    id: "benchmark", label: "Benchmark adapters", color: "#ff8e9e",
    modules: [
      ["src/semigraph/benchmark/__init__.py", 2, "Benchmark adapter package marker", "—"],
      ["src/semigraph/benchmark/finreflectkg.py", 347, "Canonicalize FinReflectKG entities, relations, gold hops, aliases และ ticker subsets", "convert_question · gold_entity_aliases · strict_ticker_questions"],
    ],
  },
];

const state = {
  view: "runtime",
  scenario: "parallelTasks",
  step: -1,
  playing: false,
  playTimer: null,
  zoom: 1,
  panX: 0,
  panY: 0,
  dragging: false,
  dragStart: null,
  selectedNode: null,
  enabledLayers: new Set(Object.keys(LAYERS)),
  lens: "full-system",
};

const els = {
  svg: document.getElementById("architecture-svg"),
  viewport: document.getElementById("viewport"),
  edgeLayer: document.getElementById("edge-layer"),
  nodeLayer: document.getElementById("node-layer"),
  diagramStage: document.getElementById("diagram-stage"),
  sourceStage: document.getElementById("source-stage"),
  sourceGroups: document.getElementById("source-groups"),
  sourceSearch: document.getElementById("source-search"),
  sourceSearchControl: document.getElementById("source-search-control"),
  sourceResultCount: document.getElementById("source-result-count"),
  scenarioControl: document.getElementById("scenario-control"),
  scenarioSelect: document.getElementById("scenario-select"),
  layerFilters: document.getElementById("layer-filters"),
  ablationLens: document.getElementById("ablation-lens"),
  viewSummary: document.getElementById("view-summary"),
  stepCaption: document.getElementById("step-caption"),
  stepCurrent: document.getElementById("step-current"),
  stepTotal: document.getElementById("step-total"),
  stepTitle: document.getElementById("step-title"),
  stepDescription: document.getElementById("step-description"),
  progressFill: document.getElementById("progress-fill"),
  play: document.getElementById("play-step"),
  playIcon: document.querySelector("#play-step .play-icon"),
  playLabel: document.querySelector("#play-step .play-label"),
  zoomReset: document.getElementById("zoom-reset"),
  inspectorLayer: document.getElementById("inspector-layer"),
  inspectorId: document.getElementById("inspector-id"),
  inspectorStatus: document.getElementById("inspector-status"),
  inspectorTitle: document.getElementById("inspector-title"),
  inspectorDescription: document.getElementById("inspector-description"),
  inspectorContract: document.getElementById("inspector-contract"),
  runtimeStateBlock: document.getElementById("runtime-state-block"),
  runtimeStateScope: document.getElementById("runtime-state-scope"),
  runtimeStateGrid: document.getElementById("runtime-state-grid"),
  inspectorPoints: document.getElementById("inspector-points"),
  inspectorFiles: document.getElementById("inspector-files"),
  inspectorNote: document.querySelector("#inspector-note p"),
};

function svgEl(tag, attrs = {}, text = null) {
  const node = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== null) node.textContent = text;
  return node;
}

function wrapTitle(text, limit = 23) {
  if (text.length <= limit) return [text];
  const words = text.split(" ");
  const lines = [""];
  for (const word of words) {
    const index = lines.length - 1;
    const next = `${lines[index]} ${word}`.trim();
    if (next.length > limit && lines[index] && lines.length < 2) lines.push(word);
    else lines[index] = next;
  }
  return lines;
}

function nodeMap(view) {
  return new Map(view.nodes.map(node => [node.id, node]));
}

function anchor(node, name = "auto", other = null) {
  if (name === "left") return [node.x, node.y + node.h / 2];
  if (name === "right") return [node.x + node.w, node.y + node.h / 2];
  if (name === "top") return [node.x + node.w / 2, node.y];
  if (name === "bottom") return [node.x + node.w / 2, node.y + node.h];
  if (other && other.x < node.x) return [node.x, node.y + node.h / 2];
  return [node.x + node.w, node.y + node.h / 2];
}

function edgePath(edge, nodes) {
  const from = nodes.get(edge.from);
  const to = nodes.get(edge.to);
  const [sx, sy] = anchor(from, edge.fromAnchor, to);
  const [tx, ty] = anchor(to, edge.toAnchor, from);
  if (edge.curve === "top") {
    const lift = Math.min(sy, ty) - 120;
    return `M ${sx} ${sy} C ${sx + 90} ${lift}, ${tx - 90} ${lift}, ${tx} ${ty}`;
  }
  if (edge.curve === "bottom") {
    const drop = Math.max(sy, ty) + 135;
    return `M ${sx} ${sy} C ${sx + 90} ${drop}, ${tx - 90} ${drop}, ${tx} ${ty}`;
  }
  if (edge.fromAnchor === "bottom" || edge.fromAnchor === "top") {
    const middle = (sy + ty) / 2;
    return `M ${sx} ${sy} C ${sx} ${middle}, ${tx} ${middle}, ${tx} ${ty}`;
  }
  const direction = tx >= sx ? 1 : -1;
  const bend = Math.max(55, Math.abs(tx - sx) * .42);
  return `M ${sx} ${sy} C ${sx + bend * direction} ${sy}, ${tx - bend * direction} ${ty}, ${tx} ${ty}`;
}

function edgeLabelPosition(edge, nodes) {
  const from = nodes.get(edge.from);
  const to = nodes.get(edge.to);
  let x = (from.x + from.w / 2 + to.x + to.w / 2) / 2;
  let y = (from.y + from.h / 2 + to.y + to.h / 2) / 2 - 8;
  if (edge.curve === "top") y = Math.min(from.y, to.y) - 105;
  if (edge.curve === "bottom") y = Math.max(from.y + from.h, to.y + to.h) + 110;
  if (edge.fromAnchor === "bottom" && edge.toAnchor === "top") x += 18;
  return [x, y];
}

function activeStep() {
  const view = VIEWS[state.view];
  if (!view) return null;
  const scenario = view.scenarios[state.scenario];
  return state.step >= 0 ? scenario.steps[state.step] : null;
}

function isNodeMutedByLens(node) {
  if (state.view !== "runtime" || state.lens === "full-system") return false;
  if (state.lens === "agentic-vector") return Boolean(node.tool && node.tool !== "vector");
  if (state.lens === "vanilla-vector") {
    const visible = new Set(["query", "vector_tool", "answer"]);
    return !visible.has(node.id);
  }
  return false;
}

function isEdgeMutedByLens(edge, nodes) {
  if (state.view !== "runtime") return false;
  if (edge.lens) return edge.lens !== state.lens;
  if (state.lens === "vanilla-vector") return true;
  if (state.lens === "agentic-vector") {
    return isNodeMutedByLens(nodes.get(edge.from)) || isNodeMutedByLens(nodes.get(edge.to));
  }
  return false;
}

function renderDiagram() {
  const view = VIEWS[state.view];
  if (!view) return;
  els.svg.setAttribute("viewBox", `0 0 ${view.width} ${view.height}`);
  els.edgeLayer.replaceChildren();
  els.nodeLayer.replaceChildren();
  const nodes = nodeMap(view);
  const step = activeStep();
  const activeNodeIds = new Set(
    step ? (Array.isArray(step[0]) ? step[0] : [step[0]]) : [],
  );
  const activeEdgeIds = new Set(
    step ? (Array.isArray(step[1]) ? step[1] : [step[1]]) : [],
  );

  for (const edge of view.edges) {
    const group = svgEl("g", { "data-edge": edge.id });
    const classes = ["edge-path"];
    if (edge.optional) classes.push("optional");
    if (edge.retry) classes.push("retry");
    if (edge.data) classes.push("data");
    const edgeFiltered = !state.enabledLayers.has(nodes.get(edge.from).layer) || !state.enabledLayers.has(nodes.get(edge.to).layer);
    if (edgeFiltered || isEdgeMutedByLens(edge, nodes)) classes.push("muted");
    if (activeEdgeIds.has(edge.id)) classes.push("active");
    const path = svgEl("path", { d: edgePath(edge, nodes), class: classes.join(" ") });
    group.append(path);
    if (edge.label) {
      const [lx, ly] = edgeLabelPosition(edge, nodes);
      group.append(svgEl("text", { x: lx, y: ly, class: "edge-label" }, edge.label));
    }
    els.edgeLayer.append(group);
  }

  for (const node of view.nodes) {
    const classes = ["architecture-node"];
    if (state.selectedNode === node.id) classes.push("selected");
    if (activeNodeIds.has(node.id)) classes.push("active");
    if (!state.enabledLayers.has(node.layer)) classes.push("filtered");
    else if (isNodeMutedByLens(node)) classes.push("muted");
    const group = svgEl("g", {
      class: classes.join(" "),
      transform: `translate(${node.x} ${node.y})`,
      "data-node": node.id,
      tabindex: "0",
      role: "button",
      "aria-label": `${node.title}: ${node.subtitle}`,
      style: `--node-color:${LAYERS[node.layer].color}`,
    });
    group.append(svgEl("circle", { cx: 18, cy: 18, r: 11, class: "node-step-ring" }));
    group.append(svgEl("rect", { x: 0, y: 0, width: node.w, height: node.h, class: "node-surface" }));
    group.append(svgEl("rect", { x: 0, y: 0, width: 3, height: node.h, rx: 2, class: "node-accent" }));
    group.append(svgEl("text", { x: 16, y: 20, class: "node-kicker" }, node.kicker));
    const titleLines = wrapTitle(node.title, Math.max(18, Math.floor(node.w / 8)));
    titleLines.forEach((line, index) => group.append(svgEl("text", { x: 16, y: 47 + index * 16, class: "node-title" }, line)));
    const subtitleY = titleLines.length === 1 ? 68 : 80;
    group.append(svgEl("text", { x: 16, y: subtitleY, class: "node-subtitle" }, node.subtitle));
    const chipWidth = Math.min(node.w - 32, Math.max(54, node.chip.length * 5.2 + 14));
    group.append(svgEl("rect", { x: 16, y: node.h - 24, width: chipWidth, height: 15, rx: 7.5, class: "node-chip" }));
    group.append(svgEl("text", { x: 23, y: node.h - 13.5, class: "node-chip-text" }, node.chip));
    const activate = () => selectNode(node);
    group.addEventListener("click", activate);
    group.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); activate(); }
    });
    els.nodeLayer.append(group);
  }
  applyViewport();
}

function selectNode(node) {
  state.selectedNode = node.id;
  updateInspector(node);
  renderDiagram();
}

function updateInspector(item, moduleGroup = null) {
  const isModule = Array.isArray(item);
  const layer = isModule ? moduleGroup.label : LAYERS[item.layer].label;
  const color = isModule ? moduleGroup.color : LAYERS[item.layer].color;
  const id = isModule ? item[0].split("/").pop().replace(".py", "") : item.id;
  const title = isModule ? item[0].split("/").pop() : item.title;
  const description = isModule ? item[2] : item.description;
  const contract = isModule ? item[3] : item.contract;
  const points = isModule
    ? [`${item[1].toLocaleString()} lines of source`, `กลุ่มความรับผิดชอบ: ${moduleGroup.label}`, `สัญลักษณ์หลัก: ${item[3]}`]
    : item.points;
  const files = isModule ? [item[0]] : item.files;
  const note = isModule
    ? "Source Map แสดง ownership ตามหน้าที่ของ module; dependency ระหว่าง module ดูได้ในสามผังหลัก"
    : item.note;
  els.inspectorLayer.textContent = layer;
  els.inspectorLayer.style.color = color;
  els.inspectorId.textContent = id.toUpperCase();
  els.inspectorStatus.textContent = isModule ? `${item[1]} LOC` : "source-grounded";
  els.inspectorTitle.textContent = title;
  els.inspectorDescription.textContent = description;
  els.inspectorContract.textContent = contract;
  els.inspectorPoints.replaceChildren(...points.map(point => {
    const li = document.createElement("li"); li.textContent = point; return li;
  }));
  els.inspectorFiles.replaceChildren(...files.map(path => {
    const div = document.createElement("div"); div.className = "file-link"; div.textContent = path; return div;
  }));
  els.inspectorNote.textContent = note;
}

function renderScenarioOptions() {
  const view = VIEWS[state.view];
  const entries = Object.entries(view.scenarios);
  if (!view.scenarios[state.scenario]) state.scenario = entries[0][0];
  els.scenarioSelect.replaceChildren(...entries.map(([id, scenario]) => {
    const option = document.createElement("option");
    option.value = id; option.textContent = scenario.label; return option;
  }));
  els.scenarioSelect.value = state.scenario;
  updateStepCaption();
}

const STATE_FIELD_COLORS = {
  original_query: "#edf5f2",
  tasks: "#64e0d4",
  current_task_index: "#ffb95c",
  current_action: "#ffb95c",
  plan_trace: "#7cb8ff",
  send_commands: "#b5a0ff",
  task_results: "#b5a0ff",
  attempts: "#ff8e9e",
  completed_tasks: "#8ddf8a",
  stop_reason: "#8ddf8a",
  final_answer: "#7cb8ff",
  citation_map: "#7cb8ff",
  synthesis_trace: "#7cb8ff",
};

const STATE_ITEM_COLORS = ["#64e0d4", "#ffb95c", "#b5a0ff", "#ff8e9e", "#8ddf8a"];

function stateValueElement(value) {
  if (!Array.isArray(value)) {
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(value, null, 2);
    return pre;
  }

  const list = document.createElement("div");
  list.className = "state-list";
  value.forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "state-list-item";
    card.style.setProperty("--item-color", STATE_ITEM_COLORS[index % STATE_ITEM_COLORS.length]);
    const badge = document.createElement("span");
    badge.className = "state-list-index";
    badge.textContent = `[${index}]`;
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(item, null, 2);
    card.append(badge, pre);
    list.append(card);
  });
  return list;
}

function renderRuntimeState(snapshotId = null) {
  if (state.view !== "runtime") return;
  const snapshot = runtimeStateSnapshots[snapshotId];
  els.runtimeStateScope.textContent = snapshot?.scope || "เลือก Play flow เพื่อดู State";

  if (!snapshot) {
    const empty = document.createElement("p");
    empty.className = "state-empty";
    empty.textContent = "State จะเปลี่ยนตาม node ที่กำลังทำงาน";
    els.runtimeStateGrid.replaceChildren(empty);
    return;
  }

  const fields = Object.entries(snapshot.fields).map(([name, value]) => {
    const card = document.createElement("section");
    card.className = "state-field";
    card.style.setProperty("--state-color", STATE_FIELD_COLORS[name] || "#edf5f2");
    const label = document.createElement("div");
    label.className = "state-field-name";
    const fieldName = document.createElement("span");
    fieldName.textContent = name;
    const shape = document.createElement("small");
    shape.textContent = Array.isArray(value) ? `list[${value.length}]` : typeof value;
    label.append(fieldName, shape);
    card.append(label, stateValueElement(value));
    return card;
  });
  els.runtimeStateGrid.replaceChildren(...fields);
}

function updateStepCaption() {
  const view = VIEWS[state.view];
  if (!view) return;
  const steps = view.scenarios[state.scenario].steps;
  els.stepTotal.textContent = `/ ${String(steps.length).padStart(2, "0")}`;
  if (state.step < 0) {
    els.stepCurrent.textContent = "00";
    els.stepTitle.textContent = "พร้อมสำรวจ";
    els.stepDescription.textContent = "กด Play flow หรือเลือกกล่องใดก็ได้เพื่อดูรายละเอียด";
    els.progressFill.style.width = "0%";
    renderRuntimeState();
    return;
  }
  const step = steps[state.step];
  els.stepCurrent.textContent = String(state.step + 1).padStart(2, "0");
  els.stepTitle.textContent = step[2];
  els.stepDescription.textContent = step[3];
  els.progressFill.style.width = `${((state.step + 1) / steps.length) * 100}%`;
  renderRuntimeState(step[4]);
  const activeNodeId = Array.isArray(step[0]) ? step[0][0] : step[0];
  const activeNode = view.nodes.find(node => node.id === activeNodeId);
  if (activeNode) {
    state.selectedNode = activeNode.id;
    updateInspector(activeNode);
  }
}

function stepBy(delta) {
  const steps = VIEWS[state.view].scenarios[state.scenario].steps;
  if (delta > 0 && state.step >= steps.length - 1) {
    state.step = -1;
    stopPlaying();
  } else {
    state.step = Math.max(-1, Math.min(steps.length - 1, state.step + delta));
  }
  updateStepCaption();
  renderDiagram();
}

function startPlaying() {
  if (state.playing) return stopPlaying();
  state.playing = true;
  els.playIcon.textContent = "Ⅱ";
  els.playLabel.textContent = "Pause";
  if (state.step < 0 || state.step >= VIEWS[state.view].scenarios[state.scenario].steps.length - 1) stepBy(1);
  state.playTimer = window.setInterval(() => stepBy(1), 1850);
}

function stopPlaying() {
  state.playing = false;
  window.clearInterval(state.playTimer);
  state.playTimer = null;
  els.playIcon.textContent = "▶";
  els.playLabel.textContent = "Play flow";
}

function renderLayerFilters() {
  const view = VIEWS[state.view];
  if (!view) return;
  const used = [...new Set(view.nodes.map(node => node.layer))];
  els.layerFilters.replaceChildren(...used.map(layer => {
    const button = document.createElement("button");
    button.className = `layer-filter${state.enabledLayers.has(layer) ? "" : " off"}`;
    button.style.setProperty("--filter-color", LAYERS[layer].color);
    button.innerHTML = `<i></i><span>${LAYERS[layer].label}</span>`;
    button.addEventListener("click", () => {
      if (state.enabledLayers.has(layer)) state.enabledLayers.delete(layer);
      else state.enabledLayers.add(layer);
      renderLayerFilters(); renderDiagram();
    });
    return button;
  }));
}

function renderSourceMap(query = "") {
  const normalized = query.trim().toLocaleLowerCase();
  let shown = 0;
  const fragments = [];
  for (const group of MODULE_GROUPS) {
    const modules = group.modules.filter(module => !normalized || module.join(" ").toLocaleLowerCase().includes(normalized));
    if (!modules.length) continue;
    shown += modules.length;
    const section = document.createElement("section"); section.className = "source-group";
    section.style.setProperty("--group-color", group.color);
    const head = document.createElement("div"); head.className = "source-group-head";
    const dot = document.createElement("i");
    const heading = document.createElement("h3"); heading.textContent = group.label;
    const count = document.createElement("span"); count.textContent = `${modules.length} modules`;
    head.append(dot, heading, count);
    const grid = document.createElement("div"); grid.className = "source-card-grid";
    for (const module of modules) {
      const card = document.createElement("article"); card.className = "source-card";
      card.tabIndex = 0;
      card.setAttribute("role", "button");
      card.setAttribute("aria-label", `Inspect ${module[0]}`);
      const top = document.createElement("div"); top.className = "source-card-top";
      const code = document.createElement("code"); code.textContent = module[0].replace("src/semigraph/", "");
      const loc = document.createElement("small"); loc.textContent = `${module[1]} LOC`;
      top.append(code, loc);
      const summary = document.createElement("p"); summary.textContent = module[2];
      const symbols = document.createElement("div"); symbols.className = "source-symbols"; symbols.textContent = module[3];
      card.append(top, summary, symbols);
      const inspectModule = () => updateInspector(module, group);
      card.addEventListener("click", inspectModule);
      card.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          inspectModule();
        }
      });
      grid.append(card);
    }
    section.append(head, grid); fragments.push(section);
  }
  els.sourceGroups.replaceChildren(...fragments);
  if (!shown) {
    const empty = document.createElement("div"); empty.className = "empty-source"; empty.textContent = "ไม่พบ module หรือ symbol ที่ตรงกับคำค้น";
    els.sourceGroups.append(empty);
  }
  els.sourceResultCount.textContent = `${shown} / 59 modules`;
}

function setView(viewId) {
  stopPlaying();
  state.view = viewId;
  state.step = -1;
  state.selectedNode = null;
  state.zoom = 1; state.panX = 0; state.panY = 0;
  document.querySelectorAll(".view-tab").forEach(button => {
    const active = button.dataset.view === viewId;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  const source = viewId === "source";
  els.diagramStage.hidden = source;
  els.sourceStage.hidden = !source;
  els.scenarioControl.hidden = source;
  els.sourceSearchControl.hidden = !source;
  els.layerFilters.hidden = source;
  els.ablationLens.hidden = true;
  els.runtimeStateBlock.hidden = viewId !== "runtime";
  els.stepCaption.hidden = source;
  document.querySelector(".zoom-controls").hidden = source;
  if (source) {
    els.viewSummary.textContent = "ค้นหา ownership ได้ครบทุก module, class และ function สำคัญใน src/semigraph";
    renderSourceMap(els.sourceSearch.value);
  } else {
    els.viewSummary.textContent = VIEWS[viewId].title;
    state.scenario = Object.keys(VIEWS[viewId].scenarios)[0];
    renderScenarioOptions();
    renderLayerFilters();
    renderDiagram();
    updateZoomLabel();
  }
}

function applyViewport() {
  els.viewport.setAttribute("transform", `translate(${state.panX} ${state.panY}) scale(${state.zoom})`);
  updateZoomLabel();
}

function updateZoomLabel() { els.zoomReset.textContent = `${Math.round(state.zoom * 100)}%`; }

function zoomBy(factor) {
  state.zoom = Math.max(.55, Math.min(2.2, state.zoom * factor));
  applyViewport();
}

function bindEvents() {
  document.querySelectorAll(".view-tab").forEach(button => button.addEventListener("click", () => setView(button.dataset.view)));
  els.scenarioSelect.addEventListener("change", event => {
    stopPlaying(); state.scenario = event.target.value; state.step = -1; updateStepCaption(); renderDiagram();
  });
  els.play.addEventListener("click", startPlaying);
  document.getElementById("previous-step").addEventListener("click", () => { stopPlaying(); stepBy(-1); });
  document.getElementById("next-step").addEventListener("click", () => { stopPlaying(); stepBy(1); });
  document.getElementById("zoom-in").addEventListener("click", () => zoomBy(1.14));
  document.getElementById("zoom-out").addEventListener("click", () => zoomBy(1 / 1.14));
  els.zoomReset.addEventListener("click", () => { state.zoom = 1; state.panX = 0; state.panY = 0; applyViewport(); });
  els.sourceSearch.addEventListener("input", event => renderSourceMap(event.target.value));
  els.ablationLens.querySelectorAll("button").forEach(button => button.addEventListener("click", () => {
    state.lens = button.dataset.lens;
    els.ablationLens.querySelectorAll("button").forEach(item => item.classList.toggle("active", item === button));
    stopPlaying(); state.step = -1; updateStepCaption(); renderDiagram();
  }));

  els.svg.addEventListener("wheel", event => {
    event.preventDefault(); zoomBy(event.deltaY < 0 ? 1.08 : 1 / 1.08);
  }, { passive: false });
  els.svg.addEventListener("pointerdown", event => {
    if (event.target.closest?.(".architecture-node")) return;
    state.dragging = true;
    state.dragStart = { x: event.clientX, y: event.clientY, panX: state.panX, panY: state.panY };
    els.diagramStage.classList.add("dragging");
    els.svg.setPointerCapture(event.pointerId);
  });
  els.svg.addEventListener("pointermove", event => {
    if (!state.dragging) return;
    const view = VIEWS[state.view];
    const scaleX = view.width / els.svg.clientWidth;
    const scaleY = view.height / els.svg.clientHeight;
    state.panX = state.dragStart.panX + (event.clientX - state.dragStart.x) * scaleX;
    state.panY = state.dragStart.panY + (event.clientY - state.dragStart.y) * scaleY;
    applyViewport();
  });
  const endDrag = () => { state.dragging = false; els.diagramStage.classList.remove("dragging"); };
  els.svg.addEventListener("pointerup", endDrag);
  els.svg.addEventListener("pointercancel", endDrag);
  document.addEventListener("keydown", event => {
    if (state.view === "source" || ["INPUT", "SELECT"].includes(document.activeElement?.tagName)) return;
    if (event.key === "ArrowRight") { stopPlaying(); stepBy(1); }
    if (event.key === "ArrowLeft") { stopPlaying(); stepBy(-1); }
    if (event.key === " ") { event.preventDefault(); startPlaying(); }
  });
}

bindEvents();
setView("runtime");
