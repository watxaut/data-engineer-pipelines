# Image ready to run pyspark commands
# Used in the repository for table-setup service and workers in airflow
FROM maven:3-jdk-11-slim AS maven

WORKDIR /spark
COPY spark/conf/pom.xml .
RUN mvn clean package

FROM python:3.10.7-bullseye

WORKDIR /app

COPY --from=maven /spark/target/lib/ /app/spark/jars

RUN pip install pyspark==3.3.0

# copy and install java
COPY --from=openjdk:8-jre-slim /usr/local/openjdk-8 /usr/local/openjdk-8
ENV JAVA_HOME /usr/local/openjdk-8
RUN update-alternatives --install /usr/bin/java java /usr/local/openjdk-8/bin/java 1


COPY spark/conf/spark-defaults.conf /app/spark
ENV SPARK_CONF_DIR=/app/spark

COPY src/ /app/src/
