#!/usr/bin/env python3
"""
按钮输入检测
演示 GPIO 数字输入读取按钮状态

硬件连接:
  GPIO17 ──[按钮]── GND
  (使用内部上拉电阻，按下时为 LOW)

学习要点:
  - GPIO 输入模式
  - 上拉/下拉电阻
  - 按钮防抖处理
  - 中断回调函数
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    sys.exit(1)

BUTTON_PIN = 17
press_count = 0
last_press_time = 0

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # 设置为输入，启用内部上拉电阻
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def read_button_polling():
    """轮询方式读取按钮（简单但占用 CPU）"""
    print("轮询模式 - 等待按钮按下 (Ctrl+C 退出)")
    last_state = GPIO.HIGH
    press_count = 0

    try:
        while True:
            current_state = GPIO.input(BUTTON_PIN)

            if current_state == GPIO.LOW and last_state == GPIO.HIGH:
                press_count += 1
                print(f"  按钮按下! 第 {press_count} 次")
                time.sleep(0.05)  # 防抖延时

            elif current_state == GPIO.HIGH and last_state == GPIO.LOW:
                print(f"  按钮释放")

            last_state = current_state
            time.sleep(0.01)

    except KeyboardInterrupt:
        print(f"\n共按下 {press_count} 次")

def button_callback(channel):
    """按钮中断回调函数"""
    global press_count, last_press_time
    current_time = time.time()

    # 软件防抖：50ms 内的重复触发忽略
    if current_time - last_press_time > 0.05:
        press_count += 1
        last_press_time = current_time
        print(f"  🔘 按钮按下! 第 {press_count} 次 (时间: {current_time:.2f})")

def read_button_interrupt():
    """中断方式读取按钮（推荐，不占用 CPU）"""
    global press_count
    press_count = 0

    print("中断模式 - 等待按钮按下 (Ctrl+C 退出)")
    print("此模式不占用 CPU，适合长时间等待\n")

    # 注册下降沿中断（按下时触发）
    GPIO.add_event_detect(
        BUTTON_PIN,
        GPIO.FALLING,
        callback=button_callback,
        bouncetime=50  # 硬件防抖时间 (ms)
    )

    try:
        while True:
            time.sleep(1)
            print(f"  [等待中... 已按下 {press_count} 次]", end='\r')
    except KeyboardInterrupt:
        print(f"\n\n共按下 {press_count} 次")
    finally:
        GPIO.remove_event_detect(BUTTON_PIN)

def wait_for_press(timeout=10):
    """等待按钮按下（带超时）"""
    print(f"等待按钮按下... ({timeout}秒超时)")

    start = time.time()
    while time.time() - start < timeout:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            print("✅ 按钮已按下!")
            # 等待释放
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                time.sleep(0.01)
            return True
        time.sleep(0.05)

    print("⏱️  超时")
    return False

def count_presses(duration=10):
    """在指定时间内计数按下次数"""
    print(f"在 {duration} 秒内尽量多按按钮!")
    count = 0
    last_state = GPIO.HIGH
    end_time = time.time() + duration

    while time.time() < end_time:
        remaining = end_time - time.time()
        state = GPIO.input(BUTTON_PIN)

        if state == GPIO.LOW and last_state == GPIO.HIGH:
            count += 1
            print(f"  按下! 计数: {count} (剩余: {remaining:.1f}s)")
            time.sleep(0.05)

        last_state = state
        time.sleep(0.01)

    print(f"\n🏆 最终结果: {duration}秒内按下 {count} 次")
    return count

def main():
    print("=" * 40)
    print("🔘 按钮输入检测示例")
    print("=" * 40)
    print(f"按钮引脚: GPIO{BUTTON_PIN}")
    print()

    setup()

    print("选择模式:")
    print("1. 轮询模式")
    print("2. 中断模式（推荐）")
    print("3. 等待单次按下")
    print("4. 计数模式（10秒）")

    choice = input("\n请选择 (1-4): ").strip()

    try:
        if choice == '1':
            read_button_polling()
        elif choice == '2':
            read_button_interrupt()
        elif choice == '3':
            wait_for_press()
        elif choice == '4':
            count_presses()
        else:
            read_button_interrupt()
    finally:
        GPIO.cleanup()
        print("GPIO 资源已释放")

if __name__ == "__main__":
    main()