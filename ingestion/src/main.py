"""
CLI orchestrateur pour l'ingestion enrichie.

Usage :
    python -m src.main                                # all sources, enrichi
    python -m src.main --source igdb --limit 100
    python -m src.main --source steamspy --no-enrich  # skip appdetails (rapide)
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
    raw_games = client.fetch_games_enriched(limit=limit)
    games = [flatten_igdb_game(g) for g in raw_games]
    write_parquet(games, source="igdb_games")


def ingest_steamspy(enrich: bool) -> None:
    client = SteamSpyClient()
    raw_games = client.fetch_top_games_enriched(page=0, enrich_details=enrich)
    games = [flatten_steamspy_game(g) for g in raw_games]
    # Path ADLS : streaming/... deja pris. On utilise "steamspy_games" (match schema Snowflake)
    write_parquet(games, source="steamspy_games")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest enriched reference data into ADLS Gen2.")
    parser.add_argument("--source", choices=["igdb", "steamspy", "all"], default="all")
    parser.add_argument("--limit", type=int, default=500, help="IGDB games per fetch (max 500).")
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="SteamSpy : skip appdetails calls (10x plus rapide, mais pas de tags/languages/genre).",
    )
    args = parser.parse_args()

    log.info("ingestion.start", source=args.source, enrich=not args.no_enrich)

    if args.source in ("igdb", "all"):
        ingest_igdb(limit=args.limit)
    if args.source in ("steamspy", "all"):
        ingest_steamspy(enrich=not args.no_enrich)

    log.info("ingestion.done")


if __name__ == "__main__":
    main()