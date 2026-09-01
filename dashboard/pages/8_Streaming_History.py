"""
Page Streaming History - Time series from Snowflake ANALYTICS.STREAM_*_AGG.
Granularity : hour / day / week / month / year
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
st.caption("Snowflake ANALYTICS.STREAM_*_AGG • Refreshed every 5 min via Airflow")


# ============================================================
# Helpers
# ============================================================
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
    for c in ("BUCKET", "bucket"):
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
            df.rename(columns={c: "bucket"}, inplace=True)
    return df


def _col(df: pd.DataFrame, *candidates):
    for c in candidates:
        if c in df.columns:
            return c
        if c.upper() in df.columns:
            return c.upper()
    return None


def _sum(df: pd.DataFrame, *candidates):
    c = _col(df, *candidates)
    if c is None:
        return 0.0
    return float(pd.to_numeric(df[c], errors="coerce").sum())


# ============================================================
# Sidebar
# ============================================================
st.sidebar.header("⚙️ Time Range")

GRAN_OPTIONS = {
    "Hourly (last 24h to 7 days)": ("hour", [1, 3, 7]),
    "Daily (last week to 3 months)": ("day", [7, 30, 90]),
    "Weekly (last month to 1 year)": ("week", [30, 90, 365]),
    "Monthly (last 6 months to 2 years)": ("month", [180, 365, 730]),
    "Yearly (last 2 years)": ("year", [365, 730]),
}
gran_label = st.sidebar.selectbox("Granularity", list(GRAN_OPTIONS.keys()), index=0)
granularity, day_options = GRAN_OPTIONS[gran_label]
days = st.sidebar.select_slider(
    "Look-back window (days)", options=day_options, value=day_options[0]
)

st.sidebar.caption(
    f"⏱️ Grouping by **{granularity}** • Range: last **{days}** days • Data lag: ~5-10 min"
)

# ============================================================
# Fetch
# ============================================================
with st.spinner("Loading history..."):
    df_p = _to_df(_api_get("/history/purchases", granularity=granularity, days=days))
    df_r = _to_df(_api_get("/history/reviews", granularity=granularity, days=days))
    df_s = _to_df(_api_get("/history/sessions", granularity=granularity, days=days))
    df_w = _to_df(_api_get("/history/wishlist", granularity=granularity, days=days))

# ============================================================
# KPIs
# ============================================================
total_revenue = _sum(df_p, "revenue")
total_purchases = int(_sum(df_p, "purchases"))
total_reviews = int(_sum(df_r, "reviews"))
total_sessions = int(_sum(df_s, "starts"))
total_wishlist_net = int(_sum(df_w, "net_added"))

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(f"💰 Revenue ({days}d)", f"${total_revenue:,.2f}")
c2.metric("🛒 Purchases", f"{total_purchases:,}")
c3.metric("⭐ Reviews", f"{total_reviews:,}")
c4.metric("🎯 Sessions started", f"{total_sessions:,}")
c5.metric("📥 Net wishlist adds", f"{total_wishlist_net:,}")

st.divider()

# ============================================================
# Charts
# ============================================================
def _empty_msg(name):
    st.info(f"No {name} data yet for granularity **{granularity}** / last **{days}** days.")


# ---- Revenue ----
st.subheader(f"💰 Revenue over time ({granularity})")
if not df_p.empty and "bucket" in df_p.columns:
    rev_c = _col(df_p, "revenue") or "revenue"
    pur_c = _col(df_p, "purchases") or "purchases"

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=df_p["bucket"], y=df_p[pur_c], name="Purchases",
               marker_color="#3b82f6", opacity=0.5),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df_p["bucket"], y=df_p[rev_c], name="Revenue (USD)",
                   mode="lines+markers", line=dict(color="#22c55e", width=3)),
        secondary_y=True,
    )
    fig.update_layout(height=380, margin=dict(t=20, b=20), hovermode="x unified")
    fig.update_yaxes(title_text="Purchases", secondary_y=False)
    fig.update_yaxes(title_text="Revenue (USD)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    _empty_msg("purchase")

st.divider()

# ---- Reviews ----
st.subheader(f"⭐ Reviews & sentiment ({granularity})")
if not df_r.empty and "bucket" in df_r.columns:
    rev_c = _col(df_r, "reviews") or "reviews"
    rec_c = _col(df_r, "avg_recommend_pct")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=df_r["bucket"], y=df_r[rev_c], name="Reviews",
               marker_color="#eab308", opacity=0.6),
        secondary_y=False,
    )
    if rec_c:
        fig.add_trace(
            go.Scatter(x=df_r["bucket"], y=df_r[rec_c], name="Recommend %",
                       mode="lines+markers", line=dict(color="#ef4444", width=3)),
            secondary_y=True,
        )
    fig.update_layout(height=380, margin=dict(t=20, b=20), hovermode="x unified")
    fig.update_yaxes(title_text="Reviews", secondary_y=False)
    fig.update_yaxes(title_text="Recommend %", secondary_y=True, range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
else:
    _empty_msg("review")

st.divider()

# ---- Sessions ----
st.subheader(f"🎯 Sessions activity ({granularity})")
if not df_s.empty and "bucket" in df_s.columns:
    starts_c = _col(df_s, "starts") or "starts"
    ends_c = _col(df_s, "ends") or "ends"
    dur_c = _col(df_s, "avg_duration_sec")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_s["bucket"], y=df_s[starts_c], name="Starts", marker_color="#22c55e"))
    fig.add_trace(go.Bar(x=df_s["bucket"], y=df_s[ends_c], name="Ends", marker_color="#ef4444"))
    fig.update_layout(height=380, margin=dict(t=20, b=20), barmode="group", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    if dur_c:
        st.markdown("**⏱️ Average session duration (seconds)**")
        fig2 = px.line(df_s, x="bucket", y=dur_c, markers=True)
        fig2.update_traces(line=dict(color="#8b5cf6", width=3))
        fig2.update_layout(height=250, margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)
else:
    _empty_msg("session")

st.divider()

# ---- Wishlist ----
st.subheader(f"📥 Wishlist trends ({granularity})")
if not df_w.empty and "bucket" in df_w.columns:
    add_c = _col(df_w, "added") or "added"
    rem_c = _col(df_w, "removed") or "removed"
    net_c = _col(df_w, "net_added") or "net_added"

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_w["bucket"], y=df_w[add_c], name="Added", marker_color="#22c55e"))
    fig.add_trace(go.Bar(x=df_w["bucket"], y=df_w[rem_c], name="Removed", marker_color="#ef4444"))
    fig.add_trace(go.Scatter(x=df_w["bucket"], y=df_w[net_c], name="Net",
                             mode="lines+markers", line=dict(color="#8b5cf6", width=3)))
    fig.update_layout(height=380, margin=dict(t=20, b=20), barmode="group", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    _empty_msg("wishlist")

st.divider()
st.caption(
    f"⏱️ Data as of {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} • "
    f"Granularity: **{granularity}** • Range: last **{days}** days"
)