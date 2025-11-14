#!/bin/bash
export JAVA_HOME=/opt/java/openjdk
export HADOOP_HOME=/opt/hadoop-3.3.1
export HADOOP_CLASSPATH=${HADOOP_HOME}/share/hadoop/tools/lib/*
export HIVE_HOME=/opt/apache-hive-metastore-3.1.3-bin

# Set S3 configuration for Hadoop
export HADOOP_OPTS="-Dfs.s3a.access.key=minioadmin -Dfs.s3a.secret.key=minioadmin -Dfs.s3a.endpoint=http://minio:9000 -Dfs.s3a.path.style.access=true"

${HIVE_HOME}/bin/schematool -initSchema -dbType mysql
${HIVE_HOME}/bin/start-metastore

