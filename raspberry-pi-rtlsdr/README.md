# Raspberry Pi RTL-SDR HDMI Monitor Suite

本项目基于树莓派和 RTL-SDR，实现了两个面向 HDMI 屏显示的无线电监视应用：

- `FM/`：FM 广播频谱与瀑布图显示
- `ADSB/`：ADS-B 飞机信息接收与显示

项目适用于同一套硬件平台下的不同无线信号监视场景，统一采用 HDMI 屏作为显示终端。

---

## 项目结构

```text
.
├─ FM/
│  ├─ main.py
│  ├─ README.md
│  ├─ requirements.txt
│  └─ run.sh
├─ ADSB/
│  ├─ main.py
│  ├─ README.md
│  ├─ requirements.txt
│  └─ run.sh
└─ README.md
```

---

## 目录说明

### 1. FM
`FM/` 目录实现 RTL-SDR 对 FM 广播频段的采集和可视化显示。

功能包括：
- FM 频段 IQ 采样
- 实时 FFT 频谱分析
- 峰值频点显示
- 瀑布图显示
- HDMI 全屏输出

详细说明见：

```text
FM/README.md
```

---

### 2. ADSB
`ADSB/` 目录实现 RTL-SDR 对 1090MHz ADS-B 信号的接收与飞机信息显示。

功能包括：
- 自动调用 `dump1090-fa` / `dump1090` / `readsb`
- 读取 `aircraft.json`
- 显示飞机 HEX、航班号、高度、速度、航向、经纬度等
- HDMI 全屏输出

详细说明见：

```text
ADSB/README.md
```

---

## 硬件环境

推荐硬件：
- Raspberry Pi
- RTL-SDR USB 接收器
- HDMI 显示器或 HDMI 小屏
- 对应天线
  - FM 广播天线
  - 1090MHz ADS-B 天线

---

## 软件方案概述

### FM 方案
- 使用 `pyrtlsdr` 从 RTL-SDR 采集 IQ 数据
- 使用 `numpy` 做 FFT 分析
- 使用 `Pillow` 绘制频谱和瀑布图
- 使用 `pygame` 输出到 HDMI 屏

### ADS-B 方案
- 使用外部解码器 `dump1090-fa` / `dump1090` / `readsb`
- Python 读取解码器生成的 `aircraft.json`
- 使用 `pygame` 在 HDMI 屏绘制飞机信息表格

---

## 安装说明

### 1. Python 依赖
请分别进入对应目录安装依赖。

#### FM
```bash
cd FM
pip install -r requirements.txt
```

#### ADSB
```bash
cd ADSB
pip install -r requirements.txt
```

---

## 使用方法

### 运行 FM 监视器

```bash
cd FM
bash run.sh
```

### 运行 ADS-B 监视器

```bash
cd ADSB
bash run.sh
```

---

## 运行前准备

### FM
需要确保：
- RTL-SDR 已正确连接
- 系统可正常识别 RTL-SDR 设备
- HDMI 显示屏已连接并可显示图形界面

### ADS-B
需要确保：
- RTL-SDR 已正确连接
- 已安装以下任一 ADS-B 解码器：
  - `dump1090-fa`
  - `dump1090`
  - `readsb`
- 默认 `aircraft.json` 路径可访问

---

## 使用建议

- 若 HDMI 屏分辨率不是 `800x480`，请修改对应目录中的 `run.sh`
- 若有多个 RTL-SDR 设备，可修改 `--device-index`
- FM 与 ADS-B 是两个独立应用，建议分开运行
- 若需要自动启动，可后续扩展为 systemd 服务

---

## 已实现内容

### FM
- [x] RTL-SDR FM 采样
- [x] 频谱显示
- [x] 瀑布图显示
- [x] HDMI 输出
- [x] README 说明文档

### ADS-B
- [x] RTL-SDR ADS-B 接收接入
- [x] aircraft.json 读取
- [x] 飞机信息显示
- [x] HDMI 输出
- [x] README 说明文档

---

## 后续可扩展方向

- FM 音频解调与扬声器播放
- ADS-B 地图显示
- 飞机距离与方位计算
- 多页面切换显示
- 开机自动启动
- 触摸屏交互操作

---

## 文档入口

- `FM/README.md`
- `ADSB/README.md`