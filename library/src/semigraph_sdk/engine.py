"""Public entry point for SDK database setup and text ingestion."""

from __future__ import annotations

from pathlib import Path

from neo4j import GraphDatabase

from .config import SDKConfig
from .database import SetupReport, setup_database
from .ingestion.embedding import Embedder, SentenceTransformerEmbedder
from .ingestion.extract import LLMExtractor, build_extractor
from .ingestion.models import IngestionReport
from .ingestion.pipeline import ingest_texts


class Engine:
    def __init__(self, config: SDKConfig) -> None:
        self.config = config
        self._driver = None

    @classmethod
    def from_config(cls, path: str | Path) -> Engine:
        return cls(SDKConfig.from_file(path))

    def setup(self) -> SetupReport:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.config.database.uri,
                auth=(self.config.database.user, self.config.database_password()),
            )
        try:
            return setup_database(self.config, self._driver)
        except Exception:
            self.close()
            raise

    def ingest(
        self,
        texts: list[str],
        *,
        extractor: LLMExtractor | None = None,
        embedder: Embedder | None = None,
    ) -> IngestionReport:
        """Extract, embed and publish plain text chunks to this knowledge base."""
        if not isinstance(texts, list):
            raise TypeError("Engine.ingest expects a list of text chunks")
        has_valid_text = any(
            isinstance(text, str) and bool(text.strip()) for text in texts
        )
        selected_extractor = extractor
        if selected_extractor is None and has_valid_text:
            selected_extractor = build_extractor(self.config)
        self.setup()
        selected_embedder = embedder
        if selected_embedder is None and has_valid_text:
            selected_embedder = SentenceTransformerEmbedder(self.config.embedding)
        if self._driver is None:  # setup() either opens it or raises
            raise RuntimeError("SDK database driver is unavailable")
        return ingest_texts(
            self._driver,
            self.config,
            texts,
            extractor=selected_extractor,
            embedder=selected_embedder,
        )

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> Engine:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
