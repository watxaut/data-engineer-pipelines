from pyspark.sql import SparkSession
from pyspark.sql import DataFrame


def get_spark_session(app_name) -> SparkSession:
    """
    TODO
    :param app_name:
    :return:
    """
    return SparkSession \
        .builder \
        .appName(app_name) \
        .enableHiveSupport() \
        .getOrCreate()


def read_dl_table(spark, path) -> DataFrame:
    """
    TODO
    :param spark:
    :param path:
    :return:
    """
    return spark.read \
        .format("parquet") \
        .option("path", f"spark-warehouse/{path}").load()


def read_hive_table(spark, table_name) -> DataFrame:
    """
    TODO
    :param spark:
    :param table_name:
    :return:
    """
    return spark.read.table(table_name)
