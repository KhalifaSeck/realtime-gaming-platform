FROM apache/spark:3.5.4-python3

USER root

WORKDIR /opt/spark/work-dir

RUN mkdir -p /home/spark/.ivy2/cache /home/spark/.ivy2/jars /home/spark/.ivy2/local \
 && chown -R spark:spark /home/spark

# Deps Python (sinks Redis + ADLS)
RUN pip install --no-cache-dir redis pandas pyarrow azure-storage-file-datalake

COPY src/ ./src/
RUN chown -R spark:spark /opt/spark/work-dir

ENV PYTHONPATH=/opt/spark/work-dir

USER spark

ENTRYPOINT ["/opt/spark/bin/spark-submit"]
CMD ["--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4", \
     "src/main.py"]