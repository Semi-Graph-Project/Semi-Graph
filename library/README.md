# SemiGraph SDK — database setup, ingestion + Agent components

SDK นี้สร้าง workspace Neo4j แยก, รับข้อความไปสกัดเป็น Free Ontology พร้อม embedding และมี Agent components แบบ Task-specific กับ DeepAgent ให้เรียกใช้
ตัวรวม Retrieval API (`Engine.query`) ยังอยู่ใน Stage 03

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

Stage 02 validation on 2026-10-25: **36 SDK tests passed**. Live smoke runs on RAGTEST at Bolt port `7695` migrated schema v1 to v2, used real `BAAI/bge-base-en-v1.5` 768-dimensional vectors, stored verified assertions, skipped completed chunks on retry, and restored the GDS projection after it was dropped. One run used a scripted extractor to verify partial failures; another used one real OpenRouter call with model `openai/gpt-5.6-luna` and published one assertion. Temporary config/secret files and smoke records were removed, leaving RAGTEST empty and `search_ready=false`; its YAML and `.env` were not changed.

Unit validation uses scripted LLMs, fake retrievers and fake embedders. Live ingestion smoke used Neo4j, the cached local embedding model and one OpenRouter extraction call. The verified environment uses Python 3.12, LangGraph 1.2.15, langchain-core 1.6.10, Pydantic 2.13.5 and DeepAgents 0.7.25. Package version ranges do not imply that every future version has been tested.

The SDK imports only its packaged modules and external dependencies. It does not import the original SemiGraph runtime modules or load the original project's `.env`.
