import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from api_client import get
from styles import inject_css, viral_badge

st.set_page_config(page_title="Trending", page_icon="📈", layout="wide")
inject_css()

st.markdown("# 📈 TRENDING NOW")

c1, c2 = st.columns([2, 1])
limit = c1.slider("Top N", 5, 200, 30)
anomaly_only = c2.checkbox("⚡ Only anomalies", value=False)

try:
    data = get("/trending", limit=limit, with_anomaly_only=anomaly_only)
    df = pd.DataFrame(data["results"])
    if df.empty:
        st.info("No trending games — lance des producers et attends ~1 min.")
        st.stop()

    # ---------- PODIUM ----------
    st.markdown("### 🏆 PODIUM")
    top3 = df.head(3)
    cols = st.columns(3)
    medals = ["🥇", "🥈", "🥉"]
    for i, (col, g) in enumerate(zip(cols, top3.to_dict("records"))):
        flags = []
        if g.get("HAD_VIRAL_PURCHASES_PERIOD"): flags.append("🔥 VIRAL")
        if g.get("HAD_REVIEW_BOMB_PERIOD"):     flags.append("💣 BOMB")
        if g.get("HAD_CCU_SPIKE_PERIOD"):       flags.append("⚡ CCU")
        badge_html = " ".join([f'<span class="badge badge-viral">{f}</span>' for f in flags])
        col.markdown(f"""
        <div class="card" style="text-align:center; padding:2rem;">
          <div style="font-size:3rem;">{medals[i]}</div>
          <h3 style="margin:0;">{g['GAME_NAME']}</h3>
          <div style="color:#00d9ff; font-size:2rem; font-family:'Orbitron', sans-serif;">
            {g['TRENDING_SCORE']:.0f}
          </div>
          <div style="color:#8b949e;">{g.get('PRIMARY_GENRE') or '-'}</div>
          <div style="margin-top:8px;">{badge_html}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ---------- Chart ----------
    st.markdown("### 📊 TRENDING SCORE — TOP 25")
    top25 = df.head(25)
    fig = go.Figure(go.Bar(
        x=top25["GAME_NAME"],
        y=top25["TRENDING_SCORE"],
        marker=dict(
            color=top25["TRENDING_SCORE"],
            colorscale=[[0, "#7c3aed"], [0.5, "#00d9ff"], [1, "#ff00d4"]],
            showscale=False,
        ),
        text=top25["TRENDING_SCORE"].round(0),
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=-45,
        height=500,
        margin=dict(t=20, b=100),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### 📋 FULL RANKING")
    st.dataframe(df, use_container_width=True, height=500)
except Exception as e:
    st.error(str(e))