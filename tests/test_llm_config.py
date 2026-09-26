"""Tests for provider-aware LLM configuration."""

from types import SimpleNamespace

import pytest
import yaml

from semigraph import connections
from semigraph.config import Config


@pytest.mark.parametrize("setting", [None, True, False])
def test_evaluation_answer_audit_config(tmp_path, setting):
    config_path = tmp_path / "config.yaml"
    data = {"financial": {"metric_registry": {
        "reported": ["revenue"],
        "derived": ["margin"],
        "snapshot": ["stock_price"],
    }}}
    if setting is not None:
        data["evaluation"] = {"answer_audit_enabled": setting}
    config_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    cfg = Config(config_path)
    assert cfg.eval_answer_audit_enabled is (True if setting is None else setting)


def test_evaluation_answer_audit_rejects_string_false(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text('evaluation:\n  answer_audit_enabled: "false"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="must be a boolean"):
        Config(config_path)


def test_get_neo4j_driver_disables_deprecation_notifications(monkeypatch):
    captured = {}

    def fake_driver(uri, **kwargs):
        captured["uri"] = uri
        captured.update(kwargs)
        return "driver"

    monkeypatch.setattr(connections.GraphDatabase, "driver", fake_driver)
    cfg = SimpleNamespace(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="secret",
    )

    driver = connections.get_neo4j_driver(cfg)

    assert driver == "driver"
    assert captured["auth"] == ("neo4j", "secret")
    assert captured["notifications_disabled_classifications"] == [
        connections.NotificationDisabledClassification.DEPRECATION,
    ]


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
        llm_reasoning={"effort": "high"},
    )

    connections.get_llm(cfg)

    assert captured["model"] == "deepseek/deepseek-v4-flash"
    assert captured["api_key"] == "selected-provider-key"
    assert captured["base_url"] == "https://openrouter.ai/api/v1"
    assert captured["reasoning_effort"] == "high"
