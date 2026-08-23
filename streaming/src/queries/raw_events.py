"""4 queries qui ecrivent les raw events (parses, non aggreges) vers ADLS."""
from __future__ import annotations

from pyspark.sql import SparkSession
from pyspark.sql.streaming import StreamingQuery

from src.kafka_reader import read_topic
from src.schemas import TOPIC_SCHEMAS
from src.sinks.adls_raw_events_sink import make_writer


def start_all(spark: SparkSession) -> list[StreamingQuery]:
    queries: list[StreamingQuery] = []
    for topic, schema in TOPIC_SCHEMAS.items():
        df = read_topic(spark, topic, schema)
        query = (
            df.writeStream
            .queryName(f"raw_events_{topic}")
            .foreachBatch(make_writer(topic))
            .option("checkpointLocation", f"/tmp/checkpoints/raw_events_{topic}")
            .outputMode("append")
            .trigger(processingTime="30 seconds")
            .start()
        )
        queries.append(query)
    return queries