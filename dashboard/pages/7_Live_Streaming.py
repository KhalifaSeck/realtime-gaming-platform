"""
Page Live Streaming - dashboard temps reel Kafka+Spark+Redis.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

from config import get_settings

st.set_page_config(page_title="Live Streaming", page_icon="🎮", layout="wide")

st.markdown(
    """
    <style>
    .stAlert { border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎮 Live Streaming — Real-Time Gaming Events")
st.caption("Powered by Kafka + Spark Structured Streaming + Redis • Auto-refresh")


# ============================================================
# Helpers
# ============================================================
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


def _parse_all_stats(resp) -> pd.DataFrame:
    """Normalise /live/all-stats [{key, data: json-str}, ...] -> DataFrame."""
    if not resp:
        return pd.DataFrame()
    if isinstance(resp, dict):
        for k in ("data", "stats", "items", "results"):
            if k in resp and isinstance(resp[k], list):
                resp = resp[k]
                break
        else:
            resp = list(resp.values())

    rows = []
    for item in resp:
        if not isinstance(item, dict):
            continue
        payload = item.get("data")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                continue
        if isinstance(payload, dict):
            payload["_key"] = item.get("key", "")
            rows.append(payload)
    return pd.DataFrame(rows)


def _extract_list(resp):
    """Extrait une liste de dicts de n'importe quelle reponse API."""
    if resp is None:
        return []
    if isinstance(resp, list):
        return [x for x in resp if isinstance(x, dict)]
    if isinstance(resp, dict):
        for k in ("data", "anomalies", "results", "items"):
            v = resp.get(k)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
            if isinstance(v, str):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [x for x in parsed if isinstance(x, dict)]
                except Exception:
                    pass
    return []


def _first_col(df: pd.DataFrame, candidates: list) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _to_num(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def _bar_top(df: pd.DataFrame, num_col: str, color_scale: str, height: int = 380):
    top = df.nlargest(len(df), num_col).sort_values(num_col)
    fig = px.bar(
        top, x=num_col, y="game_id",
        orientation="h", text=num_col,
        color=num_col, color_continuous_scale=color_scale,
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis=dict(type="category"), height=height,
        margin=dict(l=0, r=0, t=10, b=10), coloraxis_showscale=False,
    )
    return fig


# ============================================================
# Sidebar
# ============================================================
st.sidebar.header("⚙️ Settings")
refresh_seconds = st.sidebar.slider("Refresh interval (sec)", 3, 30, 5)
top_n = st.sidebar.slider("Top N games", 5, 20, 10)
st.sidebar.caption(f"⏱️ Every {refresh_seconds}s • Redis TTL: 10 min")


# ============================================================
# Corps
# ============================================================
placeholder = st.empty()

with placeholder.container():
    # ---- Fetch ----
    df_purchases = _parse_all_stats(_live_get("/live/all-stats", topic="purchases", limit=500))
    df_reviews = _parse_all_stats(_live_get("/live/all-stats", topic="reviews", limit=500))
    df_sessions = _parse_all_stats(_live_get("/live/all-stats", topic="sessions", limit=500))
    df_wishlist = _parse_all_stats(_live_get("/live/all-stats", topic="wishlist", limit=500))

    # ---- Detect numeric columns per topic ----
    p_col = _first_col(df_purchases, ["revenue_net_usd", "revenue", "num_purchases"])
    r_col = _first_col(df_reviews, ["num_reviews", "reviews_count", "num_events"])
    #s_col = _first_col(df_sessions, ["num_sessions", "active_sessions", "num_active", "sessions_count"])
    # Sessions : calcule total_activity = starts + ends
    if not df_sessions.empty and "num_starts" in df_sessions.columns and "num_ends" in df_sessions.columns:
        df_sessions["num_starts"] = pd.to_numeric(df_sessions["num_starts"], errors="coerce").fillna(0)
        df_sessions["num_ends"] = pd.to_numeric(df_sessions["num_ends"], errors="coerce").fillna(0)
        df_sessions["total_activity"] = (df_sessions["num_starts"] + df_sessions["num_ends"]).astype(int)
        s_col = "total_activity"
    else:
        s_col = _first_col(df_sessions, ["num_starts", "active_sessions", "num_active", "num_sessions"])
    w_col = _first_col(df_wishlist, ["net_added", "num_added", "num_events", "wishlist_net"])

    df_purchases = _to_num(df_purchases, ["num_purchases", "revenue_net_usd", "game_id"])
    df_reviews = _to_num(df_reviews, ["num_reviews", "avg_rating", "game_id"])
    df_sessions = _to_num(df_sessions, [s_col, "game_id"]) if s_col else df_sessions
    df_wishlist = _to_num(df_wishlist, [w_col, "game_id"]) if w_col else df_wishlist

    # ---- KPIs top ----
    total_revenue = float(df_purchases["revenue_net_usd"].sum()) if "revenue_net_usd" in df_purchases else 0
    total_purchases = int(df_purchases["num_purchases"].sum()) if "num_purchases" in df_purchases else 0
    total_reviews = int(df_reviews["num_reviews"].sum()) if "num_reviews" in df_reviews else 0
    total_sessions = int(df_sessions[s_col].sum()) if s_col else 0
    total_wishlist = int(df_wishlist[w_col].sum()) if w_col else len(df_wishlist)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Revenue (live)", f"${total_revenue:,.2f}", f"{total_purchases} purchases")
    c2.metric("🛒 Purchases", f"{total_purchases:,}")
    c3.metric("⭐ Reviews", f"{total_reviews:,}")
    c4.metric("🎯 Sessions", f"{total_sessions:,}")
    c5.metric("📥 Wishlist", f"{total_wishlist:,}")

    st.divider()

    # ---- Live pulse ----
    st.subheader("📊 Live pulse — events per topic")
    pulse_df = pd.DataFrame({
        "Topic": ["Purchases", "Reviews", "Sessions", "Wishlist"],
        "Events": [total_purchases, total_reviews, total_sessions, total_wishlist],
    })
    fig_pulse = px.bar(
        pulse_df, x="Topic", y="Events", text="Events",
        color="Topic",
        color_discrete_map={
            "Purchases": "#22c55e", "Reviews": "#eab308",
            "Sessions": "#3b82f6", "Wishlist": "#a855f7",
        },
    )
    fig_pulse.update_traces(textposition="outside")
    fig_pulse.update_layout(showlegend=False, height=280, margin=dict(t=20, b=20))
    st.plotly_chart(fig_pulse, use_container_width=True)

    st.divider()

    # ---- Top N par topic ----
    st.subheader(f"🏆 Top {top_n} games (current window)")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("### 💰 Top revenue")
        if not df_purchases.empty and "revenue_net_usd" in df_purchases:
            top_p = df_purchases.nlargest(top_n, "revenue_net_usd")
            st.plotly_chart(_bar_top(top_p, "revenue_net_usd", "greens"), use_container_width=True)
        else:
            st.info("No purchase data yet.")

    with colB:
        st.markdown("### ⭐ Top reviews")
        if not df_reviews.empty and r_col:
            top_r = df_reviews.nlargest(top_n, r_col)
            st.plotly_chart(_bar_top(top_r, r_col, "ylgn"), use_container_width=True)
        else:
            st.info("No review data yet.")

    colC, colD = st.columns(2)

    with colC:
        st.markdown("### 🎯 Top active sessions")
        if not df_sessions.empty and s_col:
            top_s = df_sessions.nlargest(top_n, s_col)
            st.plotly_chart(_bar_top(top_s, s_col, "blues"), use_container_width=True)
        else:
            st.info("No session data yet.")

    with colD:
        st.markdown("### 📥 Top wishlist adds")
        if not df_wishlist.empty and w_col:
            top_w = df_wishlist.nlargest(top_n, w_col)
            st.plotly_chart(_bar_top(top_w, w_col, "purples"), use_container_width=True)
        else:
            st.info("No wishlist data yet.")

    st.divider()

    # ---- Anomalies ----
    st.subheader("🚨 Streaming Anomalies")
    anomalies_list = _extract_list(_live_get("/anomalies/stream", limit=30))

    if anomalies_list:
        df_anom = pd.DataFrame(anomalies_list)
        type_col = _first_col(df_anom, ["anomaly_type", "ANOMALY_TYPE"])

        if type_col:
            counts = df_anom[type_col].value_counts()
            cols = st.columns(min(4, max(1, len(counts))))
            for i, (atype, count) in enumerate(counts.items()):
                label = atype.replace("is_", "").replace("_", " ").title()
                icon = {
                    "viral purchases": "🔥",
                    "viral wishlist": "📥",
                    "review bomb": "⭐",
                    "ccu spike": "🎯",
                }.get(label.lower(), "⚠️")
                cols[i % len(cols)].metric(f"{icon} {label}", int(count))

            counts_df = counts.reset_index()
            counts_df.columns = ["anomaly_type", "count"]
            fig_anom = px.bar(
                counts_df, x="anomaly_type", y="count", text="count",
                color="anomaly_type",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_anom.update_traces(textposition="outside")
            fig_anom.update_layout(
                showlegend=False, height=280,
                margin=dict(t=20, b=20),
                xaxis_title="", yaxis_title="Count (last window)",
            )
            st.plotly_chart(fig_anom, use_container_width=True)

        with st.expander(f"📋 View all {len(df_anom)} anomalies"):
            st.dataframe(df_anom, use_container_width=True, height=350)
    else:
        st.success("✅ No anomalies detected.")

    st.divider()

    # ---- Timestamp ----
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.caption(f"⏱️ Last refresh: {now_utc} • Next in {refresh_seconds}s")

# Auto-refresh
time.sleep(refresh_seconds)
st.rerun()