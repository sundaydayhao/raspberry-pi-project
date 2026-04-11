#!/bin/bash
# 自动启动脚本 - 在树莓派启动时自动打开浏览器全屏显示

find_browser_command() {
  if command -v chromium-browser &> /dev/null; then
    echo "chromium-browser"
    return 0
  fi

  if command -v chromium &> /dev/null; then
    echo "chromium"
    return 0
  fi

  return 1
}

wait_for_server() {
  local retries=30
  local delay=2
  local attempt

  for attempt in $(seq 1 "$retries"); do
    if bash -lc 'exec 3<>/dev/tcp/127.0.0.1/5000' &> /dev/null; then
      return 0
    fi
    sleep "$delay"
  done

  return 1
}

disable_screen_blanking() {
  if ! command -v xset &> /dev/null; then
    return 0
  fi

  if ! xset q &> /dev/null; then
    return 0
  fi

  xset s off
  xset -dpms
  xset s noblank
}

# 等待桌面和后端服务就绪
sleep 5
wait_for_server || echo "警告: 后端服务未在预期时间内就绪，将继续启动浏览器"

# 隐藏鼠标光标
if command -v unclutter &> /dev/null; then
  unclutter -idle 0 &
fi

# 禁用屏幕保护和电源管理
disable_screen_blanking

# 启动Chromium浏览器全屏模式
BROWSER_BIN="$(find_browser_command)"
if [ -z "$BROWSER_BIN" ]; then
  echo "未找到 Chromium 浏览器，无法启动全屏展示"
  exit 1
fi

"$BROWSER_BIN" --kiosk --incognito \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-restore-session-state \
  --noerrdialogs \
  --no-first-run \
  --disable-translate \
  --disable-features=TranslateUI \
  --disk-cache-dir=/dev/null \
  http://localhost:5000
