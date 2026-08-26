import html
import json
from datetime import datetime
from textwrap import dedent

from markdown_it import MarkdownIt
import streamlit as st

from semigraph.demo import COMPARISON_MODES, get_backend_corpora


PAGE_CONFIG = {
    "page_title": "SemiGraph — Four-Way Comparison",
    "page_icon": "⚡",
    "layout": "wide",
}


BACKEND_CORPORA = get_backend_corpora()


TRACE_STAGE_LABELS = {
    "config": "Configuration",
    "plan": "Retrieval planning",
    "retrieval": "Evidence search",
    "query_expansion": "Query expansion",
    "seed_selection": "Graph seed selection",
    "personalized_pagerank": "Personalized PageRank",
    "alias_clustering": "Alias grouping",
    "chunk_mapping": "Evidence mapping",
    "vector_candidates": "Vector search",
    "reranking": "Evidence reranking",
    "retrieval_complete": "Retrieval complete",
    "retrieval_summary": "Retrieval summary",
    "synthesis": "Answer synthesis",
    "runner": "Runner",
}


TRACE_FIELD_LABELS = {
    "corpus": "Corpus",
    "retriever": "Retriever",
    "tool": "Tool",
    "vector_index": "Vector index",
    "candidate_pool_k": "Candidate budget",
    "candidate_count": "Candidates",
    "returned_chunk_ids": "Selected chunks",
    "candidate_chunk_ids": "Candidate chunks",
    "seed_mode": "Seed mode",
    "seed_count": "Graph seeds",
    "seed_weight_mode": "Seed weighting",
    "top_k_triples": "Triple budget",
    "top_k_chunk_seeds": "Chunk-seed budget",
    "graph_mode": "Graph mode",
    "damping": "PPR damping",
    "entity_count": "Ranked entities",
    "cluster_count": "Alias clusters",
    "mode": "Mode",
    "llm_calls": "LLM calls",
    "latency_sec": "Duration",
    "error_type": "Error type",
    "abort_reason": "Stop reason",
}


TRACE_FIELD_PRIORITY = tuple(TRACE_FIELD_LABELS)


GRAPH_TRACE_STAGES = (
    "seed_selection",
    "personalized_pagerank",
    "retrieval_complete",
    "synthesis",
)

GRAPH_TRACE_STAGE_LABELS = {
    "seed_selection": "Graph seed selection",
    "personalized_pagerank": "PPR",
    "retrieval_complete": "Retrieve Complete",
    "synthesis": "Synthesize",
}


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


PANEL_KEYS = COMPARISON_MODES


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
                <span class="mode-badge"><span class="mode-dot"></span> 4 CONFIGS LIVE</span>
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
    """Render the backend selector and four independently inspectable panels."""
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
    markup = (
        '<main class="comparison-workspace">'
        f'<section class="comparison-grid" '
        f'aria-label="Comparison chats">{cards}</section>'
        "</main>"
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
        for panel_key in PANEL_KEYS:
            st.session_state[f"{panel_key}_result"] = None
            st.session_state[f"{panel_key}_pending_query"] = None
        st.session_state["comparison_history"] = {
            panel_key: [] for panel_key in PANEL_KEYS
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
    graph_trace = _is_graph_configuration(configuration)
    trace_groups = _trace_groups_for_configuration(configuration, trace)
    current_event = trace_groups[-1]["event"] if trace_groups else {
        "stage": "runner",
        "status": "running",
        "message": "Starting the retrieval pipeline",
    }
    current_message = html.escape(
        str(current_event.get("message") or _trace_label(current_event))
    )
    if trace_groups:
        trace_rows = "".join(
            _build_trace_row(
                index,
                group["event"],
                raw_events=group["raw_events"],
                is_active=index == len(trace_groups),
                graph=graph_trace,
            )
            for index, group in enumerate(trace_groups, start=1)
        )
    else:
        trace_rows = _build_trace_row(
            1,
            current_event,
            is_active=True,
            graph=graph_trace,
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
            f'<small>LIVE TRACE · {len(trace_groups) or 1} STEPS</small></div>',
            '</div>',
            '<div class="thinking-current">',
            '<span>CURRENT STEP</span>',
            f'<p>{current_message}</p>',
            '</div>',
            '<div class="thinking-trace" aria-label="Live RAG trace">',
            trace_rows,
            '</div>',
            f'<p class="thinking-caption">Running {mode_label} against the selected corpus…</p>',
            '</div></section></div>',
        )
    )
    exchanges = "".join(
        (
            _build_history_exchanges(configuration, history),
            '<div class="chat-exchange current-exchange">',
            _build_user_message(query),
            thinking_message,
            '</div>',
        )
    )
    return "".join(
        (
            '<div class="panel-result panel-result-running">',
            '<div class="result-toolbar">',
            "<span>RUNNER STATUS</span>",
            "<small>IN PROGRESS</small>",
            "</div>",
            '<div class="panel-scroll chat-history" '
            'tabindex="0" '
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
            _build_history_exchanges(configuration, history),
            '<div class="chat-exchange current-exchange">',
            _build_user_message(query),
            notice,
            '</div>',
        )
    )
    return "".join(
        (
            '<div class="panel-result panel-result-unconnected">',
            '<div class="result-toolbar">',
            '<span>CHAT HISTORY</span><small>RUNNER NOT CONNECTED</small>',
            '</div>',
            '<div class="panel-scroll chat-history" '
            'tabindex="0" '
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
    graph_trace = _is_graph_configuration(configuration)
    trace_groups = _trace_groups_for_configuration(configuration, trace)
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
        _build_trace_row(
            index,
            group["event"],
            raw_events=group["raw_events"],
            graph=graph_trace,
        )
        for index, group in enumerate(trace_groups, start=1)
    )
    if not trace_rows:
        trace_rows = (
            '<div class="trace-event-row trace-empty">'
            '<span class="trace-event-index">00</span>'
            '<span class="trace-event-dot"></span>'
            '<div class="trace-event-copy"><b>Trace unavailable</b>'
            '<p>No trace returned.</p></div></div>'
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
            f"<small>{len(trace_groups)} STEPS</small></summary>",
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
            _build_history_exchanges(configuration, history),
            _build_completed_exchange(configuration, query, result),
        )
    )
    return "".join(
        (
            '<div class="panel-result panel-result-settled">',
            '<div class="result-toolbar">',
            '<span>CHAT HISTORY</span><small>SCROLL FOR EARLIER MESSAGES</small>',
            '</div>',
            '<div class="panel-scroll chat-history" '
            'tabindex="0" '
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
    for item in history or []:
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


def _group_trace_events(events):
    """Collapse adjacent status updates into one human-readable stage."""
    groups = []
    for raw_event in events:
        if not isinstance(raw_event, dict):
            continue
        event = dict(raw_event)
        stage = str(event.get("stage") or "trace")
        if groups and groups[-1]["stage"] == stage:
            merged = dict(groups[-1]["event"])
            previous_details = merged.get("details")
            current_details = event.get("details")
            merged_details = (
                dict(previous_details)
                if isinstance(previous_details, dict)
                else {}
            )
            if isinstance(current_details, dict):
                merged_details.update(current_details)
            merged.update(event)
            if merged_details:
                merged["details"] = merged_details
            groups[-1]["event"] = merged
            groups[-1]["raw_events"].append(raw_event)
            continue
        groups.append({
            "stage": stage,
            "event": event,
            "raw_events": [raw_event],
        })
    return groups


def _is_graph_configuration(configuration):
    return configuration.get("key") in {"graph", "agent_graph"}


def _is_compact_graph_retrieval(event):
    if event.get("stage") != "retrieval":
        return False
    if not isinstance(event.get("parameters"), dict):
        return False
    return event.get("retriever") == "graph" or event.get("tool") == "graph"


def _graph_completion_status(event):
    raw_status = str(
        event.get("status") or event.get("retrieval_status") or ""
    ).lower()
    if raw_status in {"error", "failed", "provider_error"}:
        return "error"
    if event.get("abort_reason"):
        return "no_evidence"
    return "complete"


def _graph_chunk_ids(event):
    chunk_ids = event.get("returned_chunk_ids") or []
    if not chunk_ids:
        details = event.get("details")
        if isinstance(details, dict):
            chunk_ids = details.get("returned_chunk_ids") or []
    return [str(chunk_id) for chunk_id in chunk_ids]


def _graph_trace_groups_from_compact(event):
    """Rebuild the four Graph stages from an Agent's compact trace."""
    parameters = dict(event.get("parameters") or {})
    triple_filter = dict(event.get("triple_filter") or {})
    triples = list(
        event.get("triple_candidates")
        or triple_filter.get("candidates_before_filter")
        or triple_filter.get("selected_triples")
        or []
    )
    seed_count = int(event.get("seed_count") or 0)
    chunk_ids = _graph_chunk_ids(event)
    status = _graph_completion_status(event)
    return [
        {
            "stage": "seed_selection",
            "event": {
                "stage": "seed_selection",
                "status": status,
                "message": f"Selected {seed_count} graph seeds",
                "details": {
                    "seed_mode": parameters.get("seed_mode"),
                    "top_k_triples": parameters.get("top_k_triples"),
                    "triple_candidates": triples,
                },
            },
            "raw_events": [event],
        },
        {
            "stage": "personalized_pagerank",
            "event": {
                "stage": "personalized_pagerank",
                "status": status,
                "message": "Ranked graph evidence with Personalized PageRank",
                "details": {
                    "graph_mode": parameters.get("ppr_graph_mode"),
                    "seed_weight_mode": parameters.get("ppr_seed_weight_mode"),
                    "damping": parameters.get("damping"),
                },
            },
            "raw_events": [event],
        },
        {
            "stage": "retrieval_complete",
            "event": {
                "stage": "retrieval_complete",
                "status": status,
                "message": f"Retrieved {len(chunk_ids)} evidence chunks",
                "details": {
                    "returned_chunk_ids": chunk_ids,
                    "chunk_count": len(chunk_ids),
                },
            },
            "raw_events": [event],
        },
    ]


def _trace_groups_for_configuration(configuration, events):
    """Select the compact trace contract used by the Graph panels."""
    groups = _group_trace_events(events or [])
    if not _is_graph_configuration(configuration):
        return groups

    stage_groups = {
        group["stage"]: group
        for group in groups
        if group["stage"] in GRAPH_TRACE_STAGES
    }
    compact_event = next(
        (
            group["event"]
            for group in groups
            if _is_compact_graph_retrieval(group["event"])
        ),
        None,
    )
    if compact_event:
        for group in _graph_trace_groups_from_compact(compact_event):
            stage_groups.setdefault(group["stage"], group)

    return [
        stage_groups[stage]
        for stage in GRAPH_TRACE_STAGES
        if stage in stage_groups
    ]


def _trace_stage_label(event, graph=False):
    stage = str(event.get("stage") or "trace")
    if graph:
        return GRAPH_TRACE_STAGE_LABELS.get(
            stage,
            stage.replace("_", " ").title(),
        )
    return TRACE_STAGE_LABELS.get(stage, stage.replace("_", " ").title())


def _trace_status(event):
    raw_status = str(event.get("status") or "").lower()
    if raw_status == "running":
        return "running", "RUNNING"
    if raw_status == "skipped":
        return "skipped", "SKIPPED"
    if raw_status in {"error", "failed", "provider_error"} or event.get(
        "error_type"
    ):
        return "error", "ERROR"
    if raw_status == "no_evidence":
        return "complete", "NO EVIDENCE"
    if raw_status in {"complete", "ok", "success", "valid"}:
        return "complete", "COMPLETE"
    return "complete", "RECORDED"


def _trace_duration(event, raw_events):
    latency = event.get("latency_sec")
    details = event.get("details")
    if latency is None and isinstance(details, dict):
        latency = details.get("latency_sec")
    if latency is not None:
        try:
            return f"{float(latency):.1f}s"
        except (TypeError, ValueError):
            pass

    timestamps = [
        raw_event.get("timestamp")
        for raw_event in raw_events
        if raw_event.get("timestamp")
    ]
    if len(timestamps) < 2:
        return ""
    try:
        started_at = datetime.fromisoformat(
            str(timestamps[0]).replace("Z", "+00:00")
        )
        finished_at = datetime.fromisoformat(
            str(timestamps[-1]).replace("Z", "+00:00")
        )
    except ValueError:
        return ""
    seconds = max(0.0, (finished_at - started_at).total_seconds())
    return "<0.1s" if seconds < 0.1 else f"{seconds:.1f}s"


def _trace_detail_items(event):
    ignored = {
        "run_id",
        "seq",
        "timestamp",
        "stage",
        "status",
        "message",
        "details",
    }
    values = {
        key: value
        for key, value in event.items()
        if key not in ignored and value not in (None, "", [], {})
    }
    details = event.get("details")
    if isinstance(details, dict):
        values.update({
            key: value
            for key, value in details.items()
            if value not in (None, "", [], {})
        })

    ordered_keys = [key for key in TRACE_FIELD_PRIORITY if key in values]
    ordered_keys.extend(key for key in values if key not in ordered_keys)
    return [
        (
            TRACE_FIELD_LABELS.get(key, key.replace("_", " ").title()),
            _format_trace_value(values[key]),
        )
        for key in ordered_keys[:8]
    ]


def _format_trace_value(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    if isinstance(value, (list, tuple)):
        if all(isinstance(item, (str, int, float, bool)) for item in value):
            preview = ", ".join(str(item) for item in value[:3])
            remaining = len(value) - 3
            return f"{preview} +{remaining} more" if remaining > 0 else preview
        return f"{len(value)} records"
    if isinstance(value, dict):
        return f"{len(value)} fields"
    text = str(value)
    return text if len(text) <= 96 else f"{text[:93]}..."


def _graph_trace_triples(event):
    details = event.get("details")
    details = details if isinstance(details, dict) else {}
    triple_filter = details.get("triple_filter") or event.get("triple_filter")
    triple_filter = triple_filter if isinstance(triple_filter, dict) else {}
    triples = (
        details.get("triple_candidates")
        or event.get("triple_candidates")
        or triple_filter.get("candidates_before_filter")
        or triple_filter.get("candidates_after_filter")
        or triple_filter.get("selected_triples")
        or []
    )
    return [triple for triple in triples if isinstance(triple, dict)]


def _build_graph_triple_list(triples):
    if not triples:
        return '<div class="trace-triple-empty">No triple candidates returned.</div>'

    rows = []
    for index, triple in enumerate(triples, start=1):
        head = html.escape(str(triple.get("head") or "?"))
        relation = html.escape(str(triple.get("relation") or "?"))
        tail = html.escape(str(triple.get("tail") or "?"))
        similarity = triple.get("similarity")
        similarity_label = (
            _format_trace_value(similarity)
            if similarity is not None
            else "n/a"
        )
        rows.append(
            '<div class="trace-triple-row">'
            f'<span class="trace-triple-index">{index:02d}</span>'
            '<code class="trace-triple-expression">'
            f'<span class="trace-triple-node">({head})</span>'
            f'<span class="trace-triple-relation">-[{relation}]-&gt;</span>'
            f'<span class="trace-triple-node">({tail})</span>'
            '</code>'
            f'<span class="trace-triple-similarity">[{similarity_label}]</span>'
            '</div>'
        )
    return '<div class="trace-triple-list">' + "".join(rows) + '</div>'


def _build_graph_trace_details(event, raw_events):
    stage = str(event.get("stage") or "")
    if stage == "synthesis":
        return ""

    details = event.get("details")
    details = details if isinstance(details, dict) else {}
    parameters = event.get("parameters")
    parameters = parameters if isinstance(parameters, dict) else {}

    if stage == "seed_selection":
        triples = _graph_trace_triples(event)
        detail_grid = "".join(
            (
                '<div class="trace-detail-item">'
                f"<dt>{label}</dt><dd>{html.escape(value)}</dd></div>"
            )
            for label, value in (
                (
                    "Seed Mode",
                    str(
                        details.get("seed_mode")
                        or parameters.get("seed_mode")
                        or "n/a"
                    ),
                ),
                (
                    "Top-K Triple",
                    str(
                        details.get("top_k_triples")
                        or parameters.get("top_k_triples")
                        or len(triples)
                    ),
                ),
            )
        )
        detail_grid += (
            '<div class="trace-detail-item trace-detail-item-wide">'
            '<dt>Triples</dt>'
            f"{_build_graph_triple_list(triples)}</div>"
        )
        field_count = 3
    elif stage == "personalized_pagerank":
        detail_grid = "".join(
            (
                '<div class="trace-detail-item">'
                f"<dt>{label}</dt><dd>{html.escape(value)}</dd></div>"
            )
            for label, value in (
                (
                    "Mode",
                    str(
                        details.get("graph_mode")
                        or details.get("ppr_graph_mode")
                        or parameters.get("ppr_graph_mode")
                        or "n/a"
                    ),
                ),
                (
                    "Seed Weight",
                    str(
                        details.get("seed_weight_mode")
                        or details.get("ppr_seed_weight_mode")
                        or parameters.get("ppr_seed_weight_mode")
                        or "n/a"
                    ),
                ),
                (
                    "Damping",
                    str(
                        details.get("damping")
                        or parameters.get("damping")
                        or "n/a"
                    ),
                ),
            )
        )
        field_count = 3
    elif stage == "retrieval_complete":
        chunk_ids = _graph_chunk_ids(event)
        detail_grid = "".join(
            (
                '<div class="trace-detail-item">'
                f"<dt>{label}</dt><dd>{html.escape(value)}</dd></div>"
            )
            for label, value in (
                ("Chunk Count", str(len(chunk_ids))),
                ("Chunks", ", ".join(chunk_ids) or "None"),
            )
        )
        field_count = 2
    else:
        return ""

    raw_payload = raw_events[0] if len(raw_events) == 1 else {
        "stage": event.get("stage"),
        "events": raw_events,
    }
    raw_json = html.escape(
        json.dumps(raw_payload, ensure_ascii=False, indent=2, default=str)
    )
    return (
        '<details class="trace-detail-panel">'
        '<summary><span>VIEW DETAILS</span>'
        f"<small>{field_count} KEY FIELDS</small></summary>"
        '<div class="trace-detail-content">'
        f'<dl class="trace-detail-grid">{detail_grid}</dl>'
        '<details class="raw-json-disclosure">'
        '<summary>RAW JSON</summary>'
        f"<pre>{raw_json}</pre>"
        '</details></div></details>'
    )


def _build_trace_details(event, raw_events, graph=False):
    if graph:
        return _build_graph_trace_details(event, raw_events)
    detail_items = _trace_detail_items(event)
    detail_grid = "".join(
        '<div class="trace-detail-item">'
        f"<dt>{html.escape(label)}</dt>"
        f"<dd>{html.escape(value)}</dd>"
        "</div>"
        for label, value in detail_items
    )
    raw_payload = raw_events[0] if len(raw_events) == 1 else {
        "stage": event.get("stage"),
        "events": raw_events,
    }
    raw_json = html.escape(
        json.dumps(raw_payload, ensure_ascii=False, indent=2, default=str)
    )
    field_label = f"{len(detail_items)} KEY FIELDS" if detail_items else "RAW EVENT"
    grid_markup = (
        f'<dl class="trace-detail-grid">{detail_grid}</dl>'
        if detail_items
        else ""
    )
    return (
        '<details class="trace-detail-panel">'
        '<summary><span>VIEW DETAILS</span>'
        f"<small>{field_label}</small></summary>"
        '<div class="trace-detail-content">'
        f"{grid_markup}"
        '<details class="raw-json-disclosure">'
        "<summary>RAW JSON</summary>"
        f"<pre>{raw_json}</pre>"
        "</details></div></details>"
    )


def _build_trace_row(
    index,
    event,
    raw_events=None,
    is_active=False,
    graph=False,
):
    raw_events = list(raw_events or [event])
    status_class, status_label = _trace_status(event)
    active_class = " is-active" if is_active else ""
    duration = _trace_duration(event, raw_events)
    duration_markup = f"<time>{html.escape(duration)}</time>" if duration else ""
    return (
        f'<div class="trace-event-row trace-status-{status_class}{active_class}">'
        f'<span class="trace-event-index">{index:02d}</span>'
        '<span class="trace-event-dot"></span>'
        '<div class="trace-event-copy">'
        '<div class="trace-event-heading">'
        f"<b>{html.escape(_trace_stage_label(event, graph=graph))}</b>"
        '<span class="trace-event-meta">'
        f'<span class="trace-status-pill">{status_label}</span>'
        f"{duration_markup}</span></div>"
        f"<p>{html.escape(_trace_label(event))}</p>"
        f"{_build_trace_details(event, raw_events, graph=graph)}"
        "</div></div>"
    )


def _markup(value):
    """Remove Python indentation so Streamlit treats the value as raw HTML."""
    return dedent(value).strip()


def _render_answer_markdown(answer):
    """Render model Markdown safely before placing it inside the answer card."""
    renderer = MarkdownIt("commonmark", {"html": False, "breaks": True})
    return renderer.render(answer)
