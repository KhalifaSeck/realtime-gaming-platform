-- ============================================================
-- ddl/01 - Tables ANALYTICS.STREAM_*_AGG
-- CREATE OR REPLACE => drop + create, garantit un etat propre.
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE RTGAMING_DEV;
USE SCHEMA ANALYTICS;
USE WAREHOUSE COMPUTE_WH;

CREATE OR REPLACE TABLE STREAM_PURCHASES_AGG (
    window_start     TIMESTAMP_NTZ,
    game_id          INT,
    num_purchases    INT,
    revenue_net_usd  FLOAT,
    _loaded_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE STREAM_REVIEWS_AGG (
    window_start   TIMESTAMP_NTZ,
    game_id        INT,
    num_reviews    INT,
    avg_rating     FLOAT,
    recommend_pct  FLOAT,
    _loaded_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE STREAM_SESSIONS_AGG (
    window_start      TIMESTAMP_NTZ,
    game_id           INT,
    num_starts        INT,
    num_ends          INT,
    avg_duration_sec  FLOAT,
    _loaded_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE STREAM_WISHLIST_AGG (
    window_start   TIMESTAMP_NTZ,
    game_id        INT,
    num_added      INT,
    num_removed    INT,
    net_added      INT,
    _loaded_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

SHOW TABLES IN SCHEMA ANALYTICS;