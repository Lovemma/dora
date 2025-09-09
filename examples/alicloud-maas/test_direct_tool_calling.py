#!/usr/bin/env python3
"""
Direct test of Alibaba Cloud tool calling with OpenAI SDK.
This proves that Alibaba Cloud supports OpenAI-style tool calling.
"""

import os
import json
from openai import OpenAI

def test_direct():
    """Test tool calling directly with OpenAI SDK."""
    print("\n" + "="*60)
    print("🔧 Direct Alibaba Cloud Tool Calling Test")
    print("="*60)
    
    # Initialize client
    client = OpenAI(
        api_key=os.environ.get("ALIBABA_CLOUD_API_KEY", "sk-269457821d0743c9bcc700d67f8564eb"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    # Define a simple tool
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city name",
                    }
                },
                "required": ["location"],
            },
        }
    }]
    
    # Send request
    messages = [
        {"role": "user", "content": "What's the weather in Beijing?"}
    ]
    
    print("\n📤 Sending request to qwen-max with tool definition...")
    
    response = client.chat.completions.create(
        model="qwen-max",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    
    # Check for tool calls
    message = response.choices[0].message
    
    if message.tool_calls:
        print("\n✅ SUCCESS! Tool call detected:")
        for tool_call in message.tool_calls:
            print(f"  - Function: {tool_call.function.name}")
            print(f"  - Arguments: {tool_call.function.arguments}")
            
            # Parse arguments
            args = json.loads(tool_call.function.arguments)
            print(f"  - Parsed: location='{args.get('location')}'")
        
        print("\n✅ Alibaba Cloud DOES support OpenAI tool calling!")
        print("The MaaS client should work with this.")
    else:
        print("\n❌ No tool calls made")
        print(f"Response: {message.content}")

if __name__ == "__main__":
    test_direct()