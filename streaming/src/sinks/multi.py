"""Combine plusieurs sinks foreachBatch en un seul appel."""
from typing import Callable

from pyspark.sql import DataFrame


def combine(*writers: Callable) -> Callable:
    """Retourne un writer qui applique tous les sinks au meme batch.

    persist() evite de recomputer le DF pour chaque sink.
    """
    def _combined(batch_df: DataFrame, batch_id: int) -> None:
        batch_df.persist()
        try:
            for w in writers:
                w(batch_df, batch_id)
        finally:
            batch_df.unpersist()

    return _combined