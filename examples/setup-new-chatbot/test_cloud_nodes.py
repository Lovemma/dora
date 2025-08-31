#!/usr/bin/env python3
"""Test script for cloud Dora nodes - minimal dependencies without audio."""

import sys
import importlib
import subprocess
from pathlib import Path

def test_import(module_name, package_name=None):
    """Test if a module can be imported."""
    if package_name is None:
        package_name = module_name
    
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {package_name}: {version}")
        return True
    except ImportError as e:
        print(f"✗ {package_name}: Import failed - {e}")
        return False

def test_command(command, name):
    """Test if a command is available."""
    try:
        result = subprocess.run([command, '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print(f"✓ {name}: {version}")
            return True
        else:
            print(f"✗ {name}: Command failed")
            return False
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"✗ {name}: Not found - {e}")
        return False

def test_numpy_version():
    """Test numpy version is correct."""
    try:
        import numpy as np
        version = np.__version__
        if version.startswith('1.26'):
            print(f"✓ NumPy version: {version} (correct)")
            return True
        else:
            print(f"⚠ NumPy version: {version} (expected 1.26.x)")
            return False
    except ImportError:
        print(f"✗ NumPy: Not installed")
        return False

def test_cloud_nodes():
    """Test if cloud Dora nodes can be imported."""
    nodes = [
        ('dora_asr', 'dora-asr'),
        ('dora_primespeech', 'dora-primespeech'),
        ('dora_text_segmenter', 'dora-text-segmenter'),
        ('dora_speechmonitor', 'dora-speechmonitor'),
    ]
    
    all_ok = True
    for module_name, display_name in nodes:
        try:
            importlib.import_module(module_name)
            print(f"✓ {display_name}: Installed")
        except ImportError as e:
            print(f"✗ {display_name}: Not installed - {e}")
            all_ok = False
    
    return all_ok

def test_websocket_binary():
    """Test if dora-openai-websocket binary exists."""
    # Check common build locations
    binary_paths = [
        Path.home() / "home/mcp/dora/target/release/dora-openai-websocket",
        Path.home() / "home/mcp/dora/node-hub/dora-openai-websocket/target/release/dora-openai-websocket",
    ]
    
    for path in binary_paths:
        if path.exists():
            print(f"✓ dora-openai-websocket: Found at {path}")
            return True
    
    print(f"✗ dora-openai-websocket: Binary not found (run: cargo build --release -p dora-openai-websocket)")
    return False

def main():
    print("=" * 50)
    print("Testing Dora Cloud Environment")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test Python version
    python_version = sys.version.split()[0]
    if python_version.startswith('3.12'):
        print(f"✓ Python version: {python_version}")
    else:
        print(f"⚠ Python version: {python_version} (expected 3.12.x)")
        all_tests_passed = False
    
    print("\nCore Dependencies:")
    print("-" * 30)
    
    # Test core dependencies
    all_tests_passed &= test_numpy_version()
    all_tests_passed &= test_import('torch')
    all_tests_passed &= test_import('transformers')
    all_tests_passed &= test_import('dora', 'dora-rs')
    
    print("\nML Libraries:")
    print("-" * 30)
    
    # Test ML libraries
    all_tests_passed &= test_import('huggingface_hub')
    all_tests_passed &= test_import('datasets')
    all_tests_passed &= test_import('accelerate')
    all_tests_passed &= test_import('sentencepiece')
    
    print("\nProcessing Libraries:")
    print("-" * 30)
    
    # Test processing libraries (no audio)
    all_tests_passed &= test_import('onnxruntime')
    all_tests_passed &= test_import('funasr_onnx', 'funasr-onnx')
    all_tests_passed &= test_import('librosa')
    all_tests_passed &= test_import('scipy')
    
    print("\nNetworking Libraries:")
    print("-" * 30)
    
    # Test networking libraries  
    all_tests_passed &= test_import('websockets')
    all_tests_passed &= test_import('aiohttp')
    all_tests_passed &= test_import('requests')
    
    print("\nDora Cloud Nodes:")
    print("-" * 30)
    
    # Test Dora nodes
    all_tests_passed &= test_cloud_nodes()
    
    print("\nRust Components:")
    print("-" * 30)
    
    # Test Rust binaries
    all_tests_passed &= test_websocket_binary()
    
    print("\nSystem Commands:")
    print("-" * 30)
    
    # Test system commands
    all_tests_passed &= test_command('dora', 'Dora CLI')
    all_tests_passed &= test_command('cargo', 'Cargo')
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✓ All cloud dependencies are installed correctly!")
        print("\nNote: Audio packages are intentionally excluded for cloud deployment.")
        print("Audio I/O will be handled via WebSocket connections from clients.")
    else:
        print("✗ Some dependencies are missing or incorrect.")
        print("  Please run setup_cloud_env.sh to fix issues.")
    print("=" * 50)
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())