#!/bin/bash
# Stop OpenSearch Infrastructure

echo "🛑 Stopping OpenSearch Development Environment..."

# Stop all containers
docker compose -f infra/docker-compose.yml down

echo "✅ OpenSearch environment stopped"
echo ""
echo "💡 To remove volumes and start fresh:"
echo "   docker compose -f infra/docker-compose.yml down -v"