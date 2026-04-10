# 09 - 高级综合项目 (Advanced Projects)

## 📋 目录结构

```
09-advanced-projects/
├── smart_security_web/          # 🔒 智能安防监控系统（端口5003）
│   ├── smart_security_web.py
│   └── templates/
│       └── smart_security_web.html
├── energy_monitor_web/          # ⚡ 智能电能监测系统（端口5004）
│   ├── energy_monitor_web.py
│   └── templates/
│       └── energy_monitor_web.html
├── weather_station.py           # 气象站（本地）
├── alarm_system.py              # 报警系统（本地）
├── plant_monitor.py             # 植物监测（本地）
├── robot_car.py                 # 小车控制（本地）
└── README.md
```

---

## 🔒 项目一：智能安防监控系统

**目录：** `smart_security_web/`  
**访问：** `http://<树莓派IP>:5003`

### 功能特性
- 👤 **PIR人体感应**（实时检测，网页状态显示）
- 📏 **超声波入侵检测**（设定警戒距离，小于阈值触发报警）
- 📷 **摄像头自动抓拍**（检测到入侵时自动拍照，网页画廊查看）
- 🔔 **蜂鸣器报警**（有源蜂鸣器，报警时鸣响）
- 🔒 **布防/撤防控制**（网页一键切换）
- 🚨 **报警横幅**（入侵时全屏闪烁警告）
- 📊 **超声波距离实时图表**（含警戒线标注）
- 📋 **报警日志**（最近50条，含快照缩略图）
- 📈 **报警统计**（累计/今日报警次数）

### 硬件连接
```
PIR传感器  → GPIO17
超声波TRIG → GPIO23
超声波ECHO → GPIO24
蜂鸣器     → GPIO22（有源蜂鸣器）
摄像头     → USB摄像头 或 Pi Camera
```

### 运行
```bash
cd 09-advanced-projects/smart_security_web
python3 smart_security_web.py
# 访问 http://<IP>:5003
```

---

## ⚡ 项目二：智能电能监测系统

**目录：** `energy_monitor_web/`  
**访问：** `http://<树莓派IP>:5004`

### 功能特性
- 🔌 **多路电流监测**（ACS712电流传感器 + MCP3008 ADC，最多4路）
- ⚡ **实时功率计算**（P = U × I）
- 📊 **累计用电量统计**（kWh）
- 💰 **电费实时估算**（可配置电价）
- 📈 **功率趋势图**（实时折线图）
- 📊 **各路负载对比图**（柱状图）
- 📅 **每小时用电统计**（表格展示）
- 🔌 **负载状态显示**（通电/断电，进度条）

### 硬件连接
```
MCP3008 → SPI (CLK=GPIO11, MOSI=GPIO10, MISO=GPIO9, CS=GPIO8)
  CH0   → ACS712电流传感器（主回路）
  CH1   → 分压电路（电压检测）
  CH2   → ACS712电流传感器（照明回路）
  CH3   → ACS712电流传感器（插座回路）
```

### 运行
```bash
cd 09-advanced-projects/energy_monitor_web
python3 energy_monitor_web.py
# 访问 http://<IP>:5004
```

---

## 📻 其他高级项目脚本

| 文件 | 功能 |
|------|------|
| `weather_station.py` | 综合气象站（温湿度+气压+风速，本地显示） |
| `alarm_system.py` | 多传感器报警系统（本地运行） |
| `plant_monitor.py` | 植物生长监测（本地运行） |
| `robot_car.py` | 小车运动控制（本地运行） |

---

## 🔌 端口汇总（全项目 Web 服务）

| 项目 | 目录 | 端口 |
|------|------|------|
| 🏠 智能家居监测 | `08-iot-projects/smart_home_monitor/` | 5000 |
| 🌱 植物养护 | `08-iot-projects/plant_care_web/` | 5001 |
| 📊 实时仪表盘 | `08-iot-projects/realtime_dashboard/` | 5002 |
| 🔒 安防监控 | `09-advanced-projects/smart_security_web/` | 5003 |
| ⚡ 电能监测 | `09-advanced-projects/energy_monitor_web/` | 5004 |
| 📷 摄像头直播 | `07-camera/camera_web_stream/` | 5005 |
| 🎵 音频控制 | `10-audio/audio_web_player/` | 5006 |