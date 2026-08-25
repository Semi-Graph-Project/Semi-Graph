from threading import Thread
from time import sleep
from uuid import uuid4

import streamlit as st

from Component import (
    configure_page,
    render_comparison_input,
    render_comparison_workspace,
    render_topbar,
)
from Style import apply_custom_style
from semigraph.demo import run_comparison
from semigraph.trace import TRACE_STORE


configure_page()
apply_custom_style()

if "comparison_query" not in st.session_state:
    st.session_state.comparison_query = None
if "vector_result" not in st.session_state:
    st.session_state.vector_result = None
if "vector_pending_query" not in st.session_state:
    st.session_state.vector_pending_query = None
if "graph_result" not in st.session_state:
    st.session_state.graph_result = None
if "graph_pending_query" not in st.session_state:
    st.session_state.graph_pending_query = None
if "comparison_history" not in st.session_state:
    st.session_state.comparison_history = {"vector": [], "graph": []}
else:
    st.session_state.comparison_history.setdefault("vector", [])
    st.session_state.comparison_history.setdefault("graph", [])

render_topbar()
workspace = st.empty()
live_results = {}
if st.session_state.vector_result:
    live_results["vector"] = st.session_state.vector_result
if st.session_state.graph_result:
    live_results["graph"] = st.session_state.graph_result
selected_corpus = render_comparison_workspace(
    st.session_state.comparison_query,
    live_results,
    histories=st.session_state.comparison_history,
    container=workspace,
)

prompt = render_comparison_input()

if prompt:
    previous_query = st.session_state.comparison_query
    if previous_query:
        for panel_key in ("vector", "graph"):
            previous_result = st.session_state.get(f"{panel_key}_result")
            if (
                previous_result
                and previous_result.get("status") in {"complete", "error"}
            ):
                panel_history = st.session_state.comparison_history.setdefault(
                    panel_key, []
                )
                panel_history.append({
                    "query": previous_query,
                    "result": dict(previous_result),
                })
    st.session_state.comparison_query = prompt
    for panel_key in ("vector", "graph"):
        setattr(
            st.session_state,
            f"{panel_key}_result",
            {
                "status": "running",
                "answer": "",
                "citations": [],
                "trace": [],
                "latency_sec": None,
                "error": None,
            },
        )
    st.session_state.vector_pending_query = prompt
    st.session_state.graph_pending_query = prompt
    st.rerun()

pending_queries = {
    "vector": st.session_state.vector_pending_query,
    "graph": st.session_state.graph_pending_query,
}
pending_queries = {
    panel_key: query
    for panel_key, query in pending_queries.items()
    if query
}
if any(pending_queries.values()):
    st.session_state.vector_pending_query = None
    st.session_state.graph_pending_query = None
    run_ids = {panel_key: uuid4().hex for panel_key in pending_queries}
    run_states = {panel_key: {} for panel_key in pending_queries}

    def run_backend(panel_key):
        run_states[panel_key]["result"] = run_comparison(
            mode=panel_key,
            query=pending_queries[panel_key],
            corpus=selected_corpus,
            top_k=5,
            run_id=run_ids[panel_key],
        )

    workers = {
        panel_key: Thread(
            target=run_backend,
            args=(panel_key,),
            daemon=True,
        )
        for panel_key in pending_queries
    }
    for worker in workers.values():
        worker.start()

    live_traces = {panel_key: [] for panel_key in pending_queries}
    while any(worker.is_alive() for worker in workers.values()):
        trace_updated = False
        for panel_key, run_id in run_ids.items():
            events = list(TRACE_STORE.read(run_id).get("events") or [])
            if len(events) != len(live_traces[panel_key]):
                live_traces[panel_key] = events
                trace_updated = True

        visible_results = {}
        for panel_key in pending_queries:
            result = run_states[panel_key].get("result")
            if result is not None:
                visible_results[panel_key] = (
                    result.to_dict()
                    if hasattr(result, "to_dict")
                    else result
                )
            else:
                visible_results[panel_key] = {
                    "status": "running",
                    "trace": live_traces[panel_key],
                }
        if trace_updated or any(
            run_states[panel_key].get("result") is not None
            for panel_key in pending_queries
        ):
            render_comparison_workspace(
                next(iter(pending_queries.values())),
                visible_results,
                histories=st.session_state.comparison_history,
                corpus=selected_corpus,
                container=workspace,
            )
        if any(worker.is_alive() for worker in workers.values()):
            sleep(0.08)
    for panel_key, worker in workers.items():
        worker.join()
        result = run_states[panel_key].get("result")
        if result is None:
            trace_document = TRACE_STORE.read(run_ids[panel_key])
            result = {
                "status": "error",
                "answer": "",
                "citations": [],
                "trace": list(trace_document.get("events") or []),
                "latency_sec": None,
                "error": f"{panel_key.title()} runner did not return a result.",
            }
        st.session_state[f"{panel_key}_result"] = (
            result.to_dict() if hasattr(result, "to_dict") else result
        )
    st.rerun()
