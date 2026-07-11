"""Shared FinReflectKG import and benchmark conventions.

The Hugging Face release stores one extracted triplet per parquet row. Chunk
identifiers are only page-local, so this module defines the canonical IDs and
ontology normalization used by both the importer and benchmark converter.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable
import re


REFERENCE_ENTITY_TYPES = frozenset({
    "ORG",
    "ORG_GOV",
    "ORG_REG",
    "GPE",
    "PERSON",
    "COMP",
    "PRODUCT",
    "EVENT",
    "SECTOR",
    "ECON_IND",
    "FIN_INST",
    "FIN_MARKET",
    "CONCEPT",
    "RAW_MATERIAL",
    "LOGISTICS",
    "ACCOUNTING_POLICY",
    "RISK_FACTOR",
    "LITIGATION",
    "SEGMENT",
    "FIN_METRIC",
    "ESG_TOPIC",
    "MACRO_CONDITION",
    "REGULATORY_REQUIREMENT",
    "COMMENTARY",
})

ENTITY_TYPE_ALIASES = {
    "FINMETRIC": "FIN_METRIC",
    "MACROCONDITION": "MACRO_CONDITION",
    "REGULATIVE_REQUIREMENT": "REGULATORY_REQUIREMENT",
    "REGULATORYREQUIREMENT": "REGULATORY_REQUIREMENT",
    "FINANCIAL INDICES AND MARKET DYNAMICS": "FIN_MARKET",
}

REFERENCE_RELATION_TYPES = frozenset({
    "HAS_STAKE_IN",
    "ANNOUNCES",
    "OPERATES_IN",
    "INTRODUCES",
    "PRODUCES",
    "REGULATES",
    "INVOLVED_IN",
    "IMPACTED_BY",
    "IMPACTS",
    "POSITIVELY_IMPACTS",
    "NEGATIVELY_IMPACTS",
    "RELATED_TO",
    "MEMBER_OF",
    "INVESTS_IN",
    "INCREASES",
    "DECREASES",
    "DEPENDS_ON",
    "CAUSES_SHORTAGE_OF",
    "AFFECTS_STOCK",
    "STOCK_DECLINE_DUE_TO",
    "STOCK_RISE_DUE_TO",
    "MARKET_REACTS_TO",
    "DISCLOSES",
    "FACES",
    "GUIDES_ON",
    "COMPLIES_WITH",
    "SUBJECT_TO",
    "SUPPLIES",
    "PARTNERS_WITH",
})

RELATION_TYPE_ALIASES = {
    "DECREASE": "DECREASES",
    "FACE": "FACES",
    "IMPACT": "IMPACTS",
    "INCREASE": "INCREASES",
    "PRODUCE": "PRODUCES",
    "SUPPLY": "SUPPLIES",
}

# COMPETES_WITH and LISTED_ON occur in the corpus and are used by SemiGraph.
# WORKS_FOR occurs in the released 555-question benchmark patterns.
BENCHMARK_EXTRA_REL_TYPES = frozenset({
    "COMPETES_WITH",
    "LISTED_ON",
    "WORKS_FOR",
})

FINREFLECTKG_PPR_REL_TYPES = tuple(sorted(
    REFERENCE_RELATION_TYPES | BENCHMARK_EXTRA_REL_TYPES
))


_COMPANY_ALIAS_GROUPS = (
    frozenset({"amd", "advanced micro device", "advanced micro devices"}),
    frozenset({"avgo", "broadcom"}),
    frozenset({"intc", "intel"}),
    frozenset({"nvda", "nvidia"}),
    frozenset({"qcom", "qualcomm"}),
    frozenset({"txn", "texas instrument", "texas instruments"}),
)

_COMPANY_SUFFIXES = frozenset({
    "co", "company", "corp", "corporation", "inc", "incorporate",
    "incorporated", "limited", "llc", "ltd", "plc",
})

_SEGMENT_SUFFIXES = frozenset({"category", "group", "segment"})

_NO_MORPHOLOGY_ALIAS_TYPES = frozenset({"COMP", "ORG", "PERSON", "PRODUCT"})


def normalize_name(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _morphology_token(token: str) -> str:
    """Conservative token stem for benchmark-to-graph label alignment."""
    value = token.lower()
    if len(value) > 4 and value.endswith("ies"):
        value = value[:-3] + "y"
    elif len(value) > 4 and value.endswith("es"):
        value = value[:-1]
    elif len(value) > 3 and value.endswith("s") and not value.endswith("ss"):
        value = value[:-1]

    if len(value) > 5 and value.endswith("ing"):
        value = value[:-3]
    elif len(value) > 5 and value.endswith("ed"):
        value = value[:-2]

    if len(value) > 4 and value.endswith("e"):
        value = value[:-1]
    if len(value) > 3 and value[-1:] == value[-2:-1]:
        value = value[:-1]
    return value


def morphology_key(value: object) -> str:
    """Normalize punctuation and low-risk English inflection differences."""
    tokens = re.findall(r"[a-z0-9]+", normalize_name(value))
    return " ".join(_morphology_token(token) for token in tokens)


def _company_alias_key(value: object) -> str | None:
    tokens = re.findall(r"[a-z0-9]+", normalize_name(value))
    while tokens and tokens[-1] in _COMPANY_SUFFIXES:
        tokens.pop()
    candidate = " ".join(tokens)
    for index, aliases in enumerate(_COMPANY_ALIAS_GROUPS):
        if candidate in aliases:
            return f"company_{index}"
    return None


def is_conservative_entity_alias(
    reference_name: object,
    candidate_name: object,
    entity_type: object,
) -> bool:
    """Return true only for deterministic, same-entity surface variants."""
    reference = normalize_name(reference_name)
    candidate = normalize_name(candidate_name)
    if not reference or not candidate or reference == candidate:
        return False
    if ("%" in reference) != ("%" in candidate):
        return False

    normalized_type = normalize_entity_type(entity_type)
    if normalized_type in {"ORG", "COMP"}:
        reference_company = _company_alias_key(reference)
        candidate_company = _company_alias_key(candidate)
        if reference_company and reference_company == candidate_company:
            return True

    if normalized_type == "SEGMENT":
        reference_tokens = re.findall(r"[a-z0-9]+", reference)
        candidate_tokens = re.findall(r"[a-z0-9]+", candidate)
        if reference_tokens and reference_tokens[-1] in _SEGMENT_SUFFIXES:
            reference_tokens.pop()
        if candidate_tokens and candidate_tokens[-1] in _SEGMENT_SUFFIXES:
            candidate_tokens.pop()
        if reference_tokens and reference_tokens == candidate_tokens:
            return True

    return (
        normalized_type not in _NO_MORPHOLOGY_ALIAS_TYPES
        and morphology_key(reference) == morphology_key(candidate)
    )


def gold_entity_aliases(
    question: dict,
    gold_chunk_ids: Iterable[str],
    entities_by_chunk: dict[str, set[tuple[str, str]]],
    all_graph_entities: set[tuple[str, str]] | None = None,
) -> dict[str, list[str]]:
    """Find conservative aliases that are present in the benchmark graph."""
    evidence_entities: set[tuple[str, str]] = set()
    for chunk_id in gold_chunk_ids:
        evidence_entities.update(entities_by_chunk.get(chunk_id, set()))

    aliases: dict[str, list[str]] = {}
    for node in question_path_nodes(question):
        reference = normalize_name(node.get("name"))
        entity_type = normalize_entity_type(node.get("type"))
        if not reference or not entity_type:
            continue
        candidate_entities = set(evidence_entities)
        if all_graph_entities:
            candidate_entities.update(all_graph_entities)
        matches = sorted({
            candidate_name
            for candidate_name, candidate_type in candidate_entities
            if (
                candidate_type == entity_type
                or (
                    entity_type in {"ORG", "COMP"}
                    and candidate_type in {"ORG", "COMP"}
                )
            )
            and is_conservative_entity_alias(
                reference,
                candidate_name,
                entity_type,
            )
        })
        if matches:
            aliases[reference] = matches
    return aliases


def normalize_entity_type(value: object) -> str | None:
    entity_type = str(value or "").strip().upper()
    entity_type = ENTITY_TYPE_ALIASES.get(entity_type, entity_type)
    return entity_type if entity_type in REFERENCE_ENTITY_TYPES else None


def normalize_relation_type(value: object) -> str | None:
    relation_type = str(value or "").strip().upper().replace(" ", "_")
    relation_type = RELATION_TYPE_ALIASES.get(relation_type, relation_type)
    allowed = REFERENCE_RELATION_TYPES | BENCHMARK_EXTRA_REL_TYPES
    return relation_type if relation_type in allowed else None


def canonical_chunk_id(source_file: object, page_id: object, chunk_id: object) -> str:
    parts = [str(value or "").strip() for value in (source_file, page_id, chunk_id)]
    if not all(parts):
        raise ValueError("source_file, page_id, and chunk_id are required")
    return "::".join(parts)


def iter_hop_evidence(question: dict) -> Iterable[tuple[str, dict]]:
    for index in range(1, int(question["hop_count"]) + 1):
        group_name = f"hop_{index}"
        yield group_name, question["path_data"][f"{group_name}_rel"]


def question_tickers(questions: Iterable[dict]) -> set[str]:
    tickers: set[str] = set()
    for question in questions:
        for _, evidence in iter_hop_evidence(question):
            source_file = str(evidence["source_file"])
            tickers.add(source_file.split("_10k_", 1)[0].upper())
    return tickers


def question_source_tickers(question: dict) -> set[str]:
    return question_tickers([question])


def strict_ticker_questions(
    questions: Iterable[dict],
    allowed_tickers: set[str],
) -> list[dict]:
    allowed = {ticker.upper() for ticker in allowed_tickers}
    return [
        question
        for question in questions
        if question_source_tickers(question) <= allowed
    ]


def question_path_nodes(question: dict) -> list[dict]:
    path_data = question["path_data"]
    if int(question["hop_count"]) == 2:
        keys = ("start_node", "intermediate_node", "end_node")
    else:
        keys = ("start_node", "node_2", "node_3", "end_node")
    return [path_data[key] for key in keys]


def convert_question(
    question: dict,
    available_chunk_ids: set[str] | None = None,
) -> dict | None:
    evidence_groups: dict[str, list[str]] = {}
    gold_chunks: list[str] = []
    for group_name, evidence in iter_hop_evidence(question):
        chunk_id = canonical_chunk_id(
            evidence["source_file"],
            evidence["page_id"],
            evidence["chunk_id"],
        )
        if available_chunk_ids is not None and chunk_id not in available_chunk_ids:
            return None
        evidence_groups[group_name] = [chunk_id]
        if chunk_id not in gold_chunks:
            gold_chunks.append(chunk_id)

    gold_entities = []
    for node in question_path_nodes(question):
        name = normalize_name(node.get("name"))
        if name and name not in gold_entities:
            gold_entities.append(name)

    hop_count = int(question["hop_count"])
    scope = str(question["document_relationship"])
    return {
        "id": f"FRKG{int(question['question_id']):03d}",
        "query": str(question["question"]),
        "type": f"{hop_count}hop_{scope}",
        "gold_tools": ["vector", "graph", "hybrid"],
        "gold_entities": gold_entities,
        "gold_chunks": gold_chunks,
        "gold_evidence_groups": evidence_groups,
        "answer_points": [str(question["answer"])],
        "benchmark_metadata": {
            "question_id": int(question["question_id"]),
            "hop_count": hop_count,
            "document_relationship": scope,
            "pattern": str(question["pattern"]),
        },
    }


def default_dataset_dir() -> Path:
    return Path.home() / ".cache" / "semigraph" / "FinReflectKG-81819df" / "data"
