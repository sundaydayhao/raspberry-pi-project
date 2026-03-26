#!/usr/bin/env python3
"""
按钮控制 LED
演示按钮输入控制 LED 输出的综合应用

硬件连接:
  GPIO17 ──[按钮]── GND
  GPIO18 ──[330Ω]──[LED]── GND

学习要点:
  - 输入输出综合应用
  - 状态机设计
  - 多按钮控制
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    sys.exit(1)

BUTTON_PIN = 17
LED_PIN = 18

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.LOW)

def toggle_mode():
    """按钮切换 LED 开关"""
    print("切换模式: 按一次开，再按一次关 (Ctrl+C 退出)")
    led_state = False
    last_button = GPIO.HIGH

    try:
        while True:
            btn = GPIO.input(BUTTON_PIN)
            if btn == GPIO.LOW and last_button == GPIO.HIGH:
                led_state = not led_state
                GPIO.output(LED_PIN, GPIO.HIGH if led_state else GPIO.LOW)
                print(f"  LED: {'💡 开' if led_state else '⚫ 关'}")
                time.sleep(0.05)
            last_button = btn
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass

def hold_mode():
    """按住按钮 LED 亮，松开熄灭"""
    print("按住模式: 按住按钮 LED 亮，松开熄灭 (Ctrl+C 退出)")
    try:
        while True:
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                GPIO.output(LED_PIN, GPIO.HIGH)
                print("  💡 按住中...", end='\r')
            else:
                GPIO.output(LED_PIN, GPIO.LOW)
                print("  ⚫ 等待按下...", end='\r')
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass

def count_blink_mode():
    """按几次，LED 闪几下"""
    print("计数模式: 按几次按钮，LED 就闪几下 (Ctrl+C 退出)")
    print("按下按钮后等待1秒开始闪烁\n")

    count = 0
    last_btn = GPIO.HIGH
    last_press_time = time.time()

    try:
        while True:
            btn = GPIO.input(BUTTON_PIN)
            now = time.time()

            if btn == GPIO.LOW and last_btn == GPIO.HIGH:
                count += 1
                last_press_time = now
                print(f"  按下第 {count} 次")
                time.sleep(0.05)

            # 超过1秒没有按下，执行闪烁
            if count > 0 and now - last_press_time > 1.0:
                print(f"  LED 闪烁 {count} 次...")
                for _ in range(count):
                    GPIO.output(LED_PIN, GPIO.HIGH)
                    time.sleep(0.3)
                    GPIO.output(LED_PIN, GPIO.LOW)
                    time.sleep(0.3)
                count = 0
                print("  等待下次输入...\n")

            last_btn = btn
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass

def main():
    print("=" * 40)
    print("🔘💡 按钮控制 LED")
    print("=" * 40)

    setup()

    print("选择模式:")
    print("1. 切换模式（按一次开/关）")
    print("2. 按住模式（按住亮）")
    print("3. 计数闪烁模式")

    choice = input("\n请选择 (1-3): ").strip()

    try:
        if choice == '1':
            toggle_mode()
        elif choice == '2':
            hold_mode()
        elif choice == '3':
            count_blink_mode()
        else:
            toggle_mode()
    finally:
        GPIO.output(LED_PIN, GPIO.LOW)
        GPIO.cleanup()
        print("\nGPIO 资源已释放")

if __name__ == "__main__":
    main()