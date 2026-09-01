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


def _to_list(resp):
    """Normalise la reponse en liste de dicts, quelle que soit sa forme."""
    if resp is None:
        return []
    if isinstance(resp, list):
        return [x for x in resp if isinstance(x, dict)]
    if isinstance(resp, dict):
        for k in ("data", "stats", "items", "results"):
            if k in resp and isinstance(resp[k], list):
                return [x for x in resp[k] if isinstance(x, dict)]
        return [v for v in resp.values() if isinstance(v, dict)]
    return []


def _to_num(v):
    """Convertit str/None en float, fallback 0."""
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


# ---------- Sidebar refresh ----------
refresh_seconds = st.sidebar.slider("Refresh interval (sec)", 3, 30, 5)
st.sidebar.caption(f"⏱️ Refreshes every {refresh_seconds}s")

# ---------- Corps ----------
placeholder = st.empty()

with placeholder.container():
    # ---- Fetch ----
    purchases_raw = _live_get("/live/all-stats", topic="purchases", limit=500)
    reviews_raw = _live_get("/live/all-stats", topic="reviews", limit=500)
    sessions_raw = _live_get("/live/all-stats", topic="sessions", limit=500)
    wishlist_raw = _live_get("/live/all-stats", topic="wishlist", limit=500)

    # ---- Normalisation defensive ----
    purchases = _to_list(purchases_raw)
    reviews = _to_list(reviews_raw)
    sessions = _to_list(sessions_raw)
    wishlist = _to_list(wishlist_raw)

    # ---- KPIs ----
    col1, col2, col3, col4 = st.columns(4)
    total_revenue = sum(_to_num(x.get("revenue_net_usd")) for x in purchases)
    total_purchases = sum(int(_to_num(x.get("num_purchases"))) for x in purchases)
    total_reviews = sum(int(_to_num(x.get("num_reviews"))) for x in reviews)
    total_sessions = sum(int(_to_num(x.get("num_sessions"))) for x in sessions)

    col1.metric("💰 Revenue (last window)", f"${total_revenue:,.2f}", f"{total_purchases} purchases")
    col2.metric("⭐ Reviews", total_reviews)
    col3.metric("🎯 Active Sessions", total_sessions)
    col4.metric("📥 Wishlist Events", len(wishlist))

    st.divider()

    # ---- Anomalies ----
    st.subheader("🚨 Streaming Anomalies (last window)")
    anomalies_raw = _live_get("/anomalies/stream", limit=20)
    anomalies = _to_list(anomalies_raw)
    if anomalies:
        st.dataframe(pd.DataFrame(anomalies), use_container_width=True, height=250)
    else:
        st.info("No anomalies detected in the last window.")

    st.divider()

    # ---- Top games par topic ----
    tab1, tab2, tab3, tab4 = st.tabs(
        ["💰 Top Revenue", "⭐ Top Reviews", "🎯 Top Sessions", "📥 Top Wishlist"]
    )

    with tab1:
        if purchases:
            df = pd.DataFrame(purchases)
            if "revenue_net_usd" in df.columns:
                df["revenue_net_usd"] = pd.to_numeric(df["revenue_net_usd"], errors="coerce")
                df = df.sort_values("revenue_net_usd", ascending=False)
            st.dataframe(df.head(15), use_container_width=True, height=350)
        else:
            st.info("No purchase data yet.")

    with tab2:
        if reviews:
            df = pd.DataFrame(reviews)
            if "num_reviews" in df.columns:
                df["num_reviews"] = pd.to_numeric(df["num_reviews"], errors="coerce")
                df = df.sort_values("num_reviews", ascending=False)
            st.dataframe(df.head(15), use_container_width=True, height=350)
        else:
            st.info("No review data yet.")

    with tab3:
        if sessions:
            df = pd.DataFrame(sessions)
            if "num_sessions" in df.columns:
                df["num_sessions"] = pd.to_numeric(df["num_sessions"], errors="coerce")
                df = df.sort_values("num_sessions", ascending=False)
            st.dataframe(df.head(15), use_container_width=True, height=350)
        else:
            st.info("No session data yet.")

    with tab4:
        if wishlist:
            st.dataframe(pd.DataFrame(wishlist).head(15), use_container_width=True, height=350)
        else:
            st.info("No wishlist data yet.")

    st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")

# Auto-refresh
time.sleep(refresh_seconds)
st.rerun()