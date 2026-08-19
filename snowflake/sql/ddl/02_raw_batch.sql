-- ============================================================
-- Tables RAW pour les sources batch (IGDB + SteamSpy)
-- Schema aligne avec les CSV cibles (voir exemples).
--
-- NOTE : l'ingestion actuelle (Brique 2) ne remplit pas encore
-- tous les champs (themes, keywords, tags, languages, etc.).
-- Etape 5b : enrichir l'ingestion pour matcher.
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE RTGAMING_DEV;
USE SCHEMA RAW;
USE WAREHOUSE COMPUTE_WH;

-- ---------- IGDB ----------
CREATE OR REPLACE TABLE IGDB_GAMES (
    igdb_id       INT,
    name          STRING,
    summary       STRING,
    rating        FLOAT,
    rating_count  INT,
    release_date  DATE,
    genres        STRING,  -- comma-separated (ex: "Shooter, Racing, Adventure")
    themes        STRING,
    platforms     STRING,
    keywords      STRING,
    game_modes    STRING,
    developer     STRING,
    publisher     STRING,
    _loaded_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ---------- SteamSpy ----------
CREATE OR REPLACE TABLE STEAMSPY_GAMES (
    appid              INT,
    name               STRING,
    developer          STRING,
    publisher          STRING,
    score_rank         STRING,
    owners_range       STRING,   -- "100,000,000 .. 200,000,000"
    owners_estimate    BIGINT,   -- midpoint calcule
    average_forever    INT,
    average_2weeks     INT,
    median_forever     INT,
    median_2weeks      INT,
    ccu                INT,
    price_usd          FLOAT,
    initialprice_usd   FLOAT,
    discount_pct       INT,
    positive           INT,
    negative           INT,
    review_score       FLOAT,   -- % positif (calcule)
    tags               STRING,  -- comma-separated (depuis appdetails)
    languages          STRING,
    genre              STRING,
    _loaded_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

SHOW TABLES IN SCHEMA RAW;