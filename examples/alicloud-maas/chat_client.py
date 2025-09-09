#!/usr/bin/env python3
"""
Interactive chat client for testing MCP tool integration.
Shows when tools are being called and displays responses.
"""

import sys
import time
import threading
from dora import Node
import pyarrow as pa

class ChatClient:
    def __init__(self):
        self.node = Node("chat-client")
        self.waiting_response = False
        self.last_status = None
        
    def status_monitor(self):
        """Monitor status changes in background."""
        while True:
            try:
                event = self.node.next(timeout=0.1)
                if event and event["type"] == "INPUT":
                    if event["id"] == "status":
                        status = event["value"][0].as_py()
                        if status != self.last_status:
                            self.last_status = status
                            
                            # Show status updates
                            if status == "processing":
                                print("🔄 Processing request...", end="", flush=True)
                            elif status == "tool_calling":
                                print("\n🔧 Calling MCP tool...", end="", flush=True)
                            elif status == "complete":
                                if self.waiting_response:
                                    print(" ✅", flush=True)
                            elif status == "error":
                                print("\n❌ Error occurred", flush=True)
                                
                    elif event["id"] == "text":
                        response = event["value"][0].as_py()
                        print("\n📥 Assistant:", response)
                        self.waiting_response = False
                        
                    elif event["id"] == "log":
                        log_msg = event["value"][0].as_py()
                        # Check for MCP tool-related logs
                        if "tool" in log_msg.lower() or "mcp" in log_msg.lower():
                            print(f"\n   [DEBUG] {log_msg}", flush=True)
                            
            except Exception:
                pass
                
    def run(self):
        """Main chat loop."""
        print("\n" + "="*60)
        print("💬 MCP-Enabled Chat Client")
        print("="*60)
        print("Connected to MaaS client with MCP tools:")
        print("  • get_weather - Get weather for Chinese cities")
        print("  • list_cities - List available cities")
        print("\nType 'quit' to exit, 'help' for examples")
        print("-"*60)
        
        # Start status monitor in background
        monitor_thread = threading.Thread(target=self.status_monitor, daemon=True)
        monitor_thread.start()
        
        while True:
            try:
                # Get user input
                user_input = input("\n📤 You: ").strip()
                
                if user_input.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                    
                elif user_input.lower() == 'help':
                    print("\n📚 Example queries:")
                    print("  • What's the weather in Beijing?")
                    print("  • Tell me about Shanghai's weather")
                    print("  • List all cities with weather data")
                    print("  • Is it raining in Guangzhou?")
                    continue
                    
                elif not user_input:
                    continue
                
                # Send query to MaaS client
                self.waiting_response = True
                self.last_status = None
                
                self.node.send_output(
                    "text",
                    pa.array([user_input]),
                    {}
                )
                
                # Wait for response with timeout
                start_time = time.time()
                while self.waiting_response and (time.time() - start_time < 30):
                    time.sleep(0.1)
                    
                if self.waiting_response:
                    print("\n⏱️ Request timed out")
                    self.waiting_response = False
                    
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

def main():
    client = ChatClient()
    client.run()

if __name__ == "__main__":
    main()