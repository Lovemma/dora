# ASR Validation Quick Start Guide

## 🚀 Quick Test (2 minutes)

Run this single command to test if ASR is working:

```bash
# Test with current GPU setting
python test_basic_asr.py
```

Expected output:
```
============================================================
Basic ASR Test (USE_GPU=false)
============================================================
...
Transcription:
  你好吗？请你告诉我怎么坐公共汽车去北京动物园？请你告诉我梅菜扣肉怎么做和涮羊？怎么做？
...
✅ Transcription quality: GOOD (contains expected phrases)
```

## 🔧 Complete Validation (5 minutes)

Run all tests to validate your setup:

```bash
./run_all_tests.sh
```

This will:
1. ✅ Test environment variable control
2. ✅ Test CPU mode transcription
3. ✅ Test GPU mode transcription (if available)
4. ✅ Validate GPU/CPU switching
5. ✅ Check system configuration
6. ✅ Verify model availability

## ⚡ GPU vs CPU Comparison

### Quick Benchmark
```bash
# Compare CPU and GPU performance
python benchmark_gpu.py --audio test_audio_chinese.wav
```

### Expected Results (RTX 4090)
| Mode | Time | Speed | Command |
|------|------|-------|---------|
| CPU | 0.64s | 27x real-time | `USE_GPU=false python test_basic_asr.py` |
| GPU | 0.28s | 62x real-time | `USE_GPU=true python test_basic_asr.py` |

**Result**: 2.27x faster with GPU! 🚀

## 📊 Test Individual Components

### 1. Test Environment Control
```bash
python test_gpu_env_control.py
```

### 2. Test CPU Mode
```bash
USE_GPU=false python test_basic_asr.py
```

### 3. Test GPU Mode
```bash
USE_GPU=true python test_basic_asr.py
```

### 4. Test with Dora Dataflow
```bash
# GPU mode
dora start dataflow_gpu.yml

# CPU mode
dora start dataflow_cpu.yml
```

## 🔍 Check Your Setup

### GPU Availability
```bash
python -c "import torch; print(f'GPU: {torch.cuda.is_available()}')"
```

### Model Files
```bash
ls -lh ~/.dora/models/asr/funasr/
```

### ASR Package
```bash
pip show dora-asr
```

## 📝 Configuration Options

Set these environment variables to control ASR behavior:

```bash
# Enable GPU (default: false)
export USE_GPU=true

# Select engine (funasr/whisper/auto)
export ASR_ENGINE=funasr

# Set language (zh/en/auto)
export LANGUAGE=zh

# Run with custom settings
python test_basic_asr.py
```

## 🎯 Common Use Cases

### Chinese Speech Recognition (Fastest)
```bash
USE_GPU=true ASR_ENGINE=funasr LANGUAGE=zh python test_basic_asr.py
```

### English Speech Recognition
```bash
ASR_ENGINE=whisper LANGUAGE=en python test_basic_asr.py
```

### Auto-detect Language
```bash
ASR_ENGINE=auto LANGUAGE=auto python test_basic_asr.py
```

## ❓ Troubleshooting

### Issue: "No GPU detected"
```bash
# Check CUDA
nvidia-smi
# Install PyTorch with CUDA
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Issue: "Models not found"
```bash
# Download models
cd ../../model-manager
python download_models.py --model funasr
```

### Issue: "Transcription is empty"
```bash
# Check audio file
python -c "import librosa; audio, sr = librosa.load('test_audio_chinese.wav'); print(f'Duration: {len(audio)/sr:.2f}s')"
```

## 📈 Performance Tips

1. **Use GPU for Chinese**: FunASR with GPU gives best performance
2. **Batch processing**: Process multiple files together
3. **Model selection**: FunASR for Chinese, Whisper for English
4. **Memory**: GPU mode uses ~2GB VRAM

## 🎉 Success Criteria

Your ASR setup is working if:
- ✅ `test_basic_asr.py` produces correct transcription
- ✅ GPU mode is faster than CPU mode (when GPU available)
- ✅ All tests in `run_all_tests.sh` pass
- ✅ Dataflow examples work without errors

## 📚 Next Steps

1. **Integrate into your project**:
   ```python
   from dora_asr.manager import ASRManager
   manager = ASRManager()
   result = manager.transcribe(audio_data)
   ```

2. **Customize for your needs**:
   - Edit dataflow YAML files
   - Adjust environment variables
   - Add custom preprocessing

3. **Deploy to production**:
   - Use GPU for best performance
   - Monitor memory usage
   - Set up logging

## 🆘 Get Help

- Check the full [README.md](README.md) for detailed documentation
- Review [GPU_ENHANCEMENTS.md](../../../node-hub/dora-asr/GPU_ENHANCEMENTS.md) for GPU details
- Run `python test_basic_asr.py --help` for options

---
*Last updated: 2024*