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
import json
import pyarrow as pa
from dora import Node
from collections import deque


def send_log(node, level, message, config_level="INFO"):
    """Send log message through log output channel."""
    LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}

    if LOG_LEVELS.get(level, 0) < LOG_LEVELS.get(config_level, 20):
        return

    formatted_message = f"[{level}] {message}"
    log_data = {
        "node": "text-segmenter",
        "level": level,
        "message": formatted_message,
        "timestamp": time.time()
    }
    node.send_output("log", pa.array([json.dumps(log_data)]))

def should_skip_segment(text, punctuation_marks="。！？.!?", node=None, log_level="INFO"):
    """Check if segment should be skipped (only punctuation or numbers)

    Args:
        text: Text segment to check
        punctuation_marks: String of punctuation marks to consider (configurable via env var)
        node: Dora node for logging (optional)
        log_level: Log level for filtering
    """
    # Remove whitespace for checking
    text_stripped = text.strip()

    # Skip if empty
    if not text_stripped:
        if node:
            send_log(node, "DEBUG", f"Filter: SKIP empty: '{text}' (len={len(text)})", log_level)
        return True

    # Build pattern dynamically from configured punctuation marks
    # Escape special regex characters in punctuation marks
    escaped_punctuation = re.escape(punctuation_marks)

    # Pattern: only whitespace + numbers + configured punctuation marks
    # This allows filtering based on user-configured punctuation
    skip_pattern = f'^[\\s\\d{escaped_punctuation}]+$'

    matched = re.match(skip_pattern, text_stripped)
    if matched:
        if node:
            send_log(node, "DEBUG", f"Filter: SKIP punctuation: '{text}' (len={len(text)}, pattern matched)", log_level)
        return True

    if node:
        send_log(node, "DEBUG", f"Filter: KEEP: '{text}' (len={len(text)})", log_level)
    return False

def main():
    node = Node("text-segmenter")

    # Configuration from environment
    punctuation_marks = os.getenv("PUNCTUATION_MARKS", "。！？.!?，,、；：""''（）【】《》")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    send_log(node, "INFO", f"Configured punctuation marks for filtering: '{punctuation_marks}'", log_level)

    # Simple queue for segments
    segment_queue = deque()
    is_sending = False

    # Segment counter
    segment_counter = 0  # Number of segments in queue

    # Track current question_id for smart reset
    current_question_id = None

    send_log(node, "INFO", "Text Segmenter started", log_level)
    
    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "text":
                # Received text from LLM
                text = event["value"][0].as_py()
                metadata = event.get("metadata", {})

                send_log(node, "DEBUG", f"Received from LLM: '{text}' (len={len(text)})", log_level)

                # Extract question_id from metadata (passed from ASR via LLM)
                question_id = metadata.get("question_id", None)

                # Update current question_id
                if question_id is not None:
                    current_question_id = question_id

                # Check if we should skip this segment
                if not should_skip_segment(text, punctuation_marks, node, log_level):
                    # Valid segment - metadata already contains question_id
                    segment_queue.append({
                        "text": text,
                        "metadata": metadata,
                    })

                    # Increase counter by 1 (in reality, segmenter might split text further)
                    # For now, we're treating each incoming text as one segment
                    segment_counter += 1
                    send_log(node, "DEBUG", f"Queued segment (total in queue: {len(segment_queue)})", log_level)
                else:
                    send_log(node, "DEBUG", "Skipped segment based on filter", log_level)
                
                # Try to send a segment if not currently sending
                # This happens whether we queued the current segment or skipped it
                # Ensures no deadlock even if first segments are all punctuation
                if not is_sending and segment_queue:
                    segment = segment_queue.popleft()

                    # Decrease counter BEFORE sending
                    segment_counter -= 1

                    send_log(node, "INFO", f"Sending first to TTS: '{segment['text']}' (len={len(segment['text'])}, segments_remaining={segment_counter})", log_level)

                    # Send segment to TTS with metadata
                    node.send_output(
                        "text_segment",
                        pa.array([segment["text"]]),
                        metadata={
                            "segments_remaining": segment_counter,  # After decrease
                            **segment["metadata"]
                        }
                    )

                    send_log(node, "DEBUG", "First segment sent, setting is_sending=True", log_level)
                    is_sending = True
                    
            elif event["id"] == "tts_complete":
                # TTS completed a segment

                # Send next segment if available
                if segment_queue:
                    segment = segment_queue.popleft()

                    # Decrease counter BEFORE sending
                    segment_counter -= 1

                    send_log(node, "INFO", f"Sending to TTS: '{segment['text']}' (len={len(segment['text'])})", log_level)

                    node.send_output(
                        "text_segment",
                        pa.array([segment["text"]]),
                        metadata={
                            "segments_remaining": segment_counter,  # After decrease
                            **segment["metadata"]
                        }
                    )
                    send_log(node, "DEBUG", "send_output() completed, setting is_sending=True", log_level)
                else:
                    # No more segments to send
                    is_sending = False
                    
            elif event["id"] == "control":
                # Reset command
                command = event["value"][0].as_py()
                if command == "reset":
                    send_log(node, "INFO", f"Reset: Cleared {len(segment_queue)} queued segments via control command", log_level)
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
                    send_log(node, "INFO", f"Reset: Cleared {cleared_count} queued segments (no question_id)", log_level)
                else:
                    # Smart reset - only clear segments from different question_id
                    original_count = len(segment_queue)
                    new_queue = deque()
                    cleared_count = 0

                    for segment in segment_queue:
                        seg_question_id = segment["metadata"].get("question_id", None)

                        # Keep segment if:
                        # 1. It has the same question_id as the incoming reset, OR
                        # 2. It has no question_id (assume it's new content)
                        if seg_question_id == incoming_question_id or seg_question_id is None:
                            # Keep this segment
                            new_queue.append(segment)
                        else:
                            # This segment is from a different (old) question - discard it
                            cleared_count += 1

                    segment_queue = new_queue
                    segment_counter = len(segment_queue)

                    # Update current_question_id to the new question
                    current_question_id = incoming_question_id

                    # Reset is_sending if queue is empty
                    if len(segment_queue) == 0:
                        is_sending = False

                    send_log(node, "INFO", f"Smart reset: Cleared {cleared_count}/{original_count} old segments, kept {len(segment_queue)} from new question_id={incoming_question_id}", log_level)

        elif event["type"] == "STOP":
            break

if __name__ == "__main__":
    main()