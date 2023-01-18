CREATE TABLE IF NOT EXISTS public.orders AS
    (
        SELECT 1::INTEGER AS order_id, 'BCN'::VARCHAR(3) AS city_code, '2022-09-19 08:00:00'::TIMESTAMP AS creation_time
         UNION ALL
        SELECT 2::INTEGER AS order_id, 'BUC'::VARCHAR(3) AS city_code, '2022-09-19 09:00:00'::TIMESTAMP AS creation_time
         UNION ALL
        SELECT 3::INTEGER AS order_id, 'MAD'::VARCHAR(3) AS city_code, '2022-09-19 10:00:00'::TIMESTAMP AS creation_time
         UNION ALL
        SELECT 4::INTEGER AS order_id, 'TBI'::VARCHAR(3) AS city_code, '2022-09-19 11:00:00'::TIMESTAMP AS creation_time
    )