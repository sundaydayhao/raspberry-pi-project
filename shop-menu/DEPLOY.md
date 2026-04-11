# 奶茶店展示系统 - 部署指南

本文档详细说明如何在树莓派3B+上部署奶茶店HDMI展示系统。

## 系统要求

### 硬件要求
- 树莓派3B+（或更高版本）
- MicroSD卡（建议16GB以上）
- 5V 3A电源适配器
- HDMI显示器
- HDMI线缆
- 键盘和鼠标（用于初始配置）

### 软件要求
- Raspberry Pi OS（推荐使用Desktop版本）
- Python 3.7+
- Chromium浏览器
- NetworkManager

## 快速部署

### 方法一：自动安装（推荐）

1. **下载项目到树莓派**
```bash
cd ~
git clone <your-repo-url> shop-menu
cd shop-menu
```

2. **运行安装脚本**
```bash
sudo bash install.sh
```

3. **按照提示完成安装**
   - 脚本会自动安装所有依赖
   - 配置系统服务自动启动
   - 询问是否立即启动服务

4. **首次配置WiFi**
   - 系统启动后会自动创建WiFi热点
   - SSID: `TeaShop-Display`
   - 密码: `12345678`
   - 使用手机连接热点后访问: http://192.168.4.1/wifi
   - 配置WiFi连接

5. **访问管理后台**
   - 配置WiFi后，通过局域网访问: http://树莓派IP:5000/admin
   - 开始管理展示内容

### 方法二：手动安装

#### 1. 准备系统

```bash
# 更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 安装必要的系统包
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    chromium \
    x11-xserver-utils \
    network-manager \
    unclutter \
    git
```

#### 2. 下载项目

```bash
cd ~
git clone <your-repo-url> shop-menu
cd shop-menu
```

#### 3. 安装Python依赖

```bash
python3 -m venv venv
./venv/bin/python3 -m pip install -r requirements.txt
```

#### 4. 创建必要目录

```bash
mkdir -p data
mkdir -p static/images
```

#### 5. 配置自动启动

创建systemd服务文件：

```bash
sudo nano /etc/systemd/system/shop-menu.service
```

添加以下内容（注意修改路径）：

```ini
[Unit]
Description=Tea Shop Display System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/shop-menu
ExecStart=/home/pi/shop-menu/start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

说明：这里的 `systemd` 服务只负责启动 Flask 后端。Chromium 全屏展示建议通过树莓派桌面环境的 `autostart.sh` 启动，避免 `DISPLAY=:0` 无权限访问的问题。

对于 Raspberry Pi OS Bookworm，优先使用 `~/.config/labwc/autostart`；较旧系统可继续使用 `~/.config/lxsession/LXDE-pi/autostart`。另外需要把系统设置为 Boot to Desktop Autologin。

启用服务：

```bash
# 设置脚本可执行权限
chmod +x start.sh

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable shop-menu.service

# 启动服务
sudo systemctl start shop-menu.service
```

配置浏览器开机自启动：

```bash
mkdir -p ~/.config/labwc
printf '%s\n' "bash /home/pi/shop-menu/autostart.sh &" >> ~/.config/labwc/autostart

mkdir -p ~/.config/lxsession/LXDE-pi
printf '%s\n' "@bash /home/pi/shop-menu/autostart.sh" >> ~/.config/lxsession/LXDE-pi/autostart

sudo raspi-config nonint do_boot_behaviour B4
```

## 服务管理

### 启动服务
```bash
sudo systemctl start shop-menu
```

### 停止服务
```bash
sudo systemctl stop shop-menu
```

### 重启服务
```bash
sudo systemctl restart shop-menu
```

### 查看服务状态
```bash
sudo systemctl status shop-menu
```

### 查看日志
```bash
# 实时查看日志
sudo journalctl -u shop-menu -f

# 查看最近的日志
sudo journalctl -u shop-menu -n 100
```

### 禁用自动启动
```bash
sudo systemctl disable shop-menu
```

## 手动启动（用于测试）

如果不想使用systemd服务，可以手动启动：

```bash
cd ~/shop-menu
./start.sh
```

## WiFi配置

### 首次配置

1. 系统启动后会自动创建WiFi热点
2. 使用手机或电脑连接热点：
   - SSID: `TeaShop-Display`
   - 密码: `12345678`
3. 连接后访问: http://192.168.4.1/wifi
4. 扫描并连接到您的WiFi网络

### 修改WiFi配置

可以通过以下方式修改WiFi：
- 访问管理后台的WiFi配置页面
- 或访问: http://树莓派IP:5000/wifi

### AP模式配置

如需修改热点名称和密码，编辑配置文件：

```bash
nano server/config.py
```

修改以下参数：
```python
AP_SSID = 'TeaShop-Display'  # 热点名称
AP_PASSWORD = '12345678'      # 热点密码
```

## 内容管理

### 访问管理后台

在局域网内访问: http://树莓派IP:5000/admin

### 添加展示内容

1. 点击"添加新幻灯片"
2. 填写标题、副标题、内容
3. 选择背景颜色
4. 可选：上传背景图片
5. 设置显示时长
6. 点击"保存"
7. 点击"保存所有更改"使内容生效

### 上传图片

- 支持格式: PNG, JPG, JPEG, GIF, WEBP
- 最大文件大小: 16MB
- 图片会自动保存到 `static/images/` 目录

### 调整显示顺序

使用"上移"和"下移"按钮调整幻灯片顺序

## 显示配置

### 全屏显示

系统会自动在树莓派上以全屏模式显示内容。如需调整：

编辑 `start.sh` 文件中的Chromium启动参数。

### 屏幕分辨率

如需调整分辨率，编辑 `/boot/config.txt`：

```bash
sudo nano /boot/config.txt
```

添加或修改：
```
hdmi_group=2
hdmi_mode=82  # 1920x1080 60Hz
```

常用分辨率模式：
- 82: 1920x1080 60Hz
- 16: 1024x768 60Hz
- 4: 1280x720 60Hz

修改后重启：
```bash
sudo reboot
```

### 关闭屏幕保护

系统已自动配置关闭屏幕保护。如需手动配置：

```bash
# 编辑自动启动配置
nano ~/.config/lxsession/LXDE-pi/autostart
```

添加：
```
@xset s off
@xset -dpms
@xset s noblank
```

## 故障排除

### 服务无法启动

1. 检查日志：
```bash
sudo journalctl -u shop-menu -n 50
```

2. 检查Python依赖：
```bash
pip3 list | grep -i flask
```

3. 手动测试启动：
```bash
cd ~/shop-menu
python3 -m server.app
```

### WiFi无法连接

1. 检查NetworkManager状态：
```bash
sudo systemctl status NetworkManager
```

2. 重启NetworkManager：
```bash
sudo systemctl restart NetworkManager
```

3. 手动测试WiFi扫描：
```bash
nmcli dev wifi list
```

### 浏览器无法全屏

1. 检查DISPLAY环境变量：
```bash
echo $DISPLAY
```

2. 确保X服务器运行：
```bash
ps aux | grep X
```

3. 手动启动浏览器测试：
```bash
DISPLAY=:0 chromium --kiosk http://localhost:5000/display
```

### 显示器无信号

1. 检查HDMI连接
2. 检查 `/boot/config.txt` 配置
3. 尝试强制HDMI输出：
```bash
sudo nano /boot/config.txt
```
添加：
```
hdmi_force_hotplug=1
```

### 内容不更新

1. 清除浏览器缓存（系统会自动每5分钟刷新）
2. 检查数据文件：
```bash
cat ~/shop-menu/data/content.json
```
3. 重启服务：
```bash
sudo systemctl restart shop-menu
```

## 性能优化

### 减少内存使用

编辑 `start.sh`，在Chromium启动参数中添加：
```bash
--disable-gpu \
--disable-software-rasterizer \
--disable-dev-shm-usage
```

### 加快启动速度

1. 禁用不需要的服务
2. 使用轻量级桌面环境
3. 减少开机自启动程序

## 备份与恢复

### 备份内容数据

```bash
# 备份展示内容
cp ~/shop-menu/data/content.json ~/content_backup.json

# 备份图片
tar -czf ~/images_backup.tar.gz ~/shop-menu/static/images/
```

### 恢复数据

```bash
# 恢复展示内容
cp ~/content_backup.json ~/shop-menu/data/content.json

# 恢复图片
tar -xzf ~/images_backup.tar.gz -C ~/
```

## 安全建议

1. **修改默认密码**
   - 修改树莓派系统密码
   - 修改WiFi热点密码

2. **限制访问**
   - 仅在可信网络中使用
   - 考虑添加管理后台登录认证

3. **定期更新**
   - 定期更新系统包
   - 更新Python依赖

4. **防火墙配置**
```bash
# 安装UFW
sudo apt-get install ufw

# 允许5000端口
sudo ufw allow 5000

# 启用防火墙
sudo ufw enable
```

## 更新系统

### 更新代码

```bash
cd ~/shop-menu
git pull
./venv/bin/python3 -m pip install -r requirements.txt
sudo systemctl restart shop-menu
```

### 更新系统包

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo reboot
```

## 技术支持

如遇到问题，请检查：
1. 系统日志: `sudo journalctl -u shop-menu -f`
2. Python错误: 查看终端输出
3. 网络连接: `ping google.com`
4. 服务状态: `sudo systemctl status shop-menu`

## 附录

### 目录结构

```
shop-menu/
├── server/              # 后端服务
│   ├── __init__.py
│   ├── app.py          # Flask应用
│   ├── config.py       # 配置文件
│   └── wifi_manager.py # WiFi管理
├── templates/           # HTML模板
│   ├── display.html    # 展示页面
│   ├── admin.html      # 管理后台
│   └── wifi.html       # WiFi配置
├── static/             # 静态资源
│   └── images/         # 上传的图片
├── data/               # 数据存储
│   ├── content.json    # 展示内容
│   └── wifi_config.json # WiFi配置
├── requirements.txt    # Python依赖
├── start.sh           # 启动脚本
├── install.sh         # 安装脚本
├── README.md          # 项目说明
└── DEPLOY.md          # 部署文档
```

### 端口说明

- 5000: Flask Web服务器
- 192.168.4.1: AP模式下的访问地址

### 默认配置

- 默认轮播时间: 5秒
- 图片最大大小: 16MB
- AP热点SSID: TeaShop-Display
- AP热点密码: 12345678
