"""
CLI multi-producer.

Lance N producers Kafka en parallele (threads I/O-bound).

Usage :
    python -m src.main                                    # tous, 1 evt/s/producer, forever
    python -m src.main --producers purchases,reviews      # 2 producers
    python -m src.main --rate 5 --duration 60             # 5 evts/s pendant 60s
    python -m src.main --max-events 100                   # 100 evts/producer max
"""
from __future__ import annotations

import argparse
import signal
import threading
from typing import Type

import structlog

from src.producers.base import BaseProducer
from src.producers.purchases import PurchaseProducer
from src.producers.reviews import ReviewProducer
from src.producers.sessions import SessionProducer
from src.producers.wishlist import WishlistProducer

log = structlog.get_logger()

REGISTRY: dict[str, Type[BaseProducer]] = {
    "purchases": PurchaseProducer,
    "reviews": ReviewProducer,
    "sessions": SessionProducer,
    "wishlist": WishlistProducer,
}


def parse_producers(spec: str) -> list[Type[BaseProducer]]:
    if spec == "all":
        return list(REGISTRY.values())
    names = [n.strip() for n in spec.split(",")]
    unknown = [n for n in names if n not in REGISTRY]
    if unknown:
        raise ValueError(
            f"Unknown producer(s): {unknown}. Available: {list(REGISTRY.keys())}"
        )
    return [REGISTRY[n] for n in names]


def run_producer(
    cls: Type[BaseProducer],
    rate: float,
    max_events: int | None,
    stop_event: threading.Event,
) -> None:
    producer = cls()
    producer.run(
        rate_per_second=rate,
        max_events=max_events,
        stop_event=stop_event,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Kafka producers in parallel.")
    parser.add_argument(
        "--producers", "-p", default="all",
        help="Comma-separated names, or 'all'. Choices: " + ", ".join(REGISTRY.keys()),
    )
    parser.add_argument("--rate", type=float, default=1.0, help="Events/sec per producer.")
    parser.add_argument("--duration", type=int, default=None, help="Total duration (sec). Default: forever.")
    parser.add_argument("--max-events", type=int, default=None, help="Cap events per producer.")
    args = parser.parse_args()

    classes = parse_producers(args.producers)
    log.info(
        "main.start",
        producers=[c.__name__ for c in classes],
        rate=args.rate,
        duration=args.duration,
        max_events=args.max_events,
    )

    stop_event = threading.Event()

    def _handle_sigint(signum, frame) -> None:
        log.info("main.sigint.received")
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_sigint)

    # Lance chaque producer dans son propre thread
    threads: list[threading.Thread] = []
    for cls in classes:
        t = threading.Thread(
            target=run_producer,
            args=(cls, args.rate, args.max_events, stop_event),
            name=cls.__name__,
        )
        t.start()
        threads.append(t)

    # Si duration -> schedule l'arret automatique
    if args.duration is not None:
        threading.Timer(args.duration, stop_event.set).start()

    # Wait tous les threads
    for t in threads:
        t.join()

    log.info("main.done")


if __name__ == "__main__":
    main()