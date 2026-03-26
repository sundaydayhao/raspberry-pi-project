# 06 - 通信协议

## 📋 本章内容

| 文件 | 协议 | 说明 | 难度 |
|------|------|------|------|
| `i2c_scanner.py` | I2C | 扫描 I2C 设备 | ⭐ |
| `i2c_example.py` | I2C | I2C 通信示例 | ⭐⭐ |
| `spi_example.py` | SPI | SPI 通信示例 | ⭐⭐⭐ |
| `uart_serial.py` | UART | 串口通信 | ⭐⭐ |
| `bluetooth_hc05.py` | 蓝牙 | HC-05 蓝牙模块 | ⭐⭐⭐ |
| `wifi_scan.py` | WiFi | WiFi 扫描与连接 | ⭐⭐ |

## 🔌 协议对比

| 协议 | 引脚数 | 速度 | 距离 | 设备数 | 用途 |
|------|--------|------|------|--------|------|
| I2C | 2 (SDA+SCL) | 100k-400kbps | 短 | 多个 | 传感器、显示屏 |
| SPI | 4 (MOSI+MISO+CLK+CS) | 高速 | 短 | 多个 | 存储、显示屏 |
| UART | 2 (TX+RX) | 可变 | 中 | 点对点 | GPS、蓝牙模块 |
| 蓝牙 | 无线 | 中 | ~10m | 多个 | 无线控制 |
| WiFi | 无线 | 高 | ~50m | 多个 | 物联网 |

## 📐 引脚说明

### I2C 引脚
```
SDA ── GPIO2 (物理引脚 3)
SCL ── GPIO3 (物理引脚 5)
```

### SPI 引脚
```
MOSI ── GPIO10 (物理引脚 19)
MISO ── GPIO9  (物理引脚 21)
SCLK ── GPIO11 (物理引脚 23)
CE0  ── GPIO8  (物理引脚 24)
CE1  ── GPIO7  (物理引脚 26)
```

### UART 引脚
```
TX ── GPIO14 (物理引脚 8)
RX ── GPIO15 (物理引脚 10)
```

## 启用接口
```bash
sudo raspi-config
# Interface Options -> I2C/SPI/Serial Port -> Enable