# Cloud Environment Setup for Dora Chatbot

This guide provides a minimal setup for running Dora chatbot nodes on cloud instances without audio hardware. Perfect for server deployments where audio I/O is handled via WebSocket connections.

## Overview

The cloud setup installs only the essential Dora nodes needed for processing, without any audio packages. This is ideal for:

- Cloud VMs (AWS EC2, Google Cloud, Azure)
- Docker containers
- Headless servers
- CI/CD environments

## What's Included

### Nodes Installed
- **dora-asr** - Speech recognition processing (no audio capture)
- **dora-primespeech** - Text-to-speech synthesis (no audio playback)
- **dora-speechmonitor** - Speech detection and segmentation
- **dora-text-segmenter** - Text segmentation for TTS
- **dora-openai-websocket** - WebSocket server for client connections

### What's NOT Included
- Audio capture packages (pyaudio, sounddevice)
- Audio playback packages (portaudio)
- Local microphone/speaker access
- Voice activity detection (webrtcvad)

## Quick Setup

```bash
cd examples/setup-new-chatbot
./setup_cloud_env.sh
```

This creates a conda environment called `dora_cloud` with:
- Python 3.12
- NumPy 1.26.4 (critical version)
- PyTorch CPU-only (smaller footprint)
- All required ML libraries
- WebSocket and networking libraries

## Usage

### 1. Activate Environment
```bash
conda activate dora_cloud
```

### 2. Test Installation
```bash
python test_cloud_nodes.py
```

### 3. Run WebSocket Server
```bash
cd ../../examples/chatbot-with-websocket
cargo run -p dora-openai-websocket
```

The server will listen on port 8123 for WebSocket connections from clients.

### 4. Connect Clients
Clients (like Moly) can connect from anywhere to:
```
ws://your-server-ip:8123
```

## Architecture

```
┌─────────────┐     WebSocket      ┌─────────────────┐
│   Client    │◄──────────────────►│  Cloud Server   │
│   (Moly)    │                     │                 │
│             │                     │  ┌───────────┐  │
│ • Microphone│     Audio In       │  │ dora-asr  │  │
│ • Speaker   │────────────────────►│  └───────────┘  │
│             │                     │        ↓        │
│             │     Audio Out       │  ┌───────────┐  │
│             │◄────────────────────│  │   LLM     │  │
└─────────────┘                     │  └───────────┘  │
                                    │        ↓        │
                                    │  ┌───────────┐  │
                                    │  │primespeech│  │
                                    │  └───────────┘  │
                                    └─────────────────┘
```

## Key Differences from Full Setup

| Feature | Full Setup | Cloud Setup |
|---------|------------|-------------|
| Environment Name | `dora_voice_chat` | `dora_cloud` |
| Audio Packages | ✓ Included | ✗ Excluded |
| PyTorch | Full with CUDA support | CPU-only |
| Disk Space | ~5GB | ~2GB |
| Use Case | Local development | Cloud deployment |

## Deployment Options

### Docker
```dockerfile
FROM continuumio/miniconda3:latest
COPY setup_cloud_env.sh /tmp/
RUN bash /tmp/setup_cloud_env.sh
```

### SystemD Service
```ini
[Unit]
Description=Dora WebSocket Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/dora
ExecStart=/home/ubuntu/miniconda3/envs/dora_cloud/bin/cargo run -p dora-openai-websocket
Restart=always

[Install]
WantedBy=multi-user.target
```

## Performance Optimization

### For Cloud Instances

1. **CPU Optimization**
   ```yaml
   env:
     NUM_THREADS: 4  # Match vCPU count
     USE_GPU: false
   ```

2. **Memory Management**
   - Use smaller models for limited RAM
   - Enable model quantization

3. **Network Optimization**
   - Use compression for WebSocket messages
   - Deploy in same region as clients

## Troubleshooting

### Missing Binary
If `dora-openai-websocket` is not found:
```bash
cd ../../node-hub/dora-openai-websocket
cargo build --release -p dora-openai-websocket
```

### Import Errors
If nodes fail to import:
```bash
conda activate dora_cloud
pip install -e ../../node-hub/dora-asr
pip install -e ../../node-hub/dora-primespeech
# etc...
```

### WebSocket Connection Issues
- Check firewall rules (port 8123)
- Verify server IP is accessible
- Check WebSocket protocol support

## Security Considerations

1. **Use WSS (WebSocket Secure) in production**
2. **Implement authentication for connections**
3. **Use environment variables for API keys**
4. **Run with minimal privileges**
5. **Keep dependencies updated**

## Monitoring

Monitor these metrics:
- CPU usage (ASR/TTS processing)
- Memory usage (model loading)
- Network bandwidth (audio streaming)
- WebSocket connections (concurrent clients)
- Processing latency (end-to-end)

## Scaling

For multiple clients:
1. Use load balancer for WebSocket connections
2. Deploy multiple instances
3. Consider GPU instances for heavy load
4. Use Redis for session management

## Cost Optimization

- Use spot/preemptible instances
- Auto-scale based on connections
- Use ARM instances (Graviton on AWS)
- Enable model caching
- Compress audio streams