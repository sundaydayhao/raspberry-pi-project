#!/usr/bin/env python3
"""
BMP280 气压温度传感器
通过 I2C 读取气压、温度和海拔高度

硬件连接 (I2C):
  VCC ── 3.3V
  GND ── GND
  SCL ── GPIO3 (SCL)
  SDA ── GPIO2 (SDA)

启用 I2C:
  sudo raspi-config -> Interface Options -> I2C -> Enable
  sudo apt install i2c-tools python3-smbus
  pip3 install adafruit-circuitpython-bmp280

检查设备:
  sudo i2cdetect -y 1  (应显示 0x76 或 0x77)

学习要点:
  - I2C 通信协议
  - 气压与海拔换算
  - 天气预测基础
"""

import time
import sys

try:
    import board
    import busio
    import adafruit_bmp280
    BMP_AVAILABLE = True
except ImportError:
    BMP_AVAILABLE = False
    print("⚠️  未找到 BMP280 库，使用模拟数据")
    print("   安装: pip3 install adafruit-circuitpython-bmp280")

# 标准海平面气压 (hPa)
SEA_LEVEL_PRESSURE = 1013.25

class BMP280Sensor:
    def __init__(self):
        self.sensor = None
        if BMP_AVAILABLE:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
                self.sensor.sea_level_pressure = SEA_LEVEL_PRESSURE
                print("✅ BMP280 初始化成功")
            except Exception as e:
                print(f"❌ BMP280 初始化失败: {e}")

    def read(self):
        """读取传感器数据"""
        if self.sensor:
            return {
                'temperature': round(self.sensor.temperature, 2),
                'pressure': round(self.sensor.pressure, 2),
                'altitude': round(self.sensor.altitude, 2)
            }
        else:
            import random
            return {
                'temperature': round(random.uniform(20, 30), 2),
                'pressure': round(random.uniform(1000, 1020), 2),
                'altitude': round(random.uniform(0, 100), 2)
            }

    def get_weather_trend(self, pressure):
        """根据气压判断天气趋势"""
        if pressure > 1020:
            return "☀️ 晴天"
        elif pressure > 1010:
            return "⛅ 多云"
        elif pressure > 1000:
            return "🌧️ 可能有雨"
        else:
            return "⛈️ 恶劣天气"

def monitor(interval=2):
    """持续监控"""
    sensor = BMP280Sensor()
    print("\n持续监控 BMP280 (Ctrl+C 退出)")
    print("-" * 55)
    print(f"{'时间':10s} {'温度':10s} {'气压':12s} {'海拔':10s} {'天气'}")
    print("-" * 55)

    try:
        while True:
            data = sensor.read()
            weather = sensor.get_weather_trend(data['pressure'])
            t = time.strftime("%H:%M:%S")
            print(f"{t:10s} {data['temperature']:6.2f}°C  "
                  f"{data['pressure']:8.2f}hPa  "
                  f"{data['altitude']:6.2f}m  {weather}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n监控已停止")

def main():
    print("=" * 40)
    print("🌡️  BMP280 气压温度传感器")
    print("=" * 40)

    sensor = BMP280Sensor()
    data = sensor.read()
    weather = sensor.get_weather_trend(data['pressure'])

    print(f"\n📊 当前读数:")
    print(f"  🌡️  温度: {data['temperature']}°C")
    print(f"  🌬️  气压: {data['pressure']} hPa")
    print(f"  ⛰️  海拔: {data['altitude']} m")
    print(f"  {weather}")

    cont = input("\n持续监控? (y/n): ").strip().lower()
    if cont == 'y':
        monitor()

if __name__ == "__main__":
    main()