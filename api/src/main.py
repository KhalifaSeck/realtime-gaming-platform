"""
FastAPI - Realtime Gaming Platform (13 endpoints).

Endpoints :
  GET  /                          welcome
  GET  /health                    services status
  GET  /games                     list games with filters
  GET  /games/{appid}             game details
  GET  /games/{appid}/similar     similar games from KG (Neo4j)
  GET  /genres                    genre stats
  GET  /publishers                publisher stats
  GET  /trending                  trending games (batch + stream)
  GET  /anomalies/stream          streaming anomalies (Spark aggregates)
  GET  /anomalies/graph           graph anomalies (Neo4j)
  GET  /stats/reviews             review analysis
  GET  /stats/sessions            session analysis
  GET  /stats/prices              price analysis
"""
from __future__ import annotations

import structlog
from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import get_settings
from src.db import neo4j_query, redis_client, snowflake_query

log = structlog.get_logger()

app = FastAPI(
    title="Realtime Gaming Platform API",
    description="Snowflake marts + Neo4j KG + Redis live state",
    version="1.0.0",
)
Instrumentator().instrument(app).expose(app)


# ============================================================
# 1. GET /
# ============================================================
@app.get("/", tags=["meta"])
def root():
    return {
        "name": "rtgaming API",
        "version": app.version,
        "docs": "/docs",
        "metrics": "/metrics",
        "endpoints": [
            "/health", "/games", "/games/{appid}", "/games/{appid}/similar",
            "/genres", "/publishers", "/trending",
            "/anomalies/stream", "/anomalies/graph",
            "/stats/reviews", "/stats/sessions", "/stats/prices",
        ],
    }


# ============================================================
# 2. GET /health
# ============================================================
@app.get("/health", tags=["meta"])
def health():
    status = {"snowflake": "?", "redis": "?", "neo4j": "?"}
    try:
        snowflake_query("SELECT 1 AS ok")
        status["snowflake"] = "ok"
    except Exception as e:
        status["snowflake"] = f"error: {e}"
    try:
        redis_client().ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {e}"
    try:
        neo4j_query("RETURN 1 AS ok")
        status["neo4j"] = "ok"
    except Exception as e:
        status["neo4j"] = f"error: {e}"

    overall = "ok" if all(v == "ok" for v in status.values()) else "degraded"
    return {"status": overall, "services": status}


# ============================================================
# 3. GET /games
# ============================================================
@app.get("/games", tags=["games"])
def list_games(
    limit: int = Query(default=100, ge=1, le=500),
    min_owners: int = Query(default=0, ge=0),
    genre: str | None = None,
    tier: str | None = None,
):
    where = ["OWNERS_ESTIMATE >= %s"]
    params: list = [min_owners]
    if genre:
        where.append("PRIMARY_GENRE_FINAL ILIKE %s")
        params.append(f"%{genre}%")
    if tier:
        where.append("POPULARITY_TIER = %s")
        params.append(tier)

    sql = f"""
        SELECT STEAM_APP_ID, GAME_NAME, DEVELOPER, PUBLISHER,
               PRIMARY_GENRE_FINAL AS PRIMARY_GENRE,
               PRICE_USD, PRICE_TIER, REVIEW_SCORE, REVIEW_LABEL,
               OWNERS_ESTIMATE, POPULARITY_SCORE, POPULARITY_TIER
        FROM ANALYTICS.MART_GAMES
        WHERE {' AND '.join(where)}
        ORDER BY POPULARITY_SCORE DESC NULLS LAST
        LIMIT {limit}
    """
    return {"count": limit, "results": snowflake_query(sql, tuple(params))}


# ============================================================
# 4. GET /games/{appid}
# ============================================================
@app.get("/games/{appid}", tags=["games"])
def get_game(appid: int):
    rows = snowflake_query(
        "SELECT * FROM ANALYTICS.MART_GAMES WHERE STEAM_APP_ID = %s",
        (appid,),
    )
    if not rows:
        raise HTTPException(404, f"Game {appid} not found")
    return rows[0]


# ============================================================
# 5. GET /games/{appid}/similar (Neo4j)
# ============================================================
@app.get("/games/{appid}/similar", tags=["games"])
def similar_games(appid: int, limit: int = Query(default=10, ge=1, le=50)):
    cypher = """
        MATCH (g:Game {steam_app_id: $appid})-[r:SIMILAR_TO]-(other:Game)
        RETURN other.steam_app_id  AS steam_app_id,
               other.name          AS game_name,
               other.popularity_tier AS popularity_tier,
               other.popularity_score AS popularity_score,
               r.similarity_score  AS similarity,
               r.genre             AS shared_genre
        ORDER BY r.similarity_score DESC
        LIMIT $limit
    """
    results = neo4j_query(cypher, appid=appid, limit=limit)
    if not results:
        return {"count": 0, "results": [], "note": f"Game {appid} not found or no similars"}
    return {"count": len(results), "results": results}


# ============================================================
# 6. GET /genres
# ============================================================
@app.get("/genres", tags=["stats"])
def genre_stats(limit: int = Query(default=50, ge=1, le=200)):
    sql = f"""
        SELECT GENRE, NUM_GAMES, MARKET_SHARE_PCT,
               TOTAL_OWNERS, AVG_OWNERS,
               POSITIVE_RATE_PCT, AVG_REVIEW_SCORE, AVG_PRICE_USD,
               AVG_POPULARITY_SCORE, RANK_BY_OWNERS, RANK_BY_GAMES
        FROM ANALYTICS.MART_GENRE_STATS
        ORDER BY RANK_BY_OWNERS
        LIMIT {limit}
    """
    return {"count": limit, "results": snowflake_query(sql)}


# ============================================================
# 7. GET /publishers
# ============================================================
@app.get("/publishers", tags=["stats"])
def publisher_stats(limit: int = Query(default=50, ge=1, le=500)):
    sql = f"""
        SELECT PUBLISHER, NUM_GAMES, NUM_DISTINCT_GENRES,
               MARKET_SHARE_GAMES_PCT, MARKET_SHARE_OWNERS_PCT,
               TOTAL_OWNERS, POSITIVE_RATE_PCT, AVG_REVIEW_SCORE,
               AVG_PRICE_USD, AVG_POPULARITY_SCORE, RANK_BY_OWNERS
        FROM ANALYTICS.MART_PUBLISHER_STATS
        ORDER BY RANK_BY_OWNERS
        LIMIT {limit}
    """
    return {"count": limit, "results": snowflake_query(sql)}


# ============================================================
# 8. GET /trending
# ============================================================
@app.get("/trending", tags=["trending"])
def trending_games(
    limit: int = Query(default=20, ge=1, le=200),
    with_anomaly_only: bool = False,
):
    where = ""
    if with_anomaly_only:
        where = """
            WHERE HAD_VIRAL_PURCHASES_PERIOD = TRUE
               OR HAD_REVIEW_BOMB_PERIOD = TRUE
               OR HAD_CCU_SPIKE_PERIOD = TRUE
               OR HAD_VIRAL_WISHLIST_PERIOD = TRUE
        """
    sql = f"""
        SELECT STEAM_APP_ID, GAME_NAME, DEVELOPER, PUBLISHER, PRIMARY_GENRE,
               TRENDING_SCORE,
               TOTAL_PURCHASES_PERIOD, TOTAL_REVENUE_PERIOD_USD,
               TOTAL_REVIEWS_PERIOD, AVG_RATING_PERIOD,
               TOTAL_SESSIONS_PERIOD, WISHLIST_NET_ADDED_PERIOD,
               HAD_VIRAL_PURCHASES_PERIOD, HAD_REVIEW_BOMB_PERIOD,
               HAD_CCU_SPIKE_PERIOD, HAD_VIRAL_WISHLIST_PERIOD
        FROM ANALYTICS.MART_TRENDING_GAMES
        {where}
        ORDER BY TRENDING_SCORE DESC
        LIMIT {limit}
    """
    return {"count": limit, "results": snowflake_query(sql)}


# ============================================================
# 9. GET /anomalies/stream (Spark aggregates flags)
# ============================================================
@app.get("/anomalies/stream", tags=["anomalies"])
def stream_anomalies(limit: int = Query(default=50, ge=1, le=200)):
    sql = f"""
        SELECT * FROM (
            SELECT 'is_viral_purchases' AS anomaly_type,
                   steam_app_id, window_start,
                   num_purchases AS metric, NULL AS metric_2
            FROM STAGING.STG_STREAM_PURCHASES_AGG
            WHERE is_viral = TRUE

            UNION ALL SELECT 'is_review_bomb',
                   steam_app_id, window_start,
                   num_reviews, avg_rating
            FROM STAGING.STG_STREAM_REVIEWS_AGG
            WHERE is_review_bomb = TRUE

            UNION ALL SELECT 'is_ccu_spike',
                   steam_app_id, window_start,
                   num_starts, avg_duration_sec
            FROM STAGING.STG_STREAM_SESSIONS_AGG
            WHERE is_ccu_spike = TRUE

            UNION ALL SELECT 'is_viral_wishlist',
                   steam_app_id, window_start,
                   net_added, NULL
            FROM STAGING.STG_STREAM_WISHLIST_AGG
            WHERE is_viral_wishlist = TRUE
        )
        ORDER BY window_start DESC
        LIMIT {limit}
    """
    return {"count": limit, "results": snowflake_query(sql)}


# ============================================================
# 10. GET /anomalies/graph (Neo4j -> Snowflake KG_ANOMALIES)
# ============================================================
@app.get("/anomalies/graph", tags=["anomalies"])
def graph_anomalies(
    limit: int = Query(default=100, ge=1, le=500),
    anomaly_type: str | None = None,
    severity: str | None = None,
):
    where = ["1=1"]
    params: list = []
    if anomaly_type:
        where.append("ANOMALY_TYPE = %s")
        params.append(anomaly_type)
    if severity:
        where.append("SEVERITY = %s")
        params.append(severity)

    sql = f"""
        SELECT ANOMALY_TYPE, ENTITY_NAME, ENTITY_TYPE, RELATED_ENTITY,
               DESCRIPTION, METRIC_VALUE, SEVERITY, _LOADED_AT
        FROM ANALYTICS.KG_ANOMALIES
        WHERE {' AND '.join(where)}
        ORDER BY METRIC_VALUE DESC
        LIMIT {limit}
    """
    return {"count": limit, "results": snowflake_query(sql, tuple(params) if params else None)}


# ============================================================
# 11. GET /stats/reviews
# ============================================================
@app.get("/stats/reviews", tags=["stats"])
def review_stats(limit: int = Query(default=50, ge=1, le=500)):
    sql = f"""
        SELECT STEAM_APP_ID, GAME_NAME, DEVELOPER, PUBLISHER, PRIMARY_GENRE,
               HISTORICAL_POSITIVE, HISTORICAL_NEGATIVE,
               HISTORICAL_REVIEW_SCORE, HISTORICAL_LABEL,
               STREAM_REVIEWS_PERIOD, STREAM_AVG_RATING_PERIOD,
               STREAM_RECOMMEND_PCT_PERIOD,
               REVIEW_BOMB_WINDOWS_PERIOD, HAD_REVIEW_BOMB_PERIOD,
               SENTIMENT_DRIFT_PCT
        FROM ANALYTICS.MART_REVIEW_ANALYSIS
        ORDER BY REVIEW_BOMB_WINDOWS_PERIOD DESC, STREAM_REVIEWS_PERIOD DESC
        LIMIT {limit}
    """
    return {"count": limit, "results": snowflake_query(sql)}


# ============================================================
# 12. GET /stats/sessions
# ============================================================
@app.get("/stats/sessions", tags=["stats"])
def session_stats(limit: int = Query(default=50, ge=1, le=500)):
    sql = f"""
        SELECT STEAM_APP_ID, GAME_NAME, DEVELOPER, PRIMARY_GENRE,
               OWNERS_ESTIMATE, STEAM_CONCURRENT_USERS,
               HISTORICAL_AVG_PLAYTIME_HOURS,
               TOTAL_STARTS_PERIOD, TOTAL_ENDS_PERIOD,
               AVG_SESSION_DURATION_MIN_PERIOD,
               CCU_SPIKE_WINDOWS_PERIOD, HAD_CCU_SPIKE_PERIOD,
               PEAK_STARTS_IN_WINDOW_PERIOD, COMPLETION_RATE_PCT
        FROM ANALYTICS.MART_SESSION_ANALYSIS
        ORDER BY PEAK_STARTS_IN_WINDOW_PERIOD DESC, TOTAL_STARTS_PERIOD DESC
        LIMIT {limit}
    """
    return {"count": limit, "results": snowflake_query(sql)}


# ============================================================
# 13. GET /stats/prices
# ============================================================
@app.get("/stats/prices", tags=["stats"])
def price_stats():
    sql = """
        SELECT PRICE_TIER, NUM_GAMES, AVG_PRICE_USD,
               TOTAL_OWNERS, AVG_OWNERS, OWNERS_SHARE_PCT,
               AVG_REVIEW_SCORE, AVG_POPULARITY_SCORE,
               TOTAL_PURCHASES_24H, TOTAL_REVENUE_24H_USD,
               REVENUE_SHARE_PCT_24H
        FROM ANALYTICS.MART_PRICE_ANALYSIS
        ORDER BY AVG_POPULARITY_SCORE DESC NULLS LAST
    """
    return {"results": snowflake_query(sql)}


if __name__ == "__main__":
    import uvicorn
    s = get_settings()
    uvicorn.run("src.main:app", host=s.api_host, port=s.api_port, reload=True)