# ============================================================
# FastAPI - Realtime Gaming Platform API
# ============================================================
FROM python:3.11-slim

LABEL org.opencontainers.image.title="rtgaming-api"
LABEL org.opencontainers.image.description="FastAPI: Snowflake marts + Neo4j KG + Redis live state"

RUN groupadd -r api && useradd -r -g api -m -d /home/api api

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
RUN chown -R api:api /app

USER api

EXPOSE 8000

ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]