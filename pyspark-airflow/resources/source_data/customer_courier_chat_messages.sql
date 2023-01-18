CREATE TABLE IF NOT EXISTS public.customer_courier_chat_messages AS
    (
        SELECT 'Customer iOS'::VARCHAR(20)      AS sender_app_type,
               10                               AS customer_id,
               10                               AS from_id,
               20                               AS to_id,
               FALSE                            AS chat_started_by_message,
               1                                AS order_id,
               'PICKING_UP'                     AS order_stage,
               20                               AS courier_id,
               '2022-09-19T08:01:47'::TIMESTAMP AS message_sent_time
         UNION ALL
        SELECT 'Courier iOS'::VARCHAR(20)       AS sender_app_type,
               10                               AS customer_id,
               20                               AS from_id,
               10                               AS to_id,
               FALSE                            AS chat_started_by_message,
               1                                AS order_id,
               'PICKING_UP'                     AS order_stage,
               20                               AS courier_id,
               '2022-09-19T08:10:47'::TIMESTAMP AS message_sent_time
         UNION ALL
        SELECT 'Customer iOS'::VARCHAR(20)      AS sender_app_type,
               10                               AS customer_id,
               10                               AS from_id,
               20                               AS to_id,
               FALSE                            AS chat_started_by_message,
               1                                AS order_id,
               'PICKING_UP'                     AS order_stage,
               20                               AS courier_id,
               '2022-09-19T08:11:47'::TIMESTAMP AS message_sent_time
         UNION ALL
        SELECT 'Courier iOS'::VARCHAR(20)       AS sender_app_type,
               10                               AS customer_id,
               20                               AS from_id,
               10                               AS to_id,
               FALSE                            AS chat_started_by_message,
               1                                AS order_id,
               'DELIVERING'                     AS order_stage,
               20                               AS courier_id,
               '2022-09-19T08:12:47'::TIMESTAMP AS message_sent_time
         UNION ALL
        SELECT 'Courier iOS'::VARCHAR(20)       AS sender_app_type,
               11                               AS customer_id,
               21                               AS from_id,
               11                               AS to_id,
               FALSE                            AS chat_started_by_message,
               2                                AS order_id,
               'DELIVERING'                     AS order_stage,
               21                               AS courier_id,
               '2022-09-19T08:00:47'::TIMESTAMP AS message_sent_time
         UNION ALL
        SELECT 'Courier iOS'::VARCHAR(20)       AS sender_app_type,
               12                               AS customer_id,
               22                               AS from_id,
               12                               AS to_id,
               FALSE                            AS chat_started_by_message,
               3                                AS order_id,
               'PICKING_UP'                     AS order_stage,
               22                               AS courier_id,
               '2022-09-19T08:00:47'::TIMESTAMP AS message_sent_time
         UNION ALL
        SELECT 'Courier iOS'::VARCHAR(20)       AS sender_app_type,
               12                               AS customer_id,
               12                               AS from_id,
               12                               AS to_id,
               FALSE                            AS chat_started_by_message,
               3                                AS order_id,
               'PICKING_UP'                     AS order_stage,
               22                               AS courier_id,
               '2022-09-19T08:10:48'::TIMESTAMP AS message_sent_time
    )
