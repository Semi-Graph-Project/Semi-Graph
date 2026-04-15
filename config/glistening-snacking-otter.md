# Restructuring Plan: GraphRAG Multi-Agent System for Semiconductor Stock Analysis

## Context
Project ปริญญานิพนธ์ "GraphRAG-Enhanced Multi-Agent System for Fundamental Analysis of Semiconductor Stocks" ตอนนี้เป็น test scripts 11 ไฟล์แยกกัน ไม่มี module structure, hardcode ค่าทุกอย่าง, ต้องรัน manual ทีละ step ต้อง refactor ให้เป็น proper Python package ที่รันได้ end-to-end ตาม architecture ใน thesis (Offline Indexing + Online Multi-Agent + Evaluation)

---

## Target Project Structure

```
project/
├── pyproject.toml
├── .env.example                      # Template for secrets
├── config/
│   ├── default.yaml                  # chunk_size, model params, batch_size etc.
│   └── tickers.yaml                  # 20-30 semiconductor tickers
├── src/semigraph/
│   ├── __init__.py
│   ├── config.py                     # pydantic-settings (.env + YAML)
│   ├── connections.py                # Neo4j, LLM, Embedding factory functions
│   │
│   ├── offline/                      # === Indexing Pipeline ===
│   │   ├── ingest.py                 # SEC EDGAR download + RSS
│   │   ├── preprocess.py             # HTML→Markdown, section extraction
│   │   ├── chunker.py                # Text splitting config
│   │   ├── ner.py                    # GLiNER NER (NEW)
│   │   ├── kg_extract.py             # DeepSeek relation extraction
│   │   ├── kg_validate.py            # Pydantic schema validation
│   │   ├── kg_store.py               # Neo4j batch saving
│   │   └── pipeline.py              # Orchestrator
│   │
│   ├── ontology/                     # === Single Source of Truth ===
│   │   ├── nodes.py                  # Pydantic models (GraphNode, etc.)
│   │   ├── relationships.py          # Relationship definitions
│   │   └── schema.py                 # OntologyRegistry (merge dataclass + JSON)
│   │
│   ├── online/                       # === Multi-Agent ===
│   │   ├── manager_agent.py          # Plan-and-Solve + Reflexion
│   │   ├── fundamental_agent.py      # Self-RAG + Investment Thesis
│   │   ├── news_agent.py             # News fetch + Sentiment
│   │   ├── graph_qa.py               # Cypher QA chain
│   │   └── prompts/                  # External prompt templates
│   │
│   ├── evaluation/                   # === Evaluation ===
│   │   ├── financebench.py           # FinanceBench benchmark
│   │   ├── ragas_eval.py             # RAGAS comparison
│   │   └── backtesting.py            # Historical backtesting
│   │
│   └── utils/
│       ├── neo4j_diagnostic.py
│       └── logging.py
│
├── cli.py                            # Typer CLI entry point
├── data/                             # (existing, unchanged)
├── tests/
└── scripts/                          # Keep originals as reference
```

---

## Implementation Phases

### Phase 0: Foundation (config + connections)
**Files to create:** `pyproject.toml`, `.env.example`, `config/default.yaml`, `config/tickers.yaml`, `src/semigraph/config.py`, `src/semigraph/connections.py`

- `config.py`: pydantic-settings อ่าน `.env` (secrets) + YAML (params)
- `connections.py`: factory functions `get_neo4j()`, `get_llm()`, `get_embeddings()`
- ย้าย credentials ออกจาก source code ทั้งหมด (Neo4j password, DeepSeek API key อยู่ hardcode ใน 6+ files)

### Phase 1: Offline -- Ingest + Preprocess
**Refactor from:** `test_fundamental_fetch.py` → `offline/ingest.py`, `test_clean.py` → `offline/preprocess.py`

Key changes:
- **ingest.py**: parameterize ticker/filing_type, read email/org from config, accept ticker list
- **preprocess.py**: ลบ `global year`, ทำเป็น function params แทน, แก้ section key naming ให้ consistent (primary vs fallback ใช้ชื่อต่างกัน)
- **chunker.py**: extract `RecursiveCharacterTextSplitter` config จาก `test_KG_custom_chain.py:381-383`

### Phase 2: Ontology Unification
**Merge:** `Ontology` dataclass (`test_KG_custom_chain.py:28-119`) + `graph_schema.json` + `item8_node_schemas` dict

สร้าง `OntologyRegistry` class:
- `get_nodes_for_section("Item 1")` → list of node types
- `get_relationships_for_section("Item 1")` → list of relationship patterns
- `get_node_schema("FinancialTable")` → properties, examples, hints

Export `GraphNode`, `GraphRelationship`, `GraphExtractionSchema` Pydantic models จาก `ontology/nodes.py`

### Phase 3: KG Extraction Pipeline
**Refactor from:** `test_KG_custom_chain.py` → split เป็น 3 modules

| Source | Target | What |
|--------|--------|------|
| `DeepSeekGraphTransformer` class (line 205-378) | `offline/kg_extract.py` | Core extraction, inject LLM via constructor |
| `validate_node_properties` (line 283-301) | `offline/kg_validate.py` | Standalone validation |
| `save_to_neo4j_in_batches` (line 434-477) | `offline/kg_store.py` | Batch save with retry |

**NEW:** `offline/ner.py` -- GLiNER integration (ตาม thesis section 6.1.2 step 1)
- ใช้ GLiNER model สแกน entity ก่อนส่ง LLM
- ลด token cost + เพิ่มความแม่นยำ entity naming

**Bug fixes:**
- `kg_extraction()` line 404-405 เรียก `fetch_section_chunks()` ไม่ส่ง path → ลบทิ้ง (ใช้ `kg_extraction_parallel` แทน)
- `kg_extraction()` อ้าง `transformer` global ที่ไม่มี

**Pipeline orchestrator** (`offline/pipeline.py`):
```
for ticker in tickers:
    filings = ingest.download(ticker, "10-K")
    for filing in filings:
        sections = preprocess.clean_and_extract(filing)
        for section_name, content in sections.items():
            chunks = chunker.split(content)
            entities = ner.extract(chunks)           # GLiNER
            graph_docs = kg_extract.extract(chunks)  # DeepSeek
            validated = kg_validate.validate(graph_docs)
            kg_store.save_batch(validated)
```

### Phase 4: Online -- Graph QA + Agents
**Refactor from:** `test_grapQA.py` (richer prompt, 164 lines) → `online/graph_qa.py`

**NEW modules to build:**
1. **`fundamental_agent.py`**: Self-RAG pattern (query → evaluate relevance → re-query if insufficient), guided by investment thesis (Fisher, Lynch, Porter) as prompt templates
2. **`news_agent.py`**: merge `test_news_fetch.py` + `test_news_retrive.py` + add FinBERT/LLM sentiment analysis
3. **`manager_agent.py`**: Plan-and-Solve prompting, task routing to sub-agents, Reflexion loop, scoring/ranking

Prompt templates → extract to `online/prompts/` as .txt files

### Phase 5: CLI + End-to-End Pipeline
**NEW:** `cli.py` using Typer

```bash
semigraph offline ingest --tickers NVDA,INTC,TSM
semigraph offline preprocess --ticker NVDA
semigraph offline build-kg --ticker NVDA --sections "Item 1,Item 1A"
semigraph offline full-pipeline --config config/default.yaml

semigraph query "What are NVDA's risk factors?"
semigraph analyze --ticker NVDA

semigraph eval financebench
semigraph eval ragas --compare graphrag,vectorrag
semigraph diagnostic
```

### Phase 6: Evaluation Framework
**NEW modules:**
1. **`evaluation/financebench.py`**: load `financebench_open_source.jsonl`, run questions through GraphQA, compare with gold answers
2. **`evaluation/ragas_eval.py`**: RAGAS metrics (context precision/recall, answer relevance), LLM-as-a-Judge, GraphRAG vs VectorRAG comparison
3. **`evaluation/backtesting.py`**: Spearman rank correlation vs analyst consensus + historical return simulation

---

## Existing Code Mapping

| Existing Script | Action | Target Module |
|---|---|---|
| `test_fundamental_fetch.py` | REFACTOR | `offline/ingest.py` |
| `test_clean.py` | REFACTOR | `offline/preprocess.py` |
| `test_KG_custom_chain.py` | SPLIT into 4 | `kg_extract.py`, `kg_store.py`, `ontology/nodes.py`, `ontology/schema.py` |
| `test_grapQA.py` | REFACTOR | `online/graph_qa.py` |
| `test_news_fetch.py` | REFACTOR | `online/news_agent.py` |
| `test_news_retrive.py` | MERGE into | `online/news_agent.py` |
| `test_diagnostic.py` | REFACTOR | `utils/neo4j_diagnostic.py` |
| `test_KG_extactor.py` | DEPRECATE | Keep as reference |
| `test_graph_qa.py` | DEPRECATE | Merged into graph_qa.py |
| `test_deepseek_api.py` | DEPRECATE | One-off test |
| `test_deepseek_emb.py` | DEPRECATE | Superseded |
| `test_embedding.py` | DEPRECATE | Superseded |
| `test_llm_api.py` | DEPRECATE | One-off test |
| `tt.py` | DELETE | Empty file |

---

## What Needs to Be Built from Scratch

1. **GLiNER NER module** -- entity extraction ก่อน LLM (ลด cost + เพิ่มคุณภาพ)
2. **Manager Agent** -- Plan-and-Solve + Reflexion loop
3. **Fundamental Agent** -- Self-RAG + Investment Thesis frameworks
4. **Sentiment Analysis** -- FinBERT หรือ LLM-based sentiment scoring
5. **Vector Embeddings** -- Neo4j vector index สำหรับ hybrid search
6. **Evaluation Pipeline** -- FinanceBench + RAGAS + Backtesting ทั้งหมด
7. **CLI** -- Typer-based command interface
8. **Pipeline Orchestrator** -- end-to-end offline pipeline
9. **Proper Logging** -- แทน print() ทั้งหมด
10. **Tests** -- unit tests สำหรับ preprocess, kg_validate, graph_qa

---

## Decisions Made
- **Start with Phase 0-1** (Foundation + Ingest/Preprocess) ก่อน แล้วค่อยขยายต่อ
- **Multi-Agent framework: LangGraph** (LangChain ecosystem, graph-based orchestration, รองรับ Self-RAG/Reflexion)

---

## Verification Plan

1. **Phase 0-1**: รัน `semigraph offline ingest --tickers GOOGL` แล้วดูว่า filings download ลง `data/raw/` สำเร็จ จากนั้น `semigraph offline preprocess --ticker GOOGL` แล้วดูว่า sections ใน `data/processed/` ถูกต้อง
2. **Phase 2-3**: รัน `semigraph offline build-kg --ticker GOOGL --sections "Item 1"` แล้วตรวจ Neo4j ด้วย diagnostic tool ว่ามี nodes/relationships ตาม ontology
3. **Phase 4**: รัน `semigraph query "What are Alphabet's main business segments?"` แล้วตรวจว่าได้คำตอบจาก graph
4. **Phase 5**: รัน `semigraph offline full-pipeline` end-to-end สำหรับ 1 ticker
5. **Phase 6**: รัน `semigraph eval financebench` ดู accuracy scores
