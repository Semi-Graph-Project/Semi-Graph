"""Minimal smoke test for LangChain's GraphCypherQAChain.

Usage:
    python scripts/text_to_cypher.py
    python scripts/text_to_cypher.py "Find chunks about NVIDIA supply-chain risks"

The chain executes its generated Cypher, so use a read-only Neo4j account.
"""
from __future__ import annotations

import argparse

from langchain_core.prompts import PromptTemplate
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain

from semigraph.connections import get_llm, get_neo4j
from semigraph.config import get_config


CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "examples", "question"],
    template="""You translate questions into Neo4j Cypher.
Use only labels, relationships, and properties from this schema:
{schema}

Generate exactly one read-only query. Use MATCH and RETURN; WHERE, WITH, and
ORDER BY are allowed when needed. Never use CREATE, MERGE, SET, DELETE, REMOVE,
CALL, or administrative commands.

Every result row must be an evidence Chunk. Use `c` as the Chunk variable and
finish the query with these exact output fields:
RETURN DISTINCT c.chunk_id AS chunk_id,
                c.text AS text,
                c.source_file AS source_file,
                c.page_id AS page_id,
                c.fiscal_year AS fiscal_year
LIMIT 10
Return only the Cypher query, without Markdown or explanation.

Examples:
{examples}

Question: {question}
Cypher:""",
)


def answer_with_chunks(question: str) -> tuple[str, list[dict]]:
    """Return the final answer and up to 10 evidence chunks from Neo4j."""
    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri
    graph = get_neo4j(cfg)
    try:
        chain = GraphCypherQAChain.from_llm(
            llm=get_llm(cfg),
            graph=graph,
            cypher_prompt=CYPHER_PROMPT,
            top_k=10,
            return_intermediate_steps=True,
            allow_dangerous_requests=True,
        )
        result = chain.invoke({"query": question})

        chunks = next(
            (
                step["context"]
                for step in result["intermediate_steps"]
                if "context" in step
            ),
            [],
        )
        return str(result["result"]), chunks[:10]
    finally:
        graph.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Answer a question with LangChain's GraphCypherQAChain."
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="Find up to 10 evidence chunks about NVIDIA's supply-chain risks.",
        help="Natural-language question to answer from Neo4j.",
    )
    question = parser.parse_args().question

    answer, chunks = answer_with_chunks(question)

    print("\n=== Final Answer ===")
    print(answer)

    print(f"\n=== Retrieved Chunks ({len(chunks)}/10) ===")
    for position, chunk in enumerate(chunks, start=1):
        print(f"\n--- Chunk {position} ---")
        print(f"Chunk ID : {chunk.get('chunk_id') or '-'}")


if __name__ == "__main__":
    main()
