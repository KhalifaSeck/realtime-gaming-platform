"""
Orchestrateur multi-query.

Lance 4 queries streaming en parallele dans le meme SparkSession :
  - purchases_revenue
  - reviews_sentiment
  - sessions_activity
  - wishlist_net

Chaque query est definie dans src/queries/<topic>.py.
Le sink est 'console' pour debug ; les vrais sinks (Redis, ADLS)
seront branches en Brique 5.
"""
from pyspark.sql import SparkSession

from src.queries import purchases, reviews, sessions, wishlist


def main() -> None:
    spark = (
        SparkSession.builder
        .appName("rtg-streaming-multi")
        .config("spark.sql.shuffle.partitions", "4")  # dev-friendly (default 200)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # Lance les 4 queries (elles tournent en threads Spark)
    purchases.start(spark)
    reviews.start(spark)
    sessions.start(spark)
    wishlist.start(spark)

    # Attend qu'une query termine (ou Ctrl+C)
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()