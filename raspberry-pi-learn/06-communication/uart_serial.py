#!/usr/bin/env python3
"""
UART 串口通信
演示树莓派串口通信

硬件连接 (与另一设备通信):
  TX (GPIO14) ── 对方 RX
  RX (GPIO15) ── 对方 TX
  GND ──────── 共地

启用串口:
  sudo raspi-config -> Interface Options -> Serial Port
  禁用串口登录 shell，启用串口硬件

安装依赖:
  pip3 install pyserial

学习要点:
  - UART 通信协议
  - 串口配置参数
  - 数据收发
"""

import time
import sys
import threading

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("⚠️  未找到 pyserial 库")
    print("   安装: pip3 install pyserial")

SERIAL_PORT = '/dev/ttyS0'   # 树莓派串口
BAUD_RATE = 9600
TIMEOUT = 1

def list_serial_ports():
    """列出所有可用串口"""
    print("\n可用串口:")
    if SERIAL_AVAILABLE:
        ports = serial.tools.list_ports.comports()
        if ports:
            for port in ports:
                print(f"  {port.device}: {port.description}")
        else:
            print("  未发现串口设备")
    else:
        import os
        for dev in ['/dev/ttyS0', '/dev/ttyAMA0', '/dev/ttyUSB0', '/dev/ttyACM0']:
            if os.path.exists(dev):
                print(f"  {dev}")

def open_serial(port=SERIAL_PORT, baud=BAUD_RATE):
    """打开串口"""
    if not SERIAL_AVAILABLE:
        print("pyserial 未安装")
        return None

    try:
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=TIMEOUT
        )
        print(f"✅ 串口已打开: {port} @ {baud} bps")
        return ser
    except serial.SerialException as e:
        print(f"❌ 打开串口失败: {e}")
        return None

def send_data(ser, data):
    """发送数据"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    ser.write(data)
    print(f"  → 发送: {data}")

def receive_data(ser, timeout=5):
    """接收数据"""
    print(f"  等待数据 ({timeout}秒超时)...")
    ser.timeout = timeout
    data = ser.readline()
    if data:
        print(f"  ← 接收: {data}")
        try:
            print(f"  解码: {data.decode('utf-8').strip()}")
        except UnicodeDecodeError:
            print(f"  十六进制: {data.hex()}")
        return data
    else:
        print("  超时，未收到数据")
        return None

def loopback_test(ser):
    """回环测试（TX 连接 RX）"""
    print("\n回环测试 (需要将 TX 连接到 RX)")
    test_messages = ["Hello!", "12345", "测试数据"]

    for msg in test_messages:
        send_data(ser, msg + '\n')
        time.sleep(0.1)
        received = ser.readline()
        if received:
            decoded = received.decode('utf-8', errors='replace').strip()
            status = "✅" if decoded == msg else "❌"
            print(f"  {status} 发送: '{msg}' | 接收: '{decoded}'")
        else:
            print(f"  ❌ 发送: '{msg}' | 未收到回应")
        time.sleep(0.2)

def continuous_receive(ser):
    """持续接收数据"""
    print("\n持续接收模式 (Ctrl+C 退出)")
    ser.timeout = 0.1

    try:
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                timestamp = time.strftime("%H:%M:%S")
                try:
                    decoded = data.decode('utf-8', errors='replace')
                    print(f"  [{timestamp}] ← {decoded}", end='')
                except Exception:
                    print(f"  [{timestamp}] ← {data.hex()}")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n接收已停止")

def chat_mode(ser):
    """双向通信聊天模式"""
    print("\n聊天模式 (输入消息发送，Ctrl+C 退出)")

    # 启动接收线程
    stop_event = threading.Event()

    def receive_thread():
        ser.timeout = 0.1
        while not stop_event.is_set():
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                try:
                    msg = data.decode('utf-8', errors='replace').strip()
                    if msg:
                        print(f"\n  ← 收到: {msg}")
                        print("  发送: ", end='', flush=True)
                except Exception:
                    pass
            time.sleep(0.05)

    recv_thread = threading.Thread(target=receive_thread, daemon=True)
    recv_thread.start()

    try:
        while True:
            msg = input("  发送: ")
            if msg:
                send_data(ser, msg + '\n')
    except KeyboardInterrupt:
        stop_event.set()
        print("\n聊天已结束")

def gps_reader(port='/dev/ttyUSB0', baud=9600):
    """读取 GPS 模块数据（NMEA 格式）"""
    print(f"\nGPS 数据读取 ({port})")
    ser = open_serial(port, baud)
    if not ser:
        return

    print("读取 NMEA 数据 (Ctrl+C 退出)")
    try:
        while True:
            line = ser.readline().decode('ascii', errors='replace').strip()
            if line.startswith('$GPRMC') or line.startswith('$GPGGA'):
                print(f"  {line}")
                # 解析 GPRMC
                if line.startswith('$GPRMC'):
                    parts = line.split(',')
                    if len(parts) >= 7 and parts[2] == 'A':
                        lat = parts[3]
                        lon = parts[5]
                        speed = parts[7]
                        print(f"    纬度: {lat}, 经度: {lon}, 速度: {speed} 节")
    except KeyboardInterrupt:
        print("\nGPS 读取已停止")
    finally:
        ser.close()

def main():
    print("=" * 40)
    print("📡 UART 串口通信")
    print("=" * 40)

    list_serial_ports()

    print("\n选择模式:")
    print("1. 回环测试")
    print("2. 持续接收")
    print("3. 聊天模式")
    print("4. GPS 读取")

    choice = input("\n请选择 (1-4): ").strip()

    if choice == '4':
        gps_reader()
        return

    port = input(f"串口设备 (默认 {SERIAL_PORT}): ").strip() or SERIAL_PORT
    baud = input(f"波特率 (默认 {BAUD_RATE}): ").strip()
    baud = int(baud) if baud.isdigit() else BAUD_RATE

    ser = open_serial(port, baud)
    if not ser:
        return

    try:
        if choice == '1':
            loopback_test(ser)
        elif choice == '2':
            continuous_receive(ser)
        elif choice == '3':
            chat_mode(ser)
        else:
            loopback_test(ser)
    finally:
        ser.close()
        print("串口已关闭")

if __name__ == "__main__":
    main()