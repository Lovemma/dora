#!/bin/bash
# Comprehensive ASR validation test suite runner

echo "=========================================="
echo "    ASR VALIDATION TEST SUITE"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2 PASSED${NC}"
    else
        echo -e "${RED}❌ $2 FAILED${NC}"
    fi
}

# Track overall status
OVERALL_STATUS=0

# Test 1: Environment Control
echo "1. Testing Environment Variable Control"
echo "----------------------------------------"
python test_gpu_env_control.py
print_status $? "Environment control test"
if [ $? -ne 0 ]; then OVERALL_STATUS=1; fi
echo ""

# Test 2: Basic ASR with CPU
echo "2. Testing Basic ASR (CPU Mode)"
echo "----------------------------------------"
USE_GPU=false python test_basic_asr.py
print_status $? "Basic ASR CPU test"
if [ $? -ne 0 ]; then OVERALL_STATUS=1; fi
echo ""

# Test 3: Basic ASR with GPU
echo "3. Testing Basic ASR (GPU Mode)"
echo "----------------------------------------"
USE_GPU=true python test_basic_asr.py
print_status $? "Basic ASR GPU test"
if [ $? -ne 0 ]; then OVERALL_STATUS=1; fi
echo ""

# Test 4: GPU Switching Validation
echo "4. Testing GPU/CPU Switching"
echo "----------------------------------------"
python validate_gpu_switching.py
print_status $? "GPU switching test"
if [ $? -ne 0 ]; then OVERALL_STATUS=1; fi
echo ""

# Test 5: Performance Benchmark (optional)
echo "5. Performance Benchmark (Optional)"
echo "----------------------------------------"
echo -e "${YELLOW}Run manually with: python benchmark_gpu.py --audio test_audio_chinese.wav${NC}"
echo ""

# Test 6: Check CUDA availability
echo "6. System Check"
echo "----------------------------------------"
python -c "
import torch
import sys
print(f'Python version: {sys.version.split()[0]}')
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA device: {torch.cuda.get_device_name(0)}')
    print(f'CUDA version: {torch.version.cuda}')
"
echo ""

# Test 7: Model availability check
echo "7. Model Availability Check"
echo "----------------------------------------"
MODELS_DIR="$HOME/.dora/models/asr/funasr"
if [ -d "$MODELS_DIR" ]; then
    echo "FunASR models directory exists"
    # Check for specific models
    if [ -d "$MODELS_DIR/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch" ]; then
        echo -e "${GREEN}✅ ASR model found${NC}"
    else
        echo -e "${RED}❌ ASR model not found${NC}"
        OVERALL_STATUS=1
    fi
    if [ -d "$MODELS_DIR/punc_ct-transformer_cn-en-common-vocab471067-large" ]; then
        echo -e "${GREEN}✅ Punctuation model found${NC}"
    else
        echo -e "${YELLOW}⚠️ Punctuation model not found (optional)${NC}"
    fi
else
    echo -e "${RED}❌ Models directory not found: $MODELS_DIR${NC}"
    echo "Please download models first"
    OVERALL_STATUS=1
fi
echo ""

# Summary
echo "=========================================="
echo "           TEST SUMMARY"
echo "=========================================="
if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}All tests PASSED!${NC}"
    echo "ASR system is properly configured and working."
else
    echo -e "${RED}Some tests FAILED${NC}"
    echo "Please check the output above for details."
fi
echo ""

# Provide next steps
echo "Next Steps:"
echo "-----------"
echo "1. Run performance benchmark:"
echo "   python benchmark_gpu.py --audio test_audio_chinese.wav"
echo ""
echo "2. Test with Dora dataflow:"
echo "   dora start dataflow_gpu.yml   # For GPU mode"
echo "   dora start dataflow_cpu.yml   # For CPU mode"
echo ""
echo "3. Check logs:"
echo "   cat transcription_log.txt"
echo ""

exit $OVERALL_STATUS