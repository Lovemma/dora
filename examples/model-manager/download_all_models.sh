#!/bin/bash

# Download All Models Script for Dora Voice Chat
# This script downloads all required models for ASR and TTS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}   $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

# Check if conda environment is activated
check_conda_env() {
    if [[ -z "$CONDA_DEFAULT_ENV" ]]; then
        print_warning "No conda environment is activated."
        print_info "Please activate the dora_voice_chat environment:"
        echo "    conda activate dora_voice_chat"
        echo ""
        read -p "Do you want to continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "Conda environment activated: $CONDA_DEFAULT_ENV"
    fi
}

# Check Python availability
check_python() {
    if command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1)
        print_success "Python found: $PYTHON_VERSION"
    else
        print_error "Python not found. Please ensure Python is installed."
        exit 1
    fi
}

# Main function
main() {
    print_header "Dora Model Downloader - All-in-One Script"
    
    # Check prerequisites
    check_conda_env
    check_python
    
    # Get the script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    cd "$SCRIPT_DIR"
    
    # Total steps counter
    TOTAL_STEPS=4
    CURRENT_STEP=0
    
    # Step 1: Download FunASR models
    CURRENT_STEP=$((CURRENT_STEP + 1))
    print_header "[$CURRENT_STEP/$TOTAL_STEPS] Downloading FunASR Models"
    print_info "Downloading ASR models for speech recognition..."
    if python download_models.py --download funasr; then
        print_success "FunASR models downloaded successfully"
    else
        print_error "Failed to download FunASR models"
        exit 1
    fi
    
    # Step 2: Download PrimeSpeech complete package
    CURRENT_STEP=$((CURRENT_STEP + 1))
    print_header "[$CURRENT_STEP/$TOTAL_STEPS] Downloading PrimeSpeech TTS Package"
    print_info "Downloading base models, G2PW, and all voice files..."
    if python download_models.py --download primespeech; then
        print_success "PrimeSpeech package downloaded successfully"
    else
        print_error "Failed to download PrimeSpeech package"
        exit 1
    fi
    
    # Step 3: List downloaded models
    CURRENT_STEP=$((CURRENT_STEP + 1))
    print_header "[$CURRENT_STEP/$TOTAL_STEPS] Verifying Downloaded Models"
    print_info "Checking all downloaded models..."
    python download_models.py --list
    
    # Step 4: ONNX Conversion (Optional)
    CURRENT_STEP=$((CURRENT_STEP + 1))
    print_header "[$CURRENT_STEP/$TOTAL_STEPS] ONNX Model Conversion (Optional)"
    print_info "Converting models to ONNX format can improve performance."
    echo ""
    read -p "Do you want to convert models to ONNX format? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Converting models to ONNX format..."
        if python convert_to_onnx.py --convert all; then
            print_success "ONNX conversion completed successfully"
        else
            print_warning "ONNX conversion failed or partially completed"
            print_info "This is optional - the models will still work without ONNX conversion"
        fi
    else
        print_info "Skipping ONNX conversion"
    fi
    
    # Summary
    print_header "Download Complete!"
    
    echo -e "${GREEN}All models have been successfully downloaded!${NC}"
    echo ""
    echo "Summary:"
    echo "  ✓ FunASR models for speech recognition"
    echo "  ✓ PrimeSpeech base models (Chinese Hubert & Roberta)"
    echo "  ✓ G2PW model for text processing"
    echo "  ✓ All voice files for TTS"
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  ✓ ONNX conversion completed"
    fi
    echo ""
    echo "Model locations:"
    echo "  ASR models:        ~/.dora/models/asr/"
    echo "  PrimeSpeech models: ~/.dora/models/primespeech/"
    echo ""
    echo "Next steps:"
    echo "  1. Configure your OpenAI API key in the TOML config"
    echo "  2. Run validation tests to ensure everything works"
    echo "  3. Start the WebSocket server: cargo run -p dora-openai-websocket"
    echo ""
    print_success "Ready to use Dora Voice Chat!"
}

# Run main function
main "$@"