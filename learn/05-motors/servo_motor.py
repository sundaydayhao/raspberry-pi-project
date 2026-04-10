#!/usr/bin/env python3
"""
SG90 舵机控制
使用 PWM 控制舵机角度

硬件连接:
  红线 (VCC) ── 5V
  棕线 (GND) ── GND
  橙线 (信号) ── GPIO18

舵机 PWM 参数:
  频率: 50Hz (周期 20ms)
  0°:   占空比 2.5% (0.5ms)
  90°:  占空比 7.5% (1.5ms)
  180°: 占空比 12.5% (2.5ms)

学习要点:
  - PWM 控制舵机
  - 角度到占空比转换
  - 平滑运动控制
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    sys.exit(1)

SERVO_PIN = 18
PWM_FREQ = 50  # 50Hz

def angle_to_duty(angle):
    """将角度转换为占空比"""
    # 0° = 2.5%, 180° = 12.5%
    duty = 2.5 + (angle / 180.0) * 10.0
    return duty

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, PWM_FREQ)
    pwm.start(0)
    return pwm

def set_angle(pwm, angle, delay=0.3):
    """设置舵机角度"""
    angle = max(0, min(180, angle))
    duty = angle_to_duty(angle)
    pwm.ChangeDutyCycle(duty)
    time.sleep(delay)
    pwm.ChangeDutyCycle(0)  # 停止 PWM 防止抖动

def sweep(pwm, start=0, end=180, step=5, delay=0.05):
    """舵机扫描"""
    print(f"扫描 {start}° -> {end}°")
    angles = range(start, end + 1, step) if start < end else range(start, end - 1, -step)
    for angle in angles:
        duty = angle_to_duty(angle)
        pwm.ChangeDutyCycle(duty)
        time.sleep(delay)
    pwm.ChangeDutyCycle(0)

def smooth_move(pwm, from_angle, to_angle, steps=50, total_time=1.0):
    """平滑移动到目标角度"""
    delay = total_time / steps
    for i in range(steps + 1):
        angle = from_angle + (to_angle - from_angle) * i / steps
        duty = angle_to_duty(angle)
        pwm.ChangeDutyCycle(duty)
        time.sleep(delay)
    pwm.ChangeDutyCycle(0)

def interactive_control(pwm):
    """交互式角度控制"""
    print("\n交互式舵机控制")
    print("输入角度 (0-180)，输入 'q' 退出")
    current_angle = 90
    set_angle(pwm, current_angle)

    while True:
        try:
            inp = input(f"角度 (当前:{current_angle}°): ").strip()
            if inp.lower() == 'q':
                break
            angle = int(inp)
            if 0 <= angle <= 180:
                smooth_move(pwm, current_angle, angle)
                current_angle = angle
                print(f"  已移动到 {angle}°")
            else:
                print("  角度范围: 0-180")
        except ValueError:
            print("  请输入有效数字")
        except KeyboardInterrupt:
            break

def pendulum_effect(pwm, cycles=5):
    """钟摆效果"""
    print("钟摆效果...")
    current = 90
    for _ in range(cycles):
        smooth_move(pwm, current, 0, steps=30, total_time=0.5)
        smooth_move(pwm, 0, 180, steps=60, total_time=1.0)
        smooth_move(pwm, 180, 90, steps=30, total_time=0.5)
        current = 90

def main():
    print("=" * 40)
    print("⚙️  SG90 舵机控制")
    print("=" * 40)
    print(f"信号引脚: GPIO{SERVO_PIN}")
    print()

    pwm = setup()

    # 初始化到中间位置
    print("初始化到 90°...")
    set_angle(pwm, 90)
    time.sleep(1)

    print("\n选择模式:")
    print("1. 扫描 (0° -> 180° -> 0°)")
    print("2. 交互式控制")
    print("3. 钟摆效果")
    print("4. 预设位置演示")

    choice = input("\n请选择 (1-4): ").strip()

    try:
        if choice == '1':
            for _ in range(3):
                sweep(pwm, 0, 180)
                sweep(pwm, 180, 0)
        elif choice == '2':
            interactive_control(pwm)
        elif choice == '3':
            pendulum_effect(pwm)
        elif choice == '4':
            for angle in [0, 45, 90, 135, 180, 90]:
                print(f"  移动到 {angle}°")
                set_angle(pwm, angle, delay=0.5)
                time.sleep(0.5)
        else:
            sweep(pwm, 0, 180)
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        set_angle(pwm, 90)  # 回到中间位置
        pwm.stop()
        GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()