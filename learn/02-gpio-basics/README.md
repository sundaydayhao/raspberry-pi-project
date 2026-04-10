# 02 - GPIO 基础操作

## 📋 本章内容

| 文件 | 说明 | 难度 |
|------|------|------|
| `led_blink.py` | LED 闪烁基础 | ⭐ |
| `led_pwm.py` | PWM 控制 LED 亮度 | ⭐⭐ |
| `button_input.py` | 按钮输入检测 | ⭐ |
| `button_led.py` | 按钮控制 LED | ⭐⭐ |
| `traffic_light.py` | 交通灯模拟 | ⭐⭐ |
| `rgb_led.py` | RGB LED 颜色控制 | ⭐⭐ |
| `led_matrix_simple.py` | 简单 LED 矩阵 | ⭐⭐⭐ |

## 🔌 硬件需求

- LED × 3（红、黄、绿）
- RGB LED × 1
- 按钮 × 2
- 电阻 330Ω × 4
- 面包板 × 1
- 杜邦线若干

## 📐 接线说明

### LED 接线
```
GPIO18 ──[330Ω]──[LED+]──[LED-]── GND
```

### 按钮接线
```
GPIO17 ──[按钮]── GND
(内部上拉电阻，按下为 LOW)
```

### RGB LED 接线
```
GPIO17 ──[330Ω]── R (红)
GPIO18 ──[330Ω]── G (绿)  
GPIO27 ──[330Ω]── B (蓝)
GND ──────────── 公共阴极
```

## 🧠 GPIO 基础知识

### BCM vs BOARD 编号
- **BCM**: 使用 Broadcom 芯片引脚编号（推荐）
- **BOARD**: 使用物理引脚编号

```python
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)   # 使用 BCM 编号
# 或
GPIO.setmode(GPIO.BOARD) # 使用物理编号
```

### 输入/输出模式
```python
GPIO.setup(18, GPIO.OUT)  # 设为输出
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 设为输入，上拉
```

### 数字输出
```python
GPIO.output(18, GPIO.HIGH)  # 高电平 (3.3V)
GPIO.output(18, GPIO.LOW)   # 低电平 (0V)
GPIO.output(18, True)       # 等同于 HIGH
GPIO.output(18, False)      # 等同于 LOW
```

### PWM 控制
```python
pwm = GPIO.PWM(18, 1000)  # 引脚18，频率1000Hz
pwm.start(50)              # 启动，占空比50%
pwm.ChangeDutyCycle(75)    # 改变占空比
pwm.stop()                 # 停止
```

## ⚠️ 注意事项

1. **电压**: GPIO 引脚为 3.3V，不能直接连接 5V 设备
2. **电流**: 单个 GPIO 引脚最大输出 16mA，总计不超过 50mA
3. **电阻**: LED 必须串联限流电阻（通常 330Ω）
4. **清理**: 程序结束时调用 `GPIO.cleanup()` 释放资源
5. **短路**: 避免 GPIO 引脚直接连接 VCC 或 GND