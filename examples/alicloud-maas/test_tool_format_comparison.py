#!/usr/bin/env python3
"""
Test to compare tool calling formats between OpenAI and Anthropic MCP.
This will help verify which format Alibaba Cloud actually uses.
"""

import os
import json
import requests

def test_openai_format():
    """Test OpenAI's function calling format."""
    print("\n" + "="*60)
    print("🔧 OpenAI Function Calling Format")
    print("="*60)
    
    # OpenAI format for tool definition
    openai_tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        }
    }]
    
    print("\n📋 OpenAI Tool Definition:")
    print(json.dumps(openai_tools, indent=2))
    
    # Expected OpenAI response format
    openai_response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,  # Usually null when making tool calls
                "tool_calls": [{
                    "id": "call_abc123",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "Beijing", "unit": "celsius"}'  # JSON string
                    }
                }]
            }
        }]
    }
    
    print("\n📤 OpenAI Response Format (with tool call):")
    print(json.dumps(openai_response, indent=2))
    
    return openai_tools, openai_response

def test_anthropic_mcp_format():
    """Test Anthropic's MCP format."""
    print("\n" + "="*60)
    print("🔧 Anthropic MCP Format")
    print("="*60)
    
    # MCP format for tool definition
    mcp_tools = [{
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"]
                }
            },
            "required": ["location"]
        }
    }]
    
    print("\n📋 Anthropic/MCP Tool Definition:")
    print(json.dumps(mcp_tools, indent=2))
    
    # Expected Anthropic response format
    anthropic_response = {
        "content": [
            {
                "type": "text",
                "text": "I'll check the weather in Beijing for you."
            },
            {
                "type": "tool_use",
                "id": "toolu_01A09q90qw90lq917835lq9",
                "name": "get_weather",
                "input": {  # Direct object, not JSON string
                    "location": "Beijing",
                    "unit": "celsius"
                }
            }
        ]
    }
    
    print("\n📤 Anthropic Response Format (with tool use):")
    print(json.dumps(anthropic_response, indent=2))
    
    return mcp_tools, anthropic_response

def test_alibaba_cloud_format():
    """Test what format Alibaba Cloud actually uses."""
    print("\n" + "="*60)
    print("🔧 Testing Alibaba Cloud's Actual Format")
    print("="*60)
    
    api_key = os.environ.get("ALIBABA_CLOUD_API_KEY")
    if not api_key:
        print("❌ ALIBABA_CLOUD_API_KEY not set")
        return None
    
    endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # Test with OpenAI format
    print("\n📝 Testing with OpenAI-style tool definition...")
    
    openai_tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-max",
        "messages": [
            {"role": "user", "content": "What's the weather in Beijing?"}
        ],
        "tools": openai_tools,
        "tool_choice": "auto"
    }
    
    try:
        response = requests.post(
            f"{endpoint}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Alibaba Cloud Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Analyze the format
            if "choices" in result and result["choices"]:
                choice = result["choices"][0]
                message = choice.get("message", {})
                
                if "tool_calls" in message:
                    print("\n✅ Alibaba Cloud uses OpenAI format!")
                    print("   - Has 'tool_calls' field")
                    print("   - Tool calls structure matches OpenAI")
                    
                    # Check arguments format
                    tool_call = message["tool_calls"][0]
                    args = tool_call.get("function", {}).get("arguments")
                    if isinstance(args, str):
                        print("   - Arguments are JSON strings (OpenAI style)")
                    else:
                        print("   - Arguments are objects (different from OpenAI)")
                        
                elif "content" in message and isinstance(message["content"], list):
                    print("\n⚠️ Alibaba Cloud might use Anthropic format")
                    print("   - Content is a list of blocks")
                else:
                    print("\n❓ Format unclear from response")
                    
            return result
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

def compare_formats():
    """Compare the formats and provide analysis."""
    print("\n" + "="*80)
    print("📊 Format Comparison Analysis")
    print("="*80)
    
    print("""
Key Differences:

1. **Tool Definition Structure:**
   - OpenAI: Uses nested "function" object with "type": "function"
   - Anthropic: Direct tool object with "input_schema" instead of "parameters"

2. **Response Format:**
   - OpenAI: Separate "tool_calls" array in message
   - Anthropic: Mixed content blocks with "tool_use" type

3. **Arguments Format:**
   - OpenAI: Arguments as JSON string that needs parsing
   - Anthropic: Arguments as direct object/dict

4. **Content Handling:**
   - OpenAI: Content is usually null when making tool calls
   - Anthropic: Can have both text and tool_use in same response

5. **MCP Compatibility:**
   - MCP follows Anthropic's format more closely
   - OpenAI format requires conversion to work with MCP
   - Alibaba Cloud claims OpenAI compatibility
    """)

def main():
    """Run all format tests."""
    print("\n" + "="*80)
    print("🧪 Tool Calling Format Comparison Test")
    print("="*80)
    
    # Test formats
    openai_tools, openai_response = test_openai_format()
    mcp_tools, anthropic_response = test_anthropic_mcp_format()
    
    # Test Alibaba Cloud
    alibaba_result = test_alibaba_cloud_format()
    
    # Compare
    compare_formats()
    
    if alibaba_result:
        print("\n✅ Conclusion:")
        print("Alibaba Cloud uses OpenAI-compatible format, which means:")
        print("1. It's NOT directly compatible with Anthropic's MCP format")
        print("2. MCP tools need format conversion to work with Alibaba Cloud")
        print("3. The MaaS client needs to translate between formats")

if __name__ == "__main__":
    main()