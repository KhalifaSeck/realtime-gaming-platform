"""Client SteamSpy - API publique, pas d'auth."""
from __future__ import annotations

import time
from typing import Any

import requests
import structlog

log = structlog.get_logger()


class SteamSpyClient:
    BASE_URL = "https://steamspy.com/api.php"
    APPDETAILS_SLEEP = 0.25  # rate limit ~4 req/sec

    def _get(self, params: dict[str, Any]) -> Any:
        resp = requests.get(self.BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def fetch_top_games(self, page: int = 0) -> list[dict[str, Any]]:
        """Top 1000 par owners (1 seule requete)."""
        log.info("steamspy.top.fetch", page=page)
        data = self._get({"request": "all", "page": page})
        return [{"appid": int(appid), **info} for appid, info in data.items()]

    def fetch_app_details(self, appid: int) -> dict[str, Any]:
        return self._get({"request": "appdetails", "appid": appid})

    def fetch_top_games_enriched(
        self,
        page: int = 0,
        enrich_details: bool = True,
    ) -> list[dict[str, Any]]:
        """Fetch top games + enrichit chacun avec tags/languages/genre via appdetails."""
        games = self.fetch_top_games(page)
        if not enrich_details:
            return games

        log.info("steamspy.enrich.start", n=len(games))
        for i, game in enumerate(games):
            try:
                details = self.fetch_app_details(game["appid"])
                for k in ("tags", "languages", "genre"):
                    if details.get(k):
                        game[k] = details[k]
            except Exception as e:  # noqa: BLE001
                log.warning("steamspy.appdetails.failed", appid=game["appid"], error=str(e))
            if (i + 1) % 50 == 0:
                log.info("steamspy.enrich.progress", done=i + 1, total=len(games))
            time.sleep(self.APPDETAILS_SLEEP)
        log.info("steamspy.enrich.done", enriched=len(games))
        return games


if __name__ == "__main__":
    import json
    client = SteamSpyClient()
    games = client.fetch_top_games_enriched(page=0, enrich_details=True)
    print(json.dumps(games[:3], indent=2, ensure_ascii=False))
    print(f"\nFetched + enriched {len(games)} games")