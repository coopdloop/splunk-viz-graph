#!/bin/bash
# Start OpenSearch Infrastructure

set -e

echo "🚀 Starting OpenSearch Development Environment..."

# Start the infrastructure
echo "📦 Starting containers..."
docker compose -f infra/docker-compose.yml up -d

echo "⏳ Waiting for OpenSearch to be ready..."
timeout=180
counter=0

while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:9200/_cluster/health | grep -q '"status":"[yellow|green]"'; then
        echo "✅ OpenSearch is ready!"
        break
    fi
    echo "   Still starting... ($counter/$timeout seconds)"
    sleep 5
    counter=$((counter + 5))
done

if [ $counter -ge $timeout ]; then
    echo "❌ OpenSearch failed to start within $timeout seconds"
    echo "📋 Container status:"
    docker compose -f infra/docker-compose.yml ps
    echo "📋 OpenSearch logs:"
    docker compose -f infra/docker-compose.yml logs opensearch --tail 20
    exit 1
fi

# Check cluster health
echo "🏥 Cluster health:"
curl -s http://localhost:9200/_cluster/health | jq '.'

# Show service status
echo ""
echo "📊 Service Status:"
echo "   OpenSearch API: http://localhost:9200"
echo "   OpenSearch Dashboards: http://localhost:5601"
echo ""

# Check if data generator is running
if docker compose -f infra/docker-compose.yml ps data-generator | grep -q "Up"; then
    echo "📡 Data generator is running"
    echo "   Generating vendor logs every 10 seconds..."
    echo "   Use 'docker compose -f infra/docker-compose.yml logs -f data-generator' to watch"
else
    echo "⚠️  Data generator is not running, check logs:"
    echo "   docker compose -f infra/docker-compose.yml logs data-generator"
fi

echo ""
echo "✅ OpenSearch development environment is ready!"
echo "💡 Next steps:"
echo "   1. Open opensearch-analysis.ipynb in Jupyter"
echo "   2. Run: uv run jupyter lab opensearch-analysis.ipynb"
echo "   3. Use 'Local Development OpenSearch' environment"