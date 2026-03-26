#!/usr/bin/env python3
"""
HC-SR04 超声波测距传感器
测量物体距离

硬件连接:
  VCC   ── 5V
  TRIG  ── GPIO23
  ECHO  ── 分压后接 GPIO24 (5V->3.3V)
  GND   ── GND

  分压电路: ECHO ──[1kΩ]──┬── GPIO24
                          [2kΩ]
                           │
                          GND

学习要点:
  - 超声波测距原理
  - 精确时间测量
  - 距离计算公式
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    sys.exit(1)

TRIG_PIN = 23
ECHO_PIN = 24
SPEED_OF_SOUND = 34300  # cm/s (20°C)

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)
    GPIO.output(TRIG_PIN, GPIO.LOW)
    time.sleep(0.5)  # 传感器稳定时间

def measure_distance():
    """
    测量距离
    返回距离（厘米），失败返回 None
    """
    # 发送 10μs 触发脉冲
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)  # 10μs
    GPIO.output(TRIG_PIN, GPIO.LOW)

    # 等待回波开始
    timeout = time.time() + 0.1  # 100ms 超时
    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        if time.time() > timeout:
            return None
    pulse_start = time.time()

    # 等待回波结束
    timeout = time.time() + 0.1
    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        if time.time() > timeout:
            return None
    pulse_end = time.time()

    # 计算距离
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * SPEED_OF_SOUND / 2

    # 有效范围: 2cm - 400cm
    if 2 <= distance <= 400:
        return round(distance, 1)
    return None

def measure_average(samples=5):
    """多次测量取平均值"""
    measurements = []
    for _ in range(samples):
        dist = measure_distance()
        if dist is not None:
            measurements.append(dist)
        time.sleep(0.06)

    if measurements:
        return round(sum(measurements) / len(measurements), 1)
    return None

def single_measure():
    """单次测量"""
    print(f"\n测量距离...")
    dist = measure_average()
    if dist is not None:
        print(f"  📏 距离: {dist} cm ({dist/100:.2f} m)")
        # 距离可视化
        bar_len = min(40, int(dist / 10))
        bar = "█" * bar_len
        print(f"  [{bar:<40}] {dist}cm")
    else:
        print("  ❌ 测量失败，请检查接线")

def continuous_measure(interval=0.5):
    """持续测量"""
    print(f"\n持续测距 (Ctrl+C 退出)")
    print("-" * 40)

    try:
        while True:
            dist = measure_distance()
            if dist is not None:
                bar_len = min(30, int(dist / 10))
                bar = "█" * bar_len
                print(f"  📏 {dist:6.1f} cm  [{bar:<30}]", end='\r')
            else:
                print("  ❌ 超出范围              ", end='\r')
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n测量已停止")

def proximity_alarm(threshold=20):
    """接近报警"""
    print(f"\n接近报警模式 (阈值: {threshold}cm)")
    print("当物体距离小于阈值时报警\n")

    try:
        import RPi.GPIO as GPIO
        BUZZER_PIN = 25
        GPIO.setup(BUZZER_PIN, GPIO.OUT)
        has_buzzer = True
    except Exception:
        has_buzzer = False

    try:
        while True:
            dist = measure_distance()
            if dist is not None:
                if dist < threshold:
                    print(f"  ⚠️  警告! 距离: {dist:.1f}cm < {threshold}cm")
                    if has_buzzer:
                        GPIO.output(BUZZER_PIN, GPIO.HIGH)
                        time.sleep(0.1)
                        GPIO.output(BUZZER_PIN, GPIO.LOW)
                else:
                    print(f"  ✅ 安全  距离: {dist:.1f}cm", end='\r')
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n\n报警已停止")

def ruler_mode():
    """电子尺模式"""
    print("\n电子尺模式 - 按 Enter 测量，输入 'q' 退出")
    measurements = []

    while True:
        inp = input("\n按 Enter 测量: ").strip()
        if inp.lower() == 'q':
            break

        dist = measure_average(10)
        if dist is not None:
            measurements.append(dist)
            print(f"  测量 {len(measurements)}: {dist} cm")

            if len(measurements) >= 2:
                diff = abs(measurements[-1] - measurements[-2])
                print(f"  与上次差值: {diff:.1f} cm")
        else:
            print("  测量失败")

    if measurements:
        print(f"\n所有测量值: {measurements}")
        print(f"最小值: {min(measurements)} cm")
        print(f"最大值: {max(measurements)} cm")

def main():
    print("=" * 40)
    print("📏 HC-SR04 超声波测距")
    print("=" * 40)
    print(f"TRIG: GPIO{TRIG_PIN}")
    print(f"ECHO: GPIO{ECHO_PIN}")
    print()

    setup()

    print("选择模式:")
    print("1. 单次测量")
    print("2. 持续测量")
    print("3. 接近报警")
    print("4. 电子尺模式")

    choice = input("\n请选择 (1-4): ").strip()

    try:
        if choice == '1':
            single_measure()
        elif choice == '2':
            continuous_measure()
        elif choice == '3':
            threshold = input("设置报警距离 (cm, 默认20): ").strip()
            threshold = int(threshold) if threshold.isdigit() else 20
            proximity_alarm(threshold)
        elif choice == '4':
            ruler_mode()
        else:
            continuous_measure()
    finally:
        GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()