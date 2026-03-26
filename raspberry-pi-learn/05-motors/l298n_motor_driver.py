#!/usr/bin/env python3
"""
L298N 双路直流电机驱动
控制两个直流电机的速度和方向

硬件连接:
  ENA ── GPIO18 (PWM, 电机A速度)
  IN1 ── GPIO17 (电机A方向)
  IN2 ── GPIO27 (电机A方向)
  IN3 ── GPIO22 (电机B方向)
  IN4 ── GPIO23 (电机B方向)
  ENB ── GPIO24 (PWM, 电机B速度)
  12V ── 外部电源 (7-12V)
  GND ── 共地

学习要点:
  - H桥电路原理
  - 双路电机控制
  - 速度和方向控制
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    sys.exit(1)

# 引脚定义
ENA = 18  # 电机A使能 (PWM)
IN1 = 17  # 电机A方向1
IN2 = 27  # 电机A方向2
IN3 = 22  # 电机B方向1
IN4 = 23  # 电机B方向2
ENB = 24  # 电机B使能 (PWM)

PWM_FREQ = 1000

pwm_a = None
pwm_b = None

def setup():
    global pwm_a, pwm_b
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    for pin in [ENA, IN1, IN2, IN3, IN4, ENB]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    pwm_a = GPIO.PWM(ENA, PWM_FREQ)
    pwm_b = GPIO.PWM(ENB, PWM_FREQ)
    pwm_a.start(0)
    pwm_b.start(0)
    print("✅ L298N 初始化完成")

def motor_a(speed, direction='forward'):
    """控制电机A"""
    speed = max(0, min(100, abs(speed)))
    if direction == 'forward' or speed > 0:
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
    else:
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
    pwm_a.ChangeDutyCycle(speed)

def motor_b(speed, direction='forward'):
    """控制电机B"""
    speed = max(0, min(100, abs(speed)))
    if direction == 'forward' or speed > 0:
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
    else:
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
    pwm_b.ChangeDutyCycle(speed)

def stop():
    """停止所有电机"""
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_a.ChangeDutyCycle(0)
    pwm_b.ChangeDutyCycle(0)

def forward(speed=70):
    """前进"""
    motor_a(speed, 'forward')
    motor_b(speed, 'forward')
    print(f"  ⬆️  前进 (速度: {speed}%)")

def backward(speed=70):
    """后退"""
    motor_a(speed, 'backward')
    motor_b(speed, 'backward')
    print(f"  ⬇️  后退 (速度: {speed}%)")

def turn_left(speed=60):
    """左转"""
    motor_a(speed // 2, 'forward')
    motor_b(speed, 'forward')
    print(f"  ⬅️  左转 (速度: {speed}%)")

def turn_right(speed=60):
    """右转"""
    motor_a(speed, 'forward')
    motor_b(speed // 2, 'forward')
    print(f"  ➡️  右转 (速度: {speed}%)")

def spin_left(speed=60):
    """原地左旋"""
    motor_a(speed, 'backward')
    motor_b(speed, 'forward')
    print(f"  🔄 左旋 (速度: {speed}%)")

def spin_right(speed=60):
    """原地右旋"""
    motor_a(speed, 'forward')
    motor_b(speed, 'backward')
    print(f"  🔃 右旋 (速度: {speed}%)")

def demo_sequence():
    """演示动作序列"""
    print("\n演示动作序列...")
    actions = [
        (forward, 2),
        (stop, 0.5),
        (backward, 2),
        (stop, 0.5),
        (turn_left, 1),
        (stop, 0.5),
        (turn_right, 1),
        (stop, 0.5),
        (spin_left, 1),
        (stop, 0.5),
        (spin_right, 1),
        (stop, 1),
    ]

    for action, duration in actions:
        action()
        time.sleep(duration)

    print("演示完成!")

def speed_test():
    """速度测试"""
    print("\n速度测试...")
    for speed in [20, 40, 60, 80, 100]:
        print(f"  速度: {speed}%")
        motor_a(speed, 'forward')
        motor_b(speed, 'forward')
        time.sleep(1)
    stop()

def keyboard_control():
    """键盘控制（需要 pynput）"""
    print("\n键盘控制模式")
    print("W=前进 S=后退 A=左转 D=右转 Q=左旋 E=右旋 空格=停止 X=退出")

    try:
        import tty
        import termios
        import sys

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(sys.stdin.fileno())
            while True:
                ch = sys.stdin.read(1)
                if ch == 'w':
                    forward()
                elif ch == 's':
                    backward()
                elif ch == 'a':
                    turn_left()
                elif ch == 'd':
                    turn_right()
                elif ch == 'q':
                    spin_left()
                elif ch == 'e':
                    spin_right()
                elif ch == ' ':
                    stop()
                    print("  ⏹️  停止")
                elif ch in ('x', 'X', '\x03'):
                    break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except ImportError:
        print("键盘控制需要 termios 模块（仅 Linux）")

def main():
    print("=" * 40)
    print("🚗 L298N 电机驱动控制")
    print("=" * 40)

    setup()

    print("\n选择模式:")
    print("1. 演示动作序列")
    print("2. 速度测试")
    print("3. 键盘控制")

    choice = input("\n请选择 (1-3): ").strip()

    try:
        if choice == '1':
            demo_sequence()
        elif choice == '2':
            speed_test()
        elif choice == '3':
            keyboard_control()
        else:
            demo_sequence()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        stop()
        pwm_a.stop()
        pwm_b.stop()
        GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()