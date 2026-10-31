# SemiGraph SDK

SemiGraph SDK helps you build a GraphRAG knowledge base from plain text chunks. It sets up a Neo4j workspace, extracts a Free Ontology from your text, creates embeddings, and provides Vector or Graph retrieval through one Python API.

You prepare and chunk the text. The SDK handles extraction, storage, indexing, and retrieval.
The package has its own install metadata under `library/`; it does not import the main SemiGraph runtime or load the main project's `.env`.

Before running a command or code example, replace each uppercase placeholder in square brackets with your own value. For example, replace `[YOUR_KNOWLEDGE_BASE]` with `./my-knowledge-base`. Quote paths, especially when they contain spaces.

Examples below use the workspace `./pump-knowledge-base`, two pump-related text chunks, and a question about the seal material. Use your own path, text, and question in your application.

## Requirements

- Python 3.11 or later.
- Docker Engine and Docker Compose v2 for the managed database setup.
- Internet access to install packages, pull the Neo4j image, and download the embedding model.
- An LLM API key for ingestion, Agent modes, or answer generation.

The `ingestion` extra installs Sentence Transformers and PyTorch. Allow enough disk space for these dependencies and the embedding model.

## Install

### Install from GitHub

The SDK is in the `library/` directory of the Semi-Graph repository.

Replace `[SDK_BRANCH_OR_TAG]` with a branch or release tag that contains the SDK. The current development branch is `feature/standalone-sdk`:

```bash
python -m pip install 'semigraph-sdk[ingestion] @ git+https://github.com/Semi-Graph-Project/Semi-Graph.git@[SDK_BRANCH_OR_TAG]#subdirectory=library'
```

The package version in this repository is currently `0.1.0a0`.

### Install from a local clone

From the repository root, run:

```bash
python -m pip install -e './library[ingestion]'
```

### Optional: use DeepAgent

Install the `deepagents` extra if you plan to set `agent="deepagent"`.

Replace `[SDK_BRANCH_OR_TAG]` with the branch or tag you chose, then install both extras:

```bash
python -m pip install 'semigraph-sdk[ingestion,deepagents] @ git+https://github.com/Semi-Graph-Project/Semi-Graph.git@[SDK_BRANCH_OR_TAG]#subdirectory=library'
```

Or, from a local clone, run `python -m pip install -e './library[ingestion,deepagents]'` from the repository root.

## Create a database workspace

Replace `[YOUR_KNOWLEDGE_BASE]` with a directory path for this knowledge base:

```bash
semigraph-sdk init "[YOUR_KNOWLEDGE_BASE]"
```

Example, if your chosen path is `./pump-knowledge-base`:

```bash
semigraph-sdk init "./pump-knowledge-base"
```

The SDK creates `semigraph.yaml`, `compose.yaml`, `.env`, and `.gitignore` in the workspace. Default ports are `17474` for Neo4j Browser and `17687` for Bolt. The generated `.env` is ignored by Git.

If either default port is occupied, replace the port placeholders with available port numbers when creating the workspace. Use this instead of the previous `init` command. Example ports are shown only if they are free on your computer:

```bash
semigraph-sdk init "[YOUR_KNOWLEDGE_BASE]" --http-port [AVAILABLE_HTTP_PORT] --bolt-port [AVAILABLE_BOLT_PORT]
```

Example:

```bash
semigraph-sdk init "./pump-knowledge-base" --http-port 17475 --bolt-port 17688
```

### Choose an embedding model

The generated config defaults to `BAAI/bge-base-en-v1.5` with 768 dimensions.

If your data is multilingual, choose a suitable multilingual model and update `embedding.model`, `embedding.revision`, and `embedding.dimension` in `[YOUR_KNOWLEDGE_BASE]/semigraph.yaml` **before database setup and ingestion**. Use a model whose output dimension matches the configured dimension.

### Configure an LLM

Ingestion needs an LLM to extract entities and relationships. Agent modes and answer generation also use an LLM. Add your provider settings to `[YOUR_KNOWLEDGE_BASE]/semigraph.yaml`:

```yaml
llm:
  provider: "[YOUR_LLM_PROVIDER]"  # Example: openai
  model: "[YOUR_MODEL_NAME]"        # Use a model ID from your provider
  api_key_key: OPENAI_API_KEY
  # Optional for OpenAI-compatible services:
  # base_url: "[YOUR_PROVIDER_BASE_URL]"
```

Replace `[YOUR_LLM_PROVIDER]` and `[YOUR_MODEL_NAME]` with values supported by your service. For OpenAI-compatible services or OpenRouter, set `base_url` as required. The `api_key_key` value must match the key name in `.env`. If you use a different environment variable name, update both places to match.

Add the key to `[YOUR_KNOWLEDGE_BASE]/.env`:

```dotenv
OPENAI_API_KEY=[YOUR_API_KEY]
```

Replace `[YOUR_API_KEY]` with your secret. Do not commit or share `.env`.

### Start Neo4j

Start the database and wait for the command to report that setup is ready:

```bash
semigraph-sdk db up --workspace "[YOUR_KNOWLEDGE_BASE]"
```

Example:

```bash
semigraph-sdk db up --workspace "./pump-knowledge-base"
```

This starts the workspace's Neo4j container, checks APOC and GDS, creates SDK constraints and vector indexes, and waits until the indexes are online.

## Ingest text chunks

The SDK accepts a `list[str]`. It does not parse PDFs or split documents; prepare and chunk documents in your application first.

Replace the example strings below with your own text chunks:

```python
from semigraph_sdk import Engine

chunks = [
    "[YOUR_TEXT_CHUNK_1]",
    "[YOUR_TEXT_CHUNK_2]",
]

with Engine.from_config("[YOUR_KNOWLEDGE_BASE]/semigraph.yaml") as engine:
    report = engine.ingest(chunks)

    print(report.status, report.search_ready, report.corpus_revision)
    for item in report.outcomes:
        print(item.input_index, item.status, item.warnings, item.error)
```

Example chunks for the pump question below: `"Pump P7 uses a ceramic seal."` and `"The ceramic seal tolerates high temperatures."`

For each new chunk, the SDK generates its identity, calls the configured LLM to extract entities and relationships, resolves evidence quotes, creates embeddings locally, and stores the results. It prepares the corpus for search when ingestion completes. Repeated calls skip completed chunks; retryable embedding or storage failures can reuse saved extraction results.

Check `report.status`, each outcome, and `report.search_ready` before querying. Reports can be `complete`, `partial`, or `failed`. Validation warnings are reported per chunk.

## Retrieve evidence or generate an answer

`Engine.query()` requires a finalized corpus (`search_ready=true`).

### Retrieve only

Use `agent="none"` and `output="chunks"` to retrieve evidence without calling an LLM. The embedding model still encodes the query locally. The first use may download the configured model.

Replace the sample question and select the retrieval options for your use case:

```python
from semigraph_sdk import Engine

with Engine.from_config("[YOUR_KNOWLEDGE_BASE]/semigraph.yaml") as engine:
    result = engine.query(
        "[YOUR_QUESTION]",
        tool="vector",       # Choose: vector | graph
        agent="none",        # Choose: none | task_specific | deepagent
        output="chunks",     # Choose: chunks | answer
        top_k=5,              # Set the maximum number of evidence chunks
    )

    print(result.status, result.corpus_revision)
    for chunk in result.chunks:
        print(chunk.rank, chunk.chunk_id, chunk.text)
        for match in chunk.matches:
            print(match.tool, match.score_kind, match.score, match.query)
```

Example question for those chunks: `What material does pump P7 use?`

| Parameter | Options | Purpose |
| --- | --- | --- |
| `tool` | `vector`, `graph` | Search the chunk vector index or use graph seeds and GDS Personalized PageRank. |
| `agent` | `none`, `task_specific`, `deepagent` | Retrieve directly, plan focused searches, or use DeepAgent. |
| `output` | `chunks`, `answer` | Return evidence chunks or generate a grounded answer. |
| `top_k` | `1` to the configured maximum | Maximum number of evidence chunks to return. Agent mode also requires `top_k` to be at least `retrieval.agent.max_planned_tasks` (default `3`). |

Agent modes use an LLM for planning and evidence selection, even when `output="chunks"`. `output="answer"` uses an LLM for synthesis. DeepAgent also requires the `deepagents` extra.

### Generate an answer

Replace the question and select the retrieval tool and Agent:

```python
from semigraph_sdk import Engine

with Engine.from_config("[YOUR_KNOWLEDGE_BASE]/semigraph.yaml") as engine:
    result = engine.query(
        "[YOUR_QUESTION]",
        tool="graph",            # Choose: vector | graph
        agent="task_specific",   # Choose: none | task_specific | deepagent
        output="answer",
        top_k=5,
    )

    print(result.answer)
```

For the example chunks above, an answer question could be `What material does pump P7 use?`.

Answers may cite only chunk IDs returned in `result.chunks`. If no evidence is found, the result is `no_evidence` and the answer is `"Do not Answer"`.

Graph retrieval uses GDS Personalized PageRank. The SDK reuses its in-memory projection when available and rebuilds it after a Neo4j restart or ingestion.

## Use an existing Neo4j server

The managed Docker workspace above is the recommended setup for a first use. To connect to an existing dedicated Neo4j database instead:

Edit `[YOUR_KNOWLEDGE_BASE]/semigraph.yaml` with the server URI, username, and database name. Put the password in `[YOUR_KNOWLEDGE_BASE]/.env` using the key configured by `database.password_key`.

Example connection values are `bolt://127.0.0.1:7687`, username `neo4j`, and database `neo4j`. Use the actual values for your server.

Then prepare the database:

```bash
semigraph-sdk db setup --config "[YOUR_KNOWLEDGE_BASE]/semigraph.yaml"
```

The selected database must be empty or already have matching SDK metadata. This command prepares the selected database; it does not create a database on the Neo4j server. The server must provide the plugins and capabilities required by the SDK.

Python can run the same setup:

```python
from semigraph_sdk import Engine

with Engine.from_config("[YOUR_KNOWLEDGE_BASE]/semigraph.yaml") as engine:
    report = engine.setup()
    print(report)
```

## Stop and restart the managed database

Stop the container when you are done. The Docker volume and database data are preserved:

```bash
semigraph-sdk db down --workspace "[YOUR_KNOWLEDGE_BASE]"
```

Example:

```bash
semigraph-sdk db down --workspace "./pump-knowledge-base"
```

Start it again with `semigraph-sdk db up --workspace "[YOUR_KNOWLEDGE_BASE]"`.
