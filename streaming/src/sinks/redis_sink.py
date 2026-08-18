"""
Sink Redis : ecrit chaque micro-batch aggregat dans Redis en Hash.

Cle : stat:{metric_name}:{game_id}
Valeur : Hash avec les colonnes du DataFrame + window_start + updated_at
TTL : 10 minutes (auto-cleanup)
"""
from __future__ import annotations

import json
import os
import time
from typing import Callable

import redis
from pyspark.sql import DataFrame

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_TTL_SEC = 600  # 10 min


def make_writer(metric_name: str, key_col: str = "game_id") -> Callable:
    """
    Renvoie une fonction foreachBatch(batch_df, batch_id) qui ecrit
    chaque ligne dans Redis sous la cle stat:{metric_name}:{game_id}.
    """
    def _write(batch_df: DataFrame, batch_id: int) -> None:
        rows = batch_df.collect()
        if not rows:
            return

        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        pipe = client.pipeline()
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        for row in rows:
            row_dict = row.asDict()
            key_value = row_dict.get(key_col)
            if key_value is None:
                continue
            redis_key = f"stat:{metric_name}:{key_value}"

            # Redis Hash accepte str only -> serialise datetimes/nombres
            fields = {}
            for k, v in row_dict.items():
                if v is None:
                    continue
                if hasattr(v, "isoformat"):  # datetime
                    fields[k] = v.isoformat()
                else:
                    fields[k] = str(v)
            fields["updated_at"] = now_iso

            pipe.hset(redis_key, mapping=fields)
            pipe.expire(redis_key, REDIS_TTL_SEC)

        pipe.execute()
        print(f"[redis_sink] batch {batch_id} -> {len(rows)} keys under stat:{metric_name}:*")

    return _write