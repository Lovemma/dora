# Voice Chat Pipeline - Standardized Dependencies

This document defines the standard dependency versions for the Dora voice chat pipeline to ensure compatibility across all nodes.

## 🎯 Core Dependency Standards

### **Python & Core**
```toml
python = ">=3.9,<3.13"
dora-rs = ">=0.3.7"
pyarrow = ">=10.0.0"
```

### **Numerical Computing**
```toml
numpy = ">=1.21.0,<2.0"  # Pin to 1.x for compiled package compatibility
scipy = ">=1.7.0"
```

### **PyTorch Ecosystem** 
```toml
torch = ">=2.0.0,<2.3.0"      # Compatible range for voice nodes
torchaudio = ">=2.0.0,<2.3.0" # Match torch version
torchvision = ">=0.15.0,<0.18.0"  # Compatible with torch range
```

### **Transformers & AI Models**
```toml
transformers = ">=4.40.0,<4.50.0"  # Security compliant (CVE-2025-32434)
huggingface-hub = ">=0.19.0"
```

### **Audio Processing**
```toml
librosa = ">=0.10.0"
soundfile = ">=0.12.0" 
silero-vad = ">=5.1"
```

## 📋 Node-Specific Standards

### **dora-asr**
- Core: numpy, pyarrow, librosa
- Optional GPU: torch, torchaudio, torchvision, onnxruntime-gpu
- ASR: funasr-onnx, pywhispercpp

### **dora-primespeech** 
- Core: numpy, pyarrow, torch, torchaudio, scipy, librosa, soundfile
- NLP: transformers, huggingface-hub, pypinyin, jieba, cn2an
- TTS: pytorch-lightning

### **dora-speechmonitor**
- Core: numpy, pyarrow, torch, torchaudio
- VAD: silero-vad

### **dora-qwen3**
- Core: numpy, pyarrow, transformers, huggingface-hub
- Models: llama-cpp-python, mlx (macOS ARM64)
- Optional: torch, torchaudio, torchvision (for torch models)

### **dora-text-segmenter**
- Core: numpy, pyarrow (minimal dependencies)

## 🔧 Usage in pyproject.toml

```toml
[project]
dependencies = [
    "dora-rs>=0.3.7",
    "numpy>=1.21.0,<2.0",  # Voice chat pipeline standard
    "pyarrow>=10.0.0",
    "transformers>=4.40.0,<4.50.0",  # Voice chat pipeline standard (security compliant)
    # ... other node-specific deps
]

[project.optional-dependencies]
gpu = [
    "torch>=2.0.0,<2.3.0",  # Voice chat pipeline standard
    "torchaudio>=2.0.0,<2.3.0",  # Match torch version range
    "torchvision>=0.15.0,<0.18.0",  # Compatible torchvision range
]
```

## 🚀 Environment Setup

```bash
# Create voice chat environment
conda create -n dora_voice_chat python=3.12
conda activate dora_voice_chat

# Install standardized versions
pip install torch==2.2.0 torchaudio==2.2.0 torchvision==0.17.0
pip install transformers==4.45.0
pip install numpy==1.26.4

# Install voice chat nodes
pip install -e node-hub/dora-asr[gpu]
pip install -e node-hub/dora-primespeech
pip install -e node-hub/dora-speechmonitor
pip install -e node-hub/dora-text-segmenter
pip install -e node-hub/dora-qwen3[torch]
```

## 📝 Notes

- **Security**: transformers <4.50.0 addresses CVE-2025-32434
- **Compatibility**: numpy <2.0 ensures compatibility with compiled packages
- **Performance**: torch <2.3.0 provides stable GPU acceleration
- **Future**: When upgrading, test entire voice pipeline for compatibility

## 🔄 Version Updates

When updating versions, ensure:
1. All voice chat nodes use the same version ranges
2. Full pipeline testing with new versions
3. Update this documentation
4. Test on both CPU and GPU configurations