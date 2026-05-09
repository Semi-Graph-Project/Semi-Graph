"""End-to-end smoke test for local Neo4j (Docker).

Run: python scripts/test_neo4j_connection.py
"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")


def main() -> None:
    print(f"[1/5] Connecting to {URI} as {USER}")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print("      OK")

    with driver.session() as session:
        print("[2/5] Cleaning previous test data (label :SmokeTest)")
        session.run("MATCH (n:SmokeTest) DETACH DELETE n")

        print("[3/5] Creating 2 nodes + 1 relationship")
        session.run(
            """
            CREATE (a:SmokeTest:Company {name: 'NVIDIA', ticker: 'NVDA'})
            CREATE (b:SmokeTest:Company {name: 'ASML', ticker: 'ASML'})
            CREATE (a)-[:SUPPLIED_BY {since: 2020}]->(b)
            """
        )

        print("[4/5] Reading back via Cypher")
        result = session.run(
            """
            MATCH (a:SmokeTest)-[r:SUPPLIED_BY]->(b:SmokeTest)
            RETURN a.name AS source, type(r) AS rel, b.name AS target, r.since AS since
            """
        )
        for record in result:
            print(f"      {record['source']} -[{record['rel']} since {record['since']}]-> {record['target']}")

        print("[5/5] Verifying APOC + GDS plugins")
        versions = session.run("RETURN apoc.version() AS apoc, gds.version() AS gds").single()
        print(f"      APOC: {versions['apoc']} | GDS: {versions['gds']}")

        session.run("MATCH (n:SmokeTest) DETACH DELETE n")
        print("      Cleaned up test data")

    driver.close()
    print("\nAll good — Neo4j is reachable end-to-end.")


if __name__ == "__main__":
    main()
