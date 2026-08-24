"""Helpers Snowflake + Redis + Neo4j."""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache

import redis
import snowflake.connector
from neo4j import GraphDatabase

from src.config import get_settings


# ============================================================
# Snowflake
# ============================================================

@contextmanager
def snowflake_conn():
    s = get_settings()
    conn = snowflake.connector.connect(
        account=f"{s.snowflake_organization_name}-{s.snowflake_account_name}",
        user=s.snowflake_user,
        password=s.snowflake_password,
        role=s.snowflake_role,
        warehouse=s.snowflake_warehouse,
        database=s.snowflake_database,
    )
    try:
        yield conn
    finally:
        conn.close()


def snowflake_query(sql: str, params: tuple | None = None) -> list[dict]:
    with snowflake_conn() as conn:
        cur = conn.cursor(snowflake.connector.DictCursor)
        cur.execute(sql, params) if params else cur.execute(sql)
        return cur.fetchall()


# ============================================================
# Redis
# ============================================================

@lru_cache
def redis_client() -> redis.Redis:
    s = get_settings()
    return redis.Redis(host=s.redis_host, port=s.redis_port, decode_responses=True)


# ============================================================
# Neo4j
# ============================================================

@lru_cache
def neo4j_driver():
    s = get_settings()
    return GraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))


def neo4j_query(cypher: str, **params) -> list[dict]:
    with neo4j_driver().session() as session:
        return session.run(cypher, **params).data()