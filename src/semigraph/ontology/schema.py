"""
OntologyRegistry — single source of truth for the knowledge graph schema.

Adopts the FinReflectKG ontology (Arun et al., ICAIF '25, arXiv:2508.17906)
which was co-designed by LLM and financial Subject Matter Experts and
validated empirically on 17.5M triples extracted from S&P 500 10-K filings.

Two layers:
  - DOMAIN LAYER  : entity types and relationships from FinReflectKG schema
                    (semantic content of 10-K disclosures)
  - PROVENANCE LAYER: Document / Section / Chunk / FiscalYear
                    (structural anchor for citation tracing)

Usage:
    registry = OntologyRegistry()
    nodes = registry.get_nodes("Item 1A")     # entity types relevant for Item 1A
    rels  = registry.get_relationships("Item 1A")
    prompt_block = registry.build_schema_prompt("Item 1A")
    full_prompt_block = registry.build_schema_prompt(FULL_ONTOLOGY)
"""
from __future__ import annotations

from typing import Dict, List


# ---------------------------------------------------------------------------
# Domain Layer — entity types from FinReflectKG ontology
# ---------------------------------------------------------------------------
NODE_CATALOG: Dict[str, dict] = {
    # ---------- Organizations ----------
    "ORG": {
        "definition": "The filing company that issued the 10-K (the subject of the filing).",
        "examples": ["NVIDIA Corporation", "Advanced Micro Devices", "Intel"],
        "properties": {
            "name": "Official company name (required, lowercased)",
            "ticker": "Stock ticker symbol e.g. NVDA (optional)",
            "summary": "One-line description of the company (optional)",
        },
        "hint": "Extract from the cover page. Each filing has exactly one filer ORG.",
    },
    "COMP": {
        "definition": "External company referenced in the filing — competitor, supplier, customer, or partner. NOT the filer.",
        "examples": ["TSMC", "Samsung Electronics", "Microsoft", "Apple"],
        "properties": {
            "name": "Company name (required, lowercased)",
            "summary": "Brief role mentioned in the filing (optional)",
        },
        "hint": "Look for named third parties in competition, supply chain, or customer concentration discussions.",
    },
    "PERSON": {
        "definition": "Named individual — typically executives or board members.",
        "examples": ["Jensen Huang", "Lisa Su", "Pat Gelsinger"],
        "properties": {
            "name": "Full name (required)",
            "title": "Official title e.g. CEO, CFO, Director (optional)",
        },
        "hint": "Extract from cover page, executive bios, and Item 10. Name + title pairs.",
    },
    "ORG_REG": {
        "definition": "Regulatory body or industry organization.",
        "examples": ["SEC", "FDA", "FTC", "FCC"],
        "properties": {
            "name": "Organization name (required)",
        },
        "hint": "Bodies that regulate or oversee the filer.",
    },
    "ORG_GOV": {
        "definition": "Government entity (executive, legislative, judicial branches).",
        "examples": ["US Treasury", "Department of Commerce", "European Commission"],
        "properties": {"name": "Government entity name (required)"},
        "hint": "Distinct from regulators — these are policy-making/governing bodies.",
    },

    # ---------- Business structure ----------
    "SEGMENT": {
        "definition": "Internal business division or operating segment of the filer.",
        "examples": ["Data Center", "Gaming", "Professional Visualization", "Cloud"],
        "properties": {
            "name": "Segment name (required)",
            "summary": "What this segment sells and serves (optional)",
        },
        "hint": "Look for 'our reportable segments' or 'we operate through' phrases.",
    },
    "PRODUCT": {
        "definition": "A specific named product, platform, or service offering.",
        "examples": ["H100 GPU", "CUDA", "GeForce RTX", "Xeon"],
        "properties": {
            "name": "Product name (required)",
            "summary": "What it does (optional)",
        },
        "hint": "Named products only. Avoid generic 'our chips' phrasing.",
    },

    # ---------- Financial concepts (NAMES, not values) ----------
    "FIN_METRIC": {
        "definition": (
            "A named financial metric or measure. The CONCEPT, not a value. "
            "Numeric values are stored in PostgreSQL, not in the graph."
        ),
        "examples": ["revenue", "gross margin", "operating income", "R&D expense"],
        "properties": {"name": "Metric name (required, lowercased)"},
        "hint": "Extract metric names mentioned in narrative discussion (MD&A, Risk Factors).",
    },
    "FIN_INST": {
        "definition": "Financial instrument issued, held, or referenced.",
        "examples": ["common stock", "convertible note", "treasury bond", "warrant"],
        "properties": {"name": "Instrument name (required)"},
        "hint": "Extract from Item 5 (equity), Item 8 (financial statements), capitalization discussions.",
    },
    "FIN_MARKET": {
        "definition": "Stock exchange, market, or financial index.",
        "examples": ["NASDAQ", "NYSE", "S&P 500", "PHLX Semiconductor Index"],
        "properties": {"name": "Market name (required)"},
        "hint": "Where the filer is listed or benchmarked against.",
    },
    "FIN_ASSET": {
        "definition": "A financial asset class held or managed by the company.",
        "examples": ["money market funds", "corporate bonds", "marketable securities"],
        "properties": {"name": "Asset class name (required)"},
        "hint": "From investments/cash equivalents discussion.",
    },
    "ACCOUNTING_POLICY": {
        "definition": "An accounting policy, standard, or methodology applied by the filer.",
        "examples": ["revenue recognition", "ASC 606", "fair value measurement", "lease accounting"],
        "properties": {"name": "Policy name (required)"},
        "hint": "Look in 'Significant Accounting Policies' note and Item 7 narrative.",
    },

    # ---------- Risk and macro ----------
    "RISK_FACTOR": {
        "definition": "A specific risk that could materially affect the business. Each major risk paragraph = one node.",
        "examples": ["china export controls", "customer concentration", "tsmc supply dependency", "cybersecurity breach"],
        "properties": {
            "name": "Short descriptive title of the risk (required)",
            "summary": "What could happen and the potential impact (optional, 1-3 sentences)",
        },
        "hint": "Extract from Item 1A. Use descriptive titles, not 'Risk 1'.",
    },
    "MACRO_CONDITION": {
        "definition": "A macroeconomic condition that influences the business.",
        "examples": ["inflation", "interest rate hike", "recession", "supply chain disruption"],
        "properties": {"name": "Condition name (required)"},
        "hint": "Look for economy-wide forces mentioned as drivers or risks.",
    },
    "ECON_IND": {
        "definition": "An economic indicator referenced in disclosures.",
        "examples": ["consumer price index", "GDP growth", "unemployment rate"],
        "properties": {"name": "Indicator name (required)"},
        "hint": "Specific quantitative indicators of macroeconomic state.",
    },

    # ---------- Regulation and events ----------
    "REGULATORY_REQUIREMENT": {
        "definition": "A specific regulation, law, or compliance framework.",
        "examples": ["Sarbanes-Oxley", "GDPR", "CHIPS Act", "Dodd-Frank"],
        "properties": {"name": "Regulation name (required)"},
        "hint": "Named acts, frameworks, or requirements the filer must comply with.",
    },
    "EVENT": {
        "definition": "A material event — M&A, litigation, restructuring, announcement, natural disaster.",
        "examples": ["acquisition of mellanox", "covid-19 pandemic", "patent infringement lawsuit"],
        "properties": {
            "name": "Event name or description (required)",
            "date": "Approximate date if mentioned (optional)",
        },
        "hint": "From Item 1A risks, Item 7 MD&A, subsequent events, or note disclosures.",
    },

    # ---------- Geography and supply ----------
    "GPE": {
        "definition": "Geo-Political Entity — a country, region, state, or jurisdictional area.",
        "examples": ["United States", "China", "Taiwan", "Greater China", "European Union"],
        "properties": {
            "name": "Standardized geographic name (required)",
        },
        "hint": "Use canonical names. 'Greater China' not 'China' if filing uses that term.",
    },
    "RAW_MATERIAL": {
        "definition": "A raw material or input critical to operations (especially for semiconductors).",
        "examples": ["silicon wafers", "neon gas", "rare earth metals", "gallium"],
        "properties": {"name": "Material name (required)"},
        "hint": "Critical for semi domain — supply chain dependency analysis.",
    },

    # ---------- ESG ----------
    "ESG_TOPIC": {
        "definition": "An Environmental, Social, or Governance topic disclosed by the company.",
        "examples": ["carbon emissions", "diversity equity inclusion", "climate risk", "human rights"],
        "properties": {"name": "Topic name (required)"},
        "hint": "From sustainability/ESG disclosures or related risk factors.",
    },

    # ---------- Provenance Layer (structural) ----------
    "Document": {
        "definition": "A 10-K filing document (one filing = one Document node).",
        "examples": ["NVDA 10-K 2024", "AMD 10-K 2023"],
        "properties": {
            "id": "Stable id e.g. NVDA_10K_2024 (required)",
            "ticker": "Filing ticker (required)",
            "fiscal_year": "Fiscal year (required, integer)",
            "source_file": "Original filename (required)",
        },
        "hint": "Provenance node. One per filing. Anchor for citation tracing.",
    },
    "Section": {
        "definition": "A section within a 10-K document (e.g. Item 1, 1A, 7).",
        "examples": ["Item 1", "Item 1A", "Item 7"],
        "properties": {
            "id": "Composite id e.g. NVDA_10K_2024__Item_1A (required)",
            "name": "Section name (required)",
        },
        "hint": "Provenance node linking Document to Chunks.",
    },
    "Chunk": {
        "definition": "A token-aware text chunk extracted from a Section. Vector index lives on this node.",
        "examples": ["chunk_1", "chunk_42"],
        "properties": {
            "id": "Composite id e.g. NVDA_10K_2024__Item_1A__chunk_5 (required)",
            "text": "The chunk text content (required)",
            "embedding": "Vector embedding (required for retrieval)",
            "page_id": "Source page (optional)",
        },
        "hint": "Provenance node + retrieval target. Domain entities link via MENTIONS.",
    },
    "FiscalYear": {
        "definition": "A fiscal year used as a temporal anchor.",
        "examples": ["2022", "2023", "2024"],
        "properties": {
            "name": "4-digit year string (required)",
            "year": "Integer year (required)",
        },
        "hint": "Temporal anchor for cross-year queries.",
    },
}


# ---------------------------------------------------------------------------
# Domain Layer — relationship types from FinReflectKG ontology
# Source/target constraints follow the most common patterns in the dataset.
# ---------------------------------------------------------------------------
RELATIONSHIP_CATALOG: Dict[str, dict] = {
    # ---------- Disclosure (most common, ~40% of triples) ----------
    "discloses": {
        "source_type": "ORG",
        "target_type": "any",
        "description": "Filer discloses information about the target entity.",
        "hint": "Generic disclosure relationship. Use when more specific verb does not apply.",
    },

    # ---------- Business structure ----------
    "has_stake_in": {
        "source_type": "ORG",
        "target_type": "SEGMENT",
        "description": "Company has full or partial ownership/equity interest.",
        "hint": "Reportable segments or owned subsidiaries.",
    },
    "operates_in": {
        "source_type": "ORG",
        "target_type": "GPE",
        "description": "Company has operations or revenue in this geographic area.",
        "hint": "Geographic revenue breakdown or operational footprint.",
    },
    "produces": {
        "source_type": "ORG",
        "target_type": "PRODUCT",
        "description": "Company manufactures or develops the product.",
        "hint": "Look for 'we produce', 'we manufacture', 'our product line includes'.",
    },
    "supplies": {
        "source_type": "COMP",
        "target_type": "ORG",
        "description": "External company supplies the filer with materials/components.",
        "hint": "Inverted: the supplier is the source, filer is the target.",
    },
    "partners_with": {
        "source_type": "ORG",
        "target_type": "COMP",
        "description": "Strategic partnership or collaboration.",
        "hint": "Joint ventures, licensing deals, technology partnerships.",
    },
    "competes_with": {
        "source_type": "ORG",
        "target_type": "COMP",
        "description": "Direct competitive relationship.",
        "hint": "Look for 'competitors include', 'we compete with'.",
    },

    # ---------- Dependency and impact ----------
    "depends_on": {
        "source_type": "ORG",
        "target_type": "any",
        "description": "Filer depends on the target (supplier, raw material, etc).",
        "hint": "Sole-source supplier or critical input dependency.",
    },
    "impacts": {
        "source_type": "any",
        "target_type": "any",
        "description": "Source has an effect on the target (direction unspecified).",
        "hint": "Generic impact verb. Prefer positively_impacts/negatively_impacts when direction is clear.",
    },
    "impacted_by": {
        "source_type": "any",
        "target_type": "any",
        "description": "Source is affected by the target.",
        "hint": "Inverse of impacts.",
    },
    "positively_impacts": {
        "source_type": "any",
        "target_type": "any",
        "description": "Source has a beneficial effect on the target.",
        "hint": "ESG initiatives, R&D investments, partnerships that improve metrics.",
    },
    "negatively_impacts": {
        "source_type": "any",
        "target_type": "any",
        "description": "Source has a harmful effect on the target.",
        "hint": "Risk factors, macro conditions, regulatory burdens.",
    },
    "causes_shortage_of": {
        "source_type": "EVENT",
        "target_type": "RAW_MATERIAL",
        "description": "Event causes a shortage of the named raw material.",
        "hint": "Geopolitical events, natural disasters, export controls affecting supply.",
    },

    # ---------- Regulation ----------
    "complies_with": {
        "source_type": "ORG",
        "target_type": "REGULATORY_REQUIREMENT",
        "description": "Filer must comply with the regulation.",
        "hint": "Look for 'we are subject to', 'we must comply with'.",
    },
    "subject_to": {
        "source_type": "ORG",
        "target_type": "any",
        "description": "Filer is subject to a regulation, oversight, or condition.",
        "hint": "Stronger than complies_with — implies obligation.",
    },
    "regulates": {
        "source_type": "ORG_REG",
        "target_type": "ORG",
        "description": "Regulator oversees or regulates the filer.",
        "hint": "Inverse perspective from complies_with.",
    },

    # ---------- Strategic actions ----------
    "invests_in": {
        "source_type": "ORG",
        "target_type": "any",
        "description": "Company invests in target (R&D area, technology, segment, ESG topic).",
        "hint": "Capital allocation discussions in MD&A.",
    },
    "introduces": {
        "source_type": "ORG",
        "target_type": "any",
        "description": "Company introduces a new product, policy, or initiative.",
        "hint": "Product launches, policy changes, new programs.",
    },
    "announces": {
        "source_type": "ORG",
        "target_type": "EVENT",
        "description": "Company makes a formal announcement of an event.",
        "hint": "Earnings, M&A, restructuring announcements.",
    },
    "involved_in": {
        "source_type": "ORG",
        "target_type": "EVENT",
        "description": "Company is involved in an event (litigation, M&A, etc).",
        "hint": "Active participation, not passive impact.",
    },

    # ---------- Risk verbs ----------
    "faces": {
        "source_type": "ORG",
        "target_type": "RISK_FACTOR",
        "description": "Company faces this risk.",
        "hint": "Often paired with risk factor disclosure.",
    },
    "guides_on": {
        "source_type": "ORG",
        "target_type": "FIN_METRIC",
        "description": "Company provides forward guidance on the metric.",
        "hint": "MD&A forward-looking statements.",
    },

    # ---------- Industry membership ----------
    "listed_on": {
        "source_type": "ORG",
        "target_type": "FIN_MARKET",
        "description": "Company stock is listed on the named market.",
        "hint": "From cover page or capitalization discussion.",
    },

    # ---------- Provenance Layer edges ----------
    "CONTAINS_SECTION": {
        "source_type": "Document",
        "target_type": "Section",
        "description": "Document contains the section.",
        "hint": "Provenance — exactly one edge per (doc, section) pair.",
    },
    "HAS_CHUNK": {
        "source_type": "Section",
        "target_type": "Chunk",
        "description": "Section contains the chunk.",
        "hint": "Provenance — created during chunking.",
    },
    "NEXT_CHUNK": {
        "source_type": "Chunk",
        "target_type": "Chunk",
        "description": "Sequential link to the next chunk in the same section.",
        "hint": "Provenance — enables 'read more' navigation.",
    },
    "MENTIONS": {
        "source_type": "Chunk",
        "target_type": "any",
        "description": "Bridge edge — chunk text mentions a domain entity.",
        "hint": "Provenance bridge. Created whenever an entity is extracted from a chunk.",
    },
    "FILED_BY": {
        "source_type": "Document",
        "target_type": "ORG",
        "description": "Document was filed by the company.",
        "hint": "Provenance — anchors document to its filer.",
    },
    "FOR_FISCAL_YEAR": {
        "source_type": "Document",
        "target_type": "FiscalYear",
        "description": "Document covers the fiscal year.",
        "hint": "Provenance — temporal anchor.",
    },
}


# ---------------------------------------------------------------------------
# Section → recommended entity / relationship sets for extraction
#
# Used to focus GLiNER's label set and DeepSeek's extraction prompt per Item.
# This is an EFFICIENCY hint; the underlying ontology is the same across all sections.
# ---------------------------------------------------------------------------
SECTION_CONFIG: Dict[str, dict] = {
    "Item 1": {
        "nodes": [
            "ORG", "COMP", "SEGMENT", "PRODUCT",
            "GPE", "FIN_MARKET", "RAW_MATERIAL","REGULATORY_REQUIREMENT","EVENT"
        ],
        "relationships": [
            "has_stake_in", "operates_in", "produces", "supplies",
            "partners_with", "competes_with", "listed_on", "depends_on","subject_to",
            "introduces","invests_in","announces","involved_in"
        ],
        "focus": (
            "Extract company structure: segments, products, named competitors, "
            "suppliers, customers, and geographic footprint."
        ),
    },
    "Item 1A": {
        "nodes": [
            "ORG", "RISK_FACTOR", "MACRO_CONDITION", "EVENT",
            "REGULATORY_REQUIREMENT", "GPE", "RAW_MATERIAL", "COMP", "PRODUCT",
            "SEGMENT", "FIN_METRIC"
        ],
        "relationships": [
            "discloses", "faces", "negatively_impacts", "depends_on",
            "subject_to", "causes_shortage_of", "impacted_by",
            "has_stake_in", "produces" , "competes_with" , "supplies"
        ],
        "focus": (
            "Extract every material risk factor as a separate node. "
            "Link risks to macro conditions, geographies, and segments where stated."
        ),
    },
    "Item 7": {
        "nodes": [
            "ORG", "SEGMENT", "FIN_METRIC", "ACCOUNTING_POLICY",
            "EVENT", "MACRO_CONDITION", "ESG_TOPIC", "PRODUCT",
            "COMP", "GPE" , "REGULATORY_REQUIREMENT"
        ],
        "relationships": [
            "discloses", "guides_on", "invests_in", "introduces",
            "announces", "positively_impacts", "negatively_impacts",
            "involved_in", "has_stake_in" , "produces" , "depends_on",
            "subject_to", "operates_in"
        ],
        "focus": (
            "Extract management discussion themes: financial drivers, strategic initiatives, "
            "investments, and qualitative performance commentary."
        ),
    },
}


# ---------------------------------------------------------------------------
# Extraction modes and provenance boundaries
# ---------------------------------------------------------------------------

FULL_ONTOLOGY = "Full Ontology"

_PROVENANCE_NODE_TYPES = frozenset({
    "Document", "Section", "Chunk", "FiscalYear",
})

_PROVENANCE_RELATIONSHIP_TYPES = frozenset({
    "CONTAINS_SECTION", "HAS_CHUNK", "NEXT_CHUNK", "MENTIONS",
    "FILED_BY", "FOR_FISCAL_YEAR",
})

_FULL_ONTOLOGY_ALIASES = frozenset({
    "all", "full ontology", "full_ontology",
})


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
class OntologyRegistry:
    """
    Provides query methods over NODE_CATALOG, RELATIONSHIP_CATALOG, SECTION_CONFIG.
    Stateless — instantiate once and reuse.
    """

    # ------------------------------------------------------------------ #
    # Section-level queries
    # ------------------------------------------------------------------ #

    @staticmethod
    def is_full_ontology(section: str) -> bool:
        """Return whether ``section`` requests the complete domain ontology."""
        normalized = section.strip().lower().replace("-", " ")
        return normalized in _FULL_ONTOLOGY_ALIASES

    def get_nodes(self, section: str) -> List[str]:
        """Return node types for a section or the complete domain ontology."""
        if self.is_full_ontology(section):
            return self.all_domain_node_types()
        return SECTION_CONFIG.get(section, {}).get("nodes", [])

    def get_relationships(self, section: str) -> List[str]:
        """Return relationship types for a section or the complete domain ontology."""
        if self.is_full_ontology(section):
            return self.all_domain_relationship_types()
        return SECTION_CONFIG.get(section, {}).get("relationships", [])

    def get_all_sections(self) -> List[str]:
        return list(SECTION_CONFIG.keys())

    # ------------------------------------------------------------------ #
    # Catalogue lookups
    # ------------------------------------------------------------------ #

    def get_node_hints(self, node_type: str) -> dict:
        return NODE_CATALOG.get(node_type, {})

    def get_relationship_info(self, rel_type: str) -> dict:
        return RELATIONSHIP_CATALOG.get(rel_type, {})

    def all_domain_node_types(self) -> List[str]:
        """Domain-layer node types only (excludes provenance)."""
        return [t for t in NODE_CATALOG if t not in _PROVENANCE_NODE_TYPES]

    def all_domain_relationship_types(self) -> List[str]:
        """Domain-layer relationships, excluding structural provenance edges."""
        return [
            r for r in RELATIONSHIP_CATALOG
            if r not in _PROVENANCE_RELATIONSHIP_TYPES
        ]

    # ------------------------------------------------------------------ #
    # Prompt building
    # ------------------------------------------------------------------ #

    def build_schema_prompt(self, section: str) -> str:
        """
        Build a formatted string describing nodes and relationships for a section.

        Passing ``Full Ontology`` (or the aliases ``all``/``full_ontology``)
        selects all FinReflectKG domain types. Provenance relationships such as
        ``MENTIONS`` are intentionally excluded because KGStore creates them.

        Designed to be embedded directly in an LLM extraction prompt.
        """
        node_types = self.get_nodes(section)
        rel_types = self.get_relationships(section)
        if self.is_full_ontology(section):
            focus = (
                "Extract every explicitly stated domain entity and relationship "
                "using the complete FinReflectKG ontology."
            )
        else:
            focus = SECTION_CONFIG.get(section, {}).get("focus", "")

        lines: List[str] = []

        if focus:
            lines.append(f"EXTRACTION FOCUS: {focus}\n")

        lines.append("=== ALLOWED ENTITY TYPES ===")
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
