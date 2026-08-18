"""
SessionProducer : lifecycle des sessions de jeu.

3 sous-types :
  - session_start
  - session_heartbeat (emis pendant que la session tourne)
  - session_end
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any

from faker import Faker

from src.producers.base import BaseProducer
from src.producers.purchases import GAME_IDS

fake = Faker()

PLATFORMS = ["windows", "macos", "linux", "steam_deck"]
DEVICES = ["desktop", "laptop", "handheld"]
EVENT_TYPES = ["session_start", "session_heartbeat", "session_end"]


class SessionProducer(BaseProducer):
    topic = "sessions"

    def generate_event(self) -> dict[str, Any]:
        # 20% starts, 60% heartbeats, 20% ends -> distribution realiste
        event_type = random.choices(
            EVENT_TYPES,
            weights=[20, 60, 20],
            k=1,
        )[0]
        event: dict[str, Any] = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "event_time": datetime.now(timezone.utc).isoformat(),
            "session_id": str(uuid.uuid4()),
            "user_id": fake.uuid4(),
            "game_id": random.choice(GAME_IDS),
        }
        if event_type == "session_start":
            event["platform"] = random.choice(PLATFORMS)
            event["device"] = random.choice(DEVICES)
        elif event_type == "session_end":
            event["duration_seconds"] = random.randint(60, 14400)  # 1min - 4h
        return event


if __name__ == "__main__":
    producer = SessionProducer()
    producer.run(rate_per_second=3.0, max_events=30)