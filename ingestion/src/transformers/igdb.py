"""Transformer IGDB : dict brut (avec refs imbriquees) -> dict plat CSV-ready."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _list_names(items: list[dict[str, Any]] | None) -> str:
    """['{name: X}', '{name: Y}'] -> 'X, Y'."""
    if not items:
        return ""
    return ", ".join(i.get("name", "") for i in items if i.get("name"))


def _companies_by_role(items: list[dict[str, Any]] | None, role: str) -> str:
    """Filtre involved_companies par role (developer/publisher) -> 'Studio A, Studio B'."""
    if not items:
        return ""
    names = [
        ic["company"]["name"]
        for ic in items
        if ic.get(role) and ic.get("company", {}).get("name")
    ]
    return ", ".join(names)


def _ts_to_date(ts: int | None) -> str | None:
    """Unix ts (sec) -> 'YYYY-MM-DD' (ISO date)."""
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()


def flatten_igdb_game(game: dict[str, Any]) -> dict[str, Any]:
    """Flatten un game IGDB (avec fields expander) au format CSV cible."""
    return {
        "igdb_id":      game.get("id"),
        "name":         game.get("name"),
        "summary":      game.get("summary"),
        "rating":       game.get("rating"),
        "rating_count": game.get("rating_count"),
        "release_date": _ts_to_date(game.get("first_release_date")),
        "genres":       _list_names(game.get("genres")),
        "themes":       _list_names(game.get("themes")),
        "platforms":    _list_names(game.get("platforms")),
        "keywords":     _list_names(game.get("keywords")),
        "game_modes":   _list_names(game.get("game_modes")),
        "developer":    _companies_by_role(game.get("involved_companies"), "developer"),
        "publisher":    _companies_by_role(game.get("involved_companies"), "publisher"),
    }