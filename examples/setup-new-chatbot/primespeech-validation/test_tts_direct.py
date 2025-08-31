#!/usr/bin/env python3
"""
Direct test of TTS with timing and audio file saving.
"""

import sys
import time
import os
import numpy as np
import soundfile as sf
from pathlib import Path

# Setup paths
sys.path.insert(0, '/home/user/dora/node-hub/dora-primespeech')
os.environ['PRIMESPEECH_MODEL_DIR'] = '/home/user/.dora/models/primespeech'

from dora_primespeech.moyoyo_tts_wrapper_streaming_fix import StreamingMoYoYoTTSWrapper

def test_tts_timing():
    """Test TTS with Chinese text and save audio."""
    
    print("=" * 80)
    print("Direct TTS Timing Test")
    print("=" * 80)
    
    # The Chinese text from the test
    chinese_text = """我们说中国式现代化是百年大战略，这又分为三个阶段。第一个阶段，我们先用30年时间建成了独立完整的工业体系和国民经济体系；再用40年，到2021年，全面建成了小康社会。我们现在正处于第三个阶段，这又被分成上下两篇：上半篇是到2035年基本实现社会主义现代化；下半篇是到本世纪中叶，也就是2050年，建成社会主义现代化强国。"""
    
    print(f"\nText: {len(chinese_text)} characters")
    print("-" * 60)
    print(chinese_text)
    print("-" * 60)
    
    # Initialize TTS
    print("\nInitializing TTS engine...")
    init_start = time.time()
    
    wrapper = StreamingMoYoYoTTSWrapper(
        voice='doubao',
        device='cpu',
        enable_streaming=False  # Use batch mode for simplicity
    )
    
    init_time = time.time() - init_start
    print(f"Initialization time: {init_time:.2f}s")
    
    # Generate audio
    print("\nGenerating audio...")
    synthesis_start = time.time()
    
    sample_rate, audio_data = wrapper.synthesize(
        chinese_text, 
        language='zh', 
        speed=1.0
    )
    
    synthesis_time = time.time() - synthesis_start
    audio_duration = len(audio_data) / sample_rate
    
    # Calculate metrics
    chars_per_second = len(chinese_text) / synthesis_time
    real_time_factor = audio_duration / synthesis_time
    
    # Save audio
    output_dir = Path("tts_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "chinese_tts_output.wav"
    
    sf.write(output_file, audio_data, sample_rate)
    
    # Print results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Text length: {len(chinese_text)} characters")
    print(f"Audio duration: {audio_duration:.2f} seconds")
    print(f"Synthesis time: {synthesis_time:.2f} seconds")
    print(f"Real-time factor: {real_time_factor:.2f}x {'(faster than real-time)' if real_time_factor > 1 else '(slower than real-time)'}")
    print(f"Processing speed: {chars_per_second:.1f} characters/second")
    print(f"\nAudio saved to: {output_file.absolute()}")
    print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")
    print("=" * 80)
    
    return output_file


if __name__ == "__main__":
    try:
        audio_file = test_tts_timing()
        print(f"\n✓ Test completed successfully!")
        print(f"✓ Audio file: {audio_file}")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()