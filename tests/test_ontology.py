"""
Unit tests for semigraph.ontology

Run with:
    pytest tests/test_ontology.py -v
"""
import pytest

from semigraph.ontology import (
    GraphExtractionResult,
    GraphNode,
    GraphRelationship,
    OntologyRegistry,
)
from semigraph.ontology.schema import NODE_CATALOG, RELATIONSHIP_CATALOG, SECTION_CONFIG


# ===========================================================================
# GraphNode
# ===========================================================================

class TestGraphNode:

    def test_name_auto_set_from_id(self):
        """name should be injected into properties equal to id."""
        node = GraphNode(id="NVIDIA Corporation", type="Company")
        assert node.properties["name"] == "NVIDIA Corporation"

    def test_name_equals_id(self):
        """name property must equal id."""
        node = GraphNode(id="H100 GPU", type="Product")
        assert node.properties["name"] == node.id

    def test_existing_name_not_overwritten(self):
        """If caller already sets name, it should be preserved."""
        node = GraphNode(
            id="H100",
            type="Product",
            properties={"name": "NVIDIA H100 Tensor Core GPU"},
        )
        assert node.properties["name"] == "NVIDIA H100 Tensor Core GPU"

    def test_extra_properties_preserved(self):
        """Other properties alongside name should survive validation."""
        node = GraphNode(
            id="NVDA",
            type="Company",
            properties={"ticker": "NVDA", "summary": "GPU maker"},
        )
        assert node.properties["ticker"] == "NVDA"
        assert node.properties["summary"] == "GPU maker"
        assert node.properties["name"] == "NVDA"

    def test_empty_properties_default(self):
        """Default properties should be an empty dict (plus injected name)."""
        node = GraphNode(id="TSMC", type="Company")
        assert isinstance(node.properties, dict)
        assert "name" in node.properties

    def test_different_nodes_dont_share_properties(self):
        """Mutable default_factory must not share state between instances."""
        n1 = GraphNode(id="A", type="Company")
        n2 = GraphNode(id="B", type="Company")
        n1.properties["extra"] = "only_n1"
        assert "extra" not in n2.properties


# ===========================================================================
# GraphRelationship
# ===========================================================================

class TestGraphRelationship:

    def test_basic_creation(self):
        rel = GraphRelationship(
            source="NVIDIA Corporation",
            source_type="Company",
            target="AMD",
            target_type="Company",
            type="COMPETES_WITH",
        )
        assert rel.type == "COMPETES_WITH"
        assert rel.properties == {}

    def test_fiscal_year_in_properties(self):
        rel = GraphRelationship(
            source="NVIDIA Corporation",
            source_type="Company",
            target="Data Center",
            target_type="BusinessSegment",
            type="HAS_SEGMENT",
            properties={"fiscal_year": "2024"},
        )
        assert rel.properties["fiscal_year"] == "2024"

    def test_empty_properties_default(self):
        rel = GraphRelationship(
            source="A", source_type="Company",
            target="B", target_type="Company",
            type="COMPETES_WITH",
        )
        assert rel.properties == {}


# ===========================================================================
# GraphExtractionResult
# ===========================================================================

class TestGraphExtractionResult:

    def test_empty_result(self):
        result = GraphExtractionResult()
        assert result.nodes == []
        assert result.relationships == []

    def test_with_nodes_and_rels(self):
        node = GraphNode(id="NVIDIA Corporation", type="Company")
        rel = GraphRelationship(
            source="NVIDIA Corporation", source_type="Company",
            target="Data Center", target_type="BusinessSegment",
            type="HAS_SEGMENT",
        )
        result = GraphExtractionResult(nodes=[node], relationships=[rel])
        assert len(result.nodes) == 1
        assert len(result.relationships) == 1

    def test_name_propagated_in_result(self):
        """Nodes inside a result should still have name set."""
        result = GraphExtractionResult(
            nodes=[GraphNode(id="TSMC", type="Company")]
        )
        assert result.nodes[0].properties["name"] == "TSMC"


# ===========================================================================
# OntologyRegistry — section queries
# ===========================================================================

class TestOntologyRegistrySections:

    @pytest.fixture
    def registry(self):
        return OntologyRegistry()

    def test_get_all_sections(self, registry):
        sections = registry.get_all_sections()
        assert "Item 1" in sections
        assert "Item 1A" in sections
        assert "Item 7" in sections
        assert "Item 10" in sections

    @pytest.mark.parametrize("section,expected_node", [
        ("Item 1",  "BusinessSegment"),
        ("Item 1",  "Company"),
        ("Item 1",  "GeographicMarket"),
        ("Item 1A", "RiskFactor"),
        ("Item 7",  "StrategicInitiative"),
        ("Item 10", "Executive"),
    ])
    def test_get_nodes_contains_expected(self, registry, section, expected_node):
        assert expected_node in registry.get_nodes(section)

    @pytest.mark.parametrize("section,expected_rel", [
        ("Item 1",  "HAS_SEGMENT"),
        ("Item 1",  "COMPETES_WITH"),
        ("Item 1",  "SUPPLIED_BY"),
        ("Item 1A", "HAS_RISK"),
        ("Item 1A", "RELATED_TO"),
        ("Item 7",  "PURSUES"),
        ("Item 10", "HAS_EXECUTIVE"),
    ])
    def test_get_relationships_contains_expected(self, registry, section, expected_rel):
        assert expected_rel in registry.get_relationships(section)

    def test_unknown_section_returns_empty(self, registry):
        assert registry.get_nodes("Item 99") == []
        assert registry.get_relationships("Item 99") == []

    def test_item1_nodes_are_subset_of_catalog(self, registry):
        """Every node type in Item 1 config must exist in NODE_CATALOG."""
        for nt in registry.get_nodes("Item 1"):
            assert nt in NODE_CATALOG, f"Node type '{nt}' missing from NODE_CATALOG"

    def test_all_section_nodes_exist_in_catalog(self, registry):
        """Every node referenced in SECTION_CONFIG must exist in NODE_CATALOG."""
        for section in registry.get_all_sections():
            for nt in registry.get_nodes(section):
                assert nt in NODE_CATALOG, (
                    f"Section '{section}' references unknown node type '{nt}'"
                )

    def test_all_section_relationships_exist_in_catalog(self, registry):
        """Every relationship referenced in SECTION_CONFIG must exist in RELATIONSHIP_CATALOG."""
        for section in registry.get_all_sections():
            for rt in registry.get_relationships(section):
                assert rt in RELATIONSHIP_CATALOG, (
                    f"Section '{section}' references unknown relationship '{rt}'"
                )


# ===========================================================================
# OntologyRegistry — detail queries
# ===========================================================================

class TestOntologyRegistryDetails:

    @pytest.fixture
    def registry(self):
        return OntologyRegistry()

    def test_get_node_hints_known_type(self, registry):
        hints = registry.get_node_hints("Product")
        assert "definition" in hints
        assert "examples" in hints
        assert "properties" in hints
        assert "hint" in hints

    def test_get_node_hints_unknown_type(self, registry):
        assert registry.get_node_hints("NonExistentNode") == {}

    def test_get_relationship_info_known(self, registry):
        info = registry.get_relationship_info("COMPETES_WITH")
        assert info["source_type"] == "Company"
        assert info["target_type"] == "Company"
        assert "description" in info
        assert "hint" in info

    def test_get_relationship_info_unknown(self, registry):
        assert registry.get_relationship_info("FAKE_REL") == {}

    @pytest.mark.parametrize("rel_type,expected_source,expected_target", [
        ("HAS_SEGMENT",   "Company",          "BusinessSegment"),
        ("SUPPLIED_BY",   "Company",          "Company"),
        ("COMPETES_WITH", "Company",          "Company"),
        ("HAS_RISK",      "Company",          "RiskFactor"),
        ("THREATENS",     "RiskFactor",       "BusinessSegment"),
        ("RELATED_TO",    "RiskFactor",       "GeographicMarket"),
        ("HAS_EXECUTIVE", "Company",          "Executive"),
        ("PURSUES",       "Company",          "StrategicInitiative"),
        ("INVOLVES",      "StrategicInitiative", "Technology"),
    ])
    def test_relationship_source_target_types(self, registry, rel_type, expected_source, expected_target):
        info = registry.get_relationship_info(rel_type)
        assert info["source_type"] == expected_source, f"{rel_type} source mismatch"
        assert info["target_type"] == expected_target, f"{rel_type} target mismatch"


# ===========================================================================
# OntologyRegistry — prompt building
# ===========================================================================

class TestBuildSchemaPrompt:

    @pytest.fixture
    def registry(self):
        return OntologyRegistry()

    def test_returns_non_empty_string(self, registry):
        prompt = registry.build_schema_prompt("Item 1")
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_prompt_contains_node_types(self, registry):
        prompt = registry.build_schema_prompt("Item 1")
        for nt in registry.get_nodes("Item 1"):
            assert nt in prompt, f"Node type '{nt}' missing from prompt"

    def test_prompt_contains_relationship_types(self, registry):
        prompt = registry.build_schema_prompt("Item 1A")
        for rt in registry.get_relationships("Item 1A"):
            assert rt in prompt, f"Relationship '{rt}' missing from prompt"

    def test_prompt_contains_focus(self, registry):
        prompt = registry.build_schema_prompt("Item 1A")
        assert "EXTRACTION FOCUS" in prompt

    def test_prompt_unknown_section_returns_empty_ish(self, registry):
        prompt = registry.build_schema_prompt("Item 99")
        # Should not crash; may return minimal string
        assert isinstance(prompt, str)

    @pytest.mark.parametrize("section", ["Item 1", "Item 1A", "Item 7", "Item 10"])
    def test_all_sections_generate_prompt(self, registry, section):
        prompt = registry.build_schema_prompt(section)
        assert len(prompt) > 50, f"Prompt for '{section}' is too short"
