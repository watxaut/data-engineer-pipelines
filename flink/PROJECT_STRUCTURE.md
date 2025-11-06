# 📁 Project Structure

```
flink/
├── 📄 docker-compose.yml           # Main orchestration file (9 services)
├── 📄 .env                         # Environment variables
├── 📄 .gitignore                   # Git ignore patterns
├── 📄 Makefile                     # Convenient command shortcuts
├── 📄 start.sh                     # Quick start script
├── 📄 README.md                    # Complete documentation
├── 📄 QUICKSTART.md                # Quick start guide
├── 📄 PROJECT_STRUCTURE.md         # This file
│
├── 📁 data-generator/              # Python Socket Server (TCP :9999)
│   ├── Dockerfile                  # Python 3.11 slim image
│   ├── generator.py                # Event generator (150 lines)
│   └── requirements.txt            # Python dependencies (none needed)
│
├── 📁 flink/                       # Apache Flink Configuration
│   ├── Dockerfile                  # Flink 1.18 with connectors
│   ├── conf/
│   │   └── flink-conf.yaml        # JobManager/TaskManager config
│   └── jobs/
│       └── streaming_job.sql      # Flink SQL job definition
│
├── 📁 clickhouse/                  # ClickHouse Real-time DB
│   └── config/
│       └── init.sql               # Table schemas & materialized views
│
├── 📁 trino/                       # Trino Query Engine
│   └── catalog/
│       └── iceberg.properties     # Iceberg catalog configuration
│
├── 📁 grafana/                     # Grafana Dashboards
│   ├── datasources/
│   │   └── clickhouse.yml         # ClickHouse datasource config
│   └── dashboards/
│       ├── dashboard.yml          # Dashboard provisioning
│       └── realtime-events.json   # Pre-built dashboard
│
└── 📁 superset/                    # Apache Superset
    └── superset_config.py         # Superset configuration
```

## 📊 Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Flink Streaming POC                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ Data Generator   │  TCP Socket Server (Python)
│    :9999         │  → Generates 100 events/sec
└────────┬─────────┘  → Page views, clicks, purchases, etc.
         │
         │ TCP/JSON
         ▼
┌──────────────────────────────────────────────────────────────┐
│                   Apache Flink Cluster                       │
│  ┌────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │JobManager  │  │TaskManager-1│  │TaskManager-2│          │
│  │   :8081    │  │  2 slots    │  │  2 slots    │          │
│  └────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
│  • Event-time processing                                    │
│  • Exactly-once checkpointing → MinIO                       │
│  • Dual sink: ClickHouse + Iceberg                         │
└──────────────────┬─────────────────────┬─────────────────────┘
                   │                     │
         ┌─────────┘                     └──────────┐
         │                                          │
         ▼                                          ▼
┌─────────────────┐                    ┌──────────────────────┐
│  ClickHouse     │ Real-time Path     │   Iceberg/MinIO     │ Analytical Path
│    :8123        │                    │   :9000, :9001      │
│                 │                    │                      │
│ • MergeTree     │                    │ • Parquet format    │
│ • Materialized  │                    │ • Time travel       │
│   Views         │                    │ • ACID guarantees   │
│ • Fast queries  │                    │ • REST catalog      │
└────────┬────────┘                    └──────────┬───────────┘
         │                                        │
         ▼                                        ▼
┌─────────────────┐                    ┌──────────────────────┐
│    Grafana      │                    │       Trino          │
│     :3000       │                    │       :8080          │
│                 │                    │                      │
│ • Real-time     │                    │ • Distributed SQL   │
│   dashboards    │                    │ • Complex queries   │
│ • 5s refresh    │                    │ • Joins & aggs      │
└─────────────────┘                    └──────────┬───────────┘
                                                  │
                                                  ▼
                                       ┌──────────────────────┐
                                       │     Superset         │
                                       │      :8088           │
                                       │                      │
                                       │ • Analytical         │
                                       │   dashboards         │
                                       │ • Charts & viz       │
                                       └──────────────────────┘
```

## 🔧 Configuration Files

### Docker Compose Services

| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| **data-generator** | Custom (Python) | 9999 | Event generation |
| **flink-jobmanager** | Custom (Flink 1.18) | 8081 | Job coordination |
| **flink-taskmanager-1** | Custom (Flink 1.18) | - | Job execution |
| **flink-taskmanager-2** | Custom (Flink 1.18) | - | Job execution |
| **clickhouse** | clickhouse/clickhouse-server:23.8 | 8123, 9000 | Real-time OLAP |
| **minio** | minio/minio:latest | 9001, 9002 | S3 storage |
| **minio-init** | minio/mc:latest | - | Bucket initialization |
| **iceberg-rest** | tabulario/iceberg-rest:0.6.0 | 8181 | Table catalog |
| **trino** | trinodb/trino:428 | 8080 | Query engine |
| **grafana** | grafana/grafana:10.1.5 | 3000 | Real-time viz |
| **superset** | apache/superset:3.0.0 | 8088 | Analytical viz |

## 📦 Docker Images & Dependencies

### Flink Dependencies (Downloaded at build)
- `flink-sql-connector-kafka-1.18.0.jar`
- `clickhouse-jdbc-0.4.6-all.jar`
- `iceberg-flink-runtime-1.18-1.4.2.jar`
- `hadoop-aws-3.3.4.jar`
- `aws-java-sdk-bundle-1.12.262.jar`
- `flink-statebackend-rocksdb-1.18.0.jar`

## 🌐 Network Configuration

All services run on the `flink-network` bridge network:

```yaml
networks:
  flink-network:
    driver: bridge
```

This allows services to communicate using container names as hostnames:
- `data-generator:9999`
- `flink-jobmanager:8081`
- `clickhouse:8123`
- `minio:9000`
- `iceberg-rest:8181`
- `trino:8080`

## 💾 Persistent Volumes

```yaml
volumes:
  clickhouse-data    # ClickHouse database files
  minio-data         # MinIO object storage (Iceberg files, checkpoints)
  grafana-data       # Grafana dashboards and settings
  superset-data      # Superset metadata and dashboards
```

## 🔐 Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Grafana | admin | admin |
| Superset | admin | admin |
| MinIO | minioadmin | minioadmin |
| ClickHouse | default | clickhouse |
| Trino | - | - |

## 📝 Key Files Explained

### `docker-compose.yml`
- Orchestrates 9 services
- Defines networks and volumes
- Sets environment variables
- Configures health checks

### `data-generator/generator.py`
- Creates synthetic events (page_view, click, purchase, search, cart_add)
- Sends JSON events via TCP socket
- Configurable rate (default: 100 events/sec)
- Reconnects automatically on disconnect

### `flink/jobs/streaming_job.sql`
- Defines socket source connector
- Creates dual sinks (ClickHouse + Iceberg)
- Sets up event-time processing
- Configures watermarks

### `flink/conf/flink-conf.yaml`
- JobManager and TaskManager settings
- Checkpointing configuration
- State backend (RocksDB)
- S3/MinIO configuration

### `clickhouse/config/init.sql`
- Creates `events` table with MergeTree engine
- Defines materialized views for aggregations
- Sets up partitioning and TTL

### `trino/catalog/iceberg.properties`
- Configures Iceberg REST catalog
- Sets S3/MinIO connection details
- Enables path-style access

### `grafana/datasources/clickhouse.yml`
- Auto-provisions ClickHouse datasource
- Sets connection parameters
- Enables immediate querying

### `Makefile`
- Provides convenient shortcuts
- Health checks and verification
- Quick access to CLIs
- Service management

### `start.sh`
- Interactive startup script
- Port availability check
- Health verification
- Service status display

## 🚀 Resource Requirements

### Minimum
- **CPU**: 4 cores
- **RAM**: 8GB
- **Disk**: 10GB free space

### Recommended
- **CPU**: 8 cores
- **RAM**: 16GB
- **Disk**: 20GB free space

### Per-Service Memory
- Flink JobManager: 2GB
- Flink TaskManager (each): 2GB
- ClickHouse: 1.5GB
- MinIO: 500MB
- Trino: 1.5GB
- Grafana: 200MB
- Superset: 500MB
- Data Generator: 50MB

## 📊 Data Flow Summary

1. **Generation**: Python socket server creates events
2. **Ingestion**: Flink consumes via socket connector
3. **Processing**: Event-time processing with watermarks
4. **Real-time Sink**: ClickHouse for sub-second queries
5. **Analytical Sink**: Iceberg/MinIO for historical analysis
6. **Real-time Viz**: Grafana dashboards (5s refresh)
7. **Analytical Viz**: Superset dashboards
8. **Ad-hoc Queries**: Trino SQL interface

## 🔄 Exactly-Once Semantics

```
Socket Source     → At-most-once ⚠️
  ↓
Flink Processing  → Exactly-once ✅ (RocksDB + Checkpointing)
  ↓
ClickHouse Sink   → At-least-once ⚠️ (JDBC)
  ↓
Iceberg Sink      → Exactly-once ✅ (ACID transactions)
```

## 📈 Scalability Paths

1. **Add more TaskManagers**: Scale Flink processing
2. **Increase parallelism**: Modify socket to Kafka
3. **Shard ClickHouse**: Use distributed tables
4. **Partition Iceberg**: Add partition specs
5. **Scale Trino**: Add worker nodes

---

**Total Project Size**: ~3,500 lines of code/config
**Languages**: Python, SQL, YAML, Bash, Markdown
**Services**: 11 containers
**Ports**: 9 exposed
**Networks**: 1 bridge network
**Volumes**: 4 persistent volumes
