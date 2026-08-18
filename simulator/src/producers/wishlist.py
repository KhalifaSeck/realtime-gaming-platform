"""WishlistProducer : ajouts/suppressions dans la wishlist."""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any

from faker import Faker

from src.producers.base import BaseProducer
from src.producers.purchases import GAME_IDS

fake = Faker()

ACTIONS = ["added", "removed"]
SOURCES = ["search", "recommendation", "friend_activity", "store_page", "sale_page"]


class WishlistProducer(BaseProducer):
    topic = "wishlist"

    def generate_event(self) -> dict[str, Any]:
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "wishlist_action",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "user_id": fake.uuid4(),
            "game_id": random.choice(GAME_IDS),
            # 85% adds, 15% removes -> comportement realiste
            "action": random.choices(ACTIONS, weights=[85, 15], k=1)[0],
            "source": random.choice(SOURCES),
        }


if __name__ == "__main__":
    producer = WishlistProducer()
    producer.run(rate_per_second=2.0, max_events=20)