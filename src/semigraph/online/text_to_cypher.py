"""Text-to-Cypher retrieval for evidence Chunks."""
from __future__ import annotations

from langchain_core.prompts import PromptTemplate
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain

from semigraph.config import Config, get_config
from semigraph.connections import get_llm, get_neo4j


CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "examples", "question", "top_k"],
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
LIMIT {top_k}
Return only the Cypher query, without Markdown or explanation.

Examples:
{examples}

Question: {question}
Cypher:""",
)


def text_to_cypher_search(
    question: str,
    top_k_chunks: int = 10,
    cfg: Config | None = None,
) -> dict:
    """Generate Cypher and return up to ``top_k_chunks`` evidence Chunks."""
    if top_k_chunks < 1:
        raise ValueError("top_k_chunks must be greater than zero")

    cfg = cfg or get_config()
    graph = get_neo4j(cfg)
    try:
        chain = GraphCypherQAChain.from_llm(
            llm=get_llm(cfg),
            graph=graph,
            cypher_prompt=CYPHER_PROMPT.partial(top_k=top_k_chunks),
            top_k=top_k_chunks,
            return_direct=True,
            return_intermediate_steps=True,
            allow_dangerous_requests=True,
        )
        result = chain.invoke({"query": question})

        rows = result.get("result", [])
        if not isinstance(rows, list):
            raise RuntimeError("Text-to-Cypher result must be a list of rows")

        chunks = []
        seen_chunk_ids = set()
        for row in rows:
            if not isinstance(row, dict) or not row.get("chunk_id"):
                raise RuntimeError("Text-to-Cypher returned a row without chunk_id")
            chunk_id = str(row["chunk_id"])
            if chunk_id not in seen_chunk_ids:
                chunks.append(row)
                seen_chunk_ids.add(chunk_id)

        generated_cypher = next(
            (
                str(step["query"])
                for step in result.get("intermediate_steps", [])
                if "query" in step
            ),
            "",
        )
        return {
            "chunks": chunks[:top_k_chunks],
            "generated_cypher": generated_cypher,
        }
    finally:
        graph.close()



if __name__ == "__main__":
    cfg = get_config()
    cfg.neo4j_uri = cfg.controlled_neo4j_uri
    text_to_cypher_search("Nvdia Main Business?",10,cfg)