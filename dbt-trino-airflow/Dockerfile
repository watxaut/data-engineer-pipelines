FROM python:3.10-slim-buster

WORKDIR /app

RUN pip install dbt-trino==1.3.1

ENV DBT_PROFILES_DIR=/app

# this would be abstracted in the image
ENV DBT_DEFAULT_SCHEMA=central_order_metrics_internal
COPY profiles.yml profiles.yml

# copy src/ dbt project into /app/src so models is in /app/src/models
COPY src src
