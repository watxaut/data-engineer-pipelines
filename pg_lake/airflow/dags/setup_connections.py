"""
DAG to set up Airflow connections for the reverse ETL pipeline
Run this once after Airflow starts
"""

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Connection
from airflow import settings
import os

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
}

dag = DAG(
    'setup_connections',
    default_args=default_args,
    description='Set up Airflow connections',
    schedule_interval=None,
    catchup=False,
    tags=['setup'],
)

def create_postgres_connection():
    """Create PostgreSQL connection for pg_lake"""
    session = settings.Session()
    
    # Check if connection already exists
    existing = session.query(Connection).filter(Connection.conn_id == 'postgres_pglake').first()
    
    if existing:
        print("Connection 'postgres_pglake' already exists, updating...")
        session.delete(existing)
        session.commit()
    
    # Create new connection
    conn = Connection(
        conn_id='postgres_pglake',
        conn_type='postgres',
        host=os.getenv('POSTGRES_HOST', 'postgres-pglake'),
        schema=os.getenv('POSTGRES_DB', 'analytics'),
        login=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        port=int(os.getenv('POSTGRES_PORT', '5432'))
    )
    
    session.add(conn)
    session.commit()
    session.close()
    
    print("✅ PostgreSQL connection 'postgres_pglake' created successfully!")

setup_postgres = PythonOperator(
    task_id='setup_postgres_connection',
    python_callable=create_postgres_connection,
    dag=dag,
)

setup_postgres

