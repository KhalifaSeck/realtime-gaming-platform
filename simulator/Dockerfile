# ============================================================
# Simulator image
# Runs Kafka producers (purchases, reviews, sessions, wishlist).
# Deployed as k8s Deployment in Brique 15.
# ============================================================
FROM python:3.11-slim

LABEL org.opencontainers.image.title="rtgaming-simulator"
LABEL org.opencontainers.image.description="Kafka producers simulating gaming events"
LABEL org.opencontainers.image.source="https://github.com/khalifa/realtime-gaming-platform"

# Non-root user (security best-practice)
RUN groupadd -r sim && useradd -r -g sim -m -d /home/sim sim

WORKDIR /app

# Install deps first (layer cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy code
COPY src/ ./src/
COPY config/ ./config/

USER sim

# Args passed at runtime (--producers, --rate, --duration...)
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--producers", "all", "--rate", "2"]