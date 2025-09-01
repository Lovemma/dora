# Setup New Dora Chatbot Environment

This directory provides a comprehensive setup script for creating an isolated Python environment for all Dora chatbot examples. It ensures compatibility and avoids conflicts with existing Python installations.

## What This Setup Does

1. **Creates an isolated conda environment** with Python 3.12
2. **Installs all required dependencies** with standardized versions
3. **Installs all Dora nodes** from the node-hub directory with consistent dependency ranges
4. **Ensures compatibility** across all voice chat pipeline nodes
5. **Links system dora CLI** if available (version 0.3.12)
6. **Builds Rust nodes** if cargo is installed
7. **Runs validation tests** to ensure everything works

📋 **For detailed dependency information, see [DEPENDENCIES.md](./DEPENDENCIES.md)**

## Prerequisites

1. **Conda** (Miniconda or Anaconda)
   - Download from: https://docs.conda.io/en/latest/miniconda.html
   - Verify: `conda --version`

2. **Git** 
   - Required for installing Python packages from GitHub

3. **Cargo** (Optional)
   - Required only for building Rust nodes (dora-maas-client, dora-openai-websocket)
   - Install from: https://rustup.rs/

## Quick Setup

```bash
cd examples/setup-new-chatbot
./setup_isolated_env.sh
```

The script will:
- Check prerequisites
- Create a new conda environment called `dora_voice_chat`
- Install all dependencies
- Install all Dora nodes
- Run tests (optional)

## What Gets Installed

### Python Nodes
- `dora-asr` - Automatic Speech Recognition
- `dora-primespeech` - Text-to-Speech synthesis
- `dora-qwen3` - Local LLM support
- `dora-text-segmenter` - Text segmentation for TTS
- `dora-speechmonitor` - Speech detection and monitoring

### Rust Nodes (if cargo available)
- `dora-maas-client` - Cloud AI integration
- `dora-openai-websocket` - WebSocket server for real-time communication

### Key Dependencies (Standardized)
- `numpy>=1.21.0,<2.0` - Pin to 1.x for compiled package compatibility
- `torch>=2.0.0,<2.3.0` - PyTorch ecosystem (voice pipeline standard)
- `transformers>=4.40.0,<4.50.0` - Security compliant (CVE-2025-32434 fix)
- `dora-rs>=0.3.7` - Dora Python bindings

📋 **For complete dependency specifications, see [DEPENDENCIES.md](./DEPENDENCIES.md)**

## After Setup

### Activate the Environment
```bash
conda activate dora_voice_chat
```

### Test the Installation
```bash
python test_dependencies.py
```

### Run Examples

#### MAC-AEC Chat
```bash
cd ../../examples/mac-aec-chat
dora up
dora start voice-chat-with-aec.yml
```

#### WebSocket Chat
```bash
cd ../../examples/chatbot-with-websocket
cargo run -p dora-openai-websocket
# Then connect with Moly client to ws://localhost:8123
```

#### Browser WebSocket Chat
```bash
cd ../../examples/chatbot-openai-websocket-browser
cargo run -p dora-openai-websocket
# Open Moly and connect to ws://localhost:8123
```

## Troubleshooting

### NumPy Version Conflicts
The script automatically installs numpy 1.26.4. If you see numpy-related errors:
```bash
pip install numpy==1.26.4 --force-reinstall
```

### Dora CLI Version
The script will try to link system dora CLI (version 0.3.12). If not found, it uses the pip-installed version.

### Model Downloads
Models need to be downloaded separately:
- ASR models: Will download automatically on first use
- PrimeSpeech models: Place in `~/.dora/models/primespeech`

### Permission Errors
If you get permission errors, make sure the script is executable:
```bash
chmod +x setup_isolated_env.sh
```

## Manual Installation

If you prefer manual installation, see `manual_install.sh` for step-by-step commands.

## Testing

Run the test suite to validate all nodes:
```bash
python tests/run_all_tests.py
```

Individual node tests:
```bash
python tests/test_dora_asr.py
python tests/test_dora_primespeech.py
python tests/test_dora_qwen3.py
python tests/test_dora_text_segmenter.py
```

## Environment Details

- **Environment Name**: `dora_voice_chat`
- **Python Version**: 3.12
- **NumPy Version**: 1.26.4 (critical for compatibility)
- **PyTorch Version**: 2.2.0
- **Dora Version**: 0.3.6 (Python), 0.3.12 (CLI preferred)

## Notes

- The environment is completely isolated from system Python
- All nodes are installed in development mode (`pip install -e`)
- Rust nodes require cargo to build
- The setup handles all known compatibility issues automatically