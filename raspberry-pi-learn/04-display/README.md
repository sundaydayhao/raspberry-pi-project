# 04 - 显示模块

## 📋 本章内容

| 文件 | 模块 | 接口 | 难度 |
|------|------|------|------|
| `lcd_i2c.py` | LCD1602/2004 (I2C) | I2C | ⭐⭐ |
| `oled_ssd1306.py` | OLED SSD1306 | I2C/SPI | ⭐⭐⭐ |
| `seven_segment.py` | 七段数码管 | GPIO | ⭐⭐ |
| `tm1637_display.py` | TM1637 四位数码管 | GPIO | ⭐⭐ |
| `max7219_matrix.py` | MAX7219 LED 矩阵 | SPI | ⭐⭐⭐ |
| `epaper_display.py` | 电子墨水屏 | SPI | ⭐⭐⭐ |

## 🔌 硬件需求

- LCD1602 + I2C 转接板
- OLED 0.96寸 SSD1306 (128x64)
- 七段数码管（共阴极）
- TM1637 四位数码管模块（可选）

## 📐 接线说明

### LCD1602 I2C
```
VCC ── 5V
GND ── GND
SDA ── GPIO2 (SDA)
SCL ── GPIO3 (SCL)
I2C 地址通常为 0x27 或 0x3F
```

### OLED SSD1306 I2C
```
VCC ── 3.3V
GND ── GND
SDA ── GPIO2 (SDA)
SCL ── GPIO3 (SCL)
I2C 地址通常为 0x3C
```

### 七段数码管（共阴极）
```
a ── GPIO17 (通过 330Ω)
b ── GPIO18
c ── GPIO27
d ── GPIO22
e ── GPIO23
f ── GPIO24
g ── GPIO25
dp── GPIO4
GND── GND
```

## 安装依赖
```bash
# LCD I2C
pip3 install RPLCD smbus2

# OLED
pip3 install adafruit-circuitpython-ssd1306
pip3 install Pillow

# TM1637
pip3 install raspberrypi-tm1637