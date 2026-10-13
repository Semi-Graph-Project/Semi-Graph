"""Browser checks for the four-panel Streamlit comparison UI."""

import json

import pytest
from playwright.sync_api import expect


PANEL_NAMES = (
    "Vector-only RAG",
    "Graph-only RAG",
    "Agent + Vector",
    "Agent + Graph",
)


def open_app(page, url):
    page.goto(url)
    expect(page.locator(".comparison-card")).to_have_count(4, timeout=30_000)
    for name in PANEL_NAMES:
        expect(page.locator(".comparison-card h3", has_text=name)).to_be_visible()


def submit_question(page, query):
    prompt = page.locator('[data-testid="stChatInput"] textarea')
    prompt.fill(query)
    prompt.press("Enter")
    expect(page.locator(".question-banner p")).to_have_text(query)
    expect(page.locator(".comparison-card .card-status.complete")).to_have_count(
        4, timeout=20_000
    )


def test_frozen_replay_opens_four_chats_without_backend_calls(page, fake_app_server):
    url, calls = fake_app_server
    previous_calls = len(calls.read_text().splitlines()) if calls.exists() else 0
    open_app(page, url)
    page.get_by_text("Frozen replay", exact=True).click()

    expect(page.locator(".question-query-id")).to_have_text("FRKG111")
    expect(page.locator(".comparison-card .card-status.complete")).to_have_count(4)
    page.locator(".comparison-card", has=page.get_by_role("heading", name="Vector-only RAG")).locator(
        ".chat-modal-trigger"
    ).click()
    dialog = page.locator("#chat-modal-vector")
    expect(dialog).to_be_visible()
    expect(dialog.locator(".live-label")).to_contain_text("FROZEN REPLAY")
    dialog.get_by_role("button", name="Close chat").click()
    expect(dialog).not_to_be_visible()
    current_calls = len(calls.read_text().splitlines()) if calls.exists() else 0
    assert current_calls == previous_calls


def test_live_results_citations_trace_and_history(page, fake_app_server):
    url, calls = fake_app_server
    open_app(page, url)
    previous_calls = len(calls.read_text().splitlines()) if calls.exists() else 0
    first_query = "What does NVIDIA make?"
    submit_question(page, first_query)
    expect(page.locator(".comparison-card .latency-metric")).to_have_count(4)
    for metric in page.locator(".comparison-card .latency-metric").all():
        expect(metric).to_contain_text("0.2s total latency")

    first_calls = [
        json.loads(line) for line in calls.read_text().splitlines()[previous_calls:]
    ]
    assert len(first_calls) == 4
    assert {call["mode"] for call in first_calls} == {
        "vector", "graph", "agent_vector", "agent_graph"
    }
    assert {call["query"] for call in first_calls} == {first_query}
    assert {call["corpus"] for call in first_calls} == {"benchmark"}

    card = page.locator(".comparison-card", has=page.get_by_role("heading", name="Vector-only RAG"))
    card.locator(".chat-modal-trigger").click()
    dialog = page.locator("#chat-modal-vector")
    expect(dialog).to_be_visible()
    expect(dialog.locator(".answer-markdown")).to_contain_text("vector answer")
    expect(dialog.locator(".citation-chip")).to_have_count(1)
    dialog.locator(".citation-chip").click()
    inspector = page.locator("#source-vector-current-1")
    expect(inspector).to_be_visible()
    expect(inspector).to_contain_text("NVIDIA makes GPUs <not HTML>.")
    inspector.get_by_role("button", name="Close source inspector").click()
    expect(inspector).not_to_be_visible()

    dialog.locator(".chat-advanced summary").click()
    expect(dialog.locator(".trace-table")).to_be_visible()
    dialog.locator(".synthesis-chunks-details > summary").click()
    expect(dialog).to_contain_text("NOT CITED")
    expect(dialog.locator(".answer-markdown")).not_to_contain_text("<button")
    page.keyboard.press("Escape")
    expect(dialog).not_to_be_visible()

    for mode, name in (
        ("graph", "Graph-only RAG"),
        ("agent_vector", "Agent + Vector"),
        ("agent_graph", "Agent + Graph"),
    ):
        other_card = page.locator(
            ".comparison-card", has=page.get_by_role("heading", name=name)
        )
        other_card.locator(".chat-modal-trigger").click()
        other_dialog = page.locator(f"#chat-modal-{mode}")
        expect(other_dialog).to_be_visible()
        other_dialog.locator(".chat-advanced > summary").click()
        expect(other_dialog.locator(".trace-event-row")).not_to_have_count(0)
        other_dialog.locator(".citation-chip").first.click()
        expect(page.locator(".source-inspector:popover-open")).to_be_visible()
        page.keyboard.press("Escape")
        other_dialog.get_by_role("button", name="Close chat").click()

    second_query = "What else does NVIDIA sell?"
    submit_question(page, second_query)
    assert len(calls.read_text().splitlines()) - previous_calls == 8
    card.locator(".chat-modal-trigger").click()
    dialog = page.locator("#chat-modal-vector")
    expect(dialog.locator(".chat-exchange")).to_have_count(2)
    expect(dialog).to_contain_text(first_query)
    expect(dialog).to_contain_text(second_query)


@pytest.mark.parametrize("query,status", [
    ("ERROR CASE: NVIDIA", "Failed"),
    ("TIMEOUT CASE: NVIDIA", "Timeout"),
])
def test_one_panel_failure_does_not_hide_other_results(page, fake_app_server, query, status):
    url, _ = fake_app_server
    open_app(page, url)
    prompt = page.locator('[data-testid="stChatInput"] textarea')
    prompt.fill(query)
    prompt.press("Enter")

    expect(page.locator(".comparison-card .card-status.complete")).to_have_count(
        3, timeout=20_000
    )
    graph_card = page.locator(
        ".comparison-card", has=page.get_by_role("heading", name="Graph-only RAG")
    )
    expect(graph_card.locator(".card-status")).to_contain_text(status)
    graph_card.locator(".chat-modal-trigger").click()
    expect(page.locator("#chat-modal-graph")).to_contain_text(
        "Test retrieval error" if status == "Failed" else "Test run timed out"
    )


def test_switching_corpus_clears_live_results_and_disables_replay(page, fake_app_server):
    url, calls = fake_app_server
    open_app(page, url)
    submit_question(page, "NVIDIA query before switching")
    assert len(calls.read_text().splitlines()) >= 4

    page.locator('[data-testid="stSelectbox"]').first.click()
    page.get_by_role("option", name="Production · 7687").click()
    expect(page.locator(".question-banner")).to_contain_text(
        "Ask a question to compare the four retrieval configurations."
    )
    expect(page.locator(".card-status.complete")).to_have_count(0)
    expect(page.get_by_text("Frozen replay", exact=True)).to_have_count(0)
    expect(page.locator('[data-testid="stChatInput"] textarea')).to_be_visible()


def test_layout_on_desktop_and_mobile(page, fake_app_server):
    url, _ = fake_app_server
    page.set_viewport_size({"width": 1280, "height": 720})
    open_app(page, url)
    expect(page.locator('[data-testid="stChatInput"]')).to_be_visible()
    desktop = page.evaluate("""() => ({
      viewport: innerHeight,
      gridBottom: document.querySelector('.comparison-grid').getBoundingClientRect().bottom,
      inputBottom: document.querySelector('[data-testid="stChatInput"]').getBoundingClientRect().bottom,
      overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth
    })""")
    assert desktop["gridBottom"] <= desktop["viewport"] + 2
    assert desktop["inputBottom"] <= desktop["viewport"] + 2
    assert not desktop["overflowX"]

    submit_question(page, "NVIDIA layout check")
    expect(page.locator('[data-testid="stChatInput"]')).to_be_visible()
    desktop_with_results = page.evaluate("""() => ({
      gridBottom: document.querySelector('.comparison-grid').getBoundingClientRect().bottom,
      inputBottom: document.querySelector('[data-testid="stChatInput"]').getBoundingClientRect().bottom,
      overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth
    })""")
    assert desktop_with_results["gridBottom"] <= 722
    assert desktop_with_results["inputBottom"] <= 722
    assert not desktop_with_results["overflowX"]

    page.set_viewport_size({"width": 390, "height": 844})
    mobile = page.evaluate("""() => ({
      overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      cards: [...document.querySelectorAll('.comparison-card')].map(card =>
        card.getBoundingClientRect().width)
    })""")
    assert not mobile["overflowX"]
    assert all(width <= 390 for width in mobile["cards"])
