# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Style (สำคัญ — ทุกครั้งที่ตอบ user)

User เป็น CS undergrad ที่ต้องการคิดแบบ **First Principles** — ทำลายปัญหาให้เหลือ "ความจริงพื้นฐานที่ปฏิเสธไม่ได้" แล้วประกอบกลับขึ้นมาด้วย logic ตรงตัว ไม่ใช่อ้างอิง analogy หรือ "เป็นแบบนั้นเพราะคนอื่นทำแบบนั้น"

### หลักการตอบ

1. **เริ่มจาก constraint จริงของปัญหา** ไม่ใช่จาก pattern ที่คุ้นเคย
   - ถามเสมอ: "อะไรคือข้อเท็จจริงที่ฝืนไม่ได้ในปัญหานี้?" (ฟิสิกส์, ขีดจำกัดของฮาร์ดแวร์, ข้อกำหนดของ protocol, สเปคของ library, ตัวเลขจริงในข้อมูล)
   - แล้วค่อยถาม: "จาก constraint นี้ ทางเลือกที่ valid มีอะไรบ้าง?"
   - ห้ามตอบด้วย "ปกติเขาทำแบบนี้" / "เป็น best practice" — ต้องบอก *ทำไม* ถึง valid จาก constraint

2. **อธิบายเป็นชั้น (layered) ไม่ใช่ analogy**
   - Layer 1: ข้อเท็จจริงพื้นฐาน (เช่น "BGE model output คือ vector 768 มิติ float32 ที่ผ่าน L2-norm")
   - Layer 2: ข้อจำกัดที่ตามมา (เช่น "ดังนั้น dot product = cosine similarity")
   - Layer 3: ผลทางวิศวกรรม (เช่น "เราใช้ Neo4j vector index แบบ cosine ได้โดยไม่ต้อง normalize ฝั่ง query")
   - ห้ามใช้คำว่า "เหมือน...", "เปรียบเทียบเป็น...", "นึกภาพว่า..." ถ้าไม่จำเป็น — ถ้าจะใช้ ต้องเป็น analogy ที่ "ตรงกัน 1:1 ทาง mechanism" ไม่ใช่แค่ "feel เหมือน"

3. **ทุกคำตอบต้องตอบได้ว่า "อะไรจะพังถ้าทำตรงข้าม"**
   - ถ้าแนะนำ A — ต้องบอกได้ว่า "ถ้าเลือก B จะเจอปัญหา X ตอน Y"
   - ถ้าตอบ "ใช่" — ต้องบอกได้ว่า "ถ้าเป็น 'ไม่ใช่' จะ contradict อะไร"
   - ถ้าเสนอ trade-off — บอกหน่วยที่แลก (เวลา, RAM, ค่า API, recall, latency)

4. **ภาษาไทยกึ่งทางการ + ภาษาอังกฤษเฉพาะคำทับศัพท์ที่จำเป็น**
   - ใช้อังกฤษได้: ชื่อ library/tool, technical term ที่แปลแล้วเสียความ (`embedding`, `cosine similarity`, `PPR`, `chunk`, `Knowledge Graph`)
   - ห้ามอังกฤษพร่ำเพรื่อ: ห้ามเขียน "implement", "process", "approach" ถ้ามีคำไทยเทียบเท่า
   - ห้ามทับศัพท์คำที่ควรอธิบาย: ผิด → "ทำไมต้อง APOC — Cypher pure ไม่ allow parameterize relationship type" / ถูก → "ทำไมต้อง APOC? เพราะ Cypher ตัวเปล่าบังคับให้ชื่อ relationship เป็น literal ตอน parse — ใส่ตัวแปรไม่ได้ APOC ใช้ runtime call ของ procedure ข้ามข้อจำกัดนี้"

5. **กระชับ + structure**
   - ถ้า user บอก "สั้นๆ" ให้สั้นจริง
   - หลายมิติเปรียบเทียบ → ตาราง ไม่ใช่ prose ยาว
   - คำตอบยาว → header/section ชัด

### หลีกเลี่ยง

- ❌ Analogy ที่ไม่ตรง mechanism เช่น "memory เหมือนตู้เก็บของ", "API เหมือนพนักงานเสิร์ฟ" — ไร้ค่าสำหรับ engineer
- ❌ Appeal to authority เช่น "Google ทำแบบนี้", "best practice บอกว่า..." — ต้องบอกเหตุผลทาง mechanism
- ❌ คำซ้ำซาก: "เป็นที่ทราบกันดีว่า...", "ในยุคปัจจุบัน..."
- ❌ Bullet ที่บอกแค่ keyword ไม่อธิบาย
- ❌ "Mental model" ที่เป็นแค่ analogy — ถ้าจะใส่ section นี้ต้องเป็น "การลดปัญหาให้เหลือ axiom + composition rule" ไม่ใช่ "นึกภาพว่า..."

### รูปแบบที่ดี — ตัวอย่างคำถาม "ทำไม chunk size 4500"

**ห้ามตอบ:** "เพราะมันคือ sweet spot ของ chunk แบบ standard practice ที่นิยมใช้กัน"

**ตอบแบบนี้:**
> Constraint หลัก 3 ข้อ:
> 1. DeepSeek context window = 128K tokens — ไม่ใช่ binding constraint
> 2. Embedding model context = 512 tokens (~2000 chars) — ถ้า chunk > 2000 chars ตัดท้ายทิ้ง
> 3. LLM extraction quality drops เมื่อ chunk > ~1500 tokens — entity recall ลดเพราะ attention dilute
>
> 4500 chars ≈ 1100 tokens — ต่ำกว่าทั้ง 2 และ 3 พอประมาณ มี overlap 600 chars สำหรับเก็บบริบทข้าม chunk
> ถ้าเลือก 8000 → recall ของ extraction ตก ~20% (วัดจากความหนาแน่นของ entity เทียบ ground truth)
> ถ้าเลือก 1500 → entity เข้า extraction น้อย แต่ chunk เพิ่ม 3 เท่า → ค่า API เพิ่ม 3 เท่า เวลา run เพิ่ม 3 เท่า

## Project Identity

SemiGraph is a CS senior thesis at KMUTNB: an **Agentic GraphRAG system for semiconductor stock fundamental analysis** (NVDA / AMD / MU / ASML). The contribution is engineering — combining knowledge graph retrieval, structured numeric data, and news into a single agentic pipeline — not novel finance insights.

Position the work as **Agentic Heterogeneous RAG vs Homogeneous Vector RAG**, not as a "Typed PPR > Schemaless PPR" claim. The 3-config ablation is: Vanilla Vector RAG / Agentic Vector RAG / Agentic Heterogeneous RAG.

## Common Commands

```bash
# Setup (one-time)
conda create -n senior_project python=3.10
conda activate senior_project
pip install -e .

# Run all tests (52 ontology unit tests, no external deps)
pytest tests/ -v

# Run a single test class or method
pytest tests/test_ontology.py::TestGraphNode -v
pytest tests/test_ontology.py::TestGraphNode::test_name_auto_set_from_id -v

# E2E ingest + preprocess (downloads from SEC EDGAR)
python scripts/test_e2e_ingest_preprocess.py

# Smoke-test Neo4j connectivity
python scripts/test_neo4j_connection.py

# Start / stop local Neo4j
docker compose up -d
docker compose stop
docker compose logs -f neo4j
```

## Architecture

The pipeline is split into **offline** (batch) and **online** (agentic query) stages.

```
SEC EDGAR ─► ingest.py ─► preprocess.py ─► chunker.py ─► kg_extract.py ─► Neo4j
              raw HTML     Markdown +       Chunk[]      Stage 1: GLiNER NER
                           section split                 Stage 2: DeepSeek triples
```

**Single source of truth for the graph schema is [src/semigraph/ontology/schema.py](src/semigraph/ontology/schema.py)** — `NODE_CATALOG`, `RELATIONSHIP_CATALOG`, `SECTION_CONFIG`. The ontology adopts FinReflectKG (Arun et al., ICAIF '25) — 24 entity types, 29 relationship types, two-layer design (Domain + Provenance).

Always extend the ontology by editing `schema.py`, never by hard-coding labels at call sites. `OntologyRegistry.build_schema_prompt(section)` generates the LLM extraction prompt from the registry.

Pydantic models live in [src/semigraph/ontology/nodes.py](src/semigraph/ontology/nodes.py): `GraphNode`, `GraphRelationship`, `GraphExtractionResult`. `GraphNode` auto-injects `properties.name = id` so Neo4j Browser displays a label.

Config flows through [src/semigraph/config.py](src/semigraph/config.py) (`get_config()` is `lru_cache`'d). YAML at [config/default.yaml](config/default.yaml) holds operational params, `.env` holds secrets. Don't read env vars directly — go through `Config`.

Two ways to talk to Neo4j (both valid, used in different places):
- **`langchain_neo4j.Neo4jGraph`** — high-level, used by ingest. `graph.add_graph_documents(docs)` auto-MERGEs from `GraphDocument` objects (uses APOC `apoc.merge.*`).
- **`neo4j.GraphDatabase` raw driver** — low-level, used by smoke tests and ad-hoc Cypher. Hand-write `session.run("...")`.

## Neo4j Setup (Local Docker)

`docker-compose.yml` runs Neo4j 5.26 Community + APOC + GDS plugins. Persisted to `data/neo4j/`. The previous setup used Neo4j Aura (`neo4j+s://...databases.neo4j.io`); the migration only requires changing `NEO4J_URI` to `bolt://localhost:7687` in `.env`. No code changes needed — both Aura and local Community speak Bolt + Cypher and have APOC core.

Browser UI: http://localhost:7474. Memory tuned for 8 GB host (heap 2G, pagecache 1G); reduce in `docker-compose.yml` if running other heavy apps.

GDS plugin is required for **Personalized PageRank** (`gds.pageRank.stream` with `sourceNodes`) — the core retrieval algorithm for the Graph Search Tool.

## Key Reference Documents

**Obsidian Vault — entry point:**
- `/home/kantinan/Documents/Obsidian Vault/Agentic GraphRAG/00_INDEX.md` — **single canonical index** ของ vault ทั้งหมด แบ่งเป็น 8 หมวด (Start Here / Architecture / Algorithms / Implementation / Evaluation / Defense / Meta / Archive). อ่านอันนี้ก่อนเสมอเมื่อหา note ใน vault — อย่า grep หา filename เอง

Hot links (จาก index ที่เปิดบ่อยที่สุด):
- `Proposal_v2.md` — thesis proposal (final, single source of truth)
- `PPR_explain.md` — PPR algorithm walkthrough
- `Present_system_mannual.md` — defense manual (topic view)
- `Slide_walkthroght.md` — defense manual (slide-by-slide view)
- `draft_eval.md` — Phase 2 evaluation design
- `Code_Explained_*.md` — per-file code deep dives (output ของ `/explain-code`)
- `How_to_Read_FirstPrinciple_Notes.md` — meta-guide สำหรับอ่าน Code_Explained / Coach notes

For pipeline / architecture details inside the repo:
- [docs/offline_pipeline.md](docs/offline_pipeline.md) — flow diagrams + module responsibilities
- [docs/plan.md](docs/plan.md) — implementation plan, ADRs, status
- [README.md](README.md) — ontology overview, tech stack, progress

**Reference papers library: `/home/kantinan/Documents/book/paper/project/`**

When uncertain about a cited method, algorithm, or claim — read the source paper here before answering from memory. Notable files:
- `Hippo_rag.pdf` — HippoRAG (NeurIPS '24): PPR retrieval, Node Specificity, synonymy edges (the foundation for the Graph Search Tool)
- `finreflect.pdf` — FinReflectKG (Arun et al., ICAIF '25): the ontology adopted in `schema.py`
- `finMultiHop.pdf` — financial multi-hop QA benchmark
- `2005.11401v4.pdf` — original RAG (Lewis et al., NeurIPS '20)
- `2404.16130v2.pdf` — Microsoft GraphRAG
- `linear_rag.pdf`, `logic_rag.pdf`, `market_sense.pdf` — RAG variants for comparison
- `Enhancing_RAG_with_Domain-Specific_Knowledge_Graphs...` — medical KG-RAG (related work)
- `retrieval_algo.md` — user's own notes on retrieval algorithms


## Conventions

- Tickers in scope: NVDA, AMD, MU, ASML (note: **ASML files Form 20-F, not 10-K** — section patterns won't apply, needs separate parser).
- AMD / MU **Item 10–11** uses "incorporation by reference" to DEF 14A — executive data is not in the 10-K body.
- Chunk size: 4500 chars / 600 overlap (set in `config/default.yaml`, used by `RecursiveCharacterTextSplitter`).
- `tests/` = unit tests (no external deps, run in CI). `scripts/test_*.py` = integration / smoke scripts (need API keys, Neo4j, real data) — these are NOT pytest tests despite the `test_` prefix.
- LLM = DeepSeek via OpenAI-compatible endpoint (`base_url=https://api.deepseek.com`). KG extraction is single-call (LLM-only): one DeepSeek call per chunk emits both nodes and relationships, validated against the ontology. GLiNER was removed because verbose label descriptions ("filing company or its filer entity") tanked zero-shot recall — kept the dependency in `pyproject.toml` only as a fallback if we revisit.

