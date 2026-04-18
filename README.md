# SemiGraph — GraphRAG-Enhanced Multi-Agent System for Semiconductor Stock Analysis

Senior thesis project — King Mongkut's University of Technology North Bangkok (KMUTNB)

---

## Overview

SemiGraph combines **Knowledge Graph** (Neo4j) with **Retrieval-Augmented Generation** (RAG) to support fundamental analysis of semiconductor stocks. Instead of feeding raw 10-K text directly to an LLM, the system first extracts structured relationships from SEC filings and stores them in a graph database. An agentic layer then routes analyst queries to the appropriate data source.

```
User Query
    │
    ▼
┌─────────┐
│  Agent  │  (LangGraph + DeepSeek)
└────┬────┘
     │ routes to
     ├──────────────────────────────────────┐
     ▼                                      ▼
┌──────────┐   ┌──────────────────────┐   ┌───────────┐
│ Neo4j KG │   │ SQL DB               │   │ News API  │
│          │   │                      │   │           │
│ Who      │   │ Revenue, EPS,        │   │ Real-time │
│ competes │   │ Margins, Capex,      │   │ events &  │
│ with who │   │ R&D spend            │   │ sentiment │
│ Supply   │   │ (structured numbers) │   │           │
│ chains   │   └──────────────────────┘   └───────────┘
│ Risks    │
└──────────┘
```

---

## Ontology Design

The knowledge graph is designed around **Porter's 5 Forces** and **Fisher's 15 Points** — two classic frameworks for fundamental investing.

### Node Types (10)

| Node | Description | Example |
|------|-------------|---------|
| `Company` | Legal corporate entity | NVIDIA Corporation |
| `BusinessSegment` | GAAP-reportable operating division | Data Center, Gaming |
| `Product` | Named product or platform | H100 GPU, CUDA |
| `Technology` | Proprietary technology or architecture | Hopper, NVLink |
| `GeographicMarket` | Country or region | Greater China, EMEA |
| `Industry` | Market sector (shared across companies) | Semiconductor |
| `RiskFactor` | Material risk from Item 1A | China export control restrictions |
| `Executive` | Named officer or board director | Jensen Huang (CEO) |
| `StrategicInitiative` | R&D program, acquisition, partnership | Blackwell Architecture Development |
| `FiscalYear` | Temporal anchor node | 2024, 2025 |

### Relationship Types (15)

```
Porter's 5 Forces          Fisher's 15 Points
─────────────────          ──────────────────
COMPETES_WITH              HAS_EXECUTIVE
SUPPLIED_BY                PURSUES  (StrategicInitiative)
SELLS_TO                   INVOLVES (Technology)
SUBSTITUTED_BY             TARGETS  (BusinessSegment)

Business Structure         Risk
──────────────────         ────
HAS_SEGMENT                HAS_RISK
OFFERS                     THREATENS
BUILT_ON                   RELATED_TO
OPERATES_IN
IN_INDUSTRY
```

---

## Project Structure

```
semigraph/
├── src/semigraph/
│   ├── config.py             # Config loader (YAML + .env)
│   ├── connections.py        # Neo4j + LLM factory functions
│   ├── ontology/
│   │   ├── nodes.py          # Pydantic models for LLM extraction
│   │   └── schema.py         # OntologyRegistry — single source of truth
│   ├── offline/
│   │   ├── ingest.py         # SEC EDGAR download
│   │   ├── preprocess.py     # HTML → Markdown → section extraction
│   │   ├── chunker.py        # Token-aware text splitter → List[Chunk]
│   │   └── kg_extract.py     # Stage 1: GLiNER NER | Stage 2: DeepSeek relationships (WIP)
│   └── online/               # (WIP) agentic query layer
├── tests/
│   └── test_ontology.py      # 52 unit tests (zero external dependencies)
├── scripts/
│   └── test_e2e_ingest_preprocess.py  # E2E pipeline validation
├── config/
│   └── default.yaml          # Operational config
└── data/
    ├── raw/                  # Downloaded 10-K filings (git-ignored)
    └── processed/            # Extracted sections (git-ignored)
```

---

## Setup

```bash
# 1. Clone and create environment
git clone https://github.com/JohnTagarian/semigraph.git
cd semigraph
conda create -n senior_project python=3.10
conda activate senior_project

# 2. Install package
pip install -e .

# 3. Configure secrets
cp .env.example .env
# Edit .env and fill in your keys

# 4. Verify
python -m pytest tests/ -v
```

### `.env` required keys

```env
DEEPSEEK_API_KEY=sk-...
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
EDGAR_EMAIL=your@email.com
EDGAR_ORGANIZATION=YourOrg
```

---

## Running the Pipeline

```bash
# Download + preprocess 10-K filings (NVDA, ASML, MU, AMD)
conda run -n senior_project python scripts/test_e2e_ingest_preprocess.py
```

Output structure:
```
data/processed/
  NVDA/
    FY2024/  full_10K.md  Item_1.md  Item_1A.md  Item_7.md  Item_10.md ...
    FY2025/  ...
    FY2026/  ...
  AMD/
    FY2024/  ...
  MU/
    FY2023/  ...
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| LLM | DeepSeek (`deepseek-chat`) via OpenAI-compatible API |
| Orchestration | LangChain + LangGraph |
| Knowledge Graph | Neo4j |
| Data Models | Pydantic v2 |
| SEC Data | `sec-edgar-downloader` |
| HTML → Markdown | `html2text` |
| NER (Entity Detection) | `GLiNER` (`urchade/gliner_medium-v2.1`) |
| Config | YAML + `python-dotenv` |
| Testing | pytest |

---

## Progress

### Done

- [x] **Package scaffold** — `src/semigraph/` with proper `pyproject.toml`
- [x] **Config system** — unified loader from `config/default.yaml` + `.env`, `lru_cache` singleton
- [x] **Connections** — factory functions for Neo4j and DeepSeek LLM
- [x] **Ontology** — `OntologyRegistry` with full NODE_CATALOG, RELATIONSHIP_CATALOG, SECTION_CONFIG
- [x] **Pydantic models** — `GraphNode` (auto-injects `name=id` for Neo4j label display), `GraphRelationship`, `GraphExtractionResult`
- [x] **Unit tests** — 52 tests, 0 external dependencies, all passing
- [x] **SEC ingest** — batch download with rate limiting, RSS feed check
- [x] **Preprocess pipeline** — HTML → Markdown → section extraction with readable output (`TICKER/FY{YEAR}/Item_X.md`)
- [x] **Regex fix** — handle `html2text` backslash-escaped dots (`ITEM 7\.`) in AMD-style 10-Ks
- [x] **E2E validation** — 9 filings processed (NVDA FY2024–2026, MU FY2023–2025, AMD FY2024–2026)
- [x] **Chunker** — `RecursiveCharacterTextSplitter` (4,500 chars / 600 overlap) → `Chunk` Pydantic model with deterministic `chunk_id` and provenance metadata; 96–121 chunks per filing
- [x] **GLiNER NER (Stage 1)** — local entity detection (`urchade/gliner_medium-v2.1`), section-aware label mapping derived from `OntologyRegistry`, deduplication by `(text, label)`

### In Progress

- [ ] **Step 3 — KG Extraction pipeline**
  - [x] `offline/chunker.py` — token-aware text splitter per section
  - [ ] `offline/kg_extract.py` — Stage 2: DeepSeek relationship extraction → `GraphExtractionResult`
  - [ ] `offline/kg_store.py` — Neo4j MERGE upsert (idempotent)

### Planned

- [ ] **Step 4 — Offline orchestrator** (`offline/pipeline.py`)
- [ ] **Step 5 — CLI** (`cli.py` with Typer)
- [ ] **Step 6 — Online agents** (LangGraph routing: Neo4j / SQL / News)
- [ ] **Step 7 — Evaluation framework** (Competency Questions, graph coverage metrics)

---

## Known Limitations

- **ASML** — files Form 20-F (foreign private issuer), not 10-K. Section patterns are 10-K specific and do not apply. Requires separate 20-F parser.
- **AMD / MU Item 10–11** — use "incorporation by reference" to proxy statement (DEF 14A). Executive data is not embedded in the 10-K itself; extraction yields only the reference sentence.
