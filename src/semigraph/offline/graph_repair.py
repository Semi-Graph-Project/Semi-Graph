"""Evidence-grounded post-extraction graph repair.

The extractor can emit entities that are only connected to chunks through
``MENTIONS``. PPR ignores provenance edges, so those entities are dead ends for
graph search. This module repairs only those dead-end entities by asking an LLM
to read the original chunk and emit relationships that are explicitly supported
by an evidence sentence in that chunk. If no evidence-backed relationship can be
found, the mention-only entity is pruned.
"""
from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from neo4j import Driver

from semigraph.config import Config, get_config
from semigraph.connections import get_llm, get_neo4j_driver
from semigraph.offline.specificity import INFORMATIVE_REL_TYPES
from semigraph.ontology.normalization import normalize_entity_name
from semigraph.ontology.schema import RELATIONSHIP_CATALOG


DEFAULT_REPAIR_METHOD = "llm_evidence_graph_repair_v1"
DEFAULT_REPAIR_WORKERS = 4
DEFAULT_CHUNKS_PER_LLM_CALL = 3
DEFAULT_LLM_ERROR_RETRIES = 1
DEFAULT_MAX_TEXT_CHARS = 9000
DEFAULT_MAX_CONTEXT_ENTITIES = 80

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

RELATIONSHIP_GUIDE: dict[str, str] = {
    rel.upper(): f"{meta.get('description', '').strip()} Hint: {meta.get('hint', '').strip()}".strip()
    for rel, meta in RELATIONSHIP_CATALOG.items()
    if rel.upper() in INFORMATIVE_REL_TYPES
}


@dataclass(frozen=True)
class EntityRef:
    """An entity mentioned by one chunk."""

    eid: str
    name: str
    type: str


@dataclass(frozen=True)
class RepairChunk:
    """One chunk plus the dead-end entities that need repair."""

    chunk_id: str
    ticker: str
    fiscal_year: str
    filing_type: str
    section: str
    text: str
    entities: list[EntityRef]
    candidate_eids: frozenset[str]


@dataclass
class GraphRepairStats:
    """Summary returned after repairing a filing or the current graph."""

    ticker: str
    fiscal_year: str
    filing_type: str
    method: str = DEFAULT_REPAIR_METHOD
    filer_name: str = ""
    skipped: bool = False
    reason: Optional[str] = None
    candidate_chunks: int = 0
    candidate_entities: int = 0
    llm_calls: int = 0
    llm_failed: int = 0
    relationships_proposed: int = 0
    relationships_rejected: int = 0
    relationships_created: int = 0
    pruned_entities: int = 0
    pruned_mentions: int = 0
    created_by_rel: dict[str, int] = field(default_factory=dict)
    rejected_by_reason: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


def _repair_method(cfg: Config) -> str:
    return getattr(cfg, "graph_repair_method", DEFAULT_REPAIR_METHOD)


def _resolve_filer_name(ticker: str, cfg: Config) -> str:
    aliases = {**DEFAULT_FILER_ALIASES, **getattr(cfg, "graph_repair_filer_aliases", {})}
    raw_name = aliases.get(ticker.upper(), ticker)
    return normalize_entity_name(raw_name, "ORG")


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _evidence_in_text(evidence_sentence: str, chunk_text: str) -> bool:
    evidence = _normalize_ws(evidence_sentence).lower()
    text = _normalize_ws(chunk_text).lower()
    return bool(evidence) and evidence in text


def _extract_json_object(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _relationship_compatible(rel_type: str, source_type: str, target_type: str) -> bool:
    meta = RELATIONSHIP_CATALOG.get(rel_type.lower())
    if not meta:
        return False
    expected_source = str(meta.get("source_type", "any")).upper()
    expected_target = str(meta.get("target_type", "any")).upper()
    if expected_source != "ANY" and expected_source != source_type.upper():
        return False
    if expected_target != "ANY" and expected_target != target_type.upper():
        return False
    return True


def _fetch_repair_chunks(
    driver: Driver,
    ticker: Optional[str] = None,
    fiscal_year: Optional[str] = None,
    filing_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[RepairChunk]:
    """Fetch chunks mentioning entities with zero informative degree.

    The queries intentionally avoid per-entity OPTIONAL MATCH expansion. We
    fetch chunk scope, mentions, and informative endpoints once, then compute
    dead-end entities in Python.
    """
    chunk_filter = []
    params: dict[str, object] = {"rel_types": INFORMATIVE_REL_TYPES}
    if ticker:
        chunk_filter.append("c.ticker = $ticker")
        params["ticker"] = ticker.upper()
    if fiscal_year:
        chunk_filter.append("c.fiscal_year = $fiscal_year")
        params["fiscal_year"] = str(fiscal_year)
    if filing_type:
        chunk_filter.append("c.filing_type = $filing_type")
        params["filing_type"] = filing_type

    where = "WHERE " + " AND ".join(chunk_filter) if chunk_filter else ""
    chunk_cypher = f"""
    MATCH (c:Chunk)
    {where}
    RETURN c.chunk_id AS chunk_id,
           c.ticker AS ticker,
           c.fiscal_year AS fiscal_year,
           c.filing_type AS filing_type,
           c.section AS section,
           c.text AS text
    ORDER BY c.ticker, c.fiscal_year, c.section, c.chunk_id
    """
    mention_cypher = f"""
    MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
    {where}
    RETURN c.chunk_id AS chunk_id,
           elementId(e) AS eid,
           e.name AS name,
           e.type AS type
    ORDER BY c.chunk_id, e.type, e.name
    """

    with driver.session() as session:
        chunks = [dict(row) for row in session.run(chunk_cypher, **params)]
        mentions = [dict(row) for row in session.run(mention_cypher, **params)]
        connected_eids: set[str] = set()
        rows = session.run(
            """
            MATCH (a:Entity)-[r]->(b:Entity)
            WHERE type(r) IN $rel_types
            RETURN elementId(a) AS source_eid, elementId(b) AS target_eid
            """,
            rel_types=INFORMATIVE_REL_TYPES,
        )
        for row in rows:
            connected_eids.add(str(row["source_eid"]))
            connected_eids.add(str(row["target_eid"]))

    mentions_by_chunk: dict[str, list[EntityRef]] = {}
    for row in mentions:
        if not row.get("name") or not row.get("type"):
            continue
        mentions_by_chunk.setdefault(str(row["chunk_id"]), []).append(
            EntityRef(
                eid=str(row["eid"]),
                name=str(row["name"]),
                type=str(row["type"]),
            )
        )

    repair_chunks: list[RepairChunk] = []
    for row in chunks:
        chunk_id = str(row["chunk_id"])
        entities = mentions_by_chunk.get(chunk_id, [])
        candidate_eids = frozenset(e.eid for e in entities if e.eid not in connected_eids)
        if not candidate_eids:
            continue
        ordered_entities = sorted(
            entities,
            key=lambda e: (0 if e.eid in candidate_eids else 1, e.type, e.name),
        )[:DEFAULT_MAX_CONTEXT_ENTITIES]
        if not any(e.eid in candidate_eids for e in ordered_entities):
            continue
        repair_chunks.append(
            RepairChunk(
                chunk_id=chunk_id,
                ticker=str(row.get("ticker") or ""),
                fiscal_year=str(row.get("fiscal_year") or ""),
                filing_type=str(row.get("filing_type") or ""),
                section=str(row.get("section") or ""),
                text=str(row.get("text") or ""),
                entities=ordered_entities,
                candidate_eids=candidate_eids,
            )
        )
        if limit and len(repair_chunks) >= limit:
            break

    return repair_chunks


def _relationship_guide_text() -> str:
    lines = []
    for rel_type in INFORMATIVE_REL_TYPES:
        guide = RELATIONSHIP_GUIDE.get(rel_type, "")
        lines.append(f"- {rel_type}: {guide}")
    return "\n".join(lines)


def _build_llm_batch_prompt(chunks: list[RepairChunk], filer_name: str) -> str:
    chunk_blocks = []
    for chunk in chunks:
        id_by_eid = {entity.eid: f"E{i + 1}" for i, entity in enumerate(chunk.entities)}
        entity_lines = []
        candidate_ids = []
        for entity in chunk.entities:
            display_id = id_by_eid[entity.eid]
            marker = " candidate_dead_end=true" if entity.eid in chunk.candidate_eids else ""
            if marker:
                candidate_ids.append(display_id)
            entity_lines.append(
                f"- {display_id}: name={json.dumps(entity.name)} type={entity.type}{marker}"
            )
        chunk_blocks.append(
            f"""
chunk_id: {chunk.chunk_id}
ticker: {chunk.ticker}
filer_name: {filer_name}
fiscal_year: {chunk.fiscal_year}
filing_type: {chunk.filing_type}
section: {chunk.section}
candidate_ids: {", ".join(candidate_ids)}
allowed_entities:
{chr(10).join(entity_lines)}
chunk_text:
\"\"\"
{chunk.text[:DEFAULT_MAX_TEXT_CHARS]}
\"\"\"
""".strip()
        )

    joined_blocks = "\n\n---\n\n".join(chunk_blocks)
    return f"""
You repair a financial knowledge graph for PPR multi-hop retrieval.

Task:
For each chunk, only repair candidate_dead_end entities. Create a relationship
only when that chunk text explicitly states the relationship. Every relationship
MUST include one exact evidence_sentence copied from that same chunk. If the
text merely lists entities together, do not create a relationship.

Allowed relationship types and direction:
{_relationship_guide_text()}

Return strict JSON only:
{{
  "chunk_repairs": [
    {{
      "chunk_id": "exact chunk_id",
      "relationships": [
        {{
          "source_id": "E1",
          "target_id": "E2",
          "type": "PRODUCES",
          "evidence_sentence": "Exact sentence copied from this chunk.",
          "confidence": 0.0
        }}
      ]
    }}
  ]
}}

Rules:
- Entity ids are local to each chunk. Do not use an E-id from another chunk.
- At least one endpoint of every relationship must be a candidate_dead_end id.
- The evidence_sentence must be copied exactly from the same chunk and must
  mention or directly support both endpoints.
- Prefer no relationship over a weak, inferred, generic, or co-mention-only edge.
- Do not invent entities.
- Do not output markdown.

Chunks:

{joined_blocks}
""".strip()


def _validate_llm_relationships(
    chunk: RepairChunk,
    payload: dict,
    method: str,
    run_id: str,
    created_at: str,
) -> tuple[list[dict], dict[str, int], int]:
    id_to_entity = {f"E{i + 1}": entity for i, entity in enumerate(chunk.entities)}
    rows: list[dict] = []
    rejected: dict[str, int] = {}
    proposed = 0
    seen: set[tuple[str, str, str, str]] = set()

    raw_relationships = payload.get("relationships", [])
    if not isinstance(raw_relationships, list):
        rejected["relationships_not_list"] = 1
        return rows, rejected, proposed

    for raw in raw_relationships:
        proposed += 1
        if not isinstance(raw, dict):
            rejected["relationship_not_object"] = rejected.get("relationship_not_object", 0) + 1
            continue
        source_id = str(raw.get("source_id") or "").strip()
        target_id = str(raw.get("target_id") or "").strip()
        rel_type = str(raw.get("type") or "").strip().upper()
        evidence = _normalize_ws(str(raw.get("evidence_sentence") or ""))
        source = id_to_entity.get(source_id)
        target = id_to_entity.get(target_id)
        if not source or not target:
            rejected["unknown_entity_id"] = rejected.get("unknown_entity_id", 0) + 1
            continue
        if source.eid == target.eid:
            rejected["self_loop"] = rejected.get("self_loop", 0) + 1
            continue
        if source.eid not in chunk.candidate_eids and target.eid not in chunk.candidate_eids:
            rejected["no_candidate_endpoint"] = rejected.get("no_candidate_endpoint", 0) + 1
            continue
        if rel_type not in INFORMATIVE_REL_TYPES:
            rejected["invalid_relationship_type"] = rejected.get("invalid_relationship_type", 0) + 1
            continue
        direction_corrected = False
        if not _relationship_compatible(rel_type, source.type, target.type):
            if _relationship_compatible(rel_type, target.type, source.type):
                source, target = target, source
                direction_corrected = True
            else:
                rejected["incompatible_relationship_type"] = rejected.get(
                    "incompatible_relationship_type", 0
                ) + 1
                continue
        if not _evidence_in_text(evidence, chunk.text):
            rejected["evidence_not_found_in_chunk"] = rejected.get(
                "evidence_not_found_in_chunk", 0
            ) + 1
            continue
        key = (source.eid, rel_type, target.eid, chunk.chunk_id)
        if key in seen:
            rejected["duplicate_in_llm_output"] = rejected.get("duplicate_in_llm_output", 0) + 1
            continue
        seen.add(key)

        try:
            confidence = float(raw.get("confidence", 0.70))
        except (TypeError, ValueError):
            confidence = 0.70
        confidence = max(0.0, min(confidence, 1.0))
        rows.append({
            "source": source.name,
            "source_type": source.type,
            "target": target.name,
            "target_type": target.type,
            "rel_type": rel_type,
            "source_chunk": chunk.chunk_id,
            "properties": {
                "repair_method": method,
                "repair_run_id": run_id,
                "repair_rule": "llm_evidence_chunk",
                "repair_created_at": created_at,
                "repair_ticker": chunk.ticker.upper(),
                "repair_fiscal_year": str(chunk.fiscal_year),
                "repair_filing_type": chunk.filing_type,
                "repair_section": chunk.section,
                "source": "llm_graph_repair",
                "confidence": confidence,
                "ppr_weight": confidence,
                "source_chunk": chunk.chunk_id,
                "evidence_sentence": evidence,
                "repair_direction_corrected": direction_corrected,
            },
        })

    return rows, rejected, proposed


def _repair_chunk_batch(
    chunks: list[RepairChunk],
    llm,
    filer_name: str,
    method: str,
    run_id: str,
    created_at: str,
) -> tuple[list[dict], dict[str, int], int, Optional[str]]:
    prompt = _build_llm_batch_prompt(chunks, filer_name=filer_name)
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    try:
        response = llm.invoke([
            (
                "system",
                "You output strict JSON only. You reject weak or inferred graph edges.",
            ),
            ("human", prompt),
        ])
        content = response.content if hasattr(response, "content") else str(response)
        payload = _extract_json_object(content)
        repairs = payload.get("chunk_repairs")
        if repairs is None and len(chunks) == 1 and "relationships" in payload:
            repairs = [{"chunk_id": chunks[0].chunk_id, "relationships": payload["relationships"]}]
        if not isinstance(repairs, list):
            return [], {"chunk_repairs_not_list": 1}, 0, None

        all_rows: list[dict] = []
        rejected: dict[str, int] = {}
        proposed = 0
        for repair in repairs:
            if not isinstance(repair, dict):
                rejected["chunk_repair_not_object"] = rejected.get("chunk_repair_not_object", 0) + 1
                continue
            chunk_id = str(repair.get("chunk_id") or "")
            chunk = chunks_by_id.get(chunk_id)
            if not chunk:
                rejected["unknown_chunk_id"] = rejected.get("unknown_chunk_id", 0) + 1
                continue
            rows, chunk_rejected, chunk_proposed = _validate_llm_relationships(
                chunk,
                {"relationships": repair.get("relationships", [])},
                method=method,
                run_id=run_id,
                created_at=created_at,
            )
            all_rows.extend(rows)
            proposed += chunk_proposed
            for reason, count in chunk_rejected.items():
                rejected[reason] = rejected.get(reason, 0) + count
        return all_rows, rejected, proposed, None
    except Exception as exc:  # pragma: no cover - integration safety net
        return [], {"llm_error": 1}, 0, f"{type(exc).__name__}: {exc}"


def _write_repair_rows(driver: Driver, rows: list[dict], run_id: str) -> dict[str, int]:
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


def _prune_zero_informative_entities(
    driver: Driver,
    ticker: Optional[str] = None,
    fiscal_year: Optional[str] = None,
    filing_type: Optional[str] = None,
) -> tuple[int, int]:
    """Delete entities that still have only provenance edges after repair."""
    chunk_filter = []
    params: dict[str, object] = {"rel_types": INFORMATIVE_REL_TYPES}
    if ticker:
        chunk_filter.append("c.ticker = $ticker")
        params["ticker"] = ticker.upper()
    if fiscal_year:
        chunk_filter.append("c.fiscal_year = $fiscal_year")
        params["fiscal_year"] = str(fiscal_year)
    if filing_type:
        chunk_filter.append("c.filing_type = $filing_type")
        params["filing_type"] = filing_type

    where = "WHERE " + " AND ".join(chunk_filter) if chunk_filter else ""
    with driver.session() as session:
        rows = session.run(
            f"""
            MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
            {where}
            RETURN DISTINCT elementId(e) AS eid
            """,
            **params,
        )
        scoped_eids = [str(row["eid"]) for row in rows]
        if not scoped_eids:
            return 0, 0

        result = session.run(
            """
            MATCH (e:Entity)
            WHERE elementId(e) IN $eids
              AND NOT EXISTS {
                MATCH (e)-[r]-(:Entity)
                WHERE type(r) IN $rel_types
              }
            WITH collect(e) AS entities
            UNWIND entities AS e
            OPTIONAL MATCH (c:Chunk)-[m:MENTIONS]->(e)
            WITH e, collect(m) AS mentions
            FOREACH (m IN mentions | DELETE m)
            WITH collect(e) AS entities, sum(size(mentions)) AS mention_count
            FOREACH (e IN entities | DETACH DELETE e)
            RETURN size(entities) AS entity_count, mention_count
            """,
            eids=scoped_eids,
            rel_types=INFORMATIVE_REL_TYPES,
        ).single()
        if not result:
            return 0, 0
        return int(result["entity_count"]), int(result["mention_count"] or 0)


def _run_llm_repair(
    ticker: Optional[str] = None,
    fiscal_year: Optional[str] = None,
    filing_type: Optional[str] = None,
    cfg: Optional[Config] = None,
    driver: Optional[Driver] = None,
    llm=None,
    workers: int = DEFAULT_REPAIR_WORKERS,
    chunks_per_llm_call: int = DEFAULT_CHUNKS_PER_LLM_CALL,
    llm_error_retries: int = DEFAULT_LLM_ERROR_RETRIES,
    limit: Optional[int] = None,
    prune_unresolved: bool = True,
) -> GraphRepairStats:
    cfg = cfg or get_config()
    method = _repair_method(cfg)
    stats = GraphRepairStats(
        ticker=(ticker or "ALL").upper(),
        fiscal_year=str(fiscal_year or "ALL"),
        filing_type=filing_type or "ALL",
        method=method,
    )

    if not getattr(cfg, "graph_repair_enabled", True):
        stats.skipped = True
        stats.reason = "disabled"
        return stats

    close_after = driver is None
    driver = driver or get_neo4j_driver(cfg)
    llm = llm or get_llm(cfg)
    run_id = uuid4().hex
    created_at = datetime.now(timezone.utc).isoformat()
    filer_name = _resolve_filer_name(ticker, cfg) if ticker else ""
    stats.filer_name = filer_name

    try:
        chunks = _fetch_repair_chunks(
            driver,
            ticker=ticker,
            fiscal_year=fiscal_year,
            filing_type=filing_type,
            limit=limit,
        )
        stats.candidate_chunks = len(chunks)
        stats.candidate_entities = len({
            eid for chunk in chunks for eid in chunk.candidate_eids
        })
        if not chunks:
            if prune_unresolved:
                pruned, mentions = _prune_zero_informative_entities(
                    driver,
                    ticker=ticker,
                    fiscal_year=fiscal_year,
                    filing_type=filing_type,
                )
                stats.pruned_entities = pruned
                stats.pruned_mentions = mentions
            return stats

        pending_rows: list[dict] = []
        created_by_rel: dict[str, int] = {}
        rejected: dict[str, int] = {}
        failures = 0
        proposed = 0
        completed = 0
        completed_chunks = 0
        max_workers = max(1, workers)
        batch_size = max(1, chunks_per_llm_call)
        chunk_batches = [
            chunks[i:i + batch_size]
            for i in range(0, len(chunks), batch_size)
        ]

        def _flush_pending_rows() -> None:
            nonlocal pending_rows
            if not pending_rows:
                return
            created = _write_repair_rows(driver, pending_rows, run_id=run_id)
            for rel_type, count in created.items():
                created_by_rel[rel_type] = created_by_rel.get(rel_type, 0) + count
            pending_rows = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    _repair_chunk_batch,
                    batch,
                    llm=llm,
                    filer_name=filer_name,
                    method=method,
                    run_id=run_id,
                    created_at=created_at,
                ): batch
                for batch in chunk_batches
            }
            for future in as_completed(futures):
                batch = futures[future]
                rows, chunk_rejected, chunk_proposed, error = future.result()
                retry_count = 0
                while error and retry_count < max(0, llm_error_retries):
                    retry_count += 1
                    time.sleep(min(2 * retry_count, 10))
                    rows, chunk_rejected, chunk_proposed, error = _repair_chunk_batch(
                        batch,
                        llm=llm,
                        filer_name=filer_name,
                        method=method,
                        run_id=run_id,
                        created_at=created_at,
                    )
                completed += 1
                completed_chunks += len(batch)
                pending_rows.extend(rows)
                proposed += chunk_proposed
                if error:
                    failures += 1
                for reason, count in chunk_rejected.items():
                    rejected[reason] = rejected.get(reason, 0) + count
                if len(pending_rows) >= 100:
                    _flush_pending_rows()
                if completed % 5 == 0 or completed == len(chunk_batches):
                    print(
                        "[repair] "
                        f"{completed}/{len(chunk_batches)} batches "
                        f"({completed_chunks}/{len(chunks)} chunks) | "
                        f"proposed={proposed} rejected={sum(rejected.values())} "
                        f"created={sum(created_by_rel.values())} failed={failures}",
                        flush=True,
                    )

        _flush_pending_rows()

        stats.llm_calls = len(chunk_batches)
        stats.llm_failed = failures
        stats.relationships_proposed = proposed
        stats.relationships_rejected = sum(rejected.values())
        stats.rejected_by_reason = rejected
        stats.created_by_rel = created_by_rel
        stats.relationships_created = sum(stats.created_by_rel.values())

        if prune_unresolved:
            pruned, mentions = _prune_zero_informative_entities(
                driver,
                ticker=ticker,
                fiscal_year=fiscal_year,
                filing_type=filing_type,
            )
            stats.pruned_entities = pruned
            stats.pruned_mentions = mentions

        return stats
    finally:
        if close_after:
            driver.close()


def repair_filing_graph(
    ticker: str,
    fiscal_year: str,
    filing_type: str = "10-K",
    cfg: Optional[Config] = None,
    driver: Optional[Driver] = None,
    llm=None,
    workers: int = DEFAULT_REPAIR_WORKERS,
    chunks_per_llm_call: int = DEFAULT_CHUNKS_PER_LLM_CALL,
    llm_error_retries: int = DEFAULT_LLM_ERROR_RETRIES,
    limit: Optional[int] = None,
    prune_unresolved: bool = True,
) -> GraphRepairStats:
    """Repair one filing after extraction has been stored in Neo4j."""
    return _run_llm_repair(
        ticker=ticker,
        fiscal_year=str(fiscal_year),
        filing_type=filing_type,
        cfg=cfg,
        driver=driver,
        llm=llm,
        workers=workers,
        chunks_per_llm_call=chunks_per_llm_call,
        llm_error_retries=llm_error_retries,
        limit=limit,
        prune_unresolved=prune_unresolved,
    )


def repair_current_graph(
    ticker: Optional[str] = None,
    fiscal_year: Optional[str] = None,
    filing_type: Optional[str] = None,
    cfg: Optional[Config] = None,
    driver: Optional[Driver] = None,
    llm=None,
    workers: int = DEFAULT_REPAIR_WORKERS,
    chunks_per_llm_call: int = DEFAULT_CHUNKS_PER_LLM_CALL,
    llm_error_retries: int = DEFAULT_LLM_ERROR_RETRIES,
    limit: Optional[int] = None,
    prune_unresolved: bool = True,
) -> GraphRepairStats:
    """Repair an already-extracted graph without re-running extraction."""
    return _run_llm_repair(
        ticker=ticker,
        fiscal_year=fiscal_year,
        filing_type=filing_type,
        cfg=cfg,
        driver=driver,
        llm=llm,
        workers=workers,
        chunks_per_llm_call=chunks_per_llm_call,
        llm_error_retries=llm_error_retries,
        limit=limit,
        prune_unresolved=prune_unresolved,
    )
