#!/bin/bash
set -e

# Configure AWS credentials for pgduck_server
mkdir -p ~/.aws
cat > ~/.aws/config << EOF
[services testing-minio]
s3 =
   endpoint_url = http://minio:9000

[profile minio]
region = us-east-1
services = testing-minio
EOF

cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF

# Create pgduck_server init file for MinIO credentials BEFORE starting anything
cat > /tmp/pgduck_init.sql << EOF
CREATE SECRET IF NOT EXISTS s3_minio (
    TYPE S3,
    KEY_ID '${AWS_ACCESS_KEY_ID}',
    SECRET '${AWS_SECRET_ACCESS_KEY}',
    ENDPOINT 'minio:9000',
    SCOPE 's3://warehouse',
    URL_STYLE 'path',
    USE_SSL false
);
EOF

# Start pgduck_server FIRST (in background)
echo "Starting pgduck_server..."
echo "Checking if pgduck_server is available..."
which pgduck_server || echo "WARNING: pgduck_server not found in PATH"
pgduck_server --init_file_path /tmp/pgduck_init.sql --port 5332 &
PGDUCK_PID=$!

# Wait for pgduck_server to be ready
echo "Waiting for pgduck_server to start..."
for i in {1..30}; do
    if psql -h localhost -p 5332 -U postgres -c "SELECT 1" >/dev/null 2>&1; then
        echo "pgduck_server is ready!"
        break
    fi
    echo "Attempt $i/30: pgduck_server not ready yet..."
    sleep 1
done

# Now start PostgreSQL
echo "Starting PostgreSQL..."
pg_ctl -D "$PGDATA" -o "-c listen_addresses='*'" -w start

# Create database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username postgres <<-EOSQL
    SELECT 'CREATE DATABASE ${POSTGRES_DB}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${POSTGRES_DB}')\gexec
EOSQL

# Connect to the database and create extensions
psql -v ON_ERROR_STOP=1 --username postgres --dbname "${POSTGRES_DB}" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pg_lake CASCADE;
EOSQL

echo "PostgreSQL and pgduck_server started successfully!"
echo "PostgreSQL listening on port 5432"
echo "pgduck_server listening on port 5332"

# Keep container running
tail -f /dev/null

