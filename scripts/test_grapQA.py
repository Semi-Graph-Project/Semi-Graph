import os
import textwrap
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD
)

graph.refresh_schema()
print(f"Graph schema: {graph.schema}")
print("=" * 80)

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.7,
)

CYPHER_GENERATION_TEMPLATE = """
You are a Neo4j Cypher expert generating queries for a 10-K/10-Q filing knowledge graph.

=== ONTOLOGY OVERVIEW ===

**Common Nodes (across all items):**
- Document, Section, Chunk, Company, FiscalYear, Technology

**Item 1 (Business Overview):**
- Nodes: BusinessSegment, ProductLine, GeographicMarket
- Key Relationships: (Company)-[:HAS_SEGMENT]->(BusinessSegment)

**Item 1A (Risk Factors):**
- Nodes: RiskCategory, RiskFactor, RiskDriver, RiskEvent, Impact
- Key Relationships: (RiskEvent)-[:DRIVEN_BY]->(RiskDriver), (RiskEvent)-[:LEADS_TO]->(Impact)

**Item 5 (Market for Stock):**
- Nodes: RepurchaseAuthorization, RepurchaseActivity, DividendPayout, StockPerformance
- Key Relationships: (Company)-[:AUTHORIZED]->(RepurchaseAuthorization)

**Item 7 (MD&A - Management Discussion):**
- Nodes: FinancialMetric, PerformanceDriver
- Key Relationships: (PerformanceDriver)-[:IMPACTED {{direction, magnitude}}]->(FinancialMetric)

**Item 8 (Financial Statements):**
- Nodes: FinancialTable, LineItem, AccountingPolicy, AuditOpinion
- Key Relationships: (FinancialTable)-[:HAS_ROW]->(LineItem), (LineItem)-[:REPORTED_FOR]->(FiscalYear)

=== PROPERTY GUIDELINES ===

**All Nodes (except Item 8 specific nodes) have:**
- `id`: Primary identifier (use for matching specific entities)
- `summary`: 1-2 sentence description (use for semantic search)

**Item 8 Nodes have specialized properties:**
- FinancialTable: name, unit_scale, currency
- LineItem: name, original_label, value, row_order, is_total
- AccountingPolicy: name, standard_ref, description
- AuditOpinion: auditor_name, opinion_type, date

**FiscalYear:**
- `id`: Pure year number (e.g., "2024", "2025")

=== CRITICAL CYPHER RULES ===

1. **Relationship Escaping:** 
   If a relationship type contains special characters like '(', ')', ':', '->', '/', escape it with backticks.
   Example: [:`(:Company)-[:HAS_SEGMENT]->(:BusinessSegment)`]

2. **String Matching:**
   - Use DOUBLE QUOTES for string literals: WHERE fa.id = "stockholders' equity"
   - For fuzzy matching: WHERE toLower(n.id) CONTAINS "keyword"
   - For summary search: WHERE toLower(n.summary) CONTAINS "keyword"

3. **Fiscal Year Matching:**
   - FiscalYear.id is a string: WHERE fy.id = "2024"
   - For range: WHERE toInteger(fy.id) >= 2023 AND toInteger(fy.id) <= 2025

4. **Handling Optional Paths:**
   Use OPTIONAL MATCH for relationships that may not always exist:
   ```
   MATCH (c:Company)
   OPTIONAL MATCH (c)-[:HAS_SEGMENT]->(bs:BusinessSegment)
   ```

5. **Aggregation:**
   When counting or aggregating, always include RETURN DISTINCT or use appropriate grouping

=== EXAMPLE QUERIES ===

**Example 1: Find company business segments**
Question: "What are the business segments of Netflix?"
```cypher
MATCH (c:Company {{id: "Netflix"}})-[r]->(bs:BusinessSegment)
RETURN c.id AS Company, bs.id AS Segment, bs.summary AS Description
```

**Example 2: Find risk factors**
Question: "What are the main risk events mentioned?"
```cypher
MATCH (re:RiskEvent)-[:DRIVEN_BY]->(rd:RiskDriver)
OPTIONAL MATCH (re)-[:LEADS_TO]->(i:Impact)
RETURN re.id AS RiskEvent, re.summary AS Details, 
       collect(DISTINCT rd.id) AS Drivers, 
       collect(DISTINCT i.id) AS Impacts
LIMIT 10
```

**Example 3: Financial metrics with year**
Question: "Show revenue metrics for 2024"
```cypher
MATCH (fm:FinancialMetric)-[:REPORTED_IN]->(fy:FiscalYear {{id: "2024"}})
WHERE toLower(fm.id) CONTAINS "revenue"
RETURN fm.id AS Metric, fm.summary AS Details, fy.id AS Year
```

**Example 4: Item 8 financial tables**
Question: "What are the line items in the balance sheet for 2024?"
```cypher
MATCH (ft:FinancialTable)-[:HAS_ROW]->(li:LineItem)-[:REPORTED_FOR]->(fy:FiscalYear {{id: "2024"}})
WHERE toLower(ft.name) CONTAINS "balance"
RETURN ft.name AS Table, li.name AS LineItem, li.value AS Value, 
       ft.currency AS Currency, ft.unit_scale AS Scale
ORDER BY li.row_order
```

**Example 5: Company overview**
Question: "Show basic information about the company"
```cypher
MATCH (c:Company)
OPTIONAL MATCH (c)-[:HAS_SEGMENT]->(bs:BusinessSegment)
OPTIONAL MATCH (d:Document)-[:FILED_BY]->(c)
RETURN c.id AS Company, c.summary AS Overview,
       collect(DISTINCT bs.id) AS Segments,
       collect(DISTINCT d.id) AS Documents
LIMIT 1
```

=== YOUR TASK ===

Schema:
{schema}

Question: {question}

Generate a Cypher query that:
1. Uses only relationships and nodes from the schema above
2. Returns meaningful, readable column names
3. Limits results to reasonable numbers (LIMIT 20 unless user asks for more)
4. Handles null values gracefully with OPTIONAL MATCH where appropriate

Return ONLY the Cypher query, no explanations.
"""

CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True,
    cypher_prompt=CYPHER_PROMPT,
    return_intermediate_steps=True  # Helpful for debugging
)

# ===== ENHANCED QA LOOP WITH ERROR HANDLING =====
print("\n" + "="*80)
print("10-K/10-Q Knowledge Graph QA System")
print("="*80)
print("\nAvailable query types:")
print("  - Company info: 'What does [company] do?'")
print("  - Business segments: 'What are the business segments?'")
print("  - Risk factors: 'What are the main risks?'")
print("  - Financial metrics: 'Show revenue for 2024'")
print("  - Financial statements: 'What are the line items in the balance sheet?'")
print("  - Audit info: 'What was the audit opinion?'")
print("\nType 'q' to quit\n")

from termcolor import cprint
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
while True:
    question = input("\nEnter Question: ")
    if question.lower() == 'q':
        break
    
    if not question.strip():
        print("Please enter a valid question")
        continue
    
    print("\nProcessing...")
    try:
        result = chain.invoke({"query": question})
        
        # Display generated Cypher (for learning/debugging)
        if "intermediate_steps" in result:
            cypher_query = result["intermediate_steps"][0]["query"]
            print(f"\nGenerated Cypher:\n{cypher_query}\n")
        
        # Display answer
        answer = result.get("result", "No answer generated")
        wrap_answer = textwrap.fill(answer, width=80)
        cprint(f"\n >>>> Answer:\n{wrap_answer}", "green")
        print("\n" + "-"*80)
        messages = [
            SystemMessage(content="You are an expert system that combines the source prompt and context in this format: [Prompt + Context]. Your task is to come up with a creative answer based on the provided context."),
            HumanMessage(content=f"[Prompt:{question}]+[Context:{wrap_answer}]"),
        ]

        follow_up = llm.invoke(messages)
        cprint(f"\n >>>> Follow-up Insight:\n{follow_up.content}", "little_green")
        print("\n" + "="*80)

    except Exception as e:
        print(f"\n xx Error: {e}")
        print("\nTroubleshooting tips:")
        print("  1. Check if the nodes/relationships exist in your graph")
        print("  2. Verify entity names match what's in the database")
        print("  3. Try simplifying the question")
        print("  4. Use 'Show me...' or 'What are...' phrasing")
        print("-"*80)