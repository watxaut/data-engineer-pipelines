#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Flink Streaming POC - Quick Start Script${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Check available ports
echo -e "\n${YELLOW}Checking required ports...${NC}"
PORTS=(3000 8080 8081 8088 8123 9000 9001 9002 9999)
PORT_ERRORS=0

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}✗ Port $port is already in use${NC}"
        PORT_ERRORS=$((PORT_ERRORS + 1))
    else
        echo -e "${GREEN}✓ Port $port is available${NC}"
    fi
done

if [ $PORT_ERRORS -gt 0 ]; then
    echo -e "\n${RED}Some ports are in use. Please free them or stop conflicting services.${NC}"
    exit 1
fi

# Start services
echo -e "\n${YELLOW}Starting all services...${NC}"
docker-compose up -d

# Wait for services to initialize
echo -e "\n${YELLOW}Waiting for services to initialize (30 seconds)...${NC}"
for i in {30..1}; do
    echo -ne "${YELLOW}$i seconds remaining...\r${NC}"
    sleep 1
done
echo -e "${GREEN}✓ Initial startup complete${NC}"

# Health checks
echo -e "\n${YELLOW}Running health checks...${NC}"

# Check Flink
if curl -s http://localhost:8081/overview > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Flink JobManager is running${NC}"
else
    echo -e "${RED}✗ Flink JobManager is not responding${NC}"
fi

# Check MinIO
if curl -s http://localhost:9001/minio/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MinIO is running${NC}"
else
    echo -e "${RED}✗ MinIO is not responding${NC}"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Grafana is running${NC}"
else
    echo -e "${RED}✗ Grafana is not responding${NC}"
fi

# Check ClickHouse
if docker exec clickhouse clickhouse-client --query="SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ClickHouse is running${NC}"
else
    echo -e "${YELLOW}⚠ ClickHouse is starting...${NC}"
fi

# Check data generator
if docker logs data-generator 2>&1 | grep -q "listening"; then
    echo -e "${GREEN}✓ Data Generator is running${NC}"
else
    echo -e "${YELLOW}⚠ Data Generator is starting...${NC}"
fi

# Display access information
echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}   Services Ready!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${GREEN}Web Interfaces:${NC}"
echo -e "  • Flink UI:      ${BLUE}http://localhost:8081${NC}"
echo -e "  • Grafana:       ${BLUE}http://localhost:3000${NC} (admin/admin)"
echo -e "  • Superset:      ${BLUE}http://localhost:8088${NC} (admin/admin)"
echo -e "  • MinIO Console: ${BLUE}http://localhost:9001${NC} (minioadmin/minioadmin)"
echo -e "  • Trino:         ${BLUE}http://localhost:8080${NC}"
echo ""
echo -e "${GREEN}CLI Access:${NC}"
echo -e "  • ClickHouse: ${BLUE}docker exec -it clickhouse clickhouse-client${NC}"
echo -e "  • Trino:      ${BLUE}docker exec -it trino trino${NC}"
echo -e "  • Logs:       ${BLUE}docker-compose logs -f${NC}"
echo ""
echo -e "${GREEN}Quick Commands:${NC}"
echo -e "  • View logs:     ${BLUE}make logs${NC}"
echo -e "  • Stop all:      ${BLUE}make stop${NC}"
echo -e "  • Restart:       ${BLUE}make restart${NC}"
echo -e "  • Clean up:      ${BLUE}make clean${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Wait 1-2 minutes for all services to fully initialize"
echo -e "  2. Submit Flink job: See README.md for instructions"
echo -e "  3. Open Grafana to see real-time dashboards"
echo -e "  4. Query data in ClickHouse or Trino"
echo ""
echo -e "${GREEN}✓ Setup complete! Enjoy your Flink POC!${NC}"
