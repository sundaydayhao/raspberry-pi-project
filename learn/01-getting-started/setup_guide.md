# Raspberry Pi 系统安装与配置指南

## 第一步：准备材料

### 必需硬件
- Raspberry Pi 主板（推荐 4B 4GB）
- MicroSD 卡（建议 32GB Class 10 或 U1）
- USB-C 电源（5V/3A）
- HDMI 线 + 显示器（首次配置用）
- USB 键盘鼠标

### 可选硬件
- 散热片 + 风扇
- 官方保护壳
- USB 读卡器（烧录系统用）

---

## 第二步：烧录系统

### 方法一：使用 Raspberry Pi Imager（推荐）
1. 访问 https://www.raspberrypi.org/software/ 下载 Imager
2. 插入 MicroSD 卡
3. 选择设备型号
4. 选择操作系统：**Raspberry Pi OS (64-bit)**
5. 点击齿轮图标进行高级设置：
   - 设置主机名（如 `raspberrypi`）
   - 启用 SSH
   - 设置用户名和密码
   - 配置 WiFi（SSID 和密码）
6. 点击"烧录"

### 方法二：使用 dd 命令（Linux/Mac）
```bash
# 查找 SD 卡设备
lsblk

# 烧录镜像（替换 /dev/sdX 为实际设备）
sudo dd if=raspios.img of=/dev/sdX bs=4M status=progress
sync
```

---

## 第三步：首次启动配置

### 通过 SSH 连接（无头模式）
```bash
# 查找树莓派 IP 地址
nmap -sn 192.168.1.0/24 | grep -i raspberry

# SSH 连接
ssh pi@192.168.1.xxx
# 默认密码：raspberry（如果未在 Imager 中设置）
```

### 系统初始化配置
```bash
# 打开配置工具
sudo raspi-config
```

**推荐配置项：**
1. **System Options**
   - S1 Wireless LAN - 配置 WiFi
   - S3 Password - 修改密码
   - S4 Hostname - 设置主机名

2. **Interface Options**
   - I1 Legacy Camera - 启用摄像头
   - I2 SSH - 启用 SSH
   - I3 VNC - 启用远程桌面
   - I4 SPI - 启用 SPI
   - I5 I2C - 启用 I2C
   - I6 Serial Port - 启用串口

3. **Performance Options**
   - P2 GPU Memory - 设置 GPU 内存（摄像头用建议 128MB）

4. **Localisation Options**
   - L1 Locale - 设置语言（zh_CN.UTF-8）
   - L2 Timezone - 设置时区（Asia/Shanghai）

---

## 第四步：系统优化

### 更新系统
```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt autoremove -y
sudo apt autoclean
```

### 安装常用工具
```bash
# 开发工具
sudo apt install -y python3-pip python3-dev python3-venv
sudo apt install -y git vim nano htop

# GPIO 相关
sudo apt install -y python3-rpi.gpio python3-gpiozero
sudo apt install -y i2c-tools python3-smbus

# 网络工具
sudo apt install -y net-tools nmap curl wget

# 多媒体
sudo apt install -y vlc ffmpeg

# 中文支持
sudo apt install -y fonts-wqy-zenhei fonts-wqy-microhei
```

### 配置 Python 虚拟环境（推荐）
```bash
# 创建虚拟环境
python3 -m venv ~/pi-env

# 激活虚拟环境
source ~/pi-env/bin/activate

# 安装依赖
pip install RPi.GPIO gpiozero smbus2 Adafruit-DHT

# 退出虚拟环境
deactivate
```

### 配置静态 IP（可选）
```bash
sudo nano /etc/dhcpcd.conf
```
添加以下内容：
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 114.114.114.114
```

---

## 第五步：远程开发配置

### VS Code 远程开发
1. 安装 VS Code 扩展：**Remote - SSH**
2. 连接：`ssh pi@192.168.1.xxx`
3. 在树莓派上直接编写和运行代码

### VNC 远程桌面
```bash
# 树莓派端启动 VNC
vncserver :1 -geometry 1920x1080

# 客户端使用 RealVNC Viewer 连接
# 地址：192.168.1.xxx:1
```

### 文件传输
```bash
# 从本机传文件到树莓派
scp local_file.py pi@192.168.1.xxx:~/

# 从树莓派下载文件
scp pi@192.168.1.xxx:~/remote_file.py ./

# 使用 rsync 同步目录
rsync -avz ./project/ pi@192.168.1.xxx:~/project/
```

---

## 常见问题解决

### Q: 找不到树莓派 IP
```bash
# 方法1：路由器管理页面查看
# 方法2：使用 nmap 扫描
nmap -sn 192.168.1.0/24

# 方法3：使用 arp-scan
sudo arp-scan --localnet
```

### Q: SSH 连接被拒绝
```bash
# 检查 SSH 服务状态
sudo systemctl status ssh

# 启动 SSH 服务
sudo systemctl start ssh
sudo systemctl enable ssh
```

### Q: GPIO 权限不足
```bash
# 将用户添加到 gpio 组
sudo usermod -a -G gpio $USER
# 重新登录生效
```

### Q: I2C 设备找不到
```bash
# 检查 I2C 是否启用
ls /dev/i2c*

# 扫描 I2C 设备
sudo i2cdetect -y 1