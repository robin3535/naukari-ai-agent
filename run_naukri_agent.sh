#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$ROOT_DIR/naukari-agent"
PYTHON_BIN="$ROOT_DIR/venv/bin/python3"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

cd "$APP_DIR"
mkdir -p logs screenshots storage outputs

export HEADLESS="${HEADLESS:-false}"

"$PYTHON_BIN" main.py
