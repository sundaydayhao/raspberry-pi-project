#!/usr/bin/env python3
"""
安防报警系统
综合使用 PIR 传感器、摄像头和通知功能

功能:
  - PIR 运动检测
  - 摄像头抓拍
  - LED/蜂鸣器报警
  - 日志记录
  - (可选) Telegram 通知

硬件需求:
  - PIR 传感器 (GPIO17)
  - 红色 LED (GPIO18)
  - 蜂鸣器 (GPIO25)
  - 摄像头 (可选)

学习要点:
  - 多模块系统集成
  - 事件驱动编程
  - 日志系统设计
"""

import time
import os
import json
import threading
from datetime import datetime

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
except ImportError:
    GPIO_AVAILABLE = False

# 引脚配置
PIR_PIN = 17
LED_PIN = 18
BUZZER_PIN = 25

# 系统配置
CONFIG = {
    'armed': False,
    'alarm_duration': 5,      # 报警持续时间（秒）
    'cooldown': 30,           # 冷却时间（秒）
    'capture_photo': False,   # 是否拍照
    'log_file': 'alarm_log.json',
}

alarm_log = []
last_alarm_time = 0

def setup_gpio():
    """初始化 GPIO"""
    if not GPIO_AVAILABLE:
        return
    GPIO.setup(PIR_PIN, GPIO.IN)
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def trigger_alarm(reason="运动检测"):
    """触发报警"""
    global last_alarm_time

    now = time.time()
    if now - last_alarm_time < CONFIG['cooldown']:
        return  # 冷却中

    last_alarm_time = now
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 记录日志
    event = {
        'timestamp': timestamp,
        'reason': reason,
        'armed': CONFIG['armed']
    }
    alarm_log.append(event)
    print(f"\n🚨 [{timestamp}] 报警! 原因: {reason}")

    if not CONFIG['armed']:
        print("  (系统未布防，仅记录)")
        return

    # 执行报警动作
    def alarm_action():
        duration = CONFIG['alarm_duration']
        end_time = time.time() + duration

        while time.time() < end_time:
            if GPIO_AVAILABLE:
                GPIO.output(LED_PIN, GPIO.HIGH)
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
            time.sleep(0.3)
            if GPIO_AVAILABLE:
                GPIO.output(LED_PIN, GPIO.LOW)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
            time.sleep(0.3)

    alarm_thread = threading.Thread(target=alarm_action, daemon=True)
    alarm_thread.start()

    # 保存日志
    save_log()

def save_log():
    """保存报警日志"""
    with open(CONFIG['log_file'], 'w', encoding='utf-8') as f:
        json.dump(alarm_log, f, ensure_ascii=False, indent=2)

def arm_system():
    """布防"""
    CONFIG['armed'] = True
    print("🔒 系统已布防")
    if GPIO_AVAILABLE:
        # 布防提示：LED 闪烁3次
        for _ in range(3):
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.2)

def disarm_system():
    """撤防"""
    CONFIG['armed'] = False
    print("🔓 系统已撤防")

def monitor_loop():
    """监控主循环"""
    print("\n监控运行中 (Ctrl+C 停止)")
    print(f"状态: {'布防' if CONFIG['armed'] else '撤防'}\n")

    try:
        while True:
            if GPIO_AVAILABLE:
                if GPIO.input(PIR_PIN):
                    trigger_alarm("PIR 运动检测")
                    # 等待 PIR 复位
                    while GPIO.input(PIR_PIN):
                        time.sleep(0.1)
            else:
                # 模拟模式：随机触发
                import random
                if random.random() < 0.05:
                    trigger_alarm("模拟运动检测")

            status = "🔒 布防" if CONFIG['armed'] else "🔓 撤防"
            print(f"  {status} | 报警次数: {len(alarm_log)} | {time.strftime('%H:%M:%S')}", end='\r')
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n监控已停止")
        if alarm_log:
            print(f"共记录 {len(alarm_log)} 次报警事件")
            save_log()
            print(f"日志已保存: {CONFIG['log_file']}")

def show_log():
    """显示报警日志"""
    if not alarm_log:
        print("暂无报警记录")
        return

    print(f"\n📋 报警日志 (共 {len(alarm_log)} 条):")
    for event in alarm_log[-20:]:  # 显示最近20条
        armed_str = "布防" if event.get('armed') else "撤防"
        print(f"  [{event['timestamp']}] {event['reason']} ({armed_str})")

def main():
    print("=" * 50)
    print("🔒 安防报警系统")
    print("=" * 50)

    setup_gpio()

    print("\n命令:")
    print("  1. 布防并开始监控")
    print("  2. 撤防并开始监控（仅记录）")
    print("  3. 查看报警日志")
    print("  4. 测试报警")

    choice = input("\n请选择 (1-4): ").strip()

    try:
        if choice == '1':
            arm_system()
            monitor_loop()
        elif choice == '2':
            disarm_system()
            monitor_loop()
        elif choice == '3':
            show_log()
        elif choice == '4':
            print("测试报警...")
            arm_system()
            trigger_alarm("手动测试")
            time.sleep(CONFIG['alarm_duration'] + 1)
            print("测试完成")
        else:
            monitor_loop()
    finally:
        if GPIO_AVAILABLE:
            GPIO.output(LED_PIN, GPIO.LOW)
            GPIO.output(BUZZER_PIN, GPIO.LOW)
            GPIO.cleanup()

if __name__ == "__main__":
    main()