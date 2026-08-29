FROM python:3.11-slim

LABEL org.opencontainers.image.title="rtgaming-dashboard"
LABEL org.opencontainers.image.description="Streamlit dashboard for rtgaming platform"

RUN groupadd -r dash && useradd -r -g dash -m -d /home/dash dash

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Streamlit convention : tout au root
COPY Home.py api_client.py config.py styles.py ./
COPY pages/ ./pages/
COPY .streamlit/ ./.streamlit/

RUN chown -R dash:dash /app

USER dash

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "Home.py", \
            "--server.address=0.0.0.0", \
            "--server.port=8501", \
            "--server.headless=true", \
            "--browser.gatherUsageStats=false"]