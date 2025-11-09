#!/bin/bash
set -e

echo "Starting pgduck_server..."

# Configure AWS/S3 credentials for MinIO in postgres user's home
mkdir -p /var/lib/postgresql/.aws
cat > /var/lib/postgresql/.aws/config << EOF
[services testing-minio]
s3 =
   endpoint_url = ${S3_ENDPOINT}

[profile minio]
region = ${AWS_DEFAULT_REGION}
services = testing-minio
EOF

cat > /var/lib/postgresql/.aws/credentials << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF

# Create init SQL file for MinIO S3 secrets
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

# Start pgduck_server on Unix socket
echo "pgduck_server starting on Unix socket at /home/postgres/pgduck_socket_dir"
exec pgduck_server \
    --init_file_path /tmp/pgduck_init.sql \
    --port 5332 \
    --unix_socket_directory /home/postgres/pgduck_socket_dir

