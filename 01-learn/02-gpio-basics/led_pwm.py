#!/usr/bin/env python3
"""
PWM 控制 LED 亮度
演示使用 PWM 实现 LED 亮度渐变效果

硬件连接:
  GPIO18 ──[330Ω]──[LED+]──[LED-]── GND

学习要点:
  - PWM 原理（脉冲宽度调制）
  - 占空比控制亮度
  - 呼吸灯效果
"""

import time
import math
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    sys.exit(1)

LED_PIN = 18
PWM_FREQ = 1000  # PWM 频率 (Hz)

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(LED_PIN, GPIO.OUT)
    pwm = GPIO.PWM(LED_PIN, PWM_FREQ)
    pwm.start(0)
    return pwm

def fade_in_out(pwm, cycles=3, speed=0.02):
    """渐亮渐灭效果"""
    print("渐亮渐灭效果...")
    for _ in range(cycles):
        for duty in range(0, 101, 2):
            pwm.ChangeDutyCycle(duty)
            time.sleep(speed)
        for duty in range(100, -1, -2):
            pwm.ChangeDutyCycle(duty)
            time.sleep(speed)

def breathing_light(pwm, cycles=5):
    """呼吸灯效果（正弦波）"""
    print("呼吸灯效果...")
    for _ in range(cycles):
        for i in range(0, 360, 3):
            # 使用正弦函数产生平滑的呼吸效果
            duty = (math.sin(math.radians(i)) + 1) / 2 * 100
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.01)

def heartbeat(pwm, beats=10):
    """心跳效果"""
    print("心跳效果...")
    for _ in range(beats):
        # 第一次跳动
        for duty in range(0, 101, 10):
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.02)
        for duty in range(100, 30, -10):
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.02)
        # 第二次跳动
        for duty in range(30, 101, 10):
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.02)
        for duty in range(100, -1, -5):
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.03)
        time.sleep(0.3)

def set_brightness(pwm, percent):
    """设置固定亮度"""
    percent = max(0, min(100, percent))
    pwm.ChangeDutyCycle(percent)
    print(f"亮度设置为: {percent}%")

def interactive_control(pwm):
    """交互式亮度控制"""
    print("\n交互式亮度控制")
    print("输入 0-100 设置亮度，输入 'q' 退出")
    while True:
        try:
            val = input("亮度 (0-100): ").strip()
            if val.lower() == 'q':
                break
            brightness = int(val)
            set_brightness(pwm, brightness)
        except ValueError:
            print("请输入有效数字")
        except KeyboardInterrupt:
            break

def main():
    print("=" * 40)
    print("💡 PWM LED 亮度控制")
    print("=" * 40)

    pwm = setup()

    print("\n选择效果:")
    print("1. 渐亮渐灭")
    print("2. 呼吸灯")
    print("3. 心跳效果")
    print("4. 交互式控制")

    choice = input("\n请选择 (1-4): ").strip()

    try:
        if choice == '1':
            fade_in_out(pwm)
        elif choice == '2':
            breathing_light(pwm)
        elif choice == '3':
            heartbeat(pwm)
        elif choice == '4':
            interactive_control(pwm)
        else:
            breathing_light(pwm)
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        pwm.stop()
        GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()