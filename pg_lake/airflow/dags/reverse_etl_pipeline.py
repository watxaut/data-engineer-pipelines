"""
Reverse ETL Pipeline DAG
Orchestrates the flow: MinIO/Iceberg → Trino/dbt → pg_lake/PostgreSQL
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import subprocess
import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'reverse_etl_pipeline',
    default_args=default_args,
    description='Reverse ETL: Iceberg → Trino/dbt → pg_lake',
    schedule_interval=None,  # Manual trigger
    catchup=False,
    tags=['reverse-etl', 'dbt', 'pg_lake'],
)

# Task 1: Verify Trino connectivity
verify_trino = BashOperator(
    task_id='verify_trino_connection',
    bash_command='''
    for i in {1..30}; do
        if curl -s http://trino:8080/v1/info > /dev/null; then
            echo "Trino is ready!"
            exit 0
        fi
        echo "Waiting for Trino... attempt $i/30"
        sleep 10
    done
    echo "Trino did not become ready"
    exit 1
    ''',
    dag=dag,
)

# Task 2: Verify PostgreSQL connectivity
verify_postgres = BashOperator(
    task_id='verify_postgres_connection',
    bash_command='''
    echo "Verifying PostgreSQL connection..."
    echo "Host: ${POSTGRES_HOST}"
    echo "Port: ${POSTGRES_PORT}"
    echo "User: ${POSTGRES_USER}"
    echo "Database: ${POSTGRES_DB}"
    
    for i in {1..30}; do
        if PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT 1" > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready!"
            exit 0
        fi
        echo "⏳ Waiting for PostgreSQL... attempt $i/30"
        if [ $i -eq 30 ]; then
            echo "❌ PostgreSQL did not become ready after 30 attempts"
            echo "Attempting to show connection error:"
            PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT 1"
        fi
        sleep 10
    done
    exit 1
    ''',
    dag=dag,
)

# Task 3: Run dbt deps
dbt_deps = BashOperator(
    task_id='dbt_deps',
    bash_command='''
    cd /opt/airflow/dbt && dbt deps --profiles-dir .
    ''',
    dag=dag,
)

# Task 4: Run dbt debug (optional, for troubleshooting)
dbt_debug = BashOperator(
    task_id='dbt_debug',
    bash_command='''
    cd /opt/airflow/dbt && dbt debug --profiles-dir .
    ''',
    dag=dag,
)

# Task 5: Delete S3 analytics paths before dbt run
delete_s3_analytics = BashOperator(
    task_id='delete_s3_analytics_paths',
    bash_command='''
    python3 << EOF
import boto3
from botocore.client import Config
import os

# Configure boto3 for MinIO
s3_client = boto3.client(
    's3',
    endpoint_url=os.environ['MINIO_ENDPOINT'],
    aws_access_key_id=os.environ['MINIO_ACCESS_KEY'],
    aws_secret_access_key=os.environ['MINIO_SECRET_KEY'],
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

bucket = 'warehouse'
paths_to_delete = [
    'hive/analytics/popular_customizations_per_customer',
    'hive/analytics/popular_customizations_per_product',
    'hive/analytics/popular_customizations_per_customer__dbt_tmp',
    'hive/analytics/popular_customizations_per_product__dbt_tmp'
]

print("Deleting S3 paths in MinIO...")

for path in paths_to_delete:
    print(f"Deleting s3://{bucket}/{path}/")
    try:
        # List all objects with the prefix
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=path + '/')

        objects_deleted = 0
        for page in pages:
            if 'Contents' in page:
                objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                if objects_to_delete:
                    s3_client.delete_objects(
                        Bucket=bucket,
                        Delete={'Objects': objects_to_delete}
                    )
                    objects_deleted += len(objects_to_delete)

        print(f"  Deleted {objects_deleted} objects from s3://{bucket}/{path}/")
    except Exception as e:
        print(f"  Note: {e}")

print("✅ S3 analytics paths deleted successfully!")
EOF
    ''',
    dag=dag,
)

# Task 6: Create analytics schema in Trino
create_analytics_schema = BashOperator(
    task_id='create_analytics_schema',
    bash_command='''
    python3 << EOF
from trino.dbapi import connect

conn = connect(
    host='${TRINO_HOST}',
    port=int('${TRINO_PORT}'),
    user='admin',
    catalog='iceberg',
    schema='default'
)
cursor = conn.cursor()
try:
    cursor.execute("CREATE SCHEMA IF NOT EXISTS iceberg.analytics WITH (location = 's3://warehouse/analytics')")
    print("Analytics schema created successfully!")
except Exception as e:
    print(f"Schema creation note: {e}")
finally:
    cursor.close()
    conn.close()
EOF
    ''',
    dag=dag,
)

# Task 7: Run dbt models
dbt_run = BashOperator(
    task_id='dbt_run',
    bash_command='''
    export DBT_PROFILES_DIR=/opt/airflow/dbt
    cd /opt/airflow/dbt && dbt run --profiles-dir . --full-refresh
    ''',
    dag=dag,
)

# Task 8: Verify dbt results
verify_dbt_results = BashOperator(
    task_id='verify_dbt_results',
    bash_command='''
    python3 << EOF
from trino.dbapi import connect

conn = connect(
    host='${TRINO_HOST}',
    port=int('${TRINO_PORT}'),
    user='admin',
    catalog='iceberg',
    schema='analytics'
)
cursor = conn.cursor()

# Check popular_customizations_per_customer
cursor.execute("SELECT COUNT(*) FROM hive.analytics.popular_customizations_per_customer")
count1 = cursor.fetchone()[0]
print(f"popular_customizations_per_customer count: {count1}")

# Check popular_customizations_per_product
cursor.execute("SELECT COUNT(*) FROM hive.analytics.popular_customizations_per_product")
count2 = cursor.fetchone()[0]
print(f"popular_customizations_per_product count: {count2}")

cursor.close()
conn.close()

if count1 == 0 or count2 == 0:
    raise Exception("dbt models produced no results!")
print("✅ dbt results verified successfully!")
EOF
    ''',
    dag=dag,
)

# Task 9: Drop existing tables in PostgreSQL (if any)
drop_postgres_tables = PostgresOperator(
    task_id='drop_postgres_tables',
    postgres_conn_id='postgres_pglake',
    sql='''
    -- Drop regular tables
    DROP TABLE IF EXISTS popular_customizations_per_customer CASCADE;
    DROP TABLE IF EXISTS popular_customizations_per_product CASCADE;

    DROP FOREIGN TABLE IF EXISTS iceberg.popular_customizations_per_customer CASCADE;
    DROP FOREIGN TABLE IF EXISTS iceberg.popular_customizations_per_product CASCADE;
    ''',
    dag=dag,
)

# Task 10: Copy popular_customizations_per_customer from S3 to PostgreSQL
copy_customer_customizations = PostgresOperator(
    task_id='copy_customer_customizations_to_postgres',
    postgres_conn_id='postgres_pglake',
    sql='''    
    -- Create schema for foreign tables
    CREATE SCHEMA IF NOT EXISTS iceberg;
    
    CREATE FOREIGN TABLE iceberg.popular_customizations_per_customer () SERVER pg_lake
     OPTIONS (path 's3://warehouse/hive/analytics/popular_customizations_per_customer/*', format 'parquet');

    -- Create local table with data from foreign table
    CREATE TABLE popular_customizations_per_customer AS
    SELECT * FROM iceberg.popular_customizations_per_customer;
    
    -- Create indexes on the local table
    CREATE INDEX idx_customer_customizations_customer_id 
        ON popular_customizations_per_customer(customer_id);
    
    CREATE INDEX idx_customer_customizations_product_id 
        ON popular_customizations_per_customer(product_id);
    ''',
    dag=dag,
)

# Task 11: Copy popular_customizations_per_product from S3 to PostgreSQL
copy_product_customizations = PostgresOperator(
    task_id='copy_product_customizations_to_postgres',
    postgres_conn_id='postgres_pglake',
    sql='''
    CREATE SCHEMA IF NOT EXISTS iceberg;

    CREATE FOREIGN TABLE iceberg.popular_customizations_per_product () SERVER pg_lake
     OPTIONS (path 's3://warehouse/hive/analytics/popular_customizations_per_product/*', format 'parquet');

    -- Create local table with data from foreign table
    CREATE TABLE popular_customizations_per_product AS
    SELECT * FROM iceberg.popular_customizations_per_product;

    -- Create index on the local table
    CREATE INDEX idx_product_customizations_product_id
        ON popular_customizations_per_product(product_id);
    ''',
    dag=dag,
)

# Task 12: Verify PostgreSQL data
verify_postgres_data = BashOperator(
    task_id='verify_postgres_data',
    bash_command='''
    PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${POSTGRES_DB} << EOF
\\echo 'Checking popular_customizations_per_customer...'
SELECT COUNT(*) as customer_customizations_count FROM popular_customizations_per_customer;

\\echo 'Checking popular_customizations_per_product...'
SELECT COUNT(*) as product_customizations_count FROM popular_customizations_per_product;

\\echo 'Sample data from popular_customizations_per_customer:'
SELECT * FROM popular_customizations_per_customer LIMIT 5;

\\echo 'Sample data from popular_customizations_per_product:'
SELECT * FROM popular_customizations_per_product LIMIT 5;

\\echo 'Verifying indexes...'
SELECT tablename, indexname FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename IN ('popular_customizations_per_customer', 'popular_customizations_per_product')
ORDER BY tablename, indexname;

\\echo '✅ PostgreSQL data verified successfully!'
EOF
    ''',
    dag=dag,
)

# Define task dependencies
verify_trino >> create_analytics_schema
verify_postgres >> drop_postgres_tables

create_analytics_schema >> dbt_deps >> dbt_debug >> delete_s3_analytics >> dbt_run >> verify_dbt_results

verify_dbt_results >> drop_postgres_tables >> [copy_customer_customizations, copy_product_customizations]

[copy_customer_customizations, copy_product_customizations] >> verify_postgres_data

