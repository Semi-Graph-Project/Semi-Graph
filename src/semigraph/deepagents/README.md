# Deep Agents + Vector and Graph Search

Requires Python 3.11+; use `senior_project_py312`. Install the optional dependency
with `pip install -e '.[deepagents]'` if it is not already installed.

```python
from semigraph.deepagents import Deepagent

result = Deepagent("What products does NVIDIA disclose?", "graph", FullAnswer=True)
print(result["chunks"])
print(result["final_answer"])
```

`FullAnswer=False` performs retrieval and evidence selection only. Deep Agents
can plan, rewrite queries, keep temporary files, and delegate independent needs
to its general-purpose subagent. The main agent also has `write_todos` through
LangChain's `TodoListMiddleware`. Set `tool="vector"` or `tool="graph"` to give
the parent and subagent that search tool. Both workers share a per-run evidence
pool. The parent selects exact IDs from that pool in relevance order. Returned
chunk text and metadata always come from the retriever, not model-generated text.

When enabled, final answer generation calls `semigraph.agents.nodes.synthesize_node`
directly, sharing its prompt, parsing, and citations. No selected evidence returns
`Do not Answer` without an extra synthesis call.

Configuration comes from the existing Agent settings:

- `agent_retrieval.vector`: Vector index and candidate pool.
- `agent_retrieval.graph`: Graph seeds, PPR, reranking, and candidate pool.
- `agent_harness.top_k_chunks`: Results per search.
- `max_synthesis_chunks`: Maximum selected chunks, also in retrieval-only mode.
- `max_planned_tasks × max_attempts_per_task`: Shared search-call limit.
- `max_parallel_tasks`: LangGraph concurrency limit.

Deep Agents decides when to delegate; a simple question may need no subagents.
Retrieval-only still uses LLM calls for planning and selection. Unknown selected
IDs are discarded and recorded in `retrieval_trace.rejected_chunk_ids`, while
valid selections keep their order. If no valid selections remain, the result has
no chunks and Full Answer returns `Do not Answer`. This adds no LLM calls.
Tool/model errors still raise exceptions.

Run the interactive demo (real LLM and database):

```bash
conda run --no-capture-output -n senior_project_py312 python -m semigraph.deepagents.simple_deepagent
conda run --no-capture-output -n senior_project_py312 python -m semigraph.deepagents.simple_deepagent --retrieve-only "What products does NVIDIA disclose?"
conda run --no-capture-output -n senior_project_py312 \
  python -m semigraph.deepagents.simple_deepagent \
  --tool graph --retrieve-only "What products does NVIDIA disclose?"
```

## Evaluation contract

The return value matches the normalized result consumed by
`eval_scripts/evaluate_new_agent.py`: `chunks`, `final_answer`,
`answer_latency_ms`, `answer_error`, and `synthesis_trace`.
`retrieval_trace` additionally records actual queries, chunk IDs, and search times,
including searches performed by subagents. `answer_latency_ms` measures synthesis
only; measure the entire call for total Agent latency.

The evaluator exposes `deepagent_vector` and `deepagent_graph`. Both use the
controlled Neo4j database and the evaluator's top-10 chunk limit. Vector uses
the `gold_chunk_embedding` index; Graph uses the configured Graph Search
profile. Each query's DeepAgent answer is used directly; the evaluator does not
run a second synthesis call. Retrieval-only still includes DeepAgent's LLM
planning and evidence-selection calls, which are included in its latency and
token usage.

Run one query first to check the setup:

```bash
conda run --no-capture-output -n senior_project_py312 \
  python eval_scripts/evaluate_new_agent.py \
  --tool deepagent_graph \
  --version_name deepagent_graph_v1 \
  --mode retrieve_only \
  --limit 1 \
  --workers 1
```

Use `--mode full_answer` to include the same final-answer synthesis used by the
other Agent evaluation modes. Increase `--limit`, or use `--start` and `--end`,
only after the one-query run succeeds. Full Answer and retrieval-only both call
the LLM during DeepAgent retrieval; full Answer makes an additional synthesis
call when evidence was selected.

Offline tests exercise real Deep Agents tool and subagent execution with a scripted
model and mocked retrieval, without API charges:

```bash
conda run -n senior_project_py312 pytest tests/test_deepagents.py -q
```

API references: [Deep Agents](https://reference.langchain.com/python/deepagents/graph/create_deep_agent)
and [structured output](https://docs.langchain.com/oss/python/langchain/structured-output).
