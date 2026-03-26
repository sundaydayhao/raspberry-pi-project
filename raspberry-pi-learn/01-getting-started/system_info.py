#!/usr/bin/env python3
"""
系统信息监控工具
显示 Raspberry Pi 的详细系统状态信息
"""

import os
import sys
import time
import subprocess
from datetime import datetime, timedelta

def get_cpu_temperature():
    """获取 CPU 温度"""
    try:
        # 方法1：通过 vcgencmd
        result = subprocess.run(
            ['vcgencmd', 'measure_temp'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            temp_str = result.stdout.strip()
            temp = float(temp_str.replace("temp=", "").replace("'C", ""))
            return temp
    except (FileNotFoundError, ValueError):
        pass
    
    try:
        # 方法2：通过 thermal_zone
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = int(f.read().strip()) / 1000.0
            return temp
    except FileNotFoundError:
        return None

def get_cpu_usage():
    """获取 CPU 使用率"""
    try:
        import psutil
        return psutil.cpu_percent(interval=1)
    except ImportError:
        # 手动计算
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            values = list(map(int, line.split()[1:]))
            idle = values[3]
            total = sum(values)
            time.sleep(0.1)
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            values2 = list(map(int, line.split()[1:]))
            idle2 = values2[3]
            total2 = sum(values2)
            usage = 100 * (1 - (idle2 - idle) / (total2 - total))
            return round(usage, 1)
        except Exception:
            return None

def get_memory_info():
    """获取内存信息"""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        
        mem_info = {}
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].rstrip(':')
                value = int(parts[1])  # kB
                mem_info[key] = value
        
        total = mem_info.get('MemTotal', 0)
        free = mem_info.get('MemFree', 0)
        available = mem_info.get('MemAvailable', 0)
        used = total - available
        
        return {
            'total': total // 1024,  # MB
            'used': used // 1024,
            'free': free // 1024,
            'available': available // 1024,
            'percent': round(used / total * 100, 1) if total > 0 else 0
        }
    except Exception:
        return None

def get_disk_info():
    """获取磁盘信息"""
    try:
        result = subprocess.run(
            ['df', '-h', '/'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                return {
                    'total': parts[1],
                    'used': parts[2],
                    'free': parts[3],
                    'percent': parts[4]
                }
    except Exception:
        pass
    return None

def get_uptime():
    """获取系统运行时间"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
        
        uptime = timedelta(seconds=int(uptime_seconds))
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{days}天 {hours}小时 {minutes}分钟 {seconds}秒"
    except Exception:
        return "未知"

def get_network_info():
    """获取网络信息"""
    networks = {}
    try:
        result = subprocess.run(
            ['ip', 'addr', 'show'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            current_iface = None
            for line in result.stdout.split('\n'):
                if ': ' in line and not line.startswith(' '):
                    parts = line.split(': ')
                    if len(parts) >= 2:
                        current_iface = parts[1].split('@')[0]
                        networks[current_iface] = []
                elif 'inet ' in line and current_iface:
                    ip = line.strip().split()[1]
                    networks[current_iface].append(ip)
    except Exception:
        pass
    return networks

def get_gpu_memory():
    """获取 GPU 内存分配"""
    try:
        result = subprocess.run(
            ['vcgencmd', 'get_mem', 'gpu'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip().replace('gpu=', '')
    except FileNotFoundError:
        pass
    return "N/A"

def get_raspberry_pi_model():
    """获取树莓派型号"""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            return f.read().strip().replace('\x00', '')
    except FileNotFoundError:
        pass
    
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Model'):
                    return line.split(':')[1].strip()
    except Exception:
        pass
    
    return "未知设备"

def display_system_info():
    """显示完整系统信息"""
    print("\n" + "=" * 60)
    print("🍓 Raspberry Pi 系统信息监控")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 设备信息
    model = get_raspberry_pi_model()
    print(f"\n📱 设备型号: {model}")
    print(f"   运行时间: {get_uptime()}")
    
    # CPU 信息
    print("\n🔧 CPU 信息:")
    cpu_temp = get_cpu_temperature()
    if cpu_temp is not None:
        temp_icon = "🔥" if cpu_temp > 70 else "🌡️"
        print(f"   {temp_icon} 温度: {cpu_temp:.1f}°C", end="")
        if cpu_temp > 80:
            print(" ⚠️ 过热警告!")
        elif cpu_temp > 70:
            print(" ⚠️ 温度偏高")
        else:
            print(" ✅ 正常")
    
    cpu_usage = get_cpu_usage()
    if cpu_usage is not None:
        bar_len = int(cpu_usage / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"   📊 使用率: [{bar}] {cpu_usage}%")
    
    # 内存信息
    print("\n💾 内存信息:")
    mem = get_memory_info()
    if mem:
        bar_len = int(mem['percent'] / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"   总计: {mem['total']} MB")
        print(f"   已用: {mem['used']} MB")
        print(f"   可用: {mem['available']} MB")
        print(f"   使用率: [{bar}] {mem['percent']}%")
    
    # GPU 内存
    gpu_mem = get_gpu_memory()
    print(f"   GPU内存: {gpu_mem}")
    
    # 磁盘信息
    print("\n💿 磁盘信息 (/):")
    disk = get_disk_info()
    if disk:
        print(f"   总计: {disk['total']}")
        print(f"   已用: {disk['used']} ({disk['percent']})")
        print(f"   剩余: {disk['free']}")
    
    # 网络信息
    print("\n🌐 网络信息:")
    networks = get_network_info()
    for iface, ips in networks.items():
        if iface != 'lo' and ips:
            for ip in ips:
                print(f"   {iface}: {ip}")
    
    print("\n" + "=" * 60)

def monitor_mode(interval=2):
    """持续监控模式"""
    print("进入持续监控模式 (按 Ctrl+C 退出)")
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            display_system_info()
            print(f"\n⏱️  每 {interval} 秒刷新一次...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n监控已停止")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Raspberry Pi 系统信息监控')
    parser.add_argument('-m', '--monitor', action='store_true',
                        help='持续监控模式')
    parser.add_argument('-i', '--interval', type=int, default=2,
                        help='监控刷新间隔（秒），默认2秒')
    args = parser.parse_args()
    
    if args.monitor:
        monitor_mode(args.interval)
    else:
        display_system_info()