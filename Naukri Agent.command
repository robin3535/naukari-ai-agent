#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Naukri Agent..."
echo

"$ROOT_DIR/run_naukri_agent.sh"

echo
echo "Naukri Agent finished."
echo "Press any key to close this window."
read -k 1
