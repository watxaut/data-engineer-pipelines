-- ============================================
-- Flink SQL Streaming Job
-- ============================================
-- This job reads from socket, processes events,
-- and writes to both ClickHouse (real-time) and
-- Iceberg (analytical)
-- ============================================

-- Set execution mode to streaming
SET 'execution.runtime-mode' = 'streaming';
SET 'table.exec.state.ttl' = '3600000'; -- 1 hour state TTL

-- ============================================
-- SOURCE: Socket Stream
-- ============================================
CREATE TABLE events_source (
    event_id STRING,
    event_type STRING,
    user_id STRING,
    timestamp_str STRING,
    session_id STRING,
    
    -- Event-specific fields (nullable)
    page STRING,
    referrer STRING,
    duration_seconds INT,
    element_id STRING,
    x_position INT,
    y_position INT,
    product STRING,
    amount DOUBLE,
    currency STRING,
    quantity INT,
    query STRING,
    results_count INT,
    price DOUBLE,
    
    -- Event time attribute
    event_time AS TO_TIMESTAMP(timestamp_str),
    WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
) WITH (
    'connector' = 'socket',
    'hostname' = 'data-generator',
    'port' = '9999',
    'format' = 'json'
);

-- ============================================
-- SINK 1: ClickHouse (Real-time)
-- ============================================
CREATE TABLE clickhouse_events (
    event_id STRING,
    event_type STRING,
    user_id STRING,
    event_time TIMESTAMP(3),
    session_id STRING,
    page STRING,
    product STRING,
    amount DOUBLE,
    query STRING,
    PRIMARY KEY (event_id) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:clickhouse://clickhouse:8123/default',
    'table-name' = 'events',
    'username' = 'default',
    'password' = 'clickhouse',
    'driver' = 'com.clickhouse.jdbc.ClickHouseDriver',
    'sink.buffer-flush.max-rows' = '100',
    'sink.buffer-flush.interval' = '1s'
);

-- ============================================
-- SINK 2: Iceberg (Analytical)
-- ============================================
CREATE CATALOG iceberg_catalog WITH (
    'type' = 'iceberg',
    'catalog-type' = 'rest',
    'uri' = 'http://iceberg-rest:8181',
    'warehouse' = 's3://warehouse/',
    'io-impl' = 'org.apache.iceberg.aws.s3.S3FileIO',
    's3.endpoint' = 'http://minio:9000',
    's3.access-key-id' = 'minioadmin',
    's3.secret-access-key' = 'minioadmin',
    's3.path-style-access' = 'true'
);

CREATE DATABASE IF NOT EXISTS iceberg_catalog.events;

CREATE TABLE IF NOT EXISTS iceberg_catalog.events.iceberg_events (
    event_id STRING,
    event_type STRING,
    user_id STRING,
    event_time TIMESTAMP(3),
    session_id STRING,
    page STRING,
    product STRING,
    amount DOUBLE,
    query STRING,
    ingest_time TIMESTAMP(3)
) WITH (
    'format-version' = '2',
    'write.format.default' = 'parquet',
    'write.metadata.compression-codec' = 'gzip'
);

-- ============================================
-- INSERT INTO ClickHouse (Real-time path)
-- ============================================
INSERT INTO clickhouse_events
SELECT 
    event_id,
    event_type,
    user_id,
    event_time,
    session_id,
    page,
    product,
    amount,
    query
FROM events_source;

-- ============================================
-- INSERT INTO Iceberg (Analytical path)
-- ============================================
INSERT INTO iceberg_catalog.events.iceberg_events
SELECT 
    event_id,
    event_type,
    user_id,
    event_time,
    session_id,
    page,
    product,
    amount,
    query,
    CURRENT_TIMESTAMP as ingest_time
FROM events_source;
