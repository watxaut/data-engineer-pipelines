  WITH order_descriptors AS (
      SELECT *
        FROM {{ source('order_descriptors', 'order_descriptors') }}
       WHERE p_creation_month >= date('2022-09-01')
  ),
       ref_order_metrics AS (
           SELECT p_creation_month,
                  COUNT(*) AS num_orders
             FROM order_descriptors
           GROUP BY p_creation_month
       )
SELECT *
FROM ref_order_metrics
LIMIT 500  -- This is a POC, remove this in production
