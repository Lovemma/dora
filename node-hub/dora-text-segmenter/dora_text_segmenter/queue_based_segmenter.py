#!/usr/bin/env python3
"""
Queue-based Text Segmenter
1. No deadlock - first segment sent immediately
2. Don't judge if segments are complete - just queue them
3. Send one at a time, triggered by TTS completion
4. Skip segments with only punctuation or numbers
"""

import os
import time
import re
import pyarrow as pa
from dora import Node
from collections import deque

def should_skip_segment(text, punctuation_marks="。！？.!?"):
    """Check if segment should be skipped (only punctuation or numbers)

    Args:
        text: Text segment to check
        punctuation_marks: String of punctuation marks to consider (configurable via env var)
    """
    # Remove whitespace for checking
    text_stripped = text.strip()

    # Skip if empty
    if not text_stripped:
        return True

    # Build pattern dynamically from configured punctuation marks
    # Escape special regex characters in punctuation marks
    escaped_punctuation = re.escape(punctuation_marks)

    # Pattern: only whitespace + numbers + configured punctuation marks
    # This allows filtering based on user-configured punctuation
    skip_pattern = f'^[\\s\\d{escaped_punctuation}]+$'

    if re.match(skip_pattern, text_stripped):
        return True

    return False

def main():
    node = Node("text-segmenter")

    # Configuration from environment
    punctuation_marks = os.getenv("PUNCTUATION_MARKS", "。！？.!?")
    print(f"[Segmenter] Configured punctuation marks for filtering: '{punctuation_marks}'")

    # Simple queue for segments
    segment_queue = deque()
    is_sending = False

    # Segment counter
    segment_counter = 0  # Number of segments in queue

    # Track current question_id for smart reset
    current_question_id = None

    print("[Segmenter] Started")
    
    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "text":
                # Received text from LLM
                text = event["value"][0].as_py()
                metadata = event.get("metadata", {})

                # Extract question_id from metadata (passed from ASR via LLM)
                question_id = metadata.get("question_id", None)

                # Update current question_id
                if question_id is not None:
                    current_question_id = question_id

                # ALWAYS queue incoming text - don't filter here
                # Filtering only happens when reset event is received
                # Check if we should skip this segment
                if not should_skip_segment(text, punctuation_marks):
                    # Valid segment - add to queue with question_id
                    segment_queue.append({
                        "text": text,
                        "metadata": metadata,
                        "question_id": question_id,
                    })

                    # Increase counter by 1 (in reality, segmenter might split text further)
                    # For now, we're treating each incoming text as one segment
                    segment_counter += 1
                
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
                            **segment["metadata"]
                        }
                    )

                    is_sending = True
                    
            elif event["id"] == "tts_complete":
                # TTS completed a segment
                
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
                            **segment["metadata"]
                        }
                    )
                else:
                    # No more segments to send
                    is_sending = False
                    
            elif event["id"] == "control":
                # Reset command
                command = event["value"][0].as_py()
                if command == "reset":
                    print(f"[Segmenter] RESET: Cleared {len(segment_queue)} queued segments via control command")
                    segment_queue.clear()
                    is_sending = False
                    segment_counter = 0

            elif event["id"] == "reset":
                # Reset signal - clear only segments from OLD questions (different question_id)
                metadata = event.get("metadata", {})
                incoming_question_id = metadata.get("question_id", None)

                if incoming_question_id is None:
                    # No question_id in reset signal - clear all (backward compatibility)
                    cleared_count = len(segment_queue)
                    segment_queue.clear()
                    is_sending = False
                    segment_counter = 0
                    print(f"[Segmenter] RESET: Cleared {cleared_count} queued segments (no question_id)")
                else:
                    # Smart reset - only clear segments from different question_id
                    original_count = len(segment_queue)
                    new_queue = deque()
                    cleared_count = 0

                    for segment in segment_queue:
                        seg_question_id = segment.get("question_id", None)
                        if seg_question_id != incoming_question_id:
                            # This segment is from a different (old) question - discard it
                            cleared_count += 1
                        else:
                            # Keep segments with same question_id (new question)
                            new_queue.append(segment)

                    segment_queue = new_queue
                    segment_counter = len(segment_queue)

                    # Update current_question_id to the new question
                    current_question_id = incoming_question_id

                    # Reset is_sending if queue is empty
                    if len(segment_queue) == 0:
                        is_sending = False

                    print(f"[Segmenter] SMART RESET: Cleared {cleared_count}/{original_count} old segments, kept {len(segment_queue)} from new question_id={incoming_question_id}")

        elif event["type"] == "STOP":
            break

if __name__ == "__main__":
    main()