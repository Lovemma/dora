#!/bin/bash

# MCP Integration Test for Alibaba Cloud qwen-max
# Tests if qwen-max can properly call MCP tools like weather

set -e

echo "=========================================="
echo "🧪 Alibaba Cloud MCP Integration Test"
echo "=========================================="
echo "Testing: qwen-max with mock weather MCP server"
echo "=========================================="
echo ""

# Check for API key
if [ -z "$ALIBABA_CLOUD_API_KEY" ]; then
    echo "⚠️  Error: ALIBABA_CLOUD_API_KEY not set!"
    echo "   Set it with: export ALIBABA_CLOUD_API_KEY='sk-your-key'"
    echo ""
    echo -n "Enter your API key now (or press Enter to exit): "
    read api_key
    if [ -z "$api_key" ]; then
        echo "❌ Exiting: API key required"
        exit 1
    fi
    export ALIBABA_CLOUD_API_KEY="$api_key"
    echo "✅ API key set for this session"
    echo ""
fi

# Check if Dora is running
echo "📋 Checking Dora status..."
if ! dora check > /dev/null 2>&1; then
    echo "❌ Dora is not running. Starting it now..."
    dora up &
    sleep 3
    
    if ! dora check > /dev/null 2>&1; then
        echo "❌ Failed to start Dora. Please run: dora up"
        exit 1
    fi
fi
echo "✅ Dora is running"
echo ""

# Clean up any existing test dataflow
echo "🧹 Cleaning up existing test dataflows..."
dora stop --name mcp-test 2>/dev/null || true
echo ""

# Start the MCP test dataflow
echo "🚀 Starting MCP test dataflow..."
echo "   This will:"
echo "   1. Start the mock weather MCP server"
echo "   2. Initialize MaaS client with qwen-max"
echo "   3. Test MCP tool registration"
echo "   4. Test weather queries"
echo ""

# Run the dataflow
dora start mcp_test_dataflow.yml --name mcp-test

echo ""
echo "=========================================="
echo "📊 Test Results"
echo "=========================================="

# Check the log file for results
if [ -f "/tmp/weather_mcp.log" ]; then
    echo ""
    echo "📝 MCP Server Log (last 10 lines):"
    echo "-----------------------------------------"
    tail -10 /tmp/weather_mcp.log
fi

echo ""
echo "✅ Test completed!"
echo ""
echo "To view full logs:"
echo "  - MCP server: cat /tmp/weather_mcp.log"
echo "  - Dora logs: dora logs mcp-test maas-client"
echo ""

# Cleanup
echo "🧹 Stopping test dataflow..."
dora stop --name mcp-test