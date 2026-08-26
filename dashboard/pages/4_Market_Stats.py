import pandas as pd
import plotly.express as px
import streamlit as st

from api_client import get
from styles import inject_css

st.set_page_config(page_title="Market Stats", page_icon="📊", layout="wide")
inject_css()

st.markdown("# 📊 MARKET STATS")

tab_g, tab_p, tab_pr = st.tabs(["🎭 GENRES", "🏢 PUBLISHERS", "💰 PRICES"])

DARK = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

with tab_g:
    try:
        data = get("/genres", limit=50)
        df = pd.DataFrame(data["results"])
        c1, c2, c3 = st.columns(3)
        c1.metric("🎭 GENRES", len(df))
        c2.metric("🎮 TOTAL GAMES", int(df["NUM_GAMES"].sum()))
        c3.metric("👥 TOTAL OWNERS", f"{int(df['TOTAL_OWNERS'].sum()):,}")

        # Sunburst
        fig = px.sunburst(
            df.head(15), path=["GENRE"], values="TOTAL_OWNERS",
            color="POSITIVE_RATE_PCT",
            color_continuous_scale=["#7c3aed", "#00d9ff", "#00ff88"],
            title="Owners by Genre (color = positive rate %)",
        )
        fig.update_layout(**DARK, height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df, use_container_width=True, height=350)
    except Exception as e:
        st.error(str(e))

with tab_p:
    limit = st.slider("Top publishers", 10, 200, 30)
    try:
        data = get("/publishers", limit=limit)
        df = pd.DataFrame(data["results"])

        # Bubble chart
        fig = px.scatter(
            df, x="NUM_GAMES", y="TOTAL_OWNERS",
            size="MARKET_SHARE_OWNERS_PCT",
            color="AVG_REVIEW_SCORE",
            hover_name="PUBLISHER",
            color_continuous_scale=["#ff3860", "#ffa500", "#00ff88"],
            size_max=60,
            title="Publisher landscape (size = market share)",
        )
        fig.update_layout(**DARK, height=550)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df, use_container_width=True, height=400)
    except Exception as e:
        st.error(str(e))

with tab_pr:
    try:
        data = get("/stats/prices")
        df = pd.DataFrame(data["results"])
        c1, c2 = st.columns(2)

        fig1 = px.pie(
            df, names="PRICE_TIER", values="TOTAL_OWNERS",
            hole=0.55,
            color_discrete_sequence=["#00d9ff", "#7c3aed", "#ff00d4", "#00ff88", "#ffa500"],
            title="Owners share by tier",
        )
        fig1.update_layout(**DARK, height=400)
        c1.plotly_chart(fig1, use_container_width=True)

        fig2 = px.bar(
            df.sort_values("AVG_POPULARITY_SCORE", ascending=False),
            x="PRICE_TIER", y="AVG_POPULARITY_SCORE",
            color="AVG_POPULARITY_SCORE",
            color_continuous_scale=["#7c3aed", "#00d9ff", "#ff00d4"],
            title="Avg popularity by price tier",
        )
        fig2.update_layout(**DARK, height=400)
        c2.plotly_chart(fig2, use_container_width=True)

        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(str(e))