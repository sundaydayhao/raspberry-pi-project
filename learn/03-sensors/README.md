# 03 - 传感器应用

## 📋 本章内容

| 文件 | 传感器 | 接口 | 难度 |
|------|--------|------|------|
| `dht11_temperature.py` | DHT11 温湿度 | GPIO | ⭐⭐ |
| `dht22_temperature.py` | DHT22 高精度温湿度 | GPIO | ⭐⭐ |
| `ultrasonic_distance.py` | HC-SR04 超声波测距 | GPIO | ⭐⭐ |
| `pir_motion.py` | HC-SR501 人体红外 | GPIO | ⭐ |
| `light_sensor_ldr.py` | LDR 光敏电阻 | ADC | ⭐⭐ |
| `soil_moisture.py` | 土壤湿度传感器 | ADC | ⭐⭐ |
| `mq2_gas_sensor.py` | MQ-2 烟雾/气体 | ADC | ⭐⭐ |
| `bmp280_pressure.py` | BMP280 气压温度 | I2C | ⭐⭐⭐ |
| `mpu6050_gyro.py` | MPU6050 陀螺仪 | I2C | ⭐⭐⭐ |

## 🔌 硬件需求

- DHT11 或 DHT22 温湿度传感器
- HC-SR04 超声波传感器
- HC-SR501 PIR 人体红外传感器
- MCP3008 ADC 转换芯片（用于模拟传感器）
- BMP280 气压传感器（可选）
- MPU6050 陀螺仪（可选）

## 📐 接线说明

### DHT11/DHT22
```
VCC  ── 3.3V 或 5V
DATA ── GPIO4 (通过 10kΩ 上拉到 VCC)
GND  ── GND
```

### HC-SR04 超声波
```
VCC   ── 5V
TRIG  ── GPIO23
ECHO  ── GPIO24 (通过分压电路降到 3.3V!)
GND   ── GND

分压电路: ECHO ──[1kΩ]──[GPIO24]──[2kΩ]── GND
```

### HC-SR501 PIR
```
VCC  ── 5V
OUT  ── GPIO17
GND  ── GND
```

### MCP3008 ADC (SPI)
```
VDD  ── 3.3V
VREF ── 3.3V
AGND ── GND
CLK  ── GPIO11 (SCLK)
DOUT ── GPIO9  (MISO)
DIN  ── GPIO10 (MOSI)
CS   ── GPIO8  (CE0)
DGND ── GND
```

## ⚠️ 注意事项

1. DHT11/DHT22 读取间隔至少 2 秒
2. HC-SR04 的 ECHO 引脚输出 5V，必须分压后才能接 GPIO
3. 模拟传感器需要 ADC 芯片（树莓派没有内置 ADC）
4. I2C 传感器需要先启用 I2C 接口