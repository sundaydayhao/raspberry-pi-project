#!/usr/bin/env python3
"""
MQ-2 烟雾/气体传感器
检测可燃气体、烟雾浓度

硬件连接 (需要 MCP3008 ADC):
  MQ-2 AO ── MCP3008 CH0
  MQ-2 DO ── GPIO17 (数字输出，可选)
  MQ-2 VCC ── 5V
  MQ-2 GND ── GND

  MCP3008 接线:
  VDD/VREF ── 3.3V
  CLK  ── GPIO11 (SCLK)
  DOUT ── GPIO9  (MISO)
  DIN  ── GPIO10 (MOSI)
  CS   ── GPIO8  (CE0)
  DGND/AGND ── GND

注意: 传感器需要预热 20-30 秒

学习要点:
  - 模拟传感器读取
  - ADC 转换
  - 阈值报警
"""

import time
import sys

try:
    import spidev
    SPI_AVAILABLE = True
except ImportError:
    SPI_AVAILABLE = False

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

DO_PIN = 17  # 数字输出引脚
ALARM_THRESHOLD = 400  # 报警阈值 (0-1023)

def read_mcp3008(channel=0):
    """通过 SPI 读取 MCP3008 ADC 值"""
    if not SPI_AVAILABLE:
        import random
        return random.randint(100, 800)

    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1350000

    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    spi.close()
    return data

def get_gas_level(adc_value):
    """将 ADC 值转换为气体浓度百分比"""
    return round(adc_value / 1023 * 100, 1)

def get_gas_status(adc_value):
    """评估气体浓度状态"""
    if adc_value < 200:
        return "✅ 安全", "green"
    elif adc_value < 400:
        return "⚠️  轻微", "yellow"
    elif adc_value < 600:
        return "🔶 警告", "orange"
    else:
        return "🚨 危险!", "red"

def single_read():
    """单次读取"""
    print("\n读取 MQ-2 传感器...")
    print("注意: 传感器需要预热 20-30 秒")

    value = read_mcp3008(0)
    level = get_gas_level(value)
    status, _ = get_gas_status(value)

    print(f"\n📊 传感器数据:")
    print(f"  ADC 值: {value} / 1023")
    print(f"  浓度:   {level}%")
    print(f"  状态:   {status}")

    bar_len = int(level / 5)
    bar = "█" * bar_len + "░" * (20 - bar_len)
    print(f"  [{bar}] {level}%")

def continuous_monitor(interval=1):
    """持续监控"""
    print("\n持续监控 MQ-2 (Ctrl+C 退出)")
    print("等待传感器预热 (5秒)...")
    time.sleep(5)
    print("\n开始监控...\n")

    if GPIO_AVAILABLE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DO_PIN, GPIO.IN)

    try:
        while True:
            value = read_mcp3008(0)
            level = get_gas_level(value)
            status, _ = get_gas_status(value)

            bar_len = int(level / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)

            # 检查数字输出
            do_state = ""
            if GPIO_AVAILABLE:
                do_val = GPIO.input(DO_PIN)
                do_state = " [DO: 报警!]" if do_val == GPIO.HIGH else " [DO: 正常]"

            print(f"  {status} ADC:{value:4d} [{bar}] {level:5.1f}%{do_state}", end='\r')

            if value > ALARM_THRESHOLD:
                print(f"\n  🚨 气体浓度超标! ADC={value}")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n监控已停止")
    finally:
        if GPIO_AVAILABLE:
            GPIO.cleanup()

def alarm_mode():
    """报警模式"""
    threshold = int(input(f"设置报警阈值 (0-1023, 默认{ALARM_THRESHOLD}): ").strip() or ALARM_THRESHOLD)
    print(f"\n报警模式 (阈值: {threshold})")
    print("等待传感器预热 (5秒)...")
    time.sleep(5)

    alarm_count = 0
    try:
        while True:
            value = read_mcp3008(0)
            if value > threshold:
                alarm_count += 1
                print(f"\n🚨 [{time.strftime('%H:%M:%S')}] 报警! 气体浓度: {value} (第{alarm_count}次)")
            else:
                print(f"  ✅ 安全 ADC={value}", end='\r')
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\n\n共触发 {alarm_count} 次报警")

def main():
    print("=" * 40)
    print("💨 MQ-2 气体传感器")
    print("=" * 40)

    print("\n选择模式:")
    print("1. 单次读取")
    print("2. 持续监控")
    print("3. 报警模式")

    choice = input("\n请选择 (1-3): ").strip()

    if choice == '1':
        single_read()
    elif choice == '2':
        continuous_monitor()
    elif choice == '3':
        alarm_mode()
    else:
        single_read()

if __name__ == "__main__":
    main()