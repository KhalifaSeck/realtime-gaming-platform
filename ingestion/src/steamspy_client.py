"""
Client SteamSpy - API publique, pas d'auth.

Endpoint principal : ?request=all&page=<N> -> top 1000 jeux Steam
sortes par owners, paginés (1000 par page).

Doc : https://steamspy.com/api.php
Rate limit : 1 req/sec pour 'all', 4 req/sec pour les autres endpoints.
"""
from __future__ import annotations

from typing import Any

import requests
import structlog

log = structlog.get_logger()


class SteamSpyClient:
    BASE_URL = "https://steamspy.com/api.php"

    def _get(self, params: dict[str, Any]) -> Any:
        log.info("steamspy.query", params=params)
        resp = requests.get(self.BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def fetch_top_games(self, page: int = 0) -> list[dict[str, Any]]:
        """Top 1000 jeux par nombre de owners. Retourne une liste de dicts."""
        data = self._get({"request": "all", "page": page})
        # SteamSpy renvoie un dict {appid: {info}}. On aplatit en liste.
        return [{"appid": int(appid), **info} for appid, info in data.items()]

    def fetch_app_details(self, appid: int) -> dict[str, Any]:
        """Details enrichis d'un jeu unique."""
        return self._get({"request": "appdetails", "appid": appid})


if __name__ == "__main__":
    import json

    client = SteamSpyClient()
    games = client.fetch_top_games(page=0)
    print(json.dumps(games[:3], indent=2, ensure_ascii=False))
    print(f"\n✅ Fetched {len(games)} games from SteamSpy")