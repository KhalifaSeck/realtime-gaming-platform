"""PurchaseProducer : evenements d'achat de jeux fake."""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any

from faker import Faker

from src.producers.base import BaseProducer

fake = Faker()

# Pool de vrais appids Steam (top jeux) pour realisme
GAME_IDS = [
    730,      # CS:GO
    570,      # Dota 2
    1172470,  # Apex Legends
    578080,   # PUBG
    292030,   # Witcher 3
    271590,   # GTA V
    1091500,  # Cyberpunk 2077
    990080,   # Hogwarts Legacy
    1174180,  # Red Dead Redemption 2
    105600,   # Terraria
]
PAYMENT_METHODS = ["credit_card", "paypal", "steam_wallet", "bank_transfer"]
COUNTRIES = ["US", "FR", "DE", "GB", "JP", "BR", "KR", "CA", "AU", "NL"]


class PurchaseProducer(BaseProducer):
    topic = "purchases"

    def generate_event(self) -> dict[str, Any]:
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "game_purchased",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "user_id": fake.uuid4(),
            "game_id": random.choice(GAME_IDS),
            "price_usd": round(random.uniform(0.99, 59.99), 2),
            "discount_pct": random.choice([0, 0, 0, 25, 50, 75]),
            "payment_method": random.choice(PAYMENT_METHODS),
            "country": random.choice(COUNTRIES),
        }


# Self-test : envoie 20 evenements a 2/sec
if __name__ == "__main__":
    producer = PurchaseProducer()
    producer.run(rate_per_second=2.0, max_events=20)