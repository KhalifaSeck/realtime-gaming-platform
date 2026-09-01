"""
Page Live Streaming - Redis + streaming anomalies.
Bypass le cache api_client car on veut du vraiment live.
"""
from __future__ import annotations

import time

import httpx
import pandas as pd
import streamlit as st

from config import get_settings

st.set_page_config(page_title="Live Streaming", page_icon="🎮", layout="wide")

st.title("🎮 Live Streaming — Real-Time Gaming Events")
st.caption("Powered by Kafka + Spark + Redis • No cache, direct API calls")


# ---------- Client httpx sans cache ----------
def _live_get(path: str, **params):
    base = get_settings().api_base_url
    with httpx.Client(base_url=base, timeout=10.0) as c:
        try:
            r = c.get(path, params=params)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            st.warning(f"API {path} error: {e}")
            return None


# ---------- Sidebar refresh ----------
refresh_seconds = st.sidebar.slider("Refresh interval (sec)", 3, 30, 5)
st.sidebar.caption(f"⏱️ Refreshes every {refresh_seconds}s")

# ---------- Corps ----------
placeholder = st.empty()

with placeholder.container():
    purchases = _live_get("/live/all-stats", topic="purchases", limit=500) or []
    reviews = _live_get("/live/all-stats", topic="reviews", limit=500) or []
    sessions = _live_get("/live/all-stats", topic="sessions", limit=500) or []
    wishlist = _live_get("/live/all-stats", topic="wishlist", limit=500) or []

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    total_revenue = sum(float(x.get("revenue_net_usd", 0) or 0) for x in purchases)
    total_purchases = sum(int(x.get("num_purchases", 0) or 0) for x in purchases)
    total_reviews = sum(int(x.get("num_reviews", 0) or 0) for x in reviews)
    total_sessions = sum(int(x.get("num_sessions", 0) or 0) for x in sessions)

    col1.metric("💰 Revenue (last window)", f"${total_revenue:,.2f}", f"{total_purchases} purchases")
    col2.metric("⭐ Reviews", total_reviews)
    col3.metric("🎯 Active Sessions", total_sessions)
    col4.metric("📥 Wishlist Events", len(wishlist))

    st.divider()

    # Anomalies
    st.subheader("🚨 Streaming Anomalies (last window)")
    anomalies = _live_get("/anomalies/stream", limit=20) or []
    if anomalies:
        st.dataframe(pd.DataFrame(anomalies), use_container_width=True, height=250)
    else:
        st.info("No anomalies detected in the last window.")

    st.divider()

    # Top games par topic
    tab1, tab2, tab3, tab4 = st.tabs(
        ["💰 Top Revenue", "⭐ Top Reviews", "🎯 Top Sessions", "📥 Top Wishlist"]
    )

    with tab1:
        if purchases:
            df = pd.DataFrame(purchases)
            df["revenue_net_usd"] = pd.to_numeric(df.get("revenue_net_usd"), errors="coerce")
            df = df.sort_values("revenue_net_usd", ascending=False).head(15)
            st.dataframe(df, use_container_width=True, height=350)
        else:
            st.info("No purchase data yet.")

    with tab2:
        if reviews:
            df = pd.DataFrame(reviews)
            df["num_reviews"] = pd.to_numeric(df.get("num_reviews"), errors="coerce")
            df = df.sort_values("num_reviews", ascending=False).head(15)
            st.dataframe(df, use_container_width=True, height=350)
        else:
            st.info("No review data yet.")

    with tab3:
        if sessions:
            df = pd.DataFrame(sessions)
            df["num_sessions"] = pd.to_numeric(df.get("num_sessions"), errors="coerce")
            df = df.sort_values("num_sessions", ascending=False).head(15)
            st.dataframe(df, use_container_width=True, height=350)
        else:
            st.info("No session data yet.")

    with tab4:
        if wishlist:
            st.dataframe(pd.DataFrame(wishlist), use_container_width=True, height=350)
        else:
            st.info("No wishlist data yet.")

    st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")

# Auto-refresh
time.sleep(refresh_seconds)
st.rerun()