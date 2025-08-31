# Claude Context for Dora Cloud Deployment

## Project Overview
Dora is an event-driven robotics framework with voice chat capabilities. This context helps Claude understand the project structure and recent work for cloud deployment.

## Recent Work Summary

### 1. WebSocket Protocol Fixes
- Fixed dora-openai-websocket to properly handle WebSocket protocol
- Added proper close frames (1000, 1002, 1003) to prevent "connection reset" errors
- Implemented ping/pong frame handling
- Fixed InputAudioBufferCommit to not break connections
- Added graceful error recovery for malformed messages

### 2. GPU Support for FunASR
- Added GPU acceleration support for FunASR Chinese ASR engine
- Detects CUDA availability and uses device_id="0" for GPU
- Falls back to CPU (device_id="-1") when GPU unavailable
- Added onnxruntime-gpu as optional dependency
- Configuration: `USE_GPU=true` in environment

### 3. Cloud Environment Setup
- Created minimal setup for cloud instances without audio hardware
- Script: `examples/setup-new-chatbot/setup_cloud_env.sh`
- Environment name: `dora_cloud` with Python 3.12
- Only installs essential nodes: ASR, TTS, speech monitor, text segmenter, WebSocket
- No audio packages (pyaudio, portaudio, sounddevice)
- CPU-only PyTorch for smaller footprint

### 4. Example Configurations

#### chatbot-with-websocket
- WebSocket-based voice chat system
- Template: `whisper-template-metal.yml`
- Dynamically spawns dataflows with unique NODE_ID
- Supports both local (Qwen3) and cloud (MaaS) models

#### chatbot-openai-websocket-browser
- Browser integration with Moly client
- MaaS cloud models with MCP browser tools
- Configuration: `maas_mcp_browser_config.toml`
- Handles initial greetings via text_to_audio input

## Key Files and Locations

### Core Components
```
/dora/
├── node-hub/
│   ├── dora-asr/                    # ASR with FunASR/Whisper
│   ├── dora-primespeech/            # TTS synthesis
│   ├── dora-speechmonitor/          # Speech detection
│   ├── dora-text-segmenter/         # Text segmentation
│   ├── dora-openai-websocket/       # WebSocket server (Rust)
│   └── dora-maas-client/            # Cloud AI integration (Rust)
├── examples/
│   ├── setup-new-chatbot/           # Environment setup scripts
│   │   ├── setup_cloud_env.sh       # Cloud setup (minimal)
│   │   └── test_cloud_nodes.py      # Validation tests
│   ├── chatbot-with-websocket/      # WebSocket examples
│   │   └── whisper-template-metal.yml
│   └── chatbot-openai-websocket-browser/
│       └── whisper-template-metal.yml
```

### Configuration Files
- NumPy version: **1.26.4** (critical for compatibility)
- PyTorch version: **2.2.0** (CPU-only for cloud)
- Python version: **3.12**
- Dora CLI version: **0.3.12** (preferred)

## Common Commands

### Setup Cloud Environment
```bash
cd examples/setup-new-chatbot
./setup_cloud_env.sh
conda activate dora_cloud
```

### Run WebSocket Server
```bash
cd examples/chatbot-with-websocket
cargo run -p dora-openai-websocket
# Server listens on 0.0.0.0:8123
```

### Test Installation
```bash
python test_cloud_nodes.py
```

### Build Rust Components
```bash
# WebSocket server
cd node-hub/dora-openai-websocket
cargo build --release -p dora-openai-websocket

# MaaS client (if needed)
cd node-hub/dora-maas-client
cargo build --release
```

## Dataflow Configuration

### Key Environment Variables
```yaml
# ASR Configuration
ASR_ENGINE: funasr           # or whisper
LANGUAGE: zh                 # or en, auto
USE_GPU: false               # true if GPU available
ASR_MODELS_DIR: /path/to/models

# TTS Configuration  
VOICE_NAME: Doubao
PRIMESPEECH_MODEL_DIR: ~/.dora/models/primespeech
TEXT_LANG: zh
USE_GPU: false

# MaaS Configuration (if using cloud models)
CONFIG: maas_mcp_browser_config.toml
```

### Template Structure
The `whisper-template-metal.yml` uses `NODE_ID` placeholder that gets replaced with unique server ID (e.g., `server-12345`) when client connects.

## Known Issues and Solutions

### Issue: NumPy compatibility
**Solution**: Force install numpy==1.26.4
```bash
pip install numpy==1.26.4 --force-reinstall
```

### Issue: WebSocket connection reset
**Solution**: Already fixed in dora-openai-websocket/src/lib.rs
- Proper close frames
- Ping/pong handling
- Error recovery

### Issue: Models not found
**Solution**: Download models to correct directories
- ASR: `~/.dora/models/asr/`
- TTS: `~/.dora/models/primespeech/`

## Cloud Deployment Notes

### Nodes to Deploy
1. **dora-openai-websocket** - Main WebSocket server
2. **dora-asr** - Speech recognition processing
3. **dora-primespeech** - TTS generation
4. **dora-speechmonitor** - Speech segmentation
5. **dora-text-segmenter** - Text chunking

### Not Needed on Cloud
- Audio capture/playback packages
- GPU support (unless GPU instance)
- Local model files (can use cloud models)

### Network Requirements
- Port 8123 open for WebSocket
- Low latency for real-time audio
- Bandwidth: ~256kbps per client

## Testing Checklist

- [ ] Environment activated: `conda activate dora_cloud`
- [ ] Dependencies installed: `python test_cloud_nodes.py`
- [ ] WebSocket server builds: `cargo build --release -p dora-openai-websocket`
- [ ] Server starts: `cargo run -p dora-openai-websocket`
- [ ] Client can connect to ws://server:8123
- [ ] Audio flows correctly through pipeline
- [ ] Text responses generated and returned

## Quick Debug Commands

```bash
# Check Python environment
which python
python --version

# Check installed nodes
pip list | grep dora

# Check Rust binary
ls -la ../../target/release/dora-openai-websocket

# Test WebSocket connection
websocat ws://localhost:8123

# Monitor logs
tail -f /tmp/dora-*.log
```

## Contact and Resources

- Main repository: Current working directory
- Node hub: `node-hub/` directory
- Examples: `examples/` directory
- Setup scripts: `examples/setup-new-chatbot/`

This context should help you quickly understand and work with the Dora cloud deployment.