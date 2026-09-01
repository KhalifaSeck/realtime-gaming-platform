"""
Page Streaming History - Time series from Snowflake ANALYTICS.STREAM_*_AGG.
"""
from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from config import get_settings

st.set_page_config(page_title="Streaming History", page_icon="📈", layout="wide")

st.title("📈 Streaming History — Historical Trends")
st.caption("Time series from Snowflake ANALYTICS.STREAM_*_AGG • Refreshed every 5 min via Airflow")


# ---------- Helpers ----------
def _api_get(path: str, **params):
    base = get_settings().api_base_url
    with httpx.Client(base_url=base, timeout=20.0) as c:
        try:
            r = c.get(path, params=params)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            st.warning(f"API {path} error: {e}")
            return []


def _to_df(resp) -> pd.DataFrame:
    if not resp:
        return pd.DataFrame()
    if isinstance(resp, dict):
        for k in ("data", "results", "items"):
            if k in resp and isinstance(resp[k], list):
                resp = resp[k]
                break
        else:
            resp = list(resp.values())
    if not isinstance(resp, list):
        return pd.DataFrame()
    df = pd.DataFrame([x for x in resp if isinstance(x, dict)])
    if "HOUR" in df.columns:
        df["HOUR"] = pd.to_datetime(df["HOUR"], errors="coerce")
    if "hour" in df.columns:
        df["hour"] = pd.to_datetime(df["hour"], errors="coerce")
    return df


# ---------- Sidebar ----------
st.sidebar.header("⚙️ Time Range")
hours = st.sidebar.select_slider(
    "Look-back window (hours)",
    options=[1, 3, 6, 12, 24, 48, 72, 168],
    value=24,
)
st.sidebar.caption(f"⏱️ Last {hours}h • Data lag: ~5-10 min")

# ---------- Fetch ----------
with st.spinner("Loading history..."):
    df_p = _to_df(_api_get("/history/purchases", hours=hours))
    df_r = _to_df(_api_get("/history/reviews", hours=hours))
    df_s = _to_df(_api_get("/history/sessions", hours=hours))
    df_w = _to_df(_api_get("/history/wishlist", hours=hours))

# ---------- KPIs ----------
def _sum(df, col):
    col_upper = col.upper()
    for c in (col, col_upper):
        if c in df.columns:
            return float(pd.to_numeric(df[c], errors="coerce").sum())
    return 0.0


total_revenue = _sum(df_p, "revenue")
total_purchases = int(_sum(df_p, "purchases"))
total_reviews = int(_sum(df_r, "reviews"))
total_sessions = int(_sum(df_s, "starts"))
total_wishlist_net = int(_sum(df_w, "net_added"))

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(f"💰 Revenue ({hours}h)", f"${total_revenue:,.2f}")
c2.metric("🛒 Purchases", f"{total_purchases:,}")
c3.metric("⭐ Reviews", f"{total_reviews:,}")
c4.metric("🎯 Sessions started", f"{total_sessions:,}")
c5.metric("📥 Net wishlist adds", f"{total_wishlist_net:,}")

st.divider()

# ---------- Revenue time series ----------
st.subheader("💰 Revenue over time")
if not df_p.empty:
    xcol = "HOUR" if "HOUR" in df_p.columns else "hour"
    rev_col = "REVENUE" if "REVENUE" in df_p.columns else "revenue"
    pur_col = "PURCHASES" if "PURCHASES" in df_p.columns else "purchases"

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=df_p[xcol], y=df_p[pur_col], name="Purchases (count)", marker_color="#3b82f6", opacity=0.5),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df_p[xcol], y=df_p[rev_col], name="Revenue (USD)", mode="lines+markers", line=dict(color="#22c55e", width=3)),
        secondary_y=True,
    )
    fig.update_layout(height=380, margin=dict(t=20, b=20), hovermode="x unified")
    fig.update_yaxes(title_text="Purchases", secondary_y=False)
    fig.update_yaxes(title_text="Revenue (USD)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No purchase history yet. Wait for Airflow DAG streaming_agg_copy_to_snowflake to run.")

st.divider()

# ---------- Reviews & sentiment ----------
st.subheader("⭐ Reviews volume & sentiment")
if not df_r.empty:
    xcol = "HOUR" if "HOUR" in df_r.columns else "hour"
    rev_col = "REVIEWS" if "REVIEWS" in df_r.columns else "reviews"
    rec_col = "AVG_RECOMMEND_PCT" if "AVG_RECOMMEND_PCT" in df_r.columns else "avg_recommend_pct"

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=df_r[xcol], y=df_r[rev_col], name="Reviews", marker_color="#eab308", opacity=0.6),
        secondary_y=False,
    )
    if rec_col in df_r.columns:
        fig.add_trace(
            go.Scatter(x=df_r[xcol], y=df_r[rec_col], name="Recommend %", mode="lines+markers", line=dict(color="#ef4444", width=3)),
            secondary_y=True,
        )
    fig.update_layout(height=380, margin=dict(t=20, b=20), hovermode="x unified")
    fig.update_yaxes(title_text="Reviews", secondary_y=False)
    fig.update_yaxes(title_text="Recommend %", secondary_y=True, range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No review history yet.")

st.divider()

# ---------- Sessions activity ----------
st.subheader("🎯 Sessions activity")
if not df_s.empty:
    xcol = "HOUR" if "HOUR" in df_s.columns else "hour"
    starts_col = "STARTS" if "STARTS" in df_s.columns else "starts"
    ends_col = "ENDS" if "ENDS" in df_s.columns else "ends"
    dur_col = "AVG_DURATION_SEC" if "AVG_DURATION_SEC" in df_s.columns else "avg_duration_sec"

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_s[xcol], y=df_s[starts_col], name="Starts", marker_color="#22c55e"))
    fig.add_trace(go.Bar(x=df_s[xcol], y=df_s[ends_col], name="Ends", marker_color="#ef4444"))
    fig.update_layout(height=380, margin=dict(t=20, b=20), barmode="group", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    if dur_col in df_s.columns:
        st.markdown("**⏱️ Average session duration (seconds)**")
        fig2 = px.line(df_s, x=xcol, y=dur_col, markers=True)
        fig2.update_traces(line=dict(color="#8b5cf6", width=3))
        fig2.update_layout(height=250, margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No session history yet.")

st.divider()

# ---------- Wishlist ----------
st.subheader("📥 Wishlist trends")
if not df_w.empty:
    xcol = "HOUR" if "HOUR" in df_w.columns else "hour"
    add_col = "ADDED" if "ADDED" in df_w.columns else "added"
    rem_col = "REMOVED" if "REMOVED" in df_w.columns else "removed"
    net_col = "NET_ADDED" if "NET_ADDED" in df_w.columns else "net_added"

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_w[xcol], y=df_w[add_col], name="Added", marker_color="#22c55e"))
    fig.add_trace(go.Bar(x=df_w[xcol], y=df_w[rem_col], name="Removed", marker_color="#ef4444"))
    fig.add_trace(go.Scatter(x=df_w[xcol], y=df_w[net_col], name="Net", mode="lines+markers", line=dict(color="#8b5cf6", width=3)))
    fig.update_layout(height=380, margin=dict(t=20, b=20), barmode="group", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No wishlist history yet.")

st.divider()
st.caption(f"⏱️ Data as of {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} • Range: last {hours} hours")