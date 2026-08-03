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
        self.evaluate_dir = _PROJECT_ROOT / paths.get("evaluate", "benchmark/datasets")

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
        self.llm_provider: str = llm.get("provider", "openrouter")
        self.llm_model: str = llm.get(
            "model", "deepseek/deepseek-v4-flash"
        )
        self.llm_temperature: float = llm.get("temperature", 0.0)
        self.llm_reasoning: dict[str, str] = llm.get("reasoning", {})
        self.llm_base_url: str = llm.get(
            "base_url", "https://openrouter.ai/api/v1"
        )

        # --- API Keys (from env only) ---
        self.deepseek_api_key: str = os.environ.get("DEEPSEEK_API_KEY", "")
        self.openrouter_api_key: str = os.environ.get("OPENROUTER_API_KEY", "")
        self.openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
        self.google_api_key: str = os.environ.get("GOOGLE_API_KEY", "")
        self.finnhub_api_key: str = os.environ.get("FINNHUB_API_KEY", "")

        llm_api_keys = {
            "deepseek": self.deepseek_api_key,
            "openrouter": self.openrouter_api_key,
            "openai": self.openai_api_key,
        }
        self.llm_api_key: str = llm_api_keys.get(self.llm_provider, "")

        # --- Neo4j (from env only) ---
        self.neo4j_uri: str = os.environ.get("NEO4J_URI", "")
        self.neo4j_user: str = os.environ.get("NEO4J_USER", "neo4j")
        self.neo4j_password: str = os.environ.get("NEO4J_PASSWORD", "")

        # --- KG Extraction ---
        kg = data.get("kg", {})
        self.kg_max_workers: int = kg.get("max_workers", 16)
        self.kg_batch_size: int = kg.get("batch_size", 5)

        # --- Graph retrieval ---
        graph = data.get("graph", {})
        self.informative_rel_types: list[str] = [
            str(rel_type).upper()
            for rel_type in graph.get("informative_rel_types", [])
        ]

        # --- Evidence-grounded graph repair ---
        repair = data.get("graph_repair", {})
        self.graph_repair_enabled: bool = repair.get("enabled", True)
        self.graph_repair_method: str = repair.get(
            "method", "llm_evidence_graph_repair_v1"
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

        # --- Reranker ---
        reranker = data.get("reranker", {})
        self.reranker_provider = reranker.get("provider", "openrouter")
        self.reranker_model = reranker.get(
            "model", "cohere/rerank-4-fast"
        )
        self.reranker_base_url = reranker.get(
            "base_url", "https://openrouter.ai/api/v1"
        )
        self.reranker_timeout_seconds = reranker.get("timeout_seconds", 60)
        self.reranker_max_retries = reranker.get("max_retries", 2)

        # --- Agent retrieval (Phase T production profile) ---
        agent_retrieval = data.get("agent_retrieval", {})
        self.agent_retrieval: dict[str, dict] = {
            "vector": dict(agent_retrieval.get("vector", {})),
            "graph": dict(agent_retrieval.get("graph", {})),
        }

        # --- Agent harness budgets ---
        agent_harness = data.get("agent_harness", {})
        self.agent_max_parallel_tasks: int = int(
            agent_harness.get("max_parallel_tasks", 2)
        )
        if not 1 <= self.agent_max_parallel_tasks <= 5:
            raise ValueError(
                "agent_harness.max_parallel_tasks must be 1..5"
            )

        self.agent_max_attempts_per_task: int = int(
            agent_harness.get("max_attempts_per_task", 3)
        )
        if not 1 <= self.agent_max_attempts_per_task <= 3:
            raise ValueError("agent_harness.max_attempts_per_task must be 1..3")

        self.agent_max_assessment_attempts: int = int(
            agent_harness.get("max_assessment_attempts", 2)
        )
        if not 1 <= self.agent_max_assessment_attempts <= 2:
            raise ValueError(
                "agent_harness.max_assessment_attempts must be 1..2"
            )

        self.agent_max_technical_retries: int = int(
            agent_harness.get("max_technical_retries", 1)
        )
        if not 0 <= self.agent_max_technical_retries <= 3:
            raise ValueError(
                "agent_harness.max_technical_retries must be 0..3"
            )

        self.agent_assess_context_max_chars: int = int(
            agent_harness.get("assess_context_max_chars", 12000)
        )
        if self.agent_assess_context_max_chars < 2000:
            raise ValueError(
                "agent_harness.assess_context_max_chars must be >= 2000"
            )

        # --- Financial PostgreSQL (Phase F.v2) ---
        financial = data.get("financial", {})
        self.financial_backend: str = financial.get("backend", "postgresql")
        self.financial_expected_company_count: int = int(
            financial.get("expected_company_count", 14)
        )
        self.financial_annual_reports: int = int(
            financial.get("annual_reports", 3)
        )
        self.financial_quarterly_reports: int = int(
            financial.get("quarterly_reports", 8)
        )
        self.financial_request_interval_seconds: float = float(
            financial.get("request_interval_seconds", 1.1)
        )
        self.financial_max_retries: int = int(financial.get("max_retries", 3))
        self.financial_query_timeout_ms: int = int(
            financial.get("query_timeout_ms", 5000)
        )
        self.financial_max_query_rows: int = int(
            financial.get("max_query_rows", 50)
        )
        metric_registry = financial.get("metric_registry", {})
        self.financial_metric_registry: dict[str, frozenset[str]] = {
            group: frozenset(
                str(metric).strip().lower()
                for metric in metric_registry.get(group, [])
                if str(metric).strip()
            )
            for group in ("reported", "derived", "snapshot")
        }
        missing_metric_groups = [
            group
            for group, metrics in self.financial_metric_registry.items()
            if not metrics
        ]
        if missing_metric_groups:
            raise ValueError(
                "financial.metric_registry must define non-empty groups: "
                + ", ".join(missing_metric_groups)
            )

        self.postgres_admin_dsn: str = os.environ.get("POSTGRES_ADMIN_DSN", "")
        self.postgres_agent_dsn: str = os.environ.get("POSTGRES_AGENT_DSN", "")
        self.postgres_agent_user: str = os.environ.get(
            "POSTGRES_AGENT_USER", "semigraph_agent"
        )
        self.postgres_agent_password: str = os.environ.get(
            "POSTGRES_AGENT_PASSWORD", ""
        )

    @property
    def project_root(self) -> Path:
        return _PROJECT_ROOT


@lru_cache(maxsize=1)
def get_config(config_path: Optional[str] = None) -> Config:
    """Return cached Config instance."""
    path = Path(config_path) if config_path else None
    return Config(config_path=path)
