"""
Demonstrate the distinction between:
  (a) Ontology  — the SCHEMA (type definitions)
  (b) Knowledge Graph — the EXTRACTED INSTANCES (real data)

Run from project root: python scripts/ds.py
"""
import pandas as pd

df = pd.read_parquet("data/finreflectkg_sox.parquet")

print("=" * 70)
print("WHAT WE HAVE: Knowledge Graph (extracted instances)")
print("=" * 70)
print(f"\nTotal triples: {len(df):,}")
print(f"\nFirst 5 actual triples (real entities):\n")
for _, r in df.head(5).iterrows():
    print(f"  ({r['entity']}:{r['entity_type']}) "
          f"-[{r['relationship']}]-> "
          f"({r['target']}:{r['target_type']})")

print("\n" + "=" * 70)
print("WHAT WE INFER: Ontology (the schema behind the data)")
print("=" * 70)

# Entity types = ontology's NODE type catalogue
entity_types = sorted(df["entity_type"].unique())
print(f"\nEntity types (the ontology has {len(entity_types)} types):")
for et in entity_types[:25]:
    count = (df["entity_type"] == et).sum()
    print(f"  {et:<28} ({count:>6,} instances)")
if len(entity_types) > 25:
    print(f"  ... and {len(entity_types) - 25} more")

# Relationship types = ontology's EDGE type catalogue
rel_types = df["relationship"].value_counts()
print(f"\nRelationship types (top 20 of {len(rel_types)} total):")
for rel, count in rel_types.head(20).items():
    print(f"  {rel:<28} ({count:>6,} instances)")

print("\n" + "=" * 70)
print("CONCRETE EXAMPLE: NVIDIA's risks (graph + ontology)")
print("=" * 70)

# Real graph instances of one specific pattern
mask = (
    (df["ticker"] == "NVDA")
    & (df["year"] == 2024)
    & (df["relationship"] == "discloses")
    & (df["target_type"] == "RISK_FACTOR")
)
sub = df[mask].drop_duplicates(subset=["target"]).head(8)

print("\nThe ontology says: ORG -[discloses]-> RISK_FACTOR is allowed")
print(f"\nThe graph contains these real instances of that pattern:\n")
for _, r in sub.iterrows():
    print(f"  NVDA discloses → '{r['target']}'")
    print(f"    Source: {r['source_file']} {r['page_id']} {r['chunk_id']}")
