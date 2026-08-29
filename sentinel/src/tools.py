"""LangChain tools wrappent l'API FastAPI."""
from __future__ import annotations

import httpx
from langchain_core.tools import tool

from src.config import get_settings


def _api_get(path: str, **params) -> dict:
    with httpx.Client(base_url=get_settings().api_base_url, timeout=30.0) as c:
        r = c.get(path, params=params)
        r.raise_for_status()
        return r.json()


@tool
def get_trending_games(limit: int = 10, with_anomaly_only: bool = False) -> dict:
    """
    Retourne les jeux tendance des dernieres 24h.
    Args:
        limit: nombre max de jeux (default 10)
        with_anomaly_only: True pour ne retenir que ceux avec un anomaly flag
    """
    return _api_get("/trending", limit=limit, with_anomaly_only=with_anomaly_only)


@tool
def get_game_details(steam_app_id: int) -> dict:
    """
    Recupere les details complets d'un jeu par son Steam appid.
    Args:
        steam_app_id: identifiant Steam du jeu (ex: 730 pour CS:GO)
    """
    return _api_get(f"/games/{steam_app_id}")


@tool
def get_similar_games(steam_app_id: int, limit: int = 10) -> dict:
    """
    Retourne les jeux similaires depuis le Knowledge Graph Neo4j.
    Args:
        steam_app_id: identifiant Steam du jeu
        limit: nombre max de similaires
    """
    return _api_get(f"/games/{steam_app_id}/similar", limit=limit)


@tool
def get_graph_anomalies(limit: int = 20, anomaly_type: str | None = None, severity: str | None = None) -> dict:
    """
    Anomalies detectees dans le graphe Neo4j.
    Args:
        limit: nombre max
        anomaly_type: publisher_dominance | isolated_game | sales_inconsistency
        severity: High | Medium
    """
    params = {"limit": limit}
    if anomaly_type:
        params["anomaly_type"] = anomaly_type
    if severity:
        params["severity"] = severity
    return _api_get("/anomalies/graph", **params)


@tool
def get_stream_anomalies(limit: int = 20) -> dict:
    """
    Anomalies streaming detectees par Spark (viral purchases, review bombs, CCU spikes).
    Args:
        limit: nombre max
    """
    return _api_get("/anomalies/stream", limit=limit)


@tool
def get_live_stat(topic: str, steam_app_id: int) -> dict:
    """
    State temps reel d'un jeu depuis Redis.
    Args:
        topic: purchases | reviews | sessions | wishlist
        steam_app_id: identifiant Steam
    """
    return _api_get(f"/live/stats/{topic}/{steam_app_id}")


@tool
def get_genre_stats(limit: int = 20) -> dict:
    """Statistiques market share par genre."""
    return _api_get("/genres", limit=limit)


@tool
def get_publisher_stats(limit: int = 20) -> dict:
    """Ranking publishers par owners + market share."""
    return _api_get("/publishers", limit=limit)


ALL_TOOLS = [
    get_trending_games,
    get_game_details,
    get_similar_games,
    get_graph_anomalies,
    get_stream_anomalies,
    get_live_stat,
    get_genre_stats,
    get_publisher_stats,
]