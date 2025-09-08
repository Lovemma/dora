#!/usr/bin/env python3
"""
Test script for Alibaba Cloud models.
Can be run as a static node in a dataflow.
"""

import time
import os
from dora import Node, DoraStatus
import pyarrow as pa

# Configuration from environment variables or defaults
MODEL_TO_TEST = os.environ.get("TEST_MODEL", "qwen-turbo")
TEST_MODE = os.environ.get("TEST_MODE", "quick")  # quick, full, custom

# Available models
MODELS = {
    "qwen-turbo": "Qwen Turbo - Fast & cost-effective",
    "qwen-plus": "Qwen Plus - Enhanced performance", 
    "qwen-max": "Qwen Max - Most capable",
    "deepseek-chat": "DeepSeek Chat - General conversation",
    "deepseek-coder": "DeepSeek Coder - Code generation",
    "moonshot-v1-8k": "Moonshot 8K context",
    "moonshot-v1-32k": "Moonshot 32K context",
}

# Test questions
QUICK_QUESTIONS = [
    "What is artificial intelligence?",
    "Write a Python hello world function.",
    "请用中文解释什么是云计算。",
]

FULL_QUESTIONS = [
    "What is artificial intelligence and how does it work?",
    "Write a Python function to calculate fibonacci numbers recursively.",
    "Explain quantum computing in simple terms.",
    "请用中文介绍一下机器学习的主要应用。",
    "Compare cloud computing vs on-premise solutions.",
    "Write a haiku about artificial intelligence.",
    "What are the ethical considerations of AI in healthcare?",
    "Implement a binary search algorithm in Python.",
    "解释深度学习和传统机器学习的区别。",
    "What are best practices for prompt engineering?",
]

def main():
    node = Node('test-client')

    print("\n" + "=" * 80)
    print(f"🤖 Alibaba Cloud Model Test")
    print(f"   Model: {MODEL_TO_TEST} - {MODELS.get(MODEL_TO_TEST, 'Unknown model')}")
    print(f"   Mode: {TEST_MODE}")
    print("=" * 80)
    
    # Select questions based on mode
    if TEST_MODE == "quick":
        questions = QUICK_QUESTIONS
    elif TEST_MODE == "full":
        questions = FULL_QUESTIONS
    elif TEST_MODE == "custom":
        custom_q = os.environ.get("CUSTOM_QUESTIONS", "")
        questions = [q.strip() for q in custom_q.split("|") if q.strip()]
        if not questions:
            questions = ["What is AI?"]
    else:
        questions = QUICK_QUESTIONS
    
    print(f"\n📝 Testing {len(questions)} question(s)")
    print("-" * 80)
    
    question_index = 0
    response_parts = []
    waiting_for_response = False
    start_time = None
    
    # Send first question to kickstart
    if questions:
        question = questions[question_index]
        print(f"\n🔹 Question {question_index + 1}/{len(questions)}")
        print(f"   Model: {MODEL_TO_TEST}")
        print(f"   Q: {question[:80]}{'...' if len(question) > 80 else question[80:]}")
        print("-" * 60)
        
        metadata = {
            "model": MODEL_TO_TEST,
            "question_id": str(question_index + 1),
            "timestamp": str(time.time())
        }
        
        node.send_output("text", pa.array([question]), metadata)
        print("   ⏳ Waiting for response...")
        waiting_for_response = True
        start_time = time.time()
        response_parts = []
    
    # Main event loop
    for event in node:
        event_type = event.get("type")
        
        if event_type == "stop":
            print("\n🛑 Stop signal received")
            break
        
        if event_type == "INPUT":
            event_id = event.get("id")
            
            # Collect text responses
            if event_id == "text":
                data = event.get("value")
                if data and waiting_for_response:
                    try:
                        text = data.to_pylist()[0] if hasattr(data, "to_pylist") else str(data)
                        response_parts.append(text)
                    except:
                        pass
            
            # Handle status updates
            elif event_id == "status":
                data = event.get("value")
                if data:
                    try:
                        status = data.to_pylist()[0] if hasattr(data, "to_pylist") else str(data)
                        
                        if status == "processing":
                            if waiting_for_response and start_time:
                                elapsed = time.time() - start_time
                                print(f"   📡 Processing... ({elapsed:.1f}s)", end="\r", flush=True)
                        
                        elif status == "complete":
                            if waiting_for_response:
                                # Response is complete
                                elapsed = time.time() - start_time if start_time else 0
                                print(f"   📡 Processing... Done! ({elapsed:.1f}s)")
                                
                                # Display response
                                if response_parts:
                                    full_response = ''.join(response_parts)
                                    print(f"   📝 Response ({len(full_response)} chars):")
                                    print("-" * 60)
                                    # Print first 500 chars of response
                                    if len(full_response) > 500:
                                        print(full_response[:500] + "...")
                                    else:
                                        print(full_response)
                                    print("-" * 60)
                                    print(f"   ✅ Response complete")
                                else:
                                    print("   ⚠️ Empty response received")
                                
                                # Move to next question
                                question_index += 1
                                waiting_for_response = False
                                response_parts = []
                                
                                # Send next question if available
                                if question_index < len(questions):
                                    print(f"\n   ⏰ Next question in 2 seconds...")
                                    time.sleep(2)
                                    
                                    question = questions[question_index]
                                    print(f"\n🔹 Question {question_index + 1}/{len(questions)}")
                                    print(f"   Model: {MODEL_TO_TEST}")
                                    print(f"   Q: {question[:80]}{'...' if len(question) > 80 else question[80:]}")
                                    print("-" * 60)
                                    
                                    metadata = {
                                        "model": MODEL_TO_TEST,
                                        "question_id": str(question_index + 1),
                                        "timestamp": str(time.time())
                                    }
                                    
                                    node.send_output("text", pa.array([question]), metadata)
                                    print("   ⏳ Waiting for response...")
                                    waiting_for_response = True
                                    start_time = time.time()
                                    response_parts = []
                                else:
                                    # All questions completed
                                    print("\n" + "=" * 80)
                                    print(f"✨ Test complete for {MODEL_TO_TEST}!")
                                    print(f"   Processed {question_index}/{len(questions)} questions")
                                    print("=" * 80)
                                    time.sleep(1)
                                    return DoraStatus.STOP
                        
                        elif status.startswith("error:"):
                            if waiting_for_response:
                                print(f"\n   ❌ {status}")
                                
                                # Move to next question even on error
                                question_index += 1
                                waiting_for_response = False
                                response_parts = []
                                
                                if question_index < len(questions):
                                    print(f"\n   ⏰ Trying next question in 3 seconds...")
                                    time.sleep(3)
                                    
                                    question = questions[question_index]
                                    print(f"\n🔹 Question {question_index + 1}/{len(questions)}")
                                    print(f"   Model: {MODEL_TO_TEST}")
                                    print(f"   Q: {question[:80]}{'...' if len(question) > 80 else question[80:]}")
                                    print("-" * 60)
                                    
                                    metadata = {
                                        "model": MODEL_TO_TEST,
                                        "question_id": str(question_index + 1),
                                        "timestamp": str(time.time())
                                    }
                                    
                                    node.send_output("text", pa.array([question]), metadata)
                                    print("   ⏳ Waiting for response...")
                                    waiting_for_response = True
                                    start_time = time.time()
                                    response_parts = []
                                else:
                                    print("\n" + "=" * 80)
                                    print(f"✨ Test complete for {MODEL_TO_TEST}!")
                                    print(f"   Processed {question_index}/{len(questions)} questions")
                                    print("=" * 80)
                                    return DoraStatus.STOP
                    except Exception as e:
                        print(f"   ⚠️ Error parsing status: {e}")
    
    return DoraStatus.STOP

if __name__ == "__main__":
    main()