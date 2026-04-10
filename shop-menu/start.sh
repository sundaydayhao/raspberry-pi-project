#!/bin/bash
# 奶茶店展示系统启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================="
echo "  奶茶店展示系统启动中..."
echo "========================================="

# 检查Python3是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖是否安装
echo "检查依赖..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p data
mkdir -p static/images
mkdir -p templates

# 启动Flask服务器
echo "启动Flask服务器..."
python3 -m server.app &
SERVER_PID=$!
echo "服务器PID: $SERVER_PID"

# 等待服务器启动
echo "等待服务器启动..."
sleep 3

# 获取本机IP地址
IP_ADDRESS=$(hostname -I | awk '{print $1}')
echo ""
echo "========================================="
echo "  服务器启动成功！"
echo "========================================="
echo "  展示页面: http://localhost:5000"
echo "  管理后台: http://localhost:5000/admin"
echo "  WiFi配置: http://localhost:5000/wifi"
echo ""
echo "  局域网访问:"
echo "  展示页面: http://$IP_ADDRESS:5000"
echo "  管理后台: http://$IP_ADDRESS:5000/admin"
echo "========================================="
echo ""

# 检查是否在树莓派上运行
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    if [[ $MODEL == *"Raspberry Pi"* ]]; then
        echo "检测到树莓派环境"
        
        # 等待5秒后启动浏览器全屏显示
        sleep 5
        
        # 设置DISPLAY环境变量
        export DISPLAY=:0
        
        # 关闭屏幕保护和电源管理
        xset s off
        xset -dpms
        xset s noblank
        
        # 启动Chromium浏览器全屏模式
        echo "启动全屏展示..."
        chromium-browser --kiosk --incognito --disable-infobars \
            --disable-session-crashed-bubble \
            --disable-restore-session-state \
            --noerrdialogs \
            http://localhost:5000/display &
        
        BROWSER_PID=$!
        echo "浏览器PID: $BROWSER_PID"
    fi
fi

# 保持脚本运行
echo "按 Ctrl+C 停止服务"
wait $SERVER_PID