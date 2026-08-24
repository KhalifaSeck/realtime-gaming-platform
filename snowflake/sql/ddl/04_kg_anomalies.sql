-- ============================================================
-- ddl/04 - Table ANALYTICS.KG_ANOMALIES
-- Populee par graph/src/anomalies.py (Neo4j -> Snowflake).
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE RTGAMING_DEV;
USE SCHEMA ANALYTICS;
USE WAREHOUSE COMPUTE_WH;

CREATE OR REPLACE TABLE KG_ANOMALIES (
    ANOMALY_TYPE     STRING,
    ENTITY_NAME      STRING,
    ENTITY_TYPE      STRING,
    RELATED_ENTITY   STRING,
    DESCRIPTION      STRING,
    METRIC_VALUE     FLOAT,
    SEVERITY         STRING,
    _LOADED_AT       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);