"""Dashboard API Overview — FastAPI /metrics scrape par Prometheus."""
from grafanalib.core import (
    Dashboard,
    OPS_FORMAT,
    PERCENT_FORMAT,
    SECONDS_FORMAT,
    Stat,
    Target,
    TimeSeries,
)


DATASOURCE = "Prometheus"


dashboard = Dashboard(
    title="API Overview",
    description="FastAPI (rtgaming-api) : throughput, latency, errors",
    tags=["rtgaming", "api"],
    timezone="browser",
    refresh="10s",
    panels=[
        Stat(
            title="Total requests",
            dataSource=DATASOURCE,
            targets=[Target(expr='sum(http_requests_total{job="rtgaming-api"})', legendFormat="total")],
            reduceCalc="lastNotNull",
            format="short",
            gridPos={"h": 4, "w": 6, "x": 0, "y": 0},
        ),
        Stat(
            title="Requests / sec",
            dataSource=DATASOURCE,
            targets=[Target(expr='sum(rate(http_requests_total{job="rtgaming-api"}[1m]))', legendFormat="req/s")],
            reduceCalc="lastNotNull",
            format="reqps",
            gridPos={"h": 4, "w": 6, "x": 6, "y": 0},
        ),
        Stat(
            title="Error rate (5xx)",
            dataSource=DATASOURCE,
            targets=[
                Target(
                    expr='sum(rate(http_requests_total{job="rtgaming-api", status=~"5.."}[5m])) '
                         '/ sum(rate(http_requests_total{job="rtgaming-api"}[5m]))',
                    legendFormat="err %",
                ),
            ],
            reduceCalc="lastNotNull",
            format=PERCENT_FORMAT,
            gridPos={"h": 4, "w": 6, "x": 12, "y": 0},
        ),
        Stat(
            title="Latency p95",
            dataSource=DATASOURCE,
            targets=[
                Target(
                    expr='histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="rtgaming-api"}[5m])) by (le))',
                    legendFormat="p95",
                ),
            ],
            reduceCalc="lastNotNull",
            format=SECONDS_FORMAT,
            gridPos={"h": 4, "w": 6, "x": 18, "y": 0},
        ),

        TimeSeries(
            title="Requests / sec by handler",
            dataSource=DATASOURCE,
            targets=[
                Target(
                    expr='sum(rate(http_requests_total{job="rtgaming-api"}[1m])) by (handler)',
                    legendFormat="{{handler}}",
                ),
            ],
            unit="reqps",
            gridPos={"h": 8, "w": 12, "x": 0, "y": 4},
        ),
        TimeSeries(
            title="Latency percentiles (all handlers)",
            dataSource=DATASOURCE,
            targets=[
                Target(
                    expr='histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{job="rtgaming-api"}[5m])) by (le))',
                    legendFormat="p50",
                ),
                Target(
                    expr='histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="rtgaming-api"}[5m])) by (le))',
                    legendFormat="p95",
                ),
                Target(
                    expr='histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="rtgaming-api"}[5m])) by (le))',
                    legendFormat="p99",
                ),
            ],
            unit="s",
            gridPos={"h": 8, "w": 12, "x": 12, "y": 4},
        ),
        TimeSeries(
            title="Requests by status code",
            dataSource=DATASOURCE,
            targets=[
                Target(
                    expr='sum(rate(http_requests_total{job="rtgaming-api"}[1m])) by (status)',
                    legendFormat="HTTP {{status}}",
                ),
            ],
            unit="reqps",
            gridPos={"h": 8, "w": 24, "x": 0, "y": 12},
        ),
    ],
).auto_panel_ids()