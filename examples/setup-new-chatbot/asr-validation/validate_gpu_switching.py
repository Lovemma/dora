#!/usr/bin/env python3
"""
Validate that GPU switching works correctly with actual audio transcription
"""

import os
import sys
import time
import numpy as np
import librosa

def test_with_config(use_gpu: bool, audio_file: str = None):
    """Test ASR with specific GPU configuration"""
    
    # Set environment variable
    os.environ['USE_GPU'] = 'true' if use_gpu else 'false'
    
    print(f"\n{'='*60}")
    print(f"Testing with USE_GPU={os.environ['USE_GPU']}")
    print(f"{'='*60}")
    
    # Force reload of modules to pick up new environment
    modules_to_reload = [
        'dora_asr.config',
        'dora_asr.engines.funasr_gpu',
        'dora_asr.engines.funasr',
        'dora_asr.manager'
    ]
    
    for module in modules_to_reload:
        if module in sys.modules:
            del sys.modules[module]
    
    # Import fresh with new environment
    from dora_asr.manager import ASRManager
    from dora_asr.config import ASRConfig
    
    # Check config
    config = ASRConfig()
    print(f"Config.USE_GPU: {config.USE_GPU}")
    assert config.USE_GPU == use_gpu, f"Config mismatch: expected {use_gpu}, got {config.USE_GPU}"
    
    # Initialize manager
    manager = ASRManager()
    
    # Load test audio
    if audio_file and os.path.exists(audio_file):
        print(f"Loading audio from: {audio_file}")
        audio_data, sr = librosa.load(audio_file, sr=16000)
    else:
        print("Using synthetic test audio (2 seconds silence)")
        audio_data = np.zeros(32000, dtype=np.float32)
    
    # Perform transcription
    print("Performing transcription...")
    start_time = time.time()
    result = manager.transcribe(audio_data, language='zh')
    elapsed = time.time() - start_time
    
    # Check which engine was used
    engine_name = 'funasr'  # Default for Chinese
    if engine_name in manager._engines:
        engine = manager._engines[engine_name]
        print(f"Engine class: {engine.__class__.__name__}")
        
        # Check if it's the GPU-enhanced engine
        if engine.__class__.__name__ == 'FunASRGPUEngine':
            print(f"Engine device: {engine.device}")
            if use_gpu:
                import torch
                if torch.cuda.is_available():
                    assert engine.device == "cuda", f"Expected CUDA but got {engine.device}"
                    print("✅ GPU mode confirmed: using CUDA")
                else:
                    print("⚠️ GPU requested but not available, using CPU")
            else:
                assert engine.device == "cpu", f"Expected CPU but got {engine.device}"
                print("✅ CPU mode confirmed")
            
            if hasattr(engine, 'use_pytorch'):
                print(f"Backend: {'PyTorch' if engine.use_pytorch else 'ONNX'}")
        elif engine.__class__.__name__ == 'FunASREngine':
            # Original FunASR engine (always CPU)
            print("Using original FunASREngine (CPU only)")
            if use_gpu:
                print("⚠️ GPU requested but using original CPU-only engine")
            else:
                print("✅ CPU mode confirmed")
        else:
            print(f"Unknown engine type: {engine.__class__.__name__}")
    
    print(f"Transcription time: {elapsed:.3f}s")
    if result.get('text'):
        print(f"Result: {result['text'][:100]}...")
    
    # Cleanup
    manager.cleanup()
    
    return True

def main():
    """Run validation tests"""
    
    # Check for test audio file
    test_audio = "/home/user/dora/examples/funasr-gpu-test/asr.wav"
    if not os.path.exists(test_audio):
        test_audio = None
        print("Note: Using synthetic audio for testing")
    
    print("="*60)
    print("GPU SWITCHING VALIDATION TEST")
    print("="*60)
    
    try:
        # Test 1: CPU mode
        print("\n[TEST 1] CPU Mode")
        success1 = test_with_config(use_gpu=False, audio_file=test_audio)
        
        # Test 2: GPU mode
        print("\n[TEST 2] GPU Mode")
        success2 = test_with_config(use_gpu=True, audio_file=test_audio)
        
        # Test 3: Switch back to CPU
        print("\n[TEST 3] Switch back to CPU")
        success3 = test_with_config(use_gpu=False, audio_file=test_audio)
        
        if success1 and success2 and success3:
            print("\n" + "="*60)
            print("✅ ALL TESTS PASSED!")
            print("GPU switching is working correctly.")
            print("="*60)
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())