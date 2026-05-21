"""
Streamlit UI for the SemiGraph RAG demo — enterprise theme, dark + light.

A thin presentation layer over scripts/demo_rag.py — same retrieval +
generation pipeline, browser front-end styled for the advisor demo.

Theme: a runtime Dark/Light toggle (sidebar). The two palettes live in
PALETTES; build_css() renders the full stylesheet from the active palette,
so every surface — app, sidebar, cards, inputs, buttons — switches together.

Run:
    streamlit run app.py
Then open http://localhost:8501
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

logging.getLogger("neo4j").setLevel("ERROR")
logging.getLogger("httpx").setLevel("WARNING")

import streamlit as st

from semigraph.config import get_config
from semigraph.connections import get_llm
from demo_rag import rag_answer, SUGGESTED_QUERIES


st.set_page_config(
    page_title="SemiGraph RAG",
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


@st.cache_resource(show_spinner="Loading config + LLM client...")
def load_backend():
    cfg = get_config()
    llm = get_llm(cfg)
    return cfg, llm


def classify_case(answer: str) -> str:
    """Detect which of the 3 response cases the answer fell into."""
    a = answer.strip()
    if a.startswith("บริบทจากเอกสาร 10-K") or a.startswith("The provided 10-K context"):
        return "C"
    if "▸" in a:
        return "B"
    return "A"


def case_badge(case: str) -> str:
    """Return an HTML pill (CSS dot, no emoji) for the response-type badge."""
    spec = {
        "A": ("#1B3A2A", "#3FB950", "DIRECT ANSWER"),
        "B": ("#3A3115", "#D29922", "INFERENCE"),
        "C": ("#2A2F38", "#8B949E", "REFUSED"),
    }
    bg, fg, label = spec[case]
    return (f'<span class="sg-badge" style="background:{bg}; color:{fg}; '
            f'border:1px solid {fg}66;">'
            f'<span class="sg-dot" style="background:{fg};"></span>{label}</span>')


CASE_DESC = {
    "A": "Answer stated explicitly in the retrieved 10-K chunks.",
    "B": "Not stated verbatim — reasoned from related context (marked ▸).",
    "C": "Categorically absent from the corpus — system declined to answer.",
}


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

cfg, llm = load_backend()

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

    st.markdown('<div class="sg-label">Corpus</div>', unsafe_allow_html=True)
    r1c1, r1c2 = st.columns(2)
    r1c1.metric("Companies", "5")
    r1c2.metric("Filings", "15")
    r2c1, r2c2 = st.columns(2)
    r2c1.metric("Chunks", "742")
    r2c2.metric("Entities", "4,856")
    r3c1, r3c2 = st.columns(2)
    r3c1.metric("Relationships", "6,607")
    r3c2.metric("Fiscal years", "3")

    st.markdown('<div class="sg-label">Retrieval</div>', unsafe_allow_html=True)
    top_k = st.slider("Chunks retrieved (top_k)", 3, 12, 8,
                      help="Higher = more context, but risk of 'lost in the middle'.")
    st.markdown(
        '<div class="sg-muted">hybrid_search — RRF (k=60) fusion of vector + '
        'graph PPR · DeepSeek-V4-flash generation.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sg-label">Suggested queries</div>', unsafe_allow_html=True)
    for i, q in enumerate(SUGGESTED_QUERIES):
        if st.button(q["label"], key=f"sug_{i}", use_container_width=True):
            st.session_state["query"] = q["query"]
            st.session_state["auto_run"] = True

# ══════════════════════════ query input ══════════════════════
query = st.text_input(
    "Ask a question  ·  Thai or English",
    value=st.session_state.get("query", ""),
    placeholder="e.g.  Which autonomous driving subsidiary does Intel operate?",
)
st.markdown(
    '<div class="sg-muted">Grounded strictly in 15 SEC 10-K filings. '
    'Hypothetical and comparative questions are answered as marked inferences; '
    'facts absent from the corpus are declined.</div>',
    unsafe_allow_html=True,
)

run = st.button("Ask SemiGraph", type="primary") or st.session_state.pop("auto_run", False)

# ══════════════════════════ run + render ═════════════════════
if run and query.strip():
    with st.spinner("Retrieving + generating…  (first query loads the embedding model ≈25s)"):
        result = rag_answer(query, top_k=top_k, cfg=cfg, llm=llm)

    if result.get("is_thai"):
        st.markdown(
            f'<div class="sg-muted"><b>TRANSLATED FOR RETRIEVAL</b> &nbsp;—&nbsp; '
            f'<em>{result["query_translated"]}</em></div>',
            unsafe_allow_html=True,
        )

    case = classify_case(result["answer"])

    st.markdown("")
    left, right = st.columns([3, 1], gap="large")
    with left:
        st.markdown('<div class="sg-label">Answer</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sg-answer">{result["answer"]}</div>',
                    unsafe_allow_html=True)
    with right:
        st.markdown('<div class="sg-label">Response type</div>', unsafe_allow_html=True)
        st.markdown(case_badge(case), unsafe_allow_html=True)
        st.markdown(f'<div class="sg-muted">{CASE_DESC[case]}</div>',
                    unsafe_allow_html=True)

    t_parts = []
    if result.get("t_translate_s"):
        t_parts.append(f"translate {result['t_translate_s']:.1f}s")
    t_parts.append(f"retrieve {result['t_retrieve_s']:.1f}s")
    t_parts.append(f"generate {result['t_generate_s']:.1f}s")
    st.markdown(f'<div class="sg-muted"><b>LATENCY</b> &nbsp;—&nbsp; '
                f'{"  ·  ".join(t_parts)}</div>', unsafe_allow_html=True)

    st.markdown('<div class="sg-label">Retrieved evidence</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sg-muted">{len(result["chunks"])} chunks — every answer '
        f'claim must trace back to one of these.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")
    for i, c in enumerate(result["chunks"], 1):
        with st.expander(
            f"[{i}]   {c['ticker']} · FY{c['fiscal_year']} · {c['section']}"
            f"      —  score {c['score']:.3f}"
        ):
            st.text(c["text"])

elif run:
    st.markdown('<div class="sg-muted">Please enter a question first.</div>',
                unsafe_allow_html=True)
