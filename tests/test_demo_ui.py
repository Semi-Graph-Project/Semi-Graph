import re
from pathlib import Path

from Demo import Component
from Demo.Style import CUSTOM_CSS


def test_panel_keys_cover_all_four_comparison_modes():
    assert Component.PANEL_KEYS == (
        "vector",
        "graph",
        "agent_vector",
        "agent_graph",
    )
    assert tuple(
        configuration["key"]
        for configuration in Component.CONFIGURATIONS
    ) == Component.PANEL_KEYS


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

    assert markup.startswith(
        '<div class="panel-result panel-result-settled">'
    )
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


def test_first_exchange_starts_at_top_without_changing_history_order():
    result = {
        "status": "complete",
        "answer": "Answer",
        "citations": [],
        "trace": [],
        "latency_sec": 1.0,
    }
    markup = Component._build_live_result_body(
        Component.CONFIGURATIONS[0],
        "First question",
        result,
    )

    assert 'class="panel-scroll chat-history" tabindex="0"' in markup
    assert "flex-direction: column;" in CUSTOM_CSS
    assert "flex-direction: column-reverse;" not in CUSTOM_CSS


def test_comparison_card_uses_viewport_height_and_internal_vertical_scroll():
    assert "height: clamp(560px, calc(100vh - 170px), 720px);" in CUSTOM_CSS
    assert "max-width: 1680px;" in CUSTOM_CSS
    assert "gap: 20px;" in CUSTOM_CSS
    assert "width: calc(100% - 32px);" in CUSTOM_CSS
    assert "margin-inline: auto;" in CUSTOM_CSS
    assert ".panel-scroll {" in CUSTOM_CSS
    assert "overflow-y: auto;" in CUSTOM_CSS

    panel_result_css = CUSTOM_CSS.split(
        ".panel-result {", 1
    )[1].split("}", 1)[0]
    panel_scroll_css = CUSTOM_CSS.split(
        ".panel-scroll {", 1
    )[1].split("}", 1)[0]
    assert "height: 0;" in panel_result_css
    assert "height: 0;" in panel_scroll_css
    assert "max-height: 100%;" in panel_scroll_css


def test_workspace_keeps_only_the_comparison_chats():
    component_source = (
        Path(__file__).resolve().parents[1] / "Demo" / "Component.py"
    ).read_text(encoding="utf-8")

    assert "CONTROLLED 2 × 2 ABLATION" not in component_source
    assert "CONTROLLED VARIABLES" not in component_source
    assert "Comparison matrix" not in component_source
    assert "SUBMIT A NEW QUESTION TO START A NEW COMPARISON RUN" not in component_source
    assert 'aria-label="Comparison chats"' in component_source


def test_settled_result_does_not_replay_entry_animation():
    panel_base = CUSTOM_CSS.split(".panel-result {", 1)[1].split("}", 1)[0]

    assert "animation:" not in panel_base
    assert ".panel-result-running {" in CUSTOM_CSS
    assert "animation: panel-enter 360ms ease-out both;" in CUSTOM_CSS


def test_runner_publishes_completion_without_final_page_rerun():
    runner_source = (
        Path(__file__).resolve().parents[1] / "Demo" / "Mock_Result.py"
    ).read_text(encoding="utf-8")

    assert "st.rerun()" not in runner_source
    assert "running_results = {}" in runner_source
    assert "published_results = set()" in runner_source
    assert "if trace_updated or result_updated:" in runner_source
    assert "final_results = {}" in runner_source


def test_streamlit_rerun_does_not_fade_existing_content():
    assert '[data-stale="true"] {' in CUSTOM_CSS
    assert "opacity: 1 !important;" in CUSTOM_CSS


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
    assert 'class="trace-event-row trace-status-running is-active"' in markup
    assert 'class="trace-detail-trigger"' in markup
    assert 'class="trace-detail-modal" popover="auto"' in markup
    assert '<details class="trace-detail-panel">' not in markup
    assert "Vector index" in markup
    assert "RAW EVENT" in markup
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

    assert markup.index("Earlier prompt") < markup.index("Latest prompt")
    assert "flex-direction: column;" in CUSTOM_CSS
    assert "flex-direction: column-reverse;" not in CUSTOM_CSS
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


def test_graph_trace_keeps_only_the_four_readable_stages():
    result = {
        "status": "complete",
        "answer": "Graph-grounded answer",
        "citations": [],
        "trace": [
            {"stage": "config", "corpus": "benchmark"},
            {"stage": "query_expansion", "message": "Expand query"},
            {
                "stage": "seed_selection",
                "status": "complete",
                "message": "Selected 2 graph seeds",
                "details": {
                    "seed_mode": "triple",
                    "top_k_triples": 2,
                    "triple_candidates": [
                        {
                            "candidate_id": 0,
                            "head": "Intel",
                            "relation": "PRODUCES",
                            "tail": "Xeon",
                            "similarity": 0.912,
                        },
                        {
                            "candidate_id": 1,
                            "head": "Intel",
                            "relation": "OPERATES",
                            "tail": "Foundry",
                            "similarity": 0.874,
                        },
                    ],
                },
            },
            {
                "stage": "personalized_pagerank",
                "status": "complete",
                "message": "Ranked graph entities",
                "details": {
                    "graph_mode": "entity_only",
                    "seed_weight_mode": "similarity_specificity",
                    "damping": 0.5,
                },
            },
            {"stage": "alias_clustering", "message": "Group aliases"},
            {
                "stage": "retrieval_complete",
                "status": "complete",
                "message": "Graph retrieval completed",
                "details": {
                    "returned_chunk_ids": ["chunk-1", "chunk-2"],
                },
            },
            {"stage": "synthesis", "status": "complete", "message": "Done"},
        ],
        "latency_sec": 1.0,
    }

    markup = Component._build_live_result_body(
        Component.CONFIGURATIONS[1],
        "Question",
        result,
    )

    assert "Graph seed selection" in markup
    assert "PPR" in markup
    assert "Retrieve Complete" in markup
    assert "Synthesize" in markup
    assert "Query expansion" not in markup
    assert "Alias grouping" not in markup
    assert "Evidence mapping" not in markup
    assert "Evidence reranking" not in markup
    assert "Seed Mode" in markup
    assert "Top-K Triple" in markup
    assert "(Intel)" in markup
    assert "-[PRODUCES]-&gt;" in markup
    assert "[0.912]" in markup
    assert "Seed Weight" in markup
    assert "Chunk Count" in markup
    assert "chunk-1, chunk-2" in markup


def test_agent_graph_trace_rebuilds_graph_stages_from_compact_retrieval():
    result = {
        "status": "complete",
        "answer": "Agent graph answer",
        "citations": [],
        "trace": [
            {
                "stage": "retrieval",
                "tool": "graph",
                "retrieval_status": "ok",
                "parameters": {
                    "seed_mode": "triple",
                    "top_k_triples": 1,
                    "ppr_graph_mode": "entity_only",
                    "ppr_seed_weight_mode": "uniform",
                    "damping": 0.5,
                },
                "seed_count": 1,
                "triple_candidates": [{
                    "head": "AMD",
                    "relation": "USES",
                    "tail": "HBM",
                    "similarity": 0.91,
                }],
                "returned_chunk_ids": ["agent-graph-1"],
            },
            {"stage": "synthesis", "status": "complete"},
        ],
    }

    markup = Component._build_live_result_body(
        Component.CONFIGURATIONS[3],
        "Question",
        result,
    )

    assert markup.count('class="trace-event-row') == 4
    assert "Graph seed selection" in markup
    assert "PPR" in markup
    assert "Retrieve Complete" in markup
    assert "Synthesize" in markup
    assert "(AMD)" in markup
    assert "agent-graph-1" in markup


def test_completed_trace_uses_readable_details_before_raw_json():
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

    assert "Graph seed selection" in markup
    assert 'class="trace-detail-trigger"' in markup
    assert 'class="trace-detail-modal" popover="auto"' in markup
    assert '<details class="trace-detail-panel">' not in markup
    assert '<dl class="trace-detail-grid">' in markup
    assert "Seed Mode" in markup
    assert "Top-K Triple" in markup
    assert "VIEW DETAILS" in markup
    assert "RAW EVENT" in markup
    assert '<div class="trace-modal-footer">' in markup
    assert "Selected 2 graph seeds" in markup
    assert "seed_count" in markup
    assert "Intel" in markup
    assert ".trace-raw-json pre" in CUSTOM_CSS


def test_plan_tasks_render_as_separate_markdown_lines_in_trace_modal():
    markup = Component._build_trace_row(
        1,
        {
            "stage": "plan",
            "status": "complete",
            "message": "Created 2 retrieval tasks",
            "details": {
                "tasks": [
                    "T1: Find Intel product evidence",
                    "T2: Find AMD competition evidence",
                ],
            },
        },
    )

    assert "Task plan" in markup
    assert (
        "- T1: Find Intel product evidence\n"
        "- T2: Find AMD competition evidence"
    ) in markup
    assert "white-space: pre-line;" in CUSTOM_CSS


def test_trace_modal_targets_stay_unique_across_chat_history():
    result = {
        "status": "complete",
        "answer": "Answer",
        "citations": [],
        "trace": [{"stage": "plan", "status": "complete"}],
    }

    markup = Component._build_live_result_body(
        Component.CONFIGURATIONS[0],
        "Current question",
        result,
        [{"query": "Earlier question", "result": result}],
    )

    modal_ids = re.findall(r'<section id="(trace-detail-[^"]+)"', markup)
    targets = re.findall(r'popovertarget="(trace-detail-[^"]+)"', markup)

    assert len(modal_ids) == 2
    assert len(modal_ids) == len(set(modal_ids))
    assert set(targets) == set(modal_ids)
    assert all(targets.count(modal_id) == 2 for modal_id in modal_ids)


def test_citations_and_trace_use_readable_contrast_and_type():
    assert "background: #202020;" in CUSTOM_CSS
    assert "font-size: 11px;" in CUSTOM_CSS
    assert "font-size: 12px;" in CUSTOM_CSS
    assert "background: #2a2a2a;" in CUSTOM_CSS
    assert "border: 1px solid #484848;" in CUSTOM_CSS
    assert "font-size: 14px;" in CUSTOM_CSS
    assert "font-weight: 700;" in CUSTOM_CSS
    assert "font-weight: 600;" in CUSTOM_CSS


def test_trace_timeline_collapses_adjacent_stage_transitions():
    events = [
        {
            "stage": "vector_candidates",
            "status": "running",
            "message": "Searching the vector index",
            "timestamp": "2026-08-25T00:00:00+00:00",
            "details": {
                "vector_index": "gold_chunk_embedding",
                "candidate_pool_k": 100,
            },
        },
        {
            "stage": "vector_candidates",
            "status": "complete",
            "message": "Retrieved 20 vector candidates",
            "timestamp": "2026-08-25T00:00:01.400000+00:00",
            "details": {"candidate_count": 20},
        },
    ]

    groups = Component._group_trace_events(events)
    markup = Component._build_trace_row(
        1,
        groups[0]["event"],
        raw_events=groups[0]["raw_events"],
    )

    assert len(groups) == 1
    assert groups[0]["event"]["details"] == {
        "vector_index": "gold_chunk_embedding",
        "candidate_pool_k": 100,
        "candidate_count": 20,
    }
    assert "Vector search" in markup
    assert "COMPLETE" in markup
    assert "1.4s" in markup
    assert "Candidate budget" in markup
    assert "Candidates" in markup
    assert "RAW EVENT" in markup


def test_agent_trace_keeps_parallel_tasks_separate_and_shows_retry_query():
    events = [
        {
            "stage": "execute",
            "status": "running",
            "task_id": "T1",
            "attempt_id": "T1-A1",
            "message": "T1-A1 searching with graph",
        },
        {
            "stage": "execute",
            "status": "running",
            "task_id": "T2",
            "attempt_id": "T2-A1",
            "message": "T2-A1 searching with graph",
        },
        {
            "stage": "execute",
            "status": "complete",
            "task_id": "T1",
            "attempt_id": "T1-A1",
            "message": "T1-A1 retrieved 2 evidence chunk(s)",
            "details": {"chunk_count": 2},
        },
        {
            "stage": "retry",
            "status": "complete",
            "task_id": "T2",
            "attempt_id": "T2-A1",
            "message": "Rewrote T2 query: focused retry query",
            "details": {
                "strategy": "focus_missing",
                "retry_query": "focused retry query",
            },
        },
    ]

    groups = Component._trace_groups_for_configuration(
        {"key": "agent_graph"},
        events,
    )
    markup = "".join(
        Component._build_trace_row(
            index,
            group["event"],
            raw_events=group["raw_events"],
        )
        for index, group in enumerate(groups, start=1)
    )

    assert len(groups) == 3
    assert len(groups[0]["raw_events"]) == 2
    assert groups[0]["event"]["task_id"] == "T1"
    assert groups[1]["event"]["task_id"] == "T2"
    assert "focused retry query" in markup
    assert "Retry strategy" in markup
