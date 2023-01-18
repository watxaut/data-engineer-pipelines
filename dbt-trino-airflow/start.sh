#!/bin/bash

# colour CLI
green=`tput setaf 2`
red=`tput setaf 1`
yellow=`tput setaf 3`
reset=`tput sgr0`

# export abs path for airflow task volumes. You could also source a file so that it does not give warnings on
# manual docker compose up/down commands
export ABSOLUTE_PATH_DIR=$(pwd)
export AIRFLOW_UID=50000

# wait for worker status to be healthy and apply permissions to docker.sock to airflow user
airflow_worker_status="unhealthy"

# start by removing all containers and orphans
docker-compose down --remove-orphans

echo "${yellow}Starting Airflow in detached mode...${reset}"
ABSOLUTE_PATH_DIR=$(pwd) docker-compose up -d --force-recreate

echo "${yellow}build pyspark image locally to be used by DockerOperators in Airflow...${reset}"
docker build . --tag datamesh/central_order_metrics:0.0.1

echo "${yellow}Waiting for Airflow worker to start...${reset}"
while [ "$airflow_worker_status" != "healthy" ];
do
  airflow_worker_status=$(docker inspect --format='{{json .State.Health.Status}}' airflow-worker | tr -d '"')
  sleep 1
done
echo "${green}Worker ready!${reset}"

echo "${yellow}Give ownership to docker.sock to airflow user...${reset}"
docker exec -u root airflow-worker chown airflow /var/run/docker.sock

echo "${green}All done! Proceed to http://localhost:8080 (airflow as pwd and user)${reset}"
