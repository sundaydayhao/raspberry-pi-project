#!/usr/bin/env python3
"""
I2C 设备扫描器
扫描并识别连接的 I2C 设备

使用方法:
  sudo python3 i2c_scanner.py
  或
  sudo i2cdetect -y 1

学习要点:
  - I2C 协议基础
  - 设备地址扫描
  - smbus2 库使用
"""

import sys

try:
    import smbus2
    SMBUS_AVAILABLE = True
except ImportError:
    try:
        import smbus as smbus2
        SMBUS_AVAILABLE = True
    except ImportError:
        SMBUS_AVAILABLE = False
        print("⚠️  未找到 smbus2 库")
        print("   安装: pip3 install smbus2")
        print("   或: sudo apt install python3-smbus")

# 常见 I2C 设备地址数据库
KNOWN_DEVICES = {
    0x20: "PCF8574 I/O 扩展器",
    0x27: "PCF8574 LCD 背包",
    0x3C: "SSD1306 OLED 显示屏",
    0x3D: "SSD1306 OLED 显示屏",
    0x3F: "PCF8574A LCD 背包",
    0x40: "INA219 电流传感器 / PCA9685 PWM",
    0x48: "ADS1115 ADC / PCF8591 ADC",
    0x57: "AT24C32 EEPROM (DS3231 RTC)",
    0x60: "MCP4725 DAC",
    0x68: "MPU6050 陀螺仪 / DS3231 RTC",
    0x69: "MPU6050 陀螺仪 (AD0=HIGH)",
    0x76: "BMP280/BME280 气压传感器",
    0x77: "BMP280/BME280 气压传感器",
}

def scan_i2c_bus(bus_number=1):
    """扫描 I2C 总线上的设备"""
    if not SMBUS_AVAILABLE:
        print("无法扫描：smbus2 库未安装")
        return []

    devices = []
    try:
        bus = smbus2.SMBus(bus_number)

        print(f"\n扫描 I2C 总线 {bus_number}...")
        print("地址范围: 0x03 - 0x77\n")

        for address in range(3, 0x78):
            try:
                bus.read_byte(address)
                devices.append(address)
            except OSError:
                pass

        bus.close()
    except Exception as e:
        print(f"扫描失败: {e}")
        print("提示: 可能需要 sudo 权限，或 I2C 未启用")

    return devices

def display_scan_results(devices):
    """显示扫描结果"""
    print("=" * 50)
    print("I2C 设备扫描结果")
    print("=" * 50)

    if not devices:
        print("❌ 未发现任何 I2C 设备")
        print("\n可能的原因:")
        print("  1. I2C 未启用 (sudo raspi-config)")
        print("  2. 设备未正确连接")
        print("  3. 电源问题")
        return

    print(f"✅ 发现 {len(devices)} 个设备:\n")

    # 显示地址表格
    print("     ", end="")
    for col in range(16):
        print(f" {col:2X}", end="")
    print()

    for row in range(8):
        print(f"  {row*16:02X}: ", end="")
        for col in range(16):
            addr = row * 16 + col
            if addr in devices:
                print(f" {addr:02X}", end="")
            elif addr < 3 or addr > 0x77:
                print("   ", end="")
            else:
                print(" --", end="")
        print()

    print("\n📋 设备详情:")
    for addr in devices:
        name = KNOWN_DEVICES.get(addr, "未知设备")
        print(f"  0x{addr:02X} ({addr:3d}) - {name}")

def test_device_communication(address, bus_number=1):
    """测试与特定设备的通信"""
    if not SMBUS_AVAILABLE:
        return False

    try:
        bus = smbus2.SMBus(bus_number)
        bus.read_byte(address)
        bus.close()
        return True
    except Exception:
        return False

def read_device_register(address, register, bus_number=1):
    """读取设备寄存器"""
    if not SMBUS_AVAILABLE:
        return None

    try:
        bus = smbus2.SMBus(bus_number)
        value = bus.read_byte_data(address, register)
        bus.close()
        return value
    except Exception as e:
        print(f"读取失败: {e}")
        return None

def write_device_register(address, register, value, bus_number=1):
    """写入设备寄存器"""
    if not SMBUS_AVAILABLE:
        return False

    try:
        bus = smbus2.SMBus(bus_number)
        bus.write_byte_data(address, register, value)
        bus.close()
        return True
    except Exception as e:
        print(f"写入失败: {e}")
        return False

def main():
    print("=" * 50)
    print("🔍 I2C 设备扫描器")
    print("=" * 50)

    # 扫描两个总线
    for bus_num in [1, 0]:
        devices = scan_i2c_bus(bus_num)
        if devices:
            display_scan_results(devices)
            break
    else:
        display_scan_results([])

    print("\n💡 提示:")
    print("  也可以使用命令: sudo i2cdetect -y 1")
    print("  查看所有 I2C 总线: ls /dev/i2c*")

if __name__ == "__main__":
    main()