-- ============================================
-- ClickHouse Initialization Script
-- ============================================
-- Creates tables for real-time event storage
-- ============================================

-- Create database
CREATE DATABASE IF NOT EXISTS default;

-- Create events table with MergeTree engine
CREATE TABLE IF NOT EXISTS default.events (
    event_id String,
    event_type String,
    user_id String,
    event_time DateTime64(3),
    session_id String,
    page Nullable(String),
    product Nullable(String),
    amount Nullable(Float64),
    query Nullable(String),
    inserted_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (event_type, event_time, event_id)
PARTITION BY toYYYYMM(event_time)
TTL event_time + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;

-- Create materialized view for event type aggregations
CREATE MATERIALIZED VIEW IF NOT EXISTS default.events_by_type_mv
ENGINE = SummingMergeTree()
ORDER BY (event_type, hour)
AS SELECT
    event_type,
    toStartOfHour(event_time) as hour,
    count() as event_count,
    uniqExact(user_id) as unique_users,
    avg(amount) as avg_amount
FROM default.events
GROUP BY event_type, hour;

-- Create materialized view for user activity
CREATE MATERIALIZED VIEW IF NOT EXISTS default.user_activity_mv
ENGINE = AggregatingMergeTree()
ORDER BY (user_id, hour)
AS SELECT
    user_id,
    toStartOfHour(event_time) as hour,
    count() as event_count,
    uniqExact(session_id) as session_count,
    sum(amount) as total_spent
FROM default.events
GROUP BY user_id, hour;
