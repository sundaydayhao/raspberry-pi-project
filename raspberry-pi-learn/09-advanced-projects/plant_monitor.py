#!/usr/bin/env python3
"""
植物监控系统
监测植物生长环境，自动浇水

功能:
  - 土壤湿度检测 (模拟传感器)
  - 温湿度监测 (DHT22)
  - 光照强度检测
  - 自动浇水控制 (继电器)
  - 数据记录与分析

硬件需求:
  - 土壤湿度传感器 + MCP3008 ADC (SPI)
  - DHT22 温湿度传感器 (GPIO4)
  - 光敏电阻 + MCP3008 ADC
  - 继电器模块 (GPIO17) 控制水泵
  - LED 状态指示 (GPIO18)

学习要点:
  - 模拟传感器读取
  - 自动控制逻辑
  - 数据可视化
"""

import time
import os
import csv
import json
import random
from datetime import datetime

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
except ImportError:
    GPIO_AVAILABLE = False

# 引脚配置
RELAY_PIN = 17      # 继电器（控制水泵）
LED_PIN = 18        # 状态 LED
DHT_PIN = 4         # DHT22 传感器

# 阈值配置
THRESHOLDS = {
    'soil_moisture_min': 30,   # 土壤湿度低于此值时浇水 (%)
    'soil_moisture_max': 70,   # 土壤湿度高于此值时停止浇水 (%)
    'temp_max': 35,            # 最高温度警告 (°C)
    'light_min': 200,          # 最低光照值
}

# 数据记录
LOG_FILE = 'plant_monitor_log.csv'

def setup_gpio():
    if not GPIO_AVAILABLE:
        return
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(RELAY_PIN, GPIO.LOW)
    GPIO.output(LED_PIN, GPIO.LOW)

def read_soil_moisture():
    """读取土壤湿度 (0-100%)"""
    # 实际使用时通过 MCP3008 读取模拟值
    # adc_value = read_mcp3008(channel=0)
    # return 100 - (adc_value / 1023 * 100)  # 湿度越高，电阻越低，ADC值越低
    return round(random.uniform(20, 80), 1)

def read_temperature_humidity():
    """读取温湿度"""
    return {
        'temperature': round(random.uniform(18, 32), 1),
        'humidity': round(random.uniform(40, 80), 1)
    }

def read_light_level():
    """读取光照强度"""
    return random.randint(100, 900)

def water_plant(duration=3):
    """浇水"""
    print(f"  💧 开始浇水 ({duration}秒)...")
    if GPIO_AVAILABLE:
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        GPIO.output(LED_PIN, GPIO.HIGH)
    time.sleep(duration)
    if GPIO_AVAILABLE:
        GPIO.output(RELAY_PIN, GPIO.LOW)
        GPIO.output(LED_PIN, GPIO.LOW)
    print("  💧 浇水完成")

def get_plant_status(soil_moisture, temp, humidity, light):
    """评估植物状态"""
    issues = []
    status = "✅ 良好"

    if soil_moisture < THRESHOLDS['soil_moisture_min']:
        issues.append("土壤干燥，需要浇水")
        status = "⚠️  需要关注"
    elif soil_moisture > THRESHOLDS['soil_moisture_max']:
        issues.append("土壤过湿")
        status = "⚠️  需要关注"

    if temp > THRESHOLDS['temp_max']:
        issues.append(f"温度过高 ({temp}°C)")
        status = "🚨 警告"

    if light < THRESHOLDS['light_min']:
        issues.append("光照不足")
        if status == "✅ 良好":
            status = "⚠️  需要关注"

    return status, issues

def init_log():
    """初始化日志文件"""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['时间', '土壤湿度(%)', '温度(°C)', '湿度(%)', '光照', '浇水', '状态'])

def log_data(data, watered=False):
    """记录数据"""
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            data['timestamp'],
            data['soil_moisture'],
            data['temperature'],
            data['humidity'],
            data['light'],
            '是' if watered else '否',
            data['status']
        ])

def display_status(data):
    """显示当前状态"""
    print(f"\n{'='*50}")
    print(f"🌱 植物监控  [{data['timestamp']}]")
    print(f"{'='*50}")
    print(f"  💧 土壤湿度: {data['soil_moisture']:5.1f}%  ", end='')
    bar = '█' * int(data['soil_moisture'] / 5) + '░' * (20 - int(data['soil_moisture'] / 5))
    print(f"[{bar}]")
    print(f"  🌡️  温度:     {data['temperature']:5.1f}°C")
    print(f"  💦 空气湿度: {data['humidity']:5.1f}%")
    print(f"  ☀️  光照:     {data['light']:5d}")
    print(f"  状态: {data['status']}")
    if data['issues']:
        for issue in data['issues']:
            print(f"    ⚠️  {issue}")

def monitor(interval=30, auto_water=True):
    """持续监控"""
    setup_gpio()
    init_log()

    print(f"\n🌱 植物监控系统启动")
    print(f"  监控间隔: {interval}秒")
    print(f"  自动浇水: {'开启' if auto_water else '关闭'}")
    print(f"  浇水阈值: 土壤湿度 < {THRESHOLDS['soil_moisture_min']}%")
    print("  按 Ctrl+C 停止\n")

    watering_count = 0

    try:
        while True:
            # 读取传感器
            soil = read_soil_moisture()
            th = read_temperature_humidity()
            light = read_light_level()

            status, issues = get_plant_status(
                soil, th['temperature'], th['humidity'], light
            )

            data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'soil_moisture': soil,
                'temperature': th['temperature'],
                'humidity': th['humidity'],
                'light': light,
                'status': status,
                'issues': issues,
            }

            display_status(data)

            # 自动浇水逻辑
            watered = False
            if auto_water and soil < THRESHOLDS['soil_moisture_min']:
                water_plant(duration=3)
                watered = True
                watering_count += 1

            log_data(data, watered)
            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n监控已停止")
        print(f"共浇水 {watering_count} 次")
        print(f"数据已记录到: {LOG_FILE}")
    finally:
        if GPIO_AVAILABLE:
            GPIO.output(RELAY_PIN, GPIO.LOW)
            GPIO.output(LED_PIN, GPIO.LOW)
            GPIO.cleanup()

def show_statistics():
    """显示历史统计"""
    if not os.path.exists(LOG_FILE):
        print("暂无历史数据")
        return

    records = []
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)

    if not records:
        print("暂无数据")
        return

    print(f"\n📊 历史统计 (共 {len(records)} 条记录)")
    print(f"  时间范围: {records[0]['时间']} ~ {records[-1]['时间']}")

    soils = [float(r['土壤湿度(%)']) for r in records]
    temps = [float(r['温度(°C)']) for r in records]
    water_count = sum(1 for r in records if r['浇水'] == '是')

    print(f"  土壤湿度: {min(soils):.1f}% ~ {max(soils):.1f}% (平均 {sum(soils)/len(soils):.1f}%)")
    print(f"  温度范围: {min(temps):.1f}°C ~ {max(temps):.1f}°C")
    print(f"  浇水次数: {water_count} 次")

def main():
    print("=" * 50)
    print("🌱 植物监控系统")
    print("=" * 50)

    print("\n选择模式:")
    print("1. 单次检测")
    print("2. 持续监控（自动浇水）")
    print("3. 持续监控（仅监控）")
    print("4. 查看历史统计")
    print("5. 手动浇水测试")

    choice = input("\n请选择 (1-5): ").strip()

    if choice == '1':
        setup_gpio()
        soil = read_soil_moisture()
        th = read_temperature_humidity()
        light = read_light_level()
        status, issues = get_plant_status(soil, th['temperature'], th['humidity'], light)
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'soil_moisture': soil,
            'temperature': th['temperature'],
            'humidity': th['humidity'],
            'light': light,
            'status': status,
            'issues': issues,
        }
        display_status(data)
    elif choice == '2':
        interval = input("监控间隔秒数 (默认30): ").strip()
        interval = int(interval) if interval.isdigit() else 30
        monitor(interval=interval, auto_water=True)
    elif choice == '3':
        interval = input("监控间隔秒数 (默认30): ").strip()
        interval = int(interval) if interval.isdigit() else 30
        monitor(interval=interval, auto_water=False)
    elif choice == '4':
        show_statistics()
    elif choice == '5':
        setup_gpio()
        water_plant(duration=3)
    else:
        monitor(interval=10, auto_water=True)

if __name__ == "__main__":
    main()