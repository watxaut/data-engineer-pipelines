from pyspark.sql import functions as F
from pyspark.sql.window import Window

from utils import get_spark_session, read_hive_table

if __name__ == '__main__':
    spark = get_spark_session("Transform conversations")

    df_orders = read_hive_table(spark, table_name='bronze.public_orders')
    df_messages = read_hive_table(spark, table_name='bronze.public_customer_courier_chat_messages')

    # get user type from IDs (can also be achieved with sender_app_type with ILIKE expressions)
    df_messages = df_messages.withColumn(
        "user_type",
        F.when(df_messages.from_id == df_messages.courier_id, "Courier")
            .when(df_messages.from_id == df_messages.customer_id, "Customer")
            .otherwise("Unidentified user type")
    )

    # window function to partition per order_id and thus conversation
    w = Window.partitionBy("order_id").orderBy("message_sent_time")
    df_messages = df_messages.withColumn("first_message_by", F.first("user_type", ignorenulls=True).over(w)) \
        .withColumn("second_message_sent_at", F.lead("message_sent_time", 1).over(w)) \
        .withColumn("last_message_order_stage", F.last("order_stage", ignorenulls=True).over(w))

    # group by orders df_messages
    df_messages_by_order = df_messages.groupBy("order_id").agg(
        F.min(F.when(df_messages.user_type == "Courier", df_messages.message_sent_time)).alias("first_courier_message"),
        F.min(F.when(df_messages.user_type == "Customer", df_messages.message_sent_time)).alias(
            "first_customer_message"),
        F.count(F.when(df_messages.user_type == "Courier", 1)).alias("num_messages_courier"),
        F.count(F.when(df_messages.user_type == "Customer", 1)).alias("num_messages_customer"),
        F.min(df_messages.message_sent_time).alias("conversation_started_at"),
        F.max(df_messages.message_sent_time).alias("last_message_time"),
        F.first(df_messages.first_message_by).alias("first_message_by"),
        F.first(df_messages.second_message_sent_at).alias("second_message_sent_at"),
        F.first(df_messages.last_message_order_stage).alias("last_message_order_stage"),
    ).withColumnRenamed("order_id", "message_order_id")

    # assuming not all orders might have conversations, so joining from orders to messages. If there are messages
    # outside orders, then a full outer join needs to be performed if you also want all orders, or left join from
    # messages to orders
    final_df = df_orders \
        .join(df_messages_by_order, on=df_orders.order_id == df_messages_by_order.message_order_id, how='left') \
        .drop("message_order_id") \
        .withColumnRenamed("creation_time", "order_created_at")

    final_df = final_df \
        .withColumn("first_response_time_delay_seconds",
                    F.unix_timestamp(final_df.second_message_sent_at) -
                    F.unix_timestamp(final_df.conversation_started_at)) \
        .withColumn("p_creation_date", F.to_date("order_created_at", "yyyy-MM-dd"))

    final_df.printSchema()
    final_df.show(n=5, truncate=False, vertical=True)

    spark.sql("CREATE DATABASE if NOT EXISTS gold")

    # rearrange columns and place p_creation_date last
    final_df = final_df.select("order_id",
                               "city_code",
                               "first_courier_message",
                               "first_customer_message",
                               "num_messages_courier",
                               "num_messages_customer",
                               "conversation_started_at",
                               "last_message_time",
                               "first_message_by",
                               "second_message_sent_at",
                               "last_message_order_stage",
                               "first_response_time_delay_seconds",
                               "order_created_at",
                               "p_creation_date", )

    final_df.write.format("delta").saveAsTable('gold.customer_courier_conversations',
                                               mode='overwrite',
                                               partitionBy='p_creation_date')
