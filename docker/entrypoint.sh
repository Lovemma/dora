#!/bin/sh
set -euo pipefail

echo "[entrypoint] Ensuring clean Dora state..."
dora destroy || true

echo "[entrypoint] Starting Dora background services..."
dora up

echo "[entrypoint] Waiting for Dora to be ready..."
for i in $(seq 1 30); do
  if dora list >/dev/null 2>&1; then
    echo "[entrypoint] Dora is ready."
    break
  fi
  sleep 0.5
done

# Optionally switch example and pre-build/start a static dataflow
# Configure with:
#  - EXAMPLE_DIR: path to example dir (default: current WORKDIR)
#  - DATAFLOW_FILE: YAML to build/start if present (default: chatbot-staticflow.yml)
#  - WS_SERVER_NAME: name passed to websocket server (default: wserver)

EXAMPLE_DIR="${EXAMPLE_DIR:-$PWD}"
DATAFLOW_FILE="${DATAFLOW_FILE:-chatbot-staticflow.yml}"
# Give the static dataflow a stable name so we can tail logs reliably
DATAFLOW_NAME="${DATAFLOW_NAME:-staticflow}"
WS_SERVER_NAME="${WS_SERVER_NAME:-wserver}"

echo "[entrypoint] Using example dir: ${EXAMPLE_DIR}"
cd "${EXAMPLE_DIR}" || { echo "[entrypoint] ERROR: cannot cd into ${EXAMPLE_DIR}"; exit 1; }

# Ensure default MaaS config exists if example provides only an .example file
DEFAULT_CONFIG="maas_mcp_browser_config.toml"
if [ ! -f "$DEFAULT_CONFIG" ] && [ -f "${DEFAULT_CONFIG}.example" ]; then
  echo "[entrypoint] No $DEFAULT_CONFIG found; copying from ${DEFAULT_CONFIG}.example"
  cp "${DEFAULT_CONFIG}.example" "$DEFAULT_CONFIG"
fi

if [ -f "${DATAFLOW_FILE}" ]; then
  if [ "${SKIP_DORA_BUILD:-}" = "1" ]; then
    echo "[entrypoint] SKIP_DORA_BUILD=1 set; skipping dora build for ${DATAFLOW_FILE}"
  else
    echo "[entrypoint] Building dataflow: ${DATAFLOW_FILE}"
    dora build "${DATAFLOW_FILE}"
  fi
  echo "[entrypoint] Starting dataflow (detached): ${DATAFLOW_FILE} (name: ${DATAFLOW_NAME})"
  dora start "${DATAFLOW_FILE}" --name "${DATAFLOW_NAME}" --detach
  # Give the daemon a moment to register nodes so dynamic connections succeed
  sleep 1
  # Optionally tail Dora node logs to container stdout for easier debugging
  # Set TAIL_NODE_LOGS to a comma-separated list, e.g.: "primespeech,text-segmenter,asr"
  if [ -n "${TAIL_NODE_LOGS:-}" ]; then
    # Start one background tail per requested node
    for NODE in $(echo "$TAIL_NODE_LOGS" | tr ',' ' '); do
      echo "[entrypoint] Tailing Dora logs for node: $NODE (dataflow: ${DATAFLOW_NAME})"
      # Run in background; prefix lines with node name for readability
      sh -c "dora logs '${DATAFLOW_NAME}' '$NODE' 2>&1 | sed -u \"s/^/[node:$NODE] /\"" &
    done
  fi
else
  echo "[entrypoint] No ${DATAFLOW_FILE} found in ${EXAMPLE_DIR}; skipping build/start"
fi

echo "[entrypoint] Launching WebSocket server on ${HOST:-0.0.0.0}:${PORT:-8123} (name: ${WS_SERVER_NAME})"
exec dora-openai-websocket -- --name "${WS_SERVER_NAME}"
