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
    .kpi-big { font-size: 2rem; font-weight: 700; }
    .kpi-lbl { font-size: 0.85rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }
    .stAlert { border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎮 Live Streaming — Real-Time Gaming Events")
st.caption("Powered by Kafka + Spark Structured Streaming + Redis • Auto-refresh")


# ---------- Helpers ----------
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
    """
    Normalise la reponse /live/all-stats en DataFrame.
    Le format attendu : [{key, data: "json string"}, ...]
    """
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


def _to_num(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


# ---------- Sidebar ----------
st.sidebar.header("⚙️ Settings")
refresh_seconds = st.sidebar.slider("Refresh interval (sec)", 3, 30, 5)
top_n = st.sidebar.slider("Top N games", 5, 20, 10)
st.sidebar.caption(f"⏱️ Every {refresh_seconds}s • Redis TTL: 10 min")

# ---------- Layout ----------
placeholder = st.empty()

with placeholder.container():
    # ==================== Fetch ====================
    df_purchases = _parse_all_stats(_live_get("/live/all-stats", topic="purchases", limit=500))
    df_reviews = _parse_all_stats(_live_get("/live/all-stats", topic="reviews", limit=500))
    df_sessions = _parse_all_stats(_live_get("/live/all-stats", topic="sessions", limit=500))
    df_wishlist = _parse_all_stats(_live_get("/live/all-stats", topic="wishlist", limit=500))

    df_purchases = _to_num(df_purchases, ["num_purchases", "revenue_net_usd", "game_id"])
    df_reviews = _to_num(df_reviews, ["num_reviews", "avg_rating", "game_id"])
    df_sessions = _to_num(df_sessions, ["num_sessions", "avg_duration_sec", "game_id"])
    df_wishlist = _to_num(df_wishlist, ["num_events", "game_id"])

    # ==================== KPIs top ====================
    total_revenue = float(df_purchases["revenue_net_usd"].sum()) if "revenue_net_usd" in df_purchases else 0
    total_purchases = int(df_purchases["num_purchases"].sum()) if "num_purchases" in df_purchases else 0
    total_reviews = int(df_reviews["num_reviews"].sum()) if "num_reviews" in df_reviews else 0
    total_sessions = int(df_sessions["num_sessions"].sum()) if "num_sessions" in df_sessions else 0
    total_wishlist = int(df_wishlist["num_events"].sum()) if "num_events" in df_wishlist else len(df_wishlist)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Revenue (live)", f"${total_revenue:,.2f}", f"{total_purchases} purchases")
    c2.metric("🛒 Purchases", f"{total_purchases:,}")
    c3.metric("⭐ Reviews", f"{total_reviews:,}")
    c4.metric("🎯 Sessions", f"{total_sessions:,}")
    c5.metric("📥 Wishlist", f"{total_wishlist:,}")

    st.divider()

    # ==================== Live pulse par topic ====================
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

    # ==================== 2 colonnes : top games ====================
    st.subheader(f"🏆 Top {top_n} games (current window)")
    colA, colB = st.columns(2)

    # --- Purchases ---
    with colA:
        st.markdown("### 💰 Top revenue")
        if not df_purchases.empty and "revenue_net_usd" in df_purchases:
            top_p = df_purchases.nlargest(top_n, "revenue_net_usd")[
                ["game_id", "num_purchases", "revenue_net_usd", "updated_at"]
            ]
            fig = px.bar(
                top_p.sort_values("revenue_net_usd"),
                x="revenue_net_usd", y="game_id",
                orientation="h", text="revenue_net_usd",
                color="revenue_net_usd", color_continuous_scale="greens",
            )
            fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
            fig.update_layout(
                yaxis=dict(type="category"), height=380,
                margin=dict(l=0, r=0, t=10, b=10), coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No purchase data.")

    # --- Reviews ---
    with colB:
        st.markdown("### ⭐ Top reviews")
        if not df_reviews.empty and "num_reviews" in df_reviews:
            top_r = df_reviews.nlargest(top_n, "num_reviews")
            fig = px.bar(
                top_r.sort_values("num_reviews"),
                x="num_reviews", y="game_id",
                orientation="h", text="num_reviews",
                color="num_reviews", color_continuous_scale="yellowgreen",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                yaxis=dict(type="category"), height=380,
                margin=dict(l=0, r=0, t=10, b=10), coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No review data.")

    colC, colD = st.columns(2)

    # --- Sessions ---
    with colC:
        st.markdown("### 🎯 Top active sessions")
        if not df_sessions.empty and "num_sessions" in df_sessions:
            top_s = df_sessions.nlargest(top_n, "num_sessions")
            fig = px.bar(
                top_s.sort_values("num_sessions"),
                x="num_sessions", y="game_id",
                orientation="h", text="num_sessions",
                color="num_sessions", color_continuous_scale="blues",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                yaxis=dict(type="category"), height=380,
                margin=dict(l=0, r=0, t=10, b=10), coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No session data.")

    # --- Wishlist ---
    with colD:
        st.markdown("### 📥 Top wishlist adds")
        if not df_wishlist.empty:
            num_col = next(
                (c for c in ("num_events", "num_adds", "wishlist_net") if c in df_wishlist.columns),
                None,
            )
            if num_col:
                top_w = df_wishlist.nlargest(top_n, num_col)
                fig = px.bar(
                    top_w.sort_values(num_col),
                    x=num_col, y="game_id",
                    orientation="h", text=num_col,
                    color=num_col, color_continuous_scale="purples",
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    yaxis=dict(type="category"), height=380,
                    margin=dict(l=0, r=0, t=10, b=10), coloraxis_showscale=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.dataframe(df_wishlist.head(top_n), use_container_width=True, height=380)
        else:
            st.info("No wishlist data.")

    st.divider()

    # ==================== Anomalies ====================
    st.subheader("🚨 Streaming Anomalies")
    anomalies = _live_get("/anomalies/stream", limit=30) or []
    if isinstance(anomalies, dict):
        anomalies = anomalies.get("data") or list(anomalies.values())
    if anomalies:
        df_anom = pd.DataFrame(anomalies)
        # KPI cards par type d'anomalie
        if "anomaly_type" in df_anom.columns:
            counts = df_anom["anomaly_type"].value_counts()
            cols = st.columns(min(4, max(1, len(counts))))
            for i, (atype, count) in enumerate(counts.items()):
                cols[i % len(cols)].metric(f"⚠️ {atype}", int(count))
        st.dataframe(df_anom, use_container_width=True, height=300)
    else:
        st.success("✅ No anomalies detected.")

    st.divider()

    # ==================== Timestamp ====================
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.caption(f"⏱️ Last refresh: {now_utc} • Next in {refresh_seconds}s")

# Auto-refresh
time.sleep(refresh_seconds)
st.rerun()