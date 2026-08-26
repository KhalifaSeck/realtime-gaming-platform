"""Client SteamSpy - API publique, pas d'auth."""
from __future__ import annotations

import time
from typing import Any

import requests
import structlog

log = structlog.get_logger()


class SteamSpyClient:
    BASE_URL = "https://steamspy.com/api.php"
    APPDETAILS_SLEEP = 0.25
    ALL_ENDPOINT_SLEEP = 1.1

    def _get(self, params: dict[str, Any]) -> Any:
        resp = requests.get(self.BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def fetch_top_games(self, page: int = 0) -> list[dict[str, Any]]:
        data = self._get({"request": "all", "page": page})
        # SteamSpy renvoie {} vide OU non-dict quand plus rien
        if not isinstance(data, dict) or not data:
            return []
        return [{"appid": int(appid), **info} for appid, info in data.items()]

    def fetch_app_details(self, appid: int) -> dict[str, Any]:
        return self._get({"request": "appdetails", "appid": appid})

    def fetch_top_games_all_pages(self, max_pages: int | None = None) -> list[dict[str, Any]]:
        """Paginate jusqu'a page vide OU max_pages OU erreur JSON (rate-limit / HTML error)."""
        all_games: list[dict[str, Any]] = []
        page = 0
        consecutive_errors = 0

        while True:
            if max_pages is not None and page >= max_pages:
                log.info("steamspy.paginate.max_reached", page=page, max=max_pages)
                break

            log.info("steamspy.paginate.fetch", page=page)
            try:
                batch = self.fetch_top_games(page)
            except (requests.exceptions.JSONDecodeError,
                    requests.exceptions.HTTPError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                consecutive_errors += 1
                log.warning("steamspy.paginate.error",
                            page=page, retry=consecutive_errors, error=str(e)[:100])
                if consecutive_errors >= 3:
                    log.error("steamspy.paginate.give_up", page=page)
                    break
                time.sleep(5 * consecutive_errors)   # backoff exponentiel
                continue

            consecutive_errors = 0

            if not batch:
                log.info("steamspy.paginate.empty", page=page)
                break

            all_games.extend(batch)
            page += 1
            time.sleep(self.ALL_ENDPOINT_SLEEP)

        log.info("steamspy.paginate.done", total=len(all_games), pages=page)
        return all_games

    def enrich_with_appdetails(
        self,
        games: list[dict[str, Any]],
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        to_enrich = games if limit is None else games[:limit]
        log.info("steamspy.enrich.start", n=len(to_enrich), total_games=len(games))
        for i, game in enumerate(to_enrich):
            try:
                details = self.fetch_app_details(game["appid"])
                for k in ("tags", "languages", "genre"):
                    if details.get(k):
                        game[k] = details[k]
            except Exception as e:
                log.warning("steamspy.appdetails.failed", appid=game["appid"], error=str(e)[:100])
            if (i + 1) % 100 == 0:
                log.info("steamspy.enrich.progress", done=i + 1, total=len(to_enrich))
            time.sleep(self.APPDETAILS_SLEEP)
        log.info("steamspy.enrich.done", enriched=len(to_enrich))
        return games


if __name__ == "__main__":
    import json
    client = SteamSpyClient()
    games = client.fetch_top_games_all_pages(max_pages=2)
    print(json.dumps(games[:3], indent=2, ensure_ascii=False))
    print(f"\nFetched {len(games)} games")