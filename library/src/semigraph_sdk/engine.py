"""Public entry point for SDK database setup."""

from __future__ import annotations

from pathlib import Path

from neo4j import GraphDatabase

from .config import SDKConfig
from .database import SetupReport, setup_database


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

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> Engine:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
