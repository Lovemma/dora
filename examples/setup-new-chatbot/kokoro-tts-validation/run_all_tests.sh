#!/bin/bash

# Kokoro TTS Validation Test Suite
# Runs all validation tests for dora-kokoro-tts

set -e  # Exit on error

echo "================================================================================"
echo "Kokoro TTS Validation Suite"
echo "================================================================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2

    echo ""
    echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BLUE}Running: ${test_name}${NC}"
    echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    if eval "$test_command"; then
        echo ""
        echo "${GREEN}✓ ${test_name} PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo ""
        echo "${RED}✗ ${test_name} FAILED${NC}"
        ((TESTS_FAILED++))
    fi
}

# Test 1: Direct TTS Test - English
run_test "Direct TTS Test (English)" \
    "python test_tts_direct.py --language en"

# Test 2: Direct TTS Test - Chinese
run_test "Direct TTS Test (Chinese)" \
    "python test_tts_direct.py --language zh"

# Test 3: Check if Dora is available for dataflow test
if command -v dora &> /dev/null; then
    echo ""
    echo "${YELLOW}Note: Dataflow test requires manual intervention${NC}"
    echo "${YELLOW}Skipping automatic dataflow test. To run manually:${NC}"
    echo "${YELLOW}  dora destroy${NC}"
    echo "${YELLOW}  dora up${NC}"
    echo "${YELLOW}  dora start dataflow-static.yml${NC}"
    echo "${YELLOW}  # Wait for completion, then Ctrl+C${NC}"
else
    echo ""
    echo "${YELLOW}Warning: 'dora' command not found. Skipping dataflow test.${NC}"
fi

# Summary
echo ""
echo "================================================================================"
echo "Test Summary"
echo "================================================================================"
echo ""
echo "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

# Check output files
echo "Output Files:"
echo "------------"
if [ -f "tts_output/kokoro_en_output.wav" ]; then
    EN_SIZE=$(du -h "tts_output/kokoro_en_output.wav" | cut -f1)
    echo "${GREEN}✓${NC} tts_output/kokoro_en_output.wav (${EN_SIZE})"
else
    echo "${RED}✗${NC} tts_output/kokoro_en_output.wav (not found)"
fi

if [ -f "tts_output/kokoro_zh_output.wav" ]; then
    ZH_SIZE=$(du -h "tts_output/kokoro_zh_output.wav" | cut -f1)
    echo "${GREEN}✓${NC} tts_output/kokoro_zh_output.wav (${ZH_SIZE})"
else
    echo "${RED}✗${NC} tts_output/kokoro_zh_output.wav (not found)"
fi

echo ""
echo "================================================================================"

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    echo "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo "${RED}Some tests failed!${NC}"
    exit 1
fi
