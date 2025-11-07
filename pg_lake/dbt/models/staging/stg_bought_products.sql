-- Staging view for bought products
SELECT 
    bought_product_id,
    product_id,
    product_customizations,
    order_id
FROM iceberg.raw.bought_products

