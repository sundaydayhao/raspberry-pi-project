#!/usr/bin/env python3
"""
DHT11 温湿度传感器
读取环境温度和湿度数据

硬件连接:
  VCC  ── 3.3V 或 5V
  DATA ── GPIO4 (通过 10kΩ 上拉到 VCC)
  GND  ── GND

安装依赖:
  pip3 install Adafruit-DHT
  或
  pip3 install adafruit-circuitpython-dht
  sudo apt install libgpiod2

学习要点:
  - 单总线通信协议
  - 传感器数据读取
  - 数据有效性验证
"""

import time
import sys

# 尝试导入 DHT 库
DHT_LIB = None
try:
    import Adafruit_DHT
    DHT_LIB = 'adafruit'
    print("✅ 使用 Adafruit_DHT 库")
except ImportError:
    pass

if DHT_LIB is None:
    try:
        import adafruit_dht
        import board
        DHT_LIB = 'circuitpython'
        print("✅ 使用 adafruit_dht (CircuitPython) 库")
    except ImportError:
        pass

if DHT_LIB is None:
    print("⚠️  未找到 DHT 库，使用模拟数据")
    print("   安装: pip3 install Adafruit-DHT")

DATA_PIN = 4  # GPIO4

class DHT11Sensor:
    """DHT11 传感器封装类"""

    def __init__(self, pin=DATA_PIN):
        self.pin = pin
        self.sensor = None
        self._init_sensor()

    def _init_sensor(self):
        if DHT_LIB == 'adafruit':
            self.sensor_type = Adafruit_DHT.DHT11
        elif DHT_LIB == 'circuitpython':
            pin_map = {4: board.D4, 17: board.D17, 18: board.D18}
            board_pin = pin_map.get(self.pin, board.D4)
            self.sensor = adafruit_dht.DHT11(board_pin)

    def read(self):
        """
        读取温湿度数据
        返回: (temperature, humidity) 或 (None, None) 如果读取失败
        """
        if DHT_LIB == 'adafruit':
            humidity, temperature = Adafruit_DHT.read_retry(
                self.sensor_type, self.pin, retries=3
            )
            return temperature, humidity

        elif DHT_LIB == 'circuitpython':
            try:
                temperature = self.sensor.temperature
                humidity = self.sensor.humidity
                return temperature, humidity
            except RuntimeError as e:
                print(f"读取错误: {e}")
                return None, None

        else:
            # 模拟数据
            import random
            temp = round(random.uniform(20, 30), 1)
            humi = round(random.uniform(40, 80), 1)
            return temp, humi

    def read_with_retry(self, max_retries=5):
        """带重试的读取"""
        for attempt in range(max_retries):
            temp, humi = self.read()
            if temp is not None and humi is not None:
                # 验证数据范围
                if -40 <= temp <= 80 and 0 <= humi <= 100:
                    return temp, humi
            print(f"  读取失败，重试 {attempt + 1}/{max_retries}...")
            time.sleep(2)
        return None, None

    def get_heat_index(self, temp, humidity):
        """计算体感温度（热指数）"""
        # 简化版热指数公式
        if temp < 27:
            return temp
        hi = (-8.78469475556 +
              1.61139411 * temp +
              2.33854883889 * humidity +
              -0.14611605 * temp * humidity +
              -0.012308094 * temp**2 +
              -0.0164248277778 * humidity**2 +
              0.002211732 * temp**2 * humidity +
              0.00072546 * temp * humidity**2 +
              -0.000003582 * temp**2 * humidity**2)
        return round(hi, 1)

    def get_comfort_level(self, temp, humidity):
        """评估舒适度"""
        if 18 <= temp <= 26 and 40 <= humidity <= 60:
            return "😊 舒适"
        elif temp > 30 and humidity > 70:
            return "🥵 闷热"
        elif temp < 15:
            return "🥶 寒冷"
        elif humidity < 30:
            return "🏜️ 干燥"
        elif humidity > 80:
            return "💧 潮湿"
        else:
            return "😐 一般"

def single_read():
    """单次读取"""
    sensor = DHT11Sensor(DATA_PIN)
    print(f"\n读取 DHT11 数据 (GPIO{DATA_PIN})...")

    temp, humi = sensor.read_with_retry()

    if temp is not None and humi is not None:
        heat_index = sensor.get_heat_index(temp, humi)
        comfort = sensor.get_comfort_level(temp, humi)

        print(f"\n📊 传感器数据:")
        print(f"  🌡️  温度: {temp:.1f}°C")
        print(f"  💧 湿度: {humi:.1f}%")
        print(f"  🌡️  体感温度: {heat_index:.1f}°C")
        print(f"  {comfort}")
    else:
        print("❌ 读取失败，请检查接线")

def continuous_monitor(interval=3):
    """持续监控"""
    sensor = DHT11Sensor(DATA_PIN)
    print(f"\n持续监控模式 (每{interval}秒读取一次，Ctrl+C 退出)")
    print("-" * 50)
    print(f"{'时间':20s} {'温度':10s} {'湿度':10s} {'舒适度'}")
    print("-" * 50)

    readings = []

    try:
        while True:
            temp, humi = sensor.read()
            timestamp = time.strftime("%H:%M:%S")

            if temp is not None and humi is not None:
                comfort = sensor.get_comfort_level(temp, humi)
                print(f"{timestamp:20s} {temp:.1f}°C     {humi:.1f}%      {comfort}")
                readings.append((temp, humi))
            else:
                print(f"{timestamp:20s} 读取失败")

            time.sleep(interval)

    except KeyboardInterrupt:
        if readings:
            temps = [r[0] for r in readings]
            humis = [r[1] for r in readings]
            print(f"\n📈 统计信息 (共 {len(readings)} 次读取):")
            print(f"  温度: 最低 {min(temps):.1f}°C, 最高 {max(temps):.1f}°C, 平均 {sum(temps)/len(temps):.1f}°C")
            print(f"  湿度: 最低 {min(humis):.1f}%, 最高 {max(humis):.1f}%, 平均 {sum(humis)/len(humis):.1f}%")

def log_to_file(filename='temperature_log.csv', duration=60, interval=5):
    """记录数据到文件"""
    sensor = DHT11Sensor(DATA_PIN)
    print(f"\n数据记录模式 (记录 {duration} 秒，间隔 {interval} 秒)")
    print(f"保存到: {filename}")

    with open(filename, 'w') as f:
        f.write("时间戳,温度(°C),湿度(%)\n")

        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            temp, humi = sensor.read()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            if temp is not None and humi is not None:
                f.write(f"{timestamp},{temp:.1f},{humi:.1f}\n")
                f.flush()
                count += 1
                print(f"  [{count}] {timestamp}: {temp:.1f}°C, {humi:.1f}%")

            time.sleep(interval)

    print(f"\n✅ 记录完成，共 {count} 条数据")

def main():
    print("=" * 40)
    print("🌡️  DHT11 温湿度传感器")
    print("=" * 40)
    print(f"数据引脚: GPIO{DATA_PIN}")
    print()

    print("选择模式:")
    print("1. 单次读取")
    print("2. 持续监控")
    print("3. 记录到文件")

    choice = input("\n请选择 (1-3): ").strip()

    if choice == '1':
        single_read()
    elif choice == '2':
        continuous_monitor()
    elif choice == '3':
        log_to_file()
    else:
        single_read()

if __name__ == "__main__":
    main()