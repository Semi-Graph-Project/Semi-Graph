# SemiGraph SDK — database setup, ingestion + retrieval

SDK นี้สร้าง workspace Neo4j แยก, รับข้อความไปสกัดเป็น Free Ontology พร้อม embedding และมี Agent components แบบ Task-specific กับ DeepAgent ให้เรียกใช้
ผู้ใช้เรียกค้นผ่าน `Engine.query()` ได้ โดยเลือก Vector/Graph, Agent และผลลัพธ์ chunks/answer ในคำสั่งเดียว

## Requirements

- Python >=3.11
- Docker Engine และ Docker Compose plugin สำหรับคำสั่ง `db up`

## Agent components available now

Python >=3.11. From the repository root:

```bash
python -m pip install -e ./library
# Optional, for local embeddings and OpenAI-compatible extraction:
python -m pip install -e './library[ingestion]'
# Optional, when using DeepAgent:
python -m pip install -e './library[deepagents]'
```

Integration example: the caller supplies `my_llm` and `my_graph_retriever`. The callback accepts keyword `query`, `top_k_chunks` and returns dictionaries with `chunk_id`, `text`, and optional score/metadata. It must capture its own database settings.

```python
from semigraph_sdk.agents import AgentConfig, AgentRuntime, run_agent

runtime = AgentRuntime(
    llm=my_llm,
    retrievers={"graph": my_graph_retriever},
    config=AgentConfig(max_planned_tasks=3, max_synthesis_chunks=10),
    # Optional discovered hints; omit this entirely if none are available.
    relations={"USES_MATERIAL": "An item uses this material"},
)

result = run_agent(
    {"original_query": "What material does the pump use?"},
    tool="graph", runtime=runtime, generate_answer=False,
)
chunks = result["synthesis_input"]["accepted_chunks"]
```

```python
from semigraph_sdk.agents.deepagent import Deepagent

result = Deepagent(
    "What material does the pump use?",
    tool="graph", FullAnswer=True, runtime=runtime,
)
print(result["final_answer"])
```

These low-level Agent examples need a caller-provided retriever and do not connect to a database on their own. `relations` is an optional hint map, not a required ontology.

## Query the SDK corpus

Install the retrieval dependencies from the repository root:

```bash
python -m pip install -e './library[ingestion]'
# Optional, only when agent="deepagent":
python -m pip install -e './library[deepagents]'
```

`[ingestion]` provides the local sentence-transformer model used to embed each query. The first query may download the configured model if it is not cached yet. `Engine.query()` connects to the workspace database and requires a finalized corpus (`search_ready=true`).

Use this API:

```python
engine.query(question, *, tool="vector", agent="none", output="chunks", top_k=10)
```

| Parameter | Options | Meaning |
| --- | --- | --- |
| `tool` | `vector`, `graph` | Search the chunk vector index or use graph seeds and GDS Personalized PageRank. |
| `agent` | `none`, `task_specific`, `deepagent` | Retrieve directly, plan focused searches, or use DeepAgent to plan retrieval. |
| `output` | `chunks`, `answer` | Return evidence chunks only, or ask the configured LLM to write one grounded answer. |
| `top_k` | `1` to `retrieval.max_top_k` | Maximum evidence chunks returned. Agent mode also requires `top_k >= retrieval.agent.max_planned_tasks` (default `3`). |

`agent="none", output="chunks"` is Retrieve Only and does not call an LLM. Agent modes use an LLM for planning and evidence selection, even when `output="chunks"`. `output="answer"` uses an LLM for synthesis with any agent mode. DeepAgent also requires the `[deepagents]` extra.

```python
from semigraph_sdk import Engine

with Engine.from_config("knowledge/semigraph.yaml") as engine:
    result = engine.query(
        "What material does pump P7 use?",
        tool="graph",       # vector | graph
        agent="none",       # none | task_specific | deepagent
        output="chunks",    # chunks | answer
        top_k=5,
    )

    print(result.status, result.corpus_revision)
    for chunk in result.chunks:
        print(chunk.rank, chunk.chunk_id, chunk.text)
        for match in chunk.matches:
            print(match.tool, match.score_kind, match.score, match.query)
        print(chunk.assertions)
```

To ask the SDK to write one grounded answer, set `output="answer"`. The answer may cite only chunk IDs returned in `result.chunks`; no evidence returns `"Do not Answer"` without calling synthesis.

```python
with Engine.from_config("knowledge/semigraph.yaml") as engine:
    result = engine.query(
        "What material does pump P7 use?",
        tool="vector",
        agent="task_specific",
        output="answer",
        top_k=5,
    )
    print(result.answer)
```

Graph seed mode defaults to `triple`. Set `retrieval.graph.seed_mode` to `entity` or `chunk` in `knowledge/semigraph.yaml` to choose another seed source. Other settings live under `retrieval` and reject unknown keys. Lower `retrieval.agent.max_planned_tasks` when using a smaller evidence budget. Graph mode reuses its in-memory GDS projection when available, rebuilds it after a Neo4j restart, and refreshes it after ingestion.

```yaml
retrieval:
  per_search_k: 10
  graph:
    seed_mode: triple
    seed_k: 10
    damping: 0.5
    max_iterations: 20
  agent:
    max_planned_tasks: 3
    max_attempts_per_task: 2
    max_parallel_tasks: 2
```

`result.status` is `ok` or `no_evidence`. `result.chunks` contains ranked evidence with `chunk_id`, text, matches, entities, and assertions. `result.answer` is populated only for `output="answer"`; with no evidence it is `"Do not Answer"`. `result.corpus_revision` identifies the indexed corpus version. `result.trace` contains mode-specific details: direct Graph calls include seeds and projection state, while Agent calls include search results and controller traces. It never contains embedding vectors. Vector cosine and Graph PPR scores have separate `score_kind` values and must not be compared as one scale.

## Setup a database and ingest text

From the repository root after cloning:

```bash
python -m pip install -e ./library
semigraph-sdk init ./knowledge
semigraph-sdk db up --workspace ./knowledge
```

`init` creates an isolated Compose project, config, local `.env` secret and `.gitignore`. Defaults use localhost ports `17474` (Neo4j Browser) and `17687` (Bolt). If a port is occupied, choose another with `--http-port` or `--bolt-port` during `init`. `db up` starts only that workspace, checks APOC/GDS, creates SDK constraints and vector indexes, then waits until indexes are online. Before ingestion, add your LLM to `knowledge/semigraph.yaml` and its key to `knowledge/.env`:

```yaml
llm:
  provider: openai
  model: your-model-name
  api_key_key: OPENAI_API_KEY
```

```dotenv
OPENAI_API_KEY=your-key
```

Use `provider: openai-compatible` or `openrouter` and set `base_url` for an OpenAI-compatible service. Keep `.env` private; `init` already adds it to `.gitignore`.

Then pass a list of text chunks to the library:

```python
from semigraph_sdk import Engine

with Engine.from_config("knowledge/semigraph.yaml") as engine:
    setup = engine.setup()  # Engine.ingest also checks setup automatically
    report = engine.ingest([
        "Pump P7 uses a ceramic seal.",
        "The ceramic seal tolerates high temperatures.",
    ])
    print(report.status, report.search_ready, report.corpus_revision)
    for item in report.outcomes:
        print(item.input_index, item.status, item.warnings, item.error)
```

`Engine.ingest()` makes one extraction call per new chunk, resolves evidence quotes against NFC-normalized text, embeds chunk/entity/assertion text, stores verified graph data, and rebuilds the SDK GDS projection. A repeated call skips completed chunks. If embedding or storage fails after extraction was checkpointed, retrying can resume without another extraction call. Failed assertions appear in the chunk's `warnings`; a malformed LLM response or system failure marks only that chunk failed. Reports can be `complete`, `partial` or `failed`; `search_ready` becomes true only after indexes and projection are ready.

The default embedding model remains `BAAI/bge-base-en-v1.5` at 768 dimensions for the existing RAGTEST workspace. New workspaces can change model, revision and dimension before setup. The configured LLM and embedding model are supplied by the library user; model availability and retrieval quality depend on those choices.

Stop the container and keep its data:

```bash
semigraph-sdk db down --workspace ./knowledge
```

To prepare an existing empty, dedicated Neo4j, edit `knowledge/semigraph.yaml` with its URI, user and database name. Put its password under the configured key in `knowledge/.env`, then run:

```bash
semigraph-sdk db setup --config ./knowledge/semigraph.yaml
```

The selected database must be empty or already carry matching SDK metadata. Setup does not create databases on an existing Neo4j server. Python code can call the same setup method:

```python
from semigraph_sdk import Engine

with Engine.from_config("knowledge/semigraph.yaml") as engine:
    report = engine.setup()
    print(report)
```

## Verification

Install the test dependency from the repository root:

```bash
python -m pip install -e './library[test]'
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=library/src \
LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
python -B -m pytest library/tests -q -p no:cacheprovider
```

Agent-copy validation recorded 2026-10-25: **21 passed**. Live database setup acceptance on the same date covered a dedicated workspace, container restart, repeated setup, APOC 2025.04.0, GDS 2.17.1, and ONLINE 768-dimensional vector indexes.

Stage 02 validation on 2026-10-25: **36 SDK tests passed**. Earlier live smoke on RAGTEST at Bolt port `7695` verified schema migration, ingestion, retry checkpoints, and projection recovery. The database now has a finalized corpus; current Stage 03 smoke is read-only apart from rebuilding its in-memory SDK projection.

Stage 03 validation on 2026-10-25: **33 focused retrieval tests passed; 69 SDK tests passed overall**. Tests cover all 12 tool/Agent/output combinations, score provenance, cache reuse and revision replacement, seed modes, PPR ranking, projection reuse/rebuild and concurrent recovery, readiness, and revision changes.

Read-only live query smoke used the existing RAGTEST corpus at Bolt port `7695`. All **12 public modes** passed against Neo4j: Vector/Graph × no Agent/Task-specific/DeepAgent × chunks/answer. Every mode returned both chunks. Agent planning, evidence selection and answer generation used scripted in-process LLMs; no provider call was made. Chunks output did not synthesize; answer output synthesized once and passed citation checks. Earlier kernel smoke verified triple, entity and chunk seed modes, warm triple-cache reuse, and projection recovery after dropping the SDK-owned in-memory projection. The corpus stayed `search_ready=true`, revision `1`, with 2 chunks, 5 entities and 2 assertions; no workspace config or corpus rows changed.

A separate Neo4j `2025.04-community` smoke used the real SDK pipeline with an injected deterministic extractor and 8-dimensional test embedder. It ingested new relation `USES_MATERIAL`; Vector returned its chunk, Graph selected the triple, and GDS PPR returned the related chunk. A second ingest advanced revision `1 → 2` and invalidated the prior triple cache. Dropping the GDS projection and restarting Neo4j both triggered successful projection recovery. The temporary container, volume, config and credentials were removed. RAGTEST was not modified. This smoke used no paid LLM or external embedding model.

Unit validation uses scripted LLMs, fake retrievers and fake embedders. Live ingestion smoke used Neo4j, the cached local embedding model and one OpenRouter extraction call. The verified environment uses Python 3.12, LangGraph 1.2.15, langchain-core 1.6.10, Pydantic 2.13.5 and DeepAgents 0.7.25. Package version ranges do not imply that every future version has been tested.

The SDK imports only its packaged modules and external dependencies. It does not import the original SemiGraph runtime modules or load the original project's `.env`.
