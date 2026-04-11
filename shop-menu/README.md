# 🧋 奶茶店HDMI展示系统

基于树莓派3B+的奶茶店智能展示屏系统，支持HDMI输出、WiFi配网和远程内容管理。

## 📋 功能特性

- ✅ **HDMI全屏展示** - 自动轮播奶茶店活动、菜单、特色等内容
- ✅ **WiFi配网功能** - 支持扫描和连接WiFi网络
- ✅ **远程管理** - 通过手机浏览器实时修改展示内容
- ✅ **自动启动** - 开机自动运行，无需人工干预
- ✅ **实时更新** - 修改内容后自动同步到展示屏
- ✅ **系统监控** - 显示CPU温度、内存使用等系统信息

## 🛠️ 硬件要求

- 树莓派3B+（或更高版本）
- HDMI显示器
- 电源适配器（5V 2.5A）
- MicroSD卡（16GB或以上）
- 可选：键盘、鼠标（用于初始配置）

## 📦 软件依赖

- Raspberry Pi OS（推荐使用Desktop版本）
- Python 3.7+
- Flask 3.0.0
- Chromium浏览器

## 🚀 快速开始

### 1. 安装系统依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要的软件包
# Raspberry Pi OS Bookworm 通常使用 chromium；较旧系统可能仍是 chromium-browser
sudo apt install -y python3-pip python3-venv chromium unclutter

# 安装WiFi工具（如果需要）
sudo apt install -y wireless-tools wpasupplicant
```

### 2. 克隆或复制项目

```bash
# 将项目复制到树莓派
cd ~
cp -r /path/to/shop-menu ~/shop-menu
cd ~/shop-menu
```

### 3. 安装Python依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置系统服务（开机自启）

```bash
# 复制服务文件
sudo cp shop-menu.service /etc/systemd/system/

# 修改服务文件中的路径（如果项目不在/home/pi/shop-menu）
sudo nano /etc/systemd/system/shop-menu.service

# 启用并启动服务
sudo systemctl enable shop-menu.service
sudo systemctl start shop-menu.service

# 查看服务状态
sudo systemctl status shop-menu.service
```

说明：`systemd` 服务只负责启动后端服务，不直接拉起 Chromium。全屏浏览器应在树莓派桌面会话中通过 `autostart.sh` 启动，这样不会遇到 `xset` 或 `DISPLAY` 授权问题。

### 5. 配置自动启动浏览器

```bash
# Raspberry Pi OS Bookworm / labwc
mkdir -p ~/.config/labwc
printf '%s\n' "bash /home/pi/shop-menu/autostart.sh &" >> ~/.config/labwc/autostart

# 旧版 Raspberry Pi OS / LXDE
mkdir -p ~/.config/lxsession/LXDE-pi
printf '%s\n' "@bash /home/pi/shop-menu/autostart.sh" >> ~/.config/lxsession/LXDE-pi/autostart

# 让系统开机进入桌面并自动登录
sudo raspi-config nonint do_boot_behaviour B4
```

如果你使用的是仓库里的 [`install.sh`](/home/hao/work/raspberry-pi-project/shop-menu/install.sh)，它现在会自动完成上述配置。

验证当前是否已配置：

```bash
cat ~/.config/labwc/autostart
cat ~/.config/lxsession/LXDE-pi/autostart
```

如果你是通过 SSH 手动执行 `./start.sh`，脚本会检测当前是否有可用的图形会话；没有的话只启动后端，不再强行拉起浏览器。

### 6. 手动启动（测试用）

```bash
# 使用启动脚本
chmod +x start.sh
./start.sh

# 或直接使用虚拟环境中的 Python
venv/bin/python3 -m server.app
```

## 📱 使用说明

### 访问展示页面

系统启动后，HDMI显示器会自动全屏显示展示内容。

- 展示页面地址：`http://树莓派IP:5000`

### 访问管理后台

使用手机或电脑浏览器访问管理后台：

- 管理后台地址：`http://树莓派IP:5000/admin`

### 管理功能

#### 1. 内容管理
- 修改店铺名称
- 查看和管理幻灯片
- 删除不需要的幻灯片

#### 2. WiFi配置
- 查看当前WiFi连接状态
- 扫描可用的WiFi网络
- 连接到新的WiFi网络

#### 3. 系统设置
- 调整幻灯片切换间隔
- 查看系统信息（CPU温度、内存使用）

## 📝 配置文件说明

### config.json

主配置文件，包含所有展示内容和系统设置：

```json
{
  "shop_name": "悦茶时光",
  "wifi": {
    "ssid": "WiFi名称",
    "password": "WiFi密码",
    "configured": true
  },
  "display": {
    "rotation_interval": 5000
  },
  "content": {
    "slides": [
      {
        "id": 1,
        "type": "welcome",
        "title": "欢迎光临",
        "subtitle": "悦茶时光奶茶店",
        "background": "#FF6B9D",
        "enabled": true
      }
    ]
  }
}
```

### 幻灯片类型

1. **welcome** - 欢迎页面
   - `title`: 主标题
   - `subtitle`: 副标题

2. **promotion** - 促销活动
   - `title`: 活动标题
   - `content`: 活动内容
   - `description`: 活动说明

3. **menu** - 菜单展示
   - `title`: 菜单标题
   - `items`: 菜单项数组
     - `name`: 商品名称
     - `price`: 商品价格

4. **feature** - 特色展示
   - `title`: 特色标题
   - `features`: 特色列表

## 🔧 高级配置

### 修改端口

编辑 `app.py` 文件，修改最后一行：

```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

### 添加sudo权限（WiFi配置需要）

```bash
# 编辑sudoers文件
sudo visudo

# 添加以下行（允许pi用户无密码执行WiFi相关命令）
pi ALL=(ALL) NOPASSWD: /usr/bin/iwlist
pi ALL=(ALL) NOPASSWD: /usr/sbin/wpa_cli
pi ALL=(ALL) NOPASSWD: /bin/cp /tmp/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf
```

### 屏幕旋转

如果需要旋转屏幕显示：

```bash
# 编辑config.txt
sudo nano /boot/config.txt

# 添加以下行（根据需要选择）
# display_rotate=0  # 正常
# display_rotate=1  # 90度
# display_rotate=2  # 180度
# display_rotate=3  # 270度

# 重启生效
sudo reboot
```

## 🐛 故障排除

### 服务无法启动

```bash
# 查看服务日志
sudo journalctl -u shop-menu.service -f

# 检查Python依赖
source ~/shop-menu/venv/bin/activate
pip list
```

### WiFi连接失败

```bash
# 检查WiFi状态
iwconfig

# 手动测试WiFi连接
sudo iwlist wlan0 scan

# 查看wpa_supplicant日志
sudo journalctl -u wpa_supplicant -f
```

### 浏览器未自动启动

```bash
# 检查autostart配置
cat ~/.config/lxsession/LXDE-pi/autostart

# 手动测试浏览器启动
chromium --kiosk http://localhost:5000
```

### 无法访问管理后台

```bash
# 检查防火墙
sudo ufw status

# 检查服务是否运行
sudo systemctl status shop-menu.service

# 检查端口占用
sudo netstat -tulpn | grep 5000
```

## 📂 项目结构

```
shop-menu/
├── app.py                 # Flask后端服务器
├── config.json           # 配置文件
├── requirements.txt      # Python依赖
├── start.sh             # 启动脚本
├── autostart.sh         # 自动启动脚本
├── shop-menu.service    # systemd服务配置
├── templates/           # HTML模板
│   ├── display.html    # HDMI展示页面
│   └── admin.html      # 管理后台页面
└── README.md           # 项目文档
```

## 🎨 自定义样式

### 修改颜色主题

编辑 `config.json` 中的 `background` 字段，使用十六进制颜色代码：

```json
{
  "background": "#FF6B9D"  // 粉红色
}
```

### 修改字体大小

编辑 `templates/display.html` 中的CSS样式。

## 📊 性能优化

- 建议使用轻量级的图片格式（WebP、优化的PNG）
- 幻灯片数量建议控制在10个以内
- 切换间隔建议不低于3秒（3000毫秒）
- 定期清理浏览器缓存

## 🔒 安全建议

- 修改默认的Flask密钥
- 在生产环境中禁用debug模式
- 使用强密码保护WiFi
- 定期更新系统和依赖包

## 📞 技术支持

如有问题，请检查：
1. 系统日志：`sudo journalctl -u shop-menu.service`
2. Python错误：查看终端输出
3. 网络连接：`ping 8.8.8.8`

## 📄 许可证

本项目仅供学习和个人使用。

## 🙏 致谢

感谢树莓派社区和Flask框架的支持。

---

**版本**: 1.0.0  
**更新日期**: 2026-04-10  
**适用平台**: 树莓派3B+及以上
