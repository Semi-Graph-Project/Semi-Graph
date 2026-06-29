# SemiGraph — GraphRAG-Enhanced Multi-Agent System for Semiconductor Stock Analysis

Senior thesis project — King Mongkut's University of Technology North Bangkok (KMUTNB)

> **Position:** Agentic Heterogeneous RAG vs Homogeneous Vector RAG — combining Knowledge Graph, vector retrieval, structured numeric data, and news into a single agentic pipeline. The contribution is engineering, not novel finance insights.

---

## Overview

SemiGraph supports fundamental analysis of semiconductor stocks by routing queries to heterogeneous data sources through an agent. The thesis core remains NVDA / AMD / MU / ASML, while the current pilot corpus has expanded through the reusable onboarding runner in `scripts/pilot.py`.

Current config corpus tickers: AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN.

Each source plays to its strength:

```
                       User Query
                           │
                           ▼
                    ┌──────────────┐
                    │  Agent       │  (LangGraph + ReAct + Reflection)
                    │  DeepSeek    │
                    └──────┬───────┘
                           │ routes via tool selection
        ┌──────────────────┼──────────────────┬─────────────────┐
        ▼                  ▼                  ▼                 ▼
  ┌──────────┐     ┌──────────────┐    ┌─────────────┐   ┌────────────┐
  │ graph_   │     │ vector_      │    │ financial_  │   │ news_      │
  │ search   │     │ search       │    │ search      │   │ search     │
  │ (PPR)    │     │ (cosine)     │    │ (Finnhub)   │   │ (Finnhub)  │
  └────┬─────┘     └──────┬───────┘    └──────┬──────┘   └─────┬──────┘
       ▼                  ▼                   ▼                ▼
   Neo4j KG          Neo4j vector         Finnhub API      Finnhub API
   (Entity rels)     index (chunks)       (financials)     (company news)
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
│   ├── online/
│   │   ├── seed.py           # Phase C1a (Query-to-Node) + C1b+ (Query-to-Triple)
│   │   ├── ppr.py            # Phase C1b — Personalized PageRank walker (GDS)
│   │   ├── graph_search.py   # Phase C1c — full graph_search tool (closes the loop)
│   │   ├── vector_search.py  # Phase C2 — top-k cosine over chunk_embedding index
│   │   ├── hybrid_search.py  # Phase C2+ — RRF (k=60) fusion of vector + graph
│   │   ├── financial_search.py # Phase C3 — Finnhub financials/quote (Protocol pattern)
│   │   ├── news_search.py    # Phase C4 — Finnhub company news (90-day window)
│   │   ├── _ticker.py        # Shared ticker resolution (regex + LLM expansion)
│   │   └── query_expand.py   # Phase T — optional LLM query expansion for entity hints
│   └── agent/                # Phase D — LangGraph agent (Plan-then-ReAct)
│       ├── state.py          # AgentState TypedDict (total=False)
│       ├── graph.py          # StateGraph builder (7-node conditional graph)
│       ├── nodes.py          # plan/tool_select/execute/observe/reflect/advance_subquery/synthesize
│       ├── tools.py          # TOOL_SCHEMAS + shared RETRIEVERS dispatch
│       ├── ws.py             # LangGraph dev entrypoint
│       └── prompts.py        # planner/router/observe/reflect/synthesize prompts
├── scripts/
│   ├── pilot.py                  # End-to-end ticker onboarding + metrics + config sync
│   ├── run_offline_pipeline.py   # CLI for KG extraction
│   ├── embed_chunks.py           # CLI for Phase B1
│   ├── embed_nodes.py            # CLI for Phase B2 step 1
│   ├── build_synonymy.py         # CLI for Phase B2 step 2-3 (--dry-run, --show-pairs)
│   ├── compute_specificity.py    # CLI for Phase B3 (top-hubs/top-leaves preview)
│   ├── embed_triples.py          # CLI for Phase C1b+ (relationship triple embedding)
│   ├── compare_linkers.py        # Proxy-metric eval: Query-to-Node vs Query-to-Triple (12 queries)
│   ├── run_agent_e2e_probe.py    # Multi-query agent smoke test against real graph
│   ├── run_agent_trace.py        # Colored Phase D trace runner with real LLM + CLI query
│   ├── evaluate_retrieval_quality.py # Phase T benchmark: vector vs graph vs hybrid
│   ├── trace_retrieval_bottlenecks.py # Phase T seed/PPR/chunk trace helper
│   └── test_graph_search.py      # End-to-end validation of graph_search (17 queries)
├── analytics/                # Reports from validation scripts (Markdown)
│   ├── linker_comparison.md          # compare_linkers.py output
│   ├── graph_search_validation.md    # test_graph_search.py output
│   └── *_pilot_metrics.csv           # per-chunk pilot extraction metrics
├── tests/
│   ├── test_ontology.py          # 61 unit tests, no external deps
│   ├── test_agent_nodes.py       # node-level regression tests
│   ├── test_agent_graph_phase_d.py # graph-level Phase D integration tests
│   └── test_kg_store_reset.py    # KGStore filing reset regression tests
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
pytest tests/ -v               # unit tests, no external services
python scripts/test_neo4j_connection.py   # smoke test connectivity
```

---

## Running the Offline Pipeline

```bash
# 0. Pilot runner (recommended for onboarding a new ticker end-to-end)
python scripts/pilot.py --ticker KLAC --workers 8
#    Use existing raw/processed files but re-run extraction + embeddings
python scripts/pilot.py --ticker KLAC --skip-download --skip-preprocess
#    Sync config/default.yaml tickers from Neo4j only
python scripts/pilot.py --sync-only

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

# 7. Phase C1 — Online retrieval (smoke tests)
python -m semigraph.online.seed          # both modes: query_to_seeds + query_to_triple_seeds
python -m semigraph.online.ppr           # seeds → PPR → ranked entities
python -m semigraph.online.graph_search  # full pipeline: seeds → PPR → cluster → chunks

# 8. Phase C1c — Validation reports (regenerate Markdown in analytics/)
python scripts/compare_linkers.py        # Query-to-Node vs Query-to-Triple on 12 queries
python scripts/test_graph_search.py      # graph_search() end-to-end on 17 queries
```

The embedding/checkpoint steps are **rerun-safe**: re-running skips chunks/entities that already have embeddings, and `data/processed/.checkpoint.json` marks completed filings. If extraction logic, chunk IDs, or ontology output changes, clear the intended ticker/filing scope before re-ingesting so stale graph evidence does not remain beside the new run.

`scripts/pilot.py` is the preferred onboarding wrapper for new tickers: it downloads the latest three 10-K filings, preprocesses sections, runs KG extraction, embeds chunks/entities/triples, recomputes specificity, verifies Neo4j counts, writes `analytics/{ticker}_pilot_metrics.csv`, then syncs `config/default.yaml` tickers from the graph.

---

## Current Corpus Snapshot

| Asset | Count | Notes |
|---|---|---|
| Config corpus | 14 tickers | AMAT, AMD, AMKR, AVGO, COHR, ENTG, INTC, KLAC, LRCX, MU, NVDA, QCOM, RMBS, TXN |
| Pilot metric files | 10 tickers | AMAT, AMKR, AVGO, COHR, ENTG, KLAC, LRCX, QCOM, RMBS, TXN |
| Pilot ticker-year runs | 30 | latest 3 filings per pilot ticker |
| Pilot chunks extracted | 1,605 | all rows in `analytics/*_pilot_metrics.csv` are `status=ok` |
| KLAC pilot | 202 chunks | FY2023, FY2024, FY2025; latest downloaded KLAC filing in this run is not FY2026 |
| Original baseline snapshot | 9 filings | NVDA × 3, AMD × 3, MU × 3; previous measured graph baseline before pilot expansion |

The exact Neo4j graph counts depend on the live local database and repeated pilot runs. Treat the CSV counts above as extraction-run metrics, not de-duplicated graph totals.

### Last Measured Graph Baseline (9 filings)

| Asset | Count | Notes |
|---|---|---|
| Documents | 9 | NVDA × 3, AMD × 3, MU × 3 |
| Chunks | 528 | 4,500 chars / 600 overlap |
| Entities | 3,620 | post-MERGE, after pronoun cleanup |
| Domain rels | 4,290 | 22 distinct types |
| SYNONYM_OF edges | 98 | composite rule scoring |
| Triple embeddings | 4,278 × 768 | informative relationships only |

### Retrieval Benchmarks

| Metric | Result |
|---|---|
| Synthesized dev set | Graph Hit@5 38/50 vs Vector Hit@5 33/50; Graph Avg Recall@5 0.492 vs Vector 0.369 |
| Holdout set | Hybrid Avg Recall@5 0.450, Graph 0.420, Vector 0.390 |
| Linker comparison | Query-to-Triple improves seed coverage but can increase hub leakage; Query-to-Node is often cleaner |

### Phase T Quality Tuning Snapshot (2026-06-29)

Phase T focuses on making Graph/PPR retrieval beat vanilla vector retrieval on multi-hop questions before relying on LLM query expansion.

| Run | Scope | Main Result |
|---|---|---|
| Baseline, no expansion | 21 scored Phase T queries | vector Hit@5 0.333, graph 0.190, hybrid 0.381 |
| Baseline, with expansion | 21 scored Phase T queries | graph Hit@5 improves to 0.524; hybrid Hit@5 0.524 and Oracle@10 0.619 |
| Random baseline | 2,347 chunks, 21 scored queries | random Hit@5 ~= 0.004, so graph/hybrid hits are not chance |
| T2.1 rerank, small 7-query slice | wider graph candidates + section/ticker/lexical intent boosts | graph no-expansion Hit@5 improved from 0.143 to 0.429; hybrid no-expansion from 0.286 to 0.571 |

Current diagnosis: no-expansion graph retrieval usually fails because query-to-seed captures only the first hop, and entity-to-chunk mapping/reranking can bury correct evidence below top-5. Next tuning target is deterministic no-expansion seed improvement plus coverage-aware chunk ranking.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM (extraction + agent) | DeepSeek (`deepseek-v4-flash` in `config/default.yaml`) via OpenAI-compatible API |
| Embedding model | `BAAI/bge-base-en-v1.5` (768-dim, MTEB 63.5, ~1.5 GB RAM) |
| Knowledge graph | Neo4j 5.26 Community + APOC + GDS (local Docker) |
| Vector retrieval | Neo4j vector index (HNSW + cosine) |
| Agent orchestration | LangChain + LangGraph (Phase D — 7-node conditional loop with reflection + multi-subquery traversal) |
| Numeric data | Finnhub API (financials/quote) — Phase C3/F.v1 done; PostgreSQL + XBRL migration deferred (F.v2) |
| News | Finnhub company-news API + LLM ticker resolution (Phase C4 — done) |
| Data models | Pydantic v2 |
| String matching | rapidfuzz (synonymy hybrid scoring) |
| Concurrency | ThreadPoolExecutor with tenacity retry |
| Config | YAML + python-dotenv |
| Testing | pytest (`tests/`) + Neo4j smoke script; 187 tests passed locally on 2026-06-25 |

---

## Progress

### Phase A — Offline KG Pipeline ✅

- [x] Config system + Neo4j/LLM/embedding factories
- [x] Ontology (FinReflectKG: 24 entity types, 29 rel types)
- [x] SEC EDGAR ingest + preprocess (9-filing baseline + pilot onboarding path)
- [x] Chunker (token-aware, 4,500/600)
- [x] **KG extraction** — single-call DeepSeek (entities + relationships in one call)
- [x] **KG store** — idempotent MERGE with APOC dynamic relationship type
- [x] **Pipeline orchestrator** — parallel chunk processing, checkpoint, continue-on-error
- [x] Pronoun blacklist + ORG/COMP collision merge (graph cleanup)
- [x] Tx log retention policy (aggressive — saves 99% disk vs default)

### Phase B — Embeddings + Synonymy + Specificity ✅

- [x] **B1** Chunk embeddings + Neo4j vector index (528-chunk baseline, ~5 min run)
- [x] **B2** Entity embeddings (3,620-entity baseline, ~80s run)
- [x] **B2** Synonymy edges via 4 composite rules (legal_suffix, acronym, plural, semantic + digit gate)
- [x] **B3** Node Specificity (`1/log(degree+1)`) — range [0.158, 1.443], single Cypher write

### Phase C — Online Tools ✅

- [x] **C1a** `query_to_seeds` — Query-to-Node linker via `entity_embedding` index ([seed.py](src/semigraph/online/seed.py))
- [x] **C1b** `run_ppr` — Personalized PageRank via GDS named projection ([ppr.py](src/semigraph/online/ppr.py))
- [x] **C1b+** `query_to_triple_seeds` — Query-to-Triple linker (HippoRAG v2 Table 4: +12.5% R@5 over Query-to-Node) via in-memory triple cosine search ([seed.py](src/semigraph/online/seed.py))
- [x] **C1c** `graph_search` — closes the tool: alias clustering (SYNONYM_OF *0..2) → cluster-aware chunk mapping (EXISTS dedup) → SUM(PPR mass) aggregation → Phase T intent rerank over wider candidates (section/ticker/lexical boosts). Validated 17/17 (deterministic, no dup chunks, provenance intact) on diverse query set. ([graph_search.py](src/semigraph/online/graph_search.py))
- [x] **C2** `vector_search` — top-k chunks via Neo4j vector index (baseline for ablation) ([vector_search.py](src/semigraph/online/vector_search.py))
- [x] **C2+** `hybrid_search` — RRF (k=60) fusion of vector + graph ([hybrid_search.py](src/semigraph/online/hybrid_search.py))
- [x] **C3** `financial_search` — Finnhub direct API (financials/quote), Protocol-backed; PostgreSQL+XBRL migration deferred to **F.v2** ([financial_search.py](src/semigraph/online/financial_search.py))
- [x] **C4** `news_search` — Finnhub company-news (90-day window, headline/full depth) + LLM ticker resolution via shared `_ticker` module ([news_search.py](src/semigraph/online/news_search.py))
- [x] **Pilot runner** — ticker onboarding wrapper with per-chunk metrics, coverage guard, specificity recompute, Neo4j verification, and config ticker sync ([pilot.py](scripts/pilot.py))

### Phase D — Agent Core ✅ (MVP loop complete)

LangGraph **Plan-then-ReAct** state machine — 7 nodes:

`plan → tool_select → execute → observe → reflect`

then conditionally:

`reflect → tool_select` (need more evidence)

`reflect → advance_subquery → tool_select` (current subquery done, more remain)

`reflect → synthesize` (all subqueries done or hard cap reached)

- [x] **D.1** State machine skeleton + `AgentState` TypedDict with planning / retrieval / reflection / synthesis fields ([state.py](src/semigraph/agent/state.py), [graph.py](src/semigraph/agent/graph.py))
- [x] **D.2** `plan_node` — decompose query into ≤3 atomic subqueries (JSON, fallback-guarded)
- [x] **D.3** `tool_select_node` — OpenAI function-calling router over 4 tools, consumes `retry_query` + `reflection_feedback`
- [x] **D.4** `execute_node` — shared retriever dispatch, flat `chunks_history`, `latest_chunks`, append-only `tool_call_log`, error-safe fallback
- [x] **D.5** `observe_node` — summarize latest evidence only, no-evidence fallback, append `observation_history`
- [x] **D.6** `reflect_node` — sufficiency check for current subquery, emits `retry_query` / `reflection_feedback`, hard cap via `MAX_REFLECTION_ROUNDS = 5`
- [x] **D.7** `advance_subquery_node` — mark current subquery complete, reset round-local fields, continue until all subqueries are processed
- [x] **D.8** `synthesize_node` — dedupe evidence, build grounded final answer, remove invalid citations, emit `citation_map`
- [x] **D.9** Tests — node-level regression + graph-level integration for retry loop, max-round exit, and multi-subquery traversal ([test_agent_nodes.py](tests/test_agent_nodes.py), [test_agent_graph_phase_d.py](tests/test_agent_graph_phase_d.py))
- [x] **D.10** Live smoke — local Neo4j connectivity verified end-to-end (`scripts/test_neo4j_connection.py`)
- [x] **D.11** Trace runner — colored CLI harness for real-LLM end-to-end tracing (`scripts/run_agent_trace.py`)
- [ ] **D.next** Router-quality tuning, evidence packing for synthesis, `run_agent()` API / UI integration

### Phase T — Quality Tuning 🔄

- [x] Phase T benchmark file expanded to 30 queries, with 21 scored gold-chunk anchors and discovery-only questions excluded from aggregate metrics
- [x] Retrieval evaluator reports Hit@5, Recall@5, MRR@5, Oracle@10, random chance baseline, and per-query returned chunk IDs
- [x] Query expansion comparison shows expansion is useful but should remain optional while no-expansion graph quality is tuned
- [x] T2.1 graph rerank adds wider candidate retrieval plus section/ticker/lexical intent boosts
- [x] No-expansion trace identifies the main failures: seed captures only first-hop entities, PPR drifts to hubs, or correct chunks are buried after entity-to-chunk mapping
- [ ] T2.2 next: deterministic no-expansion seed improvement (`query_to_seeds + query_to_triple_seeds`, ticker/product aliases, seed weighting)
- [ ] T2.3 next: coverage-aware chunk ranking to reduce broad-chunk bias

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
- `Phase_C1b+_HippoRAG_v2_Alignment.md` — implementation rationale for Query-to-Triple linker
- `Linker_Comparison_Report.md` — Query-to-Node vs Query-to-Triple proxy-metric eval (12 queries)
- `Coach_Phase_C1c_Entities_to_Chunks.md` — coaching guide for C1c
- `Graph_MultiHop_Benchmark_Report.md` — current graph quality benchmark
- `Code_Explained_Phase_D_Agent_State.md` — Phase D state / node / graph walkthrough with algorithmic example
- `Slide_walkthroght.md` — defense presentation guide
- `How_to_Read_FirstPrinciple_Notes.md` — meta-guide for `Code_Explained_*` / `Coach_*` notes

### Reference papers (`/home/kantinan/Documents/book/paper/project/`)
- `Hippo_rag.pdf` — HippoRAG (NeurIPS '24) — PPR retrieval + Node Specificity (foundation of graph_search)
- `finreflect.pdf` — FinReflectKG (ICAIF '25) — ontology adopted in `schema.py`
- `2404.16130v2.pdf` — Microsoft GraphRAG
- `2005.11401v4.pdf` — original RAG (Lewis et al., NeurIPS '20)

---

## Known Limitations

- **ASML** files Form 20-F (foreign private issuer), not 10-K. Section patterns don't apply — requires a separate 20-F parser before it can join the 10-K-only pilot corpus.
- **AMD / MU Item 10–11** use "incorporation by reference" to proxy statement (DEF 14A). Executive data is not embedded in the 10-K body — extraction yields only the reference sentence.
- **Synonymy at scale** — composite rules tested on 977 entities (subset of 3,620 after type filter). At 28-company scale, audit `--dry-run` output before writing edges; stock-ticker style abbreviations (e.g. `qcom` ↔ `qualcomm`) may not satisfy the strict acronym rule.
- **Specificity-weighted teleport** — GDS `gds.pageRank.stream` only supports uniform `sourceNodes`. The walker treats all seeds equally; specificity is used during seed selection (C1a) but not as a teleport vector. Workarounds (seed duplication, custom Cypher PPR) are deferred to ablation experiments.
- **Intersection bias in `graph_search`** — chunks that mention many distinct PPR clusters (broad coverage) outrank chunks that go deep on a single entity. Query "AMD" returns all-NVDA chunks (NVDA filings mention AMD + Intel + suppliers, summing more cluster scores) instead of AMD-specific chunks. This is intentional design (multi-hop signal) but reduces single-entity recall. Mitigation deferred to Phase E ablation: re-rank top chunks with query↔chunk cosine to recover specificity.
- **Off-corpus queries don't short-circuit** — `query_to_triple_seeds` accepts any triple with cosine ≥ 0.6. Random text like `"qwerty zzz xyz"` can still match one triple loosely → graph_search returns 5 chunks. Agent layer (Phase D) is the right place to detect this — e.g. avg seed similarity < threshold → route to `news_search` or refuse.
- **GDS deprecations** — `id(n)` (use `elementId`) and `gds.graph.project.cypher` (use `gds.graph.project` aggregation form) emit warnings on Neo4j 5.26; both still functional. Migration tracked as future work.

---

## Common Commands

```bash
# Tests (no external deps)
pytest tests/ -v

# Agent-only regression/integration
pytest tests/test_agent_nodes.py tests/test_agent_graph_phase_d.py -v

# Run a specific test
pytest tests/test_ontology.py::TestGraphNode -v

# Agent trace runner
python scripts/run_agent_trace.py "How do KLA yield improvements at TSMC affect AMD gross margin?" --show-citations

# Phase T retrieval benchmark
python scripts/evaluate_retrieval_quality.py --tools vector graph hybrid --top-k 5 --oracle-k 10 --no-llm-expansion
python scripts/evaluate_retrieval_quality.py --tools vector graph hybrid --top-k 5 --oracle-k 10

# Phase T graph bottleneck trace
python scripts/trace_retrieval_bottlenecks.py --no-query-expand-cache "How exposed is AMD to TSMC supply risk?"

# Neo4j control
docker compose up -d         # start
docker compose stop          # stop (keep data)
docker compose down          # remove containers (keep data via volumes)
docker compose logs -f neo4j # tail logs

# Connectivity smoke test
python scripts/test_neo4j_connection.py

# Draw current LangGraph wiring
python -c "from semigraph.agent.graph import build_agent; print(build_agent().get_graph().draw_ascii())"

# Inspect graph
docker exec semigraph-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC;"
```
