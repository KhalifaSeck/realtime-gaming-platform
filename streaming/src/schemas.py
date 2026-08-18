"""
Schemas Spark pour les 4 topics Kafka.

Source de verite unique - toute mise a jour du format cote producer
doit etre reflete ici en meme temps.
"""
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


PURCHASE_SCHEMA = StructType([
    StructField("event_id",       StringType(),    False),
    StructField("event_type",     StringType(),    False),
    StructField("event_time",     TimestampType(), False),
    StructField("user_id",        StringType(),    False),
    StructField("game_id",        IntegerType(),   False),
    StructField("price_usd",      DoubleType(),    False),
    StructField("discount_pct",   IntegerType(),   True),
    StructField("payment_method", StringType(),    True),
    StructField("country",        StringType(),    True),
])


REVIEW_SCHEMA = StructType([
    StructField("event_id",            StringType(),    False),
    StructField("event_type",          StringType(),    False),
    StructField("event_time",          TimestampType(), False),
    StructField("user_id",             StringType(),    False),
    StructField("game_id",             IntegerType(),   False),
    StructField("rating",              IntegerType(),   False),
    StructField("recommended",         BooleanType(),   False),
    StructField("hours_played",        DoubleType(),    True),
    StructField("review_length_chars", IntegerType(),   True),
    StructField("language",            StringType(),    True),
    StructField("helpful_votes",       IntegerType(),   True),
])


# Note : session_start/heartbeat/end n'ont pas exactement les memes champs.
# On declare le sur-ensemble ; les champs absents seront NULL.
SESSION_SCHEMA = StructType([
    StructField("event_id",         StringType(),    False),
    StructField("event_type",       StringType(),    False),  # start/heartbeat/end
    StructField("event_time",       TimestampType(), False),
    StructField("session_id",       StringType(),    False),
    StructField("user_id",          StringType(),    False),
    StructField("game_id",          IntegerType(),   False),
    StructField("platform",         StringType(),    True),   # seulement sur session_start
    StructField("device",           StringType(),    True),   # seulement sur session_start
    StructField("duration_seconds", IntegerType(),   True),   # seulement sur session_end
])


WISHLIST_SCHEMA = StructType([
    StructField("event_id",   StringType(),    False),
    StructField("event_type", StringType(),    False),
    StructField("event_time", TimestampType(), False),
    StructField("user_id",    StringType(),    False),
    StructField("game_id",    IntegerType(),   False),
    StructField("action",     StringType(),    False),   # added / removed
    StructField("source",     StringType(),    True),
])


# Registry : mapping topic -> schema, pratique pour boucler sur les 4 plus tard
TOPIC_SCHEMAS = {
    "purchases": PURCHASE_SCHEMA,
    "reviews":   REVIEW_SCHEMA,
    "sessions":  SESSION_SCHEMA,
    "wishlist":  WISHLIST_SCHEMA,
}