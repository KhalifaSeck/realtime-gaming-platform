# ============================================================
# Ingestion service image
# Runs the IGDB + SteamSpy batch fetcher into ADLS Gen2.
# Triggered by Airflow (Brique 13) as a KubernetesPodOperator.
# ============================================================
FROM python:3.11-slim

# --- Metadata (OCI labels) ---
LABEL org.opencontainers.image.title="rtgaming-ingestion"
LABEL org.opencontainers.image.description="Batch ingestion IGDB + SteamSpy -> ADLS Gen2"
LABEL org.opencontainers.image.source="https://github.com/khalifa/realtime-gaming-platform"

# --- Non-root user (security best-practice) ---
RUN groupadd -r ingest && useradd -r -g ingest -m -d /home/ingest ingest

WORKDIR /app

# --- Install Python deps first (layer cache friendly) ---
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# --- Copy application code ---
COPY src/ ./src/
COPY config/ ./config/

# --- Drop privileges ---
USER ingest

# --- Entrypoint : args passed at runtime ---
# Example : docker run <image> --source igdb --limit 100
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--source", "all"]