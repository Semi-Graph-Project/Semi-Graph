"""
semigraph.ontology — public API

Import everything you need from here:

    from semigraph.ontology import (
        GraphNode,
        GraphRelationship,
        GraphExtractionResult,
        OntologyRegistry,
    )
"""
from semigraph.ontology.nodes import GraphExtractionResult, GraphNode, GraphRelationship
from semigraph.ontology.schema import OntologyRegistry

__all__ = [
    "GraphNode",
    "GraphRelationship",
    "GraphExtractionResult",
    "OntologyRegistry",
]
