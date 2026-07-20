# Financial SQL vs NumPy Vector Retrieval

## Experimental control

- Both methods use the same PostgreSQL-derived financial facts and benchmark gold rows.
- Vector baseline: normalized `BAAI/bge-base-en-v1.5` embeddings with plain NumPy cosine/dot-product top-100 retrieval.
- SQL reference: saved full-Agent Financial SQL benchmark run.
- Scope: retrieval only. Vector answer synthesis and abstention are not evaluated here.

## Overall retrieval result

| Metric | NumPy Vector | SQL reference | SQL - Vector |
|---|---:|---:|---:|
| Micro gold-row recall | 100.00% | 100.00% | +0.00 pp |
| Complete evidence rate | 100.00% | 100.00% | +0.00 pp |
| Mean precision@100 | 1.75% | N/A | N/A |
| Mean constraint precision@100 | 1.75% | N/A | N/A |
| NumPy search latency/query | 0.287 ms | N/A | N/A |

## Result by question category

| Category | N | Micro Recall@100 | Complete Evidence | Constraint Precision@100 |
|---|---:|---:|---:|---:|
| derived_metric | 12 | 100.00% | 100.00% | 1.00% |
| multi_company_comparison | 12 | 100.00% | 100.00% | 2.00% |
| multi_year_trend | 12 | 100.00% | 100.00% | 3.00% |
| single_company_lookup | 12 | 100.00% | 100.00% | 1.00% |
| unsupported_abstention | 12 | N/A | N/A | N/A |

## Interpretation boundary

This experiment isolates retrieval over structured financial facts. It may show
that deterministic SQL filtering retrieves complete constrained rows more
reliably than approximate semantic top-k search. It does **not** show that SQL
is universally better than vector retrieval for narrative or qualitative text.
Plain vector search always returns top-k candidates, so unsupported-query
abstention must be evaluated later through the full Agent or a calibrated
similarity threshold.
