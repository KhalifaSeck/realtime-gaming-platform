# 🎮 Realtime Gaming Intelligence Platform

> End-to-end data platform : ingestion batch + streaming Kafka, transformation dbt sur Snowflake, Knowledge Graph Neo4j, monitoring Prometheus/Grafana, et agent IA autonome (LangGraph + Ollama Qwen3) capable d'interroger l'ensemble de la plateforme.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Kafka](https://img.shields.io/badge/Apache_Kafka-3.9-231F20?logo=apachekafka&logoColor=white)
![Spark](https://img.shields.io/badge/Spark-3.5-E25A1C?logo=apachespark&logoColor=white)
![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?logo=snowflake&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-Core_1.12-FF694B?logo=dbt&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-5.18-018BFF?logo=neo4j&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white)
![Azure](https://img.shields.io/badge/Azure-0078D4?logo=microsoftazure&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama_Qwen3-000000?logo=ollama&logoColor=white)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             DATA SOURCES                                │
│      IGDB API (10K games)          SteamSpy API (top 20K games)         │
└──────────────────┬───────────────────────────┬──────────────────────────┘
                   │ batch daily              │ batch daily
                   ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    INGESTION (Python + Parquet)                         │
│     -> ADLS Gen2 : raw/igdb_games/  +  raw/steamspy_games/              │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
             ┌────────────────┴────────────────┐
             │                                 │
             ▼                                 ▼
┌─────────────────────────┐    ┌───────────────────────────────────┐
│ COPY INTO Snowflake     │    │ Kafka Producers (Python)          │
│ RAW.IGDB_GAMES          │    │ 4 topics: purchases, reviews,     │
│ RAW.STEAMSPY_GAMES      │    │           sessions, wishlist      │
└─────────────────────────┘    └────────────────┬──────────────────┘
                                                │
                                                ▼
                               ┌────────────────────────────────────┐
                               │ Spark Structured Streaming (KRaft) │
                               │  4 aggregate queries (30s windows) │
                               │  4 raw event queries (append mode) │
                               │  Sinks: Redis + ADLS Parquet       │
                               └────────────────┬───────────────────┘
                                                │
                                                ▼
                               ┌────────────────────────────────────┐
                               │ Snowflake ANALYTICS.STREAM_*_AGG   │
                               │ Snowflake RAW.STREAM_* (events)    │
                               └────────────────┬───────────────────┘
                                                │
                                                ▼
                        ┌───────────────────────────────────────────┐
                        │              dbt Core 1.12                │
                        │   10 staging views  +  7 marts tables     │
                        │   mart_games, mart_trending_games ⭐,     │
                        │   mart_genre/publisher/price/review/      │
                        │   session_analysis                        │
                        └────────────────┬──────────────────────────┘
                                         │
        ┌────────────────────────────────┼──────────────────────────┐
        ▼                                ▼                          ▼
┌──────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│  Neo4j KG        │   │      FastAPI         │   │  Prometheus          │
│  10K Game nodes  │   │  15 endpoints        │   │  scrape /metrics     │
│  Publishers,     │   │  /games, /trending,  │   │  every 15s           │
│  Genres,         │   │  /anomalies, /live   │   │                      │
│  SIMILAR_TO,     │   │  /stats/*, /health   │   │  ▼                   │
│  3 anomaly types │   └──────┬───────────────┘   │  Grafana             │
└──────────────────┘          │                   │  Dashboards-as-code  │
        ▲                     │                   │  (grafanalib)        │
        │                     ▼                   └──────────────────────┘
        │       ┌──────────────────────────────┐
        │       │  Streamlit (6 pages)         │
        │       │  Home, Games, Trending,      │
        │       │  Anomalies, Market Stats,    │
        │       │  KG, Sentinel AI Chat        │
        │       └──────┬───────────────────────┘
        │              │
        │              ▼
        │       ┌──────────────────────────────┐
        └───────│  Sentinel AI (LangGraph)     │
                │  Ollama Qwen3 + 8 tools      │
                │  Calls FastAPI + Neo4j       │
                └──────────────────────────────┘
```

---

## 🚀 Quick Start

### Prérequis

- Docker Desktop (WSL2 backend, 8 GB RAM minimum)
- Compte Azure (Free tier OK) + `az` CLI connecté
- Compte Snowflake (Free trial 30 jours suffit)
- Ollama installé sur le host + modèle `qwen3:4b` (`ollama pull qwen3:4b`)
- `dbt-env` conda (Python 3.11 + dbt-core + dbt-snowflake)

### Setup infrastructure (une fois)

```bash
# 1. Provision Azure (RG + ADLS Gen2)
cd infra/terraform/azure
terraform init
terraform apply

# 2. Provision Snowflake (DB + schemas + role + stage)
cd ../snowflake
terraform init
terraform apply

# 3. Snowflake DDL (tables RAW + ANALYTICS)
cd ../../../snowflake
python -m ops.runner sql/ddl/
```

### Lancer toute la plateforme

```bash
docker compose up -d
```

Ça démarre 10+ containers :

| Service | URL | Rôle |
|---|---|---|
| Streamlit Dashboard | http://localhost:8501 | UI principale (6 pages + chat AI) |
| Sentinel AI API | http://localhost:8888/docs | Agent LangGraph |
| Platform API | http://localhost:8000/docs | 15 endpoints (games, trending, anomalies) |
| Grafana | http://localhost:3000 (admin/rtgaming) | Monitoring |
| Prometheus | http://localhost:9090 | Metrics |
| Neo4j Browser | http://localhost:7474 (neo4j/rtgaming2026) | Knowledge Graph |
| Kafka-UI | http://localhost:8081 | Topics inspection |

### Lancer le pipeline batch quotidien (manuel ou via Task Scheduler)

```powershell
.\scripts\batch_daily.ps1
```

Effectue : ingestion IGDB + SteamSpy → COPY INTO Snowflake → dbt run.

Automatisable via Windows Task Scheduler (voir `scripts/`).

### Injecter du trafic streaming

```bash
cd simulator
python -m src.main --producers all --rate 5 --duration 120
```

4 producers Kafka envoient des événements simulés pendant 2 min.

---

## 📊 Sample interactions Sentinel AI

Depuis http://localhost:8501 → page **6_Sentinel_AI**, ou via API :

```bash
curl -X POST http://localhost:8888/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the top 3 trending games?"}'
```

Exemples de questions :
- *"Any review bombs detected recently?"*
- *"Which publishers dominate the FPS genre?"*
- *"Show me games similar to Counter-Strike"*
- *"What's happening live for game 730?"*
- *"Compare Warner Bros vs Rockstar Games"*

L'agent choisit automatiquement les tools nécessaires (jusqu'à 8 disponibles) et synthétise la réponse.

---

## 🧰 Tech stack

| Couche | Techno | Rôle |
|---|---|---|
| **Cloud IaC** | Terraform + Azure | RG, ADLS Gen2, Snowflake DB/schemas/role/stage |
| **Ingestion** | Python + requests + pyarrow | IGDB (OAuth Twitch) + SteamSpy paginated |
| **Streaming** | Apache Kafka 3.9 (KRaft) + Confluent-Kafka Python | 4 topics, 4 producers |
| **Processing** | Apache Spark 3.5 Structured Streaming | 8 queries: 4 agg + 4 raw events |
| **Cache live** | Redis 7 | State par jeu (`stat:{topic}:{game_id}` hash, TTL 10min) |
| **Data lake** | Azure ADLS Gen2 (Hierarchical Namespace) | Parquet Snappy partitionné date |
| **Warehouse** | Snowflake (trial) | External stage + COPY INTO Parquet |
| **Transformation** | dbt Core 1.12 + dbt-snowflake | 10 staging (with anomaly flags) + 7 marts |
| **Knowledge Graph** | Neo4j 5.18 + APOC + GDS | 10K games + SIMILAR_TO + 3 anomaly detectors |
| **API** | FastAPI + prometheus-fastapi-instrumentator | 15 endpoints |
| **UI** | Streamlit + Plotly (dark neon gaming theme) | 6 pages |
| **AI Agent** | LangGraph + Ollama Qwen3 4B | 8 tools, ReAct pattern |
| **Monitoring** | Prometheus + Grafana + grafanalib | Dashboards-as-code |
| **Orchestration** | PowerShell + Windows Task Scheduler (local) | Airflow migration prévue en AKS |
| **Containerization** | Docker Compose | 10+ services orchestrés |

---

## 📁 Structure du repo

```
realtime-gaming-platform/
├── infra/terraform/         Azure + Snowflake IaC
├── ingestion/               IGDB + SteamSpy batch (Python)
├── simulator/               4 Kafka producers
├── streaming/               Spark Structured Streaming
├── snowflake/               SQL DDL + COPY + Python runner
├── gaming_dbt/              dbt project (staging + marts)
├── graph/                   Neo4j loader + anomaly detection
├── api/                     FastAPI
├── dashboard/               Streamlit
├── sentinel/                LangGraph AI agent + FastAPI
├── observability/           Prometheus config + Grafana dashboards-as-code
├── scripts/                 PowerShell batch orchestration
└── docker-compose.yml       Full local stack
```

---

## 📈 Métriques du projet

- **Data volume** : 10K games IGDB + top 20K SteamSpy games (batch daily)
- **Streaming** : 4 topics × ~5-10 events/sec (configurable)
- **Snowflake** : 4 raw + 4 stream event + 4 stream agg + 7 marts = **19 tables/views**
- **Neo4j** : ~10K Game nodes + 7 relation types (SIMILAR_TO, DEVELOPED_BY, PUBLISHED_BY, BELONGS_TO, AVAILABLE_ON, HAS_THEME, TAGGED_WITH)
- **API** : 15 endpoints REST + `/metrics` Prometheus
- **Dashboards** : 1 Grafana (générable en Python) + 6 pages Streamlit

---

## 🗺️ Roadmap

- [ ] **Brique 12** — Elasticsearch + Kibana (log aggregation)
- [ ] **Brique 15** — Deploy sur AKS avec Helm chart Airflow + ArgoCD GitOps
- [ ] Tests dbt (contracts, singular tests custom)
- [ ] Tests API pytest + coverage
- [ ] GitHub Actions CI/CD (lint, tests, docker build/push)
- [ ] Sentinel AI : streaming responses + memory conversation

---

## 📝 Licence

MIT — libre d'usage éducatif.

## 🙋 Auteur

**Khalifa Seck** — Data Engineer
Projet portfolio 2026.