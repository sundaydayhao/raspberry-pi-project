#!/usr/bin/env python3
"""
智能小车控制
综合使用电机驱动、超声波避障、蓝牙/WiFi 遥控

功能:
  - 前进/后退/转向
  - 超声波自动避障
  - 键盘控制
  - 速度调节

硬件需求:
  - L298N 电机驱动模块
  - 直流电机 × 2 (或 × 4)
  - HC-SR04 超声波传感器
  - 外部电源 (7.4V 锂电池)

引脚配置:
  ENA=GPIO18, IN1=GPIO17, IN2=GPIO27
  ENB=GPIO24, IN3=GPIO22, IN4=GPIO23
  TRIG=GPIO5, ECHO=GPIO6

学习要点:
  - 电机协调控制
  - 传感器融合
  - 自主避障算法
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
except ImportError:
    GPIO_AVAILABLE = False
    print("模拟模式（无 GPIO）")

# 电机引脚
ENA = 18; IN1 = 17; IN2 = 27
ENB = 24; IN3 = 22; IN4 = 23

# 超声波引脚
TRIG = 5
ECHO = 6

# 速度配置
DEFAULT_SPEED = 70      # 默认速度 (0-100%)
TURN_SPEED = 60         # 转弯速度
OBSTACLE_DIST = 20      # 避障距离 (cm)

pwm_a = None
pwm_b = None

def setup():
    global pwm_a, pwm_b
    if not GPIO_AVAILABLE:
        print("[模拟] 小车初始化完成")
        return

    for pin in [ENA, IN1, IN2, IN3, IN4, ENB]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, GPIO.LOW)

    pwm_a = GPIO.PWM(ENA, 1000)
    pwm_b = GPIO.PWM(ENB, 1000)
    pwm_a.start(0)
    pwm_b.start(0)
    print("✅ 小车初始化完成")

def set_motor(motor, speed, direction):
    """设置单个电机"""
    speed = max(0, min(100, abs(speed)))
    if motor == 'A':
        if GPIO_AVAILABLE:
            GPIO.output(IN1, GPIO.HIGH if direction > 0 else GPIO.LOW)
            GPIO.output(IN2, GPIO.LOW if direction > 0 else GPIO.HIGH)
            pwm_a.ChangeDutyCycle(speed)
        else:
            print(f"  [模拟] 电机A: {'前' if direction>0 else '后'} {speed}%")
    else:
        if GPIO_AVAILABLE:
            GPIO.output(IN3, GPIO.HIGH if direction > 0 else GPIO.LOW)
            GPIO.output(IN4, GPIO.LOW if direction > 0 else GPIO.HIGH)
            pwm_b.ChangeDutyCycle(speed)
        else:
            print(f"  [模拟] 电机B: {'前' if direction>0 else '后'} {speed}%")

def stop():
    if GPIO_AVAILABLE:
        for pin in [IN1, IN2, IN3, IN4]:
            GPIO.output(pin, GPIO.LOW)
        pwm_a.ChangeDutyCycle(0)
        pwm_b.ChangeDutyCycle(0)
    else:
        print("  [模拟] 停止")

def forward(speed=DEFAULT_SPEED):
    set_motor('A', speed, 1)
    set_motor('B', speed, 1)

def backward(speed=DEFAULT_SPEED):
    set_motor('A', speed, -1)
    set_motor('B', speed, -1)

def turn_left(speed=TURN_SPEED):
    set_motor('A', speed // 2, 1)
    set_motor('B', speed, 1)

def turn_right(speed=TURN_SPEED):
    set_motor('A', speed, 1)
    set_motor('B', speed // 2, 1)

def spin_left(speed=TURN_SPEED):
    set_motor('A', speed, -1)
    set_motor('B', speed, 1)

def spin_right(speed=TURN_SPEED):
    set_motor('A', speed, 1)
    set_motor('B', speed, -1)

def get_distance():
    """超声波测距"""
    if not GPIO_AVAILABLE:
        import random
        return random.uniform(10, 100)

    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    timeout = time.time() + 0.1
    while GPIO.input(ECHO) == 0:
        if time.time() > timeout:
            return 999
    start = time.time()

    timeout = time.time() + 0.1
    while GPIO.input(ECHO) == 1:
        if time.time() > timeout:
            return 999
    end = time.time()

    distance = (end - start) * 34300 / 2
    return round(distance, 1)

def auto_avoid():
    """自动避障模式"""
    print("\n自动避障模式 (Ctrl+C 停止)")
    print(f"避障距离: {OBSTACLE_DIST}cm\n")

    try:
        while True:
            dist = get_distance()
            print(f"  距离: {dist:6.1f}cm", end='')

            if dist > OBSTACLE_DIST:
                forward()
                print(" → 前进", end='\r')
            else:
                stop()
                print(f" → 障碍! 后退转向")
                backward()
                time.sleep(0.5)
                stop()

                # 检测左右哪边更宽敞
                spin_left()
                time.sleep(0.4)
                stop()
                dist_left = get_distance()

                spin_right()
                time.sleep(0.8)
                stop()
                dist_right = get_distance()

                if dist_left > dist_right:
                    spin_left()
                    time.sleep(0.4)
                    stop()
                    print(f"  左转 (左:{dist_left:.0f}cm > 右:{dist_right:.0f}cm)")
                else:
                    print(f"  右转 (右:{dist_right:.0f}cm >= 左:{dist_left:.0f}cm)")

            time.sleep(0.1)

    except KeyboardInterrupt:
        stop()
        print("\n\n自动避障已停止")

def keyboard_control():
    """键盘控制模式"""
    print("\n键盘控制模式")
    print("W=前进 S=后退 A=左转 D=右转")
    print("Q=左旋 E=右旋 空格=停止 X=退出\n")

    try:
        import tty
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1).lower()
                if ch == 'w':
                    forward()
                    print("⬆️  前进", end='\r')
                elif ch == 's':
                    backward()
                    print("⬇️  后退", end='\r')
                elif ch == 'a':
                    turn_left()
                    print("⬅️  左转", end='\r')
                elif ch == 'd':
                    turn_right()
                    print("➡️  右转", end='\r')
                elif ch == 'q':
                    spin_left()
                    print("🔄 左旋", end='\r')
                elif ch == 'e':
                    spin_right()
                    print("🔃 右旋", end='\r')
                elif ch == ' ':
                    stop()
                    print("⏹️  停止", end='\r')
                elif ch in ('x', '\x03'):
                    break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    except ImportError:
        # Windows 或无 termios 环境
        print("(termios 不可用，使用 input 模式)")
        while True:
            cmd = input("命令 (w/s/a/d/q/e/space/x): ").strip().lower()
            if cmd == 'w':
                forward(); time.sleep(0.5); stop()
            elif cmd == 's':
                backward(); time.sleep(0.5); stop()
            elif cmd == 'a':
                turn_left(); time.sleep(0.3); stop()
            elif cmd == 'd':
                turn_right(); time.sleep(0.3); stop()
            elif cmd == 'x':
                break

def demo_sequence():
    """演示动作序列"""
    print("\n演示动作序列...")
    actions = [
        ("前进 2秒", forward, 2),
        ("停止", stop, 0.5),
        ("后退 1秒", backward, 1),
        ("停止", stop, 0.5),
        ("左转 1秒", turn_left, 1),
        ("停止", stop, 0.5),
        ("右转 1秒", turn_right, 1),
        ("停止", stop, 0.5),
        ("原地左旋", spin_left, 0.8),
        ("停止", stop, 0.5),
        ("原地右旋", spin_right, 0.8),
        ("停止", stop, 1),
    ]

    for name, action, duration in actions:
        print(f"  {name}")
        action()
        time.sleep(duration)

    print("演示完成!")

def main():
    print("=" * 50)
    print("🚗 智能小车控制")
    print("=" * 50)

    setup()

    print("\n选择模式:")
    print("1. 演示动作序列")
    print("2. 键盘控制")
    print("3. 自动避障")

    choice = input("\n请选择 (1-3): ").strip()

    try:
        if choice == '1':
            demo_sequence()
        elif choice == '2':
            keyboard_control()
        elif choice == '3':
            auto_avoid()
        else:
            demo_sequence()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        stop()
        if GPIO_AVAILABLE and pwm_a:
            pwm_a.stop()
            pwm_b.stop()
            GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()