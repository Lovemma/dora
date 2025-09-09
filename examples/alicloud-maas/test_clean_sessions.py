#!/usr/bin/env python3
"""
Test script that ensures clean sessions for each query.
Sends reset command between queries to avoid response mixing.
"""

import time
import sys
from dora import Node
import pyarrow as pa
import uuid

def print_progress(message, end='\n'):
    """Print with immediate flush for real-time updates."""
    print(message, end=end, flush=True)

def reset_session(node):
    """Send reset command to clear the session."""
    node.send_output(
        "control",
        pa.array(["reset"]),
        {}
    )
    time.sleep(0.5)  # Give time for reset to process

def process_query_with_clean_session(node, query, query_num):
    """Process a query with a clean session."""
    print_progress(f"\n{'='*60}")
    print_progress(f"Query #{query_num}: {query}")
    print_progress(f"{'='*60}")
    
    # Generate unique session ID for this query
    session_id = f"session_{query_num}_{uuid.uuid4().hex[:8]}"
    
    # Send query with session ID
    node.send_output(
        "text",
        pa.array([query]),
        {"session_id": session_id}
    )
    
    print_progress(f"\n📍 Session ID: {session_id}")
    print_progress("📍 Processing:")
    
    # Collect all responses for THIS query only
    segments = []
    tool_called = False
    complete_cycles = 0
    start_time = time.time()
    timeout = 20
    last_status = None
    
    while time.time() - start_time < timeout:
        event = node.next(timeout=0.5)
        
        if not event:
            continue
            
        if event["type"] == "INPUT":
            # Check if this event is for our session
            event_meta = event.get("metadata", {})
            event_session = event_meta.get("parameters", {}).get("session_id", "default")
            
            # Only process events for our session or default events
            if event_session != session_id and event_session != "default":
                continue
                
            event_id = event["id"]
            
            if event_id == "text":
                text = event["value"][0].as_py()
                if text and text.strip():
                    segments.append(text)
                    print_progress(f"   📝 Segment {len(segments)}: {len(text)} chars")
                    
            elif event_id == "status":
                status = event["value"][0].as_py()
                
                if status != last_status:
                    last_status = status
                    
                    if status == "processing":
                        print_progress(f"   🔄 Processing...")
                        
                    elif status == "tool_calling":
                        print_progress(f"   🔧 Calling MCP tool...")
                        tool_called = True
                        
                    elif status == "complete":
                        complete_cycles += 1
                        print_progress(f"   ✅ Complete (cycle {complete_cycles})")
                        
                        # If tool was called, wait for second complete (final answer)
                        if tool_called and complete_cycles >= 2:
                            print_progress("   📊 Final answer received after tool execution")
                            break
                        elif not tool_called and complete_cycles >= 1:
                            print_progress("   📊 Direct answer received")
                            break
                            
                    elif status.startswith("error"):
                        print_progress(f"   ❌ Error: {status}")
                        break
                        
            elif event_id == "log":
                log_msg = event["value"][0].as_py()
                if "Tool result:" in log_msg:
                    print_progress("   📊 Tool returned data")
                elif "Sending tool results back" in log_msg:
                    print_progress("   🔄 Getting final answer with tool data...")
    
    # Combine segments for this query only
    complete_response = " ".join(segments)
    elapsed = time.time() - start_time
    
    # Display the complete response
    if complete_response:
        print_progress(f"\n📝 COMPLETE RESPONSE ({len(segments)} segments, {elapsed:.1f}s):")
        print_progress("┌" + "─" * 58 + "┐")
        
        # Show the full response
        import textwrap
        wrapped = textwrap.wrap(complete_response, width=56)
        for line in wrapped:
            print_progress(f"│ {line:<56} │")
        
        print_progress("└" + "─" * 58 + "┘")
        
        # Check for weather data
        if tool_called:
            print_progress("\n🔍 MCP Tool Data Found:")
            response_lower = complete_response.lower()
            
            found_data = False
            if "beijing" in response_lower:
                if "15°c" in response_lower or "15 degrees" in response_lower:
                    print_progress("   • Beijing: 15°C (from mock tool)")
                    found_data = True
            if "shanghai" in response_lower:
                if "22°c" in response_lower or "22 degrees" in response_lower:
                    print_progress("   • Shanghai: 22°C (from mock tool)")
                    found_data = True
            if "partly cloudy" in response_lower:
                print_progress("   • Condition: Partly cloudy")
                found_data = True
            if "45%" in response_lower:
                print_progress("   • Humidity: 45%")
                found_data = True
                
            if not found_data:
                print_progress("   ⚠️  No specific weather data found")
    else:
        print_progress(f"\n⚠️  No response received after {elapsed:.1f}s")
    
    return complete_response, tool_called

def main():
    print("\n" + "="*60)
    print("🌦️  MCP Test - Clean Sessions")
    print("="*60)
    print("Each query uses a separate session to avoid mixing.")
    
    print_progress("\n⏳ Connecting...", end='')
    try:
        node = Node("chat-client")
        print_progress(" ✅ Connected!")
    except Exception as e:
        print_progress(f" ❌ Failed: {e}")
        print_progress("\nMake sure to run:")
        print_progress("  export ALIBABA_CLOUD_API_KEY='your-key'")
        print_progress("  dora start chat_mcp_dataflow.yml --name mcp-chat --detach")
        return
    
    # Test queries
    queries = [
        "What's the weather in Beijing?",
        "List all available cities",
        "Tell me about Shanghai's weather"
    ]
    
    print_progress(f"\n📋 Testing {len(queries)} queries with clean sessions...")
    
    results = []
    for i, query in enumerate(queries, 1):
        # Process query with its own session
        response, used_tool = process_query_with_clean_session(node, query, i)
        
        results.append({
            "query": query,
            "response": response,
            "used_tool": used_tool,
            "length": len(response) if response else 0
        })
        
        # Clear session before next query
        if i < len(queries):
            print_progress("\n🧹 Clearing session...")
            reset_session(node)
            print_progress("⏸️  Pausing 2 seconds...")
            time.sleep(2)
    
    # Summary
    print_progress("\n" + "="*60)
    print_progress("📊 FINAL SUMMARY")
    print_progress("="*60)
    
    for i, result in enumerate(results, 1):
        print_progress(f"\n{i}. Query: {result['query']}")
        print_progress(f"   Response length: {result['length']} chars")
        print_progress(f"   Tool used: {'✅ Yes' if result['used_tool'] else '❌ No'}")
        print_progress(f"   Success: {'✅' if result['response'] else '❌'}")
    
    successful = sum(1 for r in results if r["response"])
    print_progress(f"\n📈 Success rate: {successful}/{len(results)}")
    
    print_progress("\n✨ Test complete!")

if __name__ == "__main__":
    main()