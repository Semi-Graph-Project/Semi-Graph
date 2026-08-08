"""
LLM-driven knowledge graph extraction.

A single DeepSeek call extracts both entities (nodes) and relationships from a
chunk, constrained by the FinReflectKG ontology in semigraph.ontology.schema.

Output passes through:
  1. JSON parsing (tolerant of code fences / prose noise)
  2. Pydantic validation (semigraph.ontology.nodes)
  3. Ontology validation (types must exist in NODE_CATALOG / RELATIONSHIP_CATALOG,
     and relationship endpoints must respect source/target type constraints)

Anything that fails validation is silently dropped — invalid LLM output never
corrupts the graph.
"""
from __future__ import annotations

import json
import re
import time
from typing import List, Optional

from pydantic import ValidationError

from semigraph.ontology.nodes import (
    GraphExtractionResult,
    GraphNode,
    GraphRelationship,
)
from semigraph.ontology.normalization import (
    is_known_product_name,
    normalize_entity_name,
)
from semigraph.ontology.schema import (
    NODE_CATALOG,
    RELATIONSHIP_CATALOG,
    OntologyRegistry,
)


# ===========================================================================
# Prompt
# ===========================================================================

_EXTRACTION_PROMPT = """You are a knowledge graph extractor for SEC 10-K filings.

Given a text chunk, extract entities (nodes) and relationships that are
EXPLICITLY stated. Use ONLY the entity types and relationship types defined
in the schema below.

{schema_block}

# Output format

Return ONLY a valid JSON object with this exact structure:

{{
  "nodes": [
    {{
      "id": "<actual name from text, lowercased, no extra punctuation>",
      "type": "<one of the allowed entity types, UPPERCASE>",
      "properties": {{}}
    }}
  ],
  "relationships": [
    {{
      "source": "<id of source node, must appear in nodes list>",
      "source_type": "<entity type of source, UPPERCASE>",
      "target": "<id of target node, must appear in nodes list>",
      "target_type": "<entity type of target, UPPERCASE>",
      "type": "<one of the allowed relationship types, UPPERCASE>"
    }}
  ]
}}

# Rules

1. Use the ACTUAL name found in the text as the id (e.g. "nvidia", "tsmc",
   "data center segment"). Never use generic ids like "Company_1" or "Risk_A".
2. Lowercase all ids; strip surrounding quotes / punctuation.
3. Both endpoints of every relationship MUST appear in the nodes list.
4. Use ONLY entity types and relationship types from the schema above. Output
   every entity type and relationship endpoint type in UPPERCASE (for example,
   ORG, FIN_METRIC, PRODUCT). Output every relationship type in UPPERCASE
   with underscores (for example, DISCLOSES, HAS_STAKE_IN). The schema may
   display relationship names in lowercase; still output them in UPPERCASE.
5. Respect source/target type constraints — do not link an entity to a
   relationship that does not allow that pair.
6. Do not invent facts. If the text does not state a relationship, omit it.
7. Skip any node or triple you are unsure about.
8. Return at most 60 nodes and 80 relationships per chunk.

# Naming rules — CRITICAL for graph quality

9. NEVER extract pronouns or generic references as entities. Forbidden ids
   include: "the company", "company", "we", "us", "our", "the registrant",
   "it", "they", "them", "the corporation". When the text uses a pronoun,
   resolve it to the actual named entity (e.g. "the company" in an NVIDIA
   filing → "nvidia") and emit that name. If unresolvable, omit the entity.

10. ORG means the filing company that issued this filing. External companies
    mentioned by the filer — competitors, suppliers, customers, partners, or
    counterparties — are type COMP even if they are publicly traded companies
    (e.g. amd, intel, nvidia, tsmc, broadcom when they are not the filer).
    Do NOT tag an external company as ORG just because it is public.

11. Use the SHORTEST canonical form of a company name as the id. Drop legal
    suffixes ("inc", "inc.", "corporation", "corp", "ltd", "limited", "llc",
    "plc"). Examples:
      "NVIDIA Corporation" → "nvidia"
      "Advanced Micro Devices, Inc." → "advanced micro devices"
      "Micron Technology, Inc." → "micron"  (use "micron" not "micron technology")
    For products, use the canonical name without version-prefix variants when
    possible (prefer "amd epyc" over "5th gen amd epyc processors" unless the
    generation is the entity being discussed).

Output JSON only, no commentary, no markdown fences."""


def _build_schema_block(section: str) -> str:
    """Generate the schema description embedded in the system prompt."""
    registry = OntologyRegistry()
    return registry.build_schema_prompt(section)


# ===========================================================================
# JSON parsing — tolerant of LLM noise
# ===========================================================================


def _extract_json_object(text: str) -> dict:
    """
    Pull the first JSON object out of LLM text.
    Handles cases where the model adds prose or markdown fences despite instructions.
    """
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    if start == -1:
        return {}
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return {}
    return {}


# ===========================================================================
# Validation
# ===========================================================================


# Pronoun / generic-reference blacklist — defense in depth against prompt rule 9.
# These should never appear as entities; the LLM should resolve them to the
# actual named entity (e.g. "the company" → "nvidia") or omit them.
_PRONOUN_BLACKLIST: frozenset[str] = frozenset({
    "the company", "company", "we", "us", "our", "the registrant",
    "the registrants", "it", "they", "them", "the corporation",
    "the firm", "the issuer", "the parent", "the group",
})

_MAX_NODES_PER_CHUNK = 60
_MAX_RELATIONSHIPS_PER_CHUNK = 80
_COMPANY_TYPES = {"ORG", "COMP"}


def _normalize_id(value: str, entity_type: str | None = None) -> str:
    """Match the lowercasing + whitespace-stripping rule from the prompt."""
    return normalize_entity_name(value, entity_type)


def _canonical_catalog_key(value: object, catalog: dict) -> str | None:
    """Resolve a case-insensitive LLM label to the catalog's canonical key."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if candidate in catalog:
        return candidate

    lowered = candidate.lower()
    for key in catalog:
        if key.lower() == lowered:
            return key
    return None


def _validate_nodes(raw_nodes: list) -> tuple[List[GraphNode], set[tuple[str, str]]]:
    """
    Filter out nodes whose type is not in the ontology, then build a set of
    (id, type) keys for downstream relationship validation.
    """
    valid: List[GraphNode] = []
    keys: set[tuple[str, str]] = set()

    if not isinstance(raw_nodes, list):
        return valid, keys

    for n in raw_nodes:
        if not isinstance(n, dict):
            continue
        if "id" not in n or "type" not in n:
            continue
        node_type = _canonical_catalog_key(n["type"], NODE_CATALOG)
        if node_type is None:
            continue

        nid = _normalize_id(str(n["id"]), node_type)
        if not nid:
            continue
        if nid in _PRONOUN_BLACKLIST:
            continue

        # Defense in depth: product aliases such as "blackwell" or "rtx"
        # should not become company nodes just because the LLM chose ORG.
        if node_type in _COMPANY_TYPES and is_known_product_name(nid):
            continue

        key = (nid, node_type)
        if key in keys:
            continue

        try:
            node = GraphNode(
                id=nid,
                type=node_type,
                properties=n.get("properties") or {},
            )
        except ValidationError:
            continue

        valid.append(node)
        keys.add(key)

    return valid, keys


def _is_valid_triple(triple: dict, allowed_keys: set[tuple[str, str]]) -> bool:
    """A triple is valid only if both endpoints exist as nodes and the
    relationship type respects the ontology's source/target constraints."""
    if not isinstance(triple, dict):
        return False
    required = {"source", "source_type", "target", "target_type", "type"}
    if not required.issubset(triple.keys()):
        return False

    source_type = _canonical_catalog_key(triple["source_type"], NODE_CATALOG)
    target_type = _canonical_catalog_key(triple["target_type"], NODE_CATALOG)
    rel_type = _canonical_catalog_key(triple["type"], RELATIONSHIP_CATALOG)
    if source_type is None or target_type is None or rel_type is None:
        return False

    src_key = (_normalize_id(str(triple["source"]), source_type), source_type)
    tgt_key = (_normalize_id(str(triple["target"]), target_type), target_type)
    if src_key not in allowed_keys or tgt_key not in allowed_keys:
        return False

    rel_info = RELATIONSHIP_CATALOG[rel_type]
    if rel_info["source_type"] != "any" and rel_info["source_type"] != source_type:
        return False
    if rel_info["target_type"] != "any" and rel_info["target_type"] != target_type:
        return False

    normalized_triple = {
        **triple,
        "source_type": source_type,
        "target_type": target_type,
        "type": rel_type,
    }
    if not _passes_semantic_direction_guard(normalized_triple):
        return False

    return True


def _passes_semantic_direction_guard(triple: dict) -> bool:
    """Reject triples whose endpoint semantics are clearly backwards.

    Ontology type checks catch most errors, but the LLM sometimes assigns a
    company type to a product name. These guards use stable semiconductor
    aliases to prevent high-impact bad edges such as
    `blackwell PRODUCES nvidia` from entering future corpora.
    """
    rel_type = triple["type"]
    src_name = _normalize_id(str(triple["source"]), triple["source_type"])
    tgt_name = _normalize_id(str(triple["target"]), triple["target_type"])
    src_type = triple["source_type"]
    tgt_type = triple["target_type"]

    if rel_type in {"produces", "introduces"}:
        if is_known_product_name(src_name):
            return False
        if tgt_type in _COMPANY_TYPES and not is_known_product_name(tgt_name):
            return False

    if rel_type in {"depends_on", "faces", "subject_to", "discloses"}:
        if is_known_product_name(src_name):
            return False

    if rel_type == "supplies":
        if is_known_product_name(src_name):
            return False
        if tgt_type == "PRODUCT":
            return False

    return True


def _validate_relationships(
    raw_rels: list, allowed_keys: set[tuple[str, str]]
) -> List[GraphRelationship]:
    if not isinstance(raw_rels, list):
        return []

    valid: List[GraphRelationship] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for triple in raw_rels:
        source_type = _canonical_catalog_key(
            triple.get("source_type") if isinstance(triple, dict) else None,
            NODE_CATALOG,
        )
        target_type = _canonical_catalog_key(
            triple.get("target_type") if isinstance(triple, dict) else None,
            NODE_CATALOG,
        )
        rel_type = _canonical_catalog_key(
            triple.get("type") if isinstance(triple, dict) else None,
            RELATIONSHIP_CATALOG,
        )
        if source_type is None or target_type is None or rel_type is None:
            continue

        normalized_triple = {
            **triple,
            "source_type": source_type,
            "target_type": target_type,
            "type": rel_type,
        }
        if not _is_valid_triple(normalized_triple, allowed_keys):
            continue

        source = _normalize_id(str(normalized_triple["source"]), source_type)
        target = _normalize_id(str(normalized_triple["target"]), target_type)
        key = (
            source,
            source_type,
            target,
            target_type,
            rel_type,
        )
        if key in seen:
            continue
        try:
            valid.append(GraphRelationship(
                source=source,
                source_type=source_type,
                target=target,
                target_type=target_type,
                type=rel_type,
                properties=triple.get("properties") or {},
            ))
            seen.add(key)
        except ValidationError:
            continue
    return valid


# ===========================================================================
# Public API
# ===========================================================================


def extract_chunk(
    text: str,
    section: str,
    llm=None,
    metrics_sink: Optional[list] = None,
    chunk_id: str | None = None,
    filer_ticker: str | None = None,
) -> GraphExtractionResult:
    """
    Extract nodes and relationships from a single chunk via one LLM call.

    Args:
        text:         Chunk text.
        section:      Section key e.g. "Item_1A" or "Item 1A" — drives schema selection.
        llm:          Optional LangChain ChatOpenAI client. If None, uses get_llm().
        metrics_sink: Optional list. If provided, one dict per call is appended with
                      {prompt_tokens, completion_tokens, total_tokens, latency_sec}.
                      Caller is responsible for thread-safety; list.append is atomic
                      under CPython GIL so safe for ThreadPoolExecutor use.
        chunk_id:     Optional source Chunk ID supplied as extraction context.
        filer_ticker: Optional ticker identifying the filing company.

    Returns:
        GraphExtractionResult with ontology-valid nodes and relationships.
    """
    if llm is None:
        from semigraph.connections import get_llm
        llm = get_llm()

    section_key = section.replace("_", " ")
    schema_block = _build_schema_block(section_key)

    system_prompt = _EXTRACTION_PROMPT.format(schema_block=schema_block)
    context_lines = ["# Chunk context"]
    if chunk_id:
        context_lines.append(f"Chunk ID: {chunk_id}")
    if filer_ticker:
        context_lines.append(f"Filer ticker: {filer_ticker}")
    if len(context_lines) > 1:
        context_lines.append(
            "Use this metadata to resolve the filing company as an ORG when "
            "the text uses 'we', 'our', or 'the company'."
        )

    user_prompt = (
        "\n".join(context_lines)
        + f"\n\n# Text chunk\n{text}\n\nNow extract nodes and relationships."
    )

    t0 = time.time()
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])
    latency_sec = time.time() - t0
    raw = response.content if hasattr(response, "content") else str(response)

    if metrics_sink is not None:
        usage = getattr(response, "usage_metadata", None) or {}
        metrics_sink.append({
            "prompt_tokens": int(usage.get("input_tokens", 0) or 0),
            "completion_tokens": int(usage.get("output_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
            "latency_sec": round(latency_sec, 3),
        })

    parsed = _extract_json_object(raw)
    if not isinstance(parsed, dict):
        return GraphExtractionResult(nodes=[], relationships=[])

    raw_nodes = parsed.get("nodes", [])
    raw_rels = parsed.get("relationships", [])
    if isinstance(raw_nodes, list):
        raw_nodes = raw_nodes[:_MAX_NODES_PER_CHUNK]
    if isinstance(raw_rels, list):
        raw_rels = raw_rels[:_MAX_RELATIONSHIPS_PER_CHUNK]

    nodes, allowed_keys = _validate_nodes(raw_nodes)
    relationships = _validate_relationships(raw_rels, allowed_keys)


    
    return GraphExtractionResult(nodes=nodes, relationships=relationships)
