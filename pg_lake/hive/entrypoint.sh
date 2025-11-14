#!/bin/bash
set -e

# Set environment variables for apache/hive:4.0.0 image
export HIVE_HOME=/opt/hive
export HADOOP_HOME=/opt/hadoop

# Set S3 configuration for Hadoop
export HADOOP_OPTS="-Dfs.s3a.access.key=minioadmin -Dfs.s3a.secret.key=minioadmin -Dfs.s3a.endpoint=http://minio:9000 -Dfs.s3a.path.style.access=true"

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=hive psql -h hive-postgres -U hive -d metastore -c "SELECT 1" &> /dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is up"

# Check if schema is initialized by validating if VERSION table exists
echo "Checking schema status..."
SCHEMA_VALID=$(PGPASSWORD=hive psql -h hive-postgres -U hive -d metastore -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='VERSION'" 2>/dev/null || echo "0")

if [ "$SCHEMA_VALID" = "1" ]; then
    echo "Schema appears to be initialized, checking version..."
    ${HIVE_HOME}/bin/schematool -dbType postgres -info || {
        echo "Schema validation failed, dropping and reinitializing..."
        PGPASSWORD=hive psql -h hive-postgres -U hive -d postgres -c "DROP DATABASE metastore; CREATE DATABASE metastore OWNER hive;"
        ${HIVE_HOME}/bin/schematool -dbType postgres -initSchema
    }
else
    echo "Schema not initialized, initializing..."
    ${HIVE_HOME}/bin/schematool -dbType postgres -initSchema
fi

# Start metastore service
echo "$(date '+%Y-%m-%d %H:%M:%S'): Starting Hive Metastore Server"
exec ${HIVE_HOME}/bin/hive --service metastore
