import argparse

from pyspark.sql.functions import to_date

from utils import get_spark_session

if __name__ == "__main__":
    # parse arguments table, schema and partition key
    parser = argparse.ArgumentParser(description='Args for extraction')
    parser.add_argument('table', metavar='table_name', type=str,
                        help='Table name to extract, schema needs to be provided by -s option, defaults to "public"')
    parser.add_argument('-s', '--schema', metavar='schema_name', type=str, default='public',
                        help='Table to extract, schema needs to be prepended, if not assuming default DB for source')
    parser.add_argument('-p', '--partition_col', metavar='partition_column', type=str, required=False,
                        help='Column to create partition when extracting to Data Lake. Must be Date or Timestamp')
    args = parser.parse_args()

    spark = get_spark_session(f"Extract for source {args.table}")

    df_extract = spark.read \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://source-postgres:5432/source_db") \
        .option("dbtable", f"{args.schema}.{args.table}") \
        .option("user", "de_extract") \
        .option("password", "adminxd").load()

    if args.partition_col:
        # assuming 'p_creation_date' as p key, new argument might be needed to send a name for new partition key
        partitionby_field = "p_creation_date"
        df_extract = df_extract.withColumn(partitionby_field, to_date(args.partition_col, "yyyy-MM-dd"))
    else:
        partitionby_field = None

    df_extract.printSchema()  # for fun and to be able to visualize something else than random spark logs

    # potentially we won't want to overwrite in a pipeline for fact extract, but for test simplicity we will
    # assume overwrite. If batch extraction is required then we could pass two arguments more as start/end date and
    # filter accordingly
    spark.sql("CREATE DATABASE if NOT EXISTS bronze")
    df_extract.write.format("delta").saveAsTable(f'bronze.{args.schema}_{args.table}',
                                                 mode='overwrite',
                                                 partitionBy=partitionby_field)
