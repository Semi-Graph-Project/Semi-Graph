# CLAUDE.md

SemiGraph — CS senior thesis (KMUTNB): **Agentic GraphRAG for semiconductor stock fundamental analysis** (NVDA/AMD/MU/ASML). Contribution is engineering (KG retrieval + structured numerics + news in one agentic pipeline), not finance insight. Position as **Agentic Heterogeneous RAG vs Homogeneous Vector RAG**; 3-config ablation: Vanilla Vector / Agentic Vector / Agentic Heterogeneous.

## Response Style (สำคัญทุกครั้ง)

User เป็น CS undergrad. ใช้**ภาษาพูดไทยแบบรุ่นพี่ CE สอนรุ่นน้อง**เสมอ. เมื่อต้องอธิบาย concept / แนวคิด / วิธีการ / ทฤษฎี / เครื่องมือ → อธิบาย **2 ชั้นตามลำดับ**:

**ชั้น 1 — ภาพรวม (Feynman, analogy-based):** สวมบทรุ่นพี่ที่สอนเก่งระดับเทพ พาเห็นภาพด้วย analogy ที่จับได้ทันที ให้ "อ๋อ เก็ตแล้ว" ก่อนลงรายละเอียด
**ชั้น 2 — เจาะลึกเทคนิค (First Principles, non-analogy):** พอเห็นภาพแล้ว **ทิ้ง analogy ทันที** ลงลึกด้วยข้อเท็จจริงล้วน คงความถูกต้องของทฤษฎีครบ. ตอนข้ามชั้น บอกจุดที่ analogy ชั้น 1 "รั่ว" ด้วย. **non-analogy ≠ jargon-dense — ยังต้องภาษาพูด: term ที่ user อาจไม่คุ้น (เช่น "stationary distribution") ต้องกางทันที 1 term ต่อ 1 ประโยค ห้าม stack ศัพท์ติดกันโดยไม่อธิบาย**. กฎของชั้นนี้:
1. **เริ่มจาก constraint จริง** (hardware, protocol, library spec, ตัวเลขในข้อมูล) → หา option ที่ valid. ห้าม "ปกติเขาทำ"/"best practice" — บอก *ทำไม* จาก constraint
2. **อธิบายเป็นชั้น**: ข้อเท็จจริง → ข้อจำกัดที่ตามมา → ผลทางวิศวกรรม
3. **ตอบได้ว่า "อะไรพังถ้าทำตรงข้าม"** + trade-off บอกหน่วยที่แลก (เวลา/RAM/ค่า API/recall/latency)

ทั่วไป: ไทยกึ่งทางการ + อังกฤษเฉพาะคำทับศัพท์จำเป็น (ชื่อ library, `embedding`, `PPR`, `chunk`). ห้าม "implement/process/approach" ถ้ามีไทยเทียบเท่า. กระชับ — เทียบหลายมิติใช้ตาราง.

analogy ใช้ได้**เฉพาะชั้น 1**; ชั้น 2 ห้ามเด็ดขาด. หลีกเลี่ยง: ❌ appeal to authority ❌ คำซ้ำซาก ("เป็นที่ทราบกันดี") ❌ bullet ที่มีแต่ keyword

## Commands

```bash
conda activate senior_project && pip install -e .   # setup
pytest tests/ -v                                     # unit tests (no external deps)
pytest tests/test_ontology.py::TestGraphNode -v      # single class/method
docker compose up -d                                 # local Neo4j 5.26 (+ APOC + GDS), UI :7474
python scripts/test_neo4j_connection.py              # smoke-test Neo4j connectivity
```

## Architecture

Offline (batch) → Online (agentic query):
`SEC EDGAR → ingest.py → preprocess.py → chunker.py → kg_extract.py → Neo4j`

- **Schema single source of truth: [src/semigraph/ontology/schema.py](src/semigraph/ontology/schema.py)** (`NODE_CATALOG`, `RELATIONSHIP_CATALOG`, `SECTION_CONFIG`) — adopts FinReflectKG (24 entities, 29 relations). Extend by editing `schema.py`, never hard-code labels at call sites. `OntologyRegistry.build_schema_prompt(section)` builds the extraction prompt.
- Pydantic models: [src/semigraph/ontology/nodes.py](src/semigraph/ontology/nodes.py) (`GraphNode` auto-injects `properties.name = id` for Neo4j Browser labels).
- Config: [src/semigraph/config.py](src/semigraph/config.py) (`get_config()` lru_cache'd). YAML = params, `.env` = secrets. ห้ามอ่าน env ตรง — ผ่าน `Config`.
- Neo4j สองทาง: `langchain_neo4j.Neo4jGraph` (high-level, ingest, `add_graph_documents` → APOC merge) หรือ raw `neo4j.GraphDatabase` driver (low-level Cypher). **GDS plugin จำเป็นสำหรับ Personalized PageRank** (`gds.pageRank.stream` + `sourceNodes`) — core ของ Graph Search Tool.

## Key Reference Documents

**Obsidian Vault — entry point:** `/home/kantinan/Documents/Obsidian Vault/Agentic GraphRAG/00_INDEX.md` — **single canonical index** แบ่ง 8 หมวด (Start Here / Architecture / Algorithms / Implementation / Evaluation / Defense / Meta / Archive). อ่านก่อนเสมอเมื่อหา note — อย่า grep หา filename เอง

Hot links (เปิดบ่อยสุด):
- `Proposal_v2.md` — thesis proposal (final, single source of truth)
- `PPR_explain.md` — PPR algorithm walkthrough
- `Present_system_mannual.md` / `Slide_walkthroght.md` — defense manual (topic view / slide-by-slide)
- `draft_eval.md` — Phase 2 evaluation design
- `Code_Explained_*.md` — per-file code deep dives (output ของ `/explain-code`)
- `How_to_Read_FirstPrinciple_Notes.md` — meta-guide อ่าน Code_Explained / Coach notes

In-repo: [docs/plan.md](docs/plan.md) (plan/ADR/status) · [docs/offline_pipeline.md](docs/offline_pipeline.md) (flow + module responsibilities) · [README.md](README.md) (ontology/tech stack/progress)

**Papers: `/home/kantinan/Documents/book/paper/project/`** — เมื่อไม่แน่ใจ cited method/algorithm/claim อ่าน source ก่อนตอบจากความจำ:
- `Hippo_rag.pdf` — HippoRAG (NeurIPS '24): PPR, Node Specificity, synonymy edges — foundation ของ Graph Search Tool
- `finreflect.pdf` — FinReflectKG (ICAIF '25): ontology ที่ adopt ใน `schema.py`
- `finMultiHop.pdf` — financial multi-hop QA benchmark
- `2005.11401v4.pdf` — original RAG (Lewis '20) · `2404.16130v2.pdf` — Microsoft GraphRAG
- `linear_rag.pdf` / `logic_rag.pdf` / `market_sense.pdf` — RAG variants เทียบ · `retrieval_algo.md` — user's own notes

## Conventions

- Tickers: NVDA, AMD, MU, ASML. **ASML = Form 20-F ไม่ใช่ 10-K** (section pattern ใช้ไม่ได้ ต้อง parser แยก). AMD/MU **Item 10–11** ใช้ incorporation-by-reference ไป DEF 14A — exec data ไม่อยู่ใน 10-K body.
- Chunk: 4500 chars / 600 overlap (`config/default.yaml`, `RecursiveCharacterTextSplitter`). เหตุผล: embedding ctx 512 tok (~2000 chars) + extraction recall ตกเมื่อ chunk ใหญ่เกิน.
- `tests/` = unit (CI, no external deps). `scripts/test_*.py` = integration/smoke (ต้องมี API key/Neo4j/real data) — ไม่ใช่ pytest แม้ขึ้นชื่อ `test_`.
- LLM = DeepSeek (OpenAI-compatible, `base_url=https://api.deepseek.com`). KG extraction = single LLM call/chunk (emit nodes + relations, validate กับ ontology). GLiNER ถูกถอด (verbose label ทำ zero-shot recall ตก) — เหลือใน `pyproject.toml` เป็น fallback.
