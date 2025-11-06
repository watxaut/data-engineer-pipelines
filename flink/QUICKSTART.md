# 🚀 Quick Start Guide

## Prerequisites Check

Before starting, ensure you have:
- ✅ Docker Desktop installed and running
- ✅ At least 8GB RAM available
- ✅ 10GB free disk space
- ✅ Ports available: 3000, 8080, 8081, 8088, 8123, 9000-9002, 9999

## 🎯 30-Second Start

```bash
# Start everything
./start.sh

# OR using make
make start

# OR using docker-compose
docker-compose up -d
```

Wait 1-2 minutes for services to initialize.

## ✅ Verify Installation

```bash
# Check all services
make verify

# View logs
make logs

# Check specific service
docker logs flink-jobmanager
docker logs data-generator
```

## 🔗 Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Flink UI** | http://localhost:8081 | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Superset** | http://localhost:8088 | admin / admin |
| **MinIO** | http://localhost:9001 | minioadmin / minioadmin |
| **ClickHouse** | http://localhost:8123 | default / clickhouse |

## 📊 First Steps

### 1. Check Data is Flowing

```bash
# View data generator logs
make logs-generator

# Should see: "Connection established" and event counts
```

### 2. Query ClickHouse (Real-time)

```bash
# Open CLI
make clickhouse-cli

# Run query
SELECT event_type, count() as count 
FROM events 
GROUP BY event_type;
```

### 3. Query Trino (Analytical)

```bash
# Open CLI
make trino-cli

# List tables
SHOW TABLES FROM iceberg.events;

# Query data
SELECT * FROM iceberg.events.iceberg_events LIMIT 10;
```

### 4. View Grafana Dashboard

1. Open http://localhost:3000
2. Login: admin / admin
3. Navigate to Dashboards → Real-time Event Analytics
4. See live data refreshing every 5 seconds

### 5. Create Superset Dashboard

1. Open http://localhost:8088
2. Login: admin / admin
3. Settings → Database Connections → + Database
4. Configure Trino:
   - **Supported Database**: Trino
   - **Display Name**: Trino
   - **SQLAlchemy URI**: `trino://trino@trino:8080/iceberg`
5. Click "Test Connection"
6. Create charts from `iceberg.events.iceberg_events`

## 🧪 Test Queries

### ClickHouse - Real-time Analytics

```sql
-- Events in last 5 minutes
SELECT 
    toStartOfMinute(event_time) as minute,
    event_type,
    count() as events
FROM events
WHERE event_time > now() - INTERVAL 5 MINUTE
GROUP BY minute, event_type
ORDER BY minute DESC;

-- Top users by activity
SELECT 
    user_id,
    count() as events,
    uniqExact(session_id) as sessions
FROM events
WHERE event_time > now() - INTERVAL 1 HOUR
GROUP BY user_id
ORDER BY events DESC
LIMIT 10;

-- Revenue summary
SELECT 
    sum(amount) as total_revenue,
    avg(amount) as avg_amount,
    count() as purchases
FROM events
WHERE event_type = 'purchase';
```

### Trino - Analytical Queries

```sql
-- Daily summary
SELECT 
    DATE(event_time) as date,
    event_type,
    COUNT(*) as count
FROM iceberg.events.iceberg_events
GROUP BY DATE(event_time), event_type
ORDER BY date DESC;

-- User cohort analysis
SELECT 
    user_id,
    COUNT(DISTINCT DATE(event_time)) as active_days,
    COUNT(*) as total_events,
    SUM(amount) as lifetime_value
FROM iceberg.events.iceberg_events
GROUP BY user_id
ORDER BY lifetime_value DESC
LIMIT 20;
```

## 🔧 Common Tasks

### View Logs

```bash
# All services
make logs

# Specific service
docker-compose logs -f flink-jobmanager
docker-compose logs -f data-generator
docker-compose logs -f clickhouse
```

### Restart Services

```bash
# Restart all
make restart

# Restart specific service
docker-compose restart flink-jobmanager
docker-compose restart data-generator
```

### Stop Everything

```bash
# Stop (keep data)
make stop

# Stop and remove containers (keep data)
make down

# Stop and remove everything including data
make clean
```

## 🐛 Troubleshooting

### Data Generator Not Connecting

```bash
# Check if Flink is ready
curl http://localhost:8081/overview

# Restart generator
docker-compose restart data-generator
```

### No Data in ClickHouse

```bash
# Check if table exists
docker exec -it clickhouse clickhouse-client --query="SHOW TABLES"

# Create table manually if needed
docker exec -it clickhouse clickhouse-client < clickhouse/config/init.sql
```

### Flink Job Not Running

```bash
# Check Flink UI
open http://localhost:8081

# Submit job manually
docker exec -it flink-jobmanager /opt/flink/bin/sql-client.sh -f /opt/flink/jobs/streaming_job.sql
```

### MinIO Buckets Not Created

```bash
# Re-run initialization
docker-compose restart minio-init

# Verify buckets
docker exec -it minio mc ls myminio
```

### Port Already in Use

```bash
# Find process using port (e.g., 8081)
lsof -i :8081

# Kill process
kill -9 <PID>
```

## 📈 Monitoring

### Resource Usage

```bash
# All containers
make stats

# Continuous monitoring
docker stats
```

### Flink Metrics

- Web UI: http://localhost:8081
- Job → Running Jobs → Select job → Metrics

### Service Health

```bash
# Quick health check
make verify

# Individual checks
curl http://localhost:8081/overview        # Flink
curl http://localhost:3000/api/health      # Grafana
curl http://localhost:9001/minio/health/live  # MinIO
```

## 🎓 Learning Path

1. **Day 1**: Get everything running, explore UIs
2. **Day 2**: Understand data flow, write custom queries
3. **Day 3**: Create dashboards in Grafana and Superset
4. **Day 4**: Modify Flink job, experiment with windows
5. **Day 5**: Performance tuning, scaling

## 📚 Next Steps

- Read `README.md` for detailed documentation
- Explore Flink SQL in `flink/jobs/streaming_job.sql`
- Create custom dashboards in Grafana
- Experiment with Trino queries
- Scale by adding more TaskManagers

## 🆘 Getting Help

1. Check logs: `make logs`
2. Review README.md troubleshooting section
3. Verify all ports are available
4. Ensure Docker has enough resources (8GB RAM minimum)
5. Try `make clean` and `make start` for a fresh start

---

**Happy Streaming! 🎉**
