# 接线图说明

## 📐 通用接线原则

1. **电压匹配**: GPIO 引脚为 3.3V，5V 设备需要电平转换
2. **共地**: 所有设备的 GND 必须连接到树莓派 GND
3. **限流电阻**: LED 必须串联 330Ω 电阻
4. **独立供电**: 电机等大功率设备需要独立电源

---

## 🔌 常用接线图

### LED 基础接线
```
树莓派 GPIO18 ──[330Ω]──[LED 阳极(+)]──[LED 阴极(-)]── GND
```

### 按钮接线（内部上拉）
```
树莓派 GPIO17 ──[按钮一端]
                [按钮另端]── GND
(代码中设置 pull_up_down=GPIO.PUD_UP)
```

### DHT11/DHT22 温湿度传感器
```
VCC  ── 3.3V 或 5V
DATA ── GPIO4 ──[10kΩ]── VCC (上拉电阻)
GND  ── GND
```

### HC-SR04 超声波传感器（5V 转 3.3V）
```
VCC   ── 5V
TRIG  ── GPIO23
ECHO  ──[1kΩ]──┬── GPIO24
               [2kΩ]
                │
               GND
GND   ── GND
```

### HC-SR501 PIR 传感器
```
VCC ── 5V
OUT ── GPIO17
GND ── GND
```

### SG90 舵机
```
红线 (VCC)  ── 5V
棕线 (GND)  ── GND
橙线 (信号) ── GPIO18
```

### L298N 电机驱动
```
ENA ── GPIO18 (PWM)    电机A速度
IN1 ── GPIO17          电机A方向
IN2 ── GPIO27          电机A方向
IN3 ── GPIO22          电机B方向
IN4 ── GPIO23          电机B方向
ENB ── GPIO24 (PWM)    电机B速度
12V ── 外部电源正极
GND ── 外部电源负极 + 树莓派GND
```

### 28BYJ-48 步进电机 (ULN2003)
```
IN1 ── GPIO17
IN2 ── GPIO18
IN3 ── GPIO27
IN4 ── GPIO22
VCC ── 5V (独立电源)
GND ── 共地
```

### LCD1602 I2C
```
VCC ── 5V
GND ── GND
SDA ── GPIO2 (SDA, 物理引脚3)
SCL ── GPIO3 (SCL, 物理引脚5)
```

### OLED SSD1306 I2C
```
VCC ── 3.3V
GND ── GND
SDA ── GPIO2
SCL ── GPIO3
```

### BMP280 气压传感器
```
VCC ── 3.3V
GND ── GND
SDA ── GPIO2
SCL ── GPIO3
CSB ── 3.3V (I2C 模式)
SDO ── GND  (地址 0x76) 或 3.3V (地址 0x77)
```

### MPU6050 陀螺仪
```
VCC ── 3.3V
GND ── GND
SDA ── GPIO2
SCL ── GPIO3
AD0 ── GND (地址 0x68)
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

### RGB LED（共阴极）
```
R 引脚 ──[330Ω]── GPIO17
G 引脚 ──[330Ω]── GPIO18
B 引脚 ──[330Ω]── GPIO27
公共阴极 ────────── GND
```

### 无源蜂鸣器
```
GPIO18 ──[蜂鸣器+]──[蜂鸣器-]── GND
(使用 PWM 控制频率产生不同音调)
```

---

## ⚡ 电源规格

| 引脚 | 电压 | 最大电流 |
|------|------|---------|
| 3.3V | 3.3V | 50mA |
| 5V | 5V | 取决于电源适配器 |
| GPIO | 3.3V | 16mA/引脚, 50mA 总计 |

---

## 🛡️ 保护措施

1. **LED 限流**: 始终使用 220Ω-330Ω 电阻
2. **电平转换**: 5V 信号接 GPIO 前必须分压
3. **续流二极管**: 电机线圈需要并联续流二极管
4. **独立供电**: 电机、继电器等使用独立电源
5. **共地连接**: 所有电源的 GND 必须连接