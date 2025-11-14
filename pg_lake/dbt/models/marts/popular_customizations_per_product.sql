{{
    config(
        materialized='table',
        database='hive',
        schema='analytics',
        properties={
            "format": "'PARQUET'",
            "external_location": "'s3://warehouse/hive/analytics/popular_customizations_per_product'"
        }
    )
}}

-- TODO: you will need to manually drop the S3 location for it to work twice due to external_location existing
-- Popular customizations per product
-- Aggregation at product level and customization level
WITH unnested_customizations AS (
    SELECT 
        bp.product_id,
        customization
    FROM {{ ref('stg_bought_products') }} bp
    CROSS JOIN UNNEST(bp.product_customizations) AS t(customization)
)

SELECT 
    product_id,
    customization,
    COUNT(*) AS customization_count
FROM unnested_customizations
GROUP BY 
    product_id,
    customization
ORDER BY 
    product_id,
    customization_count DESC

