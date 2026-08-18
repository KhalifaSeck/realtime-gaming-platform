"""
BaseProducer : socle commun a tous les producers Kafka.

Chaque sous-classe implemente 'generate_event()' pour retourner
un dict JSON-serializable. La classe s'occupe du reste :
  - init du producer Kafka (confluent-kafka)
  - serialisation JSON UTF-8
  - keying par user_id (routing partition stable)
  - callback de delivery (log erreurs)
  - loop rate-controlled + flush propre a l'arret
  - stop_event optionnel pour shutdown depuis un thread parent
"""
from __future__ import annotations

import json
import threading
import time
from abc import ABC, abstractmethod
from typing import Any

import structlog
from confluent_kafka import Producer

from config.settings import get_settings

log = structlog.get_logger()


class BaseProducer(ABC):
    topic: str  # a definir dans chaque sous-classe

    def __init__(self) -> None:
        settings = get_settings()
        self._producer = Producer({
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "client.id": f"{settings.producer_client_id}-{self.topic}",
            "linger.ms": 10,
            "compression.type": "snappy",
        })
        self._sent = 0

    @abstractmethod
    def generate_event(self) -> dict[str, Any]:
        """Genere un event, format libre a la sous-classe."""

    def _delivery_report(self, err, msg) -> None:
        if err is not None:
            log.error("kafka.delivery.failed", topic=msg.topic(), error=str(err))

    def send_one(self, event: dict[str, Any]) -> None:
        payload = json.dumps(event, default=str).encode("utf-8")
        key_raw = str(event.get("user_id", "")).encode("utf-8") or None
        self._producer.produce(
            topic=self.topic,
            key=key_raw,
            value=payload,
            on_delivery=self._delivery_report,
        )
        self._sent += 1
        self._producer.poll(0)

    def run(
        self,
        rate_per_second: float = 1.0,
        max_events: int | None = None,
        stop_event: threading.Event | None = None,
    ) -> None:
        """Loop : genere et envoie a un debit cible.

        Arret sur :
          - max_events atteint
          - stop_event.set() depuis un thread parent
          - KeyboardInterrupt (Ctrl+C direct dans le process)
        """
        interval = 1.0 / rate_per_second
        log.info(
            "producer.start",
            topic=self.topic,
            rate_per_sec=rate_per_second,
            max_events=max_events,
        )
        try:
            while max_events is None or self._sent < max_events:
                if stop_event is not None and stop_event.is_set():
                    break
                event = self.generate_event()
                self.send_one(event)
                if self._sent % 10 == 0:
                    log.info("producer.progress", topic=self.topic, sent=self._sent)
                time.sleep(interval)
        except KeyboardInterrupt:
            log.info("producer.interrupted", topic=self.topic, sent=self._sent)
        finally:
            self._producer.flush(timeout=10)
            log.info("producer.done", topic=self.topic, sent=self._sent)