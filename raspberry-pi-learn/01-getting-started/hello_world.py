#!/usr/bin/env python3
"""
Hello World - Raspberry Pi 第一个程序
演示基本的 Python 输出和系统信息获取
"""

import os
import sys
import platform
from datetime import datetime

def print_banner():
    """打印欢迎横幅"""
    banner = """
    ╔══════════════════════════════════════════╗
    ║   🍓 欢迎来到 Raspberry Pi 学习套件!    ║
    ║      Welcome to Raspberry Pi Learning!   ║
    ╚══════════════════════════════════════════╝
    """
    print(banner)

def get_system_info():
    """获取基本系统信息"""
    info = {
        "操作系统": platform.system(),
        "系统版本": platform.version(),
        "机器架构": platform.machine(),
        "处理器": platform.processor(),
        "Python版本": sys.version.split()[0],
        "当前时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "主机名": platform.node(),
    }
    return info

def check_raspberry_pi():
    """检查是否运行在 Raspberry Pi 上"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            content = f.read()
            if 'Raspberry Pi' in content or 'BCM' in content:
                # 获取型号信息
                for line in content.split('\n'):
                    if 'Model' in line:
                        return True, line.split(':')[1].strip()
                return True, "Raspberry Pi (型号未知)"
    except FileNotFoundError:
        pass
    return False, "非 Raspberry Pi 设备"

def main():
    """主函数"""
    print_banner()
    
    print("=" * 50)
    print("📋 系统信息")
    print("=" * 50)
    
    # 打印系统信息
    info = get_system_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print()
    
    # 检查是否是树莓派
    is_pi, model = check_raspberry_pi()
    if is_pi:
        print(f"✅ 检测到 Raspberry Pi: {model}")
        print("   GPIO 功能可用!")
    else:
        print(f"⚠️  {model}")
        print("   部分 GPIO 功能可能不可用")
    
    print()
    print("=" * 50)
    print("🎉 Hello, Raspberry Pi World!")
    print("   开始你的创客之旅吧!")
    print("=" * 50)

if __name__ == "__main__":
    main()