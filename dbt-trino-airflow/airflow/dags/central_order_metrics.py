"""main dbt DAG for Data Product

dag_run.conf parameters:
    - {"full_refresh": "--full-refresh"}
      Uses dbt Full refresh flag
    - {"models": "<dbt syntax for models to execute>"}
      Models to run, normally you will want to execute it with full-refresh option.
Full example:
    {"full_refresh": "--full-refresh", "models": "order_metrics"}
"""
from datetime import timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup

import utils

DAG_NAME = "central_order_metrics"
DBT_IMAGE = "datamesh/central_order_metrics:0.0.1"

schedule_interval = "0 0 * * *"
default_args = {
    "owner": "airflow",
    "description": "DAG to create the source-aligned data product Central Order Metrics",
    "start_date": days_ago(2),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
    # number of tasks to run concurrently. If not set will read it from the default core.max_active_tasks_per_dag
    "max_active_tasks": 4,
    "depends_on_past": False,
    "max_active_runs_per_dag": 1,
}

with DAG(
        DAG_NAME,
        default_args=default_args,
        catchup=False,
        schedule_interval=schedule_interval,
) as dag:
    # create sensors for all ODPs. All tasks created in the with context manager will be part of the group
    with TaskGroup("sensors") as sensors:
        for odp in [
            "order_metrics",
        ]:
            DummyOperator(task_id=f'sensor_{odp}')

    # Executes dbt in a docker operator. Available parameters are models and full_refresh
    dbt_trino = utils.docker_dbt_trino_operator(
        'dbt_trino_run',
        [
            'dbt',
            'build',
            '--project-dir',
            'src',
            '--target',
            Variable.get('DBT_TARGET', 'local'),
            '{{ dag_run.conf.get("models", "+internal+ +odp+") }}',
            '{{ dag_run.conf.get("full_refresh", "") }}',
        ],
    )

    # create checkpoints for all ODPs. All tasks created in the with context manager will be part of the group
    with TaskGroup("checkpoints") as checkpoints:
        for odp in [
            "order_metrics",
        ]:
            DummyOperator(task_id=f'checkpoint_{odp}')

    sensors >> dbt_trino >> checkpoints
