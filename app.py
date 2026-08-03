"""
Streamlit UI for the SemiGraph Full Agent — enterprise theme, dark + light.

The UI exposes the production Agent harness in three configurations:
autonomous routing, Vector-locked, and Graph-locked. Every configuration runs
the same PlanRoute -> Execute -> Assess/Retry -> Synthesize workflow.

Theme: a runtime Dark/Light toggle (sidebar). The two palettes live in
PALETTES; build_css() renders the full stylesheet from the active palette,
so every surface — app, sidebar, cards, inputs, buttons — switches together.

Run:
    streamlit run app.py
Then open http://localhost:8501
"""
from __future__ import annotations

from html import escape
import logging
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

logging.getLogger("neo4j").setLevel("ERROR")
logging.getLogger("httpx").setLevel("WARNING")

import streamlit as st

from semigraph.agent.graph import build_agent
from semigraph.agent.ledger import retrieval_traces, tool_calls
from semigraph.connections import get_neo4j_driver
from demo_rag import SUGGESTED_QUERIES


st.set_page_config(
    page_title="SemiGraph Agent",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════ palettes ══════════════════════════
PALETTES = {
    "Dark": {
        "bg": "#0D1117", "surface": "#161B22", "sidebar": "#0A0D13",
        "border": "#30363D", "border_soft": "#21262D",
        "text": "#C9D1D9", "text_strong": "#F0F6FC", "text_muted": "#7D8590",
        "accent": "#1F6FEB", "accent_hover": "#388BFD", "accent_text": "#58A6FF",
        "input_bg": "#0D1117", "answer_bg": "#0F141B",
    },
    "Light": {
        "bg": "#FFFFFF", "surface": "#F6F8FA", "sidebar": "#F0F2F5",
        "border": "#D0D7DE", "border_soft": "#E4E7EB",
        "text": "#1F2328", "text_strong": "#0A0C10", "text_muted": "#656D76",
        "accent": "#0969DA", "accent_hover": "#0860C9", "accent_text": "#0969DA",
        "input_bg": "#FFFFFF", "answer_bg": "#F6F8FA",
    },
}


def build_css(p: dict) -> str:
    """Render the full stylesheet from a palette dict."""
    return f"""
<style>
/* ---- hide only the safe Streamlit chrome (keep header → sidebar toggle works) ---- */
#MainMenu {{visibility: hidden;}}
footer    {{visibility: hidden;}}
[data-testid="stStatusWidget"] {{visibility: hidden;}}
.stHeadingContainer a, h1 a, h2 a, h3 a {{display: none !important;}}

/* ---- app + header surfaces ---- */
[data-testid="stAppViewContainer"], .stApp {{ background: {p['bg']}; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.0rem; padding-bottom: 3rem; max-width: 1180px; }}

/* ---- global text ---- */
.stApp, .stApp p, .stApp li, .stApp label, .stApp span,
[data-testid="stMarkdownContainer"] {{ color: {p['text']}; }}

/* ---- keep the sidebar collapse / expand control clearly visible ---- */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] {{ visibility: visible !important; }}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg {{ color: {p['accent_text']}; }}

/* ---- header bar ---- */
.sg-header {{ margin-bottom: 18px; }}
.sg-brand {{ display: flex; align-items: center; gap: 11px; }}
.sg-mark {{
    width: 16px; height: 16px; background: {p['accent']};
    border-radius: 3px; transform: rotate(45deg);
}}
.sg-title {{
    font-size: 1.55rem; font-weight: 700; color: {p['text_strong']};
    letter-spacing: -0.02em; line-height: 1.1;
}}
.sg-sub {{
    font-size: 0.71rem; color: {p['text_muted']};
    margin-top: 7px; text-transform: uppercase; letter-spacing: 0.10em;
}}

/* ---- sidebar ---- */
[data-testid="stSidebar"] {{
    background: {p['sidebar']};
    border-right: 1px solid {p['border_soft']};
}}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.4rem; }}

/* ---- section labels ---- */
.sg-label {{
    font-size: 0.69rem; color: {p['text_muted']}; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.11em;
    margin: 18px 0 8px 0;
}}

/* ---- metric cards ---- */
[data-testid="stMetric"] {{
    background: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 10px 14px 8px 14px;
}}
[data-testid="stMetricValue"] {{
    font-size: 1.32rem; font-weight: 700; color: {p['accent_text']};
}}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{
    font-size: 0.65rem; color: {p['text_muted']}; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.06em;
}}

/* ---- secondary / suggested buttons ---- */
.stButton > button {{
    width: 100%;
    background: {p['surface']};
    border: 1px solid {p['border']};
    color: {p['text']};
    border-radius: 6px;
    font-size: 0.80rem; font-weight: 500;
    text-align: left;
    padding: 9px 12px; line-height: 1.35;
    transition: all 0.12s ease;
}}
.stButton > button:hover {{
    border-color: {p['accent']};
    color: {p['text_strong']};
}}
.stButton > button:active {{ transform: translateY(1px); }}

/* ---- primary "Ask" button — tall, full-width, prominent ---- */
.stButton > button[kind="primary"] {{
    background: {p['accent']};
    border: 1px solid {p['accent']};
    color: #FFFFFF;
    text-align: center;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 16px 12px;
    border-radius: 8px;
    margin-top: 4px;
}}
.stButton > button[kind="primary"]:hover {{
    background: {p['accent_hover']};
    border-color: {p['accent_hover']};
    color: #FFFFFF;
}}

/* ---- premium search input ---- */
[data-testid="stTextInput"] input {{
    background: {p['input_bg']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 15px 16px;
    font-size: 1.02rem;
    color: {p['text_strong']};
    transition: all 0.15s ease;
}}
[data-testid="stTextInput"] input:focus {{
    border-color: {p['accent']};
    box-shadow: 0 0 0 3px {p['accent']}28;
}}
[data-testid="stTextInput"] input::placeholder {{ color: {p['text_muted']}; }}
[data-testid="stTextInput"] label {{
    font-size: 0.72rem; color: {p['text_muted']}; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.07em;
}}

/* ---- expander (retrieved evidence) ---- */
[data-testid="stExpander"] {{
    border: 1px solid {p['border_soft']};
    border-radius: 6px;
    background: {p['answer_bg']};
}}
[data-testid="stExpander"] summary {{ font-size: 0.84rem; }}
[data-testid="stExpander"] summary:hover {{ color: {p['accent_text']}; }}

/* ---- radio (theme toggle) ---- */
[data-testid="stRadio"] label {{ color: {p['text']}; }}

/* ---- muted caption ---- */
.sg-muted {{
    font-size: 0.80rem; color: {p['text_muted']};
    margin-top: 6px; line-height: 1.55;
}}

/* ---- answer surface ---- */
.sg-answer {{
    background: {p['answer_bg']};
    border: 1px solid {p['border_soft']};
    border-left: 3px solid {p['accent']};
    border-radius: 6px;
    padding: 16px 20px;
    color: {p['text']};
}}

/* ---- Thinking + execution timeline ---- */
.sg-thinking {{
    background: {p['surface']};
    border: 1px solid {p['border']};
    border-left: 3px solid {p['accent_text']};
    border-radius: 8px;
    padding: 12px 15px;
    margin: 10px 0 16px 0;
}}
.sg-thinking-title {{
    color: {p['text_strong']}; font-size: 0.88rem; font-weight: 700;
}}
.sg-thinking-line {{
    color: {p['text_muted']}; font-size: 0.78rem; line-height: 1.55;
    margin-top: 4px;
}}
.sg-pulse {{
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    background: {p['accent_text']}; margin-right: 8px;
    box-shadow: 0 0 0 0 {p['accent_text']}66;
    animation: sg-pulse 1.6s infinite;
}}
@keyframes sg-pulse {{
    0% {{ box-shadow: 0 0 0 0 {p['accent_text']}66; }}
    70% {{ box-shadow: 0 0 0 7px {p['accent_text']}00; }}
    100% {{ box-shadow: 0 0 0 0 {p['accent_text']}00; }}
}}
.sg-trace-card {{
    background: {p['answer_bg']}; border: 1px solid {p['border_soft']};
    border-radius: 7px; padding: 10px 13px; margin: 7px 0;
}}
.sg-trace-card strong {{ color: {p['text_strong']}; }}
.sg-trace-muted {{ color: {p['text_muted']}; font-size: 0.76rem; }}
.sg-trace-ok {{ color: #3FB950; }}
.sg-trace-retry {{ color: #D29922; }}
.sg-trace-error {{ color: #F85149; }}
.sg-trace-running {{ color: {p['accent_text']}; }}

/* ---- response-type badge ---- */
.sg-badge {{
    display: inline-flex; align-items: center; gap: 7px;
    padding: 6px 13px; border-radius: 13px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em;
}}
.sg-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
</style>
"""


# ---- resolve active theme (default Dark) ----
mode = st.session_state.get("theme_mode", "Dark")
palette = PALETTES[mode]
st.markdown(build_css(palette), unsafe_allow_html=True)


AGENT_MODES = {
    "Full Agent (Routing)": {
        "locked_tool": None,
        "description": (
            "PlanRoute chooses Graph, Vector, Financial, or News for each task, "
            "then Assess can retry with a better query or tool."
        ),
    },
    "Agent Locked Vector": {
        "locked_tool": "vector",
        "description": (
            "The Agent still plans, assesses, and retries, but every retrieval "
            "attempt is forced through Vector Search."
        ),
    },
    "Agent Locked Graph": {
        "locked_tool": "graph",
        "description": (
            "The Agent still plans, assesses, and retries, but every retrieval "
            "attempt is forced through Graph Search (PPR)."
        ),
    },
}
AGENT_RECURSION_LIMIT = 50


@st.cache_resource(show_spinner="Loading Agent harness...")
def load_agent(mode: str, top_k: int):
    """Build and cache one compiled Agent graph per UI configuration."""
    locked_tool = AGENT_MODES[mode]["locked_tool"]
    return build_agent(locked_tool=locked_tool, top_k=top_k)


def agent_badge(mode: str) -> str:
    """Return a compact badge for the active Agent configuration."""
    colors = {
        "Full Agent (Routing)": ("#1B3A2A", "#3FB950"),
        "Agent Locked Vector": ("#1C3150", "#58A6FF"),
        "Agent Locked Graph": ("#3A3115", "#D29922"),
    }
    bg, fg = colors[mode]
    return (
        f'<span class="sg-badge" style="background:{bg}; color:{fg}; '
        f'border:1px solid {fg}66;">'
        f'<span class="sg-dot" style="background:{fg};"></span>{mode}</span>'
    )


def evidence_title(citation: dict) -> str:
    """Build a readable title for narrative, financial, or news evidence."""
    index = citation.get("citation_index", "?")
    parts = [f"[{index}]", str(citation.get("ticker") or "Unknown source")]
    fiscal_year = citation.get("fiscal_year")
    if fiscal_year:
        parts.append(f"FY{fiscal_year}")
    section = citation.get("section")
    if section:
        parts.append(str(section))
    score = citation.get("score")
    if isinstance(score, (int, float)):
        parts.append(f"score {score:.3f}")
    return "  ·  ".join(parts)


TOOL_META = {
    "vector": {"label": "Vector Search", "icon": "▦", "tone": "running"},
    "graph": {"label": "Graph Search (PPR)", "icon": "◇", "tone": "ok"},
    "financial": {"label": "Financial Search", "icon": "$", "tone": "ok"},
    "news": {"label": "News Search", "icon": "◌", "tone": "ok"},
}


def tool_label(tool: str | None) -> str:
    """Return a user-facing Tool label without exposing internal enum names."""
    return (TOOL_META.get(str(tool or ""), {}).get("label")
            or str(tool or "Unknown Tool"))


def tool_icon(tool: str | None) -> str:
    """Return a compact icon for a Tool timeline row."""
    return TOOL_META.get(str(tool or ""), {}).get("icon", "•")


def compact_query(value: Any, limit: int = 118) -> str:
    """Collapse a Tool query for a readable one-line timeline label."""
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[:limit - 1]}…"


def _attempt_latency(attempt: dict) -> float | None:
    """Extract the retriever latency recorded inside an Attempt trace."""
    trace = attempt.get("retrieval_trace") or {}
    value = trace.get("latency_sec")
    if value is None:
        value = trace.get("backend_latency_sec")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _assessment_summary(attempt: dict) -> tuple[str, str]:
    """Return a short status and reason for one Attempt."""
    if attempt.get("retrieval_status") == "tool_error":
        trace = attempt.get("retrieval_trace") or {}
        return "error", str(trace.get("error_type") or "Tool error")

    assessment = attempt.get("assessment") or {}
    controller = assessment.get("controller") or {}
    decision = str(controller.get("decision") or "").lower()
    reason = str(controller.get("reason") or "").replace("_", " ")
    if decision == "retry":
        next_action = controller.get("next_action") or {}
        next_tool = tool_label(next_action.get("tool"))
        return "retry", f"retry → {next_tool}{f' · {reason}' if reason else ''}"
    if decision == "accept":
        return "ok", "accepted by Assess"
    if controller.get("stop_reason"):
        return "retry", str(controller.get("stop_reason")).replace("_", " ")
    if assessment:
        return "running", "Assess completed"
    return "running", "retrieved · waiting for Assess"


def _thinking_label(state: dict, elapsed: float) -> str:
    """Describe the latest streamed Agent stage in plain language."""
    plan_trace = state.get("plan_trace") or {}
    tasks = state.get("tasks") or []
    attempts = state.get("attempts") or []
    task_results = state.get("task_results") or []
    synthesis = state.get("synthesis_trace") or {}

    if synthesis:
        citations = len(state.get("citation_map") or [])
        return f"สังเคราะห์คำตอบและ citations ({citations}) · {elapsed:.1f}s"

    if attempts:
        latest = attempts[-1]
        action = latest.get("action") or {}
        status, detail = _assessment_summary(latest)
        prefix = {
            "ok": "Assess ยอมรับหลักฐาน",
            "retry": "Assess ขอค้นใหม่",
            "error": "Tool error",
            "running": "กำลังประเมินหลักฐาน",
        }.get(status, "กำลังทำงาน")
        return (
            f"{prefix} · {tool_label(action.get('tool'))} · "
            f"{compact_query(action.get('query'), 84)} · {detail} · {elapsed:.1f}s"
        )

    if task_results and tasks:
        return f"Tool workers เสร็จ {len(task_results)}/{len(tasks)} task · {elapsed:.1f}s"

    if plan_trace.get("status") == "ok" and tasks:
        tools = ", ".join(tool_label((task.get("initial_action") or {}).get("tool"))
                       for task in tasks)
        return f"PlanRoute เลือก {len(tasks)} task · {tools} · {elapsed:.1f}s"

    if plan_trace.get("status") == "error":
        return "PlanRoute พบข้อผิดพลาด · กำลังปิดการทำงาน"
    return f"กำลังวางแผน evidence needs · {elapsed:.1f}s"


def run_agent_with_thinking(agent, query: str, status_box) -> tuple[dict, list[str]]:
    """Stream Agent state updates and render a live Thinking status in Streamlit.

    The production Agent remains unchanged. The UI consumes the compiled
    LangGraph stream and turns each emitted state into a human-readable stage.
    """
    started_at = time.perf_counter()
    latest_state: dict = {}
    thinking_events: list[str] = []
    status_box.update(
        label="Thinking · กำลังเริ่ม Agent",
        state="running",
        expanded=True,
    )

    for streamed_state in agent.stream(
        {"original_query": query},
        config={"recursion_limit": AGENT_RECURSION_LIMIT},
        stream_mode="values",
    ):
        if not isinstance(streamed_state, dict):
            continue
        latest_state = dict(streamed_state)
        label = _thinking_label(latest_state, time.perf_counter() - started_at)
        if not thinking_events or label != thinking_events[-1]:
            thinking_events.append(label)
            status_box.write(label)
        status_box.update(label=f"Thinking · {label}", state="running")

    status_box.update(
        label=("Thinking · เสร็จแล้ว · "
               f"{time.perf_counter() - started_at:.1f}s"),
        state="complete",
        expanded=False,
    )
    return latest_state, thinking_events


def render_thinking_summary(events: list[str]) -> None:
    """Render the compact post-run Thinking history."""
    if not events:
        return
    lines = "".join(
        f'<div class="sg-thinking-line"><span class="sg-trace-muted">{i:02d}</span> '
        f'{escape(event)}</div>'
        for i, event in enumerate(events, start=1)
    )
    st.markdown(
        '<div class="sg-thinking">'
        '<div class="sg-thinking-title">Thinking history</div>'
        f'{lines}</div>',
        unsafe_allow_html=True,
    )


def render_execution_trace(result: dict) -> None:
    """Render a progressive-disclosure timeline for plan, Tools, and synthesis."""
    tasks = result.get("tasks") or []
    attempts = result.get("attempts") or []
    plan_trace = result.get("plan_trace") or {}
    synthesis_trace = result.get("synthesis_trace") or {}

    st.markdown('<div class="sg-label">Execution trace</div>', unsafe_allow_html=True)

    plan_status = "ok" if plan_trace.get("status") == "ok" else "error"
    plan_text = (
        f"{len(tasks)} task(s) planned"
        if tasks else str(plan_trace.get("fallback_source") or "no task plan")
    )
    plan_class = "sg-trace-ok" if plan_status == "ok" else "sg-trace-error"
    st.markdown(
        f'<div class="sg-trace-card"><strong>01 · PlanRoute</strong> · '
        f'<span class="{plan_class}">{escape(plan_text)}</span>'
        f'<div class="sg-trace-muted">LLM calls: '
        f'{plan_trace.get("llm_calls", 0)} · '
        f'status: {escape(str(plan_trace.get("status") or "unknown"))}</div></div>',
        unsafe_allow_html=True,
    )

    if tasks:
        with st.expander("ดูงานที่ Planner สร้าง", expanded=False):
            for task in tasks:
                action = task.get("initial_action") or {}
                st.markdown(
                    f'**{escape(str(task.get("task_id") or "Task"))}** · '
                    f'{tool_icon(action.get("tool"))} {escape(tool_label(action.get("tool")))}  \n'
                    f'{escape(compact_query(task.get("query"), 240))}'
                )

    for index, attempt in enumerate(attempts, start=2):
        action = attempt.get("action") or {}
        status, detail = _assessment_summary(attempt)
        status_class = {
            "ok": "sg-trace-ok",
            "retry": "sg-trace-retry",
            "error": "sg-trace-error",
            "running": "sg-trace-running",
        }.get(status, "sg-trace-muted")
        latency = _attempt_latency(attempt)
        latency_text = f" · {latency:.1f}s" if latency is not None else ""
        chunks = attempt.get("chunks") or []
        st.markdown(
            f'<div class="sg-trace-card"><strong>{index:02d} · '
            f'{escape(str(attempt.get("attempt_id") or "Attempt"))}</strong> · '
            f'{tool_icon(action.get("tool"))} '
            f'{escape(tool_label(action.get("tool")))} · '
            f'<span class="{status_class}">{escape(detail)}</span>'
            f'<div class="sg-trace-muted">Retrieved chunks: {len(chunks)}{latency_text} · '
            f'query: {escape(compact_query(action.get("query")))}</div></div>',
            unsafe_allow_html=True,
        )
        with st.expander(
            f"{attempt.get('attempt_id', 'Attempt')} · ดู chunks และ Assess",
            expanded=False,
        ):
            metadata = st.columns(4)
            metadata[0].metric("Tool", tool_label(action.get("tool")))
            metadata[1].metric("Chunks", len(chunks))
            assessment = attempt.get("assessment") or {}
            output = assessment.get("output") or {}
            metadata[2].metric("Accepted", len(output.get("accepted_chunk_ids") or []))
            metadata[3].metric("Status", str(assessment.get("status") or "pending"))
            st.caption("Tool query")
            st.code(str(action.get("query") or ""), language="text")
            if chunks:
                st.caption("Retrieved evidence")
                for chunk in chunks:
                    st.write(
                        f"{chunk.get('chunk_id', 'unknown')} · "
                        f"{chunk.get('ticker', '—')} FY{chunk.get('fiscal_year', '—')} "
                        f"{chunk.get('section', '')}"
                    )
            if assessment:
                st.caption("Assess decision")
                st.json({
                    "controller": assessment.get("controller") or {},
                    "accepted_chunk_ids": output.get("accepted_chunk_ids") or [],
                    "missing_requirements": output.get("missing_requirements"),
                })

    synthesis_status = str(synthesis_trace.get("status") or "not started")
    synthesis_class = "sg-trace-ok" if synthesis_status == "ok" else "sg-trace-error"
    st.markdown(
        f'<div class="sg-trace-card"><strong>{len(attempts) + 2:02d} · '
        f'Synthesis</strong> · <span class="{synthesis_class}">'
        f'{escape(synthesis_status)}</span>'
        f'<div class="sg-trace-muted">LLM calls: '
        f'{synthesis_trace.get("llm_calls", 0)} · citations: '
        f'{len(result.get("citation_map") or [])}</div></div>',
        unsafe_allow_html=True,
    )


def render_debug_panel(result: dict) -> None:
    """Render raw trace data only when the user explicitly opens Debug."""
    attempts = result.get("attempts") or []
    with st.expander("Debugging · raw Agent trace", expanded=False):
        st.caption(
            "รายละเอียดนี้ใช้ตรวจการทำงานของ Agent: Planner, Tool calls, "
            "retrieval trace, Assess/Retry และ Synthesis"
        )
        debug_tab, raw_tab = st.tabs(["สรุป Debug", "Raw state"])
        with debug_tab:
            st.json({
                "stop_reason": result.get("stop_reason"),
                "completed_tasks": result.get("completed_tasks") or [],
                "tool_calls": tool_calls(attempts),
                "synthesis_trace": result.get("synthesis_trace") or {},
            })
        with raw_tab:
            st.json({
                "plan_trace": result.get("plan_trace") or {},
                "retrieval_traces": retrieval_traces(attempts),
                "attempts": attempts,
                "synthesis_trace": result.get("synthesis_trace") or {},
            })


@st.cache_data(ttl=60, show_spinner=False)
def load_corpus_stats() -> dict[str, int]:
    """Read live corpus counts from the configured Neo4j database."""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            record = session.run(
                """
                OPTIONAL MATCH (d:Document)
                WITH count(d) AS filings,
                     count(DISTINCT d.ticker) AS companies,
                     count(DISTINCT d.fiscal_year) AS fiscal_years
                OPTIONAL MATCH (c:Chunk)
                WITH filings, companies, fiscal_years, count(c) AS chunks
                OPTIONAL MATCH (e:Entity)
                WITH filings, companies, fiscal_years, chunks,
                     count(e) AS entities
                OPTIONAL MATCH ()-[r]->()
                RETURN companies, filings, chunks, entities, fiscal_years,
                       count(CASE WHEN NOT type(r) IN [
                           'HAS_SECTION', 'HAS_CHUNK', 'MENTIONS', 'SYNONYM_OF'
                       ] THEN 1 END) AS relationships,
                       count(r) AS all_relationships
                """
            ).single()
            if record is None:
                raise RuntimeError("Neo4j returned no corpus statistics")
            return {
                key: int(record[key])
                for key in (
                    "companies",
                    "filings",
                    "chunks",
                    "entities",
                    "fiscal_years",
                    "relationships",
                    "all_relationships",
                )
            }
    finally:
        driver.close()


def format_corpus_stat(stats: dict[str, int] | None, key: str) -> str:
    """Format a live metric, using an explicit unavailable marker on failure."""
    if stats is None:
        return "—"
    return f"{stats[key]:,}"


# ══════════════════════════ header ══════════════════════════
st.markdown(
    '<div class="sg-header">'
    '<div class="sg-brand">'
    '<span class="sg-mark"></span>'
    '<span class="sg-title">SemiGraph</span>'
    '</div>'
    '<div class="sg-sub">Agentic GraphRAG &nbsp;·&nbsp; Semiconductor 10-K '
    'Fundamental Analysis &nbsp;·&nbsp; NVDA · AMD · MU · ASML · INTC</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════ sidebar ══════════════════════════
with st.sidebar:
    st.markdown('<div class="sg-label">Appearance</div>', unsafe_allow_html=True)
    chosen = st.radio(
        "Theme", ["Dark", "Light"],
        index=["Dark", "Light"].index(mode),
        horizontal=True, label_visibility="collapsed",
    )
    if chosen != mode:
        st.session_state["theme_mode"] = chosen
        st.rerun()

    try:
        corpus_stats = load_corpus_stats()
    except Exception:
        logging.getLogger(__name__).exception("Unable to load Neo4j corpus stats")
        corpus_stats = None

    st.markdown('<div class="sg-label">Corpus</div>', unsafe_allow_html=True)
    r1c1, r1c2 = st.columns(2)
    r1c1.metric("Companies", format_corpus_stat(corpus_stats, "companies"))
    r1c2.metric("Filings", format_corpus_stat(corpus_stats, "filings"))
    r2c1, r2c2 = st.columns(2)
    r2c1.metric("Chunks", format_corpus_stat(corpus_stats, "chunks"))
    r2c2.metric("Entities", format_corpus_stat(corpus_stats, "entities"))
    r3c1, r3c2 = st.columns(2)
    r3c1.metric(
        "Relationships",
        format_corpus_stat(corpus_stats, "relationships"),
        help=(
            "Domain relationships only; provenance, MENTIONS, and SYNONYM_OF "
            "edges are excluded."
        ),
    )
    r3c2.metric(
        "Fiscal years",
        format_corpus_stat(corpus_stats, "fiscal_years"),
    )
    if corpus_stats is None:
        st.warning("Neo4j corpus statistics unavailable")
    else:
        st.caption(
            "Live Neo4j · domain relationships "
            f"({corpus_stats['relationships']:,}) · all edges "
            f"({corpus_stats['all_relationships']:,}) · refresh 60s"
        )

    st.markdown('<div class="sg-label">Agent configuration</div>',
                unsafe_allow_html=True)
    agent_mode = st.radio(
        "Agent configuration", list(AGENT_MODES),
        index=0, label_visibility="collapsed",
    )
    st.markdown(
        f'<div class="sg-muted">{AGENT_MODES[agent_mode]["description"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sg-label">Retrieval</div>', unsafe_allow_html=True)
    top_k = st.slider(
        "Chunks per attempt (top_k)", 3, 12, 5,
        help=(
            "Applied to every initial and retry action so all three Agent "
            "configurations can be compared under the same retrieval budget."
        ),
    )

    st.markdown('<div class="sg-label">Suggested queries</div>', unsafe_allow_html=True)
    for i, q in enumerate(SUGGESTED_QUERIES):
        if st.button(q["label"], key=f"sug_{i}", width="stretch"):
            st.session_state["query"] = q["query"]
            st.session_state["auto_run"] = True

# ══════════════════════════ query input ══════════════════════
query = st.text_input(
    "Ask a question  ·  Thai or English",
    value=st.session_state.get("query", ""),
    placeholder="e.g.  Which autonomous driving subsidiary does Intel operate?",
)
st.markdown(
    '<div class="sg-muted">The Agent plans evidence needs, routes each task, '
    'assesses retrieval quality, retries when needed, and synthesizes one '
    'citation-grounded answer.</div>',
    unsafe_allow_html=True,
)

run = st.button("Run SemiGraph Agent", type="primary") or st.session_state.pop(
    "auto_run", False
)

# ══════════════════════════ run + render ═════════════════════
if run and query.strip():
    result = None
    thinking_events: list[str] = []
    started_at = time.perf_counter()
    thinking_status = st.status(
        "Thinking · กำลังเตรียม Agent",
        expanded=True,
    )
    try:
        thinking_status.write("กำลังโหลด Agent harness และ retrieval configuration")
        agent = load_agent(agent_mode, top_k)
        result, thinking_events = run_agent_with_thinking(
            agent,
            query.strip(),
            thinking_status,
        )
    except Exception as exc:
        thinking_status.update(
            label=f"Thinking · ล้มเหลว: {type(exc).__name__}",
            state="error",
            expanded=True,
        )
        st.error(f"Agent run failed: {type(exc).__name__}: {exc}")

    if result is not None:
        latency = time.perf_counter() - started_at
        attempts = result.get("attempts") or []
        citations = result.get("citation_map") or []
        tasks = result.get("tasks") or []
        calls = tool_calls(attempts)

        st.markdown("")
        left, right = st.columns([3, 1], gap="large")
        with left:
            st.markdown('<div class="sg-label">Answer</div>',
                        unsafe_allow_html=True)
            answer = escape(str(result.get("final_answer") or ""))
            answer = answer.replace("\n", "<br>")
            st.markdown(f'<div class="sg-answer">{answer}</div>',
                        unsafe_allow_html=True)
        with right:
            st.markdown('<div class="sg-label">Agent mode</div>',
                        unsafe_allow_html=True)
            st.markdown(agent_badge(agent_mode), unsafe_allow_html=True)
            st.markdown(
                f'<div class="sg-muted">{AGENT_MODES[agent_mode]["description"]}</div>',
                unsafe_allow_html=True,
            )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tasks", len(tasks))
        m2.metric("Tool calls", len(calls))
        m3.metric("Citations", len(citations))
        m4.metric("Total latency", f"{latency:.1f}s")

        render_thinking_summary(thinking_events)
        render_execution_trace(result)

        st.markdown('<div class="sg-label">Cited evidence</div>',
                    unsafe_allow_html=True)
        if citations:
            st.markdown(
                f'<div class="sg-muted">{len(citations)} evidence chunks cited '
                'by the final synthesis.</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            for citation in citations:
                with st.expander(evidence_title(citation)):
                    st.text(str(citation.get("text") or "No text available."))
                    metadata = {
                        key: value
                        for key, value in citation.items()
                        if key != "text" and value not in (None, "", [], {})
                    }
                    st.json(metadata)
        else:
            st.info("The final answer did not cite an evidence chunk.")

        render_debug_panel(result)

elif run:
    st.markdown('<div class="sg-muted">Please enter a question first.</div>',
                unsafe_allow_html=True)
