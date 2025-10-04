OpenAI 0905 WebSocket Debug Status

Summary
- Symptom: After the greeting works, when the user asks a question (via voice), the server logs “Question ended” and shows completion events for TTS, but no new LLM response is produced.
- Example logs:
  - "❓ Question ended detected - complete sentence, triggering LLM response"
  - "📤 Sending completion events after last audio segment"
  - "✅ Sent response.audio.done"
  - "✅ Sent response.done - conversation complete"
  - "🔵 [MAAS-CLIENT] Received event #2: InputClosed { id: DataId(\"text\") }"

Root Cause
- First issue (fixed): the WebSocket server logged that it would send both input_audio_buffer.committed and response.create after `question_ended`, but only committed the buffer; it never actually sent the `response.create` frame. As a result, the client wasn’t instructed to start a new LLM response.
- Current issue: the client still does not hear audio even though the server logs show audio forwarding and completion. Two likely causes identified:
  - Missing `response.created` event: many clients (e.g., Moly) don’t start decoding/playback until they’ve seen a `response.created` for the same `response_id` as subsequent deltas.
  - Audio payload mismatch: the server logged `Audio: 1 samples` which reflects the Arrow ListArray length (wrapper), not the actual PCM sample count. Additionally, the resampling path used a fixed 32 kHz → 24 kHz ratio regardless of the TTS source `sample_rate`, which can lead to tiny/empty outputs on small fragments.

Fix Implemented
- File: `node-hub/dora-openai-websocket/src/main.rs`
- Change 1: After detecting `question_ended`, the server now:
  1) Sends `input_audio_buffer.committed` and logs "✅ Sent input_audio_buffer.committed".
  2) Sends `response.create` with sensible defaults and logs "✅ Sent response.create to trigger LLM".
- Additional logging added at each step to make the trigger sequence obvious.

- Change 2: Implemented proper response lifecycle priming for audio playback:
  - Added `response.created` event (with a temporary static id `"123"`) and send it before the first `response.audio.delta` of each turn.
  - Reset creation flag after `response.done` so the next turn will announce again.

- Change 3: Corrected and instrumented audio handling:
  - Use `sample_rate` from metadata to compute resampling ratio to 24 kHz (was hard-coded 32 kHz → 24 kHz).
  - Log actual f32 sample counts before/after resampling and the final PCM bytes length.
  - Small guard rails to avoid zero-sized resampler buffers.

How To Rebuild And Run (Docker Compose)
- Rebuild image:
  - `docker build -t dora-voicechat:latest -f docker/Dockerfile .`
- Start OpenAI 0905 profile:
  - `docker compose -f docker/docker-compose.yml --profile openai0905 up -d`
- Tail logs:
  - `docker compose -f docker/docker-compose.yml --profile openai0905 logs -f server_openai0905`

Dataflow Overview (OpenAI 0905)
- Pipeline: WebSocket → Speech Monitor (VAD) → ASR → MaaS Client → Text Segmenter → PrimeSpeech TTS → WebSocket
- Relevant config files:
  - `examples/chatbot-openai-0905/chatbot-staticflow.yml`
  - `examples/chatbot-openai-0905/maas_mcp_browser_config.toml`

What To Look For In Logs
- WebSocket (`wserver`):
  - "❓ Question ended detected - complete sentence, triggering LLM response"
  - "📤 Sending commit and response.create after question_ended"
  - "✅ Sent input_audio_buffer.committed"
  - "🤖 Triggering LLM response after speech ended"
  - "✅ Sent response.create to trigger LLM"
  - When TTS audio starts:
    - "✓ Extracted N audio samples" (from Arrow)
    - "ℹ️  Resampling SR_in -> 24000 (ratio ...)"
    - "✓ Resampled N_in → N_out samples"
    - "✅ Sent response.created (id=123)" (only once per turn, before the first audio delta)
    - "✓ Encoded PCM16 bytes: B" (should be > 0)
  - Then look for: ASR OUTPUT → LLM OUTPUT → AUDIO OUTPUT entries.
- MaaS client (`maas-client`):
  - "INFO Processing: <user text>"
  - Segment sends, then "complete" status when streaming finishes.
- Text Segmenter (`text-segmenter`):
  - Segment boundaries and metrics; sends `text_segment` to TTS.
- PrimeSpeech (`primespeech`):
  - Audio chunk counts; `segment_complete` events when each TTS segment is done.

Increase Verbosity (optional)
- WebSocket server uses `println!` extensively already.
- Nodes respect `LOG_LEVEL` in their env:
  - In `chatbot-staticflow.yml`, set nodes (asr, text-segmenter, primespeech) to `LOG_LEVEL: DEBUG` if deeper detail is needed.
  - MaaS config: `examples/chatbot-openai-0905/maas_mcp_browser_config.toml` → `log_level = "DEBUG"`.

Troubleshooting Checklist
- Credentials: `OPENAI_API_KEY` is set in compose env (docker/.env or your shell). MaaS config uses `api_key = "env:OPENAI_API_KEY"`.
- ASR working: you should see "🎙️ ASR OUTPUT" lines after speaking, and transcribed text.
- Trigger sequence present: after silence, you should see the commit + response.create logs in `wserver`.
- MaaS client reacts: logs "Processing: ..." and outputs segments on `maas-client/text`.
- TTS: audio chunks appear and `segment_complete` events fire.
- Confirm `response.created` appears once before audio deltas for each turn.
- Confirm resampling logs show a reasonable sample count and bytes; bytes must be > 0.
- If `InputClosed { id: DataId("text") }` appears: this is informational for input channels and not fatal.

Useful Commands
- Tail all relevant logs (compose service tails node logs via TAIL_NODE_LOGS):
  - `docker compose -f docker/docker-compose.yml --profile openai0905 logs -f server_openai0905`
- Tail specific Dora node logs (dataflow name from compose env: `DATAFLOW_NAME=chatflow0905`):
  - `dora logs chatflow0905 wserver`
  - `dora logs chatflow0905 asr`
  - `dora logs chatflow0905 maas-client`
  - `dora logs chatflow0905 text-segmenter`
  - `dora logs chatflow0905 primespeech`

Next Steps (if issues persist)
- Add session correlation IDs to metadata and logs for end-to-end tracing.
- Optionally buffer the last ASR transcript inside `wserver` and send it explicitly to `maas-client` upon `question_ended` as a second trigger path.
- Replace static `response_id` ("123") with a per-turn ID and wire it through all events to match client expectations.
- If the client expects a specific `output_audio_format` other than `pcm16`, align `response.create` and encoder accordingly.
