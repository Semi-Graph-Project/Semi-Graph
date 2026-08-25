import html
import json
from textwrap import dedent

from markdown_it import MarkdownIt
import streamlit as st

from semigraph.demo import get_backend_corpora


PAGE_CONFIG = {
    "page_title": "SemiGraph — Four-Way Comparison",
    "page_icon": "⚡",
    "layout": "wide",
}


BACKEND_CORPORA = get_backend_corpora()


CONFIGURATIONS = (
    {
        "key": "vector",
        "number": "01",
        "name": "Vector-only RAG",
        "mode": "VECTOR · AGENT OFF",
    },
    {
        "key": "graph",
        "number": "02",
        "name": "Graph-only RAG",
        "mode": "GRAPH · AGENT OFF",
    },
    {
        "key": "agent_vector",
        "number": "03",
        "name": "Agent + Vector",
        "mode": "VECTOR · AGENT ON",
    },
    {
        "key": "agent_graph",
        "number": "04",
        "name": "Agent + Graph",
        "mode": "GRAPH · AGENT ON",
        "featured": True,
    },
)


def configure_page():
    """Configure the Streamlit page before any UI is rendered."""
    st.set_page_config(**PAGE_CONFIG)


def render_topbar():
    """Render the comparison workspace header."""
    st.markdown(
        """
        <header class="topbar">
            <div>
                <div class="eyebrow">SEMIGRAPH · EVALUATION DEMO</div>
                <div class="topbar-title">Four-way comparison</div>
            </div>
            <div class="topbar-actions">
                <span class="mode-badge"><span class="mode-dot"></span> VECTOR · GRAPH LIVE</span>
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_comparison_workspace(
    query=None,
    live_results=None,
    *,
    histories=None,
    corpus=None,
    container=None,
):
    """Render the shared controls and four independently inspectable panels."""
    corpus = corpus or render_backend_corpus_selector()
    if st.session_state.pop("backend_corpus_changed", False):
        query = None
        live_results = {}
        histories = {}
    live_results = live_results or {}
    histories = histories or {}
    cards = "".join(
        _build_comparison_card(
            config,
            query,
            live_results.get(config["key"]),
            histories.get(config["key"], []),
        )
        for config in CONFIGURATIONS
    )
    connected_results = [
        live_results.get(key)
        for key in ("vector", "graph")
        if live_results.get(key)
    ]
    connected_statuses = {
        result.get("status")
        for result in connected_results
    }
    if "running" in connected_statuses:
        run_label = "RUNNING"
        run_class = "run-running"
    elif "error" in connected_statuses:
        run_label = "RUN ERROR"
        run_class = "run-error"
    elif connected_statuses and connected_statuses.issubset({"complete"}):
        run_label = "RUN COMPLETE"
        run_class = "run-complete"
    else:
        run_label = "READY FOR QUERY"
        run_class = "run-waiting"
    intro = _markup(
        f"""
        <section class="comparison-intro">
            <div class="comparison-intro-copy">
                <div class="hero-badge">CONTROLLED 2 × 2 ABLATION</div>
                <h1>One question. <span>Four configurations.</span></h1>
                <p>
                    Compare what changes when Graph Retrieval and Agent Control
                    are introduced while the generation conditions stay fixed.
                </p>
            </div>
            <div class="run-summary {run_class}">
                <span class="run-summary-dot"></span>
                <div>
                    <small>COMPARISON RUN</small>
                    <strong>{run_label}</strong>
                </div>
                <span class="run-count">4 PANELS</span>
            </div>
        </section>
        """
    )
    controls = _markup(
        f"""
        <section class="shared-controls" aria-label="Shared comparison controls">
            <div class="shared-controls-title">
                <span>CONTROLLED VARIABLES</span>
                <small>Held constant for a fair comparison</small>
            </div>
            <div><small>QUESTION</small><strong>Shared</strong></div>
            <div><small>CORPUS</small><strong>{html.escape(corpus.label)}</strong></div>
            <div><small>LLM + PROMPT</small><strong>Shared</strong></div>
            <div><small>EVIDENCE BUDGET</small><strong>Shared</strong></div>
        </section>
        """
    )
    heading = _markup(
        """
        <section class="comparison-section-heading">
            <div>
                <div class="eyebrow">CONFIGURATION OUTPUTS</div>
                <h2>Comparison matrix</h2>
            </div>
            <p>Each panel reports its own status, answer, citations, and trace.</p>
        </section>
        """
    )
    markup = (
        '<main class="comparison-workspace">'
        f"{intro}{controls}{heading}"
        f'<section class="comparison-grid">{cards}</section>'
        '<div class="composer-hint">'
        "SUBMIT A NEW QUESTION TO START A NEW COMPARISON RUN"
        "</div></main>"
    )
    target = container if container is not None else st
    target.markdown(markup, unsafe_allow_html=True)
    return corpus


def render_backend_corpus_selector():
    """Render the shared backend selector used by all four configurations."""
    labels = [corpus.label for corpus in BACKEND_CORPORA]
    selected_label = st.selectbox(
        "Backend Corpus",
        labels,
        index=0,
        key="backend_corpus",
        label_visibility="collapsed",
    )
    selected = next(
        corpus for corpus in BACKEND_CORPORA if corpus.label == selected_label
    )
    previous_key = st.session_state.get("backend_corpus_key")
    if previous_key is not None and previous_key != selected.key:
        st.session_state["comparison_query"] = None
        st.session_state["vector_result"] = None
        st.session_state["vector_pending_query"] = None
        st.session_state["graph_result"] = None
        st.session_state["graph_pending_query"] = None
        st.session_state["comparison_history"] = {
            config["key"]: [] for config in CONFIGURATIONS
        }
        st.session_state["backend_corpus_changed"] = True
    st.session_state["backend_corpus_key"] = selected.key
    return selected


def render_comparison_input():
    """Render the single question shared by all four configurations."""
    return st.chat_input("Ask one question to compare all four configurations…")


def _build_comparison_card(configuration, query, result=None, history=None):
    featured = configuration.get("featured", False)
    card_class = "comparison-card featured-card" if featured else "comparison-card"
    featured_badge = (
        '<span class="thesis-badge">THESIS SYSTEM</span>'
        if featured
        else "<!-- standard configuration -->"
    )
    result_status = result.get("status") if result else None
    if result_status == "running":
        status_label = "RUNNING"
        status_class = "status-running"
    elif result_status == "complete":
        status_label = "COMPLETE"
        status_class = "status-complete"
    elif result is not None:
        status_label = "ERROR"
        status_class = "status-error"
    elif query:
        status_label = "NOT CONNECTED"
        status_class = "status-waiting"
    else:
        status_label = "WAITING"
        status_class = "status-waiting"
    body = _build_result_body(configuration, query, result, history)

    header = _markup(
        f"""
        <div class="card-accent"></div>
        <header class="card-header">
            <div class="card-title-row">
                <span class="config-number">{configuration['number']}</span>
                <div>
                    <div class="config-mode">{configuration['mode']}</div>
                    <h3>{configuration['name']}</h3>
                </div>
            </div>
            <div class="card-status-group">
                {featured_badge}
                <span class="panel-status {status_class}">
                    <i></i>{status_label}
                </span>
            </div>
        </header>
        """
    )
    return f'<article class="{card_class}">{header}{body}</article>'


def _build_result_body(configuration, query, result=None, history=None):
    if not query:
        return _markup(
            """
        <div class="panel-empty-state">
            <span class="empty-state-mark">⌁</span>
            <strong>Waiting for the shared question</strong>
            <p>The response, citations, and technical trace will appear here.</p>
        </div>
        <div class="panel-footer panel-footer-waiting">
            <span>ANSWER FORMAT · SHARED</span>
            <span>NO RUN YET</span>
        </div>
        """
        )

    if result is not None and result.get("status") == "running":
        return _build_running_body(configuration, query, result, history)
    if result is None:
        return _build_unconnected_body(configuration, query, history)
    return _build_live_result_body(configuration, query, result, history)


def _build_running_body(configuration, query, result=None, history=None):
    """Render an in-card status while this panel's runner is working."""
    mode_label = html.escape(configuration["name"])
    trace = [
        event
        for event in (result or {}).get("trace", [])
        if isinstance(event, dict)
    ]
    current_event = trace[-1] if trace else {
        "stage": "runner",
        "status": "running",
        "message": "Starting the retrieval pipeline",
    }
    current_message = html.escape(
        str(current_event.get("message") or _trace_label(current_event))
    )
    trace_rows = []
    for index, event in enumerate(trace, start=1):
        active_class = " is-active" if index == len(trace) else ""
        stage = html.escape(str(event.get("stage") or "TRACE").upper())
        message = html.escape(
            str(event.get("message") or _trace_label(event))
        )
        details = event.get("details")
        details_markup = ""
        if details:
            payload = html.escape(
                json.dumps(details, ensure_ascii=False, indent=2, default=str)
            )
            details_markup = (
                '<details class="thinking-step-details">'
                "<summary>VIEW JSON</summary>"
                f"<pre>{payload}</pre>"
                "</details>"
            )
        trace_rows.append(
            f'<div class="thinking-trace-row{active_class}">'
            f'<span class="thinking-step-index">{index:02d}</span>'
            '<span class="thinking-step-dot"></span>'
            '<div class="thinking-step-copy">'
            f"<b>{stage}</b><small>{message}</small>{details_markup}"
            "</div></div>"
        )
    if not trace_rows:
        trace_rows.append(
            '<div class="thinking-trace-row is-active">'
            '<span class="thinking-step-index">01</span>'
            '<span class="thinking-step-dot"></span>'
            '<div class="thinking-step-copy">'
            "<b>RUNNER</b><small>Starting the retrieval pipeline</small>"
            "</div></div>"
        )
    thinking_message = "".join(
        (
            '<div class="chat-message-row assistant-message-row">',
            '<section class="chat-turn answer-turn chat-message '
            'assistant-message thinking-message">',
            '<div class="thinking-state">',
            '<div class="thinking-heading">',
            '<span class="thinking-mark" aria-label="Thinking">'
            '<i></i><i></i><i></i></span>',
            '<div><strong>Thinking</strong>',
            f'<small>LIVE TRACE · {len(trace) or 1} STEPS</small></div>',
            '</div>',
            '<div class="thinking-current">',
            '<span>CURRENT STEP</span>',
            f'<p>{current_message}</p>',
            '</div>',
            '<div class="thinking-trace" aria-label="Live RAG trace">',
            "".join(trace_rows),
            '</div>',
            f'<p class="thinking-caption">Running {mode_label} against the selected corpus…</p>',
            '</div></section></div>',
        )
    )
    exchanges = "".join(
        (
            '<div class="chat-exchange current-exchange">',
            _build_user_message(query),
            thinking_message,
            '</div>',
            _build_history_exchanges(configuration, history),
        )
    )
    return "".join(
        (
            '<div class="panel-result panel-result-running">',
            '<div class="result-toolbar">',
            "<span>RUNNER STATUS</span>",
            "<small>IN PROGRESS</small>",
            "</div>",
            '<div class="panel-scroll chat-history" tabindex="0" '
            f'aria-label="{mode_label} chat history">',
            exchanges,
            "</div>",
            '<div class="panel-footer">',
            "<span>RUNNING</span>",
            f"<span>{html.escape(configuration['mode'])}</span>",
            "</div>",
            "</div>",
        )
    )


def _build_unconnected_body(configuration, query, history=None):
    mode_label = html.escape(configuration["name"])
    notice = "".join(
        (
            '<div class="chat-message-row assistant-message-row">',
            '<section class="chat-turn answer-turn chat-message assistant-message">',
            '<span class="turn-label">ANSWER</span>',
            '<div class="connection-notice">',
            '<strong>Backend runner not connected</strong>',
            '<p>This configuration will be connected in the next step.</p>',
            '</div></section></div>',
        )
    )
    exchanges = "".join(
        (
            '<div class="chat-exchange current-exchange">',
            _build_user_message(query),
            notice,
            '</div>',
            _build_history_exchanges(configuration, history),
        )
    )
    return "".join(
        (
            '<div class="panel-result panel-result-unconnected">',
            '<div class="result-toolbar">',
            '<span>CHAT HISTORY</span><small>RUNNER NOT CONNECTED</small>',
            '</div>',
            '<div class="panel-scroll chat-history" tabindex="0" '
            f'aria-label="{mode_label} chat history">',
            exchanges,
            '</div>',
            '<div class="panel-footer panel-footer-waiting">',
            '<span>RUNNER · PENDING</span><span>NOT CONNECTED</span>',
            '</div></div>',
        )
    )


def _build_completed_exchange(configuration, query, result, is_current=True):
    answer = str(result.get("answer") or "No answer returned.")
    answer_html = _render_answer_markdown(answer)
    citations = list(result.get("citations") or [])
    trace = list(result.get("trace") or [])
    status = str(result.get("status") or "error")
    error = result.get("error")
    citation_rows = "".join(
        (
            f'<div class="citation-item"><b>[C{index}]</b>'
            f'<span>{html.escape(_citation_label(citation))}</span></div>'
        )
        for index, citation in enumerate(citations, start=1)
    )
    if not citation_rows:
        citation_rows = (
            '<div class="citation-item citation-empty">'
            "<span>No evidence citation returned.</span></div>"
        )
    trace_rows = "".join(
        _build_trace_row(index, event)
        for index, event in enumerate(trace, start=1)
        if isinstance(event, dict)
    )
    if not trace_rows:
        trace_rows = (
            '<div class="trace-row trace-empty">'
            "<span>00</span><b>TRACE</b><code>No trace returned.</code></div>"
        )
    error_block = ""
    if status != "complete" or error:
        error_block = (
            '<div class="runner-error" role="alert">'
            "<strong>Runner error</strong>"
            f"<p>{html.escape(str(error or 'Unknown error'))}</p></div>"
        )
    mode_label = html.escape(configuration["name"].upper())
    result_label = (
        "LIVE" if is_current and status == "complete"
        else "HISTORY" if status == "complete"
        else "FAILED"
    )
    exchange_class = "chat-exchange current-exchange" if is_current else "chat-exchange"

    # Keep the outer HTML flush-left. Indented dynamic fragments can otherwise
    # be parsed by Streamlit Markdown as a code block instead of real HTML.
    return "".join(
        (
            f'<div class="{exchange_class}">',
            _build_user_message(query),
            '<div class="chat-message-row assistant-message-row">',
            '<section class="chat-turn answer-turn chat-message assistant-message">',
            '<div class="answer-label-row">',
            '<span class="turn-label">ANSWER</span>',
            f'<span class="live-label">{mode_label} · {result_label}</span>',
            "</div>",
            f'<div class="answer-markdown">{answer_html}</div>',
            error_block,
            '<details class="result-disclosure citation-details">',
            "<summary><span>CITATIONS</span>",
            f"<small>{len(citations)} SOURCES</small></summary>",
            f'<div class="citation-list">{citation_rows}</div>',
            "</details>",
            '<details class="result-disclosure trace-details">',
            "<summary><span>TECHNICAL TRACE</span>",
            f"<small>{len(trace)} STEPS</small></summary>",
            f'<div class="trace-table">{trace_rows}</div>',
            "</details>",
            "</section></div></div>",
        )
    )


def _build_live_result_body(configuration, query, result, history=None):
    latency = result.get("latency_sec")
    latency_label = f"{float(latency):.1f}s" if latency is not None else "n/a"
    mode_label = html.escape(configuration["name"].upper())
    scroll_label = html.escape(f"{configuration['name']} chat history")
    exchanges = "".join(
        (
            _build_completed_exchange(configuration, query, result),
            _build_history_exchanges(configuration, history),
        )
    )
    return "".join(
        (
            '<div class="panel-result">',
            '<div class="result-toolbar">',
            '<span>CHAT HISTORY</span><small>SCROLL FOR EARLIER MESSAGES</small>',
            '</div>',
            '<div class="panel-scroll chat-history" tabindex="0" '
            f'aria-label="{scroll_label}">',
            exchanges,
            '</div>',
            '<div class="panel-footer">',
            f'<span>LIVE RESULT · {latency_label}</span>',
            f'<span>{mode_label}</span>',
            '</div></div>',
        )
    )


def _build_user_message(query):
    safe_query = html.escape(str(query))
    return "".join(
        (
            '<div class="chat-message-row user-message-row">',
            '<section class="chat-turn user-turn chat-message user-message">',
            f'<p>{safe_query}</p>',
            '</section></div>',
        )
    )


def _build_history_exchanges(configuration, history=None):
    exchanges = []
    for item in reversed(list(history or [])):
        if not isinstance(item, dict):
            continue
        past_query = item.get("query")
        past_result = item.get("result")
        if not past_query or not isinstance(past_result, dict):
            continue
        exchanges.append(
            _build_completed_exchange(
                configuration,
                past_query,
                past_result,
                is_current=False,
            )
        )
    return "".join(exchanges)


def _citation_label(citation):
    source = citation.get("ticker") or citation.get("source_kind") or "Evidence"
    chunk_id = citation.get("chunk_id") or "unknown chunk"
    section = citation.get("section")
    suffix = f" · {section}" if section else ""
    return f"{source} · {chunk_id}{suffix}"


def _trace_label(event):
    if event.get("message"):
        return str(event["message"])
    parts = []
    for key in ("retriever", "tool", "status", "retrieval_status", "corpus"):
        value = event.get(key)
        if value not in (None, ""):
            parts.append(f"{key}={value}")
    if event.get("llm_calls") is not None:
        parts.append(f"llm_calls={event['llm_calls']}")
    if event.get("latency_sec") is not None:
        parts.append(f"latency={event['latency_sec']}s")
    if event.get("error_type"):
        parts.append(f"error={event['error_type']}")
    return " · ".join(parts) or "completed"


def _build_trace_row(index, event):
    stage = html.escape(str(event.get("stage") or "TRACE").upper())
    label = html.escape(_trace_label(event))
    details = event.get("details")
    if details:
        payload = html.escape(
            json.dumps(details, ensure_ascii=False, indent=2, default=str)
        )
        content = (
            '<details class="trace-payload">'
            f"<summary>{label}</summary>"
            f"<pre>{payload}</pre>"
            "</details>"
        )
    else:
        content = f"<code>{label}</code>"
    return (
        '<div class="trace-row">'
        f"<span>{index:02d}</span>"
        f"<b>{stage}</b>"
        f"{content}"
        "</div>"
    )


def _markup(value):
    """Remove Python indentation so Streamlit treats the value as raw HTML."""
    return dedent(value).strip()


def _render_answer_markdown(answer):
    """Render model Markdown safely before placing it inside the answer card."""
    renderer = MarkdownIt("commonmark", {"html": False, "breaks": True})
    return renderer.render(answer)
