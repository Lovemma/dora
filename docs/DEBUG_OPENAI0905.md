**Summary**
- Issue: Client receives the initial greeting audio but never gets a response after asking a question; eventually disconnects with “Normal closure”.
- Context: OpenAI 0905 example, static dataflow with `maas-client` and Python nodes; WebSocket server (`dora-openai-websocket`) bridges client <→ Dora.
- Focus: Greeting duplication, missing/late completion events, and unexpected connection close.

**Environment**
- Compose service: `server_openai0905` (profile `openai0905`)
- Dataflow file: `examples/chatbot-openai-0905/chatbot-staticflow.yml`
- Dataflow name: `chatflow0905`
- WS dynamic node name: `wserver` (env `WS_SERVER_NAME: wserver`)
- Platform: runtime image `dora-voicechat:latest` built from `docker/Dockerfile` (multi-stage: Rust builder + Python runtime)

**Current Configuration**
- `docker/docker-compose.yml`
  - `SKIP_DORA_BUILD: "0"` (Python nodes build/install on start)
  - `DATAFLOW_NAME: chatflow0905`
  - `TAIL_NODE_LOGS: wserver` (tail only WS server logs for clarity)
  - `SPAWN_MAAS: "0"` (WebSocket server does not spawn dynamic `maas-client`; reuse static node)
  - `MAAS_CONFIG_PATH: /opt/dora/examples/chatbot-openai-0905/maas_mcp_browser_config_zh.local.toml`
- `examples/chatbot-openai-0905/chatbot-staticflow.yml`
  - `maas-client`: static node, `path: dora-maas-client`
  - `wserver`: dynamic node (no cargo build in YAML; binary provided by image)
  - `text-segmenter`, `asr`, `primespeech`: static Python nodes
- `node-hub/dora-maas-client/src/config.rs`
  - Config source: `MAAS_CONFIG_PATH` (TOML); enforces Chinese system prompt

**Recent Code Changes (require image rebuild to take effect)**
- `node-hub/dora-openai-websocket/src/main.rs`
  - Do not break the event loop on unhandled events; `continue` instead (prevents premature close)
  - De-duplicate greeting forwarding: ignore identical `response.create.instructions` within 3s
  - Respect `SPAWN_MAAS=0` to avoid spawning a dynamic `maas-client` when static is used
- `docker/docker-compose.yml`
  - `SKIP_DORA_BUILD=0`, `TAIL_NODE_LOGS=wserver`, `SPAWN_MAAS=0`
- `examples/chatbot-openai-0905/chatbot-staticflow.yml`
  - Use installed binaries (no cargo build steps in YAML)

Note: The runtime container does not include `cargo`. Rust binary changes require rebuilding the image.

**Observed Logs (abridged)**
- `text-segmenter` emits multiple small greeting segments in quick succession (e.g., “嘿…”, “有什么需要帮忙的…”, “系统已上线…”) across different conversations.
- `maas-client` receives the same `text_to_audio` greeting twice and performs two streaming requests.
- Missing WebSocket server logs in container stdout previously due to tailing many nodes; now tailored to `wserver` for signal.

**Interpretation**
- Greeting repeats: Client likely sends `response.create` multiple times; without dedup, WS server forwarded both → duplicate greetings via `maas-client`.
- No response after question: The WS server may fail to send `response.audio.done`/`response.done` after last TTS segment, or previously broke on unhandled events causing a server-side close. Patches mitigate both (requires rebuild).

**What Should Happen**
- On first greeting: one `response.created` and audio deltas, then `response.audio.done` and `response.done`.
- On user question: ASR → `maas-client` → `text-segmenter` → `primespeech` → WS audio deltas, followed by completion events.
- Connection should remain open across turns.

**Commands**
- Rebuild image to include WS server patches:
  - `docker build -t dora-voicechat:latest -f docker/Dockerfile .`
  - `docker compose -f docker/docker-compose.yml --profile openai0905 up -d --force-recreate`
- Tail focused logs:
  - `docker compose -f docker/docker-compose.yml --profile openai0905 logs -f --tail=300 server_openai0905`

**Log Markers To Watch (wserver)**
- Session and greeting
  - `SPAWN_MAAS disabled; using existing static maas-client`
  - `SessionCreated` and `SessionUpdated`
  - `Received ResponseCreate ...`
  - `Forwarding greeting instructions to maas-client: ...`
  - `Ignoring duplicate greeting within 3s window` (if a duplicate arrives)
- TTS/audio lifecycle
  - `🔊 TTS OUTPUT ... Forwarding to client as audio data`
  - `🎯 Last segment detected (segments_remaining=0)`
  - `✅ Sent response.audio.done`
  - `✅ Sent response.done - conversation complete`
- Disconnects / errors
  - `OpCode::Close` (client-initiated close)
  - `Protocol error`, `Unsupported data`, or `Ignoring malformed client message`

**Quick Checks**
- Verify `SPAWN_MAAS=0` is respected (see log line above)
- Ensure only one greeting forward per turn (check for dedup log)
- Confirm completion events after last TTS segment
- Confirm `asr` uses Chinese (`LANGUAGE: zh`) and `maas-client` config enforces Chinese in `system_prompt`

**Potential Edge Causes If Issue Persists**
- Client sends additional control frames leading to closure (check for `OpCode::Close`)
- `segments_remaining` metadata not reaching WS server; completion not triggered
- TTS sample rate metadata missing; resampler fail path (look for TTS resample logs)
- MaaS client tool execution delays or errors (check `maas-client` log for tool calls/errors)

**Next Steps (Debug Plan)**
- Rebuild and redeploy the image so WS patches apply
- Reproduce: connect, observe single greeting, ask a short question (2–3s speech)
- Validate WS log sequence (created → audio deltas → audio.done → done)
- If disconnect persists, capture 30 lines around:
  - first `ResponseCreate`
  - last `TTS OUTPUT`
  - close event

**File Pointers**
- Compose: `docker/docker-compose.yml`
- Dataflow: `examples/chatbot-openai-0905/chatbot-staticflow.yml`
- WS server: `node-hub/dora-openai-websocket/src/main.rs`
- MaaS client config (zh): `examples/chatbot-openai-0905/maas_mcp_browser_config_zh.local.toml`

**Notes**
- The runtime image intentionally lacks `cargo`; avoid in-container cargo builds. Use the Dockerfile rebuild path for Rust changes.

