"""ReviewProducer : avis Steam-like sur des jeux."""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any

from faker import Faker

from src.producers.base import BaseProducer
from src.producers.purchases import GAME_IDS  # reuse pool

fake = Faker()

LANGUAGES = ["en", "fr", "de", "es", "ja", "pt", "ko", "ru", "zh", "it"]


class ReviewProducer(BaseProducer):
    topic = "reviews"

    def generate_event(self) -> dict[str, Any]:
        recommended = random.random() > 0.25  # 75% avis positifs
        rating = random.randint(7, 10) if recommended else random.randint(1, 6)
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "review_posted",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "user_id": fake.uuid4(),
            "game_id": random.choice(GAME_IDS),
            "rating": rating,
            "recommended": recommended,
            "hours_played": round(random.uniform(0.5, 500.0), 1),
            "review_length_chars": random.randint(20, 2000),
            "language": random.choice(LANGUAGES),
            "helpful_votes": random.randint(0, 500),
        }


if __name__ == "__main__":
    producer = ReviewProducer()
    producer.run(rate_per_second=2.0, max_events=20)