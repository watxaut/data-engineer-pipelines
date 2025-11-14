-- Create pg_lake extension and dependencies
CREATE EXTENSION IF NOT EXISTS pg_lake CASCADE;

-- Configure pg_lake for MinIO
SET pg_lake_iceberg.default_location_prefix TO 's3://warehouse';

-- Verify extension installation
\dx pg_lake

