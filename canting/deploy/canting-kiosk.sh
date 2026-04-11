#!/usr/bin/env bash
set -euo pipefail

DISPLAY_URL="${DISPLAY_URL:-http://127.0.0.1:3200/}"
CHROMIUM_BIN="$(command -v chromium-browser || command -v chromium || true)"

if [[ -z "${CHROMIUM_BIN}" ]]; then
  echo "未找到 chromium-browser 或 chromium。"
  exit 1
fi

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/${USER}/.Xauthority}"

${CHROMIUM_BIN} \
  --kiosk \
  --incognito \
  --disable-infobars \
  --noerrdialogs \
  --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 \
  --autoplay-policy=no-user-gesture-required \
  "${DISPLAY_URL}"

