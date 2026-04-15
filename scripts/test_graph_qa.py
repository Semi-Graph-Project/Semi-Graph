import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
PDF_FILE = "data/processed/10Q-NFLX.pdf"

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD
)

graph.refresh_schema()
print(f"Graph schema: {graph.schema}")
print("------ ------- --------")

# llm = ChatGoogleGenerativeAI(
#     model="gemini-3-flash-preview",
#     temperature=0,
# )

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.2,
)

# CYPHER_GENERATION_TEMPLATE = """
# Task: Generate Cypher statement to query a graph database.
# Instructions:
# 1. Use only the provided relationship types and properties.
# 2. **IMPORTANT:** Do NOT check for the 'Company' node. Search for 'FinancialAccount' directly. (Reason: Some accounts might not be explicitly linked to the Company node due to extraction limits).
# 3. **CRITICAL:** Use DOUBLE QUOTES (`"`) for all string literals to handle apostrophes correctly.
#    - Wrong: 'stockholders' equity'
#    - Right: "stockholders' equity"

# Schema:
# (:FinancialAccount)-[:HAS_VALUE]->(:MonetaryValue)
# (:MonetaryValue)-[:DURING_PERIOD]->(:TimePeriod)

# Property Mapping:
# - FinancialAccount: Name in `.id`. Use `toLower(...) CONTAINS "..."`.
# - TimePeriod: Date in `.id`.
# - MonetaryValue: Value in `.id`.

# Example Cypher:
#    MATCH (fa:FinancialAccount)-[:HAS_VALUE]->(mv:MonetaryValue)
#    WHERE toLower(fa.id) CONTAINS "amortization"
   
#    OPTIONAL MATCH (mv)-[:DURING_PERIOD]->(tp:TimePeriod)
   
#    WITH fa, mv, tp
#    WHERE tp IS NULL OR toLower(tp.id) CONTAINS "2025"
   
#    RETURN fa.id, mv.id, tp.id

# The question is:
# {question}
# """

CYPHER_GENERATION_TEMPLATE = """
Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

IMPORTANT: Some relationship types look like Cypher syntax (e.g., contains arrow '->' or parentheses '()' , and have / such as Technology/Model).
You MUST escape these relationship types with backticks (`).

Example:
Input: List the business segment of Google
Schema: (:Company)-[:`(COMPANY)-[:HAS_SEGMENT]->(SEGMENT)`]->(:Segment)
Correct Cypher: MATCH (c:Company {{name: "Google"}})-[:`(COMPANY)-[:HAS_SEGMENT]->(SEGMENT)`]->(s:Segment) RETURN s

Schema:
{schema}

Question: {question}
"""

CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema","question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True,
    cypher_prompt=CYPHER_PROMPT
)


print("Chat Init .....")
while True:
    question = input("Enter Quesion : ")
    if question == 'q':
        break
    
    print("Process.....")
    try:
        res = chain.invoke(question)
        print(f"Answer: {res['result']}")
        print("-------------------------------------\n")
    except Exception as e:
        print(f'Exeption = {e}')

# question = "Show the basics information of company in database."
# try:
#     res = chain.invoke(question)
#     print(f"Response: {res['result']}")
# except Exception as e:
#     print("Error:", e)
