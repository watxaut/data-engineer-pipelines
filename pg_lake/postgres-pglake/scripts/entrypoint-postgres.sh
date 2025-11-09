#!/bin/bash
set -e

echo "Starting PostgreSQL with pg_lake..."

# Wait for pgduck_server socket to be available
SOCKET_PATH="/home/postgres/pgduck_socket_dir/.s.PGSQL.5332"
echo "Waiting for pgduck_server socket at $SOCKET_PATH..."
for i in {1..30}; do
    if [ -S "$SOCKET_PATH" ]; then
        echo "pgduck_server socket is ready!"
        break
    fi
    echo "Attempt $i/30: Waiting for pgduck_server socket..."
    sleep 2
done

if [ ! -S "$SOCKET_PATH" ]; then
    echo "ERROR: pgduck_server socket not found after 60 seconds!"
    exit 1
fi

# Initialize PostgreSQL if needed
if [ ! -d "$PGDATA/base" ]; then
    echo "Initializing PostgreSQL database..."
    initdb -D "$PGDATA" -k --locale=C.UTF-8
    
    # Configure PostgreSQL
    cat >> "$PGDATA/postgresql.conf" << EOF
shared_preload_libraries = 'pg_extension_base'
listen_addresses = '*'
port = 5432
EOF
    
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
    echo "local all all trust" >> "$PGDATA/pg_hba.conf"
fi

# Start PostgreSQL
echo "Starting PostgreSQL server..."
pg_ctl -D "$PGDATA" -o "-c listen_addresses='*'" -w start

# Create database and extensions
echo "Setting up database and extensions..."
psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" <<-EOSQL
    SELECT 'CREATE DATABASE ${POSTGRES_DB}' 
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${POSTGRES_DB}')\gexec
EOSQL

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pg_lake CASCADE;
EOSQL

echo "PostgreSQL with pg_lake started successfully!"
echo "PostgreSQL listening on port 5432"

# Keep container running and tail logs
tail -f "$PGDATA/log"/*.log 2>/dev/null || tail -f /dev/null

