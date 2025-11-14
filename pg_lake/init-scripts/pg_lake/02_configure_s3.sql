-- Configure S3/MinIO access
-- Note: The actual S3 credentials are configured via pgduck_server
-- This is just a placeholder to document the configuration

-- You can verify the configuration by testing a simple copy operation
-- COPY (SELECT 1 as test) TO 's3://warehouse/test.parquet' WITH (format 'parquet');

