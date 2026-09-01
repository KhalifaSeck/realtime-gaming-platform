-- ============================================================
-- copy/03 - COPY INTO RAW.STREAM_* depuis raw/streaming_events/
-- Idempotent (Snowflake tracke files loaded).
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE RTGAMING_DEV;
USE SCHEMA RAW;
USE WAREHOUSE COMPUTE_WH;

COPY INTO STREAM_PURCHASES (event_id, event_type, event_time, user_id, game_id, price_usd, discount_pct, payment_method, country)
FROM (
    SELECT
        $1:event_id::STRING,
        $1:event_type::STRING,
        $1:event_time::TIMESTAMP_NTZ,
        $1:user_id::STRING,
        $1:game_id::INT,
        $1:price_usd::FLOAT,
        $1:discount_pct::INT,
        $1:payment_method::STRING,
        $1:country::STRING
    FROM @ADLS_RAW/streaming_events/purchases
)
FILE_FORMAT = (FORMAT_NAME = 'PARQUET_SNAPPY')
PATTERN = '.*\.parquet'
ON_ERROR = CONTINUE;

COPY INTO STREAM_REVIEWS (event_id, event_type, event_time, user_id, game_id, rating, recommended, hours_played, review_length_chars, language, helpful_votes)
FROM (
    SELECT
        $1:event_id::STRING,
        $1:event_type::STRING,
        $1:event_time::TIMESTAMP_NTZ,
        $1:user_id::STRING,
        $1:game_id::INT,
        $1:rating::INT,
        $1:recommended::BOOLEAN,
        $1:hours_played::FLOAT,
        $1:review_length_chars::INT,
        $1:language::STRING,
        $1:helpful_votes::INT
    FROM @ADLS_RAW/streaming_events/reviews
)
FILE_FORMAT = (FORMAT_NAME = 'PARQUET_SNAPPY')
PATTERN = '.*\.parquet'
ON_ERROR = CONTINUE;

COPY INTO STREAM_SESSIONS (event_id, event_type, event_time, session_id, user_id, game_id, platform, device, duration_seconds)
FROM (
    SELECT
        $1:event_id::STRING,
        $1:event_type::STRING,
        $1:event_time::TIMESTAMP_NTZ,
        $1:session_id::STRING,
        $1:user_id::STRING,
        $1:game_id::INT,
        $1:platform::STRING,
        $1:device::STRING,
        $1:duration_seconds::INT
    FROM @ADLS_RAW/streaming_events/sessions
)
FILE_FORMAT = (FORMAT_NAME = 'PARQUET_SNAPPY')
PATTERN = '.*\.parquet'
ON_ERROR = CONTINUE;

COPY INTO STREAM_WISHLIST (event_id, event_type, event_time, user_id, game_id, action, source)
FROM (
    SELECT
        $1:event_id::STRING,
        $1:event_type::STRING,
        $1:event_time::TIMESTAMP_NTZ,
        $1:user_id::STRING,
        $1:game_id::INT,
        $1:action::STRING,
        $1:source::STRING
    FROM @ADLS_RAW/streaming_events/wishlist
)
FILE_FORMAT = (FORMAT_NAME = 'PARQUET_SNAPPY')
PATTERN = '.*\.parquet'
ON_ERROR = CONTINUE;

SELECT 'STREAM_PURCHASES' AS tbl, COUNT(*) AS n_rows FROM STREAM_PURCHASES
UNION ALL SELECT 'STREAM_REVIEWS',   COUNT(*) FROM STREAM_REVIEWS
UNION ALL SELECT 'STREAM_SESSIONS',  COUNT(*) FROM STREAM_SESSIONS
UNION ALL SELECT 'STREAM_WISHLIST',  COUNT(*) FROM STREAM_WISHLIST;