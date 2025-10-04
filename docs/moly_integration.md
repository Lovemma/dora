Moly Integration (OpenAI Realtime 09‑05)

Overview
- Client: https://github.com/moxin-org/moly (Rust)
- Protocol: OpenAI Realtime 2024‑09‑05 WebSocket
- Server: `node-hub/dora-openai-websocket` (Rust)
- Dataflow: Dora pipeline for VAD/ASR/LLM/TTS

Key Expectations
- Session setup via `session.update` from moly; server replies `session.created` and `session.updated`.
- Greeting is client‑initiated with a single `response.create` (optional).
- Subsequent user turns rely on server‑side VAD (server_vad): server detects `question_ended` and triggers a new turn by sending:
  1) `input_audio_buffer.committed`
  2) `response.create`

End‑to‑End Event Sequence
1) Connect: WebSocket upgrade; moly sends `session.update` (may include turn_detection.server_vad).
2) Server ack: `session.created` then `session.updated`.
3) Optional greeting: moly sends `response.create { instructions }` once.
4) Live audio: moly streams `input_audio_buffer.append` frames.
5) Turn end: Dora Speech Monitor emits `question_ended`.
6) Server trigger: server sends `input_audio_buffer.committed` then `response.create`.
7) LLM/Audio out: Dora nodes produce LLM text segments and TTS audio; server forwards text deltas and audio frames.
8) Completion: after last audio segment, server sends `response.audio.done` and `response.done`.

Server‑Side Components
- WebSocket: `node-hub/dora-openai-websocket/src/main.rs`
- MaaS client (LLM/tooling): `node-hub/dora-maas-client/`
- ASR: `node-hub/dora-asr/`
- VAD/Speech monitor: `node-hub/dora-speechmonitor/`
- Segmenter: `node-hub/dora-text-segmenter/`
- TTS: `node-hub/dora-primespeech/`
- Example dataflow: `examples/chatbot-openai-0905/chatbot-staticflow.yml`

Build/Run (Docker Compose)
- Build: `docker build -t dora-voicechat:latest -f docker/Dockerfile .`
- Run: `docker compose -f docker/docker-compose.yml --profile openai0905 up -d`
- Tail: `docker compose -f docker/docker-compose.yml --profile openai0905 logs -f server_openai0905`

Moly Run Hints
- Increase verbosity:
  - `RUST_LOG=info cargo run -p moly --release`
  - or `RUST_LOG=debug` for frame‑level detail.
- Ensure mic capture runs and sends `input_audio_buffer.append` regularly, not just commits.
- Send the greeting (single `response.create`) at session start if desired; rely on server_vad afterward.

What To Look For (Server Logs)
- Session: `Session update/created/updated` lines.
- Greeting: `Received ResponseCreate from client with instructions`.
- Audio append: Downsample/resample logs and audio to speech‑monitor.
- Turn end: `Question ended detected` → `Sent input_audio_buffer.committed` → `Sent response.create to trigger LLM`.
- LLM output: `🤖 LLM OUTPUT` chunks from `maas-client/text`.
- TTS: `🔊/🎵` audio output and `segment_complete` events.
- Completion: `✅ Sent response.audio.done` then `✅ Sent response.done`.

Per‑Node Logs (Dataflow name from compose env: `DATAFLOW_NAME=chatflow0905`)
- `dora logs chatflow0905 wserver`
- `dora logs chatflow0905 asr`
- `dora logs chatflow0905 maas-client`
- `dora logs chatflow0905 text-segmenter`
- `dora logs chatflow0905 primespeech`

Common Pitfalls & Fixes
- No response after silence:
  - Ensure server sends both `input_audio_buffer.committed` and `response.create` (fixed in wserver).
  - Verify ASR outputs appear (`🎙️ ASR OUTPUT`) after speech.
  - Check `OPENAI_API_KEY` is present; MaaS config uses `api_key = "env:OPENAI_API_KEY"`.
- Double responses:
  - If moly sends `response.create` on each turn while server_vad is enabled, you’ll get duplicates. Gate moly to only send greeting, then rely on server triggers.
- Early commit/no audio:
  - If moly commits before sending enough `append` frames, ASR has nothing to transcribe. Ensure steady append cadence and let server drive commit on `question_ended`.
- Language/model mismatch:
  - ASR set to Chinese (`LANGUAGE: zh`) in example; adjust if your speech is different.

Raising Verbosity
- Nodes (asr/text‑segmenter/primespeech): set `LOG_LEVEL: DEBUG` in `chatbot-staticflow.yml`.
- MaaS client: set `log_level = "DEBUG"` in `examples/chatbot-openai-0905/maas_mcp_browser_config.toml`.

Next Enhancements (optional)
- Add session correlation IDs across nodes for easier tracing.
- Buffer final ASR transcript in `wserver` and forward to `maas-client` on `question_ended` as a second trigger path.

