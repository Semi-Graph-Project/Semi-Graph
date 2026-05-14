# SemiGraph — GraphRAG-Enhanced Multi-Agent System for Semiconductor Stock Analysis

Senior thesis project — King Mongkut's University of Technology North Bangkok (KMUTNB)

> **Position:** Agentic Heterogeneous RAG vs Homogeneous Vector RAG — combining Knowledge Graph, vector retrieval, structured numeric data, and news into a single agentic pipeline. The contribution is engineering, not novel finance insights.

---

## Overview

SemiGraph supports fundamental analysis of semiconductor stocks (NVDA / AMD / MU / ASML) by routing queries to four heterogeneous data sources through an agent. Each source plays to its strength:

```
                       User Query
                           │
                           ▼
                    ┌──────────────┐
                    │  Agent       │  (LangGraph + ReAct + Reflection)
                    │  DeepSeek-V3 │
                    └──────┬───────┘
                           │ routes via tool selection
        ┌──────────────────┼──────────────────┬─────────────────┐
        ▼                  ▼                  ▼                 ▼
  ┌──────────┐     ┌──────────────┐    ┌─────────────┐   ┌────────────┐
  │ graph_   │     │ vector_      │    │ financial_  │   │ news_      │
  │ search   │     │ search       │    │ query       │   │ search     │
  │ (PPR)    │     │ (cosine)     │    │ (SQL)       │   │ (Finnhub)  │
  └────┬─────┘     └──────┬───────┘    └──────┬──────┘   └─────┬──────┘
       ▼                  ▼                   ▼                ▼
   Neo4j KG          Neo4j vector         PostgreSQL       Finnhub API
   (Entity rels)     index (chunks)       (financials)     (news cache)
```

The 3-config ablation (Phase E):
1. **Vanilla Vector RAG** — chunks only, no graph
2. **Agentic Vector RAG** — agent + chunks
3. **Agentic Heterogeneous RAG** — agent + all 4 sources (this work)

---

## Ontology — FinReflectKG

The graph schema follows **FinReflectKG** (Arun et al., ICAIF '25) — 24 entity types, 29 relationship types, two-layer design:

- **Domain layer**: business entities + relationships (companies, products, risks, segments...)
- **Provenance layer**: Document → Section → Chunk → Entity (with `MENTIONS` linking back)

Single source of truth: [`src/semigraph/ontology/schema.py`](src/semigraph/ontology/schema.py) — `NODE_CATALOG`, `RELATIONSHIP_CATALOG`, `SECTION_CONFIG`. Never hard-code entity/rel types at call sites — extend the catalog instead.

### Sample entity types
| Type | Examples |
|---|---|
| `ORG` | nvidia, amd, micron technology |
| `PRODUCT` | h100 gpu, blackwell architecture, epyc |
| `RISK_FACTOR` | china export controls, supply chain disruption |
| `FIN_METRIC` | revenue, gross margin, r&d expenses |
| `GPE` | china, taiwan, united states |
| `MACRO_CONDITION` | inflation, climate change |
| `SEGMENT` | data center, gaming, automotive |

### Sample relationship types
```
COMPETES_WITH    DEPENDS_ON    SUPPLIES        OPERATES_IN
PRODUCES         FACES         IMPACTED_BY     NEGATIVELY_IMPACTS
DISCLOSES        SUBJECT_TO    HAS_STAKE_IN    SYNONYM_OF (Phase B2)
```

---

## Project Structure

```
semigraph/
├── src/semigraph/
│   ├── config.py             # Config loader (YAML + .env, lru_cache singleton)
│   ├── connections.py        # Neo4j + DeepSeek + embedding-model factories
│   ├── ontology/
│   │   ├── nodes.py          # Pydantic models: GraphNode, GraphRelationship
│   │   └── schema.py         # OntologyRegistry — single source of truth
│   ├── offline/
│   │   ├── ingest.py         # SEC EDGAR download
│   │   ├── preprocess.py     # HTML → Markdown → section extraction
│   │   ├── chunker.py        # Token-aware text splitter → List[Chunk]
│   │   ├── kg_extract.py     # Single-call DeepSeek extraction (entities + rels)
│   │   ├── kg_store.py       # KGStore — idempotent MERGE via APOC
│   │   ├── pipeline.py       # Orchestrator: chunk → extract → store, with checkpoint
│   │   ├── embeddings.py     # BGE model wrapper (lazy load + L2-norm + singleton)
│   │   ├── embed_chunks.py   # Phase B1 — chunk embedding pipeline
│   │   ├── embed_nodes.py    # Phase B2 step 1 — entity embedding pipeline
│   │   ├── synonymy.py       # Phase B2 step 2-3 — composite-rule synonymy edges
│   │   ├── specificity.py    # Phase B3 — Node Specificity (1/log(degree+1))
│   │   └── embed_triples.py  # Phase C1b+ — relationship triple embedding (HippoRAG v2)
│   └── online/
│       ├── seed.py           # Phase C1a (Query-to-Node) + C1b+ (Query-to-Triple)
│       └── ppr.py            # Phase C1b — Personalized PageRank walker (GDS)
├── scripts/
│   ├── run_offline_pipeline.py   # CLI for KG extraction
│   ├── embed_chunks.py           # CLI for Phase B1
│   ├── embed_nodes.py            # CLI for Phase B2 step 1
│   ├── build_synonymy.py         # CLI for Phase B2 step 2-3 (--dry-run, --show-pairs)
│   ├── compute_specificity.py    # CLI for Phase B3 (top-hubs/top-leaves preview)
│   └── embed_triples.py          # CLI for Phase C1b+ (relationship triple embedding)
├── tests/
│   └── test_ontology.py          # 61 unit tests, no external deps
├── config/
│   └── default.yaml              # Operational config (chunker, llm, embeddings)
├── docker-compose.yml            # Neo4j 5.26 + APOC + GDS local
└── data/
    ├── raw/                      # Downloaded 10-K filings (git-ignored)
    ├── processed/                # Extracted sections + .checkpoint.json (git-ignored)
    └── neo4j/                    # Neo4j volume (git-ignored)
```

---

## Setup

### 1. Environment + dependencies

```bash
git clone https://github.com/JohnTagarian/semigraph.git
cd semigraph
conda create -n senior_project python=3.10
conda activate senior_project
pip install -e .
```

### 2. Secrets (`.env`)

```env
DEEPSEEK_API_KEY=sk-...
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
EDGAR_EMAIL=your@email.com
EDGAR_ORGANIZATION=YourOrg
```

### 3. Start Neo4j (Docker)

```bash
docker compose up -d           # starts Neo4j 5.26 + APOC + GDS
# Browser: http://localhost:7474
docker compose logs -f neo4j   # tail logs
docker compose down            # stop (data persists in data/neo4j/)
```

Tx log policy is set aggressive in `docker-compose.yml` — logs cap at ~50 MB instead of 250 MB/filing.

### 4. Verify

```bash
pytest tests/ -v               # 61 unit tests, ~0.1s
python scripts/test_neo4j_connection.py   # smoke test connectivity
```

---

## Running the Offline Pipeline

```bash
# 1. Ingest + preprocess (downloads from SEC EDGAR)
python scripts/test_e2e_ingest_preprocess.py

# 2. KG extraction (entities + relationships → Neo4j)
#    Single filing
python scripts/run_offline_pipeline.py --ticker NVDA --fiscal-year 2026 --workers 12
#    All filings discovered under data/processed/
python scripts/run_offline_pipeline.py --workers 12
#    Force re-run (ignore checkpoint)
python scripts/run_offline_pipeline.py --no-resume

# 3. Phase B1 — Chunk embeddings + vector index
python scripts/embed_chunks.py
#    --force re-embeds even if embedding already set

# 4. Phase B2 — Entity embeddings + synonymy edges
python scripts/embed_nodes.py
python scripts/build_synonymy.py --dry-run --show-pairs 30   # preview first
python scripts/build_synonymy.py                              # write edges

# 5. Phase B3 — Node Specificity (1/log(degree+1)) on all entities
python scripts/compute_specificity.py

# 6. Phase C1b+ — Triple embeddings for Query-to-Triple linker (HippoRAG v2)
python scripts/embed_triples.py
#    --force re-embeds informative-relationship triples even if already set

# 7. Phase C1 — Online retrieval (smoke test)
python -m semigraph.online.seed     # both modes: query_to_seeds + query_to_triple_seeds
python -m semigraph.online.ppr      # full pipeline: seeds → PPR → ranked entities
```

The pipeline is **idempotent**: re-running skips chunks/entities that already have an embedding, and the checkpoint file (`data/processed/.checkpoint.json`) marks completed filings.

---

## Current Graph Snapshot (9 filings)

| Asset | Count | Notes |
|---|---|---|
| Documents | 9 | NVDA × 3, AMD × 3, MU × 3 (FY2023–2026) |
| Sections | 27 | Item 1, 1A, 7 per filing |
| Chunks | 528 | 4,500 chars / 600 overlap |
| **Entities** | **3,620** | post-MERGE, after pronoun cleanup |
| **Domain rels** | **4,290** | 22 distinct types |
| Provenance rels | ~7,700 | MENTIONS, HAS_CHUNK, HAS_SECTION |
| **SYNONYM_OF edges** | **98** | composite rule scoring (legal_suffix, acronym, plural, semantic) |
| Chunk embeddings | 528 × 768 | BAAI/bge-base-en-v1.5, L2-normalized |
| Entity embeddings | 3,620 × 768 | same model |
| **Triple embeddings** | **4,278 × 768** | `"<head> <rel humanized> <tail>"` on informative rels (HippoRAG v2) |
| Vector indexes | 2 | `chunk_embedding`, `entity_embedding` (cosine + HNSW). Triple search is in-memory numpy (Neo4j requires explicit `:TYPE` per index — 21 indexes not worth it at this scale). |
| **Node specificity** | **3,620** | `1/log(degree+1)`, range [0.158, 1.443] |
| **Disk footprint** | **~103 MB** | graph data + tx logs + 3 embedding layers + GDS metadata |

### Multi-hop benchmark (5/5 pass)

| Metric | Result |
|---|---|
| Avg shortest path | 3.16 hops (cross-type) |
| Cross-filing bridges | 13 universal + 91 strong (≥6 filings) |
| Defense queries (slides 19-21) | 4/4 pass with ≥3 results each |
| Synonym expansion impact | AMD reach +34%, NVIDIA +15% |

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM (extraction + agent) | DeepSeek-V3 (`deepseek-chat`) via OpenAI-compatible API |
| Embedding model | `BAAI/bge-base-en-v1.5` (768-dim, MTEB 63.5, ~1.5 GB RAM) |
| Knowledge graph | Neo4j 5.26 Community + APOC + GDS (local Docker) |
| Vector retrieval | Neo4j vector index (HNSW + cosine) |
| Agent orchestration | LangChain + LangGraph (Phase D — planned) |
| Numeric data | PostgreSQL + SEC XBRL Frames API (Phase C3 — planned) |
| News | Finnhub API + cached embeddings (Phase C4 — planned) |
| Data models | Pydantic v2 |
| String matching | rapidfuzz (synonymy hybrid scoring) |
| Concurrency | ThreadPoolExecutor with tenacity retry |
| Config | YAML + python-dotenv |
| Testing | pytest (61 tests, 0 external deps) |

---

## Progress

### Phase A — Offline KG Pipeline ✅

- [x] Config system + Neo4j/LLM/embedding factories
- [x] Ontology (FinReflectKG: 24 entity types, 29 rel types)
- [x] SEC EDGAR ingest + preprocess (9 filings)
- [x] Chunker (token-aware, 4,500/600)
- [x] **KG extraction** — single-call DeepSeek (entities + relationships in one call)
- [x] **KG store** — idempotent MERGE with APOC dynamic relationship type
- [x] **Pipeline orchestrator** — parallel chunk processing, checkpoint, continue-on-error
- [x] Pronoun blacklist + ORG/COMP collision merge (graph cleanup)
- [x] Tx log retention policy (aggressive — saves 99% disk vs default)

### Phase B — Embeddings + Synonymy + Specificity ✅

- [x] **B1** Chunk embeddings + Neo4j vector index (528 chunks, ~5 min run)
- [x] **B2** Entity embeddings (3,620 entities, ~80s run)
- [x] **B2** Synonymy edges via 4 composite rules (legal_suffix, acronym, plural, semantic + digit gate)
- [x] **B3** Node Specificity (`1/log(degree+1)`) — range [0.158, 1.443], single Cypher write

### Phase C — Online Tools (WIP)

- [x] **C1a** `query_to_seeds` — Query-to-Node linker via `entity_embedding` index ([seed.py](src/semigraph/online/seed.py))
- [x] **C1b** `run_ppr` — Personalized PageRank via GDS named projection ([ppr.py](src/semigraph/online/ppr.py))
- [x] **C1b+** `query_to_triple_seeds` — Query-to-Triple linker (HippoRAG v2 Table 4: +12.5% R@5 over Query-to-Node) via in-memory triple cosine search ([seed.py](src/semigraph/online/seed.py))
- [ ] **C1c** entity → chunk mapping with SYNONYM_OF dedup → closes `graph_search` tool
- [ ] **C2** `vector_search` — top-k chunks via Neo4j vector index (baseline for ablation)
- [ ] **C3** `financial_query` — PostgreSQL + SEC XBRL ingestion
- [ ] **C4** `news_search` — Finnhub fetch + cached embeddings

### Phase D — Agent Core (planned)

- [ ] LangGraph state machine + ReAct loop
- [ ] Tool routing logic (query → which of the 4 tools)
- [ ] Reflection layer (verify answer against retrieved evidence)

### Phase E — Evaluation (planned)

- [ ] Layer 1 — Multi-Judge LLM ensemble (Claude + GPT-4) for correctness
- [ ] Layer 2 — RAGAS metrics (Context Precision/Recall, Answer Relevance, Faithfulness)
- [ ] Scale corpus to 28 companies × 3 years for final evaluation

---

## Reference Documents

### Inside repo
- [docs/offline_pipeline.md](docs/offline_pipeline.md) — flow diagrams + module responsibilities
- [docs/plan.md](docs/plan.md) — implementation plan, ADRs, status
- [CLAUDE.md](CLAUDE.md) — project conventions for Claude Code (response style, architecture rules)

### Obsidian Vault (`/home/kantinan/Documents/Obsidian Vault/Agentic GraphRAG/`)
- `00_INDEX.md` — **single canonical index** of the vault (start here)
- `Proposal_v2.md` — full thesis proposal
- `PPR_explain.md` — Personalized PageRank algorithm walkthrough
- `Code_Explained_pipeline.md` — Phase A pipeline.py deep-dive
- `Code_Explained_Phase_B1_ChunkEmbedding.md` — Phase B1 implementation notes
- `Code_Explained_Phase_B2_Synonymy.md` — Phase B2 with iteration history
- `Code_Explained_specificity.md` — Phase B3 deep-dive
- `Coach_Phase_C1b_PPR_walker.md` — coaching guide used to implement C1b (extended with HippoRAG v1/v2 comparison)
- `Graph_MultiHop_Benchmark_Report.md` — current graph quality benchmark
- `Slide_walkthroght.md` — defense presentation guide
- `How_to_Read_FirstPrinciple_Notes.md` — meta-guide for `Code_Explained_*` / `Coach_*` notes

### Reference papers (`/home/kantinan/Documents/book/paper/project/`)
- `Hippo_rag.pdf` — HippoRAG (NeurIPS '24) — PPR retrieval + Node Specificity (foundation of graph_search)
- `finreflect.pdf` — FinReflectKG (ICAIF '25) — ontology adopted in `schema.py`
- `2404.16130v2.pdf` — Microsoft GraphRAG
- `2005.11401v4.pdf` — original RAG (Lewis et al., NeurIPS '20)

---

## Known Limitations

- **ASML** files Form 20-F (foreign private issuer), not 10-K. Section patterns don't apply — requires a separate 20-F parser. Excluded from current 9-filing corpus.
- **AMD / MU Item 10–11** use "incorporation by reference" to proxy statement (DEF 14A). Executive data is not embedded in the 10-K body — extraction yields only the reference sentence.
- **Synonymy at scale** — composite rules tested on 977 entities (subset of 3,620 after type filter). At 28-company scale, audit `--dry-run` output before writing edges; stock-ticker style abbreviations (e.g. `qcom` ↔ `qualcomm`) may not satisfy the strict acronym rule.
- **Specificity-weighted teleport** — GDS `gds.pageRank.stream` only supports uniform `sourceNodes`. The walker treats all seeds equally; specificity is used during seed selection (C1a) but not as a teleport vector. Workarounds (seed duplication, custom Cypher PPR) are deferred to ablation experiments.
- **Alias dedup** — multiple aliases of the same entity (e.g. `amd` / `advanced micro devices` / `advanced micro devices, inc.`) can occupy adjacent top-k slots. Will be resolved in **C1c** via `SYNONYM_OF` cluster collapse before chunk mapping.
- **GDS deprecations** — `id(n)` (use `elementId`) and `gds.graph.project.cypher` (use `gds.graph.project` aggregation form) emit warnings on Neo4j 5.26; both still functional. Migration tracked as future work.

---

## Common Commands

```bash
# Tests (no external deps)
pytest tests/ -v

# Run a specific test
pytest tests/test_ontology.py::TestGraphNode -v

# Neo4j control
docker compose up -d         # start
docker compose stop          # stop (keep data)
docker compose down          # remove containers (keep data via volumes)
docker compose logs -f neo4j # tail logs

# Connectivity smoke test
python scripts/test_neo4j_connection.py

# Inspect graph
docker exec semigraph-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC;"
```
