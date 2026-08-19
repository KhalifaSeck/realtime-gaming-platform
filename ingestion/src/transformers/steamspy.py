"""Transformer SteamSpy : dict brut -> dict plat CSV-ready."""
from __future__ import annotations

from typing import Any


def _midpoint(owners_range: str | None) -> int:
    """'100,000 .. 200,000' -> 150000."""
    if not owners_range or ".." not in owners_range:
        return 0
    parts = owners_range.split("..")
    try:
        low = int(parts[0].strip().replace(",", ""))
        high = int(parts[1].strip().replace(",", ""))
        return (low + high) // 2
    except ValueError:
        return 0


def _cents_to_dollars(val: Any) -> float:
    """SteamSpy renvoie les prix en cents (string). Convertit en dollars."""
    if val is None or val == "":
        return 0.0
    try:
        return round(float(val) / 100, 2)
    except (ValueError, TypeError):
        return 0.0


def _tags_to_string(tags: Any) -> str:
    """SteamSpy renvoie tags comme dict {name: count} ou list. On flatten en 'a, b, c'."""
    if not tags:
        return ""
    if isinstance(tags, dict):
        return ", ".join(tags.keys())
    if isinstance(tags, list):
        return ", ".join(str(t) for t in tags)
    return str(tags)


def flatten_steamspy_game(game: dict[str, Any]) -> dict[str, Any]:
    """Flatten un game SteamSpy (avec appdetails enrichi) au format CSV cible."""
    positive = int(game.get("positive") or 0)
    negative = int(game.get("negative") or 0)
    total_reviews = positive + negative
    review_score = round((positive / total_reviews) * 100, 1) if total_reviews > 0 else None

    return {
        "appid":            int(game["appid"]),
        "name":             game.get("name"),
        "developer":        game.get("developer"),
        "publisher":        game.get("publisher"),
        "score_rank":       str(game.get("score_rank") or ""),
        "owners_range":     game.get("owners"),
        "owners_estimate":  _midpoint(game.get("owners")),
        "average_forever":  int(game.get("average_forever") or 0),
        "average_2weeks":   int(game.get("average_2weeks") or 0),
        "median_forever":   int(game.get("median_forever") or 0),
        "median_2weeks":    int(game.get("median_2weeks") or 0),
        "ccu":              int(game.get("ccu") or 0),
        "price_usd":        _cents_to_dollars(game.get("price")),
        "initialprice_usd": _cents_to_dollars(game.get("initialprice")),
        "discount_pct":     int(game.get("discount") or 0),
        "positive":         positive,
        "negative":         negative,
        "review_score":     review_score,
        "tags":             _tags_to_string(game.get("tags")),
        "languages":        game.get("languages"),
        "genre":            game.get("genre"),
    }