import streamlit as st

PAGE_CONFIG = {
    "page_title": "Finance Chatbot",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}


def configure_page():
    """ตั้งค่าเริ่มต้นของ Streamlit Page"""
    st.set_page_config(**PAGE_CONFIG)


def render_sidebar():
    """Component สำหรับ Sidebar"""
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-title">Finance Chatbot</div>',
            unsafe_allow_html=True,
        )

        if st.button("＋ New Chat", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.rerun()


def render_Topbar():
    """Component สำหรับ Top Bar"""
    st.markdown(
        """
        <div class="topbar">
            <span class="deploy">Deploy</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_welcome_screen():
    """Component สำหรับหน้า Welcome ตอนยังไม่มีข้อความ"""
    st.markdown(
        """
        <div class="welcome">
            <div class="welcome-title">
                🤖 &nbsp; Welcome to the Finance Chatbot
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_messages(messages):
    """Component สำหรับแสดงประวัติแชท"""
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def render_chat_input():
    """Component สำหรับช่องพิมพ์ข้อความ"""
    return st.chat_input("Type a message...")