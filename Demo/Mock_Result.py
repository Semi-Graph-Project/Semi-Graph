import streamlit as st

from Component import (
    configure_page,
    render_sidebar,
    render_Topbar,
    render_welcome_screen,
    render_chat_messages,
    render_chat_input,
)
from Style import apply_custom_style

# -----------------------------
# Page configuration & Style
# -----------------------------
configure_page()
apply_custom_style()

# -----------------------------
# Session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "new_chat" not in st.session_state:
    st.session_state.new_chat = False

# -----------------------------
# UI Components Render
# -----------------------------
render_sidebar()
render_Topbar()

# แสดงผล Content หลักตามสถานะข้อความ
if not st.session_state.messages:
    render_welcome_screen()
else:
    render_chat_messages(st.session_state.messages)

# -----------------------------
# Chat input logic
# -----------------------------
prompt = render_chat_input()

if prompt:
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Temporary response (Replace with your LLM / RAG implementation)
    response = f"You asked: **{prompt}**"

    st.session_state.messages.append({"role": "assistant", "content": response})

    st.rerun()