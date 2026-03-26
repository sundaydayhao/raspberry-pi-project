#!/usr/bin/env python3
"""
气象站综合项目
整合多种传感器，构建完整的气象监测系统

功能:
  - 温湿度监测 (DHT22)
  - 气压/海拔 (BMP280)
  - 数据记录到 CSV
  - OLED 显示
  - Web 数据展示

硬件需求:
  - DHT22 温湿度传感器 (GPIO4)
  - BMP280 气压传感器 (I2C)
  - OLED SSD1306 (I2C)
  - LED 状态指示灯 (GPIO18)

学习要点:
  - 多传感器数据融合
  - 数据持久化
  - 系统集成
"""

import time
import json
import os
import csv
import threading
from datetime import datetime

# 模拟传感器数据（实际使用时替换为真实传感器）
def read_dht22():
    """读取 DHT22 温湿度"""
    import random
    return {
        'temperature': round(20 + random.uniform(-5, 10), 1),
        'humidity': round(55 + random.uniform(-15, 20), 1)
    }

def read_bmp280():
    """读取 BMP280 气压"""
    import random
    return {
        'pressure': round(1013 + random.uniform(-10, 10), 1),
        'altitude': round(50 + random.uniform(-5, 5), 1),
        'temp_bmp': round(22 + random.uniform(-2, 5), 1)
    }

class WeatherStation:
    """气象站主类"""

    def __init__(self, log_file='weather_log.csv', log_interval=60):
        self.log_file = log_file
        self.log_interval = log_interval
        self.running = False
        self.current_data = {}
        self.history = []

        # 初始化日志文件
        self._init_log_file()
        print("✅ 气象站初始化完成")

    def _init_log_file(self):
        """初始化 CSV 日志文件"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '时间戳', '温度(°C)', '湿度(%)',
                    '气压(hPa)', '海拔(m)', '体感温度(°C)', '天气状态'
                ])

    def collect_data(self):
        """采集所有传感器数据"""
        dht_data = read_dht22()
        bmp_data = read_bmp280()

        # 计算体感温度
        temp = dht_data['temperature']
        humi = dht_data['humidity']
        heat_index = self._calc_heat_index(temp, humi)

        # 判断天气状态
        weather = self._get_weather_status(bmp_data['pressure'], temp, humi)

        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': temp,
            'humidity': humi,
            'pressure': bmp_data['pressure'],
            'altitude': bmp_data['altitude'],
            'heat_index': heat_index,
            'weather': weather,
        }

        self.current_data = data
        self.history.append(data)

        # 只保留最近 1440 条（24小时，每分钟一条）
        if len(self.history) > 1440:
            self.history = self.history[-1440:]

        return data

    def _calc_heat_index(self, temp, humidity):
        """计算体感温度"""
        if temp < 27:
            return temp
        hi = (-8.78 + 1.61 * temp + 2.34 * humidity
              - 0.146 * temp * humidity
              - 0.0123 * temp**2 - 0.0164 * humidity**2)
        return round(hi, 1)

    def _get_weather_status(self, pressure, temp, humidity):
        """判断天气状态"""
        if pressure > 1020:
            return "晴天 ☀️"
        elif pressure > 1010:
            if humidity > 70:
                return "多云 ⛅"
            return "晴转多云 🌤️"
        elif pressure > 1000:
            return "阴天/小雨 🌧️"
        else:
            return "恶劣天气 ⛈️"

    def log_data(self, data):
        """记录数据到 CSV"""
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                data['timestamp'],
                data['temperature'],
                data['humidity'],
                data['pressure'],
                data['altitude'],
                data['heat_index'],
                data['weather'],
            ])

    def display_current(self, data):
        """在终端显示当前数据"""
        print(f"\n{'='*50}")
        print(f"🌤️  气象站数据  [{data['timestamp']}]")
        print(f"{'='*50}")
        print(f"  🌡️  温度:     {data['temperature']:6.1f} °C")
        print(f"  💧 湿度:     {data['humidity']:6.1f} %")
        print(f"  🌬️  气压:     {data['pressure']:8.1f} hPa")
        print(f"  ⛰️  海拔:     {data['altitude']:6.1f} m")
        print(f"  🌡️  体感温度: {data['heat_index']:6.1f} °C")
        print(f"  🌤️  天气:     {data['weather']}")

    def get_statistics(self):
        """计算统计数据"""
        if not self.history:
            return None

        temps = [d['temperature'] for d in self.history]
        humis = [d['humidity'] for d in self.history]
        pressures = [d['pressure'] for d in self.history]

        return {
            'count': len(self.history),
            'temp_min': min(temps),
            'temp_max': max(temps),
            'temp_avg': round(sum(temps) / len(temps), 1),
            'humi_min': min(humis),
            'humi_max': max(humis),
            'humi_avg': round(sum(humis) / len(humis), 1),
            'pressure_avg': round(sum(pressures) / len(pressures), 1),
        }

    def run_continuous(self, interval=None):
        """持续运行气象站"""
        if interval is None:
            interval = self.log_interval

        self.running = True
        print(f"\n气象站运行中 (每{interval}秒采集一次，Ctrl+C 停止)")
        print(f"数据记录到: {self.log_file}\n")

        try:
            while self.running:
                data = self.collect_data()
                self.display_current(data)
                self.log_data(data)
                time.sleep(interval)

        except KeyboardInterrupt:
            self.running = False
            print("\n\n气象站已停止")

            stats = self.get_statistics()
            if stats:
                print(f"\n📊 统计摘要 (共 {stats['count']} 次采集):")
                print(f"  温度: {stats['temp_min']}°C ~ {stats['temp_max']}°C (平均 {stats['temp_avg']}°C)")
                print(f"  湿度: {stats['humi_min']}% ~ {stats['humi_max']}% (平均 {stats['humi_avg']}%)")
                print(f"  气压: 平均 {stats['pressure_avg']} hPa")

def main():
    print("=" * 50)
    print("🌤️  Raspberry Pi 气象站")
    print("=" * 50)

    print("\n选择模式:")
    print("1. 单次采集")
    print("2. 持续监控 (每分钟)")
    print("3. 快速测试 (每5秒)")

    choice = input("\n请选择 (1-3): ").strip()

    station = WeatherStation()

    if choice == '1':
        data = station.collect_data()
        station.display_current(data)
        station.log_data(data)
        print(f"\n数据已记录到: {station.log_file}")
    elif choice == '2':
        station.run_continuous(interval=60)
    elif choice == '3':
        station.run_continuous(interval=5)
    else:
        data = station.collect_data()
        station.display_current(data)

if __name__ == "__main__":
    main()