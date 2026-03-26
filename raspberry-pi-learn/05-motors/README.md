# 05 - 电机控制

## 📋 本章内容

| 文件 | 说明 | 难度 |
|------|------|------|
| `servo_motor.py` | SG90 舵机控制 | ⭐⭐ |
| `dc_motor.py` | 直流电机控制 | ⭐⭐ |
| `l298n_motor_driver.py` | L298N 双路电机驱动 | ⭐⭐⭐ |
| `stepper_motor.py` | 28BYJ-48 步进电机 | ⭐⭐⭐ |
| `robot_car_control.py` | 小车运动控制 | ⭐⭐⭐ |

## 🔌 硬件需求

- SG90 舵机 × 1
- 直流电机 × 2
- L298N 电机驱动模块 × 1
- 28BYJ-48 步进电机 + ULN2003 驱动板 × 1
- 外部电源（电机需要独立供电）

## 📐 接线说明

### SG90 舵机
```
红线 (VCC) ── 5V
棕线 (GND) ── GND
橙线 (信号) ── GPIO18 (PWM)
```

### L298N 电机驱动
```
ENA ── GPIO18 (PWM, 速度控制)
IN1 ── GPIO17
IN2 ── GPIO27
IN3 ── GPIO22
IN4 ── GPIO23
ENB ── GPIO24 (PWM, 速度控制)
12V ── 外部电源 7-12V
GND ── 共地
```

### 28BYJ-48 步进电机 (ULN2003)
```
IN1 ── GPIO17
IN2 ── GPIO18
IN3 ── GPIO27
IN4 ── GPIO22
VCC ── 5V
GND ── GND
```

## ⚠️ 注意事项

1. 电机需要独立电源，不要用树莓派 GPIO 直接驱动
2. 共地：树莓派 GND 和电机电源 GND 必须连接
3. 舵机可以用 5V 供电，但大型舵机需要独立电源
4. 步进电机驱动时注意散热