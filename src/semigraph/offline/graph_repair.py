"""Deterministic post-extraction repair for graph walkability.

The LLM extractor may emit valid entities without enough valid triples. Those
mention-only entities are useful for chunk evidence, but PPR ignores MENTIONS
edges, so they become unreachable in graph search. This module adds conservative
fallback domain edges after a filing has been fully written to Neo4j.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_neo4j_driver
from semigraph.offline.specificity import INFORMATIVE_REL_TYPES
from semigraph.ontology.normalization import normalize_entity_name


DEFAULT_REPAIR_METHOD = "deterministic_graph_repair_v1"

FILER_ANCHOR_REL_BY_ENTITY_TYPE: dict[str, str] = {
    "PRODUCT": "PRODUCES",
    "SEGMENT": "HAS_STAKE_IN",
    "GPE": "OPERATES_IN",
    "RISK_FACTOR": "FACES",
    "FIN_METRIC": "DISCLOSES",
    "REGULATORY_REQUIREMENT": "SUBJECT_TO",
    "RAW_MATERIAL": "DEPENDS_ON",
    "MACRO_CONDITION": "IMPACTED_BY",
    "EVENT": "IMPACTED_BY",
    "ACCOUNTING_POLICY": "DISCLOSES",
    "ESG_TOPIC": "DISCLOSES",
    "COMP": "DISCLOSES",
    "ORG": "DISCLOSES",
    "FIN_MARKET": "LISTED_ON",
}

ITEM_1A_RISK_BRIDGE_TARGET_TYPES: frozenset[str] = frozenset({
    "PRODUCT",
    "SEGMENT",
    "FIN_METRIC",
    "RAW_MATERIAL",
})

REPAIR_CONFIDENCE_BY_REL: dict[str, float] = {
    "PRODUCES": 0.50,
    "HAS_STAKE_IN": 0.45,
    "OPERATES_IN": 0.45,
    "FACES": 0.55,
    "SUBJECT_TO": 0.45,
    "DEPENDS_ON": 0.40,
    "IMPACTED_BY": 0.30,
    "DISCLOSES": 0.20,
    "LISTED_ON": 0.45,
    "NEGATIVELY_IMPACTS": 0.45,
}

DEFAULT_FILER_ALIASES: dict[str, str] = {
    "AMAT": "applied materials",
    "AMD": "amd",
    "AMKR": "amkor",
    "AVGO": "broadcom",
    "COHR": "coherent",
    "ENTG": "entegris",
    "INTC": "intel",
    "KLAC": "kla",
    "LRCX": "lam research",
    "MU": "micron",
    "NVDA": "nvidia",
    "QCOM": "qualcomm",
    "RMBS": "rambus",
    "TXN": "texas instruments",
}


@dataclass
class GraphRepairStats:
    """Summary returned after repairing one filing."""

    ticker: str
    fiscal_year: str
    filing_type: str
    method: str = DEFAULT_REPAIR_METHOD
    filer_name: str = ""
    skipped: bool = False
    reason: Optional[str] = None
    filer_anchor_candidates: int = 0
    filer_anchor_created: int = 0
    item_1a_risk_bridge_candidates: int = 0
    item_1a_risk_bridge_created: int = 0
    created_by_rel: dict[str, int] = field(default_factory=dict)

    @property
    def total_created(self) -> int:
        return self.filer_anchor_created + self.item_1a_risk_bridge_created

    def as_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "fiscal_year": self.fiscal_year,
            "filing_type": self.filing_type,
            "method": self.method,
            "filer_name": self.filer_name,
            "skipped": self.skipped,
            "reason": self.reason,
            "filer_anchor_candidates": self.filer_anchor_candidates,
            "filer_anchor_created": self.filer_anchor_created,
            "item_1a_risk_bridge_candidates": self.item_1a_risk_bridge_candidates,
            "item_1a_risk_bridge_created": self.item_1a_risk_bridge_created,
            "total_created": self.total_created,
            "created_by_rel": dict(self.created_by_rel),
        }


def _repair_method(cfg: Config) -> str:
    return getattr(cfg, "graph_repair_method", DEFAULT_REPAIR_METHOD)


def _resolve_filer_name(ticker: str, cfg: Config) -> str:
    aliases = {**DEFAULT_FILER_ALIASES, **getattr(cfg, "graph_repair_filer_aliases", {})}
    raw_name = aliases.get(ticker.upper(), ticker)
    return normalize_entity_name(raw_name, "ORG")


def _ensure_filer_entity(driver: Driver, filer_name: str, ticker: str) -> None:
    with driver.session() as session:
        session.run(
            """
            MERGE (f:Entity {name: $name, type: 'ORG'})
            ON CREATE SET
                f.created_by = 'graph_repair',
                f.created_at = timestamp()
            SET
                f.name = $name,
                f.type = 'ORG',
                f.ticker = coalesce(f.ticker, $ticker)
            """,
            name=filer_name,
            ticker=ticker.upper(),
        )


def _fetch_filer_anchor_candidates(
    driver: Driver,
    ticker: str,
    fiscal_year: str,
    filing_type: str,
) -> list[dict]:
    cypher = """
    MATCH (c:Chunk {
        ticker: $ticker,
        fiscal_year: $fiscal_year,
        filing_type: $filing_type
    })
    OPTIONAL MATCH ()-[chunk_rel]->()
    WHERE chunk_rel.source_chunk = c.chunk_id
      AND type(chunk_rel) IN $rel_types
    WITH c, count(chunk_rel) AS chunk_rel_count
    MATCH (c)-[:MENTIONS]->(e:Entity)
    WHERE e.type IN $target_types
      AND e.name IS NOT NULL
    WITH c, e, chunk_rel_count
    OPTIONAL MATCH (e)-[entity_rel]-(other:Entity)
    WHERE type(entity_rel) IN $rel_types
    WITH c, e, chunk_rel_count, count(entity_rel) AS entity_degree
    WHERE chunk_rel_count = 0 OR entity_degree = 0
    RETURN DISTINCT
        c.chunk_id AS source_chunk,
        c.section AS section,
        e.name AS target,
        e.type AS target_type,
        chunk_rel_count AS chunk_rel_count,
        entity_degree AS entity_degree
    """
    with driver.session() as session:
        rows = session.run(
            cypher,
            ticker=ticker.upper(),
            fiscal_year=str(fiscal_year),
            filing_type=filing_type,
            rel_types=INFORMATIVE_REL_TYPES,
            target_types=sorted(FILER_ANCHOR_REL_BY_ENTITY_TYPE),
        )
        return [dict(row) for row in rows]


def _fetch_item_1a_risk_bridge_candidates(
    driver: Driver,
    ticker: str,
    fiscal_year: str,
    filing_type: str,
) -> list[dict]:
    cypher = """
    MATCH (c:Chunk {
        ticker: $ticker,
        fiscal_year: $fiscal_year,
        filing_type: $filing_type
    })
    WHERE c.section IN ['Item_1A', 'Item 1A']
    OPTIONAL MATCH ()-[chunk_rel]->()
    WHERE chunk_rel.source_chunk = c.chunk_id
      AND type(chunk_rel) IN $rel_types
    WITH c, count(chunk_rel) AS chunk_rel_count
    MATCH (c)-[:MENTIONS]->(risk:Entity {type: 'RISK_FACTOR'})
    MATCH (c)-[:MENTIONS]->(target:Entity)
    WHERE target.type IN $target_types
      AND target.name IS NOT NULL
      AND risk.name IS NOT NULL
      AND NOT (risk.name = target.name AND risk.type = target.type)
    WITH c, risk, target, chunk_rel_count
    OPTIONAL MATCH (risk)-[risk_rel]-(risk_other:Entity)
    WHERE type(risk_rel) IN $rel_types
    WITH c, risk, target, chunk_rel_count, count(risk_rel) AS risk_degree
    OPTIONAL MATCH (target)-[target_rel]-(target_other:Entity)
    WHERE type(target_rel) IN $rel_types
    WITH c, risk, target, chunk_rel_count, risk_degree, count(target_rel) AS target_degree
    WHERE chunk_rel_count = 0 OR risk_degree = 0 OR target_degree = 0
    RETURN DISTINCT
        c.chunk_id AS source_chunk,
        c.section AS section,
        risk.name AS source,
        risk.type AS source_type,
        target.name AS target,
        target.type AS target_type,
        chunk_rel_count AS chunk_rel_count,
        risk_degree AS risk_degree,
        target_degree AS target_degree
    """
    with driver.session() as session:
        rows = session.run(
            cypher,
            ticker=ticker.upper(),
            fiscal_year=str(fiscal_year),
            filing_type=filing_type,
            rel_types=INFORMATIVE_REL_TYPES,
            target_types=sorted(ITEM_1A_RISK_BRIDGE_TARGET_TYPES),
        )
        return [dict(row) for row in rows]


def _base_properties(
    *,
    method: str,
    run_id: str,
    rule: str,
    rel_type: str,
    ticker: str,
    fiscal_year: str,
    filing_type: str,
    section: str,
    source_chunk: str,
    created_at: str,
) -> dict:
    confidence = REPAIR_CONFIDENCE_BY_REL.get(rel_type, 0.25)
    return {
        "repair_method": method,
        "repair_run_id": run_id,
        "repair_rule": rule,
        "repair_created_at": created_at,
        "repair_ticker": ticker.upper(),
        "repair_fiscal_year": str(fiscal_year),
        "repair_filing_type": filing_type,
        "repair_section": section,
        "source": "deterministic_graph_repair",
        "confidence": confidence,
        "ppr_weight": confidence,
        "source_chunk": source_chunk,
    }


def _build_filer_anchor_rows(
    candidates: list[dict],
    *,
    filer_name: str,
    ticker: str,
    fiscal_year: str,
    filing_type: str,
    method: str,
    run_id: str,
    created_at: str,
) -> list[dict]:
    rows: list[dict] = []
    seen: set[tuple[str, str, str, str, str, str]] = set()
    for candidate in candidates:
        target = candidate.get("target")
        target_type = candidate.get("target_type")
        source_chunk = candidate.get("source_chunk")
        rel_type = FILER_ANCHOR_REL_BY_ENTITY_TYPE.get(str(target_type))
        if not rel_type or not target or not source_chunk:
            continue
        if target == filer_name and target_type == "ORG":
            continue

        key = (filer_name, "ORG", str(target), str(target_type), rel_type, str(source_chunk))
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "source": filer_name,
            "source_type": "ORG",
            "target": str(target),
            "target_type": str(target_type),
            "rel_type": rel_type,
            "source_chunk": str(source_chunk),
            "properties": _base_properties(
                method=method,
                run_id=run_id,
                rule="filer_anchor",
                rel_type=rel_type,
                ticker=ticker,
                fiscal_year=fiscal_year,
                filing_type=filing_type,
                section=str(candidate.get("section") or ""),
                source_chunk=str(source_chunk),
                created_at=created_at,
            ),
        })
    return rows


def _build_item_1a_risk_bridge_rows(
    candidates: list[dict],
    *,
    ticker: str,
    fiscal_year: str,
    filing_type: str,
    method: str,
    run_id: str,
    created_at: str,
) -> list[dict]:
    rel_type = "NEGATIVELY_IMPACTS"
    rows: list[dict] = []
    seen: set[tuple[str, str, str, str, str, str]] = set()
    for candidate in candidates:
        source = candidate.get("source")
        source_type = candidate.get("source_type")
        target = candidate.get("target")
        target_type = candidate.get("target_type")
        source_chunk = candidate.get("source_chunk")
        if (
            not source
            or source_type != "RISK_FACTOR"
            or not target
            or target_type not in ITEM_1A_RISK_BRIDGE_TARGET_TYPES
            or not source_chunk
        ):
            continue

        key = (str(source), str(source_type), str(target), str(target_type), rel_type, str(source_chunk))
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "source": str(source),
            "source_type": str(source_type),
            "target": str(target),
            "target_type": str(target_type),
            "rel_type": rel_type,
            "source_chunk": str(source_chunk),
            "properties": _base_properties(
                method=method,
                run_id=run_id,
                rule="item_1a_risk_bridge",
                rel_type=rel_type,
                ticker=ticker,
                fiscal_year=fiscal_year,
                filing_type=filing_type,
                section=str(candidate.get("section") or ""),
                source_chunk=str(source_chunk),
                created_at=created_at,
            ),
        })
    return rows


def _write_repair_rows(driver: Driver, rows: list[dict], *, run_id: str) -> dict[str, int]:
    created_by_rel: dict[str, int] = {}
    rows_by_rel: dict[str, list[dict]] = {}
    for row in rows:
        rows_by_rel.setdefault(row["rel_type"], []).append(row)

    for rel_type, rel_rows in rows_by_rel.items():
        if rel_type not in INFORMATIVE_REL_TYPES:
            continue
        cypher = f"""
        UNWIND $rows AS row
        MATCH (source:Entity {{name: row.source, type: row.source_type}})
        MATCH (target:Entity {{name: row.target, type: row.target_type}})
        WHERE NOT (source.name = target.name AND source.type = target.type)
        MERGE (source)-[r:{rel_type} {{source_chunk: row.source_chunk}}]->(target)
        ON CREATE SET r += row.properties
        WITH r
        WHERE r.repair_run_id = $run_id
        RETURN count(r) AS created
        """
        with driver.session() as session:
            result = session.run(cypher, rows=rel_rows, run_id=run_id).single()
        created = int(result["created"] if result else 0)
        if created:
            created_by_rel[rel_type] = created
    return created_by_rel


def repair_filing_graph(
    ticker: str,
    fiscal_year: str,
    filing_type: str = "10-K",
    *,
    cfg: Optional[Config] = None,
    driver: Optional[Driver] = None,
) -> GraphRepairStats:
    """Repair one filing after extraction has been stored in Neo4j."""
    cfg = cfg or get_config()
    method = _repair_method(cfg)
    stats = GraphRepairStats(
        ticker=ticker.upper(),
        fiscal_year=str(fiscal_year),
        filing_type=filing_type,
        method=method,
    )

    if not getattr(cfg, "graph_repair_enabled", True):
        stats.skipped = True
        stats.reason = "disabled"
        return stats

    close_after = driver is None
    driver = driver or get_neo4j_driver(cfg)
    run_id = uuid4().hex
    created_at = datetime.now(timezone.utc).isoformat()
    filer_name = _resolve_filer_name(ticker, cfg)
    stats.filer_name = filer_name

    try:
        _ensure_filer_entity(driver, filer_name, ticker)
        anchor_candidates = _fetch_filer_anchor_candidates(
            driver, ticker, fiscal_year, filing_type
        )
        risk_candidates = _fetch_item_1a_risk_bridge_candidates(
            driver, ticker, fiscal_year, filing_type
        )

        anchor_rows = _build_filer_anchor_rows(
            anchor_candidates,
            filer_name=filer_name,
            ticker=ticker,
            fiscal_year=str(fiscal_year),
            filing_type=filing_type,
            method=method,
            run_id=run_id,
            created_at=created_at,
        )
        risk_rows = _build_item_1a_risk_bridge_rows(
            risk_candidates,
            ticker=ticker,
            fiscal_year=str(fiscal_year),
            filing_type=filing_type,
            method=method,
            run_id=run_id,
            created_at=created_at,
        )

        stats.filer_anchor_candidates = len(anchor_rows)
        stats.item_1a_risk_bridge_candidates = len(risk_rows)

        _write_repair_rows(driver, anchor_rows + risk_rows, run_id=run_id)

        # Count from the run marker so existing MERGEd edges are not reported
        # as newly created during idempotent re-runs.
        with driver.session() as session:
            rows = session.run(
                """
                MATCH ()-[r]->()
                WHERE r.repair_run_id = $run_id
                RETURN r.repair_rule AS rule, type(r) AS rel_type, count(r) AS n
                """,
                run_id=run_id,
            )
            exact_by_rule: dict[str, int] = {}
            exact_by_rel: dict[str, int] = {}
            for row in rows:
                exact_by_rule[row["rule"]] = exact_by_rule.get(row["rule"], 0) + int(row["n"])
                exact_by_rel[row["rel_type"]] = exact_by_rel.get(row["rel_type"], 0) + int(row["n"])

        stats.filer_anchor_created = exact_by_rule.get("filer_anchor", 0)
        stats.item_1a_risk_bridge_created = exact_by_rule.get("item_1a_risk_bridge", 0)
        stats.created_by_rel = exact_by_rel
        return stats
    finally:
        if close_after:
            driver.close()
