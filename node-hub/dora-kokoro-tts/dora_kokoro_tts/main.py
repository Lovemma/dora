"""
Enhanced Dora Kokoro TTS Node with PrimeSpeech-compatible interface.
Fast, multi-language text-to-speech with backpressure control.
"""

import os
import re
import sys
import time
import json
import traceback
import numpy as np
import pyarrow as pa
from dora import Node
from kokoro import KPipeline

# Environment configuration
LANGUAGE = os.getenv("LANGUAGE", "en")
VOICE = os.getenv("VOICE", "af_heart")
SPEED = float(os.getenv("SPEED", "1.0"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def send_log(node, level, message, config_level="INFO"):
    """Send log message through log output channel."""
    LOG_LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40
    }

    if LOG_LEVELS.get(level, 0) < LOG_LEVELS.get(config_level, 20):
        return

    formatted_message = f"[{level}] {message}"
    # Also print to console
    try:
        print(formatted_message, file=sys.stderr if level in {"ERROR", "WARNING"} else sys.stdout, flush=True)
    except Exception:
        pass

    log_data = {
        "node": "kokoro-tts",
        "level": level,
        "message": formatted_message,
        "timestamp": time.time()
    }
    node.send_output("log", pa.array([json.dumps(log_data)]))


def main():
    """Main entry point for Kokoro TTS node with enhanced interface."""

    node = Node()

    send_log(node, "INFO", "Kokoro TTS Node initialized", LOG_LEVEL)
    send_log(node, "INFO", f"Language: {LANGUAGE}, Voice: {VOICE}, Speed: {SPEED}", LOG_LEVEL)

    # LAZY INITIALIZATION - don't block event loop!
    # Pipeline will be initialized on first text event to avoid blocking
    pipeline = None
    send_log(node, "INFO", "Using lazy initialization - pipeline will load on first text", LOG_LEVEL)

    # Statistics
    total_syntheses = 0
    total_duration = 0

    send_log(node, "INFO", "Entering event loop, waiting for events", LOG_LEVEL)

    for event in node:
        send_log(node, "DEBUG", f"Received event: type={event['type']}, id={event.get('id', 'N/A')}", LOG_LEVEL)

        if event["type"] == "INPUT":
            input_id = event["id"]

            if input_id == "text":
                # Get text to synthesize
                text = event["value"][0].as_py()
                metadata = event.get("metadata", {})

                # Extract metadata
                segment_index = metadata.get("segment_index", -1)
                segments_remaining = metadata.get("segments_remaining", 0)
                question_id = metadata.get("question_id", "default")

                send_log(node, "DEBUG", f"Received text: '{text}' (len={len(text)}, segment={segment_index})", LOG_LEVEL)

                # Skip if text is only punctuation or whitespace
                text_stripped = text.strip()
                if not text_stripped or all(c in '。！？.!?,，、；：""''（）【】《》\n\r\t ' for c in text_stripped):
                    send_log(node, "DEBUG", f"Skipped - text is only punctuation/whitespace: '{text}'", LOG_LEVEL)
                    # Send segment_complete without audio
                    node.send_output(
                        "segment_complete",
                        pa.array(["skipped"]),
                        metadata={
                            "segment_index": segment_index,
                            "question_id": question_id
                        }
                    )
                    continue

                send_log(node, "INFO", f"Processing segment {segment_index + 1} (len={len(text)})", LOG_LEVEL)

                # Lazy initialize pipeline on first use
                if pipeline is None:
                    send_log(node, "INFO", f"Lazy initializing pipeline for language: {LANGUAGE}", LOG_LEVEL)
                    if LANGUAGE in ["zh", "ch", "chinese"]:
                        pipeline = KPipeline(lang_code="z")
                        send_log(node, "INFO", "Initialized Chinese (zh) pipeline", LOG_LEVEL)
                    elif LANGUAGE in ["ja", "japanese"]:
                        pipeline = KPipeline(lang_code="j")
                        send_log(node, "INFO", "Initialized Japanese (ja) pipeline", LOG_LEVEL)
                    elif LANGUAGE in ["ko", "korean"]:
                        pipeline = KPipeline(lang_code="k")
                        send_log(node, "INFO", "Initialized Korean (ko) pipeline", LOG_LEVEL)
                    else:
                        pipeline = KPipeline(lang_code="a")
                        send_log(node, "INFO", "Initialized English (en) pipeline", LOG_LEVEL)

                # Auto-detect language from text (if contains Chinese characters)
                if re.findall(r'[\u4e00-\u9fff]+', text):
                    if pipeline.lang_code != "z":
                        send_log(node, "DEBUG", "Switching to Chinese pipeline", LOG_LEVEL)
                        pipeline = KPipeline(lang_code="z")
                elif pipeline.lang_code != "a" and LANGUAGE in ["en", "english"]:
                    send_log(node, "DEBUG", "Switching to English pipeline", LOG_LEVEL)
                    pipeline = KPipeline(lang_code="a")

                # Synthesize speech
                start_time = time.time()

                try:
                    # Generate audio using Kokoro
                    generator = pipeline(
                        text,
                        voice=VOICE,
                        speed=SPEED,
                        split_pattern=r"\n+",
                    )

                    # Collect all audio chunks
                    audio_chunks = []
                    for _, (_, _, audio) in enumerate(generator):
                        audio_np = audio.numpy()
                        audio_chunks.append(audio_np)

                    if not audio_chunks:
                        raise RuntimeError("No audio generated from Kokoro")

                    # Concatenate all chunks
                    audio_array = np.concatenate(audio_chunks)

                    synthesis_time = time.time() - start_time
                    sample_rate = 24000  # Kokoro default
                    audio_duration = len(audio_array) / sample_rate

                    total_syntheses += 1
                    total_duration += audio_duration

                    send_log(node, "INFO", f"Synthesized: {audio_duration:.2f}s audio in {synthesis_time:.3f}s", LOG_LEVEL)

                    # Send audio output with metadata
                    node.send_output(
                        "audio",
                        pa.array([audio_array.astype(np.float32)]),
                        metadata={
                            "segment_index": segment_index,
                            "segments_remaining": segments_remaining,
                            "question_id": question_id,
                            "sample_rate": sample_rate,
                            "duration": audio_duration,
                            "is_streaming": False,
                        }
                    )

                    # Send segment completion signal
                    node.send_output(
                        "segment_complete",
                        pa.array(["completed"]),
                        metadata={
                            "segment_index": segment_index,
                            "question_id": question_id
                        }
                    )
                    send_log(node, "INFO", f"Sent segment_complete for segment {segment_index + 1}", LOG_LEVEL)

                except Exception as e:
                    error_details = traceback.format_exc()
                    send_log(node, "ERROR", f"Synthesis error: {e}", LOG_LEVEL)
                    send_log(node, "ERROR", f"Traceback: {error_details}", LOG_LEVEL)

                    # Send segment completion with error status
                    node.send_output(
                        "segment_complete",
                        pa.array(["error"]),
                        metadata={
                            "segment_index": segment_index,
                            "question_id": question_id,
                            "error": str(e),
                            "error_stage": "synthesis"
                        }
                    )
                    send_log(node, "ERROR", f"Sent error segment_complete for segment {segment_index + 1}", LOG_LEVEL)

            elif input_id == "control":
                # Handle control commands
                command = event["value"][0].as_py()

                if command == "reset":
                    send_log(node, "INFO", "[KokoroTTS] RESET received", LOG_LEVEL)
                    # Reset statistics
                    total_syntheses = 0
                    total_duration = 0
                    send_log(node, "INFO", "[KokoroTTS] Reset acknowledged", LOG_LEVEL)

                elif command == "stats":
                    send_log(node, "INFO", f"Total syntheses: {total_syntheses}", LOG_LEVEL)
                    send_log(node, "INFO", f"Total audio duration: {total_duration:.1f}s", LOG_LEVEL)
                    if total_syntheses > 0:
                        avg_duration = total_duration / total_syntheses
                        send_log(node, "INFO", f"Average audio duration: {avg_duration:.1f}s", LOG_LEVEL)

        elif event["type"] == "STOP":
            break

    send_log(node, "INFO", "Kokoro TTS node stopped", LOG_LEVEL)


if __name__ == "__main__":
    main()
