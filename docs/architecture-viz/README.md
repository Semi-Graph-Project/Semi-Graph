# SemiGraph Interactive Architecture

Interactive, source-grounded map of the current `src/semigraph` working tree.

## Open

The page has no external runtime dependencies. Open `index.html` directly, or
serve the directory locally:

```bash
python -m http.server 8765 --directory docs/architecture-viz
```

Then visit <http://127.0.0.1:8765>.

## Views

- **Agent runtime** — scenario `Parallel Tasks · State walkthrough` เดิน
  `PlanRoute → Send fan-out → isolated Task workers → task_results reducer →
  Collector → one Synthesis` พร้อม State inspector ที่แยกสีทุก field และสมาชิก
  แต่ละตัวใน list.
- **Graph search** — BGE query embedding, triple candidates, LLM recognition
  filter, entity seeds, reusable GDS projection, Personalized PageRank, and
  final evidence trace.
- **Data factory** — the SEC narrative path into Neo4j and the Finnhub numeric
  path into PostgreSQL.
- **Source map** — searchable ownership cards for all 59 Python modules under
  `src/semigraph`.
- **Interface literacy** — อ่าน boundary ของ `AgentState`, `PlanRouteOutput`,
  `RetrievalAction`, `AttemptRecord`, `AssessmentOutput`, `TaskResult` และ
  Synthesis output แบบเดินทีละขั้น พร้อม Contract Model และลำดับ debug.

The visualization intentionally describes the current source rather than older
planning documents. In particular, the active Agent uses isolated parallel
Task workers with deterministic collection before one Synthesis call,
KG extraction is one LLM call per chunk, and the default Financial runtime
backend is typed PostgreSQL retrieval.

## Maintenance

When architecture changes, update the data declarations near the top of
`app.js`: `runtimeNodes`, `interfaceNodes`, `graphNodes`, `factoryNodes`, their
edge/scenario collections, and `MODULE_GROUPS`. Keep file ownership,
Contract Model field names, and configuration values grounded in the current
source and `config/default.yaml`.
