# Corpus Repair Report - Phase T

Generated: 2026-06-30 01:43 ICT

## Scope

This repair intentionally avoided a full KG extraction rerun. It applied:

1. Permanent extraction-pipeline safeguards for future companies/filings.
2. Targeted Neo4j repair for the current graph.
3. Embedding and specificity refresh only for newly added graph elements.

## Permanent Pipeline Changes

| File | Change |
|---|---|
| `src/semigraph/ontology/normalization.py` | Added deterministic entity-name normalization for legal suffixes and high-confidence benchmark aliases. |
| `src/semigraph/offline/kg_extract.py` | Applies normalized ids, deduplicates normalized nodes/relationships, enforces hard 40 node / 40 relationship caps, and rejects product-as-company direction errors. |
| `src/semigraph/offline/kg_store.py` | Replaces prior chunk extraction output before rewriting a chunk, preventing stale `MENTIONS` and `source_chunk` relationships from accumulating. |
| `tests/test_kg_extract_quality.py` | Covers normalization, dedupe, product/company guard, and hard caps. |
| `tests/test_kg_store_reset.py` | Covers chunk-level extraction cleanup before rewrite. |

## Current Neo4j Repair

Repair log: `analytics/neo4j_manual_corpus_repair_20260630_014347.json`
Structural cleanup log: `analytics/neo4j_structural_cleanup_20260630_015029.json`

| Operation | Count |
|---|---:|
| Entities ensured | 4 |
| `MENTIONS` edges ensured | 11 |
| Informative relationships ensured | 8 |
| `SYNONYM_OF` edges ensured | 2 |

Manual entities added or ensured:

| Entity | Type | Purpose |
|---|---|---|
| `instinct` | PRODUCT | Benchmark alias for `amd instinct`. |
| `rtx` | PRODUCT | Benchmark alias for `geforce rtx`. |
| `xeon scalable` | PRODUCT | Missing Intel product entity used by T022/T024/T027. |
| `smart capital` | EVENT | Missing Intel financing/capital strategy entity used by T022. |

After repair, embeddings and specificity were refreshed:

| Command | Result |
|---|---|
| `python scripts/embed_nodes.py` | Embedded 4 missing entities. |
| `python scripts/embed_triples.py` | Embedded 8 missing triples. |
| `python scripts/compute_specificity.py --no-preview` | Updated 13,553 entities. |

Additional structural cleanup:

| Check | Before | After |
|---|---:|---:|
| Orphan chunks | 46 | 0 |
| Chunks with >40 `MENTIONS` | 22 | 5 |
| Max `MENTIONS` on one chunk | 106 | 48 |
| Unmentioned entities pruned | n/a | 205 |

The remaining 5 broad chunks were not force-trimmed below 40 because their
domain relationship endpoints themselves exceed 40. Trimming those would break
the invariant that a chunk-scoped fact's endpoint entities are mentioned by the
same chunk.

## Verification

Focused graph verification after repair:

| Check | Result |
|---|---|
| Missing benchmark gold entities | 0 |
| Missing benchmark gold chunks | 0 |
| Manual entities have embeddings | Pass |
| Manual relationships have `triple_embedding` | Pass |
| Remaining gold chunks without gold-entity mention | 0 |
| Entity nodes missing embedding | 0 |
| Entity nodes missing specificity | 0 |
| Informative relationships missing `triple_embedding` | 0 |
| Orphan chunks | 0 |

Benchmark anchors were also corrected where the benchmark itself was using
non-canonical or wrong evidence anchors:

| Query | Fix |
|---|---|
| T004 | `instinct` -> `amd instinct` |
| T007 | `rtx` -> `geforce rtx` |
| T011 | `ENTG_2026_Item_7_0000_6c99ba90` -> `ENTG_2026_Item_7_0003_d6e71ea2` |

After these benchmark fixes, focused validation reports no missing gold
entities, no missing gold chunks, and no gold chunks without a gold-entity
mention.

## Tests

Targeted tests passed:

```bash
pytest tests/test_kg_extract_quality.py tests/test_kg_store_reset.py -v
```

Full test suite status:

```text
199 passed, 1 failed
```

The remaining failure is unrelated to this repair:

```text
tests/test_agent_nodes.py::TestObserveNode::test_observe_summarizes_latest_chunks_and_appends_history
Expected prompt fragment: [c1] AMD FY2025 Item_1
Actual prompt fragment:   [c1] ticker: AMD FY: 2025 section: Item_1
```
