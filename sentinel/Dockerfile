# ============================================================
# Sentinel AI - LangGraph agent (Ollama + Qwen3)
# ============================================================
FROM python:3.11-slim

LABEL org.opencontainers.image.title="rtgaming-sentinel"
LABEL org.opencontainers.image.description="LangGraph AI agent over rtgaming platform"

RUN groupadd -r sentinel && useradd -r -g sentinel -m -d /home/sentinel sentinel

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
RUN chown -R sentinel:sentinel /app

USER sentinel

EXPOSE 8888

ENTRYPOINT ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8888"]