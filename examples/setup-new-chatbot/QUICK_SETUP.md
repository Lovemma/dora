# Quick Setup Guide - Dora Voice Chat

## 🚀 One-Command Setup

```bash
cd examples/setup-new-chatbot
./setup_isolated_env.sh
```

## 📋 What Gets Installed

### **Standardized Dependencies**
- **Python 3.12** - Recommended Python version
- **NumPy 1.26.4** - Compatible with all compiled packages  
- **PyTorch 2.2.0** - Within voice pipeline range (2.0.0-2.3.0)
- **Transformers 4.45.0** - Security compliant version
- **Dora-rs ≥0.3.7** - Latest Dora framework

### **Voice Chat Nodes**
- **dora-asr** - Speech recognition (FunASR + Whisper)
- **dora-primespeech** - Text-to-speech (MoYoYo TTS)  
- **dora-speechmonitor** - Voice activity detection
- **dora-text-segmenter** - Text processing for TTS
- **dora-qwen3** - Local language model

### **Rust Components** (if Cargo available)
- **dora-openai-websocket** - Real-time WebSocket server
- **dora-maas-client** - Cloud AI integration

## ✅ Verification

After setup, test your installation:

```bash
conda activate dora_voice_chat
cd examples/setup-new-chatbot

# Quick dependency check
python test_dependencies.py

# Full ASR validation
cd asr-validation
./run_all_tests.sh

# TTS validation
cd ../primespeech-validation  
python test_tts_direct.py
```

## 🔧 Manual Installation

If the automatic script fails:

```bash
# Create environment
conda create -n dora_voice_chat python=3.12
conda activate dora_voice_chat

# Install core dependencies
pip install numpy==1.26.4
pip install torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0
pip install transformers==4.45.0

# Install voice nodes
pip install -e ../../node-hub/dora-asr[gpu]
pip install -e ../../node-hub/dora-primespeech  
pip install -e ../../node-hub/dora-speechmonitor
pip install -e ../../node-hub/dora-text-segmenter
pip install -e ../../node-hub/dora-qwen3[torch]

# Build Rust components (optional)
cargo build --release -p dora-openai-websocket
cargo build --release -p dora-maas-client
```

## 📚 Documentation

- **[DEPENDENCIES.md](./DEPENDENCIES.md)** - Complete dependency specifications
- **[README.md](./README.md)** - Full setup documentation  
- **[README_CLOUD.md](./README_CLOUD.md)** - Cloud deployment guide

## 🆘 Common Issues

### NumPy 2.0 Error
```bash
pip install numpy==1.26.4 --force-reinstall
```

### PyTorch Version Conflicts  
```bash
pip uninstall torch torchaudio torchvision
pip install torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0
```

### Transformers Security Warning
```bash
pip install transformers==4.45.0 --force-reinstall
```

## 🎯 Environment Variables

For consistent behavior:

```bash
export TRANSFORMERS_OFFLINE="1"
export HF_HUB_OFFLINE="1" 
export PYTORCH_ENABLE_MPS_FALLBACK="1"  # macOS Metal
```

---

**Total Setup Time:** ~10-15 minutes  
**Environment Size:** ~3-4GB  
**Supported Platforms:** macOS, Linux, Windows