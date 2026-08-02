from __future__ import annotations

from functools import lru_cache

from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from neo4j import Driver, GraphDatabase

from semigraph.config import Config, get_config


def get_neo4j(config: Config | None = None) -> Neo4jGraph:
    """Return a connected Neo4jGraph instance (high-level LangChain wrapper)."""
    cfg = config or get_config()
    return Neo4jGraph(
        url=cfg.neo4j_uri,
        username=cfg.neo4j_user,
        password=cfg.neo4j_password,
    )


def get_neo4j_driver(config: Config | None = None) -> Driver:
    """Return a raw neo4j Driver — caller is responsible for closing it."""
    cfg = config or get_config()
    return GraphDatabase.driver(cfg.neo4j_uri, auth=(cfg.neo4j_user, cfg.neo4j_password))


def get_llm(config: Config | None = None) -> ChatOpenAI:
    """Return the configured OpenAI-compatible chat client."""
    cfg = config or get_config()
    return ChatOpenAI(
        model=cfg.llm_model,
        api_key=cfg.llm_api_key,
        base_url=cfg.llm_base_url,
        temperature=cfg.llm_temperature,
        timeout=120.0,
        max_retries=2,
    )


# def get_embeddings(config: Config | None = None) -> OpenAIEmbeddings:
#     """Return an OpenAIEmbeddings client (uses OPENAI_API_KEY from .env)."""
#     cfg = config or get_config()
#     return OpenAIEmbeddings(
#         api_key=cfg.openai_api_key,
    # )
