# ADS-B RTL-SDR HDMI 飞机信息监视器

## 方案说明

该目录实现了一个基于树莓派和 RTL-SDR 的 ADS-B 飞机监视器，用于接收 1090MHz ADS-B 信号，并在 HDMI 屏上显示飞机信息列表。

### 功能
- 使用 RTL-SDR 接收 1090MHz ADS-B 信号
- 自动调用系统中的 ADS-B 解码器：
  - `dump1090-fa`
  - `dump1090`
  - `readsb`
- 周期性读取 `aircraft.json`
- 在 HDMI 屏上显示飞机信息：
  - ICAO HEX
  - 航班号
  - 高度
  - 地速
  - 航向
  - 经纬度
  - 最近更新时间
- 支持全屏显示
- 支持 `Q` / `ESC` 退出

### 显示方案
该方案基于 HDMI 显示器输出，不依赖 SPI LCD。  
程序使用 `pygame` 在 HDMI 屏上绘制飞机表格信息，适合同样硬件条件下的树莓派 HDMI 小屏或普通显示器。

### 核心实现思路
1. 通过外部解码器接入 RTL-SDR 并采集 1090MHz ADS-B 数据
2. 由解码器生成 `aircraft.json`
3. Python 程序周期性读取 JSON 文件
4. 将飞机信息整理为表格
5. 使用 `pygame` 实时显示到 HDMI 屏

---

## 文件说明

- `main.py`  
  主程序，负责启动 ADS-B 解码器、读取 JSON 数据并显示飞机信息

- `requirements.txt`  
  Python 依赖列表

- `run.sh`  
  启动脚本，包含默认参数

---

## 依赖安装

### Python 依赖

```bash
pip install -r requirements.txt
```

### 系统依赖

该程序本身只负责显示，不直接完成 ADS-B 原始报文解码。  
需要在树莓派系统中预先安装以下任一解码器：

- `dump1090-fa`
- `dump1090`
- `readsb`

如果系统已经安装其中一个，程序会自动尝试调用。

---

## 使用方法

进入目录后运行：

```bash
bash run.sh
```

或者直接运行：

```bash
python3 main.py --json-path /run/dump1090-fa/aircraft.json --refresh-hz 2 --width 800 --height 480 --gain auto --device-index 0 --rows 12
```

---

## 参数说明

### 常用参数
- `--json-path`  
  `aircraft.json` 文件路径

- `--refresh-hz`  
  刷新频率，单位 Hz

- `--width`  
  HDMI 显示宽度

- `--height`  
  HDMI 显示高度

- `--windowed`  
  以窗口模式运行，而不是全屏

- `--dump1090-cmd`  
  自定义 ADS-B 解码器启动命令  
  默认值为 `auto`，会自动尝试 `dump1090-fa`、`dump1090`、`readsb`

- `--gain`  
  RTL-SDR 增益

- `--device-index`  
  RTL-SDR 设备编号

- `--rows`  
  屏幕上显示的飞机条数

---

## 默认配置

`run.sh` 默认参数为：

- JSON 路径：`/run/dump1090-fa/aircraft.json`
- 刷新频率：`2 Hz`
- 分辨率：`800 x 480`
- 增益：`auto`
- RTL 设备编号：`0`
- 显示条数：`12`

---

## 显示字段说明

- **HEX**  
  飞机的 ICAO 24 位地址

- **FLIGHT**  
  航班号/呼号

- **ALT**  
  高度

- **SPD**  
  地速

- **HDG**  
  航向

- **LAT / LON**  
  经纬度

- **SEEN**  
  最近一次接收到该飞机数据距现在的秒数

---

## 适用场景

- 树莓派 + RTL-SDR + 1090MHz 天线
- HDMI 小屏飞机监视终端
- 简易本地 ADS-B 可视化显示设备
- 便携式飞行监视信息显示

---

## 注意事项

1. 程序依赖外部 ADS-B 解码器生成 `aircraft.json`
2. 如果没有安装 `dump1090-fa` / `dump1090` / `readsb`，程序将无法启动
3. 建议使用 1090MHz 专用天线，以获得更好的接收效果
4. 若屏幕分辨率不同，请调整 `run.sh` 中的 `--width` 和 `--height`
5. 如果 `aircraft.json` 路径不同，请修改 `--json-path`

---

## 退出方式

运行过程中按以下按键可退出：

- `Q`
- `ESC`