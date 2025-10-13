# Voice Assistant Architecture (macOS AEC Pipelines)

This repository holds three Dora dataflows that combine acoustic echo cancellation, speech recognition, LLM/MaaS reasoning, and text-to-speech playback. The pipelines share most building blocks; the primary differences are which reasoning backend is used (local Qwen3 versus external MaaS) and which TTS (PrimeSpeech or Kokoro) delivers the final audio. This document describes every node, how the flows are wired, and key runtime properties such as audio formats.

---

## 1. Node Layering

| Layer | Node ID | Implementation | Key Inputs | Outputs | Notes |
|-------|---------|----------------|------------|---------|-------|
| Audio Capture & Echo Cancellation | `mac-aec` (dynamic) | `mac_aec_simple_segmentation.py` wrapping `dora-aec` | microphone | `audio`, `audio_segment`, `is_speaking`, `speech_started`, `speech_ended`, `question_ended`, `log` | Runs acoustic echo cancellation, drains the native buffer every 10 ms, segments speech, and emits question IDs. Audio format: 16 kHz float32. |
| Speech Recognition | `asr` | `node-hub/dora-asr` (FunASR + optional Whisper) | `audio_segment` | `transcription`, `language_detected`, `processing_time`, `confidence`, `log` | Queue size 10. Default language `zh`, punctuation restored in-line. |
| Reasoning (local) | `qwen3-llm` | `node-hub/dora-qwen3` (MLX) | `transcription` | `text`, `status`, `log` | Used only in `voice-chat-with-aec.yml`. Streams partial tokens as soon as they are decoded. |
| Reasoning (MaaS) | `maas-client` | `../../target/release/dora-maas-client` | `transcription` | `text`, `status`, `log` | Present in the two `*-maas*.yml` flows. Connects to an external LLM via Playwright/browser automations. |
| Text Buffering | `text-segmenter` | `node-hub/dora-text-segmenter` | `text`, `tts_complete`, `reset` | `text_segment`, `metrics`, `status`, `log` | Maintains a queue per question, slices streaming text into short sentences (default 5–20 chars), and honours backpressure via `segment_complete`. |
| TTS (PrimeSpeech) | `primespeech` | `node-hub/dora-primespeech` | `text_segment` | `audio`, `segment_complete`, `log` | GPT-SoVITS Doubao voice by default. Emits 32 kHz float32 buffers. |
| TTS (Kokoro) | `kokoro-tts` | `node-hub/dora-kokoro-tts` | `text_segment` | `audio`, `segment_complete`, `log` | Streaming-capable Kokoro pipeline. Auto-detects Chinese text and switches voices. Output is 24 kHz float32. |
| Playback | `audio-player` (dynamic) | `audio_player.py` | `audio`, `control` | `buffer_status`, `status` | Circular buffer with smart resets keyed to `question_ended`. Accepts runtime `--sample-rate` and can auto-adjust to TTS metadata. |
| Monitoring | `viewer` (dynamic) | `viewer.py` | `transcription`, `llm_output`, `segment`, `speech_started`, `speech_ended`, `mac_aec_log`, `asr_log`, `maas_log`/`qwen3_log`, `segmenter_log`, `kokoro_log`/`primespeech_log` | — | Consolidates transcription, segment timing, and per-node logs (INFO/WARNING/ERROR) in chronological order with color-coded output and node-specific icons. |

**Audio formats**

- PrimeSpeech → 32 kHz mono float32. Start the player with `python audio_player.py --sample-rate 32000` to avoid resampling.
- Kokoro → 24 kHz mono float32. Use `python audio_player.py --sample-rate 24000` when running the Kokoro flow.

Dynamic nodes (`mac-aec`, `audio-player`, `viewer`) do **not** inherit environment variables from the YAML files; update defaults directly in the Python scripts if you need to change parameters such as silence thresholds.

---

## 2. Dataflow Topologies

All three flows follow the same backbone: capture speech → recognise text → stream responses → segment text → synthesise → play audio. The diference lies in the reasoning node and the TTS backend.

### 2.1 Local Qwen3 + PrimeSpeech (`voice-chat-with-aec.yml`)

```
microphone
  │
  ▼
mac-aec  ──segment→  asr  ──text→  qwen3-llm  ──chunks→  text-segmenter  ──segments→  primespeech  ──audio→  audio-player
  │              │                             │                              │
  └──events──────┴──────────────────────────────┴──────────────────────────────┴──backpressure (segment_complete)
```

- Qwen3 runs locally using MLX on Apple Silicon; responses are streamed token-by-token.
- PrimeSpeech converts every segment to 32 kHz audio and acknowledges via `segment_complete`.
- Feedback: `question_ended` from `mac-aec` resets the segmenter queue and clears the player buffer; `segment_complete` throttles upstream output.

### 2.2 MaaS LLM + PrimeSpeech (`voice-chat-with-aec-maas.yml`)

```
mac-aec → asr → maas-client → text-segmenter → primespeech → audio-player
```

- Identical front end; the reasoning node is the MaaS client, which emits streaming text from your configured provider.
- PrimeSpeech remains the TTS stage at 32 kHz.

### 2.3 MaaS LLM + Kokoro (`voice-chat-with-aec-maas-kokoro.yml`)

```
mac-aec → asr → maas-client → text-segmenter → kokoro-tts → audio-player
```

- Same ASR + MaaS arrangement as the previous flow.
- Kokoro performs low-latency TTS at 24 kHz. The audio player should be started with the matching sample rate to avoid playback speed changes.

---

## 3. Launch Sequence

Each dataflow requires four terminals: one for Dora itself and three for the dynamic nodes.

1. **Terminal 1 – start/stop Dora graph**
   ```bash
   dora stop
   dora start <dataflow-yaml>
   ```
2. **Terminal 2 – start AEC capture**
   ```bash
   python mac_aec_simple_segmentation.py
   ```
3. **Terminal 3 – start audio playback**
   ```bash
   # PrimeSpeech flows
   python audio_player.py --sample-rate 32000

   # Kokoro flow
   python audio_player.py --sample-rate 24000
   ```
4. **Terminal 4 (optional) – open the viewer**
   ```bash
   python viewer.py
   ```

The viewer renders a time-series dashboard of transcription, LLM/MaaS output, segmentation events, and per-node logs, which is invaluable for diagnosing backpressure or timing issues.

---

## 4. Logging Architecture

All nodes implement unified structured logging that outputs to dedicated `log` channels:

**Log Message Format:**
```json
{
  "node": "primespeech",
  "level": "INFO",
  "message": "[INFO] Using MoYoYo TTS implementation",
  "timestamp": 1234567890.123
}
```

**Log Levels:**
- **DEBUG**: Detailed execution traces (filtered by default in viewer)
- **INFO**: Standard operational messages
- **WARNING**: Non-critical issues that don't stop execution
- **ERROR**: Critical failures with tracebacks

**Logging Implementation:**
- **Python nodes with Dora context** (runtime): Use `send_log(node, level, message, config_level)` which outputs to both console and Dora log channel
- **Python modules at import time**: Use standard `logging` module (console only, before node starts)
- **Rust nodes**: Implement equivalent structured logging to Dora channels

**Environment Control:**
All nodes respect the `LOG_LEVEL` environment variable in their YAML configuration. Set to `DEBUG` for detailed traces:
```yaml
env:
  LOG_LEVEL: DEBUG  # DEBUG, INFO, WARNING, ERROR
```

**Viewer Integration:**
The viewer aggregates logs from all nodes and displays them with:
- Timestamps for every event
- Color coding (❌ RED for errors, ⚠️ YELLOW for warnings, CYAN for info)
- Node-specific icons (🎙️ 🎤 🤖 🧠 ✂️ 🔊 🗣️)

This centralized logging makes debugging pipeline issues much easier, as all node activity is visible in a single chronological stream.

---

## 5. Internal Communication & Backpressure

- `mac-aec` sends `question_ended` to both the text segmenter and audio player to flush stale data whenever the user pauses for the configured duration (default ≈600 ms silence).
- `text-segmenter` defers sending the next chunk until it receives `segment_complete` from the active TTS node, preventing audio overlap.
- `audio-player` publishes `buffer_status` continuously; downstream consumers (for example the viewer) can react if the buffer underruns.
- All TTS audio is streamed as `pa.array([numpy_array])` so Arrow preserves the whole chunk; downstream nodes must convert back to NumPy (`value[0].as_py()`).

---

## 6. Key Implementation Notes

1. **MAC-AEC wrapper**
   - Drains native buffers in a tight loop (otherwise 97 % of audio frames are lost).
   - Polls every 10 ms to enforce accurate silence timing.
   - Converts int16 PCM → float32 before publishing.

2. **ASR**
   - FunASR models live under `~/.dora/models/asr` by default; `ASR_MODELS_DIR` can be set for custom locations.

3. **TTS model storage**
   - PrimeSpeech: `~/.dora/models/primespeech` plus placeholders for GPT/SoVITS weights and reference audio.
   - Kokoro: `~/.dora/models/kokoro` for `config.json`, `kokoro-v1_0.pth`, and `voices/*.pt`; the Hugging Face cache (`~/.cache/huggingface/hub/hexgrad--Kokoro-82M`) is kept warm during downloads for offline use.

4. **Audio player**
   - Automatically rebuilds its buffer if incoming metadata reports a different `sample_rate`, but passing the correct rate on the command line prevents transient underruns.

---

## 7. Extending the Pipelines

- Swap in alternative LLMs by editing the YAML to point to another reasoning node (e.g. a local GGUF model) while reusing `text-segmenter` and the chosen TTS.
- To experiment with other voices, download them via the model manager (`python ../model-manager/download_models.py --voice <PrimeSpeechVoice>` or `--kokoro-voice <voice>`).
- The viewer is modular—extend it to display additional metrics (e.g. ASR confidence, MaaS latency) by subscribing to the relevant outputs.

These architectural notes should help you understand and modify the macOS AEC voice assistant flows without re-reading the node implementations.
