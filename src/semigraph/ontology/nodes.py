"""
Pydantic models for knowledge graph extraction.
These define the JSON contract between the LLM and the Neo4j storage layer.
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, model_validator


class GraphNode(BaseModel):
    """A single node extracted from text by the LLM."""

    id: str = Field(description="Actual name/identifier found in the text. Never use generic ids like 'Company_1'.")
    type: str = Field(description="Node type from the allowed list e.g. 'Company', 'Product'.")
    properties: dict = Field(
        default_factory=dict,
        description="Additional attributes for this node.",
    )

    @model_validator(mode="after")
    def ensure_name_equals_id(self) -> "GraphNode":
        """Neo4j shows 'name' as the display label in Viz — keep it in sync with id."""
        if "name" not in self.properties:
            self.properties["name"] = self.id
        return self


class GraphRelationship(BaseModel):
    """A directed relationship between two nodes."""

    source: str = Field(description="id of the source node.")
    source_type: str = Field(description="type of the source node.")
    target: str = Field(description="id of the target node.")
    target_type: str = Field(description="type of the target node.")
    type: str = Field(description="Relationship type from the allowed list e.g. 'COMPETES_WITH'.")
    properties: dict = Field(
        default_factory=dict,
        description="Relationship attributes. Always include fiscal_year when determinable.",
    )


class GraphExtractionResult(BaseModel):
    """Full output from a single LLM extraction call over one chunk."""

    nodes: List[GraphNode] = Field(default_factory=list)
    relationships: List[GraphRelationship] = Field(default_factory=list)
