"""
Neo4j Graph Schema Diagnostic Tool
===================================
ใช้ script นี้เพื่อตรวจสอบว่า graph มีข้อมูลอะไรบ้าง
และ relationship types เป็นแบบไหนจริงๆ
"""

import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD
)

print("=" * 80)
print("NEO4J GRAPH DIAGNOSTICS")
print("=" * 80)

# 1. Check all node labels
print("\n📊 1. NODE TYPES AND COUNTS")
print("-" * 80)
query_nodes = """
MATCH (n)
RETURN labels(n)[0] AS NodeType, count(*) AS Count
ORDER BY Count DESC
"""
results = graph.query(query_nodes)
for row in results:
    print(f"  • {row['NodeType']:30s} : {row['Count']:>6,} nodes")

# 2. Check all relationship types
print("\n🔗 2. RELATIONSHIP TYPES")
print("-" * 80)
query_rels = """
MATCH ()-[r]->()
RETURN DISTINCT type(r) AS RelType, count(*) AS Count
ORDER BY Count DESC
"""
results = graph.query(query_rels)
for row in results:
    rel_type = row['RelType']
    count = row['Count']
    # ตรวจสอบว่ามี special characters หรือไม่
    needs_escape = any(char in rel_type for char in ['(', ')', ':', '-', '/', ' '])
    escape_indicator = " ⚠️  NEEDS BACKTICKS" if needs_escape else ""
    print(f"  • {rel_type:50s} : {count:>6,} edges{escape_indicator}")

# 3. Sample relationship patterns
print("\n🌐 3. RELATIONSHIP PATTERNS (Top 20)")
print("-" * 80)
query_patterns = """
MATCH (a)-[r]->(b)
RETURN DISTINCT 
  labels(a)[0] AS FromNode,
  type(r) AS Relationship,
  labels(b)[0] AS ToNode,
  count(*) AS Count
ORDER BY Count DESC
LIMIT 20
"""
results = graph.query(query_patterns)
print(f"{'From Node':20s} -> {'Relationship':40s} -> {'To Node':20s} | Count")
print("-" * 80)
for row in results:
    from_node = row['FromNode'] or 'Unknown'
    rel = row['Relationship']
    to_node = row['ToNode'] or 'Unknown'
    count = row['Count']
    print(f"{from_node:20s} -> {rel:40s} -> {to_node:20s} | {count:>5,}")

# 4. Sample Company nodes
print("\n🏢 4. SAMPLE COMPANY NODES")
print("-" * 80)
query_companies = """
MATCH (c:Company)
RETURN c.id AS CompanyID, 
       c.summary AS Summary
LIMIT 5
"""
try:
    results = graph.query(query_companies)
    if results:
        for i, row in enumerate(results, 1):
            company_id = row.get('CompanyID', 'N/A')
            summary = row.get('Summary', 'No summary')
            print(f"\n  Company {i}: {company_id}")
            print(f"  Summary: {summary[:100]}..." if len(summary) > 100 else f"  Summary: {summary}")
    else:
        print("  ⚠️  No Company nodes found!")
except Exception as e:
    print(f"  ⚠️  Error querying Company nodes: {e}")

# 5. Check FiscalYear format
print("\n📅 5. FISCAL YEAR FORMAT")
print("-" * 80)
query_fiscal = """
MATCH (fy:FiscalYear)
RETURN DISTINCT fy.id AS FiscalYear
ORDER BY fy.id
LIMIT 10
"""
try:
    results = graph.query(query_fiscal)
    if results:
        years = [row['FiscalYear'] for row in results]
        print(f"  Found years: {years}")
        print(f"  Data type: {type(years[0]).__name__}")
        
        # Check if it's string or int
        if isinstance(years[0], str):
            print("  ✅ FiscalYear.id is STRING (use quotes in queries)")
        else:
            print("  ⚠️  FiscalYear.id is INTEGER (don't use quotes)")
    else:
        print("  ⚠️  No FiscalYear nodes found!")
except Exception as e:
    print(f"  ⚠️  Error querying FiscalYear: {e}")

# 6. Check if nodes have 'summary' property
print("\n📝 6. NODES WITH 'summary' PROPERTY")
print("-" * 80)
query_summary = """
MATCH (n)
WHERE n.summary IS NOT NULL
RETURN labels(n)[0] AS NodeType, count(*) AS CountWithSummary
ORDER BY CountWithSummary DESC
LIMIT 10
"""
results = graph.query(query_summary)
for row in results:
    node_type = row['NodeType']
    count = row['CountWithSummary']
    print(f"  • {node_type:30s} : {count:>6,} nodes have summary")

# 7. Sample Item 8 nodes (if exist)
print("\n💰 7. ITEM 8 FINANCIAL NODES")
print("-" * 80)

# Check FinancialTable
query_tables = """
MATCH (ft:FinancialTable)
RETURN ft.name AS TableName, 
       ft.unit_scale AS Scale,
       ft.currency AS Currency
LIMIT 3
"""
try:
    results = graph.query(query_tables)
    if results:
        print("  ✅ FinancialTable nodes found:")
        for row in results:
            print(f"    - {row.get('TableName', 'N/A')} ({row.get('Scale', 'N/A')} {row.get('Currency', 'N/A')})")
    else:
        print("  ⚠️  No FinancialTable nodes found")
except Exception as e:
    print(f"  ⚠️  Error: {e}")

# Check LineItem
query_lineitems = """
MATCH (li:LineItem)
RETURN li.name AS ItemName, 
       li.value AS Value,
       li.is_total AS IsTotal
LIMIT 5
"""
try:
    results = graph.query(query_lineitems)
    if results:
        print("\n  ✅ LineItem nodes found:")
        for row in results:
            name = row.get('ItemName', 'N/A')
            value = row.get('Value', 'N/A')
            is_total = row.get('IsTotal', False)
            total_marker = " [TOTAL]" if is_total else ""
            print(f"    - {name}: {value}{total_marker}")
    else:
        print("  ⚠️  No LineItem nodes found")
except Exception as e:
    print(f"  ⚠️  Error: {e}")

# 8. Check for common issues
print("\n⚠️  8. POTENTIAL ISSUES")
print("-" * 80)

issues_found = False

# Issue 1: Orphaned nodes
query_orphans = """
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n)[0] AS NodeType, count(*) AS OrphanCount
ORDER BY OrphanCount DESC
LIMIT 5
"""
results = graph.query(query_orphans)
orphans = [row for row in results if row['OrphanCount'] > 0]
if orphans:
    issues_found = True
    print("  ⚠️  Orphaned nodes (not connected to anything):")
    for row in orphans:
        print(f"    - {row['NodeType']}: {row['OrphanCount']} nodes")

# Issue 2: Missing Company nodes
query_company_count = "MATCH (c:Company) RETURN count(c) AS Count"
company_count = graph.query(query_company_count)[0]['Count']
if company_count == 0:
    issues_found = True
    print("  ⚠️  No Company nodes found! Most queries will fail.")

if not issues_found:
    print("  ✅ No obvious issues detected!")

# 9. Recommendations
print("\n💡 9. RECOMMENDATIONS FOR QA SYSTEM")
print("-" * 80)

# Count relationships with special characters
query_special = """
MATCH ()-[r]->()
WHERE type(r) CONTAINS '(' OR type(r) CONTAINS ')' OR type(r) CONTAINS ':' 
   OR type(r) CONTAINS '/' OR type(r) CONTAINS '-'
RETURN count(DISTINCT type(r)) AS SpecialRelCount
"""
special_count = graph.query(query_special)[0]['SpecialRelCount']

if special_count > 0:
    print(f"  ⚠️  Found {special_count} relationship types with special characters")
    print("  💡 Recommendation: Update your prompt to ALWAYS use backticks for relationships:")
    print("     Example: [:`(:Company)-[:HAS_SEGMENT]->(:BusinessSegment)`]")
    print()
    print("  Or consider simplifying relationship names during extraction:")
    print("     Instead of: (:Company)-[:HAS_SEGMENT]->(:BusinessSegment)")
    print("     Use: HAS_SEGMENT")
else:
    print("  ✅ No special characters in relationship names - good!")

# Check summary coverage
query_summary_coverage = """
MATCH (n)
WHERE n.summary IS NOT NULL
WITH count(n) AS WithSummary
MATCH (n2)
WITH WithSummary, count(n2) AS Total
RETURN WithSummary, Total, 
       round(100.0 * WithSummary / Total, 1) AS CoveragePercent
"""
results = graph.query(query_summary_coverage)
if results:
    coverage = results[0]['CoveragePercent']
    print(f"\n  📊 {coverage}% of nodes have 'summary' property")
    if coverage < 50:
        print("  ⚠️  Low coverage! Consider adding summaries during extraction.")
    else:
        print("  ✅ Good coverage for semantic search!")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\n💡 Next steps:")
print("  1. Review the relationship types - do they match your Ontology?")
print("  2. Check if special characters in relationships need escaping")
print("  3. Verify FiscalYear format (string vs integer)")
print("  4. Confirm Company nodes exist and have correct IDs")
print("  5. Update the QA prompt based on findings above")
print("\n")