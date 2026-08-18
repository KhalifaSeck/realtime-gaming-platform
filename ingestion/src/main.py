"""
CLI orchestrateur pour l'ingestion.

Usage :
    python -m src.main                          # all sources
    python -m src.main --source igdb --limit 100
    python -m src.main --source steamspy
"""
from __future__ import annotations

import argparse

import structlog

from src.igdb_client import IGDBClient
from src.steamspy_client import SteamSpyClient
from src.writer import write_parquet

log = structlog.get_logger()


def ingest_igdb(limit: int) -> None:
    client = IGDBClient()
    games = client.fetch_games(limit=limit)
    write_parquet(games, source="igdb_games")


def ingest_steamspy() -> None:
    client = SteamSpyClient()
    games = client.fetch_top_games(page=0)
    write_parquet(games, source="steamspy_top")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest reference data from IGDB and SteamSpy into ADLS Gen2.")
    parser.add_argument("--source", choices=["igdb", "steamspy", "all"], default="all")
    parser.add_argument("--limit", type=int, default=500, help="IGDB limit per fetch (max 500).")
    args = parser.parse_args()

    log.info("ingestion.start", source=args.source)

    if args.source in ("igdb", "all"):
        ingest_igdb(limit=args.limit)
    if args.source in ("steamspy", "all"):
        ingest_steamspy()

    log.info("ingestion.done")


if __name__ == "__main__":
    main()