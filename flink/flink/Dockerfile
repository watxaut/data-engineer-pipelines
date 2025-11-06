FROM flink:1.18.0-scala_2.12-java11

# Install required dependencies
USER root

# Download Flink connectors and dependencies
RUN mkdir -p /opt/flink/lib && \
    cd /opt/flink/lib && \
    # Flink SQL client
    wget -q https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/1.18.0/flink-sql-connector-kafka-1.18.0.jar && \
    # ClickHouse connector
    wget -q https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.4.6/clickhouse-jdbc-0.4.6-all.jar && \
    # Iceberg connector for Flink
    wget -q https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-flink-runtime-1.18/1.4.2/iceberg-flink-runtime-1.18-1.4.2.jar && \
    # AWS S3 (for MinIO)
    wget -q https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    wget -q https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar && \
    # RocksDB state backend
    wget -q https://repo1.maven.org/maven2/org/apache/flink/flink-statebackend-rocksdb/1.18.0/flink-statebackend-rocksdb-1.18.0.jar

# Copy configuration files
COPY conf/flink-conf.yaml /opt/flink/conf/flink-conf.yaml

# Create jobs directory
RUN mkdir -p /opt/flink/jobs

# Set permissions
RUN chown -R flink:flink /opt/flink

USER flink

WORKDIR /opt/flink
