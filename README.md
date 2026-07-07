# SemiGraph

<img width="1672" height="941" alt="SemiGraphCover" src="https://github.com/user-attachments/assets/957f5c4e-26b9-4691-9a56-a9f0518ec245" />

SemiGraph is a CS senior project from KMUTNB: an agentic heterogeneous RAG system for semiconductor fundamental-analysis questions.

The project compares a normal vector-only RAG setup with a richer retrieval system that can use:

- a Neo4j knowledge graph built from SEC filings
- vector search over filing chunks
- structured financial data from Finnhub
- recent company news from Finnhub
- a LangGraph agent that chooses which tool to call

The goal is engineering, not stock advice. SemiGraph is about making retrieval better for multi-hop, evidence-based questions over financial disclosures.

## Why It Exists

Vector RAG is good at finding text that looks similar to the query, but financial questions often need more than similar text.

Example:

> How could TSMC supply risk affect AMD's gross margin?

That question may require several hops: AMD depends on TSMC, TSMC manufactures products, product availability affects revenue or margin, and recent news may change context. SemiGraph tests whether graph retrieval plus agentic tool use can recover that evidence better than vector search alone.

## Architecture

```text
                       User Query
                           |
                           v
                    +--------------+
                    | LangGraph    |
                    | Agent        |
                    +------+-------+
                           |
           +---------------+---------------+---------------+
           v               v               v               v
    graph_search     vector_search   financial_search   news_search
      Neo4j KG       Neo4j vectors      Finnhub API      Finnhub API
       + PPR           chunks        financial data        news
```

Offline, SemiGraph builds the corpus:

```text
SEC EDGAR filings
    -> HTML/filing cleanup
    -> section extraction
    -> chunking
    -> LLM knowledge-graph extraction
    -> Neo4j graph + vector indexes
```

Online, the agent routes each user question to one or more retrieval tools and synthesizes an answer with cited evidence.

## What It Can Do

- Download and preprocess SEC 10-K filings.
- Extract filing sections into clean Markdown.
- Chunk filings and embed chunks for vector search.
- Extract ontology-grounded entities and relationships with structured validation.
- Store graph facts and provenance in Neo4j.
- Run Personalized PageRank over the graph for multi-hop retrieval.
- Search chunks with vector similarity.
- Query financial and news APIs as separate tools.
- Run a LangGraph agent with planning, tool selection, reflection, and answer synthesis.
- Evaluate retrieval quality across three configurations:
  - Vanilla Vector RAG
  - Agentic Vector RAG
  - Agentic Heterogeneous RAG

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python |
| Agent | LangGraph, LangChain |
| LLM | DeepSeek API |
| Knowledge graph | Neo4j 5.26, APOC, GDS |
| Embeddings | BGE embedding model |
| Data models | Pydantic v2 |
| Data source | SEC EDGAR filings, Finnhub API |
| Testing | pytest |
| Local infra | Docker Compose |

## Core Modules

```text
src/semigraph/
├── ontology/      # FinReflectKG-based schema and Pydantic graph models
├── offline/       # ingest, preprocess, chunk, extract, store, embed
├── online/        # graph/vector/financial/news search tools
├── agent/         # LangGraph agent state, nodes, graph, prompts, tools
├── config.py      # YAML + .env config loader
└── connections.py # Neo4j, LLM, and embedding factories
```

Important scripts:

```text
scripts/pilot.py                       # onboard a ticker end-to-end
scripts/run_offline_pipeline.py        # extract graph data into Neo4j
scripts/embed_chunks.py                # build chunk embeddings
scripts/embed_nodes.py                 # build entity embeddings
scripts/build_synonymy.py              # create synonymy edges
scripts/compute_specificity.py         # compute node specificity
scripts/embed_triples.py               # build relationship triple embeddings
scripts/run_agent_trace.py             # run a traced agent query
scripts/evaluate_retrieval_quality.py  # compare retrieval tools
```

## Quick Start

```bash
conda create -n senior_project python=3.10
conda activate senior_project
pip install -e .
```

Create `.env`:

```env
DEEPSEEK_API_KEY=...
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
EDGAR_EMAIL=your@email.com
EDGAR_ORGANIZATION=YourOrg
FINNHUB_API_KEY=...
```

Start Neo4j:

```bash
docker compose up -d
```

Run tests:

```bash
pytest tests/ -v
```

Smoke-test Neo4j:

```bash
python scripts/test_neo4j_connection.py
```

## Example Commands

Onboard a ticker:

```bash
python scripts/pilot.py --ticker KLAC --workers 8
```

Run graph extraction:

```bash
python scripts/run_offline_pipeline.py --ticker NVDA --fiscal-year 2026 --workers 12
```

Build embeddings:

```bash
python scripts/embed_chunks.py
python scripts/embed_nodes.py
python scripts/build_synonymy.py
python scripts/compute_specificity.py
python scripts/embed_triples.py
```

Trace an agent answer:

```bash
python scripts/run_agent_trace.py "How exposed is AMD to TSMC supply risk?" --show-citations
```

Run retrieval evaluation:

```bash
python scripts/evaluate_retrieval_quality.py --tools vector graph hybrid --top-k 5 --oracle-k 10
```

## Current Scope

The main corpus focuses on semiconductor companies such as NVDA, AMD, MU, and ASML, with the working local corpus expanded to more US semiconductor tickers during pilot runs.

ASML uses Form 20-F instead of 10-K, so it needs a separate parser before it can be handled cleanly with the same pipeline.

## Notes

- This project is not a trading system and does not make buy/sell recommendations.
- The contribution is the retrieval and agent engineering: combining graph retrieval, vector retrieval, structured numeric lookup, and news lookup in one pipeline.
- Generated data, local Neo4j volumes, secrets, and agent-local instruction files should stay out of Git.
