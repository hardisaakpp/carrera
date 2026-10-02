#!/usr/bin/env bash
# Starts carrera: the Python API on :8920 and the web app on :3010. Ctrl+C stops both.
#   ./dev.sh            your data lives in ./data (cv.local.yaml, ofertas.db, ...)
set -euo pipefail
cd "$(dirname "$0")"
export DOCKER_CONTEXT="${CARRERA_DOCKER_CONTEXT:-default}" # the CV is compiled with Docker Engine
export CARRERA_DATOS="${CARRERA_DATOS:-data}"

.venv/bin/uvicorn carrera.api:crear_app --factory --host 127.0.0.1 --port 8920 &
API=$!
trap 'kill $API 2>/dev/null' EXIT
cd web && exec npx next dev --port 3010
