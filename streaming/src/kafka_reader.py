"""Helper commun : lit un topic Kafka -> DataFrame streaming parse."""
import os
from typing import Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType


DEFAULT_BOOTSTRAP = os.environ.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka:29092",
)


def read_topic(
    spark: SparkSession,
    topic: str,
    schema: StructType,
    bootstrap: Optional[str] = None,
) -> DataFrame:
    servers = bootstrap or DEFAULT_BOOTSTRAP
    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", servers)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .load()
    )
    return (
        raw
        .selectExpr("CAST(value AS STRING) AS json_str")
        .select(from_json(col("json_str"), schema).alias("data"))
        .select("data.*")
    )