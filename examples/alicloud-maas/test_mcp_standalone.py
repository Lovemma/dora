#!/usr/bin/env python3
"""
Standalone test for MCP integration with Alibaba Cloud.
Tests if qwen-max can properly use MCP tools.
"""

import os
import sys
import json
import requests
import time

def test_mcp_with_qwen_max():
    """Test MCP tool calling with qwen-max via direct API call."""
    
    api_key = os.environ.get("ALIBABA_CLOUD_API_KEY")
    if not api_key:
        print("❌ Error: ALIBABA_CLOUD_API_KEY not set!")
        return False
    
    endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    print("\n" + "="*60)
    print("🧪 Testing MCP Tool Calling with qwen-max")
    print("="*60)
    
    # Test 1: Ask about weather (should trigger tool call)
    print("\n📝 Test 1: Weather Query")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Define the weather tool
    weather_tool = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g., 'beijing', 'shanghai')"
                    }
                },
                "required": ["city"]
            }
        }
    }
    
    # Test message asking about weather
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant with access to weather information. Use the get_weather tool when asked about weather."
        },
        {
            "role": "user",
            "content": "What's the weather like in Beijing today?"
        }
    ]
    
    payload = {
        "model": "qwen-max",
        "messages": messages,
        "tools": [weather_tool],
        "tool_choice": "auto",
        "temperature": 0.7
    }
    
    print("🔧 Sending request with weather tool definition...")
    
    try:
        response = requests.post(
            f"{endpoint}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        print("\n📥 Response received:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Check if model tried to use the tool
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            
            # Check for tool calls
            if "message" in choice and "tool_calls" in choice["message"]:
                tool_calls = choice["message"]["tool_calls"]
                print(f"\n✅ Tool calls detected: {len(tool_calls)} call(s)")
                
                for tool_call in tool_calls:
                    print(f"\n🔧 Tool Call:")
                    print(f"  - Name: {tool_call.get('function', {}).get('name')}")
                    print(f"  - Arguments: {tool_call.get('function', {}).get('arguments')}")
                    
                    # Simulate tool execution
                    if tool_call.get('function', {}).get('name') == 'get_weather':
                        args = json.loads(tool_call.get('function', {}).get('arguments', '{}'))
                        city = args.get('city', 'unknown')
                        
                        print(f"\n📍 Simulating weather lookup for: {city}")
                        
                        # Mock weather response
                        weather_result = {
                            "city": city,
                            "temperature": 15,
                            "condition": "Partly Cloudy",
                            "humidity": 45,
                            "description": f"{city.title()} weather: 15°C, partly cloudy"
                        }
                        
                        # Send follow-up with tool result
                        print("\n📤 Sending tool result back to model...")
                        
                        messages.append(choice["message"])
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.get("id"),
                            "content": json.dumps(weather_result)
                        })
                        
                        # Get final response
                        payload["messages"] = messages
                        
                        response2 = requests.post(
                            f"{endpoint}/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=30
                        )
                        
                        if response2.status_code == 200:
                            result2 = response2.json()
                            final_message = result2["choices"][0]["message"]["content"]
                            print(f"\n💬 Final Response: {final_message}")
                            return True
                        else:
                            print(f"\n❌ Error getting final response: {response2.status_code}")
                            return False
                
                return True
            else:
                # Check if model mentioned it would use tools
                content = choice.get("message", {}).get("content", "")
                print(f"\n💬 Response: {content}")
                
                if "tool" in content.lower() or "function" in content.lower():
                    print("\n⚠️ Model mentioned tools but didn't call them")
                else:
                    print("\n❌ No tool calls detected in response")
                return False
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_listing():
    """Test if qwen-max can list available tools."""
    
    api_key = os.environ.get("ALIBABA_CLOUD_API_KEY")
    if not api_key:
        return False
    
    endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    print("\n" + "="*60)
    print("📋 Test 2: Tool Listing")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Define multiple tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a city"
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "list_cities",
                "description": "List all cities with available weather data"
            }
        }
    ]
    
    messages = [
        {
            "role": "user",
            "content": "What tools do you have available? List them."
        }
    ]
    
    payload = {
        "model": "qwen-max",
        "messages": messages,
        "tools": tools,
        "temperature": 0.7
    }
    
    print("🔧 Asking model to list available tools...")
    
    try:
        response = requests.post(
            f"{endpoint}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"\n💬 Response: {content}")
            
            if "get_weather" in content.lower() or "list_cities" in content.lower():
                print("\n✅ Model correctly identified available tools!")
                return True
            else:
                print("\n⚠️ Model didn't mention specific tools")
                return False
        else:
            print(f"\n❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def main():
    """Main test runner."""
    print("\n" + "="*80)
    print("🧪 Alibaba Cloud qwen-max MCP Tool Calling Test")
    print("="*80)
    
    # Check API key
    if not os.environ.get("ALIBABA_CLOUD_API_KEY"):
        print("\n❌ Error: ALIBABA_CLOUD_API_KEY not set!")
        print("Set it with: export ALIBABA_CLOUD_API_KEY='sk-your-key'")
        return 1
    
    tests_passed = 0
    tests_total = 2
    
    # Test 1: Tool calling
    if test_mcp_with_qwen_max():
        tests_passed += 1
        print("\n✅ Test 1 PASSED: Tool calling works!")
    else:
        print("\n❌ Test 1 FAILED: Tool calling not working")
    
    # Test 2: Tool listing
    if test_tool_listing():
        tests_passed += 1
        print("\n✅ Test 2 PASSED: Tool listing works!")
    else:
        print("\n❌ Test 2 FAILED: Tool listing not working")
    
    # Summary
    print("\n" + "="*80)
    print(f"📊 Results: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("✅ SUCCESS: qwen-max supports tool calling (MCP compatible)!")
        return 0
    else:
        print(f"❌ FAILURE: {tests_total - tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())