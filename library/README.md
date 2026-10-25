# SemiGraph SDK — database setup + Agent components

SDK นี้มีคำสั่งสร้าง workspace และเตรียม Neo4j พร้อม Agent components แบบ Task-specific และ DeepAgent
ส่วนการสกัด Free Ontology จากข้อความและ retrieval facade แบบรวมยังอยู่ระหว่างพัฒนา

## Requirements

- Python >=3.11
- Docker Engine และ Docker Compose plugin สำหรับคำสั่ง `db up`

## Agent components available now

Python >=3.11. From the repository root:

```bash
python -m pip install -e ./library
# Optional, when using DeepAgent:
python -m pip install -e 'library[deepagents]'
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

These low-level examples need a caller-provided retriever and do not connect to a database on their own. `relations` is an optional hint map, not a required ontology. The SDK's generic ingestion and unified retrieval APIs are not available yet.

## Database setup available now

From the repository root after cloning:

```bash
python -m pip install -e ./library
semigraph-sdk init ./knowledge
semigraph-sdk db up --workspace ./knowledge
```

`init` creates an isolated Compose project, config, local `.env` secret and `.gitignore`. Defaults use localhost ports `17474` (Neo4j Browser) and `17687` (Bolt). If a port is occupied, choose another with `--http-port` or `--bolt-port` during `init`. `db up` starts only that workspace, checks APOC/GDS, creates SDK constraints and vector indexes, then waits until indexes are online. First setup reports `search_ready=false`; ingestion is a later stage.

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

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=library/src \
LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
python -B -m pytest library/tests -q -p no:cacheprovider
```

Agent-copy validation recorded 2026-10-25: **21 passed**. Live database acceptance on the same date covered a dedicated workspace, container restart, repeated setup, APOC 2025.04.0, GDS 2.17.1, and ONLINE 768-dimensional vector indexes. The expected initial state was `search_ready=false` because ingestion is a later stage.

Validation uses actual Agent graphs/tool loops, scripted LLMs and fake retrievers; no paid provider or Neo4j calls. The verified environment uses Python 3.12, LangGraph 1.2.15, langchain-core 1.6.10, Pydantic 2.13.5 and DeepAgents 0.7.25. Package version ranges do not imply that every future version has been tested.

The SDK imports only its packaged modules and external dependencies. It does not import the original SemiGraph runtime modules or load the original project's `.env`.
