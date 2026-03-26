#!/usr/bin/env python3
"""
网络配置工具
用于配置和检测 Raspberry Pi 的网络连接
"""

import os
import subprocess
import socket
import time

def get_ip_address(interface='wlan0'):
    """获取指定网络接口的 IP 地址"""
    try:
        result = subprocess.run(
            ['ip', 'addr', 'show', interface],
            capture_output=True, text=True
        )
        for line in result.stdout.split('\n'):
            if 'inet ' in line:
                ip = line.strip().split()[1].split('/')[0]
                return ip
    except Exception:
        pass
    return None

def get_all_interfaces():
    """获取所有网络接口信息"""
    interfaces = {}
    try:
        result = subprocess.run(
            ['ip', '-o', 'addr', 'show'],
            capture_output=True, text=True
        )
        for line in result.stdout.split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    iface = parts[1]
                    if 'inet' in parts[2]:
                        ip = parts[3].split('/')[0]
                        if iface not in interfaces:
                            interfaces[iface] = []
                        interfaces[iface].append(ip)
    except Exception:
        pass
    return interfaces

def check_internet_connection():
    """检查互联网连接"""
    test_hosts = [
        ('8.8.8.8', '谷歌 DNS'),
        ('114.114.114.114', '国内 DNS'),
        ('baidu.com', '百度'),
    ]
    
    print("\n🌐 检查互联网连接...")
    connected = False
    
    for host, name in test_hosts:
        try:
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, 53))
            print(f"  ✅ {name} ({host}) - 可达")
            connected = True
        except socket.error:
            print(f"  ❌ {name} ({host}) - 不可达")
    
    return connected

def scan_wifi_networks():
    """扫描可用 WiFi 网络"""
    print("\n📡 扫描 WiFi 网络...")
    try:
        result = subprocess.run(
            ['sudo', 'iwlist', 'wlan0', 'scan'],
            capture_output=True, text=True
        )
        
        networks = []
        current_network = {}
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if 'Cell' in line and 'Address' in line:
                if current_network:
                    networks.append(current_network)
                current_network = {'mac': line.split('Address:')[1].strip()}
            elif 'ESSID:' in line:
                ssid = line.split('ESSID:')[1].strip().strip('"')
                current_network['ssid'] = ssid
            elif 'Signal level' in line:
                try:
                    signal = line.split('Signal level=')[1].split(' ')[0]
                    current_network['signal'] = signal
                except IndexError:
                    pass
            elif 'Encryption key:' in line:
                current_network['encrypted'] = 'on' in line
        
        if current_network:
            networks.append(current_network)
        
        if networks:
            print(f"  发现 {len(networks)} 个网络:")
            for net in networks:
                ssid = net.get('ssid', '隐藏网络')
                signal = net.get('signal', 'N/A')
                lock = "🔒" if net.get('encrypted') else "🔓"
                print(f"  {lock} {ssid:30s} 信号: {signal}")
        else:
            print("  未发现 WiFi 网络")
            
    except Exception as e:
        print(f"  扫描失败: {e}")
        print("  提示: 需要 sudo 权限")

def configure_wifi(ssid, password):
    """配置 WiFi 连接"""
    wpa_config = f"""
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
    
    print(f"\n配置 WiFi: {ssid}")
    
    # 追加到 wpa_supplicant.conf
    config_file = '/etc/wpa_supplicant/wpa_supplicant.conf'
    
    try:
        with open(config_file, 'a') as f:
            f.write(wpa_config)
        
        # 重新加载配置
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'])
        
        print("✅ WiFi 配置已更新")
        print("等待连接...")
        time.sleep(5)
        
        ip = get_ip_address('wlan0')
        if ip:
            print(f"✅ 已连接! IP 地址: {ip}")
        else:
            print("❌ 连接失败，请检查密码")
            
    except PermissionError:
        print("❌ 权限不足，请使用 sudo 运行")
    except Exception as e:
        print(f"❌ 配置失败: {e}")

def show_network_status():
    """显示网络状态"""
    print("\n" + "=" * 50)
    print("🌐 网络状态信息")
    print("=" * 50)
    
    # 获取所有接口
    interfaces = get_all_interfaces()
    
    print("\n📋 网络接口:")
    for iface, ips in interfaces.items():
        if iface == 'lo':
            continue
        status = "✅" if ips else "❌"
        print(f"  {status} {iface}:")
        for ip in ips:
            print(f"     IP: {ip}")
    
    # 检查互联网
    check_internet_connection()
    
    # 显示主机名
    hostname = socket.gethostname()
    print(f"\n🏠 主机名: {hostname}")
    
    # 显示 DNS 配置
    print("\n🔍 DNS 配置:")
    try:
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if line.startswith('nameserver'):
                    print(f"  {line.strip()}")
    except Exception:
        pass
    
    print("\n" + "=" * 50)

def ping_test(host='8.8.8.8', count=4):
    """Ping 测试"""
    print(f"\n🏓 Ping 测试 ({host})...")
    try:
        result = subprocess.run(
            ['ping', '-c', str(count), host],
            capture_output=True, text=True
        )
        print(result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"Ping 失败: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Raspberry Pi 网络配置工具')
    parser.add_argument('--status', action='store_true', help='显示网络状态')
    parser.add_argument('--scan', action='store_true', help='扫描 WiFi 网络')
    parser.add_argument('--ping', metavar='HOST', help='Ping 测试')
    parser.add_argument('--connect', nargs=2, metavar=('SSID', 'PASSWORD'),
                        help='连接 WiFi')
    
    args = parser.parse_args()
    
    if args.status:
        show_network_status()
    elif args.scan:
        scan_wifi_networks()
    elif args.ping:
        ping_test(args.ping)
    elif args.connect:
        configure_wifi(args.connect[0], args.connect[1])
    else:
        # 默认显示状态
        show_network_status()