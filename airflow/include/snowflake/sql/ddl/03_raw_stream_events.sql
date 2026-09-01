-- ============================================================
-- ddl/03 - Tables RAW.STREAM_* (event-level, non aggreges).
-- Peuplees par le sink Spark raw events (Etape a venir).
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE RTGAMING_DEV;
USE SCHEMA RAW;
USE WAREHOUSE COMPUTE_WH;

CREATE OR REPLACE TABLE STREAM_PURCHASES (
    event_id         STRING,
    event_type       STRING,
    event_time       TIMESTAMP_NTZ,
    user_id          STRING,
    game_id          INT,
    price_usd        FLOAT,
    discount_pct     INT,
    payment_method   STRING,
    country          STRING,
    _loaded_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE STREAM_REVIEWS (
    event_id             STRING,
    event_type           STRING,
    event_time           TIMESTAMP_NTZ,
    user_id              STRING,
    game_id              INT,
    rating               INT,
    recommended          BOOLEAN,
    hours_played         FLOAT,
    review_length_chars  INT,
    language             STRING,
    helpful_votes        INT,
    _loaded_at           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE STREAM_SESSIONS (
    event_id         STRING,
    event_type       STRING,
    event_time       TIMESTAMP_NTZ,
    session_id       STRING,
    user_id          STRING,
    game_id          INT,
    platform         STRING,
    device           STRING,
    duration_seconds INT,
    _loaded_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE STREAM_WISHLIST (
    event_id      STRING,
    event_type    STRING,
    event_time    TIMESTAMP_NTZ,
    user_id       STRING,
    game_id       INT,
    action        STRING,
    source        STRING,
    _loaded_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

SHOW TABLES IN SCHEMA RAW;