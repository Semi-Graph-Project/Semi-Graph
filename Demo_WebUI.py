import streamlit as st

# ตั้งค่าหน้าเว็บให้เป็น Wide layout และใส่ Title
st.set_page_config(
    page_title="Finance Chatbot - Active Sessions",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
    <style>
    /* ปรับระยะห่างระหว่างตัวเลือกในแนวนอน */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        gap: 16px !important; /* เพิ่มระยะห่างระหว่างปุ่มตามใจชอบ */
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("Finance Chatbot")
    
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        st.toast("สร้าง Chat ใหม่แล้ว!")
        
    st.divider()
    
    # เมนูแถบข้าง
    st.radio(
        "Navigation",
        ["Vector Baseline", "Graph Baseline", "Agentic Vector", "Agentic Graph"],
        index=1,
        label_visibility="collapsed"
    )
    
    st.divider()

st.header("🤖 Welcome to the Finance Chatbot",text_alignment="center")
# --- 3. 2x2 GRID CHAT PANELS ---
row1_col1, row1_col2 = st.columns(2)

# ----- Panel 1: Vector Baseline -----
with row1_col1:
    with st.container(border=True):
        st.subheader("🔴 Vector Baseline")
        st.caption("Tag: Finance Vector")
        
        # Message History
        with st.chat_message("user"):
            st.write("Summarize the Q3 tech sector earnings reports.")
            
        with st.chat_message("assistant"):
            st.write("Here is a summary of Q3 tech sector earnings:")
            st.markdown("- **Cloud Infrastructure:** Growth remains strong (22% YoY average).")
            st.markdown("- **Hardware:** Sluggish consumer demand led to a 4% miss on expectations.")
            
        st.chat_input("Type a message...", key="chat1")

# ----- Panel 2: Graph Baseline -----
with row1_col2:
    with st.container(border=True):
        st.subheader("🔵 Graph Baseline")
        st.caption("Tag: Finance Graph")
        
        with st.chat_message("user"):
            st.write("Review PR #402 for security vulnerabilities.")
            
        with st.chat_message("assistant"):
            st.write("Analysis complete. Found 1 medium severity issue:")
            st.code("// Potential SQL injection risk\nconst query = `SELECT * FROM users WHERE id = ${userId}`;", language="javascript")
            st.caption("Recommendation: Use parameterized queries.")
            
        st.chat_input("Type a message...", key="chat2")

# Row 2
row2_col1, row2_col2 = st.columns(2)

# ----- Panel 3: Agentic Vector -----
with row2_col1:
    with st.container(border=True):
        st.subheader("🟡 Agentic Vector")
        st.caption("Tag: Agentic Vector finance")
        
        with st.chat_message("user"):
            st.write("Ticket #8812: User cannot reset password.")
            
        with st.chat_message("assistant"):
            st.write("Drafted response sent to queue:")
            st.info('"Hi Sarah, I see you\'re having trouble resetting your password. I\'ve sent a direct reset link to your alternate email on file..."')
            
        st.chat_input("Type a message...", key="chat3")

# ----- Panel 4: Agentic Graph Baseline -----
with row2_col2:
    with st.container(border=True):
        st.subheader("🟢 Agentic Graph Baseline")
        st.caption("Tag: Agentic Graph Finance")
        
        with st.chat_message("user"):
            st.write("Generate 3 taglines for the new 'Orbit' smartwatch campaign.")
            
        with st.chat_message("assistant"):
            st.markdown('1. "Your universe, on your wrist."')
            st.markdown('2. "Orbit: Time reimagined."')
            st.markdown('3. "Sync with your world."')
            
        st.chat_input("Type a message...", key="chat4")