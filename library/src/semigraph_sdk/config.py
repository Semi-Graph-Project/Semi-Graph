"""Explicit, workspace-local configuration for one knowledge base."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ConfigError(ValueError):
    """The SDK workspace configuration or secrets are invalid."""


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    uri: str
    user: str
    name: str
    password_key: str = "NEO4J_PASSWORD"

    @field_validator("uri")
    @classmethod
    def valid_uri(cls, value: str) -> str:
        schemes = (
            "bolt://", "neo4j://", "bolt+s://", "neo4j+s://",
            "bolt+ssc://", "neo4j+ssc://",
        )
        if not value.startswith(schemes):
            raise ValueError("database.uri must use a supported Neo4j Bolt scheme")
        return value

    @field_validator("user", "name", "password_key")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("database values must not be empty")
        return value


class EmbeddingConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str
    revision: str
    dimension: int = Field(ge=1, le=4096)
    normalize: bool = True
    device: str = "cpu"

    @field_validator("model", "revision", "device")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("embedding values must not be empty")
        return value

    @property
    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json")
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class LLMConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    model: str
    api_key_key: str
    base_url: str | None = None

    @field_validator("provider", "model", "api_key_key")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("LLM values must not be empty")
        return value


class VectorRetrievalConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    min_score: float | None = Field(default=None, ge=-1, le=1)


class GraphRetrievalConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    seed_mode: Literal["triple", "entity", "chunk"] = "triple"
    seed_k: int = Field(default=10, ge=1, le=100)
    min_seed_score: float | None = Field(default=None, ge=-1, le=1)
    damping: float = Field(default=0.5, gt=0, lt=1)
    max_iterations: int = Field(default=20, ge=1, le=100)
    top_k_entities_in_trace: int = Field(default=20, ge=0, le=100)


class AgentRetrievalConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_planned_tasks: int = Field(default=3, ge=1, le=16)
    max_attempts_per_task: int = Field(default=2, ge=1, le=8)
    max_parallel_tasks: int = Field(default=2, ge=1, le=16)
    max_relation_hints: int = Field(default=8, ge=0, le=32)


class RetrievalConfig(BaseModel):
    """Bounded retrieval controls; omitted from old configs by default."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    per_search_k: int = Field(default=10, ge=1, le=100)
    max_top_k: int = Field(default=100, ge=1, le=1000)
    vector: VectorRetrievalConfig = Field(default_factory=VectorRetrievalConfig)
    graph: GraphRetrievalConfig = Field(default_factory=GraphRetrievalConfig)
    agent: AgentRetrievalConfig = Field(default_factory=AgentRetrievalConfig)

    @model_validator(mode="after")
    def validate_budgets(self) -> RetrievalConfig:
        if self.per_search_k > self.max_top_k:
            raise ValueError("retrieval.per_search_k must not exceed retrieval.max_top_k")
        if self.agent.max_planned_tasks > self.max_top_k:
            raise ValueError("Agent tasks must fit within retrieval.max_top_k")
        return self


class SDKConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_id: str = Field(pattern=r"^[a-z][a-z0-9-]{5,62}$")
    database: DatabaseConfig
    embedding: EmbeddingConfig
    secrets_file: Path
    llm: LLMConfig | None = None
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    config_path: Path = Field(exclude=True)

    @classmethod
    def from_file(cls, path: str | Path) -> SDKConfig:
        config_path = Path(path).expanduser().resolve()
        try:
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise ConfigError(f"Cannot read SDK config {config_path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ConfigError("SDK config must be a YAML mapping")
        try:
            config = cls.model_validate({**raw, "config_path": config_path})
        except ValueError as exc:
            raise ConfigError(f"Invalid SDK config {config_path}: {exc}") from exc
        secrets = config.secrets_file.expanduser()
        if not secrets.is_absolute():
            secrets = config_path.parent / secrets
        object.__setattr__(config, "secrets_file", secrets.resolve())
        return config

    def secret(self, secret_name: str) -> str:
        try:
            lines = self.secrets_file.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ConfigError(f"Cannot read SDK secrets file {self.secrets_file}: {exc}") from exc
        values: dict[str, str] = {}
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if "=" not in line:
                raise ConfigError(f"Invalid KEY=VALUE line in {self.secrets_file}")
            entry_key, value = line.split("=", 1)
            values[entry_key.strip()] = value.strip().strip('"').strip("'")
        value = values.get(secret_name)
        if not value:
            raise ConfigError(f"Missing {secret_name} in {self.secrets_file}")
        return value

    def database_password(self) -> str:
        return self.secret(self.database.password_key)

    def llm_api_key(self) -> str:
        if self.llm is None:
            raise ConfigError("No LLM is configured in this SDK workspace")
        return self.secret(self.llm.api_key_key)
