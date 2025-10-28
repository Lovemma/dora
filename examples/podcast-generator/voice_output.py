#!/usr/bin/env python3
"""
Voice Output - Concatenate audio with silence padding
Adds random 1-3 seconds of silence when speaker changes
"""
import argparse
import json
import time
import random
from dora import Node
import numpy as np
from scipy.io import wavfile
import pyarrow as pa


def send_log(node, level, message, config_level="INFO"):
    """Send log message through log output channel."""
    LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}

    if LOG_LEVELS.get(level, 0) < LOG_LEVELS.get(config_level, 20):
        return

    formatted_message = f"[{level}] {message}"
    log_data = {
        "node": "voice-output",
        "level": level,
        "message": formatted_message,
        "timestamp": time.time()
    }
    node.send_output("log", pa.array([json.dumps(log_data)]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-file', required=True, help='Path to output WAV file')
    args = parser.parse_args()

    node = Node("voice-output")
    log_level = "DEBUG"  # Enable DEBUG logging for troubleshooting

    # Configuration
    # "Segment" = one incoming text payload; MiniMax streams each segment as
    # multiple audio "fragments". fragment_num == 1 marks the start of a new
    # segment and is the moment to inject speaker-switch silence.
    sample_rate = 32000  # PrimeSpeech default (32 kHz, not 24 kHz!)
    silence_min = 1.0  # minimum silence in seconds
    silence_max = 3.0  # maximum silence in seconds

    # State
    audio_buffer = []
    last_speaker = None
    segment_count = 0

    send_log(node, "INFO", f"Voice Output initialized. Output: {args.output_file}", log_level)
    send_log(node, "INFO", f"Sample rate: {sample_rate} Hz, Silence: {silence_min}-{silence_max}s (random)", log_level)
    send_log(node, "INFO", "Entering event loop, waiting for audio...", log_level)

    # Event loop
    for event in node:
        send_log(node, "DEBUG", f"Received event type: {event['type']}", log_level)

        if event["type"] == "INPUT":
            event_id = event["id"]
            send_log(node, "DEBUG", f"Processing INPUT: {event_id}", log_level)

            if event_id == "daniu_audio":
                send_log(node, "DEBUG", ">>> Received daniu_audio event", log_level)

                metadata = event.get("metadata", {})
                fragment_num = metadata.get("fragment_num")
                is_segment_start = fragment_num == 1 if fragment_num is not None else True

                # Add silence BEFORE audio only when a new segment begins
                if is_segment_start:
                    if last_speaker is not None and last_speaker != 'daniu':
                        silence_duration = random.uniform(silence_min, silence_max)
                        silence_samples = int(sample_rate * silence_duration)
                        silence = np.zeros(silence_samples, dtype=np.int16)
                        audio_buffer.append(silence)
                        send_log(
                            node,
                            "INFO",
                            f"Added {silence_duration:.2f}s silence ({last_speaker} → 大牛)",
                            log_level,
                        )
                    last_speaker = 'daniu'

                # Append audio - use as_py() like audio_player does
                try:
                    # Get audio data using as_py() method (same as audio_player.py line 334)
                    raw_value = event.get("value")
                    if raw_value and len(raw_value) > 0:
                        audio_data = raw_value[0].as_py()

                        # Convert to numpy array if needed
                        if not isinstance(audio_data, np.ndarray):
                            audio_data = np.array(audio_data, dtype=np.float32)

                        original_dtype = audio_data.dtype
                        send_log(node, "DEBUG", f"Received audio: len={len(audio_data)}, dtype={original_dtype}, range=[{audio_data.min():.4f}, {audio_data.max():.4f}]", log_level)

                        # Convert float32 to int16 properly
                        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                            # Audio is in float format (range -1.0 to 1.0), convert to int16
                            audio_data = (audio_data * 32767).astype(np.int16)
                            send_log(node, "DEBUG", f"Converted {original_dtype} to int16 (range: {audio_data.min()} to {audio_data.max()})", log_level)
                        elif audio_data.dtype != np.int16:
                            # Unknown dtype, just cast
                            audio_data = audio_data.astype(np.int16)
                            send_log(node, "WARNING", f"Unknown dtype {original_dtype}, casting to int16", log_level)

                        audio_buffer.append(audio_data)
                        segment_count += 1
                        fragment_label = fragment_num if fragment_num is not None else "?"
                        send_log(
                            node,
                            "INFO",
                            f"✓ Received audio from 大牛 (fragment #{fragment_label}, {len(audio_data)} samples, {original_dtype}→int16, buffer now has {len(audio_buffer)} arrays)",
                            log_level,
                        )
                except Exception as e:
                    send_log(node, "ERROR", f"Failed to process daniu_audio: {e}", log_level)
                    import traceback
                    send_log(node, "ERROR", f"Traceback: {traceback.format_exc()}", log_level)

            elif event_id == "yifan_audio":
                send_log(node, "DEBUG", ">>> Received yifan_audio event", log_level)

                metadata = event.get("metadata", {})
                fragment_num = metadata.get("fragment_num")
                is_segment_start = fragment_num == 1 if fragment_num is not None else True

                # Add silence BEFORE audio only when a new segment begins
                if is_segment_start:
                    if last_speaker is not None and last_speaker != 'yifan':
                        silence_duration = random.uniform(silence_min, silence_max)
                        silence_samples = int(sample_rate * silence_duration)
                        silence = np.zeros(silence_samples, dtype=np.int16)
                        audio_buffer.append(silence)
                        send_log(
                            node,
                            "INFO",
                            f"Added {silence_duration:.2f}s silence ({last_speaker} → 一帆)",
                            log_level,
                        )
                    last_speaker = 'yifan'

                # Append audio - use as_py() like audio_player does
                try:
                    # Get audio data using as_py() method (same as audio_player.py line 334)
                    raw_value = event.get("value")
                    if raw_value and len(raw_value) > 0:
                        audio_data = raw_value[0].as_py()

                        # Convert to numpy array if needed
                        if not isinstance(audio_data, np.ndarray):
                            audio_data = np.array(audio_data, dtype=np.float32)

                        original_dtype = audio_data.dtype
                        send_log(node, "DEBUG", f"Received audio: len={len(audio_data)}, dtype={original_dtype}, range=[{audio_data.min():.4f}, {audio_data.max():.4f}]", log_level)

                        # Convert float32 to int16 properly
                        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                            # Audio is in float format (range -1.0 to 1.0), convert to int16
                            audio_data = (audio_data * 32767).astype(np.int16)
                            send_log(node, "DEBUG", f"Converted {original_dtype} to int16 (range: {audio_data.min()} to {audio_data.max()})", log_level)
                        elif audio_data.dtype != np.int16:
                            # Unknown dtype, just cast
                            audio_data = audio_data.astype(np.int16)
                            send_log(node, "WARNING", f"Unknown dtype {original_dtype}, casting to int16", log_level)

                        audio_buffer.append(audio_data)
                        segment_count += 1
                        fragment_label = fragment_num if fragment_num is not None else "?"
                        send_log(
                            node,
                            "INFO",
                            f"✓ Received audio from 一帆 (fragment #{fragment_label}, {len(audio_data)} samples, {original_dtype}→int16, buffer now has {len(audio_buffer)} arrays)",
                            log_level,
                        )
                except Exception as e:
                    send_log(node, "ERROR", f"Failed to process yifan_audio: {e}", log_level)
                    import traceback
                    send_log(node, "ERROR", f"Traceback: {traceback.format_exc()}", log_level)

            elif event_id == "daniu_segment_complete":
                # Just track the speaker, don't add silence here
                last_speaker = 'daniu'
                send_log(node, "DEBUG", f"大牛 segment complete, last_speaker = {last_speaker}", log_level)

            elif event_id == "yifan_segment_complete":
                # Just track the speaker, don't add silence here
                last_speaker = 'yifan'
                send_log(node, "DEBUG", f"一帆 segment complete, last_speaker = {last_speaker}", log_level)

            elif event_id == "script_complete":
                send_log(node, "INFO", f"Script complete. Concatenating {segment_count} segments...", log_level)
                send_log(node, "INFO", f"Audio buffer has {len(audio_buffer)} arrays", log_level)

                if len(audio_buffer) == 0:
                    send_log(node, "ERROR", "No audio received! Buffer is empty.", log_level)
                else:
                    try:
                        send_log(node, "INFO", "Starting concatenation...", log_level)

                        # Verify all arrays are int16 before concatenating
                        for i, arr in enumerate(audio_buffer):
                            if arr.dtype != np.int16:
                                send_log(node, "WARNING", f"Array {i} has dtype {arr.dtype}, converting to int16", log_level)
                                audio_buffer[i] = arr.astype(np.int16)

                        final_audio = np.concatenate(audio_buffer)
                        send_log(node, "INFO", f"Concatenation done. Total samples: {len(final_audio)}, dtype: {final_audio.dtype}", log_level)

                        send_log(node, "INFO", f"Writing to {args.output_file}...", log_level)

                        # Write WAV file
                        wavfile.write(args.output_file, sample_rate, final_audio)

                        # Ensure file is flushed to disk
                        import os
                        os.sync()

                        duration = len(final_audio) / sample_rate
                        file_size = os.path.getsize(args.output_file)
                        send_log(node, "INFO", f"✓ Podcast saved: {args.output_file} ({duration:.2f}s, {file_size} bytes)", log_level)
                    except Exception as e:
                        send_log(node, "ERROR", f"Failed to write audio: {e}", log_level)
                        import traceback
                        send_log(node, "ERROR", f"Traceback: {traceback.format_exc()}", log_level)

                # Give time for logs to be sent before exiting
                time.sleep(0.1)
                send_log(node, "INFO", "Exiting voice-output node", log_level)
                break

        elif event["type"] == "STOP":
            send_log(node, "INFO", "Received STOP event", log_level)
            break

    send_log(node, "INFO", "Voice output event loop exited", log_level)


if __name__ == "__main__":
    main()
