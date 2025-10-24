# macOS Voice Chat Dataflows

> **Prerequisite:** Before running these flows, create and activate the `dora_voice_chat` conda environment via `examples/setup-new-chatbot/setup_isolated_env.sh`. All terminals used during the commands below must run `conda activate dora_voice_chat` first so they share the same dependencies.

Three turnkey dataflows live in this directory. Each combines acoustic echo cancellation (AEC), speech recognition, an LLM or MaaS service, and a text-to-speech (TTS) backend. This document summarises the available nodes, explains how each dataflow is wired, and lists the exact commands you need to launch them.

---

## 1. Node Inventory

| Node ID | Role & Implementation | Key Inputs | Outputs |
|---------|----------------------|-----------|---------|
| `mac-aec` (dynamic) | Wraps `mac_aec_simple_segmentation.py`. Calls the macOS hardware acoustic echo cancellation API, which taps the system microphone and speaker loopback, produces an echo-cleaned stream, performs VAD, and segments speech into questions. | (implicit) mic/speaker capture | `audio`, `audio_segment`, `is_speaking`, `speech_started`, `speech_ended`, `question_ended`, `log` |
| `asr` | `node-hub/dora-asr` (FunASR + optional Whisper). Converts `audio_segment` into text plus metadata. | `audio` (16 kHz float32) | `transcription`, `language_detected`, `processing_time`, `confidence`, `log` |
| `qwen3-llm` | `node-hub/dora-qwen3`. Local MLX execution of Qwen3; used only in `voice-chat-with-aec.yml`. | `text` (ASR output) | `text`, `status`, `log` |
| `maas-client` | Prebuilt binary `dora-maas-client`. Streams ASR text to an external MaaS provider (OpenAI-compatible) and yields responses. | `text` | `text`, `status`, `log` |
| `text-segmenter` | `node-hub/dora-text-segmenter`. Buffers LLM/MaaS output, cuts it into short sentences, and respects `segment_complete` backpressure. | `text`, `tts_complete`, optional `reset` | `text_segment`, `status`, `metrics`, `log` |
| `primespeech` | `node-hub/dora-primespeech`. GPT-SoVITS based TTS. Emits 32 kHz float32 audio. | `text_segment` | `audio`, `segment_complete`, `log` |
| `kokoro-tts` | `node-hub/dora-kokoro-tts`. Fast multilingual TTS. Emits 24 kHz float32 audio. | `text_segment` | `audio`, `segment_complete`, `log` |
| `audio-player` (dynamic) | `audio_player.py`. Circular-buffer playback with smart resets. Accepts the TTS audio stream and plays it through CoreAudio. | `audio`, `control` | `buffer_status`, `status` |
| `viewer` (dynamic) | `viewer.py`. Renders time-aligned transcription, LLM/MaaS output, segmentation events, and aggregated log messages from all nodes (MAC-AEC, ASR, LLM/MaaS, Segmenter, TTS) with color-coded output (🎙️ 🎤 🤖 🧠 ✂️ 🔊 🗣️) for debugging. | `transcription`, `llm_output`, `segment`, `speech_*`, `*_log` (all nodes) | none |

**Sampling rates**

- PrimeSpeech emits 32 kHz audio. Start the player with `--sample-rate 32000` so CoreAudio consumes it at the correct speed.
- Kokoro emits 24 kHz audio. Start the player with `--sample-rate 24000` (the player can auto-adjust, but an explicit rate avoids resampling artifacts).

**Model setup**

Install node packages and download models once with the model manager:

```bash
# install nodes
pip install -e ../../node-hub/dora-asr
pip install -e ../../node-hub/dora-qwen3
pip install -e ../../node-hub/dora-text-segmenter
pip install -e ../../node-hub/dora-primespeech
pip install -e ../../node-hub/dora-kokoro-tts

# download models (from examples/model-manager/)
python download_models.py --download funasr
python download_models.py --download primespeech
python download_models.py --download Qwen/Qwen3-8B-MLX-4bit
python download_models.py --download kokoro
```

PrimeSpeech assets live in `~/.dora/models/primespeech`; Kokoro base files and voices live in `~/.dora/models/kokoro` and the Hugging Face cache for `hexgrad/Kokoro-82M`. Use `--remove` flags (e.g. `--remove kokoro`) if you need to clear them.

---

## 2. Dataflows

Each dataflow lives in the `voice-chat-with-*.yml` files. In every case you must run the static graph via `dora start …` and then launch the three dynamic processes (`mac_aec_simple_segmentation.py`, `audio_player.py`, `viewer.py`) in separate terminals.

### 2.1 `voice-chat-with-aec.yml` — Local Qwen3 + PrimeSpeech

**Flow**

```
microphone → mac-aec → asr → qwen3-llm → text-segmenter → primespeech → audio-player
```

- Qwen3 (MLX) runs locally; no external API calls.
- PrimeSpeech converts the segmented text to 32 kHz float32 audio.

**Launch sequence**

1. **Terminal 1** – activate the environment, stop old runs, and start the dataflow:
   ```bash
   conda activate dora_voice_chat
   dora stop
   dora start voice-chat-with-aec.yml
   ```
2. **Terminal 2** – activate the environment and start the dynamic MAC-AEC wrapper:
   ```bash
   conda activate dora_voice_chat
   python mac_aec_simple_segmentation.py
   ```
3. **Terminal 3** – activate the environment and launch the audio player at 32 kHz:
   ```bash
   conda activate dora_voice_chat
   python audio_player.py --sample-rate 32000
   ```
4. **Terminal 4 (optional)** – activate the environment and open the viewer:
   ```bash
   conda activate dora_voice_chat
   python viewer.py
   ```

### 2.2 `voice-chat-with-aec-maas.yml` — MaaS LLM + PrimeSpeech

**Flow**

```
microphone → mac-aec → asr → maas-client → text-segmenter → primespeech → audio-player
```

- `maas-client` streams recognition results to your configured cloud LLM and returns text.
- PrimeSpeech again produces 32 kHz output.

**Launch sequence**

1. **Terminal 1**
    ```bash
    conda activate dora_voice_chat
    # LLM credentials forwarded through the MaaS node env block
    export OPENAI_API_KEY="your-openai-key"          # needed for OpenAI routes
    export ALIBABA_CLOUD_API_KEY="your-alicloud-key" # needed for Qwen / DeepSeek / Moonshot routes
    dora stop
    dora start voice-chat-with-aec-maas.yml
    ```
2. **Terminal 2**
   ```bash
   conda activate dora_voice_chat
   python mac_aec_simple_segmentation.py
   ```
3. **Terminal 3**
   ```bash
   conda activate dora_voice_chat
   python audio_player.py --sample-rate 32000
   ```
4. **Terminal 4 (optional)**
   ```bash
   conda activate dora_voice_chat
   python viewer.py
   ```

### 2.3 `voice-chat-with-aec-maas-kokoro.yml` — MaaS LLM + Kokoro

**Flow**

```
microphone → mac-aec → asr → maas-client → text-segmenter → kokoro-tts → audio-player
```

- Identical front half to the MaaS pipeline above.
- Swaps PrimeSpeech for Kokoro (24 kHz) to reduce latency and support multilingual voices.

**Launch sequence**

1. **Terminal 1**
    ```bash
    conda activate dora_voice_chat
    export OPENAI_API_KEY="your-new-key"
    dora stop
    dora start voice-chat-with-aec-maas-kokoro.yml
    ```
2. **Terminal 2**
   ```bash
   conda activate dora_voice_chat
   python mac_aec_simple_segmentation.py
   ```
3. **Terminal 3** – activate the environment and note the 24 kHz sample rate:
   ```bash
   conda activate dora_voice_chat
   python audio_player.py --sample-rate 24000
   ```
4. **Terminal 4 (optional)**
   ```bash
   conda activate dora_voice_chat
   python viewer.py
   ```

The audio player will adapt to the rate advertised in the TTS metadata, but supplying the explicit value avoids momentary resets when the first buffer arrives.

---

## 3. Viewer & Logging

The `viewer.py` script aggregates logs from all nodes in the pipeline and displays them with:
- **Timestamps**: Every event is timestamped for debugging timing issues
- **Color coding**:
  - ❌ RED for ERROR messages
  - ⚠️ YELLOW for WARNING messages
  - CYAN for INFO messages
  - DEBUG messages are filtered out by default
- **Node-specific icons**:
  - 🎙️ MAC-AEC (audio capture & speech detection)
  - 🎤 ASR (speech recognition)
  - 🤖 MAAS / 🧠 QWEN3 (LLM reasoning)
  - ✂️ SEGMENTER (text segmentation)
  - 🔊 KOKORO / 🗣️ PRIMESPEECH (text-to-speech)

**Example output:**
```
[15:32:45] 🎙️ MAC-AEC: [INFO] Speech Monitor initialized
[15:32:46] 🎤 ASR: [INFO] FunASR models loaded successfully
[15:32:47] 🧠 QWEN3: [INFO] Model loaded successfully
[15:32:48] ✂️ SEGMENTER: [INFO] Text Segmenter started
[15:32:49] 🗣️ PRIMESPEECH: [INFO] Using MoYoYo TTS implementation
[15:32:50] 🎤 USER: 你好
[15:32:51] 🤖 ASSISTANT: 你好！有什么可以帮助你的吗？
[15:32:52] 🔊 TTS: Speaking: '你好！有什么可以帮助你的吗？'
```

All nodes implement structured logging that respects the `LOG_LEVEL` environment variable (DEBUG, INFO, WARNING, ERROR). Set `LOG_LEVEL=DEBUG` in the YAML files to see detailed execution traces.

---

## 4. Tips & Troubleshooting

- **Always stop old flows** before starting a new one; `dora stop` without arguments stops any active session.
- **Dynamic nodes must stay running**. If the AEC script or audio player exits, the dataflow will stall.
- **Viewer** displays transcription, segment timing, and each node’s logs in chronological order—use it to diagnose alignment issues or see how backpressure behaves.
- **PrimeSpeech models** live under `~/.dora/models/primespeech`; **Kokoro** expects `~/.dora/models/kokoro` plus the Hugging Face cache of `hexgrad/Kokoro-82M` for offline mode.
- **Audio formats** are float32: PrimeSpeech at 32 kHz, Kokoro at 24 kHz. Downstream nodes should not assume PCM16.

Enjoy building on the Dora AEC voice pipelines!
