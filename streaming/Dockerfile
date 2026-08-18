# ============================================================
# Spark Structured Streaming image
# Base : apache/spark 3.5 (Python + JVM + Spark preinstalles)
# ============================================================
FROM apache/spark:3.5.4-python3

USER root

WORKDIR /opt/spark/work-dir

# Cache Ivy pour --packages
RUN mkdir -p /home/spark/.ivy2/cache /home/spark/.ivy2/jars /home/spark/.ivy2/local \
 && chown -R spark:spark /home/spark

# Deps Python additionnelles (redis-py pour sinks)
RUN pip install --no-cache-dir redis

# Copie du code
COPY src/ ./src/
RUN chown -R spark:spark /opt/spark/work-dir

ENV PYTHONPATH=/opt/spark/work-dir

USER spark

ENTRYPOINT ["/opt/spark/bin/spark-submit"]
CMD ["--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4", \
     "src/main.py"]