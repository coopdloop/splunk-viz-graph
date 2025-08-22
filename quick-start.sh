#!/bin/bash

# Quick Start Script for Docker Splunk Environment
# This script sets up and launches the Splunk vendor analysis tool

echo "🚀 Splunk Vendor Query Tool - Quick Start"
echo "=========================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   source ~/.cargo/env"
    exit 1
fi

echo "✅ uv found"

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Check if Splunk is accessible
echo "🔍 Checking Splunk connectivity..."
if curl -s -k --max-time 5 http://localhost:8089/services/server/info -u admin:splunksplunk > /dev/null 2>&1; then
    echo "✅ Splunk is accessible at localhost:8089"
else
    echo "⚠️  Splunk not accessible at localhost:8089"
    echo "   Please ensure your Splunk Docker container is running:"
    echo "   docker ps | grep splunk"
    echo ""
    echo "   If not running, start it with:"
    echo "   docker run -d --name splunk -p 8000:8000 -p 8089:8089 \\"
    echo "     -e SPLUNK_START_ARGS=--accept-license \\"
    echo "     -e SPLUNK_USERNAME=admin \\"
    echo "     -e SPLUNK_PASSWORD=splunksplunk \\"
    echo "     splunk/splunk:latest"
    echo ""
    echo "   You can still proceed - configure the connection in the notebook."
fi

# Create exports directory
mkdir -p exports
echo "✅ Created exports directory"

# Display configuration summary
echo ""
echo "📋 Configuration Summary:"
echo "   Splunk Host: localhost:8089"
echo "   Username: admin"
echo "   Password: splunksplunk"
echo "   HEC Token: 12345678-1234-1234-1234-123456789012"
echo "   Environment: Docker Local (via localhost)"
echo ""

# Launch Jupyter
echo "🚀 Launching Jupyter Lab..."
echo "   Opening vendor-analysis.ipynb..."
echo "   Browser should open automatically"
echo ""
echo "📝 Next Steps in Jupyter:"
echo "   1. Select 'Docker Local (via localhost)' environment"
echo "   2. Click 'Initialize Connection'"
echo "   3. Click 'Test Connection'"
echo "   4. Configure query settings"
echo "   5. Execute vendor analysis"
echo ""

# Launch Jupyter Lab with the specific notebook
uv run jupyter lab vendor-analysis.ipynb --no-browser --port=8888 &

# Wait a moment for Jupyter to start
sleep 3

# Try to open browser (works on macOS and most Linux systems)
if command -v open &> /dev/null; then
    open http://localhost:8888/lab/tree/vendor-analysis.ipynb
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8888/lab/tree/vendor-analysis.ipynb
else
    echo "🌐 Jupyter Lab is running at: http://localhost:8888"
    echo "   Manually open this URL in your browser"
fi

echo ""
echo "✅ Setup complete! Jupyter Lab should be running."
echo "   Press Ctrl+C to stop Jupyter when done."

# Keep script running so user can see the output
wait