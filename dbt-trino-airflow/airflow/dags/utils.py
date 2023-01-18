from typing import List
from docker.types import Mount

from airflow.providers.docker.operators.docker import DockerOperator



def docker_dbt_trino_operator(task_id: str,
                              command: List[str],
                              image='datamesh/central_order_metrics:0.0.1') -> DockerOperator:
    """

    :param task_id:
    :param command:
    :param image:
    :return:
    """
    return DockerOperator(
        task_id=task_id,
        image=image,
        api_version='auto',  # auto detect docker server's version
        force_pull=False,  # set to True if you want Docker to first pull the latest image from repository
        # we are running docker in docker (see
        # https://airflow.apache.org/docs/apache-airflow-providers-docker/2.4.1/_api/airflow/providers/docker/operators/docker/index.html)
        network_mode='central-default',  # use network created by docker-compose
        mount_tmp_dir=False,
        command=command,
        # Mounts with host machine need to be with full path to the outer machine
        mounts=[
            # this mount is useful to understand what dbt is compiling/running in Airflow
            Mount(
                source=f'{Variable.get("ABSOLUTE_PATH_DIR")}/src/target',
                target='/app/src/target',
                type='bind'
            ),
            # this mount mounts dbt logs for debugging purposes with localhost
            Mount(
                source=f'{Variable.get("ABSOLUTE_PATH_DIR")}/src/logs',
                target='/app/src/logs',
                type='bind'
            ),
        ],
        # env vars are passed in docker-compose
        environment={
            'DBT_USER': Variable.get('DBT_USER'),
            'DBT_HOST': Variable.get('DBT_HOST'),
            'DBT_PORT': Variable.get('DBT_PORT'),
            'DBT_AUTH': Variable.get('DBT_AUTH', None),
            'DBT_DEFAULT_SCHEMA': Variable.get('DBT_DEFAULT_SCHEMA'),
            'DBT_HTTP_SCHEME': Variable.get('DBT_HTTP_SCHEME'),
        }
    )