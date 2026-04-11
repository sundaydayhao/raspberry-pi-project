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

# 等待网络和X服务器就绪
sleep 10

# 隐藏鼠标光标
unclutter -idle 0 &

# 禁用屏幕保护和电源管理
xset s off
xset -dpms
xset s noblank

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
  --disable-translate \
  --disable-features=TranslateUI \
  --disk-cache-dir=/dev/null \
  http://localhost:5000
