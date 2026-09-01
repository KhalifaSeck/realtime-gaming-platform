"""
CLI Neo4j loader + anomaly detection.

Usage :
    python -m src.main --mode load          # load graphe
    python -m src.main --mode wipe          # vide le graphe
    python -m src.main --mode reload        # wipe + load
    python -m src.main --mode stats         # affiche stats
    python -m src.main --mode anomalies     # detecte + save vers ANALYTICS.KG_ANOMALIES
    python -m src.main --mode all           # reload + anomalies (full refresh)
"""
from __future__ import annotations

import argparse

import structlog

from src.anomalies import run_all as run_anomalies
from src.loader import (
    create_constraints,
    create_similar_to,
    fetch_data,
    load_games_and_rels,
    load_genres,
    load_publishers,
    neo4j_driver,
    print_stats,
    wipe,
)

log = structlog.get_logger()


def _load(driver, wipe_first: bool = False) -> None:
    if wipe_first:
        wipe(driver)
    create_constraints(driver)
    games, genres, publishers = fetch_data()
    load_genres(driver, genres)
    load_publishers(driver, publishers)
    load_games_and_rels(driver, games)
    create_similar_to(driver, games)
    print_stats(driver)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["load", "wipe", "reload", "stats", "anomalies", "all"],
        default="load",
    )
    args = parser.parse_args()

    driver = neo4j_driver()
    try:
        if args.mode == "wipe":
            wipe(driver)
        elif args.mode == "stats":
            print_stats(driver)
        elif args.mode == "load":
            _load(driver, wipe_first=False)
        elif args.mode == "reload":
            _load(driver, wipe_first=True)
        elif args.mode == "anomalies":
            run_anomalies(driver)
        elif args.mode == "all":
            _load(driver, wipe_first=True)
            run_anomalies(driver)
    finally:
        driver.close()

    log.info("main.done", mode=args.mode)


if __name__ == "__main__":
    main()