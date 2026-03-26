#!/usr/bin/env python3
"""
WiFi 扫描与网络管理
扫描周边 WiFi 网络，管理网络连接

功能:
  - 扫描可用 WiFi 网络
  - 显示信号强度
  - 连接/断开 WiFi
  - 获取网络信息
  - 网络速度测试

学习要点:
  - 网络接口管理
  - WiFi 信号分析
  - 网络编程基础
"""

import os
import sys
import time
import subprocess
import socket
import json

def run_command(cmd, timeout=10):
    """执行系统命令"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except Exception as e:
        return str(e), -1

def scan_wifi():
    """扫描 WiFi 网络"""
    print("\n扫描 WiFi 网络...")

    # 尝试使用 nmcli
    output, rc = run_command("nmcli -t -f SSID,SIGNAL,SECURITY,CHAN dev wifi list")
    if rc == 0 and output:
        networks = []
        for line in output.split('\n'):
            if line.strip():
                parts = line.split(':')
                if len(parts) >= 4:
                    networks.append({
                        'ssid': parts[0] or '(隐藏网络)',
                        'signal': int(parts[1]) if parts[1].isdigit() else 0,
                        'security': parts[2] or '开放',
                        'channel': parts[3],
                    })

        if networks:
            networks.sort(key=lambda x: x['signal'], reverse=True)
            print(f"\n发现 {len(networks)} 个 WiFi 网络:\n")
            print(f"{'SSID':<30} {'信号':>6} {'安全':>10} {'信道':>6}")
            print("-" * 60)
            for net in networks:
                signal_bar = '█' * (net['signal'] // 20) + '░' * (5 - net['signal'] // 20)
                lock = '🔒' if net['security'] != '开放' else '🔓'
                print(f"{net['ssid']:<30} {signal_bar} {net['signal']:3d}% {lock}{net['security']:>8} {net['channel']:>6}")
            return networks

    # 尝试使用 iwlist
    output, rc = run_command("sudo iwlist wlan0 scan 2>/dev/null")
    if rc == 0 and output:
        networks = []
        current = {}
        for line in output.split('\n'):
            line = line.strip()
            if 'ESSID:' in line:
                ssid = line.split('"')[1] if '"' in line else ''
                current['ssid'] = ssid or '(隐藏)'
            elif 'Signal level=' in line:
                try:
                    signal = line.split('Signal level=')[1].split(' ')[0]
                    current['signal'] = signal
                except Exception:
                    current['signal'] = 'N/A'
            elif 'Encryption key:' in line:
                current['security'] = 'WPA' if 'on' in line else '开放'
                if current.get('ssid'):
                    networks.append(current.copy())
                    current = {}

        if networks:
            print(f"\n发现 {len(networks)} 个 WiFi 网络:")
            for net in networks:
                print(f"  {net.get('ssid', 'N/A'):<30} 信号:{net.get('signal', 'N/A')} {net.get('security', '')}")
            return networks

    print("无法扫描 WiFi（可能需要 sudo 权限或 nmcli/iwlist）")
    return []

def get_current_connection():
    """获取当前 WiFi 连接信息"""
    print("\n当前网络连接:")

    # 使用 nmcli
    output, rc = run_command("nmcli -t -f NAME,TYPE,STATE,DEVICE con show --active")
    if rc == 0 and output:
        for line in output.split('\n'):
            parts = line.split(':')
            if len(parts) >= 4 and 'wifi' in parts[1].lower():
                print(f"  连接名: {parts[0]}")
                print(f"  状态:   {parts[2]}")
                print(f"  设备:   {parts[3]}")

    # 获取 IP 地址
    output, rc = run_command("ip addr show wlan0 2>/dev/null | grep 'inet '")
    if rc == 0 and output:
        ip = output.strip().split()[1]
        print(f"  IP地址: {ip}")

    # 获取信号强度
    output, rc = run_command("iwconfig wlan0 2>/dev/null | grep 'Signal level'")
    if rc == 0 and output:
        print(f"  {output.strip()}")

def get_network_info():
    """获取详细网络信息"""
    print("\n网络信息:")

    # 主机名
    hostname = socket.gethostname()
    print(f"  主机名: {hostname}")

    # IP 地址
    try:
        ip = socket.gethostbyname(hostname)
        print(f"  本机IP: {ip}")
    except Exception:
        pass

    # 所有网络接口
    output, _ = run_command("ip addr show")
    if output:
        interfaces = []
        current_if = None
        for line in output.split('\n'):
            if ': ' in line and not line.startswith(' '):
                parts = line.split(': ')
                if len(parts) >= 2:
                    current_if = parts[1].split('@')[0]
            elif 'inet ' in line and current_if:
                ip = line.strip().split()[1]
                interfaces.append((current_if, ip))

        print("\n  网络接口:")
        for iface, ip in interfaces:
            print(f"    {iface}: {ip}")

    # 默认网关
    output, _ = run_command("ip route | grep default")
    if output:
        gateway = output.split()[2] if len(output.split()) > 2 else 'N/A'
        print(f"\n  默认网关: {gateway}")

    # DNS
    output, _ = run_command("cat /etc/resolv.conf | grep nameserver")
    if output:
        print("  DNS 服务器:")
        for line in output.split('\n'):
            if 'nameserver' in line:
                print(f"    {line.split()[1]}")

def ping_test(host="8.8.8.8", count=4):
    """Ping 测试"""
    print(f"\nPing 测试: {host}")
    output, rc = run_command(f"ping -c {count} {host}")
    if rc == 0:
        print(output)
    else:
        print(f"Ping 失败: {host}")

def speed_test_simple():
    """简单网速测试（下载测试文件）"""
    print("\n网速测试...")
    test_url = "http://speedtest.tele2.net/1MB.zip"

    start = time.time()
    output, rc = run_command(f"curl -o /dev/null -s -w '%{{speed_download}}' {test_url}", timeout=30)

    if rc == 0 and output:
        try:
            speed_bps = float(output)
            speed_mbps = speed_bps / 1024 / 1024
            elapsed = time.time() - start
            print(f"  下载速度: {speed_mbps:.2f} MB/s ({speed_bps/1024:.1f} KB/s)")
            print(f"  测试耗时: {elapsed:.1f}秒")
        except ValueError:
            print("  无法解析速度数据")
    else:
        print("  速度测试失败（需要网络连接）")

def connect_wifi(ssid, password=None):
    """连接 WiFi"""
    print(f"\n连接到: {ssid}")

    if password:
        cmd = f'nmcli dev wifi connect "{ssid}" password "{password}"'
    else:
        cmd = f'nmcli dev wifi connect "{ssid}"'

    output, rc = run_command(cmd, timeout=30)
    if rc == 0:
        print(f"✅ 已连接到 {ssid}")
    else:
        print(f"❌ 连接失败: {output}")

def main():
    print("=" * 50)
    print("📶 WiFi 网络管理")
    print("=" * 50)

    print("\n选择功能:")
    print("1. 扫描 WiFi 网络")
    print("2. 当前连接信息")
    print("3. 详细网络信息")
    print("4. Ping 测试")
    print("5. 网速测试")
    print("6. 连接 WiFi")

    choice = input("\n请选择 (1-6): ").strip()

    if choice == '1':
        scan_wifi()
    elif choice == '2':
        get_current_connection()
    elif choice == '3':
        get_network_info()
    elif choice == '4':
        host = input("目标地址 (默认 8.8.8.8): ").strip() or "8.8.8.8"
        ping_test(host)
    elif choice == '5':
        speed_test_simple()
    elif choice == '6':
        ssid = input("WiFi 名称 (SSID): ").strip()
        if ssid:
            password = input("密码 (无密码直接回车): ").strip() or None
            connect_wifi(ssid, password)
    else:
        get_network_info()

if __name__ == "__main__":
    main()