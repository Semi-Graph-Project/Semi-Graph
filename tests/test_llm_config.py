"""Tests for provider-aware LLM configuration."""

from types import SimpleNamespace

from semigraph import connections
from semigraph.config import Config


def test_default_llm_uses_openrouter_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")

    cfg = Config()

    assert cfg.llm_provider == "openrouter"
    assert cfg.llm_model == "openai/gpt-5.6-luna"
    assert cfg.llm_reasoning == {"effort": "max"}
    assert cfg.llm_base_url == "https://openrouter.ai/api/v1"
    assert cfg.llm_api_key == "test-openrouter-key"


def test_get_llm_uses_provider_selected_key(monkeypatch):
    captured = {}

    def fake_chat_openai(**kwargs):
        captured.update(kwargs)
        return kwargs

    monkeypatch.setattr(connections, "ChatOpenAI", fake_chat_openai)
    cfg = SimpleNamespace(
        llm_model="deepseek/deepseek-v4-flash",
        llm_api_key="selected-provider-key",
        llm_base_url="https://openrouter.ai/api/v1",
        llm_temperature=0.0,
        llm_reasoning={"effort": "max"},
    )

    connections.get_llm(cfg)

    assert captured["model"] == "deepseek/deepseek-v4-flash"
    assert captured["api_key"] == "selected-provider-key"
    assert captured["base_url"] == "https://openrouter.ai/api/v1"
    assert captured["reasoning"] == {"effort": "max"}
