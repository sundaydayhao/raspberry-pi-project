# 🍓 Raspberry Pi 学习套件 (Raspberry Pi Learning Kit)

> 适合科技创客和学生的全面 Raspberry Pi 学习资源

![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=Raspberry%20Pi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

---

## 📚 目录结构

```
raspberry-pi-learn/
├── 01-getting-started/          # 入门基础
├── 02-gpio-basics/              # GPIO 基础操作
├── 03-sensors/                  # 传感器应用
├── 04-display/                  # 显示模块
├── 05-motors/                   # 电机控制
├── 06-communication/            # 通信协议
├── 07-camera/
│   ├── camera_web_stream/       # 📷 摄像头网页直播（端口5005）
│   └── *.py                     # 本地摄像头脚本
├── 08-iot-projects/
│   ├── smart_home_monitor/      # 🏠 智能家居监测（端口5000）
│   ├── plant_care_web/          # 🌱 植物养护系统（端口5001）
│   ├── realtime_dashboard/      # 📊 实时传感器仪表盘（端口5002）
│   └── *.py                     # MQTT、基础Web服务器
├── 09-advanced-projects/
│   ├── smart_security_web/      # 🔒 智能安防监控（端口5003）
│   ├── energy_monitor_web/      # ⚡ 电能监测系统（端口5004）
│   └── *.py                     # 气象站、报警系统等
├── 10-audio/
│   ├── audio_web_player/        # 🎵 网页音频控制（端口5006）
│   └── *.py                     # 本地音频脚本
├── 11-ai-ml/
│   ├── ai_dashboard_web/        # 🤖 AI/ML 智能仪表盘（端口5007）
│   └── *.py                     # 异常检测、图像分类、手势识别、语音命令
└── wiring_diagrams/             # 接线图说明
```

---

## 🚀 快速开始

### 硬件要求
- Raspberry Pi 3B+ / 4B / Zero 2W（推荐）
- MicroSD 卡（16GB 以上，Class 10）
- 5V/3A 电源适配器
- 面包板、杜邦线若干

### 软件环境
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 依赖
pip3 install -r requirements.txt

# 启用 I2C、SPI、Camera 等接口
sudo raspi-config
```

---

## 📖 学习路径

### 🌱 初学者路径
1. [入门基础](./01-getting-started/) - 系统配置、Hello World
2. [GPIO 基础](./02-gpio-basics/) - LED、按钮、PWM
3. [传感器入门](./03-sensors/) - 温湿度、距离传感器

### 🌿 进阶路径
4. [显示模块](./04-display/) - LCD、OLED 屏幕
5. [电机控制](./05-motors/) - 舵机、步进电机
6. [通信协议](./06-communication/) - I2C、SPI、UART

### 🌳 高级路径
7. [摄像头应用](./07-camera/) - 拍照、视频、**网页直播**
8. [物联网项目](./08-iot-projects/) - MQTT、**传感器Web仪表盘**
9. [高级项目](./09-advanced-projects/) - **安防监控、电能监测**
10. [音频处理](./10-audio/) - 录音、播放、**网页音频控制**

### 🧠 AI/ML 路径
11. [AI/ML 人工智能](./11-ai-ml/) - **异常检测、图像分类、手势识别、语音命令**

---

## 🌐 IoT Web 项目汇总

> 树莓派采集数据 → WiFi上传 → 网页实时展示，**PC和手机均可访问**

| # | 项目 | 目录 | 端口 | 核心传感器/功能 |
|---|------|------|------|----------------|
| 1 | 🏠 智能家居环境监测站 | `08-iot-projects/smart_home_monitor/` | **5000** | DHT11+BMP280+MQ-2+PIR，报警横幅 |
| 2 | 🌱 智能植物养护系统 | `08-iot-projects/plant_care_web/` | **5001** | 土壤湿度+光照+自动浇水+远程控制 |
| 3 | 📊 实时多传感器仪表盘 | `08-iot-projects/realtime_dashboard/` | **5002** | WebSocket推送+6路传感器+CSV导出 |
| 4 | 🔒 智能安防监控系统 | `09-advanced-projects/smart_security_web/` | **5003** | PIR+超声波+摄像头抓拍+布防撤防 |
| 5 | ⚡ 智能电能监测系统 | `09-advanced-projects/energy_monitor_web/` | **5004** | ACS712多路电流+功率+用电量+电费 |
| 6 | 📷 摄像头网页直播 | `07-camera/camera_web_stream/` | **5005** | MJPEG直播+运动检测+人脸检测+拍照 |
| 7 | 🎵 网页音频控制中心 | `10-audio/audio_web_player/` | **5006** | 播放MP3+TTS朗读+蜂鸣器音乐+录音 |
| 8 | 🤖 AI/ML 智能仪表盘 | `11-ai-ml/ai_dashboard_web/` | **5007** | 异常检测+图像分类+手势识别+语音命令 |

### 快速运行（无需硬件，自动模拟数据）
```bash
pip3 install flask flask-socketio eventlet opencv-python

# 任选一个项目运行：
cd 08-iot-projects/smart_home_monitor  && python3 smart_home_monitor.py   # http://localhost:5000
cd 08-iot-projects/plant_care_web      && python3 plant_care_web.py        # http://localhost:5001
cd 08-iot-projects/realtime_dashboard  && python3 realtime_dashboard.py    # http://localhost:5002
cd 09-advanced-projects/smart_security_web  && python3 smart_security_web.py   # http://localhost:5003
cd 09-advanced-projects/energy_monitor_web  && python3 energy_monitor_web.py   # http://localhost:5004
cd 07-camera/camera_web_stream         && python3 camera_web_stream.py     # http://localhost:5005
cd 10-audio/audio_web_player           && python3 audio_web_player.py      # http://localhost:5006
cd 11-ai-ml/ai_dashboard_web           && python3 ai_dashboard_web.py      # http://localhost:5007
```

### 手机访问
1. 确保手机与树莓派连接**同一 WiFi**
2. 查看树莓派 IP：`hostname -I`
3. 手机浏览器访问：`http://<树莓派IP>:<端口>`

---

## 🛠 常用工具命令

```bash
# 查看 GPIO 引脚状态
gpio readall

# 查看 I2C 设备
sudo i2cdetect -y 1

# 查看系统信息
vcgencmd measure_temp    # CPU 温度
vcgencmd get_mem arm     # ARM 内存

# 查看 USB 设备
lsusb

# 查看串口设备
ls /dev/tty*

# 查看摄像头
ls /dev/video*
```

---

## 📌 GPIO 引脚图 (BCM 编号)

```
                    3V3  (1) (2)  5V
                  GPIO2  (3) (4)  5V
                  GPIO3  (5) (6)  GND
                  GPIO4  (7) (8)  GPIO14
                    GND  (9) (10) GPIO15
                 GPIO17 (11) (12) GPIO18
                 GPIO27 (13) (14) GND
                 GPIO22 (15) (16) GPIO23
                    3V3 (17) (18) GPIO24
                 GPIO10 (19) (20) GND
                  GPIO9 (21) (22) GPIO25
                 GPIO11 (23) (24) GPIO8
                    GND (25) (26) GPIO7
                  GPIO0 (27) (28) GPIO1
                  GPIO5 (29) (30) GND
                  GPIO6 (31) (32) GPIO12
                 GPIO13 (33) (34) GND
                 GPIO19 (35) (36) GPIO16
                 GPIO26 (37) (38) GPIO20
                    GND (39) (40) GPIO21
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License - 自由学习和使用

---

*Happy Making! 🎉*