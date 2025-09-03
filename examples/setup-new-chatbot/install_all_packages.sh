#!/bin/bash

# Install All Packages Script for Dora Voice Chat
# This script installs all required packages and builds Rust components

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

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}   $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

# Activate conda environment
print_header "Activating Conda Environment"
eval "$(conda shell.bash hook)"
conda activate dora_voice_chat
print_success "Activated conda environment: dora_voice_chat"

# Install Ubuntu/Linux build dependencies
print_header "Installing System Dependencies"
print_info "Installing essential build tools and libraries..."
sudo apt-get update
sudo apt-get install -y gcc gfortran libopenblas-dev build-essential openssl libssl-dev
print_success "System dependencies installed"

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

print_info "Project root: $PROJECT_ROOT"

# Install all Dora packages in editable mode
print_header "Installing Dora Python Packages"
cd "$PROJECT_ROOT"

print_info "Installing dora-primespeech..."
pip install -e node-hub/dora-primespeech
print_success "dora-primespeech installed"

print_info "Installing dora-asr..."
pip install -e node-hub/dora-asr
print_success "dora-asr installed"

print_info "Installing dora-speechmonitor..."
pip install -e node-hub/dora-speechmonitor
print_success "dora-speechmonitor installed"

print_info "Installing dora-text-segmenter..."
pip install -e node-hub/dora-text-segmenter
print_success "dora-text-segmenter installed"

# Install Rust if not already installed
print_header "Setting up Rust"
if command -v cargo &> /dev/null; then
    print_info "Rust is already installed"
    rustc --version
    cargo --version
else
    print_info "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
    print_success "Rust installed successfully"
fi

# Install Dora CLI
print_header "Installing Dora CLI"
if command -v dora &> /dev/null; then
    current_version=$(dora --version 2>&1 | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
    print_info "Dora CLI is already installed (version: $current_version)"
    read -p "Do you want to reinstall/update Dora CLI? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cargo install dora-cli --locked
        print_success "Dora CLI updated"
    fi
else
    print_info "Installing Dora CLI..."
    cargo install dora-cli --locked
    print_success "Dora CLI installed"
fi

# Build Rust-based nodes
print_header "Building Rust Components"
cd "$PROJECT_ROOT"

print_info "Building dora-maas-client..."
cargo build --release -p dora-maas-client
print_success "dora-maas-client built"

print_info "Building dora-openai-websocket..."
cargo build --release -p dora-openai-websocket
print_success "dora-openai-websocket built"

# Summary
print_header "Installation Complete!"
echo -e "${GREEN}All packages have been successfully installed!${NC}"
echo ""
echo "Summary:"
echo "  ✓ System dependencies installed"
echo "  ✓ Python packages installed in editable mode"
echo "  ✓ Rust and Dora CLI installed"
echo "  ✓ Rust components built"
echo ""
echo "Next steps:"
echo "  1. Download models: cd examples/model-manager && python download_models.py --download primespeech"
echo "  2. Configure your OpenAI API key"
echo "  3. Run the WebSocket server: cargo run -p dora-openai-websocket"
echo ""
print_success "Ready to use Dora Voice Chat!"