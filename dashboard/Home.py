"""Dashboard Home - Hero gaming."""
import streamlit as st
from api_client import get
from config import get_settings
from styles import inject_css, NEON_CYAN, NEON_PINK

st.set_page_config(
    page_title="rtgaming Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ---------- HERO ----------
st.markdown("""
<div class="hero">
  <div style="text-align:center;">
    <h1 style="font-size:4rem; margin:0;">⚡ RTGAMING</h1>
    <div style="color:#8b949e; font-size:1.2rem; letter-spacing:2px; text-transform:uppercase;">
      Realtime Gaming Intelligence Platform
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- Health ----------
try:
    health = get("/health")
    ok_svcs = [k for k, v in health["services"].items() if v == "ok"]
    status_icons = " ".join([f"✅ {s}" for s in ok_svcs])
    st.markdown(
        f'<div class="card" style="text-align:center; color:{NEON_CYAN};"><b>SYSTEMS ONLINE</b> — {status_icons}</div>',
        unsafe_allow_html=True,
    )
except Exception as e:
    st.error(f"❌ API unreachable: {e}")
    st.stop()

st.write("")

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)

for col, path, params, label, icon in [
    (c1, "/games", {"limit": 500}, "GAMES INDEXED", "🎮"),
    (c2, "/trending", {"limit": 200}, "TRENDING NOW", "📈"),
    (c3, "/anomalies/graph", {"limit": 500}, "KG ANOMALIES", "🕸️"),
    (c4, "/anomalies/stream", {"limit": 200}, "STREAM ANOMALIES", "⚡"),
]:
    try:
        data = get(path, **params)
        col.metric(f"{icon} {label}", f"{len(data['results']):,}")
    except Exception:
        col.metric(f"{icon} {label}", "n/a")

st.write("")

# ---------- Feature grid ----------
st.markdown("### 🎯 NAVIGATION")
cols = st.columns(5)
features = [
    ("🎮", "Games", "Browse 10K+ games"),
    ("📈", "Trending", "Live rankings"),
    ("⚠️", "Anomalies", "Detection engine"),
    ("📊", "Market Stats", "Publisher analytics"),
    ("🕸️", "Knowledge Graph", "Similar games"),
]
for col, (icon, name, desc) in zip(cols, features):
    col.markdown(f"""
    <div class="card" style="text-align:center;">
      <div style="font-size:2.5rem;">{icon}</div>
      <div style="color:#00d9ff; font-weight:700; text-transform:uppercase; letter-spacing:1px;">{name}</div>
      <div style="color:#8b949e; font-size:0.85rem; margin-top:5px;">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.caption(f"API: `{get_settings().api_base_url}` · Cache: 30s")