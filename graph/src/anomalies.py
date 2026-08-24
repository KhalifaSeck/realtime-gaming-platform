"""
Detection d'anomalies relationnelles dans le Knowledge Graph Neo4j.

3 methodes :
  1. publisher_dominance  -> publisher controle >50% d'un genre
  2. isolated_games       -> jeux populaires SANS SIMILAR_TO (outliers structurels)
  3. sales_inconsistency  -> jeux similaires avec ecart de popularite >3x

Output : ANALYTICS.KG_ANOMALIES (Snowflake)
Table doit exister avant (voir snowflake/sql/ddl/04_kg_anomalies.sql).

INSERT direct via cursor.executemany() (bypass PUT+S3 qui peut etre bloque par le reseau).
"""
from __future__ import annotations

import pandas as pd
import snowflake.connector
import structlog

from src.config import get_settings

log = structlog.get_logger()


# ============================================================
# Detection 1 : Publisher dominance
# ============================================================

def detect_publisher_dominance(driver) -> list[dict]:
    with driver.session() as session:
        results = session.run("""
            MATCH (p:Publisher)<-[:PUBLISHED_BY]-(g:Game)-[:BELONGS_TO]->(gen:Genre)
            WITH gen.name AS genre, p.name AS publisher, count(g) AS nb_games
            MATCH (g2:Game)-[:BELONGS_TO]->(gen2:Genre {name: genre})
            WITH genre, publisher, nb_games, count(g2) AS total_in_genre
            WITH genre, publisher, nb_games, total_in_genre,
                 toFloat(nb_games) / total_in_genre * 100 AS dominance_pct
            WHERE dominance_pct > 50 AND nb_games >= 3
            RETURN genre, publisher, nb_games, total_in_genre,
                   round(dominance_pct, 1) AS dominance_pct
            ORDER BY dominance_pct DESC
            LIMIT 50
        """).data()

    anomalies = [
        {
            "anomaly_type":   "publisher_dominance",
            "entity_name":    r["publisher"],
            "entity_type":    "Publisher",
            "related_entity": r["genre"],
            "description":    f"{r['publisher']} controls {r['dominance_pct']}% of {r['genre']} ({r['nb_games']}/{r['total_in_genre']} games)",
            "metric_value":   float(r["dominance_pct"]),
            "severity":       "High" if r["dominance_pct"] > 70 else "Medium",
        }
        for r in results
    ]
    log.info("anomalies.publisher_dominance", n=len(anomalies))
    return anomalies


# ============================================================
# Detection 2 : Isolated games (no SIMILAR_TO neighbors)
# ============================================================

def detect_isolated_games(driver) -> list[dict]:
    with driver.session() as session:
        results = session.run("""
            MATCH (g:Game)
            WHERE NOT (g)-[:SIMILAR_TO]-()
              AND g.owners_estimate > 100000
              AND g.popularity_score > 30
            RETURN g.steam_app_id AS appid, g.name AS name,
                   g.popularity_score AS popularity_score,
                   g.popularity_tier  AS tier,
                   g.owners_estimate  AS owners_estimate
            ORDER BY g.popularity_score DESC
            LIMIT 100
        """).data()

    anomalies = [
        {
            "anomaly_type":   "isolated_game",
            "entity_name":    r["name"],
            "entity_type":    "Game",
            "related_entity": None,
            "description":    f"{r['name']} has no similar games (score:{r['popularity_score']}, tier:{r['tier']}, owners:{r['owners_estimate']:,})",
            "metric_value":   float(r["popularity_score"] or 0),
            "severity":       "High" if float(r["popularity_score"] or 0) > 60 else "Medium",
        }
        for r in results
    ]
    log.info("anomalies.isolated_games", n=len(anomalies))
    return anomalies


# ============================================================
# Detection 3 : Sales inconsistency
# ============================================================

def detect_sales_inconsistency(driver) -> list[dict]:
    with driver.session() as session:
        results = session.run("""
            MATCH (a:Game)-[r:SIMILAR_TO]->(b:Game)
            WHERE a.popularity_score > 0 AND b.popularity_score > 0
            WITH a, b, r,
                 CASE WHEN a.popularity_score > b.popularity_score
                      THEN a.popularity_score / b.popularity_score
                      ELSE b.popularity_score / a.popularity_score
                 END AS score_ratio
            WHERE score_ratio > 3
            RETURN a.name AS game_a, b.name AS game_b,
                   a.popularity_score AS score_a,
                   b.popularity_score AS score_b,
                   round(score_ratio, 1) AS score_ratio,
                   r.genre AS genre,
                   r.similarity_score AS similarity
            ORDER BY score_ratio DESC
            LIMIT 50
        """).data()

    anomalies = [
        {
            "anomaly_type":   "sales_inconsistency",
            "entity_name":    r["game_a"],
            "entity_type":    "Game",
            "related_entity": r["game_b"],
            "description":    f"{r['game_a']} (score:{r['score_a']}) vs {r['game_b']} (score:{r['score_b']}) - {r['score_ratio']}x diff despite similarity={r['similarity']} ({r['genre']})",
            "metric_value":   float(r["score_ratio"] or 0),
            "severity":       "High" if float(r["score_ratio"] or 0) > 5 else "Medium",
        }
        for r in results
    ]
    log.info("anomalies.sales_inconsistency", n=len(anomalies))
    return anomalies


# ============================================================
# Save to Snowflake ANALYTICS.KG_ANOMALIES
# ============================================================

def save_to_snowflake(anomalies: list[dict]) -> None:
    if not anomalies:
        log.warning("anomalies.empty")
        return

    df = pd.DataFrame(anomalies)
    df.columns = [c.upper() for c in df.columns]

    s = get_settings()
    conn = snowflake.connector.connect(
        account=f"{s.snowflake_organization_name}-{s.snowflake_account_name}",
        user=s.snowflake_user,
        password=s.snowflake_password,
        role=s.snowflake_role,
        warehouse=s.snowflake_warehouse,
        database=s.snowflake_database,
        schema="ANALYTICS",
    )
    try:
        cur = conn.cursor()

        # TRUNCATE puis INSERT batch (bypass PUT+S3 bloque par certains reseaux)
        cur.execute("TRUNCATE TABLE ANALYTICS.KG_ANOMALIES")

        rows = [
            (
                row["ANOMALY_TYPE"],
                row["ENTITY_NAME"],
                row["ENTITY_TYPE"],
                row.get("RELATED_ENTITY"),
                row["DESCRIPTION"],
                float(row["METRIC_VALUE"]) if row["METRIC_VALUE"] is not None else None,
                row["SEVERITY"],
            )
            for _, row in df.iterrows()
        ]

        cur.executemany("""
            INSERT INTO ANALYTICS.KG_ANOMALIES
                (ANOMALY_TYPE, ENTITY_NAME, ENTITY_TYPE, RELATED_ENTITY,
                 DESCRIPTION, METRIC_VALUE, SEVERITY)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, rows)
        conn.commit()

        log.info("snowflake.kg_anomalies.saved", rows=len(rows))

        for atype, group in df.groupby("ANOMALY_TYPE"):
            counts = group["SEVERITY"].value_counts().to_dict()
            log.info("anomalies.summary", type=atype, total=len(group), severities=counts)
    finally:
        conn.close()


# ============================================================
# Entrypoint
# ============================================================

def run_all(driver) -> list[dict]:
    all_anomalies = []
    all_anomalies += detect_publisher_dominance(driver)
    all_anomalies += detect_isolated_games(driver)
    all_anomalies += detect_sales_inconsistency(driver)
    log.info("anomalies.total", n=len(all_anomalies))
    save_to_snowflake(all_anomalies)
    return all_anomalies