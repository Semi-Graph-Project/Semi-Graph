"""LangGraph dev entrypoint for local workspace tooling."""

from semigraph.agents.graph import build_agent, build_task_worker


graph = build_agent(tool="vector")
