FROM apache/airflow:2.8.1-python3.11

USER root

# Install PostgreSQL client and other dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install dbt-trino and other Python dependencies
RUN pip install --no-cache-dir \
    dbt-trino==1.7.1 \
    trino==0.328.0 \
    psycopg2-binary==2.9.9 \
    pandas==2.1.4

# Create dbt directory
RUN mkdir -p /opt/airflow/dbt

WORKDIR /opt/airflow

