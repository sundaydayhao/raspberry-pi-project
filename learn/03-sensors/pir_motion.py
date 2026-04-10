#!/usr/bin/env python3
"""
HC-SR501 PIR 人体红外运动传感器
检测人体运动

硬件连接:
  VCC ── 5V
  OUT ── GPIO17
  GND ── GND

传感器调节:
  - 灵敏度旋钮: 顺时针增大检测距离
  - 延时旋钮: 顺时针增大触发后保持时间
  - 跳线: H=重复触发, L=单次触发

学习要点:
  - PIR 传感器工作原理
  - 中断检测运动
  - 事件记录
"""

import time
import sys
from datetime import datetime

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    sys.exit(1)

PIR_PIN = 17
LED_PIN = 18  # 可选：运动指示 LED

motion_count = 0
motion_log = []

def setup(use_led=False):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIR_PIN, GPIO.IN)
    if use_led:
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, GPIO.LOW)

def motion_callback(channel):
    """运动检测回调函数"""
    global motion_count
    motion_count += 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    motion_log.append(timestamp)
    print(f"\n  🚶 检测到运动! [{timestamp}] 第 {motion_count} 次")

def simple_detect():
    """简单运动检测"""
    print(f"\n运动检测模式 (GPIO{PIR_PIN})")
    print("等待传感器稳定 (2秒)...")
    time.sleep(2)
    print("开始检测... (Ctrl+C 退出)\n")

    try:
        while True:
            if GPIO.input(PIR_PIN):
                print("  🚶 检测到运动!", end='\r')
            else:
                print("  😴 无运动...  ", end='\r')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n检测已停止")

def interrupt_detect():
    """中断方式检测（推荐）"""
    global motion_count
    motion_count = 0

    print(f"\n中断检测模式 (GPIO{PIR_PIN})")
    print("等待传感器稳定 (2秒)...")
    time.sleep(2)
    print("开始检测... (Ctrl+C 退出)\n")

    GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=motion_callback)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.remove_event_detect(PIR_PIN)
        print(f"\n\n共检测到 {motion_count} 次运动")
        if motion_log:
            print("运动记录:")
            for log in motion_log[-10:]:  # 显示最后10条
                print(f"  {log}")

def security_monitor():
    """安防监控模式"""
    print("\n安防监控模式")
    print("检测到运动时发出警报\n")

    # 可选：连接蜂鸣器
    BUZZER_PIN = 25
    try:
        GPIO.setup(BUZZER_PIN, GPIO.OUT)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        has_buzzer = True
    except Exception:
        has_buzzer = False

    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.LOW)

    print("等待传感器稳定 (3秒)...")
    time.sleep(3)
    print("监控已启动!\n")

    alert_count = 0

    try:
        while True:
            if GPIO.input(PIR_PIN):
                alert_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"  ⚠️  [{timestamp}] 警报! 检测到入侵! (第{alert_count}次)")

                # 闪烁 LED
                for _ in range(5):
                    GPIO.output(LED_PIN, GPIO.HIGH)
                    if has_buzzer:
                        GPIO.output(BUZZER_PIN, GPIO.HIGH)
                    time.sleep(0.2)
                    GPIO.output(LED_PIN, GPIO.LOW)
                    if has_buzzer:
                        GPIO.output(BUZZER_PIN, GPIO.LOW)
                    time.sleep(0.2)

                # 等待传感器复位
                while GPIO.input(PIR_PIN):
                    time.sleep(0.1)
                print(f"  ✅ 区域已清空")
            else:
                print(f"  🔒 监控中... 警报次数: {alert_count}", end='\r')

            time.sleep(0.1)

    except KeyboardInterrupt:
        GPIO.output(LED_PIN, GPIO.LOW)
        print(f"\n\n监控已停止，共触发 {alert_count} 次警报")

def activity_logger(duration=60):
    """活动记录器"""
    print(f"\n活动记录模式 (记录 {duration} 秒)")

    events = []
    last_state = False
    end_time = time.time() + duration

    print("等待传感器稳定 (2秒)...")
    time.sleep(2)
    print("开始记录...\n")

    while time.time() < end_time:
        current_state = bool(GPIO.input(PIR_PIN))
        remaining = end_time - time.time()

        if current_state != last_state:
            timestamp = time.time()
            event_type = "进入" if current_state else "离开"
            events.append((timestamp, event_type))
            print(f"  [{time.strftime('%H:%M:%S')}] {event_type} 检测区域")

        last_state = current_state
        print(f"  剩余: {remaining:.0f}s  状态: {'有人' if current_state else '无人'}", end='\r')
        time.sleep(0.1)

    print(f"\n\n📊 活动统计:")
    print(f"  总事件数: {len(events)}")
    enter_count = sum(1 for _, t in events if t == "进入")
    print(f"  进入次数: {enter_count}")
    print(f"  离开次数: {len(events) - enter_count}")

def main():
    print("=" * 40)
    print("🚶 PIR 人体红外传感器")
    print("=" * 40)
    print(f"传感器引脚: GPIO{PIR_PIN}")
    print()

    setup()

    print("选择模式:")
    print("1. 简单检测")
    print("2. 中断检测（推荐）")
    print("3. 安防监控")
    print("4. 活动记录")

    choice = input("\n请选择 (1-4): ").strip()

    try:
        if choice == '1':
            simple_detect()
        elif choice == '2':
            interrupt_detect()
        elif choice == '3':
            security_monitor()
        elif choice == '4':
            activity_logger()
        else:
            interrupt_detect()
    finally:
        GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()
