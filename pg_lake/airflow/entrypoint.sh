#!/bin/bash
set -e

echo "Waiting for services to be ready..."
sleep 20

echo "Running database migrations..."
airflow db migrate

echo "Creating admin user..."
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin || echo "Admin user already exists"

echo "Configuring connections..."
airflow connections delete postgres_pglake 2>/dev/null || true
airflow connections add postgres_pglake \
    --conn-type postgres \
    --conn-host postgres-pglake \
    --conn-schema analytics \
    --conn-login postgres \
    --conn-password postgres \
    --conn-port 5432

echo "Starting Airflow webserver in background..."
airflow webserver &
WEBSERVER_PID=$!

# Give webserver time to start
sleep 5

echo "Starting Airflow scheduler..."
airflow scheduler &
SCHEDULER_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down gracefully..."
    kill -TERM $WEBSERVER_PID 2>/dev/null || true
    kill -TERM $SCHEDULER_PID 2>/dev/null || true
    wait $WEBSERVER_PID 2>/dev/null || true
    wait $SCHEDULER_PID 2>/dev/null || true
    exit 0
}

trap shutdown SIGTERM SIGINT

# Wait for both processes
wait -n

# If one process exits, kill the other and exit
echo "One of the processes exited, shutting down..."
kill -TERM $WEBSERVER_PID 2>/dev/null || true
kill -TERM $SCHEDULER_PID 2>/dev/null || true
wait
