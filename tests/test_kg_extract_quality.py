"""Unit tests for extraction quality guards."""
from __future__ import annotations

from semigraph.offline import kg_extract
from semigraph.ontology.normalization import normalize_entity_name


def test_normalize_entity_name_canonical_aliases():
    assert normalize_entity_name("NVIDIA Corporation", "ORG") == "nvidia"
    assert normalize_entity_name("Micron Technology, Inc.", "ORG") == "micron"
    assert normalize_entity_name("RTX Series", "PRODUCT") == "geforce rtx"
    assert normalize_entity_name("Xeon Scalable processors", "PRODUCT") == "xeon scalable"


def test_validate_nodes_dedupes_after_normalization():
    nodes, keys = kg_extract._validate_nodes([
        {"id": "NVIDIA Corporation", "type": "ORG", "properties": {}},
        {"id": "nvidia", "type": "ORG", "properties": {}},
    ])

    assert len(nodes) == 1
    assert nodes[0].id == "nvidia"
    assert keys == {("nvidia", "ORG")}


def test_validate_nodes_rejects_known_product_mislabeled_as_company():
    nodes, keys = kg_extract._validate_nodes([
        {"id": "Blackwell", "type": "ORG", "properties": {}},
        {"id": "Blackwell", "type": "PRODUCT", "properties": {}},
    ])

    assert len(nodes) == 1
    assert nodes[0].id == "blackwell"
    assert nodes[0].type == "PRODUCT"
    assert keys == {("blackwell", "PRODUCT")}


def test_validate_relationships_rejects_product_source_for_produces():
    _, keys = kg_extract._validate_nodes([
        {"id": "Blackwell", "type": "ORG", "properties": {}},
        {"id": "NVIDIA", "type": "PRODUCT", "properties": {}},
    ])

    rels = kg_extract._validate_relationships([
        {
            "source": "Blackwell",
            "source_type": "ORG",
            "target": "NVIDIA",
            "target_type": "PRODUCT",
            "type": "produces",
        }
    ], keys)

    assert rels == []


def test_extract_chunk_enforces_node_and_relationship_caps():
    class _Response:
        usage_metadata = {}

        def __init__(self, content: str) -> None:
            self.content = content

    class _LLM:
        def invoke(self, messages):
            nodes = [
                {"id": f"Product {i}", "type": "PRODUCT", "properties": {}}
                for i in range(45)
            ]
            rels = [
                {
                    "source": "NVIDIA",
                    "source_type": "ORG",
                    "target": f"Product {i}",
                    "target_type": "PRODUCT",
                    "type": "produces",
                }
                for i in range(45)
            ]
            nodes.insert(0, {"id": "NVIDIA", "type": "ORG", "properties": {}})
            import json

            return _Response(json.dumps({"nodes": nodes, "relationships": rels}))

    result = kg_extract.extract_chunk("NVIDIA produces many products.", "Item_1", llm=_LLM())

    assert len(result.nodes) == 40
    assert len(result.relationships) == 39
