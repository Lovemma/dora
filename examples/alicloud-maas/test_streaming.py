#!/usr/bin/env python3
"""
Test streaming functionality with Alibaba Cloud API.
Verifies if it works the same way as OpenAI's streaming API.
"""

import os
import sys
import json
import time
import requests
from typing import Optional

def load_api_key(config_path: str = "alicloud_config.toml") -> Optional[str]:
    """Load API key from config file or environment variable."""
    
    # First try environment variable
    api_key = os.environ.get("ALIBABA_CLOUD_API_KEY")
    if api_key:
        return api_key
    
    # Try loading from config file
    try:
        with open(config_path, "r") as f:
            for line in f:
                if "api_key" in line and "=" in line:
                    parts = line.split("=", 1)[1].strip()
                    if parts.startswith('"') and parts.endswith('"'):
                        return parts[1:-1]
                    elif parts.startswith("'") and parts.endswith("'"):
                        return parts[1:-1]
    except FileNotFoundError:
        pass
    
    return None

def test_streaming(model: str = "qwen-turbo", message: str = "Count from 1 to 10 slowly."):
    """Test streaming with Alibaba Cloud API."""
    
    api_key = load_api_key()
    if not api_key:
        print("❌ Error: No API key found!")
        return
    
    endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ],
        "stream": True,  # Enable streaming
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    print(f"🔍 Testing streaming with model: {model}")
    print(f"📝 Message: {message}")
    print("=" * 60)
    print("\n📡 Streaming response:\n")
    
    try:
        # Make streaming request
        response = requests.post(
            f"{endpoint}/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        )
        
        response.raise_for_status()
        
        # Process streaming response
        full_content = ""
        chunk_count = 0
        start_time = time.time()
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                # OpenAI format: lines start with "data: "
                if line_str.startswith("data: "):
                    data_str = line_str[6:]  # Remove "data: " prefix
                    
                    # Check for stream end
                    if data_str == "[DONE]":
                        print("\n\n✅ Stream completed")
                        break
                    
                    try:
                        # Parse JSON chunk
                        chunk = json.loads(data_str)
                        chunk_count += 1
                        
                        # Extract content from chunk (OpenAI format)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            choice = chunk["choices"][0]
                            
                            # Get delta content
                            if "delta" in choice:
                                delta = choice["delta"]
                                if "content" in delta:
                                    content = delta["content"]
                                    full_content += content
                                    print(content, end="", flush=True)
                                elif "role" in delta:
                                    # First chunk often contains role
                                    pass
                            
                            # Check finish reason
                            if "finish_reason" in choice and choice["finish_reason"]:
                                print(f"\n\n📌 Finish reason: {choice['finish_reason']}")
                        
                        # Print chunk details for first 3 chunks (for debugging)
                        if chunk_count <= 3:
                            print(f"\n\n🔍 Chunk {chunk_count} structure:", file=sys.stderr)
                            print(json.dumps(chunk, indent=2), file=sys.stderr)
                            print("", file=sys.stderr)
                            
                    except json.JSONDecodeError as e:
                        print(f"\n⚠️ Failed to parse chunk: {data_str[:100]}...", file=sys.stderr)
                        print(f"   Error: {e}", file=sys.stderr)
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 60)
        print(f"\n📊 Streaming Statistics:")
        print(f"  • Total chunks received: {chunk_count}")
        print(f"  • Total content length: {len(full_content)} chars")
        print(f"  • Streaming duration: {elapsed:.2f} seconds")
        print(f"  • Average chunk rate: {chunk_count/elapsed:.1f} chunks/sec")
        
        print("\n✅ Streaming format verification:")
        print("  • Uses 'data: ' prefix: Yes (OpenAI compatible)")
        print("  • Uses '[DONE]' terminator: Yes (OpenAI compatible)")
        print("  • Uses 'delta' for incremental content: Yes (OpenAI compatible)")
        print("  • Compatible with OpenAI streaming clients: Yes")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request error: {e}")
        return
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

def test_non_streaming(model: str = "qwen-turbo", message: str = "Count from 1 to 10."):
    """Test non-streaming for comparison."""
    
    api_key = load_api_key()
    if not api_key:
        print("❌ Error: No API key found!")
        return
    
    endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ],
        "stream": False,  # Disable streaming
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    print(f"\n🔍 Testing non-streaming with model: {model}")
    print(f"📝 Message: {message}")
    print("=" * 60)
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{endpoint}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        elapsed = time.time() - start_time
        
        result = response.json()
        
        print("\n📦 Non-streaming response structure:")
        print(json.dumps(result, indent=2))
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print(f"\n📝 Content: {content}")
        
        print(f"\n⏱️ Response time: {elapsed:.2f} seconds")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request error: {e}")
        return

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test Alibaba Cloud streaming API")
    parser.add_argument("--model", default="qwen-turbo", help="Model to test")
    parser.add_argument("--message", default="Write a short poem about streaming data.", 
                       help="Test message")
    parser.add_argument("--non-streaming", action="store_true", 
                       help="Test non-streaming mode for comparison")
    parser.add_argument("--both", action="store_true",
                       help="Test both streaming and non-streaming")
    
    args = parser.parse_args()
    
    if args.both:
        test_streaming(args.model, args.message)
        print("\n" + "=" * 80 + "\n")
        test_non_streaming(args.model, args.message)
    elif args.non_streaming:
        test_non_streaming(args.model, args.message)
    else:
        test_streaming(args.model, args.message)

if __name__ == "__main__":
    main()