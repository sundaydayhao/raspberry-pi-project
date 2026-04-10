#!/bin/bash
# 自动启动脚本 - 在树莓派启动时自动打开浏览器全屏显示

# 等待网络和X服务器就绪
sleep 10

# 隐藏鼠标光标
unclutter -idle 0 &

# 禁用屏幕保护和电源管理
xset s off
xset -dpms
xset s noblank

# 启动Chromium浏览器全屏模式
chromium-browser --kiosk --incognito \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-restore-session-state \
  --noerrdialogs \
  --disable-translate \
  --disable-features=TranslateUI \
  --disk-cache-dir=/dev/null \
  http://localhost:5000