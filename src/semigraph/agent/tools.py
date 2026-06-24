from __future__ import annotations

from typing import Callable

from semigraph.online.financial_search import financial_search
from semigraph.online.graph_search import graph_search
from semigraph.online.hybrid_search import hybrid_search
from semigraph.online.news_search import news_search
from semigraph.online.vector_search import vector_search


DEFAULT_TOP_K = 5

# Shared retrieval dispatch for the agent layer. All retrievers return the
# same 6-key chunk contract, so execute_node can call them uniformly.
RETRIEVERS: dict[str, Callable[..., list[dict]]] = {
    "vector": vector_search,
    "graph": graph_search,
    "hybrid": hybrid_search,
    "financial": financial_search,
    "news": news_search,
}


TOOL_SCHEMAS: list[dict] = [
    {
        "type" : "function",
        "function": {
            "name": "graph",
            "description": "Relational reasoning across entities — supplier chains, customer relationships, subsidiaries, competitive positioning (X → Y → Z multi-hop paths in a knowledge graph)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural language question to query the knowledge graph.",
                    }
                },
                "required": ["query"],
            }
        }
    },

    {
        "type" : "function",
        "function": {
            "name": "vector",
            "description": "semantic similarity search over SEC filing narrative — business strategy, product descriptions, risk factors, management commentary. Use when the question asks what a company SAYS or DESCRIBES about a topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The input text to retrieve vector embeddings for.",
                    }
                },
                "required": ["query"],
            }
        }
    },

    {
        "type" : "function",
        "function": {
            "name": "financial",
            "description": "Retrieve financial data and insights based on a natural language query. This tool can access financial databases and APIs to provide relevant information such as stock prices, financial statements, market trends, and other financial metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural language question to retrieve financial data and insights.",
                    }
                },
                "required": ["query"],
            }
        }
    },

    {
        "type" : "function",
        "function": {
            "name": "news",
            "description": "Retrieve the latest news articles and updates based on a natural language query. This tool can access news databases and APIs to provide relevant information such as recent events, market news, company announcements, and other newsworthy topics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural language question to retrieve the latest news articles and updates.",
                    }
                },
                "required": ["query"],
            }
        }
    }


]
