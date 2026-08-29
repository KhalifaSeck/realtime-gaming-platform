"""Chat interactif avec l'agent Sentinel."""
import httpx
import streamlit as st

from styles import inject_css
import os

SENTINEL_URL = os.environ.get("SENTINEL_URL", "http://localhost:8888")

st.set_page_config(page_title="Sentinel AI", page_icon="🤖", layout="wide")
inject_css()

st.markdown("# 🤖 SENTINEL AI")
st.caption("Ton agent gaming — powered by LangGraph + Ollama Qwen3")

# ---------- Sidebar : exemples ----------
with st.sidebar:
    st.markdown("### 💡 EXEMPLES")
    examples = [
        "What are the top 3 trending games right now?",
        "Any review bombs detected recently?",
        "Which publishers dominate the market?",
        "Show me games similar to Counter-Strike (appid 730)",
        "Give me a market analysis of RPG genre",
        "What's happening live for game 730?",
        "Any viral purchase spikes in the last 24h?",
        "Compare Warner Bros vs Rockstar Games",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:20]}", use_container_width=True):
            st.session_state.pending_question = ex
            st.rerun()

    st.divider()
    st.markdown("### ⚙️ CONFIG")
    st.code(f"Server: {SENTINEL_URL}")
    if st.button("🗑️ Clear history"):
        st.session_state.messages = []
        st.rerun()

# ---------- Session state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ---------- Affichage historique ----------
for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role, avatar="🤖" if role == "assistant" else "🎮"):
        st.markdown(msg["content"])

# ---------- Nouvelle question ----------
prompt = st.chat_input("Ask Sentinel about your gaming platform...")

# Handle example click
if st.session_state.pending_question and not prompt:
    prompt = st.session_state.pending_question
    st.session_state.pending_question = None

if prompt:
    # Display user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🎮"):
        st.markdown(prompt)

    # Call Sentinel
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Sentinel is analyzing..."):
            try:
                r = httpx.post(f"{SENTINEL_URL}/ask", json={"question": prompt}, timeout=120.0)
                r.raise_for_status()
                answer = r.json()["answer"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except httpx.ConnectError:
                err = f"❌ Sentinel server unreachable at {SENTINEL_URL}. Start it with:\n\n```\ncd sentinel && uvicorn src.server:app --port 8888\n```"
                st.error(err)
            except Exception as e:
                st.error(f"❌ Error: {e}")