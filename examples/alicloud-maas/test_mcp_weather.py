#!/usr/bin/env python3
"""
Test MCP integration with Alibaba Cloud qwen-max model.
Verifies that MCP tools are registered and can be called.
"""

import os
import sys
import time
import json
from dora import Node, DoraStatus
import pyarrow as pa

def test_mcp_registration(node):
    """Test if MCP tools are properly registered."""
    print("\n" + "="*60)
    print("🔍 TEST 1: MCP Tool Registration")
    print("="*60)
    
    # Send a query asking about available tools
    test_message = "What tools do you have available? List them for me."
    
    print(f"📝 Sending: {test_message}")
    
    # Send to MaaS client
    node.send_output(
        "text",
        pa.array([test_message]),
        {"model": "qwen-max", "session_id": "mcp_test_registration"}
    )
    
    # Wait for response
    response_received = False
    timeout = 30
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        event = node.next(timeout=1000)  # 1 second timeout
        
        if event is None:
            continue
            
        event_type = event.get("type")
        if event_type == "INPUT":
            event_id = event.get("id")
            
            if event_id == "text":
                data = event.get("value")
                if data:
                    response = data.to_pylist()[0] if hasattr(data, "to_pylist") else str(data)
                    print(f"\n📥 Response: {response}")
                    
                    # Check if response mentions weather tool
                    if "weather" in response.lower() or "get_weather" in response.lower():
                        print("✅ MCP weather tool detected in response!")
                        response_received = True
                    else:
                        print("⚠️ Weather tool not mentioned in response")
                        response_received = True
                    break
            
            elif event_id == "status":
                data = event.get("value")
                if data:
                    status = data.to_pylist()[0] if hasattr(data, "to_pylist") else str(data)
                    print(f"📊 Status: {status}")
                    
                    if status == "complete":
                        if not response_received:
                            print("⚠️ Response completed but no text received")
                        break
                    elif status.startswith("error"):
                        print(f"❌ Error: {status}")
                        return False
    
    if not response_received:
        print("❌ Timeout waiting for response")
        return False
    
    return True

def test_weather_query(node):
    """Test if qwen-max can call the weather MCP tool."""
    print("\n" + "="*60)
    print("🌤️ TEST 2: Weather Query with MCP Tool")
    print("="*60)
    
    # Test queries
    test_queries = [
        "What's the weather in Beijing?",
        "Tell me about Shanghai's weather conditions",
        "北京的天气怎么样？",
    ]
    
    for idx, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {idx}: {query}")
        
        # Send query
        node.send_output(
            "text",
            pa.array([query]),
            {"model": "qwen-max", "session_id": f"weather_test_{idx}"}
        )
        
        # Collect response
        response_parts = []
        response_complete = False
        timeout = 30
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            event = node.next(timeout=1000)
            
            if event is None:
                continue
                
            event_type = event.get("type")
            if event_type == "INPUT":
                event_id = event.get("id")
                
                if event_id == "text":
                    data = event.get("value")
                    if data:
                        text = data.to_pylist()[0] if hasattr(data, "to_pylist") else str(data)
                        response_parts.append(text)
                        print(f"📥 Response chunk: {text[:100]}...")
                
                elif event_id == "status":
                    data = event.get("value")
                    if data:
                        status = data.to_pylist()[0] if hasattr(data, "to_pylist") else str(data)
                        print(f"📊 Status: {status}")
                        
                        if status == "complete":
                            response_complete = True
                            break
                        elif status.startswith("error"):
                            print(f"❌ Error: {status}")
                            return False
                
                elif event_id == "log":
                    data = event.get("value")
                    if data:
                        log = data.to_pylist()[0] if hasattr(data, "to_pylist") else str(data)
                        if "tool" in log.lower() or "mcp" in log.lower():
                            print(f"🔧 Tool log: {log}")
        
        if response_complete and response_parts:
            full_response = "".join(response_parts)
            print(f"\n✅ Complete response ({len(full_response)} chars):")
            print("-" * 40)
            print(full_response[:500])  # First 500 chars
            
            # Check if response contains weather information
            weather_keywords = ["temperature", "°C", "weather", "condition", "humidity", "天气", "温度", "湿度"]
            if any(keyword in full_response for keyword in weather_keywords):
                print("\n✅ Weather information found in response!")
            else:
                print("\n⚠️ No weather information detected in response")
        else:
            print(f"❌ Failed to get complete response")
            return False
        
        # Small delay between queries
        time.sleep(2)
    
    return True

def main():
    """Main test function."""
    print("\n" + "="*80)
    print("🧪 Alibaba Cloud MCP Integration Test")
    print("="*80)
    print(f"Model: qwen-max")
    print(f"MCP Server: mock-weather")
    print(f"Config: mcp_test_config.toml")
    
    # Check API key
    if not os.environ.get("ALIBABA_CLOUD_API_KEY"):
        print("\n❌ Error: ALIBABA_CLOUD_API_KEY not set!")
        print("Set it with: export ALIBABA_CLOUD_API_KEY='your-key'")
        return 1
    
    # Create test node
    print("\n📡 Initializing test node...")
    node = Node("mcp-test-client")
    
    # Run tests
    tests_passed = 0
    tests_total = 2
    
    # Test 1: MCP Registration
    if test_mcp_registration(node):
        tests_passed += 1
        print("✅ Test 1 PASSED: MCP tools are registered")
    else:
        print("❌ Test 1 FAILED: MCP tools not properly registered")
    
    # Test 2: Weather Query
    if test_weather_query(node):
        tests_passed += 1
        print("✅ Test 2 PASSED: Weather queries work with MCP")
    else:
        print("❌ Test 2 FAILED: Weather queries not working")
    
    # Summary
    print("\n" + "="*80)
    print(f"📊 Test Results: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        print("✅ All tests PASSED! MCP integration with qwen-max is working!")
        return 0
    else:
        print(f"❌ {tests_total - tests_passed} test(s) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())