"""
CLI ingestion enrichie.

Usage :
    # All-in (recommande pour prod, LONG : ~85 min si tu enrichis tout)
    python -m src.main --source all --limit 10000

    # Fast dev (top 1000 SteamSpy enrichi seulement)
    python -m src.main --source steamspy --enrich-limit 1000

    # Full sans enrichissement (aucun tags/languages/genre)
    python -m src.main --source steamspy --no-enrich

    # IGDB seul
    python -m src.main --source igdb --limit 10000

    # SteamSpy toutes pages sans limit enrichissement
    python -m src.main --source steamspy --pages 20
"""
from __future__ import annotations

import argparse

import structlog

from src.igdb_client import IGDBClient
from src.steamspy_client import SteamSpyClient
from src.transformers.igdb import flatten_igdb_game
from src.transformers.steamspy import flatten_steamspy_game
from src.writer import write_parquet

log = structlog.get_logger()


def ingest_igdb(limit: int) -> None:
    client = IGDBClient()
    raw_games = client.fetch_all_games_enriched(total=limit)
    games = [flatten_igdb_game(g) for g in raw_games]
    write_parquet(games, source="igdb_games")


def ingest_steamspy(pages: int | None, enrich_limit: int | None) -> None:
    client = SteamSpyClient()
    games = client.fetch_top_games_all_pages(max_pages=pages)
    if enrich_limit is None or enrich_limit > 0:
        client.enrich_with_appdetails(games, limit=enrich_limit)
    games_flat = [flatten_steamspy_game(g) for g in games]
    write_parquet(games_flat, source="steamspy_games")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest enriched reference data into ADLS Gen2.")
    parser.add_argument("--source", choices=["igdb", "steamspy", "all"], default="all")
    parser.add_argument("--limit", type=int, default=10000,
                        help="IGDB total games (default: 10000). Paginated 500 per request.")
    parser.add_argument("--pages", type=int, default=None,
                        help="SteamSpy: nombre de pages (default: all, ~20). Chaque page = 1000 games.")
    parser.add_argument("--enrich-limit", type=int, default=None,
                        help="SteamSpy: enrich top N games only (default: all). 0 = skip.")
    parser.add_argument("--no-enrich", action="store_true",
                        help="SteamSpy: skip appdetails entirely (equivalent --enrich-limit 0).")
    args = parser.parse_args()

    if args.no_enrich:
        args.enrich_limit = 0

    log.info(
        "ingestion.start",
        source=args.source,
        igdb_limit=args.limit,
        steamspy_pages=args.pages,
        steamspy_enrich_limit=args.enrich_limit,
    )

    if args.source in ("igdb", "all"):
        ingest_igdb(limit=args.limit)
    if args.source in ("steamspy", "all"):
        ingest_steamspy(pages=args.pages, enrich_limit=args.enrich_limit)

    log.info("ingestion.done")


if __name__ == "__main__":
    main()