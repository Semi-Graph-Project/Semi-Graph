import html
from textwrap import dedent

from markdown_it import MarkdownIt
import streamlit as st


PAGE_CONFIG = {
    "page_title": "SemiGraph — Four-Way Comparison",
    "page_icon": "⚡",
    "layout": "wide",
}


BACKEND_CORPORA = (
    {
        "key": "benchmark",
        "label": "Benchmark (7690)",
        "description": "Controlled retrieval benchmark backend",
    },
    {
        "key": "production",
        "label": "Production (7687)",
        "description": "Main production Neo4j backend",
    },
)


CONFIGURATIONS = (
    {
        "number": "01",
        "name": "Vector-only RAG",
        "mode": "VECTOR · AGENT OFF",
        "retriever": "Vector",
        "agent": "Off",
        "answer": (
            "**Mock answer.** Synthesized directly from the highest-ranked "
            "semantic text chunks.\n\n"
            "- Retrieval: `vector_search`\n"
            "- Prompt: shared answer format"
        ),
        "trace": (
            ("01", "ROUTE", "direct retrieval"),
            ("02", "TOOL", "vector_search · top_k=5"),
            ("03", "ANSWER", "shared synthesis prompt"),
        ),
    },
    {
        "number": "02",
        "name": "Graph-only RAG",
        "mode": "GRAPH · AGENT OFF",
        "retriever": "Graph",
        "agent": "Off",
        "answer": (
            "**Mock answer.** Synthesized from graph-linked entities, concepts, "
            "and supporting chunks.\n\n"
            "- Retrieval: `graph_search`\n"
            "- Context: linked evidence"
        ),
        "trace": (
            ("01", "SEED", "entity and concept linking"),
            ("02", "TOOL", "graph_search · PPR"),
            ("03", "ANSWER", "shared synthesis prompt"),
        ),
    },
    {
        "number": "03",
        "name": "Agent + Vector",
        "mode": "VECTOR · AGENT ON",
        "retriever": "Vector",
        "agent": "On",
        "answer": (
            "**Mock answer.** The Agent plans a retrieval attempt, checks the "
            "evidence, and answers from vector results.\n\n"
            "1. Plan evidence requirements\n"
            "2. Run `vector_search`"
        ),
        "trace": (
            ("01", "PLAN", "evidence requirements"),
            ("02", "TOOL", "vector_search · top_k=5"),
            ("03", "CHECK", "evidence assessment"),
            ("04", "ANSWER", "shared synthesis prompt"),
        ),
    },
    {
        "number": "04",
        "name": "Agent + Graph",
        "mode": "GRAPH · AGENT ON",
        "retriever": "Graph",
        "agent": "On",
        "featured": True,
        "answer": (
            "**Mock answer.** The thesis configuration combines Agent control, "
            "graph retrieval, and evidence-adaptive retry.\n\n"
            "> The answer renderer accepts Markdown from the model."
        ),
        "trace": (
            ("01", "PLAN", "evidence requirements"),
            ("02", "TOOL", "graph_search · PPR"),
            ("03", "CHECK", "evidence assessment"),
            ("04", "ADAPT", "retry when evidence is insufficient"),
            ("05", "ANSWER", "shared synthesis prompt"),
        ),
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
                <span class="mode-badge"><span class="mode-dot"></span> MOCK MODE</span>
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_comparison_workspace(query=None):
    """Render the shared controls and four independently inspectable panels."""
    corpus = render_backend_corpus_selector()
    cards = "".join(_build_comparison_card(config, query) for config in CONFIGURATIONS)
    run_label = "RUN COMPLETE" if query else "READY FOR QUERY"
    run_class = "run-complete" if query else "run-waiting"
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
            <div><small>CORPUS</small><strong>{html.escape(corpus['label'])}</strong></div>
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
    st.markdown(markup, unsafe_allow_html=True)


def render_backend_corpus_selector():
    """Render the shared backend selector used by all four configurations."""
    labels = [corpus["label"] for corpus in BACKEND_CORPORA]
    selected_label = st.selectbox(
        "Backend Corpus",
        labels,
        index=0,
        key="backend_corpus",
        label_visibility="collapsed",
    )
    return next(corpus for corpus in BACKEND_CORPORA if corpus["label"] == selected_label)


def render_comparison_input():
    """Render the single question shared by all four configurations."""
    return st.chat_input("Ask one question to compare all four configurations…")


def _build_comparison_card(configuration, query):
    featured = configuration.get("featured", False)
    card_class = "comparison-card featured-card" if featured else "comparison-card"
    featured_badge = (
        '<span class="thesis-badge">THESIS SYSTEM</span>'
        if featured
        else "<!-- standard configuration -->"
    )
    status_label = "COMPLETE" if query else "WAITING"
    status_class = "status-complete" if query else "status-waiting"
    body = _build_result_body(configuration, query)

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
        <div class="config-tags">
            <span>RETRIEVER <b>{configuration['retriever']}</b></span>
            <span>AGENT <b>{configuration['agent']}</b></span>
        </div>
        """
    )
    return f'<article class="{card_class}">{header}{body}</article>'


def _build_result_body(configuration, query):
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

    safe_query = html.escape(query)
    answer_html = _render_answer_markdown(configuration["answer"])
    trace_rows = "".join(
        _markup(
            f"""
        <div class="trace-row">
            <span>{step}</span><b>{event}</b><code>{detail}</code>
        </div>
        """
        )
        for step, event, detail in configuration["trace"]
    )

    return _markup(
        f"""
        <div class="panel-chat">
            <div class="chat-turn user-turn">
                <span class="turn-label">SHARED QUESTION</span>
                <p>{safe_query}</p>
            </div>
            <div class="chat-turn answer-turn">
                <div class="answer-label-row">
                    <span class="turn-label">MOCK ANSWER</span>
                    <span class="mock-label">UI PLACEHOLDER</span>
                </div>
                <div class="answer-markdown">{answer_html}</div>
            </div>
        </div>
        <div class="evidence-section">
            <div class="section-label-row">
                <span>CITATIONS</span><small>2 MOCK SOURCES</small>
            </div>
            <div class="citation-list">
                <div><b>[C1]</b><span>Main corpus · filing chunk</span></div>
                <div><b>[C2]</b><span>Supporting evidence chunk</span></div>
            </div>
        </div>
        <details class="trace-details">
            <summary>
                <span>TECHNICAL TRACE</span>
                <small>{len(configuration['trace'])} STEPS</small>
            </summary>
            <div class="trace-table">{trace_rows}</div>
        </details>
        <div class="panel-footer">
            <span>INDEPENDENT STATUS · COMPLETE</span>
            <span>MOCK RESULT</span>
        </div>
    """
    )


def _markup(value):
    """Remove Python indentation so Streamlit treats the value as raw HTML."""
    return dedent(value).strip()


def _render_answer_markdown(answer):
    """Render model Markdown safely before placing it inside the answer card."""
    renderer = MarkdownIt("commonmark", {"html": False, "breaks": True})
    return renderer.render(answer).replace("\n", "")
