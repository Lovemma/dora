#!/usr/bin/env python3
"""
Queue-based Text Segmenter
1. No deadlock - first segment sent immediately
2. Don't judge if segments are complete - just queue them
3. Send one at a time, triggered by TTS completion
4. Skip segments with only punctuation or numbers
"""

import time
import re
import uuid
import pyarrow as pa
from dora import Node
from collections import deque

def should_skip_segment(text):
    """Check if segment should be skipped (only punctuation or numbers)"""
    # Remove whitespace for checking
    text_stripped = text.strip()
    
    # Skip if empty
    if not text_stripped:
        return True
    
    # Pattern: only punctuation, numbers, whitespace, or common symbols
    # Includes Chinese and English punctuation
    skip_pattern = r'^[\s\d\.\,\!\?\;\:\-\—\~\@\#\$\%\^\&\*\(\)\[\]\{\}\_\+\=\|\\\/\<\>\"\'\`。，！？；：、""''（）【】《》「」『』〈〉〔〕……——～·]+$'
    
    if re.match(skip_pattern, text_stripped):
        print(f"[Segmenter] Skipping punctuation/number only segment: '{text_stripped}'")
        return True
    
    return False

def main():
    node = Node("text-segmenter")
    
    # Simple queue for segments
    segment_queue = deque()
    is_sending = False
    
    # Segment counter and conversation tracking
    segment_counter = 0  # Number of segments in queue
    conversation_id = None  # Reset when counter reaches zero
    
    print("[Segmenter] Started - Queue-based segmenter with segment counting")
    print("[Segmenter] Will send first segment immediately, then wait for TTS completion")
    print("[Segmenter] Will skip segments with only punctuation or numbers")
    
    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "text":
                # Received text from LLM
                text = event["value"][0].as_py()
                metadata = event.get("metadata", {})
                
                print(f"[Segmenter] Received text chunk: {len(text)} chars")
                
                # If counter is 0, start new conversation
                if segment_counter == 0:
                    conversation_id = str(uuid.uuid4())[:8]
                    print(f"[Segmenter] 🆕 New conversation: {conversation_id}")
                
                # Check if we should skip this segment
                if not should_skip_segment(text):
                    # Valid segment - add to queue
                    segment_queue.append({
                        "text": text,
                        "metadata": metadata,
                    })
                    
                    # Increase counter by 1 (in reality, segmenter might split text further)
                    # For now, we're treating each incoming text as one segment
                    segment_counter += 1
                    print(f"[Segmenter] Queued segment, counter: {segment_counter}")
                
                # Try to send a segment if not currently sending
                # This happens whether we queued the current segment or skipped it
                # Ensures no deadlock even if first segments are all punctuation
                if not is_sending and segment_queue:
                    segment = segment_queue.popleft()
                    
                    # Decrease counter BEFORE sending
                    segment_counter -= 1
                    
                    # Send segment to TTS with metadata
                    node.send_output(
                        "text_segment",
                        pa.array([segment["text"]]),
                        metadata={
                            "segments_remaining": segment_counter,  # After decrease
                            "conversation_id": conversation_id,
                            **segment["metadata"]
                        }
                    )
                    
                    print(f"[Segmenter] → Sent segment: '{segment['text'][:30]}...' ({len(segment['text'])} chars)")
                    print(f"[Segmenter]   Segments remaining: {segment_counter}")
                    is_sending = True
                    
                    # Reset conversation if counter reaches zero
                    if segment_counter == 0:
                        print(f"[Segmenter] ✅ Conversation {conversation_id} complete")
                        conversation_id = None
                    
            elif event["id"] == "tts_complete":
                # TTS completed a segment
                print(f"[Segmenter] TTS completed, queue size: {len(segment_queue)}")
                
                # Send next segment if available
                if segment_queue:
                    segment = segment_queue.popleft()
                    
                    # Decrease counter BEFORE sending
                    segment_counter -= 1
                    
                    node.send_output(
                        "text_segment",
                        pa.array([segment["text"]]),
                        metadata={
                            "segments_remaining": segment_counter,  # After decrease
                            "conversation_id": conversation_id,
                            **segment["metadata"]
                        }
                    )
                    
                    print(f"[Segmenter] → Sent segment: '{segment['text'][:30]}...' ({len(segment['text'])} chars)")
                    print(f"[Segmenter]   Segments remaining: {segment_counter}")
                    
                    # Reset conversation if counter reaches zero
                    if segment_counter == 0:
                        print(f"[Segmenter] ✅ Conversation {conversation_id} complete")
                        conversation_id = None
                else:
                    # No more segments to send
                    print("[Segmenter] No more segments in queue")
                    is_sending = False
                    
            elif event["id"] == "control":
                # Reset command
                command = event["value"][0].as_py()
                if command == "reset":
                    print(f"[Segmenter] RESET - clearing {len(segment_queue)} queued segments")
                    segment_queue.clear()
                    is_sending = False
                    segment_counter = 0
                    conversation_id = None
                    
        elif event["type"] == "STOP":
            break
    
    print("[Segmenter] Stopped")

if __name__ == "__main__":
    main()