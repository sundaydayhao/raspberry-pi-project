#!/usr/bin/env python3
"""
RGB LED 颜色控制
使用 PWM 控制 RGB LED 显示各种颜色

硬件连接:
  GPIO17 ──[330Ω]── R (红色引脚)
  GPIO18 ──[330Ω]── G (绿色引脚)
  GPIO27 ──[330Ω]── B (蓝色引脚)
  GND ──────────── 公共阴极 (-)

学习要点:
  - 多路 PWM 控制
  - RGB 颜色混合原理
  - 颜色渐变算法
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    sys.exit(1)

RED_PIN = 17
GREEN_PIN = 18
BLUE_PIN = 27
PWM_FREQ = 1000

# 预定义颜色 (R, G, B) 0-100
COLORS = {
    '红色': (100, 0, 0),
    '绿色': (0, 100, 0),
    '蓝色': (0, 0, 100),
    '黄色': (100, 100, 0),
    '青色': (0, 100, 100),
    '紫色': (100, 0, 100),
    '白色': (100, 100, 100),
    '橙色': (100, 50, 0),
    '粉色': (100, 20, 50),
    '关闭': (0, 0, 0),
}

pwm_r = pwm_g = pwm_b = None

def setup():
    global pwm_r, pwm_g, pwm_b
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in [RED_PIN, GREEN_PIN, BLUE_PIN]:
        GPIO.setup(pin, GPIO.OUT)
    pwm_r = GPIO.PWM(RED_PIN, PWM_FREQ)
    pwm_g = GPIO.PWM(GREEN_PIN, PWM_FREQ)
    pwm_b = GPIO.PWM(BLUE_PIN, PWM_FREQ)
    pwm_r.start(0)
    pwm_g.start(0)
    pwm_b.start(0)

def set_color(r, g, b):
    """设置 RGB 颜色 (0-100)"""
    pwm_r.ChangeDutyCycle(max(0, min(100, r)))
    pwm_g.ChangeDutyCycle(max(0, min(100, g)))
    pwm_b.ChangeDutyCycle(max(0, min(100, b)))

def set_color_hex(hex_color):
    """通过十六进制颜色码设置颜色 (如 #FF0000)"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255 * 100
    g = int(hex_color[2:4], 16) / 255 * 100
    b = int(hex_color[4:6], 16) / 255 * 100
    set_color(r, g, b)

def show_preset_colors():
    """显示预设颜色"""
    print("显示预设颜色...")
    for name, (r, g, b) in COLORS.items():
        if name == '关闭':
            continue
        print(f"  {name}: R={r}, G={g}, B={b}")
        set_color(r, g, b)
        time.sleep(1)
    set_color(0, 0, 0)

def rainbow_cycle(cycles=2, speed=0.02):
    """彩虹渐变效果"""
    print("彩虹渐变效果...")
    for _ in range(cycles):
        # 红 -> 黄 -> 绿
        for i in range(101):
            set_color(100, i, 0)
            time.sleep(speed)
        # 绿 -> 青
        for i in range(101):
            set_color(100 - i, 100, 0)
            time.sleep(speed)
        # 青 -> 蓝
        for i in range(101):
            set_color(0, 100, i)
            time.sleep(speed)
        # 蓝 -> 紫
        for i in range(101):
            set_color(0, 100 - i, 100)
            time.sleep(speed)
        # 紫 -> 红
        for i in range(101):
            set_color(i, 0, 100)
            time.sleep(speed)
        for i in range(101):
            set_color(100, 0, 100 - i)
            time.sleep(speed)

def color_fade(color1, color2, steps=50, delay=0.03):
    """两种颜色之间渐变"""
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    for i in range(steps + 1):
        t = i / steps
        r = r1 + (r2 - r1) * t
        g = g1 + (g2 - g1) * t
        b = b1 + (b2 - b1) * t
        set_color(r, g, b)
        time.sleep(delay)

def candle_effect():
    """蜡烛火焰效果"""
    import random
    print("蜡烛效果 (Ctrl+C 退出)...")
    try:
        while True:
            r = random.randint(80, 100)
            g = random.randint(20, 50)
            b = random.randint(0, 5)
            set_color(r, g, b)
            time.sleep(random.uniform(0.05, 0.15))
    except KeyboardInterrupt:
        pass

def interactive_color():
    """交互式颜色设置"""
    print("\n交互式颜色控制")
    print("输入 R G B 值 (0-100)，或颜色名称，输入 'q' 退出")
    print("可用颜色:", ', '.join(COLORS.keys()))

    while True:
        try:
            inp = input("\n颜色 (R G B 或名称): ").strip()
            if inp.lower() == 'q':
                break
            if inp in COLORS:
                r, g, b = COLORS[inp]
                set_color(r, g, b)
                print(f"  设置为 {inp}: R={r}, G={g}, B={b}")
            elif inp.startswith('#'):
                set_color_hex(inp)
                print(f"  设置为 {inp}")
            else:
                parts = inp.split()
                if len(parts) == 3:
                    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                    set_color(r, g, b)
                    print(f"  设置为 R={r}, G={g}, B={b}")
                else:
                    print("  格式错误，请输入 'R G B' 或颜色名称")
        except (ValueError, KeyboardInterrupt):
            break

def main():
    print("=" * 40)
    print("🌈 RGB LED 颜色控制")
    print("=" * 40)

    setup()

    print("\n选择效果:")
    print("1. 预设颜色展示")
    print("2. 彩虹渐变")
    print("3. 蜡烛效果")
    print("4. 交互式控制")

    choice = input("\n请选择 (1-4): ").strip()

    try:
        if choice == '1':
            show_preset_colors()
        elif choice == '2':
            rainbow_cycle()
        elif choice == '3':
            candle_effect()
        elif choice == '4':
            interactive_color()
        else:
            rainbow_cycle()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        set_color(0, 0, 0)
        pwm_r.stop()
        pwm_g.stop()
        pwm_b.stop()
        GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()