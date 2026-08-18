# ============================================================
# Spark Structured Streaming image
# Base : apache/spark 3.5 (Python + JVM + Spark preinstalles)
# ============================================================
FROM apache/spark:3.5.4-python3

USER root

WORKDIR /opt/spark/work-dir

# Cache Ivy (obligatoire pour --packages ; non cree par defaut dans l'image)
RUN mkdir -p /home/spark/.ivy2/cache /home/spark/.ivy2/jars /home/spark/.ivy2/local \
 && chown -R spark:spark /home/spark

# Copie du code Python
COPY src/ ./src/
RUN chown -R spark:spark /opt/spark/work-dir

# PYTHONPATH : autorise 'from src.xxx import ...' dans les scripts
ENV PYTHONPATH=/opt/spark/work-dir

USER spark

ENTRYPOINT ["/opt/spark/bin/spark-submit"]
CMD ["--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4", \
     "src/main.py"]