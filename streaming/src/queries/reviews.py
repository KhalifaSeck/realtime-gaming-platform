"""Query : sentiment par jeu par 30s -> Redis."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, count as _count, sum as _sum, when, window
from pyspark.sql.streaming import StreamingQuery

from src.kafka_reader import read_topic
from src.schemas import REVIEW_SCHEMA
from src.sinks.redis_sink import make_writer


def start(spark: SparkSession) -> StreamingQuery:
    df = read_topic(spark, "reviews", REVIEW_SCHEMA)

    agg = (
        df.withWatermark("event_time", "10 seconds")
        .groupBy(
            window(col("event_time"), "30 seconds").alias("time_window"),
            col("game_id"),
        )
        .agg(
            _count("*").alias("num_reviews"),
            avg("rating").alias("avg_rating"),
            (_sum(when(col("recommended"), 1).otherwise(0)) * 100.0 / _count("*"))
                .alias("recommend_pct"),
        )
        .select(
            col("time_window.start").alias("window_start"),
            col("game_id"),
            col("num_reviews"),
            col("avg_rating"),
            col("recommend_pct"),
        )
    )

    return (
        agg.writeStream
        .queryName("reviews_sentiment")
        .foreachBatch(make_writer("reviews"))
        .outputMode("update")
        .trigger(processingTime="15 seconds")
        .start()
    )