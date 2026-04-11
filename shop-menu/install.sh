#!/bin/bash
# 奶茶店展示系统安装脚本

echo "========================================="
echo "  奶茶店展示系统 - 安装向导"
echo "========================================="
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用sudo运行此脚本"
    echo "例如: sudo bash install.sh"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
VENV_DIR="$SCRIPT_DIR/venv"

INSTALL_USER="${SUDO_USER:-}"
if [ -z "$INSTALL_USER" ] || ! id "$INSTALL_USER" &> /dev/null; then
    INSTALL_USER="$(stat -c '%U' "$SCRIPT_DIR" 2>/dev/null)"
fi
if [ -z "$INSTALL_USER" ] || ! id "$INSTALL_USER" &> /dev/null; then
    INSTALL_USER="root"
fi

run_as_install_user() {
    if [ "$INSTALL_USER" = "root" ]; then
        "$@"
    else
        runuser -u "$INSTALL_USER" -- "$@"
    fi
}

detect_browser_package() {
    local pkg
    local policy

    for pkg in chromium chromium-browser; do
        policy="$(apt-cache policy "$pkg" 2>/dev/null || true)"
        if printf '%s\n' "$policy" | grep -q "Candidate:" && \
           ! printf '%s\n' "$policy" | grep -q "Candidate: (none)"; then
            echo "$pkg"
            return 0
        fi
    done

    return 1
}

echo "步骤 1/6: 更新系统包..."
apt-get update

echo ""
echo "步骤 2/6: 安装Python3和pip..."
apt-get install -y python3 python3-pip python3-venv

echo ""
echo "步骤 3/6: 安装系统依赖..."
BROWSER_PACKAGE="$(detect_browser_package)"
if [ -n "$BROWSER_PACKAGE" ]; then
    echo "检测到浏览器软件包: $BROWSER_PACKAGE"
    apt-get install -y \
        "$BROWSER_PACKAGE" \
        x11-xserver-utils \
        network-manager \
        unclutter
else
    echo "警告: 未找到可用的 Chromium 软件包，跳过浏览器安装"
    echo "请手动安装 chromium 或 chromium-browser"
    apt-get install -y \
        x11-xserver-utils \
        network-manager \
        unclutter
fi

echo ""
echo "步骤 4/6: 安装Python依赖..."
if [ "$INSTALL_USER" != "root" ] && ! runuser -u "$INSTALL_USER" -- test -w "$SCRIPT_DIR"; then
    echo "警告: $INSTALL_USER 无法写入 $SCRIPT_DIR，将使用 root 创建虚拟环境"
    INSTALL_USER="root"
fi

if [ ! -x "$VENV_DIR/bin/python3" ]; then
    echo "创建虚拟环境: $VENV_DIR"
    run_as_install_user python3 -m venv "$VENV_DIR"
fi

echo "使用用户 $INSTALL_USER 安装依赖到虚拟环境..."
run_as_install_user "$VENV_DIR/bin/python3" -m pip install -r requirements.txt

echo ""
echo "步骤 5/6: 创建必要的目录..."
mkdir -p data
mkdir -p static/images
mkdir -p templates

echo ""
echo "步骤 6/6: 配置自动启动..."

# 创建systemd服务文件
cat > /etc/systemd/system/shop-menu.service << EOF
[Unit]
Description=Tea Shop Display System
After=network.target

[Service]
Type=simple
User=$INSTALL_USER
WorkingDirectory=$SCRIPT_DIR
Environment=SHOP_MENU_SKIP_BROWSER=1
ExecStart=$SCRIPT_DIR/start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 设置脚本可执行权限
chmod +x start.sh

# 重新加载systemd
systemctl daemon-reload

# 启用服务
systemctl enable shop-menu.service

echo ""
echo "========================================="
echo "  安装完成！"
echo "========================================="
echo ""
echo "服务管理命令:"
echo "  启动服务: sudo systemctl start shop-menu"
echo "  停止服务: sudo systemctl stop shop-menu"
echo "  查看状态: sudo systemctl status shop-menu"
echo "  查看日志: sudo journalctl -u shop-menu -f"
echo ""
echo "手动启动:"
echo "  cd $SCRIPT_DIR"
echo "  ./start.sh"
echo ""
echo "首次使用:"
echo "  1. 系统会自动启动并创建WiFi热点"
echo "  2. 使用手机连接热点: TeaShop-Display (密码: 12345678)"
echo "  3. 访问 http://192.168.4.1/wifi 配置WiFi"
echo "  4. 配置完成后访问 http://树莓派IP:5000/admin 管理内容"
echo ""
echo "是否现在启动服务? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    systemctl start shop-menu
    echo "服务已启动！"
    echo "请等待几秒钟，然后访问管理后台"
else
    echo "您可以稍后使用以下命令启动服务:"
    echo "sudo systemctl start shop-menu"
fi

echo ""
echo "========================================="
