#!/bin/bash

echo "=========================================="
echo "🚀 Starting MCP-Enabled Chat Client"
echo "=========================================="

# Set API key
# Set your API key here or export it before running this script
# export ALIBABA_CLOUD_API_KEY='your-api-key'
if [ -z "$ALIBABA_CLOUD_API_KEY" ]; then
    echo "❌ Error: ALIBABA_CLOUD_API_KEY not set"
    echo "Please run: export ALIBABA_CLOUD_API_KEY='your-api-key'"
    exit 1
fi

# Clear previous log
> /tmp/weather_mcp.log

echo ""
echo "📋 Starting dataflow with MCP support..."
dora start chat_mcp_dataflow.yml --name mcp-chat --detach

# Wait for initialization
sleep 3

# Check if MCP tools loaded
echo "🔍 Checking MCP tool loading..."
if grep -q "get_weather" /tmp/weather_mcp.log; then
    echo "✅ MCP tools loaded successfully!"
else
    echo "⚠️  MCP tools may not be loaded, continuing anyway..."
fi

echo ""
echo "💬 Starting interactive chat client..."
echo "----------------------------------------"

# Run the chat client as dynamic node
python3 chat_client.py

echo ""
echo "🧹 Cleaning up..."
dora stop mcp-chat 2>/dev/null

echo "👋 Chat session ended"