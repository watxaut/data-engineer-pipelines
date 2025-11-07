# Reverse ETL Pipeline with pg_lake

A comprehensive reverse ETL pipeline demonstrating the integration of MinIO (S3-compatible storage), Apache Iceberg, Trino, dbt, and PostgreSQL with pg_lake extension.

## 🎯 Overview

This POC implements a complete reverse ETL pipeline that:

1. **Stores raw data** in MinIO as Iceberg tables (orders and bought_products)
2. **Transforms data** using Trino and dbt into analytical parquet tables
3. **Copies data** into PostgreSQL with pg_lake extension with appropriate indexes for fast querying

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Reverse ETL Pipeline                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────┐     ┌──────────────┐     ┌─────────┐     ┌──────────┐
│  MinIO   │────▶│ Iceberg REST │────▶│  Trino  │────▶│ pg_lake  │
│   (S3)   │     │   Catalog    │     │ + dbt   │     │(Postgres)│
└──────────┘     └──────────────┘     └─────────┘     └──────────┘
     │                                       │               │
     │           ┌───────────────────────────┘               │
     │           │                                           │
     └───────────┴───────────────────────────────────────────┘
                        Orchestrated by Airflow
```

### Components

- **MinIO**: S3-compatible object storage for data lake
- **Apache Iceberg REST Catalog**: Manages Iceberg table metadata
- **Trino**: Distributed SQL query engine
- **dbt-trino**: Data transformation framework
- **PostgreSQL with pg_lake**: PostgreSQL extended with data lake capabilities
- **pgduck_server**: DuckDB-based query engine for pg_lake
- **Apache Airflow**: Workflow orchestration

## 📋 Data Model

### Source Tables (Iceberg in MinIO)

#### `orders` table
- `order_id` (BIGINT) - Primary Key
- `customer_id` (BIGINT)
- `order_date` (TIMESTAMP)
- `order_status` (VARCHAR)

#### `bought_products` table
- `bought_product_id` (BIGINT) - Primary Key
- `product_id` (BIGINT)
- `product_customizations` (ARRAY[INTEGER]) - 0-3 customizations per product
- `order_id` (BIGINT) - Foreign Key to orders

### Analytics Tables (Parquet in MinIO → PostgreSQL)

#### `popular_customizations_per_customer`
- `customer_id` (BIGINT) - **Indexed**
- `product_id` (BIGINT) - **Indexed**
- `customization` (INTEGER)
- `customization_count` (BIGINT)

**Purpose**: Track the most popular customizations per customer and product

#### `popular_customizations_per_product`
- `product_id` (BIGINT) - **Indexed**
- `customization` (INTEGER)
- `customization_count` (BIGINT)

**Purpose**: Track the most popular customizations across all customers per product

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- At least 8GB RAM available for Docker
- 20GB free disk space
- ~45 minutes for initial build (pg_lake from source)

### Installation

1. **Clone and navigate to the directory**:
```bash
cd pg_lake/
```

2. **Make the start script executable**:
```bash
chmod +x start.sh
```

3. **Start all services**:
```bash
./start.sh
```

This will:
- Start MinIO (S3-compatible storage)
- Start Iceberg REST Catalog
- Start Trino query engine
- Build and start PostgreSQL with pg_lake (from source, takes ~30-45 min)
- Start Airflow with dbt-trino
- Initialize fake data (1000 orders, 5000 bought products)

### Post-Startup Steps

1. **Wait for all services to be ready** (~5 minutes after script completes)

2. **Access Airflow UI**: http://localhost:8082
   - Username: `admin`
   - Password: `admin`

3. **Run the setup DAG** (one-time):
   - In Airflow UI, find the `setup_connections` DAG
   - Click the play button to trigger it
   - This creates the PostgreSQL connection

4. **Run the main pipeline**:
   - Find the `reverse_etl_pipeline` DAG
   - Click the play button to trigger it
   - Watch the pipeline execute through all stages

## 📂 Project Structure

```
pg_lake/
├── docker-compose.yml          # Main orchestration file
├── start.sh                    # Startup script
├── .env.example                # Environment variables template
├── README.md                   # This file
│
├── airflow/                    # Airflow configuration
│   ├── Dockerfile              # Custom Airflow image with dbt-trino
│   └── dags/                   # DAG definitions
│       ├── reverse_etl_pipeline.py
│       └── setup_connections.py
│
├── dbt/                        # dbt project
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/            # Staging views
│       │   ├── stg_orders.sql
│       │   └── stg_bought_products.sql
│       └── marts/              # Analytics tables
│           ├── popular_customizations_per_customer.sql
│           └── popular_customizations_per_product.sql
│
├── postgres-pglake/            # PostgreSQL with pg_lake
│   ├── Dockerfile              # Builds pg_lake from source
│   └── entrypoint.sh           # Startup script
│
├── data-init/                  # Data initialization
│   ├── Dockerfile
│   └── initialize_data.py      # Generates fake data
│
├── trino/                      # Trino configuration
│   ├── catalog/
│   │   └── iceberg.properties  # Iceberg catalog config
│   └── config.properties       # Trino config
│
└── init-scripts/               # PostgreSQL init scripts
    └── pg_lake/
        ├── 01_create_extensions.sql
        └── 02_configure_s3.sql
```

## 🔍 Pipeline Flow

The `reverse_etl_pipeline` DAG executes the following steps:

1. **Verify Connectivity**: Check Trino and PostgreSQL are ready
2. **Create Schema**: Create analytics schema in Trino/Iceberg
3. **dbt Setup**: Run `dbt deps` and `dbt debug`
4. **dbt Transform**: Run dbt models to create analytics tables
5. **Verify Results**: Check that dbt produced data
6. **Drop Old Tables**: Clean up any existing PostgreSQL tables
7. **Copy to PostgreSQL**: Use `COPY FROM` to load parquet data
8. **Create Indexes**: Add indexes for fast querying
9. **Verify Data**: Confirm data is loaded and indexed correctly

## 🌐 Service Access

| Service | URL | Credentials |
|---------|-----|-------------|
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| Trino UI | http://localhost:8080 | - |
| Airflow UI | http://localhost:8082 | admin / admin |
| PostgreSQL | localhost:5432 | postgres / postgres |
| pgduck_server | localhost:5332 | postgres / postgres |

## 🛠️ Useful Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres-pglake
docker-compose logs -f airflow
docker-compose logs -f trino
```

### Restart a service
```bash
docker-compose restart [service-name]
```

### Connect to PostgreSQL
```bash
docker-compose exec postgres-pglake psql -U postgres -d analytics
```

### Check data in PostgreSQL
```sql
-- Connect to analytics database
\c analytics

-- Check tables
\dt

-- Query popular customizations per customer
SELECT * FROM popular_customizations_per_customer 
WHERE customer_id = 1 
LIMIT 10;

-- Query popular customizations per product
SELECT * FROM popular_customizations_per_product 
WHERE product_id = 5 
LIMIT 10;

-- Check indexes
\di
```

### Connect to Trino
```bash
docker-compose exec trino trino
```

### Check Iceberg tables
```sql
-- In Trino CLI
SHOW SCHEMAS IN iceberg;
SHOW TABLES IN iceberg.raw;
SHOW TABLES IN iceberg.analytics;

SELECT * FROM iceberg.raw.orders LIMIT 10;
SELECT * FROM iceberg.analytics.popular_customizations_per_customer LIMIT 10;
```

### Run dbt manually
```bash
docker-compose exec airflow bash
cd /opt/airflow/dbt
dbt run --profiles-dir .
```

## 🔧 Troubleshooting

### pg_lake build fails
The pg_lake Dockerfile builds from source, which can be resource-intensive:
- Ensure you have at least 8GB RAM allocated to Docker
- The build can take 30-45 minutes
- Check logs: `docker-compose logs postgres-pglake`

### Trino can't connect to MinIO
- Verify MinIO is running: `docker-compose ps minio`
- Check MinIO logs: `docker-compose logs minio`
- Ensure buckets were created: Check MinIO console at http://localhost:9001

### Airflow DAG fails
- Check if all services are healthy: `docker-compose ps`
- Run the `setup_connections` DAG first
- Verify dbt connection: `docker-compose exec airflow dbt debug --profiles-dir /opt/airflow/dbt`

### PostgreSQL COPY fails
- Ensure pgduck_server is running inside the postgres-pglake container
- Check MinIO credentials in entrypoint.sh
- Verify the S3 path exists in MinIO

## 📚 References

- [pg_lake GitHub](https://github.com/Snowflake-Labs/pg_lake) - Main pg_lake repository
- [pg_lake Documentation](https://github.com/Snowflake-Labs/pg_lake/blob/main/docs/README.md) - Full documentation
- [Building from Source](https://github.com/Snowflake-Labs/pg_lake/blob/main/docs/building-from-source.md) - Build instructions
- [Apache Iceberg](https://iceberg.apache.org/) - Iceberg table format
- [dbt-trino](https://github.com/starburstdata/dbt-trino) - dbt adapter for Trino

## 📊 Sample Data

The pipeline initializes with:
- **1000 orders** from 200 unique customers
- **5000 bought products** with 0-3 customizations each
- **50 unique products**
- **20 possible customization types**

This generates realistic analytical tables with varying cardinalities perfect for testing queries and performance.

## 🎓 Learning Objectives

This POC demonstrates:

1. ✅ **Data Lake Architecture**: Using MinIO as S3-compatible object storage
2. ✅ **Iceberg Tables**: Managing transactional data lake tables
3. ✅ **Query Federation**: Trino accessing Iceberg tables
4. ✅ **Data Transformation**: dbt models with complex SQL (UNNEST arrays)
5. ✅ **Reverse ETL**: Copying analytical results back to operational database
6. ✅ **pg_lake Extension**: Extending PostgreSQL with data lake capabilities
7. ✅ **Workflow Orchestration**: Airflow coordinating the entire pipeline
8. ✅ **Performance Optimization**: Creating indexes for analytical queries

## 🚨 Important Notes

- This is a **POC/Development environment** - not production-ready
- All data is ephemeral unless volumes are persisted
- Security is minimal (default passwords, no SSL)
- pg_lake is built from source for the latest features
- Resource-intensive: requires significant CPU and memory

## 🧹 Cleanup

### Stop all services
```bash
docker-compose down
```

### Remove all data (including volumes)
```bash
docker-compose down -v
```

### Remove all images
```bash
docker-compose down -v --rmi all
```

## 📝 License

This project is provided as-is for educational and demonstration purposes.

## 🤝 Contributing

Feel free to open issues or submit pull requests for improvements!

---

**Happy Data Engineering! 🚀**
