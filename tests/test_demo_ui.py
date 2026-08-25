from Demo import Component
from Demo.Style import CUSTOM_CSS


def test_live_result_uses_scroll_viewport_and_real_markdown_html():
    result = {
        "status": "complete",
        "answer": "**Grounded answer**\n\n- First fact\n- Second fact",
        "citations": [{"ticker": "INTC", "chunk_id": "chunk-1"}],
        "trace": [{"stage": "retrieval", "retriever": "vector"}],
        "latency_sec": 1.25,
    }

    markup = Component._build_live_result_body(
        Component.CONFIGURATIONS[0],
        "What is Intel's main business?",
        result,
    )

    assert markup.startswith('<div class="panel-result">')
    assert '<div class="panel-scroll chat-history"' in markup
    assert '<strong>Grounded answer</strong>' in markup
    assert "<li>First fact</li>" in markup
    assert '<details class="result-disclosure citation-details">' in markup
    assert '<details class="result-disclosure trace-details">' in markup
    assert 'class="panel-scroll chat-history"' in markup
    assert 'class="chat-message-row user-message-row"' in markup
    assert 'class="chat-message-row assistant-message-row"' in markup
    assert markup.count("<section") == markup.count("</section>")
    assert '<span class="turn-label">PROMPT</span>' not in markup
    assert "RETRIEVER" not in markup
    assert "\n        <" not in markup


def test_comparison_card_has_fixed_height_and_internal_vertical_scroll():
    assert "height: 560px;" in CUSTOM_CSS
    assert "width: calc(100% - 32px);" in CUSTOM_CSS
    assert "margin-inline: auto;" in CUSTOM_CSS
    assert ".panel-scroll {" in CUSTOM_CSS
    assert "overflow-y: auto;" in CUSTOM_CSS


def test_scroll_focus_highlight_uses_a_reserved_border():
    assert "border: 1px solid transparent;" in CUSTOM_CSS
    assert ".panel-scroll:focus" in CUSTOM_CSS
    assert "outline: none;" in CUSTOM_CSS
    assert "border-color: var(--sg-primary);" in CUSTOM_CSS


def test_running_result_keeps_thinking_message_inside_panel():
    markup = Component._build_result_body(
        Component.CONFIGURATIONS[0],
        "What is Intel's main business?",
        {"status": "running"},
    )

    assert 'class="panel-result panel-result-running"' in markup
    assert "<strong>Thinking</strong>" in markup
    assert "Running Vector-only RAG against the selected corpus…" in markup
    assert 'class="panel-scroll chat-history"' in markup
    assert '<span class="thinking-mark" aria-label="Thinking">' in markup
    assert "<i></i><i></i><i></i>" in markup


def test_thinking_motion_has_live_dots_and_reduced_motion_fallback():
    assert "@keyframes thinking-dot" in CUSTOM_CSS
    assert "animation: thinking-dot 1.1s ease-in-out infinite;" in CUSTOM_CSS
    assert "@keyframes panel-enter" in CUSTOM_CSS
    assert "prefers-reduced-motion: reduce" in CUSTOM_CSS


def test_running_result_renders_live_trace_and_current_step():
    markup = Component._build_result_body(
        Component.CONFIGURATIONS[0],
        "What is Intel's main business?",
        {
            "status": "running",
            "trace": [
                {
                    "stage": "config",
                    "message": "Loaded the selected corpus configuration",
                },
                {
                    "stage": "retrieval",
                    "status": "running",
                    "message": "Searching evidence with vector retrieval",
                    "details": {"vector_index": "gold_chunk_embedding"},
                },
            ],
        },
    )

    assert "LIVE TRACE · 2 STEPS" in markup
    assert "CURRENT STEP" in markup
    assert "Searching evidence with vector retrieval" in markup
    assert 'class="thinking-trace-row is-active"' in markup
    assert '<details class="thinking-step-details">' in markup
    assert "gold_chunk_embedding" in markup


def test_chat_history_keeps_latest_exchange_at_bottom():
    previous_result = {
        "status": "complete",
        "answer": "Earlier answer",
        "citations": [],
        "trace": [],
        "latency_sec": 0.5,
    }
    current_result = {
        "status": "complete",
        "answer": "Latest answer",
        "citations": [],
        "trace": [],
        "latency_sec": 0.8,
    }

    markup = Component._build_live_result_body(
        Component.CONFIGURATIONS[0],
        "Latest prompt",
        current_result,
        [{"query": "Earlier prompt", "result": previous_result}],
    )

    assert markup.index("Latest prompt") < markup.index("Earlier prompt")
    assert "flex-direction: column-reverse;" in CUSTOM_CSS
    assert ".user-message-row" in CUSTOM_CSS
    assert "justify-content: flex-end;" in CUSTOM_CSS
    assert ".assistant-message-row" in CUSTOM_CSS
    assert "justify-content: flex-start;" in CUSTOM_CSS


def test_prompt_bubble_has_separate_modern_active_accent():
    assert "border-radius: var(--sg-radius-md);" in CUSTOM_CSS
    assert ".user-message-row" in CUSTOM_CSS
    assert "padding-right: 8px;" in CUSTOM_CSS
    assert ".user-message::after" in CUSTOM_CSS
    assert "right: -7px;" in CUSTOM_CSS
    assert "background: var(--sg-primary);" in CUSTOM_CSS


def test_graph_panel_renders_connected_result():
    result = {
        "status": "complete",
        "answer": "Graph-grounded answer",
        "citations": [{"ticker": "INTC", "chunk_id": "graph-1"}],
        "trace": [{"stage": "retrieval", "retriever": "graph"}],
        "latency_sec": 2.4,
    }

    markup = Component._build_comparison_card(
        Component.CONFIGURATIONS[1],
        "How does Intel use its graph?",
        result,
    )

    assert "Graph-only RAG" in markup
    assert "COMPLETE" in markup
    assert "Graph-grounded answer" in markup
    assert "Backend runner not connected" not in markup


def test_completed_trace_exposes_json_event_details():
    result = {
        "status": "complete",
        "answer": "Grounded answer",
        "citations": [],
        "trace": [{
            "stage": "seed_selection",
            "message": "Selected 2 graph seeds",
            "details": {
                "seed_count": 2,
                "seeds": ["Intel", "Revenue"],
            },
        }],
        "latency_sec": 1.0,
    }

    markup = Component._build_live_result_body(
        Component.CONFIGURATIONS[1],
        "Question",
        result,
    )

    assert '<details class="trace-payload">' in markup
    assert "Selected 2 graph seeds" in markup
    assert "seed_count" in markup
    assert "Intel" in markup
    assert ".trace-payload pre" in CUSTOM_CSS
