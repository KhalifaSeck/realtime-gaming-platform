import pandas as pd
import streamlit as st

from api_client import get
from styles import game_card, inject_css, tier_badge

st.set_page_config(page_title="Knowledge Graph", page_icon="🕸️", layout="wide")
inject_css()

st.markdown("# 🕸️ KNOWLEDGE GRAPH")
st.caption("Explore relations SIMILAR_TO du KG Neo4j via l'API")

c1, c2, c3 = st.columns([1, 1, 1])
appid = c1.number_input("Steam appid", 0, 10_000_000, 730)
limit = c2.slider("Nb similars", 3, 30, 12)
go = c3.button("🔍 FETCH")

if go:
    try:
        detail = get(f"/games/{appid}")

        # Hero du jeu
        st.markdown(f"""
        <div class="card" style="padding:2rem;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <h2 style="margin:0;">🎮 {detail.get('GAME_NAME')}</h2>
            {tier_badge(detail.get('POPULARITY_TIER'))}
          </div>
          <div style="color:#8b949e; margin-top:8px;">
            AppID: <b>{detail.get('STEAM_APP_ID')}</b> · {detail.get('DEVELOPER') or '?'} · {detail.get('PUBLISHER') or '?'}
          </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🎯 POPULARITY", f"{detail.get('POPULARITY_SCORE', 0):.1f}")
        c2.metric("👥 OWNERS", f"{detail.get('OWNERS_ESTIMATE') or 0:,}")
        c3.metric("⭐ REVIEW", f"{detail.get('REVIEW_SCORE') or 0:.1f}")
        c4.metric("💵 PRICE", f"${detail.get('PRICE_USD') or 0:.2f}")

        st.divider()

        # Similars
        st.markdown("### 🕸️ SIMILAR GAMES")
        similar = get(f"/games/{appid}/similar", limit=limit)
        results = similar["results"]

        if not results:
            st.info("Aucun jeu similaire trouve dans le KG.")
        else:
            cols = st.columns(3)
            for i, g in enumerate(results):
                with cols[i % 3]:
                    sim = g.get("similarity", 0)
                    st.markdown(f"""
                    <div class="card">
                      <h4 style="margin:0;">🎮 {g.get('game_name')}</h4>
                      <div style="color:#8b949e; font-size:0.85rem; margin:6px 0;">
                        AppID: <b>{g.get('steam_app_id')}</b>
                      </div>
                      <div style="display:flex; gap:12px; margin-top:8px; font-size:0.9rem;">
                        <span>🎯 <b style="color:#00d9ff;">{g.get('popularity_score', 0):.1f}</b></span>
                        <span>🕸️ <b style="color:#ff00d4;">{sim:.2f}</b></span>
                      </div>
                      <div style="margin-top:8px; color:#8b949e; font-size:0.8rem;">
                        Shared genre: <b>{g.get('shared_genre') or '-'}</b>
                      </div>
                      {tier_badge(g.get('popularity_tier'))}
                    </div>
                    """, unsafe_allow_html=True)
                    st.write("")
    except Exception as e:
        st.error(str(e))