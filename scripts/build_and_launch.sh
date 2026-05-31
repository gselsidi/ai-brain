#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
HOST="${HOST:-127.0.0.1}"
KB_PORT="${KB_PORT:-8001}"
KB_URL="${KB_URL:-http://localhost:${KB_PORT}}"

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  echo "Creating virtual environment at ${VENV_DIR}..."
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo "Installing/updating development dependencies..."
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install -e ".[dev]"

export PATH="${ROOT_DIR}/${VENV_DIR}/bin:${PATH}"
export HOST
export KB_PORT

echo "Running full local framework evidence loop..."
make maintenance-daily

echo "Starting knowledge base server at ${KB_URL}..."
mkdocs serve --dev-addr "${HOST}:${KB_PORT}" > state/reports/knowledge_base_server.log 2>&1 &
kb_pid=$!
trap 'kill "${kb_pid}" 2>/dev/null || true' EXIT

for _ in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS "${KB_URL}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -fsS "${KB_URL}" >/dev/null

cat <<EOF

Build and framework evidence are complete.

Knowledge:  ${KB_URL}
Reports:    ${ROOT_DIR}/state/reports/combined_report.html

Knowledge base server is running. Press Ctrl-C to stop it.
EOF

wait "${kb_pid}"
