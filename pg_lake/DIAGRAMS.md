# Reverse ETL Pipeline - Visual Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        REVERSE ETL PIPELINE ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────────────────────┘

                                                                                
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Data Lake Layer                                 │
│  ┌────────────┐          ┌──────────────────┐                               │
│  │   MinIO    │◀────────▶│  Iceberg REST    │                               │
│  │ (S3 API)   │          │    Catalog       │                               │
│  │            │          │                  │                               │
│  │  Port 9000 │          │    Port 8181     │                               │
│  └────────────┘          └──────────────────┘                               │
│       │                            │                                         │
│       │  Stores:                   │  Manages:                               │
│       │  • Parquet files           │  • Table metadata                       │
│       │  • Iceberg data            │  • Snapshots                            │
│       │  • Analytics output        │  • Schema versions                      │
└──────────────────────────────────────────────────────────────────────────────┘
       │                            │
       │                            │
       ▼                            ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Query & Transform Layer                            │
│  ┌────────────────────────────────────────────────────────────┐              │
│  │                         Trino                              │              │
│  │                    (Port 8080)                             │              │
│  │                                                            │              │
│  │  ┌──────────────┐         ┌──────────────┐                │              │
│  │  │   Iceberg    │         │     dbt      │                │              │
│  │  │  Connector   │◀───────▶│   Models     │                │              │
│  │  └──────────────┘         └──────────────┘                │              │
│  │                                                            │              │
│  └────────────────────────────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Writes Parquet
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Serving Layer                                     │
│  ┌────────────────────────────────────────────────────────────┐              │
│  │              PostgreSQL 17 with pg_lake                    │              │
│  │                     (Port 5432)                            │              │
│  │                                                            │              │
│  │  ┌──────────────┐         ┌──────────────┐                │              │
│  │  │   pg_lake    │◀───────▶│  pgduck_     │                │              │
│  │  │  Extension   │         │  server      │                │              │
│  │  │              │         │  (Port 5332) │                │              │
│  │  └──────────────┘         └──────────────┘                │              │
│  │                                 │                          │              │
│  │                                 │ Reads from S3            │              │
│  │                                 ▼                          │              │
│  │  ┌────────────────────────────────────────────┐           │              │
│  │  │    Indexed Tables Ready for Applications   │           │              │
│  │  └────────────────────────────────────────────┘           │              │
│  └────────────────────────────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Orchestrated by
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Orchestration Layer                                 │
│  ┌────────────────────────────────────────────────────────────┐              │
│  │                    Apache Airflow                          │              │
│  │                     (Port 8082)                            │              │
│  │                                                            │              │
│  │  • DAG: setup_connections                                 │              │
│  │  • DAG: reverse_etl_pipeline                              │              │
│  └────────────────────────────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA FLOW                                         │
└─────────────────────────────────────────────────────────────────────────────┘


STEP 1: DATA INITIALIZATION
────────────────────────────

  ┌──────────────┐
  │  Python      │
  │  Script      │
  └──────┬───────┘
         │ Generates:
         │ • 1000 orders
         │ • 5000 bought_products
         ▼
  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
  │    Trino     │─────▶│   Iceberg    │─────▶│    MinIO     │
  │              │      │ REST Catalog │      │   (S3://     │
  └──────────────┘      └──────────────┘      │  warehouse/) │
                                               └──────────────┘
                                                     │
                                                     ▼
                                        ┌─────────────────────────┐
                                        │ iceberg.raw.orders      │
                                        │ iceberg.raw.bought_     │
                                        │         products        │
                                        └─────────────────────────┘


STEP 2: DBT TRANSFORMATION
───────────────────────────

  ┌──────────────┐
  │     dbt      │
  │   Models     │
  └──────┬───────┘
         │ Compiles SQL
         ▼
  ┌──────────────┐
  │    Trino     │
  │              │
  └──────┬───────┘
         │ Reads from
         ▼
  ┌──────────────┐      ┌──────────────┐
  │   Iceberg    │─────▶│  Raw Tables  │
  │   Catalog    │      │  • orders    │
  └──────────────┘      │  • bought_   │
                        │    products  │
                        └──────────────┘
         │
         │ UNNEST Arrays
         │ Aggregate
         │ Group By
         ▼
  ┌──────────────────────────────────────┐
  │        Transformed Data              │
  │                                      │
  │  popular_customizations_per_customer │
  │  popular_customizations_per_product  │
  └──────────────────┬───────────────────┘
                     │
                     │ Write as Parquet
                     ▼
              ┌──────────────┐
              │    MinIO     │
              │  s3://       │
              │  warehouse/  │
              │  analytics/  │
              └──────────────┘


STEP 3: COPY TO POSTGRESQL
───────────────────────────

  ┌──────────────┐
  │  Airflow     │
  │  Triggers    │
  └──────┬───────┘
         │
         │ COPY FROM 's3://...'
         ▼
  ┌──────────────┐      ┌──────────────┐
  │ PostgreSQL   │◀────▶│  pgduck_     │
  │  pg_lake     │      │  server      │
  └──────┬───────┘      └──────┬───────┘
         │                     │
         │                     │ Reads Parquet
         │                     ▼
         │              ┌──────────────┐
         │              │    MinIO     │
         │              │  analytics/  │
         │              │  *.parquet   │
         │              └──────────────┘
         │
         │ Creates Tables + Indexes
         ▼
  ┌─────────────────────────────────────┐
  │  PostgreSQL Tables (Indexed)        │
  │                                     │
  │  popular_customizations_per_        │
  │    customer                         │
  │    • idx: customer_id               │
  │    • idx: product_id                │
  │                                     │
  │  popular_customizations_per_        │
  │    product                          │
  │    • idx: product_id                │
  └─────────────────────────────────────┘
```

## Airflow DAG Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AIRFLOW DAG: reverse_etl_pipeline                        │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │ verify_trino_       │
                    │   connection        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ create_analytics_   │
                    │     schema          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    dbt_deps         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    dbt_debug        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     dbt_run         │
                    │  (Transform Data)   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ verify_dbt_results  │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         │                                           │
         ▼                                           ▼
┌─────────────────────┐                 ┌─────────────────────┐
│ verify_postgres_    │                 │ drop_postgres_      │
│   connection        │                 │    tables           │
└─────────────────────┘                 └──────────┬──────────┘
                                                   │
                               ┌───────────────────┴─────────────────┐
                               │                                     │
                               ▼                                     ▼
                  ┌──────────────────────┐         ┌──────────────────────┐
                  │ copy_customer_       │         │ copy_product_        │
                  │  customizations      │         │  customizations      │
                  │  (with indexes)      │         │  (with indexes)      │
                  └──────────┬───────────┘         └──────────┬───────────┘
                             │                                │
                             └────────────┬───────────────────┘
                                          │
                                          ▼
                              ┌─────────────────────┐
                              │ verify_postgres_    │
                              │      data           │
                              └─────────────────────┘
                                          │
                                          ▼
                                      SUCCESS!
```

## Data Model Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA MODEL                                        │
└─────────────────────────────────────────────────────────────────────────────┘


SOURCE TABLES (Iceberg in MinIO)
─────────────────────────────────

┌─────────────────────┐                    ┌─────────────────────────┐
│      orders         │                    │   bought_products       │
├─────────────────────┤                    ├─────────────────────────┤
│ order_id      [PK]  │◀───────────────────│ bought_product_id [PK]  │
│ customer_id         │                    │ product_id              │
│ order_date          │                    │ product_customizations  │
│ order_status        │                    │   (ARRAY[INT])          │
└─────────────────────┘                    │ order_id          [FK]  │
                                           └─────────────────────────┘
       │                                              │
       │                                              │
       │  Granularity: order_id                       │  Granularity: bought_product_id
       │  Count: 1,000 rows                           │  Count: 5,000 rows
       │  Customers: 200 unique                       │  Products: 50 unique
       │                                              │  Customizations: 0-3 per product
       │                                              │
       └──────────────┬───────────────────────────────┘
                      │
                      │  dbt Transformation
                      │  • JOIN tables
                      │  • UNNEST customizations array
                      │  • GROUP BY and aggregate
                      │  • Write as Parquet
                      │
       ┌──────────────┴───────────────────────────────┐
       │                                              │
       ▼                                              ▼

ANALYTICS TABLES (Parquet → PostgreSQL)
────────────────────────────────────────

┌──────────────────────────────┐     ┌──────────────────────────────┐
│ popular_customizations_      │     │ popular_customizations_      │
│      per_customer            │     │      per_product             │
├──────────────────────────────┤     ├──────────────────────────────┤
│ customer_id    [INDEXED]     │     │ product_id     [INDEXED]     │
│ product_id     [INDEXED]     │     │ customization                │
│ customization                │     │ customization_count          │
│ customization_count          │     └──────────────────────────────┘
└──────────────────────────────┘              │
       │                                      │
       │  Granularity:                        │  Granularity:
       │  • customer_id                       │  • product_id
       │  • product_id                        │  • customization
       │  • customization                     │
       │                                      │
       │  Use Case:                           │  Use Case:
       │  "What are customer 123's            │  "What are the most
       │   favorite customizations            │   popular customizations
       │   for product 5?"                    │   for product 10?"
       │                                      │
       └──────────────┬───────────────────────┘
                      │
                      ▼
              ┌──────────────┐
              │ Applications │
              │  • REST APIs │
              │  • Dashboards│
              │  • Reports   │
              └──────────────┘
```

## Docker Container Network

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Docker Network: reverse-etl-network                      │
└─────────────────────────────────────────────────────────────────────────────┘


┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│     MinIO      │    │   Iceberg      │    │     Trino      │
│   (minio)      │    │   REST         │    │   (trino)      │
│                │    │   (iceberg-    │    │                │
│  Ports:        │    │     rest)      │    │  Port:         │
│   • 9000  API  │    │                │    │   • 8080       │
│   • 9001  UI   │    │  Port:         │    │                │
│                │    │   • 8181       │    │                │
└────────┬───────┘    └────────┬───────┘    └────────┬───────┘
         │                     │                     │
         │                     │                     │
         └─────────────────────┴─────────────────────┘
                               │
                               │ Internal DNS
                               │
         ┌─────────────────────┴─────────────────────┐
         │                                           │
         ▼                                           ▼
┌────────────────┐                        ┌────────────────┐
│  PostgreSQL    │                        │   Airflow      │
│  pg_lake       │                        │  (airflow)     │
│  (postgres-    │                        │                │
│    pglake)     │                        │  Port:         │
│                │                        │   • 8082  UI   │
│  Ports:        │                        │                │
│   • 5432  PG   │                        │  + Airflow DB  │
│   • 5332  Duck │                        │    (postgres)  │
└────────────────┘                        └────────────────┘


Port Mappings (Host → Container)
─────────────────────────────────
Host          Container      Service
9000     →    9000          MinIO API
9001     →    9001          MinIO Console
8080     →    8080          Trino
8181     →    8181          Iceberg REST
5432     →    5432          PostgreSQL pg_lake
5332     →    5332          pgduck_server
8082     →    8080          Airflow Web UI
```

## File Storage Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MinIO Bucket: warehouse                                │
└─────────────────────────────────────────────────────────────────────────────┘

s3://warehouse/
│
├── raw/                                    [Raw Iceberg Tables]
│   ├── orders/
│   │   ├── metadata/                      [Iceberg metadata]
│   │   │   ├── v1.metadata.json
│   │   │   ├── v2.metadata.json
│   │   │   └── snap-*.avro
│   │   └── data/                          [Parquet data files]
│   │       ├── 00000-0-data.parquet
│   │       ├── 00001-0-data.parquet
│   │       └── ...
│   │
│   └── bought_products/
│       ├── metadata/                      [Iceberg metadata]
│       │   ├── v1.metadata.json
│       │   └── snap-*.avro
│       └── data/                          [Parquet data files]
│           ├── 00000-0-data.parquet
│           └── ...
│
└── analytics/                             [Analytics Parquet Tables]
    ├── popular_customizations_per_customer/
    │   ├── part-00000.parquet
    │   ├── part-00001.parquet
    │   └── ...
    │
    └── popular_customizations_per_product/
        ├── part-00000.parquet
        └── ...


┌─────────────────────────────────────────────────────────────────────────────┐
│                    PostgreSQL: analytics database                           │
└─────────────────────────────────────────────────────────────────────────────┘

analytics/
│
└── public/                                [Schema]
    ├── popular_customizations_per_customer    [Table]
    │   ├── customer_id                        [Column, Indexed]
    │   ├── product_id                         [Column, Indexed]
    │   ├── customization                      [Column]
    │   └── customization_count                [Column]
    │
    └── popular_customizations_per_product     [Table]
        ├── product_id                         [Column, Indexed]
        ├── customization                      [Column]
        └── customization_count                [Column]
```

---

**These diagrams illustrate the complete architecture, data flow, and relationships in the Reverse ETL pipeline.**

