"""Dependencies supplied by the library, without the project's global config."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Retriever(Protocol):
    def __call__(self, *, query: str, top_k_chunks: int) -> list[dict]: ...


class AgentConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_planned_tasks: int = Field(default=5, ge=1)
    max_parallel_tasks: int = Field(default=4, ge=1)
    top_k_chunks: int = Field(default=10, ge=1)
    max_attempts_per_task: int = Field(default=3, ge=1)
    max_synthesis_chunks: int = Field(default=10, ge=1)
    max_num_relations: int = Field(default=8, ge=1)
    json_mode: bool = False

    @model_validator(mode="after")
    def allow_one_chunk_per_task(self):
        if self.max_synthesis_chunks < self.max_planned_tasks:
            raise ValueError("max_synthesis_chunks must be >= max_planned_tasks")
        return self


@dataclass(frozen=True)
class AgentRuntime:
    """Relation hints describe the corpus; they are not an extraction whitelist.

    Retriever callbacks capture their own database/embedding configuration.
    The LLM and retrievers must support concurrent calls when parallelism > 1.
    """

    llm: Any
    retrievers: Mapping[str, Retriever]
    config: AgentConfig = field(default_factory=AgentConfig)
    relations: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        unknown = set(self.retrievers) - {"vector", "graph"}
        if unknown:
            raise ValueError(f"Unsupported retrievers: {sorted(unknown)}")
        if not self.retrievers or not all(callable(r) for r in self.retrievers.values()):
            raise ValueError("Provide at least one callable retriever")
        if not all(
            isinstance(name, str) and name.strip() and isinstance(description, str)
            for name, description in self.relations.items()
        ):
            raise ValueError("relations must map nonempty names to text descriptions")
        object.__setattr__(self, "retrievers", MappingProxyType(dict(self.retrievers)))
        object.__setattr__(self, "relations", MappingProxyType(dict(self.relations)))

    def retriever(self, tool: str) -> Retriever:
        if tool not in self.retrievers:
            raise ValueError(f"No retriever configured for tool={tool!r}")
        return self.retrievers[tool]


def response_text(response: Any) -> str:
    """Read text-only and content-block chat responses, ignoring non-text blocks."""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block if isinstance(block, str) else block.get("text", "")
            for block in content
            if isinstance(block, str) or (
                isinstance(block, dict) and isinstance(block.get("text"), str)
            )
        )
    raise ValueError("LLM response must contain text or text content blocks")
