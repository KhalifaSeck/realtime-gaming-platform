"""Client IGDB (Internet Game Database) - auth OAuth2 Twitch."""
from __future__ import annotations

import time
from typing import Any

import requests
import structlog

from config.settings import get_settings

log = structlog.get_logger()


class IGDBClient:
    TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    API_URL = "https://api.igdb.com/v4"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token
        log.info("igdb.token.fetch")
        resp = requests.post(
            self.TOKEN_URL,
            params={
                "client_id": self._settings.twitch_client_id,
                "client_secret": self._settings.twitch_client_secret,
                "grant_type": "client_credentials",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"]
        log.info("igdb.token.acquired", expires_in_sec=data["expires_in"])
        return self._token

    def query(self, endpoint: str, body: str) -> list[dict[str, Any]]:
        token = self._get_token()
        headers = {
            "Client-ID": self._settings.twitch_client_id,
            "Authorization": f"Bearer {token}",
        }
        url = f"{self.API_URL}/{endpoint}"
        log.info("igdb.query", endpoint=endpoint, body=body[:120])
        resp = requests.post(url, headers=headers, data=body, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def fetch_games(self, limit: int = 500, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch minimal (legacy tests)."""
        body = (
            "fields name, first_release_date, rating, rating_count, "
            "genres, platforms, summary; "
            f"limit {limit}; offset {offset};"
        )
        return self.query("games", body)

    def fetch_games_enriched(self, limit: int = 500, offset: int = 0) -> list[dict[str, Any]]:
        """Single batch (max 500) enriched via IGDB expander syntax."""
        body = (
            "fields name, summary, rating, rating_count, first_release_date, "
            "genres.name, themes.name, platforms.name, keywords.name, game_modes.name, "
            "involved_companies.company.name, "
            "involved_companies.developer, involved_companies.publisher; "
            f"limit {limit}; offset {offset};"
        )
        return self.query("games", body)

    def fetch_all_games_enriched(
        self,
        total: int,
        page_size: int = 500,
    ) -> list[dict[str, Any]]:
        """
        Fetch up to `total` games via pagination + sort rating desc.
        Filter rating != null to keep quality games first.
        """
        all_games: list[dict[str, Any]] = []
        offset = 0
        page_size = min(page_size, 500)

        while len(all_games) < total:
            batch_size = min(page_size, total - len(all_games))
            body = (
                "fields name, summary, rating, rating_count, first_release_date, "
                "genres.name, themes.name, platforms.name, keywords.name, game_modes.name, "
                "involved_companies.company.name, "
                "involved_companies.developer, involved_companies.publisher; "
                "where rating != null; "
                "sort rating desc; "
                f"limit {batch_size}; offset {offset};"
            )
            batch = self.query("games", body)
            if not batch:
                break
            all_games.extend(batch)
            offset += batch_size
            log.info(
                "igdb.paginate.progress",
                fetched=len(all_games),
                target=total,
                offset=offset,
            )

        return all_games


if __name__ == "__main__":
    import json
    client = IGDBClient()
    games = client.fetch_all_games_enriched(total=5)
    print(json.dumps(games, indent=2, ensure_ascii=False))