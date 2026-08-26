import pandas as pd
import plotly.express as px
import streamlit as st

from api_client import get
from styles import SEVERITY_COLORS, inject_css, severity_badge

st.set_page_config(page_title="Anomalies", page_icon="⚠️", layout="wide")
inject_css()

st.markdown("# ⚠️ ANOMALY DETECTION")

tab_kg, tab_stream = st.tabs(["🕸️ GRAPH ANOMALIES (NEO4J)", "🌊 STREAM ANOMALIES (SPARK)"])

with tab_kg:
    c1, c2, c3 = st.columns(3)
    limit = c1.slider("Limit", 10, 500, 100, key="kg_lim")
    atype = c2.selectbox("Type", ["", "publisher_dominance", "isolated_game", "sales_inconsistency"])
    sev = c3.selectbox("Severity", ["", "High", "Medium"])

    params = {"limit": limit}
    if atype:
        params["anomaly_type"] = atype
    if sev:
        params["severity"] = sev

    try:
        data = get("/anomalies/graph", **params)
        df = pd.DataFrame(data["results"])
        if df.empty:
            st.info("No anomalies matching filters.")
        else:
            # KPIs
            c1, c2, c3 = st.columns(3)
            c1.metric("🚨 TOTAL", len(df))
            c2.metric("🔴 HIGH", int((df["SEVERITY"] == "High").sum()))
            c3.metric("🟡 MEDIUM", int((df["SEVERITY"] == "Medium").sum()))

            # Treemap
            fig = px.treemap(
                df, path=["ANOMALY_TYPE", "SEVERITY", "ENTITY_NAME"],
                values="METRIC_VALUE",
                color="SEVERITY",
                color_discrete_map=SEVERITY_COLORS,
                title=None,
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Table stylée
            st.markdown("### 📋 DETAILS")
            df_disp = df.copy()
            df_disp["SEV"] = df_disp["SEVERITY"].apply(
                lambda s: f"🔴 {s}" if s == "High" else f"🟡 {s}"
            )
            st.dataframe(df_disp, use_container_width=True, height=400)
    except Exception as e:
        st.error(str(e))

with tab_stream:
    limit = st.slider("Limit", 10, 200, 50, key="stream_lim")
    try:
        data = get("/anomalies/stream", limit=limit)
        df = pd.DataFrame(data["results"])
        if df.empty:
            st.info("No stream anomalies detected in the last window.")
        else:
            counts = df["ANOMALY_TYPE"].value_counts().reset_index()
            counts.columns = ["type", "n"]
            c1, c2 = st.columns([1, 2])
            fig = px.pie(
                counts, names="type", values="n",
                hole=0.5,
                color_discrete_sequence=["#00d9ff", "#ff00d4", "#7c3aed", "#00ff88"],
            )
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=400)
            c1.plotly_chart(fig, use_container_width=True)

            with c2:
                st.dataframe(df, use_container_width=True, height=400)
    except Exception as e:
        st.error(str(e))