# Flink Streaming POC - Simplified Architecture

A production-ready proof-of-concept demonstrating real-time streaming data processing with Apache Flink.

## 🏗️ Architecture

```
Python Socket Server → Apache Flink (Dual Sink)
      :9999                ├→ ClickHouse → Grafana (Real-time)
                           └→ Iceberg/MinIO → Trino → Superset (Analytical)
```

### Components

| Component | Purpose | Port | URL |
|-----------|---------|------|-----|
| **Data Generator** | TCP socket server streaming events | 9999 | - |
| **Flink JobManager** | Flink cluster coordinator | 8081 | http://localhost:8081 |
| **Flink TaskManagers** | Flink workers (2 instances) | - | - |
| **ClickHouse** | Real-time OLAP database | 8123, 9000 | http://localhost:8123 |
| **MinIO** | S3-compatible object storage | 9001, 9002 | http://localhost:9001 |
| **Iceberg REST** | Table catalog service | 8181 | - |
| **Trino** | Distributed SQL query engine | 8080 | http://localhost:8080 |
| **Grafana** | Real-time dashboards | 3000 | http://localhost:3000 |
| **Superset** | Analytical dashboards | 8088 | http://localhost:8088 |

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- At least 8GB RAM available
- Ports 3000, 8080, 8081, 8088, 8123, 9000-9002, 9999 available

### 1. Start the Stack

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 2. Verify Services

**Data Generator** (wait 10-20 seconds for connection):
```bash
# Check if events are being generated
docker logs data-generator

# Should see: "Connection established" and event counts
```

**Flink Web UI**:
```bash
# Open browser
open http://localhost:8081

# Should see JobManager with 2 TaskManagers
```

**ClickHouse**:
```bash
# Connect to ClickHouse
docker exec -it clickhouse clickhouse-client

# Query events
SELECT event_type, count() FROM events GROUP BY event_type;
```

**MinIO Console**:
```bash
# Open browser
open http://localhost:9001

# Login: minioadmin / minioadmin
# Should see buckets: flink, iceberg, warehouse
```

**Trino CLI**:
```bash
# Connect to Trino
docker exec -it trino trino

# List catalogs
SHOW CATALOGS;

# Query Iceberg tables
SELECT * FROM iceberg.events.iceberg_events LIMIT 10;
```

**Grafana**:
```bash
# Open browser
open http://localhost:3000

# Login: admin / admin
# Dashboard: "Real-time Event Analytics"
```

**Superset**:
```bash
# Open browser
open http://localhost:8088

# Login: admin / admin
# Add Trino database connection:
# - Type: Trino
# - Host: trino
# - Port: 8080
# - Database: iceberg
```

## 📊 Data Flow

### Real-time Path (Low Latency)
1. **Data Generator** sends events via TCP socket
2. **Flink** processes events with exactly-once semantics
3. **ClickHouse** stores events in MergeTree tables
4. **Grafana** visualizes real-time metrics (refreshes every 5s)

### Analytical Path (High Throughput)
1. **Data Generator** sends events via TCP socket
2. **Flink** processes and writes to Iceberg with exactly-once
3. **MinIO** stores Parquet files (S3-compatible)
4. **Trino** queries Iceberg tables with SQL
5. **Superset** creates analytical dashboards

## 🔧 Configuration

### Environment Variables

Edit `.env` file to customize:

```bash
# Data generation rate
EVENTS_PER_SECOND=100

# MinIO credentials
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# ClickHouse credentials
CLICKHOUSE_PASSWORD=clickhouse

# Flink settings
FLINK_CHECKPOINT_INTERVAL=60000
```

### Flink Job

The Flink job is defined in `flink/jobs/streaming_job.sql`:
- Reads from socket source
- Processes with event-time semantics
- Dual sink: ClickHouse + Iceberg
- Exactly-once checkpointing to MinIO

To submit the job:
```bash
docker exec -it flink-jobmanager /opt/flink/bin/sql-client.sh -f /opt/flink/jobs/streaming_job.sql
```

## 📈 Sample Queries

### ClickHouse (Real-time Analytics)

```sql
-- Events per minute (last hour)
SELECT 
    toStartOfMinute(event_time) as minute,
    count() as events
FROM events
WHERE event_time > now() - INTERVAL 1 HOUR
GROUP BY minute
ORDER BY minute;

-- Top users by purchase amount
SELECT 
    user_id,
    sum(amount) as total_spent,
    count() as purchases
FROM events
WHERE event_type = 'purchase'
GROUP BY user_id
ORDER BY total_spent DESC
LIMIT 10;

-- Event distribution
SELECT 
    event_type,
    count() as count,
    round(count() * 100.0 / sum(count()) OVER (), 2) as percentage
FROM events
GROUP BY event_type;
```

### Trino (Analytical Queries)

```sql
-- Daily event summary
SELECT 
    DATE(event_time) as date,
    event_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as unique_users
FROM iceberg.events.iceberg_events
GROUP BY DATE(event_time), event_type
ORDER BY date DESC, event_type;

-- User behavior analysis
SELECT 
    user_id,
    COUNT(DISTINCT session_id) as sessions,
    COUNT(*) as total_events,
    SUM(CASE WHEN event_type = 'purchase' THEN amount ELSE 0 END) as total_revenue
FROM iceberg.events.iceberg_events
GROUP BY user_id
ORDER BY total_revenue DESC
LIMIT 20;

-- Hourly revenue trend
SELECT 
    DATE_TRUNC('hour', event_time) as hour,
    COUNT(*) as purchases,
    SUM(amount) as revenue,
    AVG(amount) as avg_order_value
FROM iceberg.events.iceberg_events
WHERE event_type = 'purchase'
GROUP BY DATE_TRUNC('hour', event_time)
ORDER BY hour DESC;
```

## 🛠️ Troubleshooting

### Services not starting

```bash
# Check service logs
docker-compose logs <service-name>

# Restart a specific service
docker-compose restart <service-name>

# Full restart
docker-compose down && docker-compose up -d
```

### Data generator connection issues

```bash
# Check if Flink is ready
docker logs flink-jobmanager

# Restart data generator
docker-compose restart data-generator
```

### ClickHouse table not found

```bash
# Initialize tables manually
docker exec -it clickhouse clickhouse-client < clickhouse/config/init.sql
```

### MinIO bucket errors

```bash
# Re-run bucket initialization
docker-compose restart minio-init
```

### Flink job not running

```bash
# Check Flink UI: http://localhost:8081
# Submit job manually:
docker exec -it flink-jobmanager /opt/flink/bin/sql-client.sh -f /opt/flink/jobs/streaming_job.sql
```

## 📊 Monitoring

### Flink Metrics
- **Web UI**: http://localhost:8081
- **Checkpoints**: S3://flink/checkpoints in MinIO
- **Job status**: Running Jobs tab

### ClickHouse Performance
```sql
-- Table size
SELECT 
    table,
    formatReadableSize(sum(bytes)) as size,
    sum(rows) as rows
FROM system.parts
WHERE active
GROUP BY table;

-- Query performance
SELECT 
    query_id,
    query,
    query_duration_ms
FROM system.query_log
ORDER BY event_time DESC
LIMIT 10;
```

### Resource Usage
```bash
# Docker stats
docker stats

# Service-specific
docker stats flink-jobmanager flink-taskmanager-1 flink-taskmanager-2
```

## 🧹 Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## 🎯 Next Steps

### Production Migration
1. **Replace Socket Source** → Kafka/Kinesis
2. **Replace MinIO** → AWS S3/Azure Blob
3. **Scale Flink** → Add more TaskManagers
4. **Add Authentication** → Secure all endpoints
5. **Add Monitoring** → Prometheus + AlertManager
6. **Add Schema Registry** → Avro/Protobuf schemas
7. **Tune Checkpointing** → Optimize for your SLA

### Learning Paths
1. **Explore Flink SQL**: Windowing, aggregations, joins
2. **ClickHouse**: Materialized views, projections
3. **Iceberg**: Partitioning, time travel, compaction
4. **Trino**: Distributed joins, query optimization

## 📚 Resources

- [Apache Flink Documentation](https://flink.apache.org/)
- [ClickHouse Documentation](https://clickhouse.com/docs)
- [Apache Iceberg](https://iceberg.apache.org/)
- [Trino Documentation](https://trino.io/docs/current/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Apache Superset](https://superset.apache.org/)

## 📝 License

MIT License - See LICENSE file for details
