# 🏛️ Architecture détaillée

## Flux de données bout en bout

### 1. Batch — Référentiels externes → Data Lake → Warehouse

```
IGDB /games (OAuth Twitch)
  │  paginate 500/req × 20 pages = 10K games
  │  field expander (genres.name, involved_companies.company.name)
  ▼
Python (ingestion/src/igdb_client.py)
  │  transformer (flatten IDs → names)
  ▼
Pandas -> Parquet (Snappy)
  │  BytesIO buffer
  ▼
ADLS Gen2 : raw/igdb_games/date=YYYY-MM-DD/igdb_games.parquet
  │
  │  COPY INTO (Snowflake external stage + PARQUET file format)
  ▼
Snowflake RAW.IGDB_GAMES
```

Identique pour SteamSpy (avec appdetails enrichment pour tags/languages/genre).

### 2. Streaming — Kafka → Spark → multi-sinks

```
Simulator (4 producers Python)
  │  15 events/sec par topic
  ▼
Kafka KRaft (apache/kafka 3.9 single node)
  │  topics: purchases, reviews, sessions, wishlist
  ▼
Spark Structured Streaming (in Docker apache/spark 3.5)
  │
  │  8 queries en parallèle :
  │
  ├─ Agg queries (foreachBatch) :
  │    parsed → withWatermark 10s → groupBy(window 30s, game_id)
  │       → COALESCE aggregations (num, sum, avg)
  │       → anomaly flags (is_viral, is_review_bomb, is_ccu_spike)
  │       → dual write: Redis Hash + ADLS Parquet
  │
  └─ Raw event queries (append) :
       parsed → write to ADLS raw/streaming_events/{topic}/date=/
```

Puis Snowflake COPY INTO depuis `raw/streaming_events/` et `raw/streaming/`.

### 3. Transformation dbt

```
Sources (dbt sources.yml)
  ├─ raw.igdb_games, raw.steamspy_games
  ├─ raw.stream_purchases/reviews/sessions/wishlist  (event level)
  └─ analytics.stream_*_agg (from Spark)
       ▼
Staging views (10) :
  ├─ stg_igdb_games (rating_normalized, primary_genre)
  ├─ stg_steamspy_games (price_tier, review_label, playtime_hours)
  ├─ stg_stream_* (event-level, event_hour, event_day)
  └─ stg_stream_*_agg (anomaly flags calculated)
       ▼
Marts tables (7) :
  ├─ mart_games (unified dim, popularity_score, tier)
  ├─ mart_trending_games ⭐ (24h signals + anomaly flags + composite score)
  ├─ mart_genre_stats (market share, positive rate)
  ├─ mart_publisher_stats (rank, distinct genres)
  ├─ mart_price_analysis (revenue/tier)
  ├─ mart_review_analysis (review bombing, sentiment drift)
  └─ mart_session_analysis (CCU spikes, completion rate)
```

### 4. Knowledge Graph Neo4j

```
Python (graph/src/loader.py)
  │  SELECT depuis mart_games, mart_genre_stats, mart_publisher_stats
  │  UNWIND batch inserts (500 nodes/relations par tx)
  ▼
Neo4j (10K Game nodes) :
  ├─ (:Game)-[:BELONGS_TO]->(:Genre)
  ├─ (:Game)-[:DEVELOPED_BY]->(:Developer)
  ├─ (:Game)-[:PUBLISHED_BY]->(:Publisher)
  ├─ (:Game)-[:AVAILABLE_ON]->(:Platform)
  ├─ (:Game)-[:HAS_THEME]->(:Theme)
  ├─ (:Game)-[:TAGGED_WITH]->(:Tag)
  └─ (:Game)-[:SIMILAR_TO {score, genre}]->(:Game)

3 anomaly detectors :
  ├─ publisher_dominance (>50% d'un genre)
  ├─ isolated_games (>100K owners, no SIMILAR_TO)
  └─ sales_inconsistency (SIMILAR_TO avec ratio >3x)
       ▼
Snowflake ANALYTICS.KG_ANOMALIES (via cursor.executemany INSERT)
```

### 5. Sentinel AI

```
User question
  ▼
LangGraph create_react_agent (Ollama Qwen3 4B)
  │  choisit 1..N tools parmi 8
  │  (get_trending_games, get_game_details, get_similar_games,
  │   get_graph_anomalies, get_stream_anomalies, get_live_stat,
  │   get_genre_stats, get_publisher_stats)
  ▼
Chaque tool = httpx call à FastAPI (port 8000)
  ▼
FastAPI query Snowflake / Neo4j / Redis
  ▼
LLM synthétise → réponse markdown → user
```

---

## Décisions clés

### Pourquoi Kafka KRaft (pas Zookeeper) ?

Simple : moins de containers, config unifiée, plus stable en dev. Apache Kafka 3.9 est full-KRaft depuis 2024.

### Pourquoi Spark + Redis + ADLS (multi-sink) ?

- **Redis** : latence <1ms pour la page dashboard live.
- **ADLS Parquet** : archivage long-terme queryable par Snowflake COPY INTO.
- **Redis TTL 10min** : évite l'explosion mémoire, focus sur le "récent".

### Pourquoi dbt et pas Spark Batch pour les marts ?

- Volumes petits (10K rows) → SQL Snowflake plus efficace que Spark job.
- dbt = tests + lineage + docs auto.
- Simpler stack : moins de compétences à maintenir.

### Pourquoi Neo4j pour les similars ?

- Similarités = problème de graphe (queries "voisins de X à N hops").
- Cypher clair vs SQL récursif.
- Bonus : anomaly detection sur patterns de graphes.

### Pourquoi LangGraph au lieu de LangChain simple ?

- **Multi-step reasoning** : le pattern ReAct enchaîne tool→observation→pensée→tool.
- **Stateful** : conversation memory possible (à ajouter en future).

### Pourquoi Ollama local (pas OpenAI) ?

- 100% offline, gratuit, souveraineté data.
- Qwen3 4B suffisant pour tool-calling structuré.
- Swap trivial vers OpenAI/Anthropic/Groq (changer 1 import).

### Pourquoi Terraform Snowflake ?

- Reproductibilité : `terraform apply` = même DB/schemas/role/grants partout.
- Séparation IaC / DML : Terraform gère la structure, Python le contenu.

### Pourquoi PowerShell script + pas Airflow local ?

- Airflow 3.x + Astro dev présentait des bugs de token JWT persistants.
- Un script batch quotidien suffit largement en dev.
- Airflow arrive en production sur AKS (Brique 15) avec le Helm chart officiel Apache + KubernetesExecutor (auth par managed identity, pas de token éphémère).

---

## Chiffres clés

| Métrique | Valeur |
|---|---|
| Lignes de code Python | ~3500 |
| Lignes SQL (dbt + DDL + COPY) | ~800 |
| Services Docker | 10+ |
| Endpoints API | 15 |
| Marts dbt | 7 |
| Anomaly detectors | 6 (3 stream + 3 graph) |
| Tables Snowflake | 19 (raw + analytics) |
| Nodes Neo4j (typique) | ~10K |
| Relations Neo4j (typique) | ~50K |
| Tools Sentinel AI | 8 |

---

## Limitations connues

- **Local dev** : pas de HA, pas de retention Kafka > 1 semaine.
- **AKS non déployé** (roadmap Brique 15).
- **Pas de tests unitaires** (roadmap CI/CD).
- **SteamSpy enrichment lent** (85 min pour full 20K games à 4 req/sec).

## Améliorations futures

- Great Expectations / dbt tests custom pour data quality
- Kafka Schema Registry (Avro / Protobuf) au lieu de JSON
- Streaming SQL avec Materialize / Flink
- Feature Store (Feast) pour ML predictions
- Vector search dans Snowflake pour game recommendations