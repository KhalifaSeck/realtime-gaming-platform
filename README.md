# 🎮 Real-Time Gaming Intelligence Platform

**Fully automated, cloud-native real-time gaming data platform on Azure, provisioned through Terraform and GitOps, processing Kafka events with Spark and using Agentic AI for autonomous DataOps investigation.**

[![Terraform](https://img.shields.io/badge/Terraform-1.9+-623CE4?logo=terraform)](https://www.terraform.io/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.30+-326CE5?logo=kubernetes)](https://kubernetes.io/)
[![Apache Kafka](https://img.shields.io/badge/Kafka_KRaft-3.7+-231F20?logo=apachekafka)](https://kafka.apache.org/)
[![Apache Spark](https://img.shields.io/badge/Spark_Streaming-3.5+-E25A1C?logo=apachespark)](https://spark.apache.org/)
[![Snowflake](https://img.shields.io/badge/Snowflake-Cloud-29B5E8?logo=snowflake)](https://www.snowflake.com/)
[![dbt](https://img.shields.io/badge/dbt-1.8+-FF694B?logo=dbt)](https://www.getdbt.com/)
[![Power BI](https://img.shields.io/badge/Power_BI-Dashboard-F2C811?logo=powerbi)](https://powerbi.microsoft.com/)

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  KUBERNETES (namespace: gaming)                                      │
│                                                                      │
│  ┌───────────┐   ┌───────┐   ┌───────────────────┐                  │
│  │ Producers │──▶│ Kafka │──▶│ Spark Streaming   │                  │
│  │ (4 topics)│   │ KRaft │   │  (8 streaming     │                  │
│  └───────────┘   └───────┘   │   queries)        │                  │
│                               │  ┌──▶ Redis       │                  │
│                               │  ├──▶ Local Lake  │                  │
│                               │  └──▶ ADLS Gen2 ☁ │                  │
│                               └───────────────────┘                  │
│                                                                      │
│  ┌───────────┐   ┌────────────┐   ┌─────────┐                      │
│  │ FastAPI   │──▶│ Prometheus │──▶│ Grafana │                       │
│  │ /metrics  │   │            │   │         │                       │
│  └───────────┘   └────────────┘   └─────────┘                      │
│                                                                      │
│  ┌─────────────────────────────────────────────┐                    │
│  │  CronJob (every 5 min)                       │                    │
│  │  COPY INTO Snowflake ─▶ dbt run ─▶ dbt test │                    │
│  └─────────────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│  AZURE CLOUD                                                         │
│  ADLS Gen2 ──▶ Snowflake (RAW → STAGING → MARTS) ──▶ Power BI      │
└──────────────────────────────────────────────────────────────────────┘
```

## Data Sources

| Source | Volume | Refresh |
|--------|--------|---------|
| **IGDB API** | ~10,000 games | Daily batch |
| **SteamSpy API** | ~19,600 games | Daily batch |
| **Kafka Producers** | 4 topics (purchases 10%, reviews 20%, sessions 50%, wishlist 20%) | Real-time |

## Kafka Topics

| Topic | Share | Description |
|-------|-------|-------------|
| `steam.purchases` | 10% | Purchase events |
| `steam.reviews` | 20% | Player reviews |
| `steam.sessions` | 50% | Gaming sessions |
| `steam.wishlist` | 20% | Wishlist actions |

## Snowflake Schema

| Layer | Objects | Description |
|-------|---------|-------------|
| **RAW** | 4 tables | Raw events from ADLS |
| **STAGING** | 10 views | Cleaned, typed, deduplicated |
| **MARTS** | 6 tables | Business-ready aggregates |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **IaC** | Terraform 1.9+ |
| **Container Orchestration** | Kubernetes (AKS) |
| **GitOps** | ArgoCD |
| **Message Broker** | Apache Kafka (KRaft mode) |
| **Stream Processing** | Apache Spark Structured Streaming 3.5 |
| **Live State** | Redis |
| **Cloud Storage** | Azure Data Lake Storage Gen2 |
| **Data Warehouse** | Snowflake |
| **Transformation** | dbt 1.8+ |
| **Batch Analytics** | Apache Spark (batch) |
| **Knowledge Graph** | Neo4j |
| **API** | FastAPI |
| **Dashboard** | Power BI + Streamlit |
| **Search & Logs** | Elasticsearch + Kibana |
| **Orchestration** | Apache Airflow |
| **Observability** | Prometheus + Grafana |
| **Agentic AI** | Sentinel AI (LangGraph + Claude + MCP) |

## Build Roadmap (Brick by Brick 🧱)

| Brique | Description | Status |
|--------|-------------|--------|
| 1 | Scaffold + Terraform (ADLS, AKS) | 🔨 In Progress |
| 2 | Batch Ingestion (IGDB + SteamSpy → raw.*) | ⏳ |
| 3 | Kafka KRaft on K8s + 4 Producers | ⏳ |
| 4 | Spark Structured Streaming (8 queries) | ⏳ |
| 5 | Multi-sink (Redis + ADLS + Local Lake) | ⏳ |
| 6 | Snowflake COPY INTO + RAW tables | ⏳ |
| 7 | dbt (10 staging + 6 marts) | ⏳ |
| 8 | Spark Batch Analytics | ⏳ |
| 9 | Neo4j Knowledge Graph | ⏳ |
| 10 | FastAPI (13 endpoints) | ⏳ |
| 11 | Streamlit (6 pages) | ⏳ |
| 12 | Elasticsearch + Kibana | ⏳ |
| 13 | Airflow (2 DAGs) | ⏳ |
| 14 | Prometheus + Grafana | ⏳ |
| 15 | K8s Manifests + GitOps (ArgoCD) | ⏳ |
| 16 | Sentinel AI — Agentic DataOps | ⏳ |

## Getting Started

```bash
# Prerequisites: Terraform >= 1.9, kubectl, Azure CLI, Snowflake account, IGDB API creds, Python 3.10+

# 1. Provision infrastructure
cd terraform/environments/dev
terraform init && terraform plan && terraform apply

# 2. Deploy to Kubernetes
kubectl apply -k k8s/overlays/dev/

# 3. Run batch ingestion
python src/ingestion/igdb/ingest.py
python src/ingestion/steamspy/ingest.py

# 4. Start streaming
kubectl apply -f k8s/base/kafka/
kubectl apply -f k8s/base/spark/
```


## License

MIT