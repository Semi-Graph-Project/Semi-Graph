"""LangGraph dev entrypoint for local workspace tooling."""

from semigraph.agents.graph import build_agent


graph = build_agent(tool="vector")
