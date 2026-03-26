#!/usr/bin/env python3
"""
七段数码管控制
通过 GPIO 控制七段数码管显示数字

硬件连接 (共阴极):
  a ── GPIO17 (通过 330Ω)
  b ── GPIO18
  c ── GPIO27
  d ── GPIO22
  e ── GPIO23
  f ── GPIO24
  g ── GPIO25
  dp── GPIO4
  GND── GND (公共阴极)

七段显示:
   _
  |_|
  |_|.

  a=上, b=右上, c=右下, d=下, e=左下, f=左上, g=中

学习要点:
  - 多引脚协调控制
  - 数字编码
  - 动态扫描（多位数码管）
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("模拟模式")

# 引脚定义 (a, b, c, d, e, f, g, dp)
SEGMENTS = {
    'a': 17, 'b': 18, 'c': 27, 'd': 22,
    'e': 23, 'f': 24, 'g': 25, 'dp': 4
}

# 数字编码 (a, b, c, d, e, f, g)
DIGIT_CODES = {
    0: [1, 1, 1, 1, 1, 1, 0],
    1: [0, 1, 1, 0, 0, 0, 0],
    2: [1, 1, 0, 1, 1, 0, 1],
    3: [1, 1, 1, 1, 0, 0, 1],
    4: [0, 1, 1, 0, 0, 1, 1],
    5: [1, 0, 1, 1, 0, 1, 1],
    6: [1, 0, 1, 1, 1, 1, 1],
    7: [1, 1, 1, 0, 0, 0, 0],
    8: [1, 1, 1, 1, 1, 1, 1],
    9: [1, 1, 1, 1, 0, 1, 1],
    '-': [0, 0, 0, 0, 0, 0, 1],
    ' ': [0, 0, 0, 0, 0, 0, 0],
}

SEG_NAMES = ['a', 'b', 'c', 'd', 'e', 'f', 'g']

def setup():
    if GPIO_AVAILABLE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in SEGMENTS.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

def display_digit(digit, dp=False):
    """显示单个数字"""
    code = DIGIT_CODES.get(digit, DIGIT_CODES[' '])

    if GPIO_AVAILABLE:
        for i, seg_name in enumerate(SEG_NAMES):
            GPIO.output(SEGMENTS[seg_name], GPIO.HIGH if code[i] else GPIO.LOW)
        GPIO.output(SEGMENTS['dp'], GPIO.HIGH if dp else GPIO.LOW)
    else:
        # 终端可视化
        segs = {SEG_NAMES[i]: bool(code[i]) for i in range(7)}
        top = " _ " if segs['a'] else "   "
        mid_top = ("|" if segs['f'] else " ") + ("_" if segs['g'] else " ") + ("|" if segs['b'] else " ")
        mid_bot = ("|" if segs['e'] else " ") + ("_" if segs['d'] else " ") + ("|" if segs['c'] else " ")
        dp_char = "." if dp else " "
        print(f" {top}")
        print(f" {mid_top}")
        print(f" {mid_bot}{dp_char}")

def clear_display():
    """清除显示"""
    if GPIO_AVAILABLE:
        for pin in SEGMENTS.values():
            GPIO.output(pin, GPIO.LOW)

def count_down(start=9):
    """倒计时"""
    print(f"倒计时 {start} -> 0")
    for i in range(start, -1, -1):
        print(f"\n数字: {i}")
        display_digit(i)
        time.sleep(1)
    clear_display()

def count_up(end=9, delay=0.5):
    """正计数"""
    print(f"正计数 0 -> {end}")
    for i in range(end + 1):
        print(f"\n数字: {i}")
        display_digit(i)
        time.sleep(delay)
    clear_display()

def show_all_digits():
    """显示所有数字"""
    print("显示 0-9 所有数字")
    for i in range(10):
        print(f"\n数字: {i}")
        display_digit(i)
        time.sleep(0.8)
    clear_display()

def main():
    print("=" * 40)
    print("🔢 七段数码管控制")
    print("=" * 40)

    setup()

    print("\n选择模式:")
    print("1. 显示所有数字 (0-9)")
    print("2. 倒计时")
    print("3. 正计数")
    print("4. 输入数字显示")

    choice = input("\n请选择 (1-4): ").strip()

    try:
        if choice == '1':
            show_all_digits()
        elif choice == '2':
            count_down(9)
        elif choice == '3':
            count_up(9)
        elif choice == '4':
            while True:
                inp = input("输入数字 (0-9) 或 q 退出: ").strip()
                if inp.lower() == 'q':
                    break
                try:
                    n = int(inp)
                    if 0 <= n <= 9:
                        display_digit(n)
                    else:
                        print("请输入 0-9")
                except ValueError:
                    print("无效输入")
        else:
            show_all_digits()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        clear_display()
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()
