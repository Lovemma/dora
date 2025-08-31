#!/usr/bin/env python3
"""
WAV file player node for Dora dataflow
Reads a WAV file and sends audio data
"""

import time
import librosa
import numpy as np
from pathlib import Path
from dora import Node

def main():
    """Main function for WAV player node"""
    
    # Initialize Dora node
    node = Node()
    
    # Audio file to play
    audio_file = "test_audio_chinese.wav"
    
    # Check if file exists
    if not Path(audio_file).exists():
        print(f"Error: Audio file '{audio_file}' not found!")
        return
    
    print(f"Loading audio file: {audio_file}")
    
    # Load audio
    audio_data, sr = librosa.load(audio_file, sr=16000)
    duration = len(audio_data) / sr
    
    print(f"Audio loaded:")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Samples: {len(audio_data)}")
    
    # Wait a moment for other nodes to initialize
    time.sleep(1)
    
    # Send audio data
    print("Sending audio data...")
    audio_bytes = audio_data.astype(np.float32).tobytes()
    node.send_output("audio", audio_bytes)
    
    print(f"Audio sent ({len(audio_bytes)} bytes)")
    
    # Keep node alive for a moment to ensure delivery
    time.sleep(2)
    
    print("WAV player node completed")

if __name__ == "__main__":
    main()