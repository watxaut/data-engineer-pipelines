#!/bin/bash

set -e

echo "🚀 Starting Reverse ETL Pipeline with pg_lake"
echo "=============================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.example..."
    cp .env.example .env
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p airflow/dags
mkdir -p airflow/logs
mkdir -p dbt/models/staging
mkdir -p dbt/models/marts
mkdir -p trino/catalog
mkdir -p postgres-pglake
mkdir -p data-init
mkdir -p init-scripts/pg_lake

echo ""
echo "🐳 Starting Docker Compose services..."
echo "⚠️  Note: Building pg_lake from source will take ~30-45 minutes on first run"
echo ""

# Start services in stages
echo "Stage 1: Starting MinIO and Iceberg REST Catalog..."
docker-compose up -d minio minio-init iceberg-rest

echo "Waiting for MinIO and Iceberg REST to be ready..."
sleep 15

echo ""
echo "Stage 2: Starting Trino..."
docker-compose up -d trino

echo "Waiting for Trino to be ready..."
sleep 20

echo ""
echo "Stage 3: Building and starting PostgreSQL with pg_lake..."
echo "⏰ This will take a while as it builds pg_lake from source..."
docker-compose up -d postgres-pglake

echo ""
echo "Stage 4: Starting Airflow services..."
docker-compose up -d airflow-postgres
sleep 10
docker-compose up -d airflow

echo ""
echo "Stage 5: Initializing data..."
docker-compose up data-initializer

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📊 Access the services:"
echo "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo "  - Trino UI: http://localhost:8080"
echo "  - Airflow UI: http://localhost:8082 (admin/admin)"
echo "  - PostgreSQL pg_lake: localhost:5432 (postgres/postgres)"
echo ""
echo "🔧 Next steps:"
echo "  1. Wait for all services to be fully ready (~5 minutes)"
echo "  2. Access Airflow UI at http://localhost:8082"
echo "  3. Run the 'setup_connections' DAG once"
echo "  4. Run the 'reverse_etl_pipeline' DAG to execute the full pipeline"
echo ""
echo "📝 Check logs with: docker-compose logs -f [service-name]"
echo "🛑 Stop services with: docker-compose down"
echo "🗑️  Remove all data with: docker-compose down -v"

