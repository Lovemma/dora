# Dora Voice Chat Docker (dora-voicechat)

Use this image to run Dora’s voice chat demos end‑to‑end:
- Download/cache models once and reuse them
- Run ASR/TTS smoke tests
- Start the WebSocket server for OpenAI (0905) or Alicloud (0908) examples

Supported examples in this image:
- `examples/chatbot-openai-0905/`
- `examples/chatbot-alicloud-0908/`
- Default compose profile: `examples/chatbot-openai-websocket-browser/`

The image mounts host directories for models and HF cache.

## Quick Start
- Set host paths (one time):
  - `cp docker/.env.example docker/.env` and edit absolute paths, or export in your shell:
    - `export MODELS_DIR="$HOME/.dora/models"`
    - `export HF_CACHE="$HOME/.cache/huggingface"`
- Set API keys (repo root):
  - `cp .env.example .env` and fill `OPENAI_API_KEY` and/or `ALIBABA_CLOUD_API_KEY`
- Download models: `./docker/download-models.sh all && ./docker/download-models.sh onnx`
- Run tests: `./docker/run-tests.sh`
- Start server (OpenAI 0905): `docker compose -f docker/docker-compose.yml --profile openai0905 up`

## Environment
- MODELS_DIR: absolute path where models are stored (e.g., `/home/you/.dora/models`)
- HF_CACHE: absolute path for Hugging Face cache (e.g., `/home/you/.cache/huggingface`)
- Where to set:
  - Compose: `docker/.env` (absolute paths; Compose doesn’t expand `$HOME`)
  - Shell: `export MODELS_DIR=...` and `export HF_CACHE=...`
- API keys:
  - `./.env` at repo root is loaded by Compose via `env_file: ../.env`
  - Set `OPENAI_API_KEY` for OpenAI profile; `ALIBABA_CLOUD_API_KEY` for Alicloud
  - Optional: `HUGGING_FACE_HUB_TOKEN` when pulling gated models

## Build Image
```
docker build -t dora-voicechat:latest -f docker/Dockerfile .
```

## Models
Two options to fetch models to your `MODELS_DIR` and cache to `HF_CACHE`:

- Helper script (recommended):
  - `./docker/download-models.sh all` (FunASR + PrimeSpeech, then list)
  - `./docker/download-models.sh onnx` (convert to ONNX; faster CPU inference)
  - `./docker/download-models.sh voice doubao` (download specific voice)
- Compose downloader:
  - `docker compose -f docker/docker-compose.yml up downloader`

## Testing
Run ASR and TTS validations without starting the server.

- One‑shot container (default):
  - `./docker/run-tests.sh`
  - Custom paths: `./docker/run-tests.sh --models-dir "$MODELS_DIR" --cache-dir "$HF_CACHE" --tts-out "$PWD/tts_output"`
- Against compose server (if already running):
  - `./docker/compose-tests.sh --voice doubao`

What to expect
- ASR: imports of `funasr_onnx`, `onnxruntime`, `pywhispercpp`; CPU provider is fine. Transcription in zh for sample audio.
- ONNX converter: the test auto‑answers “no” to overwrite prompts to stay non‑interactive.
- TTS: generates `tts_output/chinese_tts_output.wav` with a reasonable duration; CPU RTF around 0.8–1.2× is OK.

Common test notes
- `pkg_resources` deprecation warnings are benign.
- Slow ASR on CPU? Ensure ONNX conversion ran: `./docker/download-models.sh onnx`.

## Run Server
The entrypoint:
- Starts Dora (`dora up`)
- Prebuilds/starts a static dataflow if `DATAFLOW_FILE` exists
- Launches `dora-openai-websocket` on `${HOST:-0.0.0.0}:${PORT:-8123}`

Profiles
- Browser demo:
  - `docker compose -f docker/docker-compose.yml --profile browser up`
- OpenAI 0905:
  - `docker compose -f docker/docker-compose.yml --profile openai0905 up`
- Alicloud 0908:
  - `docker compose -f docker/docker-compose.yml --profile alicloud0908 up`

Notebook
- Start JupyterLab:
  - `docker compose -f docker/docker-compose.yml up notebook`
- Auth options (set in your environment or in `../.env` for compose):
  - Password (recommended): set `JUPYTER_PASSWORD=strong-password`. This disables token auth.
  - Token (default if no password): set `JUPYTER_TOKEN=dora` (or your own). The default in compose is `dora`.
  - Port: set `JUPYTER_PORT=8888` (default 8888). Connect to `http://localhost:8888`.
- Notes:
  - The entrypoint runs as root inside the container with `allow_root=True`.
  - If you prefer to run as your user, add `user: "${UID:-1000}:${GID:-1000}"` under the `notebook` service and ensure mounted paths are readable.

Customize
- `EXAMPLE_DIR`: container path to example (default set per profile)
- `DATAFLOW_FILE`: YAML to build/start (default `chatbot-staticflow.yml`)
- `WS_SERVER_NAME`: dynamic node name (`wserver` by default)

Direct docker run (optional)
```
# OpenAI 0905
docker run --rm -it -p 8123:8123 \
  -e HOST=0.0.0.0 -e PORT=8123 \
  -e OPENAI_API_KEY \
  -e ASR_ENGINE=funasr \
  -e ASR_MODELS_DIR=/root/.dora/models/asr \
  -e PRIMESPEECH_MODEL_DIR=/root/.dora/models/primespeech \
  -e EXAMPLE_DIR=/opt/dora/examples/chatbot-openai-0905 \
  -e DATAFLOW_FILE=chatbot-staticflow.yml \
  -v "$MODELS_DIR":/root/.dora/models \
  -v "$HF_CACHE":/root/.cache/huggingface \
  dora-voicechat:latest

# Alicloud 0908
docker run --rm -it -p 8123:8123 \
  -e HOST=0.0.0.0 -e PORT=8123 \
  -e ALIBABA_CLOUD_API_KEY \
  -e ASR_ENGINE=funasr \
  -e ASR_MODELS_DIR=/root/.dora/models/asr \
  -e PRIMESPEECH_MODEL_DIR=/root/.dora/models/primespeech \
  -e EXAMPLE_DIR=/opt/dora/examples/chatbot-alicloud-0908 \
  -e DATAFLOW_FILE=chatbot-staticflow.yml \
  -v "$MODELS_DIR":/root/.dora/models \
  -v "$HF_CACHE":/root/.cache/huggingface \
  dora-voicechat:latest
```

## Troubleshooting
- Port 8123 busy: `docker ps --filter "publish=8123"` then `docker ps -q --filter "publish=8123" | xargs -r docker stop`.
- Missing models: run downloads first; prefer `ASR_ENGINE=funasr`.
- Git missing during node build: image now includes `git`; rebuild if using an older image.
- HF rate limits: set `HUGGING_FACE_HUB_TOKEN` in your shell only when needed.
- Permissions: helper scripts run as your UID:GID to avoid root‑owned files.
- Logs: `docker compose logs -f server` (or the specific profile service).
- Reset Dora: `dora destroy && dora up` inside the container.

## File Map
- `docker/docker-compose.yml` — services and profiles (`browser`, `openai0905`, `alicloud0908`, `notebook`)
- `docker/download-models.sh` — model download/convert helpers
- `docker/run-tests.sh` — one‑shot ASR/TTS tests (non‑interactive)
- `docker/compose-tests.sh` — tests against running compose server
- `docker/entrypoint.sh` — starts Dora + WS server; honors `EXAMPLE_DIR`, `DATAFLOW_FILE`, `WS_SERVER_NAME`

## Security
- Never commit API keys. Keep them in `../.env` or export at runtime.
- Models live in `MODELS_DIR` on your host and are mounted into the container.
