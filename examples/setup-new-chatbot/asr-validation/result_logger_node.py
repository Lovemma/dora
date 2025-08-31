#!/usr/bin/env python3
"""
Result logger node for Dora dataflow
Receives and displays ASR transcription results
"""

import time
import json
from dora import Node

def main():
    """Main function for result logger node"""
    
    # Initialize Dora node
    node = Node()
    
    print("Result logger node started, waiting for transcriptions...")
    print("="*60)
    
    # Process events
    for event in node:
        if event["type"] == "INPUT" and event["id"] == "text":
            # Get transcription text
            text = event["value"][0].as_py()
            
            # Display result
            print("\n📝 TRANSCRIPTION RECEIVED")
            print("-"*60)
            print(f"Text: {text}")
            print(f"Length: {len(text)} characters")
            print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check for expected content
            if "你好吗" in text and "北京动物园" in text:
                print("✅ Quality check: PASSED (contains expected phrases)")
            else:
                print("⚠️ Quality check: Please verify manually")
            
            print("="*60)
            
            # Log to file as well
            with open("transcription_log.txt", "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {text}\n")
            
            print("Result logged to transcription_log.txt")

if __name__ == "__main__":
    main()