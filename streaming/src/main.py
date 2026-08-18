"""
Job Spark Structured Streaming - Etape 3.

Aggregation windowed sur le topic 'purchases' :
  - fenetres tumbling 30s (event_time based)
  - watermark 10s (tolerance late data)
  - metriques par jeu : num_purchases, revenue_net_usd, avg_price
  - output mode 'update' -> partial aggregates emis chaque trigger

Pour tester :
  Terminal Spark : docker run --rm --network ... rtgaming-streaming:dev
  Terminal producer : python -m src.main --producers purchases --rate 5 --duration 120
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    count as _count,
    from_json,
    sum as _sum,
    window,
)

from src.schemas import PURCHASE_SCHEMA

# --- Config dev (bumper pour la prod) ---
WINDOW_DURATION = "30 seconds"
WATERMARK_DELAY = "10 seconds"
TRIGGER_INTERVAL = "10 seconds"


def main() -> None:
    spark = (
        SparkSession.builder
        .appName("rtg-streaming-purchases-windowed")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    kafka_bootstrap = "kafka:29092"

    # --- Source Kafka (uniquement nouveaux events, ignore historique) ---
    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", "purchases")
        .option("startingOffsets", "latest")
        .load()
    )

    # --- Parse JSON -> struct type ---
    parsed = (
        raw
        .selectExpr("CAST(value AS STRING) AS json_str")
        .select(from_json(col("json_str"), PURCHASE_SCHEMA).alias("data"))
        .select("data.*")
    )

    # --- Enrichir avec le revenu net (apres discount) ---
    with_net = parsed.withColumn(
        "revenue_net",
        col("price_usd") * (1 - col("discount_pct") / 100.0),
    )

    # --- Aggregation windowed par jeu ---
    aggregated = (
        with_net
        .withWatermark("event_time", WATERMARK_DELAY)
        .groupBy(
            window(col("event_time"), WINDOW_DURATION).alias("time_window"),
            col("game_id"),
        )
        .agg(
            _count("*").alias("num_purchases"),
            _sum("revenue_net").alias("revenue_net_usd"),
            avg("price_usd").alias("avg_price"),
        )
        .select(
            col("time_window.start").alias("window_start"),
            col("time_window.end").alias("window_end"),
            col("game_id"),
            col("num_purchases"),
            col("revenue_net_usd"),
            col("avg_price"),
        )
        .orderBy(col("window_start").desc(), col("revenue_net_usd").desc())
    )

    # --- Sink console (update mode : partial aggregates emis chaque trigger) ---
    query = (
        aggregated.writeStream
        .format("console")
        .option("truncate", "false")
        .outputMode("complete")   # complete requis quand orderBy present
        .trigger(processingTime=TRIGGER_INTERVAL)
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()