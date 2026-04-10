# 08 - 物联网项目 (IoT)

## 📋 目录结构

```
08-iot-projects/
├── smart_home_monitor/          # 🏠 智能家居环境监测站（端口5000）
│   ├── smart_home_monitor.py
│   └── templates/
│       └── smart_home_monitor.html
├── plant_care_web/              # 🌱 智能植物养护系统（端口5001）
│   ├── plant_care_web.py
│   └── templates/
│       └── plant_care_web.html
├── realtime_dashboard/          # 📊 实时多传感器仪表盘（端口5002）
│   ├── realtime_dashboard.py
│   └── templates/
│       └── realtime_dashboard.html
├── web_server_flask.py          # Flask基础Web服务器示例
├── mqtt_publisher.py            # MQTT消息发布
├── mqtt_subscriber.py           # MQTT消息订阅
├── IOT_WEB_PROJECTS.md          # 详细项目文档
└── README.md
```

---

## 🌐 物联网架构

```
传感器 → 树莓派（数据采集+处理）
              │
              ├── Flask Web服务器 ──→ 浏览器（PC/手机）
              │        │
              │    REST API / WebSocket
              │
              └── MQTT Broker ──→ 订阅者（其他设备）
```

---

## 🏠 项目一：智能家居环境监测站

**目录：** `smart_home_monitor/`  
**访问：** `http://<树莓派IP>:5000`

### 功能特性
- 🌡️ 实时温湿度监测（DHT11/DHT22）
- 🌬️ 大气压强监测（BMP280）
- 🔥 烟雾/可燃气体报警（MQ-2）
- 👤 人体运动检测（PIR）
- 📈 历史数据折线图（Chart.js）
- 🚨 超限自动报警横幅
- 📱 手机/PC自适应界面

### 硬件连接
```
DHT11  → GPIO4
BMP280 → I2C (SDA=GPIO2, SCL=GPIO3)
MQ-2   → GPIO17 (数字输出)
PIR    → GPIO27
```

### 运行
```bash
cd 08-iot-projects/smart_home_monitor
python3 smart_home_monitor.py
# 访问 http://<IP>:5000
```

---

## 🌱 项目二：智能植物养护系统

**目录：** `plant_care_web/`  
**访问：** `http://<树莓派IP>:5001`

### 功能特性
- 🌱 土壤湿度实时监测（电容式传感器 + MCP3008 ADC）
- ☀️ 光照强度监测（光敏电阻 + ADC）
- 🌡️ 环境温湿度（DHT11）
- 💧 **自动浇水**（土壤干燥时自动触发继电器）
- 🎮 Web远程手动控制水泵
- 📊 土壤湿度/温度历史趋势图
- 📝 浇水历史记录

### 硬件连接
```
DHT11      → GPIO4
MCP3008    → SPI (CLK=GPIO11, MOSI=GPIO10, MISO=GPIO9, CS=GPIO8)
  CH0      → 土壤湿度传感器
  CH1      → 光敏电阻
继电器(水泵) → GPIO18
```

### 运行
```bash
cd 08-iot-projects/plant_care_web
python3 plant_care_web.py
# 访问 http://<IP>:5001
```

---

## 📊 项目三：实时多传感器仪表盘（WebSocket版）

**目录：** `realtime_dashboard/`  
**访问：** `http://<树莓派IP>:5002`

### 功能特性
- ⚡ **WebSocket实时推送**（无需轮询，延迟极低）
- 🌡️ 温湿度 + 超声波距离 + 光照 + 加速度（6路传感器）
- 📈 4个实时折线图（Chart.js）
- 📐 加速度三轴可视化柱状图
- 📥 一键导出CSV数据
- 🌈 舒适度综合评估
- 🔗 WebSocket连接状态指示

### 硬件连接
```
DHT11   → GPIO4
HC-SR04 → TRIG=GPIO23, ECHO=GPIO24
MPU6050 → I2C
光敏电阻  → MCP3008 CH0
```

### 安装依赖
```bash
pip3 install flask flask-socketio eventlet
```

### 运行
```bash
cd 08-iot-projects/realtime_dashboard
python3 realtime_dashboard.py
# 访问 http://<IP>:5002
```

---

## 🔧 通用安装依赖

```bash
pip3 install flask flask-socketio eventlet
pip3 install paho-mqtt
pip3 install Adafruit-DHT spidev smbus2
```

## MQTT Broker 安装
```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

## 📡 手机访问说明

1. 确保手机与树莓派连接**同一WiFi网络**
2. 查看树莓派IP地址：`hostname -I`
3. 手机浏览器访问：`http://<树莓派IP>:<端口>`

## 🔌 端口汇总

| 项目 | 端口 |
|------|------|
| 智能家居环境监测站 | 5000 |
| 智能植物养护系统 | 5001 |
| 实时多传感器仪表盘 | 5002 |
| 智能安防监控中心（09目录） | 5003 |
| 智能电能监测系统（09目录） | 5004 |