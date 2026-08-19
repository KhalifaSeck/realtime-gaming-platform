-- ============================================================
-- copy/02 - COPY INTO RAW.IGDB_GAMES + RAW.STEAMSPY_GAMES
--
-- Pattern full-refresh : TRUNCATE puis COPY.
-- Necessaire car l'ingestion ecrit le meme filename chaque jour
-- (overwrite=True) et Snowflake tracke par filename -> sinon skip.
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE RTGAMING_DEV;
USE SCHEMA RAW;
USE WAREHOUSE COMPUTE_WH;

-- ---------- IGDB ----------
TRUNCATE TABLE IGDB_GAMES;

COPY INTO IGDB_GAMES (
    igdb_id, name, summary, rating, rating_count, release_date,
    genres, themes, platforms, keywords, game_modes, developer, publisher
)
FROM (
    SELECT
        $1:igdb_id::INT,
        $1:name::STRING,
        $1:summary::STRING,
        $1:rating::FLOAT,
        $1:rating_count::INT,
        $1:release_date::DATE,
        $1:genres::STRING,
        $1:themes::STRING,
        $1:platforms::STRING,
        $1:keywords::STRING,
        $1:game_modes::STRING,
        $1:developer::STRING,
        $1:publisher::STRING
    FROM @ADLS_RAW/igdb_games
)
FILE_FORMAT = (FORMAT_NAME = 'PARQUET_SNAPPY')
PATTERN = '.*\.parquet'
ON_ERROR = CONTINUE
FORCE = TRUE;

-- ---------- SteamSpy ----------
TRUNCATE TABLE STEAMSPY_GAMES;

COPY INTO STEAMSPY_GAMES (
    appid, name, developer, publisher, score_rank, owners_range, owners_estimate,
    average_forever, average_2weeks, median_forever, median_2weeks, ccu,
    price_usd, initialprice_usd, discount_pct, positive, negative, review_score,
    tags, languages, genre
)
FROM (
    SELECT
        $1:appid::INT,
        $1:name::STRING,
        $1:developer::STRING,
        $1:publisher::STRING,
        $1:score_rank::STRING,
        $1:owners_range::STRING,
        $1:owners_estimate::BIGINT,
        $1:average_forever::INT,
        $1:average_2weeks::INT,
        $1:median_forever::INT,
        $1:median_2weeks::INT,
        $1:ccu::INT,
        $1:price_usd::FLOAT,
        $1:initialprice_usd::FLOAT,
        $1:discount_pct::INT,
        $1:positive::INT,
        $1:negative::INT,
        $1:review_score::FLOAT,
        $1:tags::STRING,
        $1:languages::STRING,
        $1:genre::STRING
    FROM @ADLS_RAW/steamspy_games
)
FILE_FORMAT = (FORMAT_NAME = 'PARQUET_SNAPPY')
PATTERN = '.*\.parquet'
ON_ERROR = CONTINUE
FORCE = TRUE;

SELECT 'RAW.IGDB_GAMES'     AS tbl, COUNT(*) AS n_rows FROM IGDB_GAMES
UNION ALL SELECT 'RAW.STEAMSPY_GAMES', COUNT(*) FROM STEAMSPY_GAMES;