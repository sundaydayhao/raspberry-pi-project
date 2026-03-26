#!/usr/bin/env python3
"""
LED 闪烁示例
演示 GPIO 数字输出控制 LED

硬件连接:
  GPIO18 ──[330Ω]──[LED+]──[LED-]── GND

学习要点:
  - GPIO 初始化和清理
  - 数字输出控制
  - 循环和延时
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("错误: 未找到 RPi.GPIO 库")
    print("安装命令: pip3 install RPi.GPIO")
    sys.exit(1)

# ============ 配置区域 ============
LED_PIN = 18        # LED 连接的 GPIO 引脚 (BCM 编号)
BLINK_INTERVAL = 0.5  # 闪烁间隔（秒）
BLINK_COUNT = 10    # 闪烁次数（0 = 无限循环）
# ==================================

def setup():
    """初始化 GPIO"""
    GPIO.setmode(GPIO.BCM)           # 使用 BCM 编号
    GPIO.setwarnings(False)          # 关闭警告
    GPIO.setup(LED_PIN, GPIO.OUT)    # 设置为输出模式
    GPIO.output(LED_PIN, GPIO.LOW)   # 初始状态为低电平（LED 灭）
    print(f"✅ GPIO{LED_PIN} 初始化完成")

def led_on():
    """点亮 LED"""
    GPIO.output(LED_PIN, GPIO.HIGH)

def led_off():
    """熄灭 LED"""
    GPIO.output(LED_PIN, GPIO.LOW)

def blink(count=0, interval=0.5):
    """
    LED 闪烁
    
    参数:
        count: 闪烁次数，0 表示无限循环
        interval: 闪烁间隔（秒）
    """
    print(f"开始闪烁 (间隔: {interval}s, 次数: {'无限' if count == 0 else count})")
    print("按 Ctrl+C 停止\n")
    
    blink_num = 0
    try:
        while count == 0 or blink_num < count:
            led_on()
            print(f"  第{blink_num + 1}次: 💡 亮", end='\r')
            time.sleep(interval)
            
            led_off()
            print(f"  第{blink_num + 1}次: ⚫ 灭", end='\r')
            time.sleep(interval)
            
            blink_num += 1
            
    except KeyboardInterrupt:
        print(f"\n\n已停止，共闪烁 {blink_num} 次")

def morse_code(message):
    """
    用 LED 发送摩斯电码
    
    参数:
        message: 要发送的文字（英文）
    """
    MORSE_CODE = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
        'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
        'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
        'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
        'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
        'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
        '3': '...--', '4': '....-', '5': '.....', '6': '-....',
        '7': '--...', '8': '---..', '9': '----.',
        ' ': ' '
    }
    
    DOT_TIME = 0.2    # 点的时长
    DASH_TIME = 0.6   # 划的时长
    SYMBOL_GAP = 0.2  # 符号间隔
    LETTER_GAP = 0.6  # 字母间隔
    WORD_GAP = 1.4    # 单词间隔
    
    print(f"\n发送摩斯电码: {message}")
    
    for char in message.upper():
        if char == ' ':
            print("  [空格]")
            time.sleep(WORD_GAP)
        elif char in MORSE_CODE:
            code = MORSE_CODE[char]
            print(f"  {char}: {code}")
            
            for symbol in code:
                if symbol == '.':
                    led_on()
                    time.sleep(DOT_TIME)
                    led_off()
                elif symbol == '-':
                    led_on()
                    time.sleep(DASH_TIME)
                    led_off()
                time.sleep(SYMBOL_GAP)
            
            time.sleep(LETTER_GAP)
    
    print("发送完成!")

def cleanup():
    """清理 GPIO 资源"""
    led_off()
    GPIO.cleanup()
    print("GPIO 资源已释放")

def main():
    """主函数"""
    print("=" * 40)
    print("💡 LED 闪烁示例")
    print("=" * 40)
    print(f"LED 引脚: GPIO{LED_PIN}")
    print()
    
    setup()
    
    print("选择模式:")
    print("1. 普通闪烁")
    print("2. 快速闪烁")
    print("3. 慢速闪烁")
    print("4. 摩斯电码 (SOS)")
    print("5. 自定义摩斯电码")
    
    choice = input("\n请选择 (1-5): ").strip()
    
    try:
        if choice == '1':
            blink(BLINK_COUNT, BLINK_INTERVAL)
        elif choice == '2':
            blink(20, 0.1)
        elif choice == '3':
            blink(5, 1.0)
        elif choice == '4':
            morse_code("SOS")
        elif choice == '5':
            msg = input("输入要发送的英文消息: ")
            morse_code(msg)
        else:
            print("无效选项，使用默认闪烁")
            blink(BLINK_COUNT, BLINK_INTERVAL)
    finally:
        cleanup()

if __name__ == "__main__":
    main()