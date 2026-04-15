"""
OntologyRegistry — single source of truth for the knowledge graph schema.

Defines:
  - NODE_CATALOG       : all allowed node types with extraction hints for LLM prompts
  - RELATIONSHIP_CATALOG: all allowed relationship types with source/target constraints
  - SECTION_CONFIG     : which nodes/relationships to extract from each 10-K section

Usage:
    registry = OntologyRegistry()
    nodes = registry.get_nodes("Item 1")          # ["Company", "BusinessSegment", ...]
    rels  = registry.get_relationships("Item 1A") # ["HAS_RISK", "THREATENS", ...]
    prompt_block = registry.build_schema_prompt("Item 1")  # formatted string for LLM
"""
from __future__ import annotations

from typing import Dict, List


# ---------------------------------------------------------------------------
# Node catalogue
# Each entry has: definition, examples, properties, hint
# ---------------------------------------------------------------------------
NODE_CATALOG: Dict[str, dict] = {
    "Company": {
        "definition": (
            "A legal corporate entity. For cross-company relationships (competitors, "
            "suppliers, customers), create a Company node for the other company too."
        ),
        "examples": [
            "NVIDIA Corporation",
            "Taiwan Semiconductor Manufacturing Company",
            "Advanced Micro Devices",
        ],
        "properties": {
            "name": "Official company name — set equal to id (required)",
            "ticker": "Stock symbol e.g. NVDA (optional)",
            "summary": "1-2 sentence description of what the company does (required)",
        },
        "hint": (
            "Extract from cover page. When competitors, suppliers, or customers are named "
            "in text, create a Company node for them too."
        ),
    },

    "BusinessSegment": {
        "definition": "A GAAP-reportable operating division of the company.",
        "examples": ["Data Center", "Gaming", "Professional Visualization", "Automotive"],
        "properties": {
            "name": "Official segment name (required)",
            "summary": "What this segment sells and to whom (required)",
        },
        "hint": (
            "Only formal reportable segments — not generic product categories. "
            "Look for 'our reportable segments are' or 'we operate through'."
        ),
    },

    "Product": {
        "definition": "A specific named product, platform, or service offering.",
        "examples": ["H100 GPU", "CUDA", "GeForce RTX 4090", "DGX SuperPOD", "NVIDIA AI Enterprise"],
        "properties": {
            "name": "Product name (required)",
            "category": "GPU / Software / Platform / Service / Other (optional)",
            "summary": "What this product does and who buys it (required)",
        },
        "hint": "Named products/platforms only. Avoid generic phrases like 'our chips' — look for proper nouns.",
    },

    "Technology": {
        "definition": "A core proprietary technology, architecture, or technical platform.",
        "examples": ["Transformer Engine", "NVLink", "Hopper Architecture", "CUDA", "InfiniBand"],
        "properties": {
            "name": "Technology name (required)",
            "summary": "What it does and why it matters competitively (required)",
        },
        "hint": "Proprietary or specifically named technology. Not vague terms like 'AI technology'.",
    },

    "GeographicMarket": {
        "definition": "A specific country, region, or geographic area of operation or revenue.",
        "examples": ["United States", "Greater China", "EMEA", "Taiwan", "Japan"],
        "properties": {
            "name": "Standardized region or country name (required)",
            "type": "Country / Region / Continent (optional)",
        },
        "hint": (
            "Use standardized names: 'Greater China' not just 'China'. "
            "Extract from geographic revenue breakdown or operational footprint."
        ),
    },

    "Industry": {
        "definition": (
            "An industry or market sector. Shared node across companies — "
            "do NOT create a new one per filing."
        ),
        "examples": ["Semiconductor", "Data Center Infrastructure", "Automotive AI", "Cloud Computing"],
        "properties": {
            "name": "Industry name (required)",
            "summary": "Brief description of what this industry covers (optional)",
        },
        "hint": "High-level classification. Can connect multiple companies in cross-company analysis.",
    },

    "RiskFactor": {
        "definition": (
            "A specific risk factor from Item 1A that could materially affect the business. "
            "Each major risk paragraph = one node."
        ),
        "examples": [
            "China export control restrictions",
            "Customer concentration risk",
            "TSMC supply dependency",
            "Cybersecurity breach risk",
        ],
        "properties": {
            "name": "Short descriptive title of the risk (required)",
            "category": "Geopolitical / Regulatory / Operational / Financial / Competitive / Technology (required)",
            "summary": (
                "Full risk: what could happen AND what the impact would be. "
                "1-3 sentences (required)"
            ),
        },
        "hint": (
            "Do NOT use generic names like 'Risk 1'. "
            "Derive a descriptive title from the risk paragraph header or first sentence."
        ),
    },

    "Executive": {
        "definition": "A named executive officer or board director.",
        "examples": ["Jensen Huang", "Colette Kress", "Dawn Hudson"],
        "properties": {
            "name": "Full name (required)",
            "title": "Official title e.g. CEO, CFO, President, Director (required)",
            "summary": "Brief background if mentioned in text (optional)",
        },
        "hint": "Found in Item 10 (Directors & Executive Officers). Extract name+title pairs.",
    },

    "StrategicInitiative": {
        "definition": (
            "A named strategic program, R&D effort, acquisition, partnership, "
            "or major business initiative mentioned in MD&A."
        ),
        "examples": [
            "Blackwell Architecture Development",
            "Automotive AI Platform Roadmap",
            "NVIDIA AI Enterprise Expansion",
        ],
        "properties": {
            "name": "Initiative name or a short descriptive label (required)",
            "type": "R&D / Acquisition / Partnership / CostReduction / Expansion / Other (required)",
            "summary": "What this initiative aims to achieve and why (required)",
        },
        "hint": (
            "Look for 'we are investing in', 'we plan to', 'our strategy includes', "
            "'we acquired', 'we partnered with' in MD&A (Item 7)."
        ),
    },

    "FiscalYear": {
        "definition": "A fiscal year used as a temporal anchor node.",
        "examples": ["2024", "2023", "2022"],
        "properties": {
            "name": "4-digit year string (required)",
            "year": "Same value as integer (required)",
        },
        "hint": "Extract from 'For the fiscal year ended ...' on the document cover page.",
    },
}


# ---------------------------------------------------------------------------
# Relationship catalogue
# Each entry has: source_type, target_type, description, hint
# ---------------------------------------------------------------------------
RELATIONSHIP_CATALOG: Dict[str, dict] = {
    # --- Business structure ---
    "HAS_SEGMENT": {
        "source_type": "Company",
        "target_type": "BusinessSegment",
        "description": "Company operates this business segment.",
        "hint": "Every named segment links back to the filing company via HAS_SEGMENT.",
    },
    "OFFERS": {
        "source_type": "BusinessSegment",
        "target_type": "Product",
        "description": "Segment offers this product or service.",
        "hint": "Products listed under or described as part of a segment.",
    },
    "BUILT_ON": {
        "source_type": "Product",
        "target_type": "Technology",
        "description": "Product is powered by or built on this technology.",
        "hint": "Look for 'powered by', 'built on', 'uses', 'based on'.",
    },
    "OPERATES_IN": {
        "source_type": "Company",
        "target_type": "GeographicMarket",
        "description": "Company has significant operations or revenue in this market.",
        "hint": "Geographic revenue segments or 'we operate in X' statements.",
    },
    "IN_INDUSTRY": {
        "source_type": "Company",
        "target_type": "Industry",
        "description": "Company belongs to this industry or competes in this market sector.",
        "hint": "Industry classification on cover page or business description.",
    },

    # --- Cross-company (Porter's 5 Forces) ---
    "COMPETES_WITH": {
        "source_type": "Company",
        "target_type": "Company",
        "description": "Direct competitive relationship between two companies.",
        "hint": (
            "Look for 'competitors include', 'we compete with', 'competitive landscape', "
            "or any named rivals. Create a Company node for each."
        ),
    },
    "SUPPLIED_BY": {
        "source_type": "Company",
        "target_type": "Company",
        "description": "Filing company depends on another company as a key supplier or foundry.",
        "hint": (
            "Look for 'manufactured by', 'supplied by', 'third-party foundry', "
            "'sole source supplier', 'we rely on X to manufacture'."
        ),
    },
    "SELLS_TO": {
        "source_type": "Company",
        "target_type": "Company",
        "description": "Filing company sells a significant portion of revenue to this customer company.",
        "hint": (
            "Look for 'major customer', 'significant customer', 'revenue concentration', "
            "or named customers that represent >10% of revenue."
        ),
    },
    "SUBSTITUTED_BY": {
        "source_type": "Product",
        "target_type": "Product",
        "description": "This product faces a substitute threat from another product.",
        "hint": "Look for 'alternative to', 'could be replaced by', 'substitute'.",
    },

    # --- Risk ---
    "HAS_RISK": {
        "source_type": "Company",
        "target_type": "RiskFactor",
        "description": "Company discloses this risk factor in its filing.",
        "hint": "Every RiskFactor extracted from Item 1A links to the filing company via HAS_RISK.",
    },
    "THREATENS": {
        "source_type": "RiskFactor",
        "target_type": "BusinessSegment",
        "description": "Risk factor could materially harm this specific business segment.",
        "hint": "Only when the risk explicitly names or clearly implies impact on a specific segment.",
    },
    "RELATED_TO": {
        "source_type": "RiskFactor",
        "target_type": "GeographicMarket",
        "description": "Risk factor is geographically specific to this market.",
        "hint": (
            "China export controls → RELATED_TO 'Greater China'. "
            "Tariff risks → RELATED_TO specific country or region."
        ),
    },

    # --- People & Strategy (Fisher's 15 Points) ---
    "HAS_EXECUTIVE": {
        "source_type": "Company",
        "target_type": "Executive",
        "description": "Company has this person in a named leadership role.",
        "hint": "From Item 10. Every named officer/director gets this relationship.",
    },
    "PURSUES": {
        "source_type": "Company",
        "target_type": "StrategicInitiative",
        "description": "Company is actively pursuing this strategic initiative.",
        "hint": "From MD&A (Item 7). R&D programs, acquisitions, partnerships, growth plans.",
    },
    "INVOLVES": {
        "source_type": "StrategicInitiative",
        "target_type": "Technology",
        "description": "Strategic initiative focuses on or uses this technology.",
        "hint": "R&D initiative centred on a specific technology area.",
    },
    "TARGETS": {
        "source_type": "StrategicInitiative",
        "target_type": "BusinessSegment",
        "description": "Strategic initiative aims to grow or improve this segment.",
        "hint": "Initiative is explicitly discussed in the context of a specific segment.",
    },
}


# ---------------------------------------------------------------------------
# Section → nodes / relationships mapping
# ---------------------------------------------------------------------------
SECTION_CONFIG: Dict[str, dict] = {
    "Item 1": {
        "nodes": [
            "Company", "BusinessSegment", "Product", "Technology",
            "GeographicMarket", "Industry", "FiscalYear",
        ],
        "relationships": [
            "HAS_SEGMENT", "OFFERS", "BUILT_ON", "OPERATES_IN", "IN_INDUSTRY",
            "COMPETES_WITH", "SUPPLIED_BY", "SELLS_TO",
        ],
        "focus": (
            "Extract company structure, named products, core technologies, geographic markets, "
            "and all explicitly named competitors, suppliers, and customers."
        ),
    },

    "Item 1A": {
        "nodes": ["Company", "RiskFactor", "GeographicMarket", "BusinessSegment"],
        "relationships": ["HAS_RISK", "THREATENS", "RELATED_TO"],
        "focus": (
            "Extract every material risk factor as a separate node. "
            "Link risks to geographies and segments where explicitly stated."
        ),
    },

    "Item 7": {
        "nodes": [
            "Company", "StrategicInitiative", "Technology",
            "BusinessSegment", "GeographicMarket",
        ],
        "relationships": ["PURSUES", "INVOLVES", "TARGETS"],
        "focus": (
            "Extract strategic initiatives, R&D investments, and qualitative performance "
            "drivers from the MD&A narrative. Avoid extracting raw financial numbers."
        ),
    },

    "Item 10": {
        "nodes": ["Company", "Executive"],
        "relationships": ["HAS_EXECUTIVE"],
        "focus": "Extract all named executive officers and directors with their official titles.",
    },
}


# ---------------------------------------------------------------------------
# Registry class
# ---------------------------------------------------------------------------
class OntologyRegistry:
    """
    Provides query methods over NODE_CATALOG, RELATIONSHIP_CATALOG, SECTION_CONFIG.
    Stateless — instantiate once and reuse.
    """

    # ------------------------------------------------------------------ #
    # Section-level queries
    # ------------------------------------------------------------------ #

    def get_nodes(self, section: str) -> List[str]:
        """Return allowed node type names for a given 10-K section."""
        return SECTION_CONFIG.get(section, {}).get("nodes", [])

    def get_relationships(self, section: str) -> List[str]:
        """Return allowed relationship type names for a given 10-K section."""
        return SECTION_CONFIG.get(section, {}).get("relationships", [])

    def get_all_sections(self) -> List[str]:
        """Return all configured section names."""
        return list(SECTION_CONFIG.keys())

    # ------------------------------------------------------------------ #
    # Node / relationship detail queries
    # ------------------------------------------------------------------ #

    def get_node_hints(self, node_type: str) -> dict:
        """
        Return the full catalogue entry for a node type.
        Returns empty dict if node_type is unknown.
        """
        return NODE_CATALOG.get(node_type, {})

    def get_relationship_info(self, rel_type: str) -> dict:
        """
        Return the catalogue entry for a relationship type.
        Returns empty dict if rel_type is unknown.
        """
        return RELATIONSHIP_CATALOG.get(rel_type, {})

    # ------------------------------------------------------------------ #
    # Prompt building
    # ------------------------------------------------------------------ #

    def build_schema_prompt(self, section: str) -> str:
        """
        Build a formatted string describing nodes and relationships for a section.
        Designed to be embedded directly in an LLM system prompt.
        """
        node_types = self.get_nodes(section)
        rel_types = self.get_relationships(section)
        focus = SECTION_CONFIG.get(section, {}).get("focus", "")

        lines: List[str] = []

        if focus:
            lines.append(f"EXTRACTION FOCUS: {focus}\n")

        # --- Nodes ---
        lines.append("=== ALLOWED NODE TYPES ===")
        for nt in node_types:
            info = NODE_CATALOG.get(nt, {})
            if not info:
                lines.append(f"**{nt}**: (no definition)\n")
                continue
            examples = ", ".join(f'"{e}"' for e in info.get("examples", [])[:3])
            props = "; ".join(
                f"{k}: {v}" for k, v in info.get("properties", {}).items()
            )
            lines.append(
                f"**{nt}**\n"
                f"  Definition : {info.get('definition', '')}\n"
                f"  Examples   : {examples}\n"
                f"  Properties : {props}\n"
                f"  Hint       : {info.get('hint', '')}\n"
            )

        # --- Relationships ---
        lines.append("=== ALLOWED RELATIONSHIP TYPES ===")
        for rt in rel_types:
            info = RELATIONSHIP_CATALOG.get(rt, {})
            if not info:
                lines.append(f"**{rt}**: (no definition)\n")
                continue
            lines.append(
                f"**{rt}**  ({info.get('source_type')} → {info.get('target_type')})\n"
                f"  {info.get('description', '')}\n"
                f"  Hint: {info.get('hint', '')}\n"
            )

        return "\n".join(lines)
