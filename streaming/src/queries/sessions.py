"""Query : activite sessions par jeu par 30s -> Redis + ADLS."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, sum as _sum, when, window
from pyspark.sql.streaming import StreamingQuery

from src.kafka_reader import read_topic
from src.schemas import SESSION_SCHEMA
from src.sinks.adls_sink import make_writer as make_adls_writer
from src.sinks.multi import combine
from src.sinks.redis_sink import make_writer as make_redis_writer


def start(spark: SparkSession) -> StreamingQuery:
    df = read_topic(spark, "sessions", SESSION_SCHEMA)
    agg = (
        df.withWatermark("event_time", "10 seconds")
        .groupBy(
            window(col("event_time"), "30 seconds").alias("time_window"),
            col("game_id"),
        )
        .agg(
            _sum(when(col("event_type") == "session_start", 1).otherwise(0)).alias("num_starts"),
            _sum(when(col("event_type") == "session_end", 1).otherwise(0)).alias("num_ends"),
            avg(when(col("event_type") == "session_end", col("duration_seconds"))).alias("avg_duration_sec"),
        )
        .select(
            col("time_window.start").alias("window_start"),
            col("game_id"),
            col("num_starts"),
            col("num_ends"),
            col("avg_duration_sec"),
        )
    )
    return (
        agg.writeStream
        .queryName("sessions_activity")
        .foreachBatch(combine(
            make_redis_writer("sessions"),
            make_adls_writer("sessions"),
        ))
        .option("checkpointLocation", "/tmp/checkpoints/sessions_activity")
        .outputMode("update")
        .trigger(processingTime="15 seconds")
        .start()
    )