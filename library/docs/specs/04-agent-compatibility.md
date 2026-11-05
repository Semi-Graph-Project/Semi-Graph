# Spec 04 — Copied Agents compatible with Free Ontology

Status: implemented slice, with specification recorded after work began. The user explicitly requested finishing this started slice and documenting every subsequent slice before implementation.

## Scope

Copy the original Task-specific Agent and DeepAgent under `semigraph_sdk.agents`, preserving their orchestration. Make them accept arbitrary document text and injected LLM/retrieval dependencies without importing the original runtime/config/catalog. This slice supplies Agent controllers; it does not supply a Neo4j retriever or Free Ontology extraction.

## Implemented contract

- `AgentRuntime(llm=..., retrievers={...}, config=AgentConfig(...), relations={...})` supplies dependencies explicitly. Relation hints are optional; empty hints work. Maps are snapshotted to avoid external mutation during a run.
- Each callback accepts `query` and `top_k_chunks` as keyword arguments and returns chunk dictionaries containing at least `chunk_id` and `text`. Connection/model dependencies are captured by the callback.
- `run_agent(state, tool, runtime=..., generate_answer=...)` retains the Task-specific graph and raw state return shape.
- `Deepagent(query, tool, FullAnswer, runtime=...)` retains tool/subagent evidence collection and the original dictionary return shape. Import it explicitly from `semigraph_sdk.agents.deepagent` when the optional dependency is installed.
- `AgentConfig` is immutable, validates positive budgets and requires `max_synthesis_chunks >= max_planned_tasks` for the inherited collector policy.
- Planning accepts arbitrary observed relations or no relations, correctly names the selected tool, and validates the planned task budget. JSON repair stays bounded.
- Assess receives observed relations directly rather than filtering through the financial catalog. Retry/stop and unknown-evidence checks are retained.
- Synthesis uses generic entity wording, keeps evidence-ID citations and skips the LLM when no evidence exists. Collector output removes duplicate IDs.
- LLM text and text-content blocks are supported at parsing boundaries.

## Copy provenance and maintenance

Seven original modules were copied: contracts, state, synthesis helpers, prompts, nodes, graph, and DeepAgent. Original paths and SHA256 baselines are in `../copied-sources.json` and file headers. None of these original files was modified. New runtime code and tests live only under `library/`.

Future changes compare against the recorded base and test the copy independently. Do not silently synchronize upstream changes or introduce a fallback import of original config.

## Verification scope

The new tests exercise real LangGraph/DeepAgent tool loops with scripted LLM responses and injected fake retrievers, including Thai pump/seal text, arbitrary/empty relation hints, both tools and output modes, evidence retries, unknown IDs, content blocks, excess-plan repair, parallel collection, error propagation and evidence isolation across runs. A fresh interpreter checks that importing the SDK does not import `semigraph` or load its database/API-key environment settings.

These checks establish interface and control-flow behavior. They do not measure LLM accuracy, Neo4j connectivity, Free Ontology extraction quality or Graph/PPR recall. The existing synthesis parser flags invalid citations in its trace; it is not a guarantee that every claim is factually supported.

## Remaining integration

Spec 03 will supply actual configured Vector/Graph callbacks, populate relation hints from ingestion and normalize the two result shapes behind the friendly API. Until then the caller supplies an LLM and retriever callbacks directly.
