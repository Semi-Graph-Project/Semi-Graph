"""
Configuration loader for SemiGraph.
Reads .env for secrets and config/default.yaml for operational params.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

# Load .env from project root (works regardless of where script is run from)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


def _resolve_env_vars(value: str) -> str:
    """Replace ${VAR} placeholders with environment variable values."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_key = value[2:-1]
        return os.environ.get(env_key, "")
    return value


def _resolve_dict(d: dict) -> dict:
    """Recursively resolve env var placeholders in a dict."""
    resolved = {}
    for k, v in d.items():
        if isinstance(v, dict):
            resolved[k] = _resolve_dict(v)
        elif isinstance(v, str):
            resolved[k] = _resolve_env_vars(v)
        else:
            resolved[k] = v
    return resolved


class Config:
    """Project-wide configuration loaded from YAML + environment variables."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = _PROJECT_ROOT / "config" / "default.yaml"

        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        data = _resolve_dict(raw)

        # --- SEC EDGAR ---
        edgar = data.get("edgar", {})
        self.edgar_email: str = os.environ.get("EDGAR_EMAIL", edgar.get("email", ""))
        self.edgar_org: str = os.environ.get("EDGAR_ORGANIZATION", edgar.get("organization", ""))
        self.filing_types: list[str] = edgar.get("filing_types", ["10-K"])
        self.edgar_limit: int = edgar.get("limit", 5)

        # --- Tickers ---
        self.tickers: list[str] = data.get("tickers", [])

        # --- Paths (always relative to project root) ---
        paths = data.get("paths", {})
        self.raw_dir = _PROJECT_ROOT / paths.get("raw", "data/raw")
        self.processed_dir = _PROJECT_ROOT / paths.get("processed", "data/processed")
        self.log_dir = _PROJECT_ROOT / paths.get("logs", "log")
        self.news_dir = _PROJECT_ROOT / paths.get("news", "data/news")
        self.schemas_dir = _PROJECT_ROOT / paths.get("schemas", "data/schemas")
        self.evaluate_dir = _PROJECT_ROOT / paths.get("evaluate", "data/evaluate")

        # --- Preprocessing ---
        pre = data.get("preprocess", {})
        self.markdown_method: str = pre.get("markdown_method", "html2text")
        self.extract_sections: bool = pre.get("extract_sections", True)
        self.use_fallback_extraction: bool = pre.get("use_fallback_extraction", True)
        self.target_sections: list[str] = pre.get("target_sections", ["Item 1", "Item 1A", "Item 7"])

        # --- Chunker ---
        chunker = data.get("chunker", {})
        self.chunk_size: int = chunker.get("chunk_size", 4500)
        self.chunk_overlap: int = chunker.get("chunk_overlap", 600)

        # --- News tool (Phase E) ---
        news_cfg = data.get("news", {})
        self.news_days_back: int = news_cfg.get("days_back", 90)
        self.news_cache_dir: Path = _PROJECT_ROOT / news_cfg.get("cache_dir", "data/news/cache")
        self.news_default_depth: str = news_cfg.get("default_depth", "headline")

        # --- LLM ---
        llm = data.get("llm", {})
        self.llm_provider: str = llm.get("provider", "deepseek")
        self.llm_model: str = llm.get("model", "deepseek-chat")
        self.llm_temperature: float = llm.get("temperature", 0.0)
        self.llm_base_url: str = llm.get("base_url", "https://api.deepseek.com")

        # --- API Keys (from env only) ---
        self.deepseek_api_key: str = os.environ.get("DEEPSEEK_API_KEY", "")
        self.openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
        self.google_api_key: str = os.environ.get("GOOGLE_API_KEY", "")
        self.finnhub_api_key: str = os.environ.get("FINNHUB_API_KEY", "")

        # --- Neo4j (from env only) ---
        self.neo4j_uri: str = os.environ.get("NEO4J_URI", "")
        self.neo4j_user: str = os.environ.get("NEO4J_USER", "neo4j")
        self.neo4j_password: str = os.environ.get("NEO4J_PASSWORD", "")

        # --- KG Extraction ---
        kg = data.get("kg", {})
        self.kg_max_workers: int = kg.get("max_workers", 16)
        self.kg_batch_size: int = kg.get("batch_size", 5)

        # --- Deterministic graph repair ---
        repair = data.get("graph_repair", {})
        self.graph_repair_enabled: bool = repair.get("enabled", True)
        self.graph_repair_method: str = repair.get(
            "method", "deterministic_graph_repair_v1"
        )
        self.graph_repair_filer_aliases: dict[str, str] = {
            str(ticker).upper(): str(name)
            for ticker, name in repair.get("filer_aliases", {}).items()
        }

        # --- Embeddings ---
        emb = data.get("embeddings", {})
        self.embed_model: str = emb.get("model", "BAAI/bge-base-en-v1.5")
        self.embed_dim: int = emb.get("dimensions", 768)
        self.embed_batch_size: int = emb.get("batch_size", 32)
        self.embed_device: str = emb.get("device", "cpu")
        self.embed_normalize: bool = emb.get("normalize", True)

    @property
    def project_root(self) -> Path:
        return _PROJECT_ROOT


@lru_cache(maxsize=1)
def get_config(config_path: Optional[str] = None) -> Config:
    """Return cached Config instance."""
    path = Path(config_path) if config_path else None
    return Config(config_path=path)
