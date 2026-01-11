.PHONY: help start stop restart logs clean init verify test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

start: ## Start all services
	@echo "Starting Flink POC services..."
	docker-compose up -d
	@echo "✓ Services started!"
	@echo "Wait 30 seconds for services to initialize, then run: make verify"

stop: ## Stop all services
	@echo "Stopping services..."
	docker-compose stop

down: ## Stop and remove all containers
	@echo "Removing all containers..."
	docker-compose down

restart: ## Restart all services
	@echo "Restarting services..."
	docker-compose restart

logs: ## Tail logs from all services
	docker-compose logs -f

logs-flink: ## Tail Flink logs
	docker-compose logs -f flink-jobmanager flink-taskmanager-1 flink-taskmanager-2

logs-generator: ## Tail data generator logs
	docker-compose logs -f data-generator

clean: ## Remove all containers and volumes
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "✓ Cleanup complete"

verify: ## Verify all services are running
	@echo "Verifying services..."
	@echo ""
	@echo "1. Checking Docker containers..."
	@docker-compose ps
	@echo ""
	@echo "2. Service URLs:"
	@echo "  - Flink UI:      http://localhost:8081"
	@echo "  - Grafana:       http://localhost:3000 (admin/admin)"
	@echo "  - Superset:      http://localhost:8088 (admin/admin)"
	@echo "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
	@echo "  - Trino:         http://localhost:8080"
	@echo ""
	@echo "3. Quick health checks:"
	@curl -s http://localhost:8081/overview > /dev/null && echo "  ✓ Flink is running" || echo "  ✗ Flink is not responding"
	@curl -s http://localhost:3000/api/health > /dev/null && echo "  ✓ Grafana is running" || echo "  ✗ Grafana is not responding"
	@curl -s http://localhost:9001/minio/health/live > /dev/null && echo "  ✓ MinIO is running" || echo "  ✗ MinIO is not responding"

ps: ## Show running containers
	docker-compose ps

stats: ## Show resource usage
	docker stats --no-stream

clickhouse-cli: ## Open ClickHouse CLI
	docker exec -it clickhouse clickhouse-client

trino-cli: ## Open Trino CLI
	docker exec -it trino trino

minio-console: ## Open MinIO console in browser
	@echo "Opening MinIO Console..."
	@open http://localhost:9001 || xdg-open http://localhost:9001

flink-ui: ## Open Flink UI in browser
	@echo "Opening Flink Web UI..."
	@open http://localhost:8081 || xdg-open http://localhost:8081

grafana: ## Open Grafana in browser
	@echo "Opening Grafana..."
	@open http://localhost:3000 || xdg-open http://localhost:3000

superset: ## Open Superset in browser
	@echo "Opening Superset..."
	@open http://localhost:8088 || xdg-open http://localhost:8088

test-generator: ## Test data generator connection
	@echo "Testing data generator..."
	@docker logs data-generator | tail -20

query-clickhouse: ## Run sample ClickHouse query
	@echo "Running sample query on ClickHouse..."
	docker exec -it clickhouse clickhouse-client --query="SELECT event_type, count() as count FROM default.events GROUP BY event_type"

query-trino: ## Run sample Trino query
	@echo "Running sample query on Trino..."
	docker exec -it trino trino --execute="SELECT COUNT(*) as total_events FROM iceberg.events.iceberg_events"

build: ## Build all Docker images
	docker-compose build

rebuild: ## Rebuild all Docker images (no cache)
	docker-compose build --no-cache

pull: ## Pull latest images
	docker-compose pull
