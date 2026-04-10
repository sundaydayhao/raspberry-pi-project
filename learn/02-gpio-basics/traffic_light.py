#!/usr/bin/env python3
"""
交通灯模拟
使用三色 LED 模拟交通灯控制系统

硬件连接:
  GPIO17 ──[330Ω]──[红色LED]── GND
  GPIO18 ──[330Ω]──[黄色LED]── GND
  GPIO27 ──[330Ω]──[绿色LED]── GND

学习要点:
  - 多 GPIO 引脚控制
  - 状态机设计
  - 定时控制
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    sys.exit(1)

RED_PIN = 17
YELLOW_PIN = 18
GREEN_PIN = 27

# 交通灯时序（秒）
RED_TIME = 5
YELLOW_TIME = 2
GREEN_TIME = 5

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in [RED_PIN, YELLOW_PIN, GREEN_PIN]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

def all_off():
    for pin in [RED_PIN, YELLOW_PIN, GREEN_PIN]:
        GPIO.output(pin, GPIO.LOW)

def set_light(red=False, yellow=False, green=False):
    GPIO.output(RED_PIN, GPIO.HIGH if red else GPIO.LOW)
    GPIO.output(YELLOW_PIN, GPIO.HIGH if yellow else GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.HIGH if green else GPIO.LOW)

def traffic_light_cycle():
    """标准交通灯循环"""
    print("交通灯模拟启动 (Ctrl+C 停止)\n")
    cycle = 0

    try:
        while True:
            cycle += 1
            print(f"--- 第 {cycle} 轮 ---")

            # 红灯
            set_light(red=True)
            print(f"🔴 红灯 ({RED_TIME}秒)")
            time.sleep(RED_TIME)

            # 绿灯
            set_light(green=True)
            print(f"🟢 绿灯 ({GREEN_TIME}秒)")
            time.sleep(GREEN_TIME)

            # 黄灯（闪烁）
            print(f"🟡 黄灯 ({YELLOW_TIME}秒)")
            for _ in range(YELLOW_TIME * 2):
                set_light(yellow=True)
                time.sleep(0.25)
                set_light()
                time.sleep(0.25)

    except KeyboardInterrupt:
        print("\n交通灯已停止")

def pedestrian_crossing():
    """行人过街模式（带按钮）"""
    BUTTON_PIN = 22
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print("行人过街模式")
    print("按下按钮请求过街\n")

    try:
        while True:
            # 正常行车（绿灯）
            set_light(green=True)
            print("🟢 行车绿灯", end='\r')

            # 检测行人按钮
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                print("\n行人请求过街!")
                time.sleep(1)

                # 切换到行人通行
                set_light(yellow=True)
                print("🟡 准备停车...")
                time.sleep(2)

                set_light(red=True)
                print("🔴 车辆停止，行人通行!")
                time.sleep(5)

                # 恢复行车
                set_light(yellow=True)
                print("🟡 行人请注意，即将恢复行车")
                time.sleep(2)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n已停止")

def emergency_mode():
    """紧急模式（黄灯闪烁）"""
    print("紧急模式：黄灯闪烁 (Ctrl+C 退出)")
    try:
        while True:
            set_light(yellow=True)
            time.sleep(0.5)
            all_off()
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

def main():
    print("=" * 40)
    print("🚦 交通灯模拟系统")
    print("=" * 40)
    print(f"红灯: GPIO{RED_PIN}")
    print(f"黄灯: GPIO{YELLOW_PIN}")
    print(f"绿灯: GPIO{GREEN_PIN}")
    print()

    setup()

    print("选择模式:")
    print("1. 标准交通灯循环")
    print("2. 行人过街模式")
    print("3. 紧急模式（黄灯闪烁）")

    choice = input("\n请选择 (1-3): ").strip()

    try:
        if choice == '1':
            traffic_light_cycle()
        elif choice == '2':
            pedestrian_crossing()
        elif choice == '3':
            emergency_mode()
        else:
            traffic_light_cycle()
    finally:
        all_off()
        GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()