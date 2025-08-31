#!/usr/bin/env python3
"""
Static text sender node that waits before sending text.
"""

import time
import pyarrow as pa
from dora import Node

def main():
    """Static node that sends text after a delay."""
    
    print("=" * 80)
    print("Static Text Sender - Waiting then sending text")
    print("=" * 80)
    
    node = Node()
    
    # Complete Chinese text
    chinese_text = """我们说中国式现代化是百年大战略，这又分为三个阶段。第一个阶段，我们先用30年时间建成了独立完整的工业体系和国民经济体系；再用40年，到2021年，全面建成了小康社会。我们现在正处于第三个阶段，这又被分成上下两篇：上半篇是到2035年基本实现社会主义现代化；下半篇是到本世纪中叶，也就是2050年，建成社会主义现代化强国。"""
    
    print(f"\nText to send ({len(chinese_text)} characters)")
    print("-" * 60)
    
    # Wait for system to be ready
    print("Waiting 5 seconds for all nodes to initialize...")
    time.sleep(5)
    
    # Send the text
    start_time = time.time()
    print(f"\nSending text at {time.strftime('%H:%M:%S')}...")
    
    node.send_output(
        "text_output",
        pa.array([chinese_text]),
        metadata={
            "session_id": "timing_test",
            "char_count": len(chinese_text),
            "start_time": start_time
        }
    )
    
    print(f"✓ Text sent to text-segmenter")
    
    # Keep running to observe results
    print("\nWaiting for TTS processing...")
    
    # Wait for events or timeout
    timeout = 120  # 2 minutes
    start = time.time()
    
    for event in node:
        if event["type"] == "STOP":
            break
        if time.time() - start > timeout:
            print("Timeout reached, exiting")
            break
    
    print("\n" + "=" * 80)
    print("Text sender completed")
    print("=" * 80)


if __name__ == "__main__":
    main()