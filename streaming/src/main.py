"""
Orchestrateur multi-query.

8 queries streaming en parallele :
  - 4 aggregates : purchases_revenue, reviews_sentiment, sessions_activity, wishlist_net
  - 4 raw events : raw_events_purchases, raw_events_reviews, raw_events_sessions, raw_events_wishlist

Aggregates -> Redis + ANALYTICS Parquet
Raw events -> ADLS Parquet (charges dans RAW.STREAM_* via COPY INTO)
"""
from pyspark.sql import SparkSession

from src.queries import purchases, reviews, sessions, wishlist, raw_events


def main() -> None:
    spark = (
        SparkSession.builder
        .appName("rtg-streaming-multi")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # Aggregates (4)
    purchases.start(spark)
    reviews.start(spark)
    sessions.start(spark)
    wishlist.start(spark)

    # Raw events (4)
    raw_events.start_all(spark)

    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()