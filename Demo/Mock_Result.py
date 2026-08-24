import streamlit as st

from Component import (
    configure_page,
    render_comparison_input,
    render_comparison_workspace,
    render_topbar,
)
from Style import apply_custom_style


configure_page()
apply_custom_style()

if "comparison_query" not in st.session_state:
    st.session_state.comparison_query = None

render_topbar()
render_comparison_workspace(st.session_state.comparison_query)

prompt = render_comparison_input()

if prompt:
    st.session_state.comparison_query = prompt
    st.rerun()
