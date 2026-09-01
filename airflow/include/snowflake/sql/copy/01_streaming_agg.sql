-- ============================================================
-- COPY INTO : ADLS Parquet -> ANALYTICS.STREAM_*_AGG
-- Idempotent (metadata Snowflake tracke les fichiers deja ingerse).
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE RTGAMING_DEV;
USE SCHEMA ANALYTICS;
USE WAREHOUSE COMPUTE_WH;

COPY INTO STREAM_PURCHASES_AGG (window_start, game_id, num_purchases, revenue_net_usd)
FROM (
    SELECT
        TO_TIMESTAMP_NTZ($1:window_start::NUMBER / 1000000000),
        $1:game_id::INT,
        $1:num_purchases::INT,
        $1:revenue_net_usd::FLOAT
    FROM @RAW.ADLS_RAW/streaming/purchases
)
FILE_FORMAT = (FORMAT_NAME = 'RAW.PARQUET_SNAPPY')
PATTERN = '.*\.parquet'
ON_ERROR = CONTINUE;

COPY INTO STREAM_REVIEWS_AGG (window_start, game_id, num_reviews, avg_rating, recommend_pct)
FROM (
    SELECT
        TO_TIMESTAMP_NTZ($1:window_start::NUMBER / 1000000000),
        $1:game_id::INT,
        $1:num_reviews::INT,
        $1:avg_rating::FLOAT,
        $1:recommend_pct::FLOAT
    FROM @RAW.ADLS_RAW/streaming/reviews
)
FILE_FORMAT = (FORMAT_NAME = 'RAW.PARQUET_SNAPPY')
PATTERN = '.*\.parquet'
ON_ERROR = CONTINUE;

COPY INTO STREAM_SESSIONS_AGG (window_start, game_id, num_starts, num_ends, avg_duration_sec)
FROM (
    SELECT
        TO_TIMESTAMP_NTZ($1:window_start::NUMBER / 1000000000),
        $1:game_id::INT,
        $1:num_starts::INT,
        $1:num_ends::INT,
        $1:avg_duration_sec::FLOAT
    FROM @RAW.ADLS_RAW/streaming/sessions
)
FILE_FORMAT = (FORMAT_NAME = 'RAW.PARQUET_SNAPPY')
PATTERN = '.*\.parquet'
ON_ERROR = CONTINUE;

COPY INTO STREAM_WISHLIST_AGG (window_start, game_id, num_added, num_removed, net_added)
FROM (
    SELECT
        TO_TIMESTAMP_NTZ($1:window_start::NUMBER / 1000000000),
        $1:game_id::INT,
        $1:num_added::INT,
        $1:num_removed::INT,
        $1:net_added::INT
    FROM @RAW.ADLS_RAW/streaming/wishlist
)
FILE_FORMAT = (FORMAT_NAME = 'RAW.PARQUET_SNAPPY')
PATTERN = '.*\.parquet'
ON_ERROR = CONTINUE;