# Flink POC Implementation Analysis: Simplified Architecture

## Executive Summary

This document provides a critical analysis of the **simplified** Flink POC architecture from a production engineering perspective. This version removes Kafka, ClickHouse, and Superset for a more manageable POC while still demonstrating core streaming concepts.

**Simplified Architecture (7 Services):**
```
Python Socket Server → Flink (Dual Sink)
         :9999           ├→ Clickhouse → Grafana (Real-time)
                         └→ Iceberg/MinIO → Trino -> Superset (Analytical)
```

## Architecture Overview

## Component Analysis

### 1. Python Socket Server

**What it is:** TCP socket server that streams events to Flink

**Implementation:**
```python
import socket, json, time

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 9999))
server.listen(1)
conn, addr = server.accept()

while True:
    event = generate_event()
    conn.sendall((json.dumps(event) + '\n').encode())
    time.sleep(0.01)  # 100 events/sec
```

#### ✅ Pros
- **Very simple**: ~150 lines of Python
- **No dependencies**: Only Python standard library
- **Direct connection**: Easy to debug (can telnet to test)
- **Fast setup**: No Kafka/ZooKeeper configuration
- **Saves resources**: No Kafka (1.5GB RAM saved)

#### ❌ Cons
- **Not production-ready**: Real systems use Kafka/Kinesis
- **No replay**: Can't reprocess events
- **No durability**: Events lost on disconnection
- **Single stream**: Parallelism = 1
- **Fragile**: Connection drops require restart

#### Production Migration
```
POC:        Socket source
Production: Replace with Kafka/Kinesis

Same Flink job, just change source connector!
```

### 2. Apache Flink ✅ CORE

**Configuration:**
- 1 JobManager + 2 TaskManagers
- Parallelism: 1 (socket limitation)
- Checkpointing: 60 seconds to MinIO
- State backend: RocksDB
- Dual sink: PostgreSQL + Iceberg

#### ✅ Pros
- True streaming (not micro-batches)
- Exactly-once to Iceberg ✅
- Stateful processing
- Event-time handling
- Industry standard

#### ❌ Cons
- Complex learning curve
- Resource intensive (4GB RAM)
- At-most-once from socket source ⚠️


### 3. Clickhouse ✅ SIMPLIFIED CHOICE


#### ✅ Pros
1. **Necessary for the POC**

### 4. MinIO + Iceberg ✅ KEEP

**No changes from original** - These are essential for the analytical path.

#### ✅ Pros
- Iceberg: Industry standard, ACID transactions
- MinIO: S3-compatible, easy migration to real S3
- Exactly-once writes from Flink ✅

#### ⚠️ Considerations
- Small file problem (need compaction)
- Replace MinIO with S3 in production

#### Verdict
✅ **Keep both** - Core learning objectives.

---

### 5. Trino ✅ KEEP

**No changes from original** - Essential for analytical queries.

#### Use Trino CLI instead of Superset

```bash
# Connect to Trino
docker exec -it trino trino

# Query Iceberg tables
trino> SELECT event_type, COUNT(*) FROM iceberg.events.iceberg_sink GROUP BY event_type;
```

#### ✅ Pros (vs Superset)
- Much simpler (no service to configure)
- Immediate query results
- Standard SQL

#### ❌ Cons (vs Superset)
- No dashboards
- Terminal-only
- No collaboration

#### Verdict
✅ **CLI is sufficient for POC** - Saves setup time.

**Add Metabase later if needed** (simpler than Superset).

---

### 6. Grafana ✅ KEEP

**Connects to PostgreSQL** (simpler than ClickHouse plugin)

```yaml
datasources:
  - name: PostgreSQL
    type: postgres  # Native support, no plugin needed
    url: postgres:5432
```

#### ✅ Pros
- Native PostgreSQL support
- Familiar to all developers
- Good for real-time dashboards

#### Verdict
✅ **Keep Grafana** - Essential for real-time visualization.

### 7. Superset

- Necessary for the POC

## Integration Points

### 1. Socket → Flink

```python
# Flink source configuration
CREATE TABLE events_source (...) WITH (
    'connector' = 'socket',
    'hostname' = 'data-generator',
    'port' = '9999',
    'format' = 'json'
)
```

#### ✅ Pros
- Very simple
- Direct connection
- Low latency (< 100ms)

#### ❌ Cons
- No replay
- Parallelism = 1
- Fragile connection

#### Verdict
✅ **Good for POC**, replace with Kafka for production.

---

### 2. Flink → Iceberg

**Exactly-once maintained** ✅

```python
CREATE TABLE iceberg_sink (...) WITH (
    'connector' = 'iceberg',
    'catalog-type' = 'rest',
    ...
)
```

#### Verdict
✅ **Production-ready** - ACID transactions, exactly-once.

