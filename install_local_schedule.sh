#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_PATH="$HOME/Library/LaunchAgents/com.robin.naukri-agent.plist"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.robin.naukri-agent</string>

  <key>ProgramArguments</key>
  <array>
    <string>$ROOT_DIR/run_naukri_agent.sh</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$ROOT_DIR</string>

  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Hour</key>
      <integer>8</integer>
      <key>Minute</key>
      <integer>0</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>10</integer>
      <key>Minute</key>
      <integer>0</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>12</integer>
      <key>Minute</key>
      <integer>0</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>14</integer>
      <key>Minute</key>
      <integer>0</integer>
    </dict>
  </array>

  <key>StandardOutPath</key>
  <string>$ROOT_DIR/logs/launchd.out.log</string>

  <key>StandardErrorPath</key>
  <string>$ROOT_DIR/logs/launchd.err.log</string>
</dict>
</plist>
PLIST

mkdir -p "$ROOT_DIR/logs"
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "Installed local Naukri Agent schedule:"
echo "8:00 AM, 10:00 AM, 12:00 AM, 2:00 PM"
echo "$PLIST_PATH"
