FROM astrocrpublic.azurecr.io/runtime:3.3-2
USER root
RUN apt-get update && apt-get install -y --no-install-recommends git curl && \
    rm -rf /var/lib/apt/lists/*
USER astro

ENV DBT_PROFILES_DIR="/usr/local/airflow/include/gaming_dbt"