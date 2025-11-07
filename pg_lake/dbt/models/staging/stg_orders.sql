-- Staging view for orders
SELECT 
    order_id,
    customer_id,
    order_date,
    order_status
FROM iceberg.raw.orders

