"""Query : wishlist net par jeu par 30s -> Redis."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, when, window
from pyspark.sql.streaming import StreamingQuery

from src.kafka_reader import read_topic
from src.schemas import WISHLIST_SCHEMA
from src.sinks.redis_sink import make_writer


def start(spark: SparkSession) -> StreamingQuery:
    df = read_topic(spark, "wishlist", WISHLIST_SCHEMA)

    agg = (
        df.withWatermark("event_time", "10 seconds")
        .groupBy(
            window(col("event_time"), "30 seconds").alias("time_window"),
            col("game_id"),
        )
        .agg(
            _sum(when(col("action") == "added", 1).otherwise(0)).alias("num_added"),
            _sum(when(col("action") == "removed", 1).otherwise(0)).alias("num_removed"),
        )
        .withColumn("net_added", col("num_added") - col("num_removed"))
        .select(
            col("time_window.start").alias("window_start"),
            col("game_id"),
            col("num_added"),
            col("num_removed"),
            col("net_added"),
        )
    )

    return (
        agg.writeStream
        .queryName("wishlist_net")
        .foreachBatch(make_writer("wishlist"))
        .outputMode("update")
        .trigger(processingTime="15 seconds")
        .start()
    )