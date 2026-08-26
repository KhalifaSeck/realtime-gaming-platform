import pandas as pd
import streamlit as st

from api_client import get
from styles import game_card, inject_css, tier_badge
st.set_page_config(page_title="Games", page_icon="🎮", layout="wide")
inject_css()

st.markdown("# 🎮 GAMES LIBRARY")

# ---------- Filters ----------
with st.expander("🔧 Filters", expanded=True):
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
    limit = c1.slider("Limit", 12, 500, 60, step=12)
    min_owners = c2.number_input("Min owners", 0, 1_000_000_000, 100_000, step=100_000)
    genre = c3.text_input("Genre contains")
    tier = c4.selectbox("Tier", ["", "superstar", "hit", "mid", "niche", "unknown"])
    view = c5.radio("View", ["Grid", "Table"], horizontal=True)

params = {"limit": limit, "min_owners": min_owners}
if genre:
    params["genre"] = genre
if tier:
    params["tier"] = tier

try:
    data = get("/games", **params)
    games = data["results"]
    st.caption(f"⚡ {len(games)} games")

    if view == "Grid":
        cols = st.columns(3)
        for i, g in enumerate(games):
            with cols[i % 3]:
                st.markdown(game_card(g), unsafe_allow_html=True)
                st.write("")
    else:
        df = pd.DataFrame(games)
        st.dataframe(df, use_container_width=True, height=600)

    # ---------- Detail ----------
    st.divider()
    st.markdown("### 🔍 GAME DETAIL")
    c1, c2 = st.columns([1, 3])
    appid = c1.number_input("Appid", 0, 10_000_000, 730)
    if c1.button("Fetch"):
        try:
            g = get(f"/games/{appid}")
            with c2:
                st.markdown(game_card(g), unsafe_allow_html=True)
                with st.expander("Full detail JSON"):
                    st.json(g)
        except Exception as e:
            c2.error(str(e))
except Exception as e:
    st.error(f"API error: {e}")