#!/bin/bash

# Dora Cloud Environment Setup
# Minimal setup for cloud instances without audio hardware
# Focuses on core processing nodes only

set -e  # Exit on error

# Configuration
ENV_NAME="dora_cloud"
PYTHON_VERSION="3.12"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."  # Assumes script is in examples/setup-new-chatbot
NODE_HUB_DIR="$PROJECT_ROOT/node-hub"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
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

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check conda
    if command -v conda &> /dev/null; then
        print_success "Conda found: $(conda --version)"
    else
        print_error "Conda not found. Please install Miniconda or Anaconda"
        echo "Download from: https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi
    
    # Check git
    if command -v git &> /dev/null; then
        print_success "Git found: $(git --version)"
    else
        print_error "Git not found. Please install git"
        exit 1
    fi
    
    # Check cargo (required for Rust nodes)
    if command -v cargo &> /dev/null; then
        print_success "Cargo found: $(cargo --version)"
    else
        print_error "Cargo not found. Required for building Rust nodes"
        echo "Install from: https://rustup.rs/"
        exit 1
    fi
}

# Create conda environment
create_environment() {
    print_header "Creating Conda Environment: $ENV_NAME"
    
    # Check if environment already exists
    if conda env list | grep -q "^$ENV_NAME "; then
        print_warning "Environment '$ENV_NAME' already exists"
        read -p "Do you want to remove and recreate it? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing existing environment..."
            conda env remove -n $ENV_NAME -y
        else
            print_info "Using existing environment"
            return
        fi
    fi
    
    print_info "Creating new conda environment with Python $PYTHON_VERSION..."
    conda create -n $ENV_NAME python=$PYTHON_VERSION -y
    print_success "Environment created successfully"
}

# Install minimal dependencies for cloud
install_cloud_dependencies() {
    print_header "Installing Cloud Dependencies"
    
    # Activate environment
    eval "$(conda shell.bash hook)"
    conda activate $ENV_NAME
    
    print_info "Active Python: $(which python)"
    print_info "Python version: $(python --version)"
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install critical dependencies with specific versions
    print_info "Installing core dependencies..."
    pip install numpy==1.26.4  # Critical for compatibility
    
    # Install PyTorch CPU-only version (smaller, no GPU)
    print_info "Installing PyTorch (CPU-only)..."
    pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu
    
    # Install transformers and related packages
    print_info "Installing ML libraries..."
    pip install transformers==4.36.2
    pip install huggingface-hub==0.17.3
    pip install datasets accelerate sentencepiece protobuf
    
    # Install dora-rs
    print_info "Installing dora-rs..."
    pip install dora-rs==0.3.6
    
    # Install minimal dependencies (no audio)
    print_info "Installing processing libraries..."
    pip install pyarrow scipy librosa
    pip install onnxruntime  # CPU version for cloud
    pip install funasr-onnx  # For ASR processing
    pip install websockets aiohttp requests
    pip install pyyaml toml python-dotenv
    
    # Skip audio packages (pyaudio, portaudio, sounddevice, webrtcvad)
    print_warning "Skipping audio packages (not needed for cloud)"
    
    print_success "Cloud dependencies installed"
}

# Check and link system dora CLI if available
check_dora_cli() {
    print_header "Checking Dora CLI"
    
    # Check for system dora with version 0.3.12
    SYSTEM_DORA=""
    
    # Check common locations
    for dora_path in /usr/local/bin/dora ~/.cargo/bin/dora ~/bin/dora; do
        if [ -f "$dora_path" ]; then
            VERSION=$($dora_path --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "")
            if [ "$VERSION" = "0.3.12" ]; then
                SYSTEM_DORA="$dora_path"
                print_success "Found dora CLI version 0.3.12 at: $dora_path"
                break
            fi
        fi
    done
    
    # Link system dora to environment if found
    if [ -n "$SYSTEM_DORA" ]; then
        ln -sf "$SYSTEM_DORA" "$CONDA_PREFIX/bin/dora"
        print_success "Linked system dora CLI to environment"
    else
        print_warning "Dora CLI version 0.3.12 not found in system"
        print_info "Using dora from pip installation (may be older version)"
    fi
}

# Install minimal Dora nodes for cloud
install_cloud_nodes() {
    print_header "Installing Cloud Dora Nodes"
    
    # List of Python nodes for cloud
    NODES=(
        "dora-asr"
        "dora-primespeech" 
        "dora-speechmonitor"
        "dora-text-segmenter"
    )
    
    for node in "${NODES[@]}"; do
        NODE_PATH="$NODE_HUB_DIR/$node"
        if [ -d "$NODE_PATH" ]; then
            print_info "Installing $node..."
            pip install -e "$NODE_PATH"
            print_success "$node installed"
        else
            print_warning "$node not found at $NODE_PATH"
        fi
    done
    
    # Build Rust node - dora-openai-websocket
    print_info "Building dora-openai-websocket..."
    if [ -d "$NODE_HUB_DIR/dora-openai-websocket" ]; then
        cd "$NODE_HUB_DIR/dora-openai-websocket"
        cargo build --release -p dora-openai-websocket
        print_success "dora-openai-websocket built"
    else
        print_error "dora-openai-websocket not found"
    fi
    
    cd "$SCRIPT_DIR"
}

# Fix numpy compatibility
fix_numpy_compatibility() {
    print_header "Fixing NumPy Compatibility"
    
    print_info "Ensuring numpy 1.26.4 is installed..."
    pip install numpy==1.26.4 --force-reinstall
    
    print_success "NumPy compatibility fixed"
}

# Run cloud-specific tests
run_cloud_tests() {
    print_header "Running Cloud Node Tests"
    
    if [ -f "$SCRIPT_DIR/test_cloud_nodes.py" ]; then
        print_info "Running cloud test suite..."
        python "$SCRIPT_DIR/test_cloud_nodes.py"
    else
        print_warning "Cloud test script not found"
    fi
}

# Print summary
print_summary() {
    print_header "Cloud Setup Complete!"
    
    echo ""
    echo "Environment Name: $ENV_NAME"
    echo "Python Version: $PYTHON_VERSION"
    echo ""
    echo "Installed Nodes:"
    echo "  - dora-asr (Speech recognition)"
    echo "  - dora-primespeech (Text-to-speech)"
    echo "  - dora-speechmonitor (Speech detection)"
    echo "  - dora-text-segmenter (Text segmentation)"
    echo "  - dora-openai-websocket (WebSocket server)"
    echo ""
    echo "To activate the environment:"
    echo "  conda activate $ENV_NAME"
    echo ""
    echo "To run the WebSocket server:"
    echo "  cd $PROJECT_ROOT/examples/chatbot-with-websocket"
    echo "  cargo run -p dora-openai-websocket"
    echo ""
    echo "Note: This is a minimal cloud setup without audio packages."
    echo "Audio I/O is handled via WebSocket connections from clients."
    echo ""
    print_success "Cloud setup completed successfully!"
}

# Main execution
main() {
    print_header "Dora Cloud Environment Setup"
    print_info "Minimal setup for cloud instances without audio hardware"
    
    check_prerequisites
    create_environment
    
    # Activate environment for remaining steps
    eval "$(conda shell.bash hook)"
    conda activate $ENV_NAME
    
    install_cloud_dependencies
    check_dora_cli
    install_cloud_nodes
    fix_numpy_compatibility
    
    # Optional: run tests
    read -p "Do you want to run cloud tests now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_cloud_tests
    fi
    
    print_summary
}

# Run main function
main "$@"