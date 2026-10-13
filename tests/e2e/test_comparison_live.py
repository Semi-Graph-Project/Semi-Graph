"""Opt-in live smoke: one browser question per Neo4j corpus, four modes each."""

import json
import os
from pathlib import Path
from time import monotonic

import pytest
from neo4j import GraphDatabase
from playwright.sync_api import expect

from semigraph.config import get_config


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "tests" / "e2e" / "artifacts"
QUERY = "What products does NVIDIA disclose in its 2024 10-K?"
MODES = {
    "vector": "Vector-only RAG",
    "graph": "Graph-only RAG",
    "agent_vector": "Agent + Vector",
    "agent_graph": "Agent + Graph",
}


@pytest.fixture(scope="module")
def live_preflight():
    if os.environ.get("SEMIGRAPH_LIVE_UI_TEST") != "1":
        pytest.skip("Set SEMIGRAPH_LIVE_UI_TEST=1 to allow two paid live queries")

    cfg = get_config()
    assert cfg.llm_api_key, "LLM API key is missing; no query was submitted"
    for corpus, uri in (
        ("benchmark", cfg.controlled_neo4j_uri),
        ("production", cfg.production_neo4j_uri),
    ):
        with GraphDatabase.driver(
            uri,
            auth=(cfg.neo4j_user, cfg.neo4j_password),
            connection_timeout=5,
        ) as driver:
            driver.verify_connectivity()
            rows, _, _ = driver.execute_query(
                "MATCH (c:Chunk) WHERE toUpper(coalesce(toString(c.ticker), '')) = 'NVDA' "
                "AND toString(c.fiscal_year) = '2024' RETURN count(c) AS chunks"
            )
            assert rows[0]["chunks"] > 0, f"{corpus} has no NVIDIA 2024 chunks"


@pytest.mark.parametrize("corpus,label", [
    ("benchmark", "Benchmark · 7690"),
    ("production", "Production · 7687"),
])
def test_one_live_query_per_corpus(
    page, start_streamlit, tmp_path, live_preflight, corpus, label
):
    """Exactly one submission per corpus; never retry a paid run."""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACTS / f"live_{corpus}.json"
    screenshot_path = ARTIFACTS / f"live_{corpus}_failure.png"
    report = {"corpus": corpus, "query": QUERY, "submitted": False, "panels": {}}
    started = monotonic()

    try:
        with start_streamlit(
            ROOT / "Demo" / "comparison_app.py",
            tmp_path / f"streamlit_{corpus}.log",
        ) as url:
            page.goto(url)
            expect(page.locator(".comparison-card")).to_have_count(4, timeout=30_000)
            if corpus == "production":
                page.locator('[data-testid="stSelectbox"]').first.click()
                page.get_by_role("option", name=label).click()

            prompt = page.locator('[data-testid="stChatInput"] textarea')
            prompt.fill(QUERY)
            prompt.press("Enter")
            report["submitted"] = True
            page.wait_for_function("""() => {
              const states = [...document.querySelectorAll('.comparison-card .card-status')];
              return states.length === 4 && states.every(node =>
                /Complete|Failed|Timeout/.test(node.textContent));
            }""", timeout=125_000)

            for mode, name in MODES.items():
                card = page.locator(
                    ".comparison-card", has=page.get_by_role("heading", name=name)
                )
                status_element = card.locator(".card-status")
                status = status_element.inner_text().strip()
                complete = "complete" in (status_element.get_attribute("class") or "").split()
                answer = card.locator(".card-answer-preview").inner_text()
                card.locator(".chat-modal-trigger").click()
                dialog = page.locator(f"#chat-modal-{mode}")
                expect(dialog).to_be_visible()
                dialog.locator(".chat-advanced > summary").click()
                trace_count = dialog.locator(".trace-event-row").count()
                citations = dialog.locator(".citation-chip")
                citation_count = citations.count()
                if citation_count:
                    citations.first.click()
                    inspector = page.locator(".source-inspector:popover-open")
                    expect(inspector).to_be_visible()
                    inspector.get_by_role(
                        "button", name="Close source inspector"
                    ).click()
                dialog.get_by_role("button", name="Close chat").click()
                report["panels"][mode] = {
                    "status": status,
                    "complete": complete,
                    "answer": answer,
                    "trace_steps": trace_count,
                    "citation_chips": citation_count,
                }

            assert all(
                panel["complete"] and panel["answer"]
                and panel["trace_steps"] > 0
                for panel in report["panels"].values()
            ), report["panels"]
    except Exception:
        if not page.is_closed():
            try:
                page.screenshot(path=str(screenshot_path), full_page=True, timeout=5000)
            except Exception:
                pass
        raise
    finally:
        report["elapsed_sec"] = round(monotonic() - started, 2)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
