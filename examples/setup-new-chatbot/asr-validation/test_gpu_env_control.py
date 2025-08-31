#!/usr/bin/env python3
"""
Test script to validate GPU environment variable control
"""

import os
import sys
import importlib

def test_gpu_control():
    """Test that USE_GPU environment variable correctly controls GPU usage"""
    
    print("="*60)
    print("Testing GPU Environment Variable Control")
    print("="*60)
    
    # Test 1: USE_GPU=false should use CPU
    print("\nTest 1: Setting USE_GPU=false")
    os.environ['USE_GPU'] = 'false'
    
    # Force reload modules to pick up new environment
    if 'dora_asr.config' in sys.modules:
        del sys.modules['dora_asr.config']
    if 'dora_asr.engines.funasr_gpu' in sys.modules:
        del sys.modules['dora_asr.engines.funasr_gpu']
    
    from dora_asr.config import ASRConfig
    config = ASRConfig()
    print(f"  Config.USE_GPU: {config.USE_GPU}")
    assert config.USE_GPU == False, "USE_GPU should be False"
    
    from dora_asr.engines.funasr_gpu import FunASRGPUEngine
    engine = FunASRGPUEngine()
    print(f"  Engine config.USE_GPU: {engine.config.USE_GPU}")
    
    # Setup and check device
    try:
        engine.setup()
        print(f"  Engine device: {engine.device}")
        print(f"  Engine backend: {'PyTorch' if engine.use_pytorch else 'ONNX'}")
        assert engine.device == "cpu", "Device should be CPU when USE_GPU=false"
        print("  ✅ Test 1 PASSED: CPU mode activated with USE_GPU=false")
    except Exception as e:
        print(f"  ❌ Test 1 FAILED: {e}")
        return False
    
    # Test 2: USE_GPU=true should use GPU (if available)
    print("\nTest 2: Setting USE_GPU=true")
    os.environ['USE_GPU'] = 'true'
    
    # Force reload modules again
    if 'dora_asr.config' in sys.modules:
        del sys.modules['dora_asr.config']
    if 'dora_asr.engines.funasr_gpu' in sys.modules:
        del sys.modules['dora_asr.engines.funasr_gpu']
    
    from dora_asr.config import ASRConfig
    config = ASRConfig()
    print(f"  Config.USE_GPU: {config.USE_GPU}")
    assert config.USE_GPU == True, "USE_GPU should be True"
    
    from dora_asr.engines.funasr_gpu import FunASRGPUEngine
    import torch
    
    engine = FunASRGPUEngine()
    print(f"  Engine config.USE_GPU: {engine.config.USE_GPU}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    
    # Setup and check device
    try:
        engine.setup()
        print(f"  Engine device: {engine.device}")
        print(f"  Engine backend: {'PyTorch' if engine.use_pytorch else 'ONNX'}")
        
        if torch.cuda.is_available():
            assert engine.device == "cuda", "Device should be CUDA when USE_GPU=true and GPU available"
            print("  ✅ Test 2 PASSED: GPU mode activated with USE_GPU=true")
        else:
            assert engine.device == "cpu", "Device should fall back to CPU when GPU not available"
            print("  ✅ Test 2 PASSED: Correctly fell back to CPU (no GPU available)")
    except Exception as e:
        print(f"  ❌ Test 2 FAILED: {e}")
        return False
    
    # Test 3: Different string formats
    print("\nTest 3: Testing different string formats")
    test_cases = [
        ("True", True),
        ("TRUE", True),
        ("true", True),
        ("False", False),
        ("FALSE", False),
        ("false", False),
        ("1", False),  # Should be false (not "true")
        ("0", False),
        ("yes", False),  # Should be false (not "true")
        ("", False),  # Empty defaults to false
    ]
    
    for value, expected in test_cases:
        os.environ['USE_GPU'] = value
        
        # Force reload
        if 'dora_asr.config' in sys.modules:
            del sys.modules['dora_asr.config']
        
        from dora_asr.config import ASRConfig
        config = ASRConfig()
        
        if config.USE_GPU == expected:
            print(f"  ✅ USE_GPU='{value}' -> {config.USE_GPU} (expected {expected})")
        else:
            print(f"  ❌ USE_GPU='{value}' -> {config.USE_GPU} (expected {expected})")
            return False
    
    print("\n" + "="*60)
    print("All tests PASSED! Environment control working correctly.")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_gpu_control()
    sys.exit(0 if success else 1)