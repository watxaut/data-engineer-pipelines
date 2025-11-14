#!/bin/bash
set -e

# Set environment variables for apache/hive:4.0.0 image
export HIVE_HOME=/opt/hive
export HADOOP_HOME=/opt/hadoop

# Set S3 configuration for Hadoop
export HADOOP_OPTS="-Dfs.s3a.access.key=minio -Dfs.s3a.secret.key=minio123 -Dfs.s3a.endpoint=http://minio:9000 -Dfs.s3a.path.style.access=true"

# Initialize schema if needed (will skip if already initialized)
${HIVE_HOME}/bin/schematool -dbType mysql -initSchema || echo "Schema already initialized or init failed, continuing..."

# Start metastore service
exec ${HIVE_HOME}/bin/hive --service metastore
