from semigraph.connections import get_neo4j, get_llm
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


llm = get_llm()
response = llm.invoke("Say hello in one word.")
print(response.content) 

# Test 2: Neo4j
graph = get_neo4j()
result = graph.query("RETURN 1 AS test")
print(result)


llm2 = get_llm()
print(llm is llm2)