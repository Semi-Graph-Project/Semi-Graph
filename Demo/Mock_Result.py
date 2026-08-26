from threading import Thread
from time import sleep
from uuid import uuid4

import streamlit as st

from Component import (
    PANEL_KEYS,
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
for panel_key in PANEL_KEYS:
    result_key = f"{panel_key}_result"
    pending_key = f"{panel_key}_pending_query"
    if result_key not in st.session_state:
        st.session_state[result_key] = None
    if pending_key not in st.session_state:
        st.session_state[pending_key] = None
if "comparison_history" not in st.session_state:
    st.session_state.comparison_history = {
        panel_key: [] for panel_key in PANEL_KEYS
    }
for panel_key in PANEL_KEYS:
    st.session_state.comparison_history.setdefault(panel_key, [])

render_topbar()
workspace = st.empty()
live_results = {
    panel_key: st.session_state[f"{panel_key}_result"]
    for panel_key in PANEL_KEYS
    if st.session_state[f"{panel_key}_result"]
}
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
        for panel_key in PANEL_KEYS:
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
    running_results = {}
    for panel_key in PANEL_KEYS:
        running_result = {
            "status": "running",
            "answer": "",
            "citations": [],
            "trace": [],
            "latency_sec": None,
            "error": None,
        }
        st.session_state[f"{panel_key}_result"] = running_result
        st.session_state[f"{panel_key}_pending_query"] = prompt
        running_results[panel_key] = running_result
    render_comparison_workspace(
        prompt,
        running_results,
        histories=st.session_state.comparison_history,
        corpus=selected_corpus,
        container=workspace,
    )

pending_queries = {
    panel_key: st.session_state[f"{panel_key}_pending_query"]
    for panel_key in PANEL_KEYS
}
pending_queries = {
    panel_key: query
    for panel_key, query in pending_queries.items()
    if query
}
if any(pending_queries.values()):
    for panel_key in pending_queries:
        st.session_state[f"{panel_key}_pending_query"] = None
    run_ids = {panel_key: uuid4().hex for panel_key in pending_queries}
    run_states = {panel_key: {} for panel_key in pending_queries}

    def run_backend(panel_key):
        run_states[panel_key]["result"] = run_comparison(
            mode=panel_key,
            query=pending_queries[panel_key],
            corpus=selected_corpus,
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
    published_results = set()
    while any(worker.is_alive() for worker in workers.values()):
        trace_updated = False
        result_updated = False
        for panel_key, run_id in run_ids.items():
            events = list(TRACE_STORE.read(run_id).get("events") or [])
            if len(events) != len(live_traces[panel_key]):
                live_traces[panel_key] = events
                trace_updated = True

        visible_results = {}
        for panel_key in pending_queries:
            result = run_states[panel_key].get("result")
            if result is not None:
                if panel_key not in published_results:
                    published_results.add(panel_key)
                    result_updated = True
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
        if trace_updated or result_updated:
            render_comparison_workspace(
                next(iter(pending_queries.values())),
                visible_results,
                histories=st.session_state.comparison_history,
                corpus=selected_corpus,
                container=workspace,
            )
        if any(worker.is_alive() for worker in workers.values()):
            sleep(0.08)
    final_results = {}
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
        normalized_result = (
            result.to_dict() if hasattr(result, "to_dict") else result
        )
        st.session_state[f"{panel_key}_result"] = normalized_result
        final_results[panel_key] = normalized_result
    render_comparison_workspace(
        next(iter(pending_queries.values())),
        final_results,
        histories=st.session_state.comparison_history,
        corpus=selected_corpus,
        container=workspace,
    )
