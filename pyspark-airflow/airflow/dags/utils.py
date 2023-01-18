import os
from typing import List

from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount


def docker_pyspark_operator(task_id: str,
                            command: List[str],
                            image='data-engineering/pyspark-engine-local:0.0.1') -> DockerOperator:
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
        mount_tmp_dir=False,
        # we are running docker in docker (see https://airflow.apache.org/docs/apache-airflow-providers-docker/2.4.1/_api/airflow/providers/docker/operators/docker/index.html)
        network_mode='airflow-stack',  # use network created by docker-compose
        # Mounts with host machine need to be with full path to the outer machine
        mounts=[
            Mount(
                source=f'{os.getenv("ABSOLUTE_PATH_DIR")}/spark-warehouse',
                target='/app/spark-warehouse',
                type='bind'
            )
        ],
        command=command
    )
