  WITH order_metrics AS (
      SELECT *
        FROM {{ ref('ref_order_metrics') }}
  )
SELECT *
    FROM order_metrics
