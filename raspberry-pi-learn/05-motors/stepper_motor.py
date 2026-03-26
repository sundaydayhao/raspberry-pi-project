#!/usr/bin/env python3
"""
28BYJ-48 步进电机控制
通过 ULN2003 驱动板控制步进电机

硬件连接 (ULN2003):
  IN1 ── GPIO17
  IN2 ── GPIO18
  IN3 ── GPIO27
  IN4 ── GPIO22
  VCC ── 5V (独立电源)
  GND ── 共地

步进电机参数:
  步距角: 5.625° / 64 (减速比)
  每圈步数: 512 步 (半步模式)
  转速: 约 15 RPM (最大)

学习要点:
  - 步进电机工作原理
  - 全步/半步驱动模式
  - 精确角度控制
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    sys.exit(1)

IN1 = 17
IN2 = 18
IN3 = 27
IN4 = 22

PINS = [IN1, IN2, IN3, IN4]

# 半步序列（8步，更平滑）
HALF_STEP_SEQ = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1],
]

# 全步序列（4步）
FULL_STEP_SEQ = [
    [1, 0, 0, 1],
    [1, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 1],
]

STEPS_PER_REV = 512  # 半步模式下每圈步数

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    print("✅ 步进电机初始化完成")

def set_step(step_seq, step_index):
    """设置线圈状态"""
    seq = step_seq[step_index % len(step_seq)]
    for i, pin in enumerate(PINS):
        GPIO.output(pin, GPIO.HIGH if seq[i] else GPIO.LOW)

def all_off():
    """关闭所有线圈"""
    for pin in PINS:
        GPIO.output(pin, GPIO.LOW)

def step(steps, direction=1, delay=0.002, mode='half'):
    """
    执行指定步数
    steps: 步数
    direction: 1=顺时针, -1=逆时针
    delay: 步间延时（秒）
    mode: 'half'=半步, 'full'=全步
    """
    seq = HALF_STEP_SEQ if mode == 'half' else FULL_STEP_SEQ
    seq_len = len(seq)

    step_index = 0
    for i in range(abs(steps)):
        set_step(seq, step_index)
        step_index = (step_index + direction) % seq_len
        time.sleep(delay)

    all_off()

def rotate_degrees(degrees, direction=1, delay=0.002):
    """旋转指定角度"""
    steps = int(STEPS_PER_REV * abs(degrees) / 360)
    print(f"旋转 {degrees}° ({steps} 步)")
    step(steps, direction, delay)

def rotate_revolutions(revs, direction=1, delay=0.002):
    """旋转指定圈数"""
    steps = int(STEPS_PER_REV * abs(revs))
    print(f"旋转 {revs} 圈 ({steps} 步)")
    step(steps, direction, delay)

def interactive_control():
    """交互式控制"""
    print("\n交互式步进电机控制")
    print("命令: r <角度> [方向(1/-1)] | c <圈数> | q=退出")
    print("示例: r 90  或  r 180 -1  或  c 2")

    while True:
        try:
            inp = input("\n命令: ").strip()
            if inp.lower() == 'q':
                break
            parts = inp.split()
            if not parts:
                continue

            cmd = parts[0].lower()
            if cmd == 'r' and len(parts) >= 2:
                degrees = float(parts[1])
                direction = int(parts[2]) if len(parts) >= 3 else 1
                rotate_degrees(degrees, direction)
            elif cmd == 'c' and len(parts) >= 2:
                revs = float(parts[1])
                direction = int(parts[2]) if len(parts) >= 3 else 1
                rotate_revolutions(revs, direction)
            else:
                print("  无效命令")
        except (ValueError, IndexError):
            print("  输入格式错误")
        except KeyboardInterrupt:
            break

def demo():
    """演示"""
    print("\n步进电机演示...")
    print("顺时针旋转一圈")
    rotate_revolutions(1, direction=1)
    time.sleep(0.5)

    print("逆时针旋转一圈")
    rotate_revolutions(1, direction=-1)
    time.sleep(0.5)

    print("旋转 90°")
    rotate_degrees(90, direction=1)
    time.sleep(0.5)

    print("旋转 -90°（逆时针）")
    rotate_degrees(90, direction=-1)
    print("演示完成!")

def main():
    print("=" * 40)
    print("⚙️  28BYJ-48 步进电机控制")
    print("=" * 40)
    print(f"引脚: IN1=GPIO{IN1}, IN2=GPIO{IN2}, IN3=GPIO{IN3}, IN4=GPIO{IN4}")
    print()

    setup()

    print("选择模式:")
    print("1. 演示")
    print("2. 交互式控制")
    print("3. 连续旋转测试")

    choice = input("\n请选择 (1-3): ").strip()

    try:
        if choice == '1':
            demo()
        elif choice == '2':
            interactive_control()
        elif choice == '3':
            print("连续旋转 (Ctrl+C 停止)")
            while True:
                step(8, direction=1, delay=0.002)
        else:
            demo()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        all_off()
        GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()
