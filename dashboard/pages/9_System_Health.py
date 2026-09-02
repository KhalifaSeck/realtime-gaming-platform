"""
Page System Health - alertes Grafana + metrics Prometheus temps reel.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx
import pandas as pd
import streamlit as st

st.set_page_config(page_title="System Health", page_icon="🩺", layout="wide")

st.title("🩺 System Health — Alerts & Live Metrics")
st.caption("Powered by Prometheus + Grafana Alerts • Auto-refresh")

# ---------- Endpoints internes AKS ----------
PROM_URL = "http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090"
GRAFANA_URL = "http://prometheus-grafana.observability.svc.cluster.local"


# ---------- Helpers ----------
def prom_query(query: str, timeout: float = 5.0):
    """Query Prometheus API : /api/v1/query"""
    try:
        with httpx.Client(timeout=timeout) as c:
            r = c.get(f"{PROM_URL}/api/v1/query", params={"query": query})
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "success":
                return data["data"]["result"]
    except Exception as e:
        st.error(f"Prometheus error: {e}")
    return []


def prom_scalar(query: str, default: float = 0.0) -> float:
    """Prend le premier scalar d'une prom_query."""
    result = prom_query(query)
    if result and "value" in result[0]:
        try:
            return float(result[0]["value"][1])
        except (ValueError, IndexError):
            return default
    return default


def grafana_alerts():
    """Query Grafana alerts API pour recuperer l'etat des rules."""
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.get(
                f"{GRAFANA_URL}/api/prometheus/grafana/api/v1/rules",
                auth=("admin", "rtgaming2026"),
            )
            r.raise_for_status()
            data = r.json()
            groups = data.get("data", {}).get("groups", [])
            rules = []
            for g in groups:
                for r_ in g.get("rules", []):
                    rules.append({
                        "name": r_.get("name"),
                        "state": r_.get("state", "unknown"),
                        "health": r_.get("health", "unknown"),
                        "summary": (r_.get("annotations") or {}).get("summary", ""),
                        "severity": (r_.get("labels") or {}).get("severity", ""),
                        "last_eval": r_.get("lastEvaluation", ""),
                    })
            return rules
    except Exception as e:
        st.warning(f"Grafana alerts API error: {e}")
    return []


# ---------- Sidebar ----------
refresh = st.sidebar.slider("Refresh (sec)", 5, 60, 10)
st.sidebar.caption(f"⏱️ Every {refresh}s")
st.sidebar.markdown(
    "**External links:**\n"
    "- [Grafana](http://20.116.178.122)\n"
    "- [GitHub](https://github.com/KhalifaSeck/realtime-gaming-platform)"
)

# ---------- Corps ----------
placeholder = st.empty()

with placeholder.container():
    # ============================ KPIs ============================
    pods_running = int(prom_scalar('sum(kube_pod_status_phase{namespace="rtgaming", phase="Running"})'))
    pods_failed = int(prom_scalar('sum(kube_pod_status_phase{namespace="rtgaming", phase=~"Failed|Pending"})'))
    api_rps = prom_scalar('sum(rate(http_requests_total{namespace="rtgaming"}[1m]))')
    api_5xx = prom_scalar('sum(rate(http_requests_total{namespace="rtgaming", status=~"5.."}[5m]))')
    api_p99 = prom_scalar(
        'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{namespace="rtgaming"}[5m])) by (le))'
    )
    node_cpu = prom_scalar('100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])))')

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🟢 Pods Running", pods_running)
    c2.metric("🔴 Failed/Pending", pods_failed, delta="⚠️" if pods_failed > 0 else "OK")
    c3.metric("📊 API req/s", f"{api_rps:.2f}")
    c4.metric("⚠️ 5xx err/s", f"{api_5xx:.3f}", delta="⚠️" if api_5xx > 0 else "OK")
    c5.metric("⏱️ API P99 (s)", f"{api_p99:.3f}")
    c6.metric("🖥️ Node CPU %", f"{node_cpu:.1f}%")

    st.divider()

    # ============================ ALERTS ============================
    st.subheader("🚨 Grafana Alerts")
    alerts = grafana_alerts()
    if alerts:
        df_alerts = pd.DataFrame(alerts)

        firing = df_alerts[df_alerts["state"].str.lower() == "firing"]
        pending = df_alerts[df_alerts["state"].str.lower() == "pending"]
        normal = df_alerts[df_alerts["state"].str.lower() == "normal"]

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("🔥 Firing", len(firing))
        a2.metric("⏳ Pending", len(pending))
        a3.metric("✅ Normal", len(normal))
        a4.metric("📋 Total", len(df_alerts))

        # Colorier selon l'etat
        def _color(row):
            state = str(row.get("state", "")).lower()
            if state == "firing":
                return ["background-color: #7f1d1d; color: white"] * len(row)
            if state == "pending":
                return ["background-color: #78350f; color: white"] * len(row)
            return [""] * len(row)

        display_df = df_alerts[["name", "state", "severity", "summary", "last_eval"]]
        st.dataframe(
            display_df.style.apply(_color, axis=1),
            use_container_width=True,
            height=250,
        )
    else:
        st.info("No alerts configured yet (or Grafana API unreachable).")

    st.divider()

    # ============================ POD STATUS ============================
    st.subheader("📦 Pods (rtgaming namespace)")
    pod_data = prom_query('kube_pod_status_phase{namespace="rtgaming"} == 1')
    if pod_data:
        rows = []
        for series in pod_data:
            m = series.get("metric", {})
            rows.append({
                "pod": m.get("pod", "?"),
                "phase": m.get("phase", "?"),
            })
        df_pods = pd.DataFrame(rows).drop_duplicates(subset="pod").sort_values("pod")
        st.dataframe(df_pods, use_container_width=True, height=280)
    else:
        st.info("No pod status data.")

    st.divider()

    # ============================ Timestamp ============================
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.caption(f"⏱️ Last refresh: {now} • Full Grafana → http://20.116.178.122")

time.sleep(refresh)
st.rerun()