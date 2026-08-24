"""
CLI Neo4j loader.

Usage :
    python -m src.main --mode load
    python -m src.main --mode wipe
    python -m src.main --mode reload
    python -m src.main --mode stats
"""
from __future__ import annotations

import argparse

import structlog

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["load", "wipe", "reload", "stats"], default="load")
    args = parser.parse_args()

    driver = neo4j_driver()
    try:
        if args.mode == "wipe":
            wipe(driver)
        elif args.mode == "stats":
            print_stats(driver)
        else:
            if args.mode == "reload":
                wipe(driver)
            create_constraints(driver)
            games, genres, publishers = fetch_data()
            load_genres(driver, genres)
            load_publishers(driver, publishers)
            load_games_and_rels(driver, games)
            create_similar_to(driver, games)
            print_stats(driver)
    finally:
        driver.close()

    log.info("main.done", mode=args.mode)


if __name__ == "__main__":
    main()