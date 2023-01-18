"""
This DAG extracts from orders and customer_courier_chat_messages, transforms this information and aggregates
it, creating gold/customer_courier_conversations

There are no parameters available for the DAG, although as next steps it would be nice to have some date start/end
DAG parameters to be able to run backfills on the presentation table
"""

import utils
import documentation

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator

with DAG(
        'customer_contacts_pipeline',
        # These args will get passed on to each operator
        # You can override them on a per-task basis during operator initialization
        default_args={
            'depends_on_past': False,
            'email': ['airflow@example.com'],
            'email_on_failure': False,
            'email_on_retry': False,
            'retries': 0,
            'retry_delay': timedelta(minutes=5),
        },
        description='''Extract orders and contacts information into bronze layer in datalake, clean it, and 
        present it in the gold layer''',
        schedule=timedelta(days=1),
        start_date=datetime(2022, 9, 1),
        catchup=False,
) as dag:
    dag.doc_md = __doc__  # adds docstring as docs for the DAG

    # Start cluster (mock start cluster as we are executing it locally with pyspark)
    start_cluster = DummyOperator(task_id='start_cluster')
    # given we had a real cluster, you should add trigger_rule='all_done' to close the cluster when something failed
    stop_cluster = DummyOperator(task_id='stop_cluster', trigger_rule='all_done')

    l_table_extracts = [
        ('public', 'orders', 'creation_time'),
        ('public', 'customer_courier_chat_messages', 'message_sent_time'),
    ]

    # create extracts to `l_table_extracts` by creating different DockerOperators that will run pyspark, connecting to
    # postgres-source host and land the information in bronze layer
    extracts = []
    for schema, table, partition_field in l_table_extracts:
        e = utils.docker_pyspark_operator(
            task_id=f'extract_{schema}_{table}',
            # client mode as we are running it locally in the image, no cluster involved. If it was connecting to
            # a spark cluster (yarn/k8s) it would be
            # schema public is the default for extract.py
            command=["spark-submit", "--deploy-mode", "client", "src/extract.py", table, "-p", partition_field]
        )
        e.doc_md = documentation.d_extracts[table]
        extracts.append(e)
    # given we needed to also clean source data, we would create a silver schema with cleaned and refined data

    # transform `l_table_extracts` and create `customer_courier_conversations` in gold layer
    transformation = utils.docker_pyspark_operator(
        task_id=f'transform_conversations',
        command=["spark-submit", "--deploy-mode", "client", "src/transform_conversations.py"]
    )
    transformation.doc_md = documentation.transformation

    start_cluster >> extracts >> transformation >> stop_cluster
