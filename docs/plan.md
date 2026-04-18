# SemiGraph — Implementation Plan (v2.0)

> อัปเดตล่าสุด: 2026-04-15 • สอดคล้องกับเอกสาร `Project_GraphRAG.pdf`  
> สถานะปัจจุบัน: **Offline pipeline เสร็จ 70%** — เหลือ chunker + kg_extract + kg_store + pipeline orchestrator

---

## 1. Positioning งานวิจัย

**ชื่อแนวทาง:** Agentic GraphRAG with Investment Skills

**Contribution หลัก:**
- ด้าน GraphRAG Retrieval — graph-based context retrieval ด้วย semantic search + relationship traversal
- ด้าน Agent Engineering — Single Agent ที่มี tool มากมาย + Skill abstraction ที่ inject context ตามสถานการณ์

**ไม่ใช่** Multi-Agent Orchestration และ **ไม่ใช่** financial insight ใหม่ — contribution อยู่ที่ engineering ของระบบที่ apply framework เก่าอย่าง Fisher / Porter ลงบน corpus ขนาดใหญ่ผ่านระบบอัตโนมัติ

---

## 2. Architecture Decisions (ADR)

| ID | Decision | เหตุผลโดยย่อ |
|----|----------|--------------|
| **A1** | **Single Agent (LangGraph + ReAct + reflection)** — ไม่ใช้ Multi-Agent | scope เหมาะกับ thesis เดี่ยว, ไม่ต้องออกแบบ inter-agent protocol ที่ defend ยาก |
| **A2** | **Frameworks เป็น Skill ไม่ใช่ Agent** — Skill = system prompt bundle + scoring rubric | inject context ต่อ task ได้ ไม่เกิด information loss ระหว่าง agent |
| **A3** | **News/Sentiment เป็น tool ไม่ใช่ Agent** — ฝังใน `news_tools` | ลดความซับซ้อน, Agent ตัวเดียวเรียกได้ทุกเครื่องมือ |
| **A4** | **Ontology framework-neutral** — แยก "fact layer" (graph) จาก "interpretation layer" (Skill) | เพิ่ม Skill ใหม่ไม่ต้องแก้ graph schema |
| **A5** | **Evaluation ไม่ใช้ analyst consensus เป็น ground truth** — ใช้ internal consistency + explanation faithfulness + case study | consensus ไม่ใช่ objective truth; frame เป็น feature ไม่ใช่ bug |
| **A6** | **UI = Streamlit/Gradio demo tool** — แสดง reasoning trace | ลด dev overhead, เน้น demo สาธิตไม่ใช่ production |

---

## 3. ภาพรวมสถาปัตยกรรม

```
┌─────────────── Offline Indexing (batch) ──────────────┐
│                                                        │
│  SEC EDGAR  →  HTML→Markdown  →  Section extract      │
│                                                        │
│  Section text  →  chunker  →  2-stage extraction       │
│                                │  ├── GLiNER (entity)  │
│                                │  └── DeepSeek (rel)   │
│                                ▼                       │
│                         Neo4j KG (+ vector index)      │
└────────────────────────────────────────────────────────┘
                          ↓ query at runtime
┌─────────────── Online Reasoning ──────────────────────┐
│                                                        │
│  User → Workflow (QA / Ranking)                        │
│           │                                            │
│           └──► Single Agent (LangGraph ReAct loop)     │
│                   │                                    │
│                   ├── Skill (Fisher / Porter / ...)   │
│                   │     → inject system prompt         │
│                   │                                    │
│                   └── Tools:                           │
│                       ├── graph_tools   → Neo4j       │
│                       ├── financial_tools → Postgres  │
│                       └── news_tools    → News API    │
│                                                        │
│                   ↓ reflection → final answer          │
└────────────────────────────────────────────────────────┘
```

**3 data sources:**
- **Neo4j KG** — เก็บความสัมพันธ์เชิงคุณภาพจาก 10-K
- **PostgreSQL** — เก็บตัวเลขการเงิน (revenue, margin, ratios)
- **News API** — หัวข้อข่าวสารสดพร้อม sentiment

---

## 4. สถานะปัจจุบัน (2026-04-15)

| Step | ชื่อ | สถานะ | ไฟล์หลัก |
|------|------|--------|----------|
| 1 | Foundation — Config + Connections | ✅ Done | `config.py`, `connections.py` |
| 2 | Ontology — Schema + Pydantic Models | ✅ Done | `ontology/nodes.py`, `ontology/schema.py` |
| 2.5 | Offline — Ingest + Preprocess | ✅ Done | `offline/ingest.py`, `offline/preprocess.py` |
| 3 | Offline — KG Extraction | 🔜 Next | `offline/chunker.py`, `offline/kg_extract.py`, `offline/kg_store.py` |
| 4 | Offline — Pipeline Orchestrator | ⏳ Planned | `offline/pipeline.py` |
| 5 | Online — Tool Layer | ⏳ Planned | `online/tools/` |
| 6 | Online — Agent Core | ⏳ Planned | `online/agent/` |
| 7 | Online — Skills | ⏳ Planned | `online/skills/` |
| 8 | Online — Workflows (QA + Ranking) | ⏳ Planned | `online/workflows/` |
| 9 | Evaluation Framework | ⏳ Planned | `evaluate/` |
| 10 | UI Demo | ⏳ Planned | `app/` |

---

## 5. Step 3 — KG Extraction (สำคัญที่สุดที่กำลังจะทำ)

### 5.1 `offline/chunker.py`

**Goal:** ตัด section text เป็น chunks ที่ token-aware และ **รักษาขอบเขตย่อหน้า/ประโยค** เพื่อไม่ให้ entity ถูกตัดข้างกลาง

**Parameters:**
- chunk size: 800–1,000 tokens (default)
- overlap: 50–100 tokens
- separators: `["\n\n", "\n", ". ", " "]` (recursive)
- tune ได้ผ่าน `config.yaml`

**Input / Output:**
```python
chunks: List[ChunkMeta] = chunker.split(section_text, section, ticker, fiscal_year)
# ChunkMeta = { content, chunk_id, section, ticker, fiscal_year }
```

**Unit test:**
- chunk size ไม่เกิน max
- overlap ถูกต้อง
- section สั้น (<1,000 tokens) ไม่ถูก split

---

### 5.2 `offline/kg_extract.py` — 2-Stage Extraction

**ทำไมต้อง 2 stage** — การให้ LLM ทำทั้งการหา entity + หา relationship พร้อมกันในครั้งเดียวทำให้ recall ต่ำ เพราะ attention ถูก split ไปหลายงาน การแยกเป็น:
1. **Stage 1 — Entity Detection (GLiNER)** — เร็ว, local, high recall
2. **Stage 2 — Relationship Extraction (DeepSeek)** — ได้ entity list เป็น hint, focus ที่ relationship อย่างเดียว

ทำให้ precision + recall ดีกว่า single-stage approach

#### Stage 1 — GLiNER Entity Detection

```
chunk_text
    │
    │  labels = allowed node types from OntologyRegistry
    │           ["Company", "Product", "Technology", ...]
    ▼
GLiNER Model (urchade/gliner_large-v2.1)
    │
    ▼
List[Entity]
  - "NVIDIA Corporation"  (Company)
  - "H100 GPU"            (Product)
  - "CUDA"                (Technology)
  - "TSMC"                (Company)
```

#### Stage 2 — DeepSeek Relationship Extraction

```
System Prompt:
  - schema prompt จาก OntologyRegistry.build_schema_prompt(section)
  - entity list จาก Stage 1 เป็น "candidate entities"
  - คำสั่ง: "ใช้ entity จากรายการนี้ + หา entity เพิ่มถ้าจำเป็น + ระบุ relationships"

Human Message:
  - chunk_text

↓ with_structured_output(GraphExtractionResult)

GraphExtractionResult
  nodes: [...]
  relationships: [...]
```

#### Inline Validation

```python
valid_nodes = [n for n in result.nodes 
               if n.type in registry.get_nodes(section)]
valid_rels  = [r for r in result.relationships 
               if r.type in registry.get_relationships(section)]
```

**Unit test (no real LLM / GLiNER):**
- mock GLiNER return → ตรวจว่า entity list ถูกส่งต่อ Stage 2 ถูก
- mock DeepSeek return → ตรวจว่า validation filter กรอง hallucinate type ออก
- ตรวจว่า `name = id` ถูก inject อัตโนมัติ

---

### 5.3 `offline/kg_store.py` — Idempotent MERGE + Provenance

#### Provenance Properties

ทุก relationship จะมี metadata ติดไปด้วยเพื่อให้ **trace ได้ว่าข้อเท็จจริงนี้มาจากไหน** — สำคัญสำหรับ explanation faithfulness ใน evaluation:

```python
rel.properties.update({
    "source_filing": "0001045810-26-000021",  # SEC accession
    "ticker":        "NVDA",
    "fiscal_year":   "2026",
    "section":       "Item 1",
    "chunk_id":      "NVDA_FY2026_Item1_chunk_003",
})
```

#### Unique Constraints (รันครั้งแรก)

```cypher
CREATE CONSTRAINT IF NOT EXISTS
FOR (n:Company) REQUIRE n.id IS UNIQUE
-- ทำทุก label ใน NODE_CATALOG
```

#### MERGE Pattern

```cypher
MERGE (n:{label} {id: $id})
ON CREATE SET n += $properties
ON MATCH  SET n += $properties

MATCH (s:{src_label} {id: $source})
MATCH (t:{tgt_label} {id: $target})
MERGE (s)-[r:{rel_type} {fiscal_year: $fy}]->(t)
SET r += $properties
```

**หมายเหตุ:** relationship key รวม `fiscal_year` เพื่อให้ `COMPETES_WITH` ปี 2024 vs 2026 เป็นคนละ edge → graph เก็บ timeline ได้

#### Vector Index (รันครั้งแรก)

```cypher
CREATE VECTOR INDEX node_summary_embedding IF NOT EXISTS
FOR (n:Company) ON (n.summary_embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}
```

สร้างทุก node type ที่มี `summary` property เพื่อรองรับ `graph_semantic_search` tool

---

### 5.4 `offline/pipeline.py` — Orchestrator

**Goal:** รัน Step 3 แบบครบวงจรต่อ (ticker × fiscal_year × section)

**Features:**
- **Checkpoint** — บันทึกว่า chunk ไหน extract แล้ว → resume ได้ถ้า crash (SQLite `.checkpoint.db` ใน `data/`)
- **Error isolation** — 1 chunk fail ไม่หยุดทั้ง pipeline
- **Rate limiting** — delay ระหว่าง LLM calls
- **Summary report** — สรุปจำนวน nodes/rels ต่อ filing

**Config:**
```yaml
kg:
  max_workers: 16
  batch_size: 5
  checkpoint_enabled: true
```

---

## 6. Step 4 — Tool Layer

โครงสร้างใน `src/semigraph/online/tools/`:

```
tools/
├── graph_tools.py       graph_query_competitive, graph_query_risk, graph_semantic_search
├── financial_tools.py   get_financial_ratios, get_price_performance
└── news_tools.py        news_search_recent, news_check_events
```

**หลักการออกแบบ tool:**
- แต่ละ tool 1 งานเดียว ไม่ overlap
- docstring ครอบคลุม **when to use / what it returns / examples** — LLM เลือก tool จาก docstring นี้
- จำนวน tool รวม **6–8 ตัว** (LLM สับสนถ้ามากกว่านี้)

**Graph tools (สำคัญที่สุด):**

| Tool | ใช้เมื่อ | ทำอะไร |
|------|---------|--------|
| `graph_query_competitive` | คำถาม competitive landscape | traverse COMPETES_WITH, SUPPLIED_BY, SELLS_TO, SUBSTITUTED_BY |
| `graph_query_risk` | คำถามความเสี่ยง | traverse HAS_RISK, THREATENS + group by segment/geography |
| `graph_semantic_search` | คำถามที่ไม่เข้ากับ pattern อื่น | vector similarity search บน `summary_embedding` → **Hybrid GraphRAG** |

**Financial tools:**

| Tool | ทำอะไร |
|------|--------|
| `get_financial_ratios` | query PostgreSQL → revenue growth, gross margin, R&D %, etc. |
| `get_price_performance` | query PostgreSQL → return over N days |

**News tools:**

| Tool | ทำอะไร |
|------|--------|
| `news_search_recent` | ticker + time window → list of headlines + sentiment score |
| `news_check_events` | ตรวจ material events (ประกาศผลประกอบการ, เปลี่ยน management) |

**Token management:** news tool pre-filter + summarize ก่อน return ไม่งั้น context window overflow

---

## 7. Step 5 — Agent Core

**LangGraph state:**

```python
class AgentState(TypedDict):
    messages: List[BaseMessage]
    current_skill: Optional[str]        # Skill ที่ inject อยู่
    tool_calls: List[ToolCall]          # log สำหรับ reasoning trace
    scores: Dict[str, float]            # คะแนนแต่ละ Skill
    reflection_count: int               # นับรอบ reflect, กันลูปไม่สิ้นสุด
    evidence: List[GraphRef]            # node/rel ที่อ้างถึง (explanation)
    final_answer: Optional[str]
```

**Graph nodes:**
- `agent_node` — เรียก LLM ตัดสินใจว่าจะเรียก tool หรือตอบ
- `tool_node` — execute tool และส่งผลกลับ
- `reflection_node` — ตรวจสอบคำตอบ, ถ้าไม่พอจะวนต่อ (max `reflection_count=2`)
- `skill_loader_node` — inject Skill prompt (ใช้ใน Ranking mode)

**Flow:**
```
user query → agent_node → tool_node → agent_node (วนจนพอ)
                                          ↓
                                    reflection_node
                                          ↓
                              [end] หรือ [agent_node] ถ้ายังไม่พอ
```

---

## 8. Step 6 — Skills

**Skill Interface (Python class):**

```python
class Skill(ABC):
    name: str
    
    @abstractmethod
    def build_prompt(self, ticker: str, available_tools: List[str]) -> str: ...
    
    @abstractmethod
    def score_output(self, agent_response: str) -> Dict[str, float]: ...
    
    @abstractmethod
    def required_tools(self) -> List[str]: ...
```

### FisherSkill

Implement **Fisher's 15 Points** จาก *Common Stocks and Uncommon Profits*
- ครอบคลุม: growth potential, R&D commitment, profit margins, depth of management, accounting conservatism
- Prompt ระบุ hint ว่าแต่ละ point ควรเรียก tool ไหน (R&D → Technology nodes + R&D expense ratio)
- Score 1–5 ต่อ point → weighted total

### PorterSkill

Implement **Five Forces Analysis**
- threat of new entrants, bargaining power of suppliers, bargaining power of buyers, threat of substitutes, competitive rivalry
- Rate 1 (อ่อน = ดีสำหรับบริษัท) – 5 (แรง = ไม่ดี)

**Key property:** เพิ่ม Skill ใหม่ (เช่น DCF Skill) = เพิ่มไฟล์ใน `skills/` folder โดยไม่ต้องแก้ที่อื่น → **Extensibility เป็นจุดขายใน thesis**

---

## 9. Step 7 — Workflows

### QA Workflow

```
user query
    ↓
initialize agent state
    ↓
run LangGraph (agent ↔ tool ↔ reflection)
    ↓
return answer + tool_call trace
```

ไม่มีการโหลด Skill — Agent ใช้ default system prompt สำหรับ semiconductor analyst

### Ranking Workflow

```python
# Deterministic Python loop, ไม่ใช่ agent
for ticker in tickers:              # NVDA, AMD, MU, ...
    for skill in [fisher, porter]:
        # Agent ถูกเรียกเป็น sub-routine
        result = agent.run(
            query=f"Evaluate {ticker} using {skill.name}",
            skill=skill
        )
        scores[ticker][skill.name] = skill.score_output(result)

# รวม score เป็น composite ด้วย weighted average
ranked = sorted(tickers, key=lambda t: composite_score(scores[t]))
```

**ข้อดีของการแยก workflow จาก agent:**
- Deterministic order (คุณสมบัติที่ต้องการใน ranking)
- Parallelize ได้ (company × Skill independent)
- Agent ตัวเดียวใช้ซ้ำทุก iteration

---

## 10. Step 8 — Evaluation Framework (3 ชั้น)

### ชั้นที่ 1 — Retrieval Quality

**Benchmark ที่ใช้:**

| Source | ชนิดคำถาม | จำนวน |
|--------|-----------|-------|
| **FinanceBench subset** | qualitative + multi-hop (ตัด numerical-only ออก) | ~50 |
| **Custom Semiconductor QA** | derive จาก Competency Questions ของ ontology | 50–100 |

Custom benchmark ต้อง label gold answer + second verifier review → **contribution รอง** ของ thesis

**Ablation Study:**

```
┌────────────────────┬──────────┬──────────┬──────────┐
│ Config             │ Recall   │ Precision│ F1       │
├────────────────────┼──────────┼──────────┼──────────┤
│ vector-only        │  ?       │  ?       │  ?       │
│ graph-only         │  ?       │  ?       │  ?       │
│ hybrid (ของเรา)    │  ?       │  ?       │  ?       │
└────────────────────┴──────────┴──────────┴──────────┘
```

→ quantify contribution ของ graph component ได้

### ชั้นที่ 2 — Reasoning Quality

**LLM-as-a-Judge:**
- Judge ใช้ model **ต่างจาก agent** เพื่อลด bias
- (agent = DeepSeek, judge = Claude หรือ GPT)
- ประเมิน: **faithfulness** (ตอบตาม evidence), **relevance** (ตอบตรงคำถาม), **coherence** (สอดคล้องเป็นเหตุเป็นผล)

Semantic similarity เป็น secondary metric สำหรับ flag misalignment ไป manual review

### ชั้นที่ 3 — Ranking Quality

| Metric | ทำอะไร |
|--------|--------|
| **Internal Consistency** (Kendall's tau) | รัน ranking 2 ครั้งด้วย input เหมือน → ตรวจว่าอันดับเหมือนกันแค่ไหน |
| **Explanation Faithfulness** | sample ranking decisions → manually verify ว่า explanation chain trace กลับไป graph ได้จริง |
| **Qualitative Case Study** | เลือก 3–5 บริษัท top/bottom → เทียบ reasoning กับ published analyst reports |
| **Spearman rank correlation vs consensus** | **exploratory เท่านั้น** — consensus ไม่ใช่ ground truth |

### Skill Contribution Analysis

ทดลอง 3 config: Fisher only / Porter only / Combined  
→ รายงานว่าแต่ละ Skill contribute อะไรต่อ final ranking  
→ support หลัก extensibility ของระบบ

---

## 11. Timeline (ตาม `Project_GraphRAG.pdf`)

| เดือน | Milestone | Deliverable |
|-------|-----------|-------------|
| **ต.ค. 2568** | เสร็จ Offline Pipeline | Neo4j มี KG ครบ 15–20 บริษัท + vector index + smoke test |
| **มี.ค. 2569** | Tool Layer เสร็จ | 6–8 tools + FinanceBench baseline + PostgreSQL ETL + News API prototype |
| **เม.ย. 2569** | Agent Core + Skills | QA mode end-to-end + Fisher/Porter Skill + Ranking smoke test |
| **พ.ค. 2569** | Evaluation + เขียนบท | Custom benchmark เสร็จ + LLM-as-Judge + ranking metrics + Methodology/Architecture chapters |
| **มิ.ย. 2569** | Buffer | **ไม่ควรถึง — เผื่อสำหรับแก้ปัญหาไม่คาดคิด** |
| **ก.ค. 2569** | Finalize + Presentation | Results/Discussion chapters + demo + slides |

---

## 12. ขอบเขตโครงงาน (สิ่งที่ **ไม่** ทำ)

- ❌ ไม่สร้าง production-grade investment system
- ❌ ไม่รวม trade execution, portfolio construction, risk management
- ❌ ไม่ claim financial insight ใหม่
- ❌ ไม่ขยายเกิน 10-K (ไม่รวม 10-Q, DEF 14A, 20-F ในขอบเขตนี้)
- ❌ ไม่เปรียบเทียบ LLM — hold DeepSeek constant, วัด retrieval config แทน

**contribution scope:**
- ✅ Engineering: GraphRAG pipeline + Agent + Skills architecture
- ✅ Retrieval evaluation: ablation study (vector / graph / hybrid)
- ✅ Extensibility: plug-in Skills framework
- ✅ Custom benchmark: Semiconductor QA dataset (secondary contribution)

---

## 13. ความเสี่ยงและการบรรเทา

| # | ความเสี่ยง | บรรเทา |
|---|-----------|--------|
| 1 | **KG extraction quality ต่ำ** (LLM สับสน, GLiNER ข้าม entity สำคัญ) | iterate prompt + เพิ่ม verification pass (LLM call ครวจสอบ relationship กับ source text) ก่อน store |
| 2 | **Custom benchmark ใช้เวลาสร้างเยอะเกิน** | ถ้าทำไม่เสร็จ → ลดเหลือ 30 คำถาม focus CQ หลัก, เขียนเป็น limitation |
| 3 | **Token consumption สูงใน ranking** | prompt caching ของ Skill prompt + summarize tool output + hard cap รอบ tool calls |
| 4 | **FinanceBench subset ไม่ตรง semiconductor** | custom benchmark ครอบคลุม universe ของเรา; FinanceBench = supplementary ไม่ใช่ primary |

---

## 14. จุดที่เปลี่ยนจาก Plan v1

| เดิม (v1) | ใหม่ (v2) | เหตุผล |
|----------|-----------|--------|
| Multi-Agent (Manager + Fundamental + News) | Single Agent + Skills + Tools | Defend Multi-Agent ยาก, scope ใหญ่เกิน thesis เดี่ยว |
| Single-stage LLM extraction | 2-stage (GLiNER → DeepSeek) | Recall + precision ดีกว่า |
| ไม่มี provenance ใน edges | source_filing/chunk_id ใน relationship properties | จำเป็นสำหรับ explanation faithfulness |
| CQ pass rate เป็น metric หลัก | 3-layer evaluation (Retrieval / Reasoning / Ranking) | รอบด้านกว่า + defend ได้ |
| Spearman vs consensus = primary | Exploratory only | consensus ไม่ใช่ ground truth |
| ไม่คิดเรื่อง UI | Streamlit/Gradio demo | เผื่อใช้สาธิตในการสอบ |

---

*เอกสารนี้จะอัปเดตเมื่อ implement แต่ละ step — เก็บเวอร์ชันเก่าใน git history*
