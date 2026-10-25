"""Explicit, workspace-local configuration for one knowledge base."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class SDKConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_id: str = Field(pattern=r"^[a-z][a-z0-9-]{5,62}$")
    database: DatabaseConfig
    embedding: EmbeddingConfig
    secrets_file: Path
    llm: LLMConfig | None = None
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
