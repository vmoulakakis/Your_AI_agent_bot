import uuid
import streamlit as st

from app.ai import chat_with_memory

st.set_page_config(page_title="Chat", layout="wide")

st.title("💬 Shopping Assistant")

if "chat_session_id" not in st.session_state:
    st.session_state["chat_session_id"] = str(uuid.uuid4())

session_id = st.session_state["chat_session_id"]

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask for product advice, deals, or trends…")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    with st.spinner("Thinking…"):
        reply = chat_with_memory(session_id, user_input)
        st.session_state.setdefault("chat_history", []).append(("user", user_input))
        st.session_state["chat_history"].append(("assistant", reply))

for role, msg in st.session_state.get("chat_history", []):
    if role == "user":
        st.markdown(f"**You:** {msg}")
    else:
        st.markdown(f"**Assistant:** {msg}")