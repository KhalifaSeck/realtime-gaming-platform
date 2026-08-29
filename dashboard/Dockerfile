# ============================================================
# Streamlit Dashboard
# ============================================================
FROM python:3.11-slim

LABEL org.opencontainers.image.title="rtgaming-dashboard"
LABEL org.opencontainers.image.description="Streamlit dashboard - 6 pages"

RUN groupadd -r st && useradd -r -g st -m -d /home/st st

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY .streamlit/ ./.streamlit/
COPY Home.py api_client.py config.py styles.py ./
COPY pages/ ./pages/

RUN chown -R st:st /app

USER st

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "Home.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]