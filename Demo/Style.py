import streamlit as st

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@400&display=swap');

html, body, [class*="css"] {
    font-family: "Hanken Grotesk", sans-serif;
}

.stApp {
    background: #f9f9ff;
    color: #151c27;
}

/* Hide Streamlit default UI */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #f0f3ff;
    border-right: 1px solid #e2bebc;
}

section[data-testid="stSidebar"] > div {
    padding: 24px;
}

.sidebar-title {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 28px;
    color: #151c27;
}

.new-chat {
    width: 100%;
    background: #b1232a;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    margin-bottom: 28px;
}

.new-chat:hover {
    opacity: 0.9;
}

.sidebar-bottom {
    position: fixed;
    bottom: 20px;
    width: 220px;
    border-top: 1px solid #e2bebc;
    padding-top: 16px;
}

.sidebar-link {
    display: block;
    padding: 10px 14px;
    color: #5a403f;
    text-decoration: none;
    border-radius: 8px;
    margin-bottom: 4px;
}

.sidebar-link:hover {
    background: #dce2f3;
    color: #151c27;
}

/* Main header */
.topbar {
    height: 64px;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding: 12px 32px;
    background: #f9f9ff;
    border-bottom: 0;
}

.deploy {
    color: #b1232a;
    font-weight: 700;
    padding: 8px 16px;
    border-radius: 8px;
}

.deploy:hover {
    background: #dce2f3;
}

/* Welcome */
.welcome {
    min-height: calc(100vh - 190px);
    display: flex;
    align-items: center;
    justify-content: center;
}

.welcome-title {
    font-size: 30px;
    line-height: 38px;
    font-weight: 700;
    color: #151c27;
}

/* Chat input */
.chat-wrapper {
    width: 100%;
    max-width: 1440px;
    margin: 0 auto 10px auto;
}

.chat-box {
    background: #f0f3ff;
    border-radius: 12px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    color: #5a403f;
}

div[data-testid="stTextInput"] input {
    background: transparent;
    border: none;
    box-shadow: none;
    color: #151c27;
    font-family: "Hanken Grotesk", sans-serif;
    font-size: 16px;
}

div[data-testid="stTextInput"] input:focus {
    border: none;
    box-shadow: none;
}

div[data-testid="stTextInput"] {
    margin-bottom: 0;
}

/* Buttons */
div.stButton > button {
    border-radius: 8px;
    font-family: "Hanken Grotesk", sans-serif;
    font-weight: 700;
}

.send-button button {
    background: #dce2f3 !important;
    color: #151c27 !important;
    border: none !important;
    min-height: 42px;
}

/* Remove excessive top spacing */
.block-container {
    padding-top: 0.5rem;
    padding-bottom: 1rem;
    max-width: 100%;
}
</style>
"""


def apply_custom_style():
    """ฟังก์ชันสำหรับโหลด Custom CSS ไปยัง Streamlit"""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)