#!/usr/bin/env python3
"""
MPU6050 六轴陀螺仪加速度计
通过 I2C 读取加速度和角速度数据

硬件连接 (I2C):
  VCC ── 3.3V
  GND ── GND
  SCL ── GPIO3 (SCL)
  SDA ── GPIO2 (SDA)
  AD0 ── GND (I2C 地址 0x68)

安装依赖:
  pip3 install mpu6050-raspberrypi

学习要点:
  - 六轴传感器数据读取
  - 姿态角计算
  - 互补滤波器
"""

import time
import math
import sys

try:
    from mpu6050 import mpu6050
    MPU_AVAILABLE = True
except ImportError:
    MPU_AVAILABLE = False
    print("⚠️  未找到 mpu6050 库，使用模拟数据")
    print("   安装: pip3 install mpu6050-raspberrypi")

MPU_ADDRESS = 0x68

class MPU6050Sensor:
    def __init__(self, address=MPU_ADDRESS):
        self.sensor = None
        if MPU_AVAILABLE:
            try:
                self.sensor = mpu6050(address)
                print(f"✅ MPU6050 初始化成功 (地址: 0x{address:02X})")
            except Exception as e:
                print(f"❌ MPU6050 初始化失败: {e}")

    def read_raw(self):
        """读取原始数据"""
        if self.sensor:
            accel = self.sensor.get_accel_data()
            gyro = self.sensor.get_gyro_data()
            temp = self.sensor.get_temp()
            return accel, gyro, temp
        else:
            import random
            accel = {'x': random.uniform(-1, 1), 'y': random.uniform(-1, 1), 'z': random.uniform(9, 10)}
            gyro = {'x': random.uniform(-5, 5), 'y': random.uniform(-5, 5), 'z': random.uniform(-5, 5)}
            temp = random.uniform(25, 35)
            return accel, gyro, temp

    def get_angles(self, accel):
        """从加速度计算倾斜角"""
        ax, ay, az = accel['x'], accel['y'], accel['z']
        roll = math.atan2(ay, az) * 180 / math.pi
        pitch = math.atan2(-ax, math.sqrt(ay**2 + az**2)) * 180 / math.pi
        return round(roll, 2), round(pitch, 2)

    def detect_shake(self, threshold=2.0):
        """检测震动"""
        accel, _, _ = self.read_raw()
        magnitude = math.sqrt(accel['x']**2 + accel['y']**2 + accel['z']**2)
        return magnitude > (9.8 + threshold) or magnitude < (9.8 - threshold)

def display_data():
    """显示传感器数据"""
    sensor = MPU6050Sensor()
    print("\n持续读取 MPU6050 数据 (Ctrl+C 退出)")
    print("-" * 60)

    try:
        while True:
            accel, gyro, temp = sensor.read_raw()
            roll, pitch = sensor.get_angles(accel)

            print(f"\r加速度: X={accel['x']:6.2f} Y={accel['y']:6.2f} Z={accel['z']:6.2f} m/s²  "
                  f"Roll={roll:6.1f}° Pitch={pitch:6.1f}°", end='')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n已停止")

def shake_detector():
    """震动检测器"""
    sensor = MPU6050Sensor()
    print("\n震动检测模式 (Ctrl+C 退出)")
    shake_count = 0

    try:
        while True:
            if sensor.detect_shake(threshold=3.0):
                shake_count += 1
                print(f"  📳 检测到震动! 第 {shake_count} 次")
                time.sleep(0.5)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print(f"\n共检测到 {shake_count} 次震动")

def level_indicator():
    """水平仪"""
    sensor = MPU6050Sensor()
    print("\n水平仪模式 (Ctrl+C 退出)")
    print("将设备放平，观察角度变化\n")

    try:
        while True:
            accel, _, _ = sensor.read_raw()
            roll, pitch = sensor.get_angles(accel)

            # 可视化
            roll_bar = int(roll / 2) + 20
            pitch_bar = int(pitch / 2) + 20
            roll_bar = max(0, min(40, roll_bar))
            pitch_bar = max(0, min(40, pitch_bar))

            print(f"  Roll:  {roll:6.1f}° {'|' * roll_bar + ' ' * (40 - roll_bar)}")
            print(f"  Pitch: {pitch:6.1f}° {'|' * pitch_bar + ' ' * (40 - pitch_bar)}")

            if abs(roll) < 2 and abs(pitch) < 2:
                print("  ✅ 水平!")
            else:
                print("  ⚠️  不水平")

            print("\033[3A", end='')  # 上移3行
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n已停止")

def main():
    print("=" * 40)
    print("🎯 MPU6050 陀螺仪加速度计")
    print("=" * 40)

    print("\n选择模式:")
    print("1. 显示原始数据")
    print("2. 震动检测")
    print("3. 水平仪")

    choice = input("\n请选择 (1-3): ").strip()

    if choice == '1':
        display_data()
    elif choice == '2':
        shake_detector()
    elif choice == '3':
        level_indicator()
    else:
        display_data()

if __name__ == "__main__":
    main()