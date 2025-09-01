# Voice Chat Pipeline - Dependency Management

This document provides comprehensive guidance for managing dependencies in the Dora voice chat pipeline to avoid conflicts and ensure compatibility.

## 🎯 Core Dependency Standards

All voice chat nodes follow standardized dependency versions to ensure compatibility and avoid conflicts during installation.

### **Python & Core Framework**
```toml
python = ">=3.9,<3.13"              # Recommended: 3.12
dora-rs = ">=0.3.7"                 # Dora framework core
pyarrow = ">=10.0.0"                # Data serialization
```

### **Numerical Computing**
```toml
numpy = ">=1.21.0,<2.0"             # Pin to 1.x for compiled package compatibility
scipy = ">=1.7.0"                   # Scientific computing
```

### **PyTorch Ecosystem (Voice Pipeline Standard)**
```toml
torch = ">=2.0.0,<2.3.0"           # Compatible range for all voice nodes
torchaudio = ">=2.0.0,<2.3.0"      # Audio processing, matches torch
torchvision = ">=0.15.0,<0.18.0"   # Vision models (when needed)
```

### **AI Models & NLP**
```toml
transformers = ">=4.40.0,<4.50.0"  # Security compliant (CVE-2025-32434 fix)
huggingface-hub = ">=0.19.0"       # Model downloads and management
```

### **Audio Processing**
```toml
librosa = ">=0.10.0"                # Audio analysis and processing
soundfile = ">=0.12.0"              # Audio file I/O
silero-vad = ">=5.1"                # Voice activity detection
```

## 📦 Node-Specific Dependencies

### **dora-asr** (Automatic Speech Recognition)
**Core Dependencies:**
- `numpy>=1.21.0,<2.0`
- `pyarrow>=10.0.0`
- `funasr-onnx>=0.3.2,<0.5.0`
- `librosa>=0.10.0`
- `pywhispercpp` (from GitHub)

**GPU Dependencies (Optional):**
- `torch>=2.0.0,<2.3.0`
- `torchaudio>=2.0.0,<2.3.0`
- `torchvision>=0.15.0,<0.18.0`
- `onnxruntime-gpu>=1.16.0`

**Installation:**
```bash
# CPU only
pip install -e node-hub/dora-asr

# With GPU support
pip install -e node-hub/dora-asr[gpu]
```

### **dora-primespeech** (Text-to-Speech)
**Core Dependencies:**
- `numpy>=1.21.0,<2.0`
- `torch>=2.0.0,<2.3.0`
- `torchaudio>=2.0.0,<2.3.0`
- `transformers>=4.40.0,<4.50.0`
- `pytorch-lightning>=2.0.0`
- Chinese NLP: `pypinyin>=0.50.0`, `jieba>=0.42.1`, `cn2an>=0.5.22`

**Installation:**
```bash
pip install -e node-hub/dora-primespeech
```

### **dora-speechmonitor** (Voice Activity Detection)
**Core Dependencies:**
- `numpy>=1.21.0,<2.0`
- `torch>=2.0.0,<2.3.0`
- `torchaudio>=2.0.0,<2.3.0`
- `silero-vad>=5.1`

**Installation:**
```bash
pip install -e node-hub/dora-speechmonitor
```

### **dora-qwen3** (Language Model)
**Core Dependencies:**
- `numpy>=1.21.0,<2.0`
- `transformers>=4.40.0,<4.50.0`
- `llama-cpp-python`
- `mlx>=0.5.0` (macOS ARM64 only)
- `mlx-lm>=0.10.0` (macOS ARM64 only)

**Torch Dependencies (Optional):**
- `torch>=2.0.0,<2.3.0`
- `torchaudio>=2.0.0,<2.3.0`

**Installation:**
```bash
# Standard installation
pip install -e node-hub/dora-qwen3

# With torch support (for torch models)
pip install -e node-hub/dora-qwen3[torch]
```

### **dora-text-segmenter** (Text Processing)
**Core Dependencies:**
- `numpy>=1.21.0,<2.0`
- `pyarrow>=10.0.0`

**Installation:**
```bash
pip install -e node-hub/dora-text-segmenter
```

## 🚀 Environment Setup

### **Method 1: Automated Setup (Recommended)**
```bash
cd examples/setup-new-chatbot
./setup_isolated_env.sh
```

### **Method 2: Manual Setup**
```bash
# Create voice chat environment
conda create -n dora_voice_chat python=3.12
conda activate dora_voice_chat

# Install PyTorch ecosystem (standardized versions)
pip install torch==2.2.0 torchaudio==2.2.0 torchvision==0.17.0

# Install Transformers (security compliant)
pip install transformers==4.45.0

# Install NumPy (compatible version)  
pip install numpy==1.26.4

# Install voice chat nodes
pip install -e ../../node-hub/dora-asr[gpu]
pip install -e ../../node-hub/dora-primespeech
pip install -e ../../node-hub/dora-speechmonitor
pip install -e ../../node-hub/dora-text-segmenter
pip install -e ../../node-hub/dora-qwen3[torch]

# Build Rust components
cargo build --release -p dora-openai-websocket
cargo build --release -p dora-maas-client
```

## ⚠️ Common Issues & Solutions

### **Issue 1: PyTorch Version Conflicts**
```bash
# Symptom: Different torch versions installed
# Solution: Force reinstall with consistent versions
pip uninstall torch torchaudio torchvision
pip install torch==2.2.0 torchaudio==2.2.0 torchvision==0.17.0
```

### **Issue 2: NumPy 2.0 Compatibility**
```bash
# Symptom: Errors with compiled packages (funasr-onnx, etc.)
# Solution: Downgrade to numpy 1.x
pip install numpy==1.26.4
```

### **Issue 3: Transformers Security Warning**
```bash
# Symptom: CVE-2025-32434 warning
# Solution: Use security-compliant version
pip install transformers==4.45.0
```

### **Issue 4: CUDA/GPU Issues**
```bash
# Check CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Reinstall PyTorch with CUDA support
pip uninstall torch torchaudio
pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121
```

## 🔍 Validation & Testing

### **Quick Dependency Check**
```bash
cd examples/setup-new-chatbot
python test_dependencies.py
```

### **Full Pipeline Validation**
```bash
# ASR validation
cd examples/setup-new-chatbot/asr-validation
./run_all_tests.sh

# PrimeSpeech validation  
cd ../primespeech-validation
python test_tts_direct.py
```

## 📋 Environment Variables

For consistent behavior across installations:

```bash
# Transformers security (temporary workaround)
export TRANSFORMERS_OFFLINE="1"
export HF_HUB_OFFLINE="1"

# PyTorch settings
export PYTORCH_ENABLE_MPS_FALLBACK="1"  # macOS Metal fallback

# CUDA settings (Linux/Windows with GPU)
export CUDA_VISIBLE_DEVICES="0"
```

## 📊 Tested Configurations

### **✅ Confirmed Working Setups**
1. **macOS ARM64** - Python 3.12, torch 2.2.0, transformers 4.45.0, numpy 1.26.4
2. **Linux GPU** - Python 3.12, torch 2.2.0+cu121, transformers 4.45.0, numpy 1.26.4
3. **Windows CPU** - Python 3.12, torch 2.2.0, transformers 4.45.0, numpy 1.26.4

### **⚠️ Known Issues**
1. **PyTorch 2.3+** - May cause compatibility issues with some audio processing
2. **NumPy 2.0+** - Breaks compatibility with funasr-onnx and other compiled packages
3. **Transformers 4.50+** - Security vulnerability (CVE-2025-32434)

## 🔄 Updating Dependencies

When updating versions:

1. **Test full pipeline** with new versions
2. **Update all voice nodes** to use same version ranges  
3. **Validate on multiple platforms**
4. **Update this documentation**
5. **Run validation suites**

## 📚 Additional Resources

- **Dora Core Documentation**: `/Users/yuechen/home/fresh/dora/VOICE_CHAT_DEPENDENCIES.md`
- **ASR Validation Suite**: `examples/setup-new-chatbot/asr-validation/`
- **PrimeSpeech Testing**: `examples/setup-new-chatbot/primespeech-validation/`
- **Cloud Setup**: `examples/setup-new-chatbot/README_CLOUD.md`