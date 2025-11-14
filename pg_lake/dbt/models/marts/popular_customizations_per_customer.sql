-- We need to add the location because else dbt adds the __dbt_tmp to the folder
{{
    config(
        materialized='table',
        database='hive',
        schema='analytics',
        properties={
            "format": "'PARQUET'",
            "external_location": "'s3://warehouse/hive/analytics/popular_customizations_per_customer'"
        }
    )
}}
-- TODO: you will need to manually drop the S3 location for it to work twice due to external_location existing
-- Popular customizations per customer and product
-- Aggregation at customer level, product level, and customization level
WITH unnested_customizations AS (
    SELECT 
        o.customer_id,
        bp.product_id,
        customization,
        o.order_id
    FROM {{ ref('stg_orders') }} o
    INNER JOIN {{ ref('stg_bought_products') }} bp 
        ON o.order_id = bp.order_id
    CROSS JOIN UNNEST(bp.product_customizations) AS t(customization)
)

SELECT 
    customer_id,
    product_id,
    customization,
    COUNT(*) AS customization_count
FROM unnested_customizations
GROUP BY 
    customer_id,
    product_id,
    customization
ORDER BY 
    customer_id,
    product_id,
    customization_count DESC

