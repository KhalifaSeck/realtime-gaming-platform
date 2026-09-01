"""
Loader Snowflake -> Neo4j Knowledge Graph.

Nodes :
  (:Game       {steam_app_id, name, popularity_score, popularity_tier, price_usd, ...})
  (:Genre      {name, market_share_pct, avg_review_score, num_games, total_owners})
  (:Publisher  {name, market_share_pct, rank, num_games, total_owners})
  (:Developer  {name})
  (:Platform   {name})
  (:Theme      {name})
  (:Tag        {name})

Relations :
  (Game)-[:BELONGS_TO]->(Genre)
  (Game)-[:DEVELOPED_BY]->(Developer)
  (Game)-[:PUBLISHED_BY]->(Publisher)
  (Game)-[:AVAILABLE_ON]->(Platform)
  (Game)-[:HAS_THEME]->(Theme)
  (Game)-[:TAGGED_WITH]->(Tag)
  (Game)-[:SIMILAR_TO {similarity_score, genre}]->(Game)
"""
from __future__ import annotations

import structlog
import snowflake.connector
from neo4j import GraphDatabase

from src.config import get_settings

log = structlog.get_logger()

BATCH_SIZE = 500
SIMILAR_TOP = 5
SIMILAR_MAX_DIFF = 0.30


# ============================================================
# Snowflake
# ============================================================

def _snowflake_conn():
    s = get_settings()
    return snowflake.connector.connect(
        account=f"{s.snowflake_organization_name}-{s.snowflake_account_name}",
        user=s.snowflake_user,
        password=s.snowflake_password,
        role=s.snowflake_role,
        warehouse=s.snowflake_warehouse,
        database=s.snowflake_database,
    )


def fetch_data() -> tuple[list[dict], list[dict], list[dict]]:
    """Fetch mart_games, mart_genre_stats, mart_publisher_stats."""
    conn = _snowflake_conn()
    try:
        cur = conn.cursor(snowflake.connector.DictCursor)

        cur.execute("""
            SELECT
                steam_app_id, game_name, developer, publisher,
                primary_genre_final AS genre, igdb_genres, platforms, themes,
                tags, review_score, review_label,
                owners_estimate, popularity_score, popularity_tier,
                price_usd, price_tier, concurrent_users AS ccu,
                avg_playtime_hours, release_date
            FROM ANALYTICS.mart_games
            WHERE game_name IS NOT NULL AND game_name <> ''
        """)
        games = cur.fetchall()

        cur.execute("""
            SELECT
                genre, market_share_pct, avg_review_score,
                num_games, total_owners, positive_rate_pct
            FROM ANALYTICS.mart_genre_stats
        """)
        genres = cur.fetchall()

        cur.execute("""
            SELECT
                publisher, market_share_games_pct AS market_share_pct,
                rank_by_owners AS rank, num_games, total_owners,
                avg_review_score, num_distinct_genres
            FROM ANALYTICS.mart_publisher_stats
            LIMIT 200
        """)
        publishers = cur.fetchall()

        log.info("snowflake.fetched",
                 games=len(games), genres=len(genres), publishers=len(publishers))
        return games, genres, publishers
    finally:
        conn.close()


def _split_csv(value: str | None, limit: int | None = None) -> list[str]:
    if not value:
        return []
    items = [x.strip() for x in value.split(",") if x.strip()]
    return items[:limit] if limit else items


# ============================================================
# Neo4j
# ============================================================

def neo4j_driver():
    s = get_settings()
    return GraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))


def create_constraints(driver) -> None:
    constraints = [
        "CREATE CONSTRAINT game_id      IF NOT EXISTS FOR (g:Game)      REQUIRE g.steam_app_id IS UNIQUE",
        "CREATE CONSTRAINT genre_name   IF NOT EXISTS FOR (g:Genre)     REQUIRE g.name IS UNIQUE",
        "CREATE CONSTRAINT dev_name     IF NOT EXISTS FOR (d:Developer) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT pub_name     IF NOT EXISTS FOR (p:Publisher) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT platform_nm  IF NOT EXISTS FOR (p:Platform)  REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT theme_name   IF NOT EXISTS FOR (t:Theme)     REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT tag_name     IF NOT EXISTS FOR (t:Tag)       REQUIRE t.name IS UNIQUE",
    ]
    with driver.session() as session:
        for c in constraints:
            session.run(c)
    log.info("neo4j.constraints.created")


def wipe(driver) -> None:
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    log.info("neo4j.graph.wiped")


def load_genres(driver, genres: list[dict]) -> None:
    rows = [
        {
            "name": g["GENRE"],
            "market_share_pct": float(g["MARKET_SHARE_PCT"] or 0),
            "avg_review_score": float(g["AVG_REVIEW_SCORE"] or 0),
            "num_games": int(g["NUM_GAMES"] or 0),
            "total_owners": int(g["TOTAL_OWNERS"] or 0),
            "positive_rate_pct": float(g["POSITIVE_RATE_PCT"] or 0),
        }
        for g in genres if g["GENRE"]
    ]
    with driver.session() as session:
        session.run("""
            UNWIND $rows AS r
            MERGE (g:Genre {name: r.name})
            SET g.market_share_pct  = r.market_share_pct,
                g.avg_review_score  = r.avg_review_score,
                g.num_games         = r.num_games,
                g.total_owners      = r.total_owners,
                g.positive_rate_pct = r.positive_rate_pct
        """, rows=rows)
    log.info("neo4j.genres.loaded", n=len(rows))


def load_publishers(driver, publishers: list[dict]) -> None:
    rows = [
        {
            "name": p["PUBLISHER"],
            "market_share_pct": float(p["MARKET_SHARE_PCT"] or 0),
            "rank": int(p["RANK"] or 0),
            "num_games": int(p["NUM_GAMES"] or 0),
            "total_owners": int(p["TOTAL_OWNERS"] or 0),
            "avg_review_score": float(p["AVG_REVIEW_SCORE"] or 0),
            "num_distinct_genres": int(p["NUM_DISTINCT_GENRES"] or 0),
        }
        for p in publishers if p["PUBLISHER"]
    ]
    with driver.session() as session:
        session.run("""
            UNWIND $rows AS r
            MERGE (p:Publisher {name: r.name})
            SET p.market_share_pct    = r.market_share_pct,
                p.rank                = r.rank,
                p.num_games           = r.num_games,
                p.total_owners        = r.total_owners,
                p.avg_review_score    = r.avg_review_score,
                p.num_distinct_genres = r.num_distinct_genres
        """, rows=rows)
    log.info("neo4j.publishers.loaded", n=len(rows))


def load_games_and_rels(driver, games: list[dict]) -> None:
    """Cree les Game nodes + toutes les relations en UNWIND batch."""
    # ---------- Game nodes ----------
    game_rows = [
        {
            "steam_app_id": int(g["STEAM_APP_ID"]),
            "name": g["GAME_NAME"],
            "review_score": float(g["REVIEW_SCORE"] or 0),
            "review_label": g["REVIEW_LABEL"],
            "owners_estimate": int(g["OWNERS_ESTIMATE"] or 0),
            "popularity_score": float(g["POPULARITY_SCORE"] or 0),
            "popularity_tier": g["POPULARITY_TIER"],
            "price_usd": float(g["PRICE_USD"] or 0),
            "price_tier": g["PRICE_TIER"],
            "ccu": int(g["CCU"] or 0),
            "avg_playtime_hours": float(g["AVG_PLAYTIME_HOURS"] or 0),
            "release_date": str(g["RELEASE_DATE"]) if g["RELEASE_DATE"] else None,
            "primary_genre": g["GENRE"],
        }
        for g in games
    ]
    for i in range(0, len(game_rows), BATCH_SIZE):
        batch = game_rows[i:i + BATCH_SIZE]
        with driver.session() as session:
            session.run("""
                UNWIND $rows AS row
                MERGE (g:Game {steam_app_id: row.steam_app_id})
                SET g.name              = row.name,
                    g.review_score      = row.review_score,
                    g.review_label      = row.review_label,
                    g.owners_estimate   = row.owners_estimate,
                    g.popularity_score  = row.popularity_score,
                    g.popularity_tier   = row.popularity_tier,
                    g.price_usd         = row.price_usd,
                    g.price_tier        = row.price_tier,
                    g.ccu               = row.ccu,
                    g.avg_playtime_hours = row.avg_playtime_hours,
                    g.release_date      = row.release_date,
                    g.primary_genre     = row.primary_genre
            """, rows=batch)
    log.info("neo4j.games.loaded", n=len(game_rows))

    # ---------- Relations ----------
    _bulk_rel(driver, games, "GENRE", "genre",
              "MERGE (n:Genre {name: r.value}) WITH n,r MATCH (g:Game {steam_app_id: r.appid}) MERGE (g)-[:BELONGS_TO]->(n)",
              extractor=lambda g: [g["GENRE"]] if g.get("GENRE") else [])

    _bulk_rel(driver, games, "DEV", "developer",
              "MERGE (n:Developer {name: r.value}) WITH n,r MATCH (g:Game {steam_app_id: r.appid}) MERGE (g)-[:DEVELOPED_BY]->(n)",
              extractor=lambda g: _split_csv(g.get("DEVELOPER")))

    _bulk_rel(driver, games, "PUB", "publisher",
              "MERGE (n:Publisher {name: r.value}) WITH n,r MATCH (g:Game {steam_app_id: r.appid}) MERGE (g)-[:PUBLISHED_BY]->(n)",
              extractor=lambda g: _split_csv(g.get("PUBLISHER")))

    _bulk_rel(driver, games, "PLATFORM", "platform",
              "MERGE (n:Platform {name: r.value}) WITH n,r MATCH (g:Game {steam_app_id: r.appid}) MERGE (g)-[:AVAILABLE_ON]->(n)",
              extractor=lambda g: _split_csv(g.get("PLATFORMS")))

    _bulk_rel(driver, games, "THEME", "theme",
              "MERGE (n:Theme {name: r.value}) WITH n,r MATCH (g:Game {steam_app_id: r.appid}) MERGE (g)-[:HAS_THEME]->(n)",
              extractor=lambda g: _split_csv(g.get("THEMES")))

    _bulk_rel(driver, games, "TAG", "tag",
              "MERGE (n:Tag {name: r.value}) WITH n,r MATCH (g:Game {steam_app_id: r.appid}) MERGE (g)-[:TAGGED_WITH]->(n)",
              extractor=lambda g: _split_csv(g.get("TAGS"), limit=3))


def _bulk_rel(driver, games: list[dict], kind: str, value_key: str, cypher: str, extractor) -> None:
    """Helper generique UNWIND pour creer une type de relation."""
    rels = [
        {"appid": int(g["STEAM_APP_ID"]), "value": v}
        for g in games
        for v in extractor(g)
    ]
    if not rels:
        return
    for i in range(0, len(rels), BATCH_SIZE):
        batch = rels[i:i + BATCH_SIZE]
        with driver.session() as session:
            session.run(f"UNWIND $rels AS r {cypher}", rels=batch)
    log.info("neo4j.rel.loaded", kind=kind, n=len(rels))


def create_similar_to(driver, games: list[dict]) -> None:
    """SIMILAR_TO entre jeux du meme genre + popularity_score proche (<30% diff)."""
    from collections import defaultdict
    by_genre = defaultdict(list)
    for g in games:
        if g.get("GENRE") and g.get("POPULARITY_SCORE"):
            by_genre[g["GENRE"]].append({
                "appid": int(g["STEAM_APP_ID"]),
                "score": float(g["POPULARITY_SCORE"] or 0),
            })

    rels = []
    for genre, items in by_genre.items():
        items = sorted(items, key=lambda x: x["score"], reverse=True)[:20]
        for i, a in enumerate(items):
            for b in items[i+1:i+1+SIMILAR_TOP]:
                if a["score"] == 0 or b["score"] == 0:
                    continue
                diff = abs(a["score"] - b["score"]) / max(a["score"], b["score"])
                if diff < SIMILAR_MAX_DIFF:
                    rels.append({
                        "a": a["appid"], "b": b["appid"],
                        "score": round(1 - diff, 3), "genre": genre,
                    })

    if not rels:
        return
    for i in range(0, len(rels), BATCH_SIZE):
        batch = rels[i:i + BATCH_SIZE]
        with driver.session() as session:
            session.run("""
                UNWIND $rels AS r
                MATCH (a:Game {steam_app_id: r.a})
                MATCH (b:Game {steam_app_id: r.b})
                MERGE (a)-[rel:SIMILAR_TO]->(b)
                SET rel.similarity_score = r.score, rel.genre = r.genre
            """, rels=batch)
    log.info("neo4j.similar_to.loaded", n=len(rels))


def print_stats(driver) -> None:
    with driver.session() as session:
        nodes = session.run("""
            MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n
            ORDER BY n DESC
        """).data()
        rels = session.run("""
            MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS n
            ORDER BY n DESC
        """).data()

    log.info("neo4j.stats.nodes", rows=nodes)
    log.info("neo4j.stats.rels", rows=rels)