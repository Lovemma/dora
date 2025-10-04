PrimeSpeech + WebSocket Debug Notes (OpenAI 0905)

Scope
- Track and resolve TTS errors seen on new client connections in the `openai0905` profile.
- Ensure server/client handshake, MaaS orchestration, and TTS synthesis are healthy.

Current State (as of last session)
- PrimeSpeech models present under `/root/.dora/models/primespeech` (mounted from host).
- YAML fix: `PRIMESPEECH_MODEL_DIR: /root/.dora/models/primespeech` (avoid `~` expansion issue).
- Chinese-only: `TEXT_LANG: zh`, `PROMPT_LANG: zh` set in `examples/chatbot-openai-0905/chatbot-staticflow.yml`.
- Python deps added: `wordsegment`, `g2p_en`, `nltk` (baked into Docker image via requirements).
- Observability: entrypoint tails node logs when `TAIL_NODE_LOGS` is set; compose sets
  `DATAFLOW_NAME=chatflow0905` and `TAIL_NODE_LOGS=primespeech,text-segmenter,asr,maas-client`.

Rebuild + Up
- docker build -t dora-voicechat:latest -f docker/Dockerfile .
- docker compose -f docker/docker-compose.yml --profile openai0905 up -d

Quick Log Access
- Container name (typically): `docker-server_openai0905-1`.
- See consolidated logs with node tails:
  - docker compose -f docker/docker-compose.yml --profile openai0905 logs -f server_openai0905
- Direct Dora logs inside container (useful when tails aren’t enabled):
  - docker exec -it docker-server_openai0905-1 dora list
  - docker exec -it docker-server_openai0905-1 dora logs <DATAFLOW_NAME> primespeech
  - docker exec -it docker-server_openai0905-1 dora logs <DATAFLOW_NAME> maas-client
  - docker exec -it docker-server_openai0905-1 dora logs <DATAFLOW_NAME> wserver

Client Handshake (expected)
1) Client connects to `ws://<host>:8123/` with headers:
   - `openai-beta: realtime=v1`, `Authorization: Bearer <any>`
2) Send `session.update` JSON.
3) Server spawns `maas-client`, then sends `session.created` + `session.updated`.
4) Client sends `response.create` OR streams audio via `input_audio_buffer.append` + `commit`.
5) Pipeline: WebSocket → ASR → MaaS → Text-Segmenter → TTS → Audio → WebSocket.

TTS Readiness Checklist
- Models dir exists in container: `/root/.dora/models/primespeech`.
  - Contains `moyoyo` subdir: `GPT_weights/*`, `SoVITS_weights/*`, `ref_audios/*`,
    `chinese-hubert-base/*`, `chinese-roberta-wwm-ext-large/*`.
  - Contains `G2PWModel/g2pW.onnx`.
- PrimeSpeech env in YAML: `PRIMESPEECH_MODEL_DIR=/root/.dora/models/primespeech`, `TEXT_LANG=zh`, `PROMPT_LANG=zh`.
- CPU path: `USE_GPU=false` is fine.

Known Issues + Fixes
- G2PW path error: `~/.dora/...` not expanded → use absolute path in YAML (done).
- Missing `wordsegment`/`g2p_en`/`nltk`: English cleaner import error (even on mixed text) → added to image and node pyproject (done). If English voices are selected, these are required.
- Connection reset / `Unexpected EOF`: can occur after manual dataflow restart while server is running → prefer restarting the server container:
  - docker compose -f docker/docker-compose.yml --profile openai0905 restart server_openai0905
- `maas-client` “failed to send output”: transient during startup; logs show restart; verify after a few seconds.

When Client Stuck on “Loading”
1) Check server logs for handshake and `session.created/session.updated`.
2) Tail `primespeech` logs; look for `[ERROR]` lines (G2PW, model file, import, etc.).
3) Tail `text-segmenter` logs; confirm segments forwarded.
4) Tail `maas-client` logs; confirm “Starting streaming request”, tool calls (if MCP in use).
5) If TTS emits `segment_complete: error`, the WebSocket server forwards `response.audio_transcript.delta { "delta": "error" }`.

Reset Sequence (safe)
- Restart server container (clean Dora + staticflow):
  - docker compose -f docker/docker-compose.yml --profile openai0905 restart server_openai0905
- If needed, stop/start dataflow inside container:
  - docker exec -it docker-server_openai0905-1 dora list
  - docker exec -it docker-server_openai0905-1 dora stop <UUID>
  - docker exec -it docker-server_openai0905-1 dora start /opt/dora/examples/chatbot-openai-0905/chatbot-staticflow.yml --name chatflow0905 --detach

MCP (Headless Playwright)
- Preinstalled: Node/npm, `@playwright/mcp`, filesystem MCP, Chromium browsers.
- TOML at `examples/chatbot-openai-0905/maas_mcp_browser_config.toml` is auto-copied from `.example` if missing.
- Expect `maas-client` logs: “Starting MCP server … playwright” and “Connected”.

Useful One‑liners
- Models presence check on host: `find ~/.dora/models/primespeech -maxdepth 2 -type f | head -n 20`
- In-container models dir: `docker exec docker-server_openai0905-1 bash -lc 'ls -la /root/.dora/models/primespeech && find /root/.dora/models/primespeech -maxdepth 2 -type f | head'`
- WebSocket quick probe: `docker exec docker-server_openai0905-1 curl -sS -v http://127.0.0.1:8123/` (expects Empty reply)

Next Hypotheses To Test
- Ensure first client message ordering: `session.update` → wait for acknowledgments → `response.create`.
- Verify Chinese text path is consistently hit (no English cleaner code path).
- Confirm G2PW model readable inside container with correct permissions.
- Watch for PrimeSpeech sending empty audio fragments (would trigger error handling in node).
