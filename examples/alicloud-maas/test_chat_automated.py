#!/usr/bin/env python3
"""
Automated chat test that sends predefined queries with progress indicators.
"""

import time
import sys
from dora import Node
import pyarrow as pa

def print_progress(message, end='\n'):
    """Print with immediate flush for real-time updates."""
    print(message, end=end, flush=True)

def main():
    print("\n" + "="*60)
    print("🤖 Automated Chat Test with MCP Tools")
    print("="*60)
    
    print_progress("\n⏳ Initializing node connection...", end='')
    try:
        node = Node("chat-client")
        print_progress(" ✅ Connected!")
    except Exception as e:
        print_progress(f" ❌ Failed: {e}")
        return
    
    # Test queries
    queries = [
        "What's the weather in Beijing?",
        "List all available cities",
        "Tell me about Shanghai weather"
    ]
    
    print_progress(f"\n📋 Will send {len(queries)} test queries")
    print("-" * 40)
    
    for i, query in enumerate(queries, 1):
        print_progress(f"\n[{i}/{len(queries)}] 📤 Sending: {query}")
        
        # Send query
        node.send_output("text", pa.array([query]), {})
        
        # Track response progress
        responses = []
        tool_called = False
        last_status = None
        dots = 0
        start_time = time.time()
        
        print_progress("    ⏳ Waiting for response", end='')
        
        while time.time() - start_time < 20:  # Extended timeout for tool calls
            event = node.next(timeout=0.5)
            
            if event and event["type"] == "INPUT":
                if event["id"] == "text":
                    response = event["value"][0].as_py()
                    responses.append(response)
                    
                    # Check if this is the final answer (after tool call) or initial response
                    if tool_called or (response.strip() and not "Error:" in response):
                        elapsed = time.time() - start_time
                        print_progress(f"\n    ✅ Final answer received in {elapsed:.1f}s:")
                        
                        # Display the complete final answer in a box
                        print_progress("\n    " + "─" * 50)
                        # Word wrap for better display
                        words = response.split()
                        line = "    "
                        for word in words:
                            if len(line) + len(word) > 54:
                                print_progress(line)
                                line = "    "
                            line += word + " "
                        if len(line) > 4:
                            print_progress(line)
                        print_progress("    " + "─" * 50)
                        
                        # Check for weather data
                        if tool_called:
                            print_progress("\n    🔍 MCP tool data included:")
                            if "15°c" in response.lower():
                                print_progress("       • Temperature: 15°C (from mock tool)")
                            if "partly cloudy" in response.lower():
                                print_progress("       • Condition: Partly cloudy")
                            if "45%" in response.lower():
                                print_progress("       • Humidity: 45%")
                        
                        break
                    
                elif event["id"] == "status":
                    status = event["value"][0].as_py()
                    if status != last_status:
                        last_status = status
                        
                        # Show status with icons
                        if status == "processing":
                            print_progress("\n    🔄 Processing request", end='')
                        elif status == "tool_calling":
                            print_progress("\n    🔧 Calling MCP weather tool", end='')
                            tool_called = True
                        elif status == "complete":
                            print_progress(" ✅", end='')
                        elif status == "error":
                            print_progress("\n    ❌ Error occurred")
            else:
                # Show progress dots while waiting
                dots = (dots + 1) % 4
                print_progress('\r    ⏳ Waiting for response' + '.' * dots + ' ' * (3-dots), end='')
        
        if not responses:
            elapsed = time.time() - start_time
            print_progress(f"\n    ⚠️ Timeout after {elapsed:.1f}s - no response received")
        
        # Progress bar between queries
        if i < len(queries):
            print_progress("\n    💤 Pausing 2s before next query...", end='')
            time.sleep(2)
            print_progress(" Ready!")
    
    print_progress("\n" + "="*60)
    print_progress("📊 Test Summary:")
    print_progress(f"   • Queries sent: {len(queries)}")
    print_progress("   • MCP tools: get_weather, list_cities")
    print_progress("   • Model: qwen-max (Alibaba Cloud)")
    print_progress("\n✅ Test complete!")

if __name__ == "__main__":
    main()