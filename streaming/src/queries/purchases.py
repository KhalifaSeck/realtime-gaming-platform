"""Query : revenu net + nb achats par jeu par fenetre 30s -> Redis."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count as _count, sum as _sum, window
from pyspark.sql.streaming import StreamingQuery

from src.kafka_reader import read_topic
from src.schemas import PURCHASE_SCHEMA
from src.sinks.redis_sink import make_writer


def start(spark: SparkSession) -> StreamingQuery:
    df = read_topic(spark, "purchases", PURCHASE_SCHEMA)

    with_net = df.withColumn(
        "revenue_net",
        col("price_usd") * (1 - col("discount_pct") / 100.0),
    )

    agg = (
        with_net
        .withWatermark("event_time", "10 seconds")
        .groupBy(
            window(col("event_time"), "30 seconds").alias("time_window"),
            col("game_id"),
        )
        .agg(
            _count("*").alias("num_purchases"),
            _sum("revenue_net").alias("revenue_net_usd"),
        )
        .select(
            col("time_window.start").alias("window_start"),
            col("game_id"),
            col("num_purchases"),
            col("revenue_net_usd"),
        )
    )

    return (
        agg.writeStream
        .queryName("purchases_revenue")
        .foreachBatch(make_writer("purchases"))
        .outputMode("update")
        .trigger(processingTime="15 seconds")
        .start()
    )