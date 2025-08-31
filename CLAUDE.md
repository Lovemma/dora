# Claude Context for Dora AI Framework

## Project Overview
Dora is an event-driven robotics framework with advanced voice chat capabilities. This context document provides comprehensive guidance for working with the Dora ecosystem, including recent GPU acceleration enhancements, model management improvements, and complete validation suites.

## Major Recent Developments

### 1. GPU Acceleration for ASR (Speech Recognition)
- **Complete GPU acceleration** for FunASR Chinese ASR engine
- **2.27x performance improvement** with CUDA (0.28s vs 0.64s processing)
- **Dual backend support**: PyTorch and ONNX with automatic selection
- **Intelligent device management**: Automatic GPU detection with CPU fallback
- **Memory efficient**: Only 2GB VRAM usage on modern GPUs
- **Environment control**: `USE_GPU=true/false` for easy switching

### 2. Enhanced Model Management System
- **Complete model downloads**: Fixed Git LFS integration for large model files
- **G2PW model fix**: Downloads complete repository with all dependencies
- **ONNX conversion tools**: PyTorch to ONNX conversion for optimization
- **Standalone operation**: Model manager no longer depends on PrimeSpeech modules
- **Automated validation**: Built-in model integrity checking

### 3. Comprehensive Validation Suites
- **ASR Validation Suite**: Complete testing framework with GPU benchmarks
- **PrimeSpeech TTS Validation**: Performance analysis and optimization guides  
- **Automated test runners**: One-command validation of entire pipeline
- **Integration examples**: Ready-to-use code for various deployment scenarios

### 4. Production-Ready Error Handling
- **Robust error recovery**: Enhanced error handling across all components
- **Comprehensive logging**: Detailed debug information with proper tracebacks
- **Graceful degradation**: Automatic fallback mechanisms for hardware failures
- **WebSocket stability**: Fixed connection reset issues and improved reliability

## Architecture Overview

### Core Components
```
/dora/
├── node-hub/                           # Core processing nodes
│   ├── dora-asr/                      # GPU-accelerated ASR (FunASR/Whisper)
│   │   ├── dora_asr/engines/funasr_gpu.py  # GPU engine with PyTorch/ONNX
│   │   ├── GPU_ENHANCEMENTS.md        # Technical documentation
│   │   └── benchmark_gpu.py           # Performance testing
│   ├── dora-primespeech/              # TTS synthesis with error handling
│   ├── dora-speechmonitor/            # Speech activity detection
│   ├── dora-text-segmenter/           # Intelligent text chunking
│   ├── dora-openai-websocket/         # WebSocket server (Rust)
│   └── dora-maas-client/              # Cloud AI integration (Rust)
├── examples/
│   ├── model-manager/                 # Enhanced model download system
│   │   ├── download_models.py         # Complete model management
│   │   └── convert_to_onnx.py         # PyTorch to ONNX conversion
│   ├── setup-new-chatbot/            # Environment setup and validation
│   │   ├── asr-validation/            # Complete ASR testing suite
│   │   ├── primespeech-validation/    # TTS performance analysis
│   │   └── setup_cloud_env.sh         # Cloud deployment script
│   └── chatbot-with-websocket/        # Production examples
```

### Validation and Testing Framework
```
examples/setup-new-chatbot/asr-validation/
├── README.md                    # Comprehensive documentation
├── QUICK_START.md              # 5-minute getting started guide
├── INTEGRATION_GUIDE.md        # Production integration examples
├── run_all_tests.sh            # Automated test suite
├── test_basic_asr.py           # Functionality validation
├── benchmark_gpu.py            # Performance comparison
├── test_gpu_env_control.py     # Environment variable testing
├── validate_gpu_switching.py   # Runtime GPU/CPU switching
├── dataflow_gpu.yml            # GPU-enabled Dora dataflow
├── dataflow_cpu.yml            # CPU-only Dora dataflow
└── test_audio_chinese.wav      # Standardized test audio (17.35s)
```

## Performance Benchmarks

### ASR Performance (RTX 4090, 17.35s Chinese Audio)
| Configuration | Processing Time | RTF | Real-time Speed | Memory |
|--------------|-----------------|-----|-----------------|---------|
| Original ONNX (CPU) | 0.640s | 0.037 | 27.1x | N/A |
| GPU PyTorch CPU | 0.955s | 0.055 | 18.2x | N/A |
| **GPU PyTorch CUDA** | **0.282s** | **0.016** | **61.6x** | **2GB** |

**Key Results:**
- **2.27x faster** with GPU acceleration
- **61.6x real-time processing** speed
- **Identical transcription quality** across all modes
- **Efficient memory usage**: Only 2GB VRAM

### TTS Performance (PrimeSpeech CPU)
- **Input**: 160 Chinese characters
- **Output**: 31.97s audio
- **Processing Time**: 41.84s 
- **Real-time Factor**: 0.76x (CPU baseline)
- **GPU potential**: Expected 3-5x improvement

## Configuration Management

### Environment Variables
```yaml
# ASR Configuration
USE_GPU: "true"                 # Enable GPU acceleration
ASR_ENGINE: "funasr"           # funasr/whisper/auto
LANGUAGE: "zh"                 # zh/en/auto
ASR_MODELS_DIR: "~/.dora/models/asr"
ENABLE_PUNCTUATION: "true"
MIN_AUDIO_DURATION: "0.5"

# TTS Configuration
VOICE_NAME: "Doubao"
PRIMESPEECH_MODEL_DIR: "~/.dora/models/primespeech"
TEXT_LANG: "zh"
USE_GPU: "false"              # TTS GPU support coming soon

# System Configuration
LOG_LEVEL: "INFO"             # DEBUG/INFO/WARNING/ERROR
NUM_THREADS: "4"
```

### GPU Control Examples
```yaml
# GPU-enabled ASR node
- id: asr-gpu
  operator:
    python: ../../node-hub/dora-asr
  inputs:
    audio: audio-source/audio
  outputs:
    - text
  env:
    USE_GPU: "true"
    ASR_ENGINE: "funasr"
    LANGUAGE: "zh"

# CPU-only ASR node
- id: asr-cpu
  operator:
    python: ../../node-hub/dora-asr
  inputs:
    audio: audio-source/audio
  outputs:
    - text
  env:
    USE_GPU: "false"
    ASR_ENGINE: "funasr"
    LANGUAGE: "zh"
```

## Quick Start Commands

### Environment Setup
```bash
# Setup cloud environment
cd examples/setup-new-chatbot
./setup_cloud_env.sh
conda activate dora_cloud

# Download models
cd ../model-manager
python download_models.py --model funasr
python download_models.py --model primespeech
```

### Validation and Testing
```bash
# Complete ASR validation
cd examples/setup-new-chatbot/asr-validation
./run_all_tests.sh

# Quick ASR test
USE_GPU=true python test_basic_asr.py

# Performance benchmark
python benchmark_gpu.py --audio test_audio_chinese.wav

# Test TTS performance
cd ../primespeech-validation
python test_tts_direct.py

# TTS dataflow test  
dora start dataflow-static.yml
```

### Production Deployment
```bash
# Build WebSocket server
cd node-hub/dora-openai-websocket
cargo build --release

# Start server
cargo run -p dora-openai-websocket

# Run GPU-enabled dataflow
cd examples/setup-new-chatbot/asr-validation
dora start dataflow_gpu.yml
```

## Model Management

### Required Models
```bash
# ASR Models (FunASR)
~/.dora/models/asr/funasr/
├── speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch/
└── punc_ct-transformer_cn-en-common-vocab471067-large/

# TTS Models (PrimeSpeech)
~/.dora/models/primespeech/
├── G2PWModel/               # Complete HuggingFace repository
├── hifigan/                 # Vocoder model
└── fastspeech2/            # Acoustic model
```

### Model Download Commands
```bash
# Download ASR models with Git LFS
cd examples/model-manager
python download_models.py --model funasr
git lfs pull  # Ensure actual model files, not pointers

# Download complete G2PW model (fixed)
python download_models.py --model g2pw

# Convert models to ONNX (optional)
python convert_to_onnx.py --model paraformer --input-dir ~/.dora/models/asr/funasr
```

## Advanced Features

### Multi-Language Support
```python
from dora_asr.manager import ASRManager

manager = ASRManager()

# Chinese - uses FunASR with GPU
chinese_result = manager.transcribe(audio, language='zh')

# English - uses Whisper
english_result = manager.transcribe(audio, language='en') 

# Auto-detect language
auto_result = manager.transcribe(audio, language='auto')
print(f"Detected: {auto_result['language']}")
```

### Performance Optimization
```python
# GPU memory monitoring
import torch
if torch.cuda.is_available():
    print(f"GPU Memory: {torch.cuda.memory_allocated()/1024**3:.2f} GB")

# Batch processing for efficiency
manager = ASRManager()
for audio_file in audio_files:
    result = manager.transcribe(audio_data)  # Reuses loaded models

# Cleanup when done
manager.cleanup()
torch.cuda.empty_cache()
```

### WebSocket Integration
```yaml
# Production WebSocket dataflow
nodes:
  - id: websocket-server
    operator:
      rust: ../../node-hub/dora-openai-websocket
    outputs: [audio]
    
  - id: asr-gpu
    operator:
      python: ../../node-hub/dora-asr
    inputs:
      audio: websocket-server/audio
    outputs: [text]
    env:
      USE_GPU: "true"
      ASR_ENGINE: "funasr"
      LANGUAGE: "auto"
```

## Troubleshooting Guide

### GPU Issues
```bash
# Check CUDA availability
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
nvidia-smi

# Reinstall PyTorch with CUDA
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Verify GPU engine selection
USE_GPU=true python -c "
from dora_asr.manager import ASRManager
m = ASRManager()
print(f'Engine: {m._engine_classes[\"funasr\"].__name__}')
"
```

### Model Issues
```bash
# Check model files (not Git LFS pointers)
ls -lh ~/.dora/models/asr/funasr/*/model*
# Files should be >100MB, not ~134 bytes

# Pull actual model files
cd ~/.dora/models/asr/funasr/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch
git lfs pull

# Validate model integrity
python -c "
from dora_asr.manager import ASRManager
try:
    m = ASRManager()
    print('✅ Models loaded successfully')
except Exception as e:
    print(f'❌ Model error: {e}')
"
```

### Performance Issues
```bash
# Run comprehensive benchmark
cd examples/setup-new-chatbot/asr-validation
python benchmark_gpu.py --audio test_audio_chinese.wav

# Monitor GPU utilization
watch -n 0.5 nvidia-smi

# Check CPU/GPU engine selection
USE_GPU=true python test_basic_asr.py | grep "Engine"
```

## Cloud Deployment

### Docker Configuration
```dockerfile
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 python3-pip git git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Install Dora components
COPY node-hub/dora-asr /app/dora-asr
WORKDIR /app
RUN pip install -e dora-asr

# Download models
RUN python examples/model-manager/download_models.py --model funasr

# GPU configuration
ENV USE_GPU=true
ENV ASR_ENGINE=funasr
ENV LANGUAGE=zh

EXPOSE 8123
CMD ["python", "websocket_server.py"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dora-asr-gpu
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dora-asr
  template:
    metadata:
      labels:
        app: dora-asr
    spec:
      containers:
      - name: asr-gpu
        image: your-registry/dora-asr:gpu-latest
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "8Gi"
          requests:
            nvidia.com/gpu: 1
            memory: "4Gi"
        env:
        - name: USE_GPU
          value: "true"
        - name: ASR_ENGINE
          value: "funasr"
        ports:
        - containerPort: 8123
```

## Recent Commits and Changes

### Latest Commits (Branch: cloud-model-mcp)
1. **7dfd3364** - Enhanced PrimeSpeech TTS with complete G2PW model download and validation suite
   - Fixed G2PW model download to include all required files (config.py, bert_config.json, POLYPHONIC_CHARS.txt)
   - Added comprehensive error handling with traceback logging to dora-primespeech
   - Ensures segment_complete signal sent even on TTS synthesis errors
   - Added complete PrimeSpeech validation suite with performance benchmarks
   - Performance baseline: 160 Chinese chars → 31.97s audio in 41.84s (0.76x RTF on CPU)
2. **9430a80b** - Added comprehensive ASR validation suite with GPU benchmarking  
3. **ab79bffd** - Added GPU acceleration support for FunASR engine
4. **39eac0e1** - Enhanced model-manager with standalone functionality

### Key Files Modified
- `node-hub/dora-asr/dora_asr/engines/funasr_gpu.py` - GPU acceleration engine
- `node-hub/dora-asr/dora_asr/manager.py` - Automatic GPU engine selection
- `node-hub/dora-primespeech/dora_primespeech/main.py` - Enhanced error handling with tracebacks
- `examples/model-manager/download_models.py` - Fixed G2PW complete model downloads
- `examples/setup-new-chatbot/asr-validation/` - Complete ASR validation suite
- `examples/setup-new-chatbot/primespeech-validation/` - Complete TTS validation suite

## System Requirements

### Minimum Requirements
- **Python**: 3.12
- **PyTorch**: 2.0+ with CUDA support
- **NumPy**: 1.26.4 (critical for compatibility)
- **Dora CLI**: 0.3.12+

### Recommended GPU Setup
- **GPU**: NVIDIA with CUDA Compute 3.5+
- **CUDA**: 12.1 (recommended)
- **VRAM**: 4GB+ (ASR uses ~2GB)
- **Driver**: Latest NVIDIA drivers

### Production Checklist
- [ ] GPU drivers and CUDA installed
- [ ] Models downloaded and verified (not Git LFS pointers)
- [ ] Validation suite passes: `./run_all_tests.sh`
- [ ] WebSocket server builds: `cargo build --release`
- [ ] Performance benchmark meets requirements
- [ ] Error handling tested under load
- [ ] Monitoring and logging configured

## Contact and Resources

- **Repository**: https://github.com/kippalbot/dora.git
- **Branch**: cloud-model-mcp
- **ASR Validation**: `examples/setup-new-chatbot/asr-validation/`
- **TTS Validation**: `examples/setup-new-chatbot/primespeech-validation/`
- **GPU Documentation**: `node-hub/dora-asr/GPU_ENHANCEMENTS.md` 
- **Integration Examples**: `examples/setup-new-chatbot/asr-validation/INTEGRATION_GUIDE.md`
- **Performance Results**: `examples/setup-new-chatbot/primespeech-validation/RESULTS.md`

This context provides comprehensive guidance for working with the enhanced Dora AI framework, including GPU acceleration, validation tools, and production deployment strategies.