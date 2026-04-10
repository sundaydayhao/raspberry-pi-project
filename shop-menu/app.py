#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奶茶店HDMI展示系统 - 后端服务器
支持内容管理、WiFi配网和远程控制
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
import subprocess
import socket

app = Flask(__name__)
CORS(app)

CONFIG_FILE = 'config.json'

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_local_ip():
    """获取本机IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_wifi_status():
    """获取WiFi连接状态"""
    try:
        # 在树莓派上检查WiFi状态
        result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return {
                'connected': True,
                'ssid': result.stdout.strip()
            }
    except:
        pass
    return {'connected': False, 'ssid': None}

def scan_wifi_networks():
    """扫描可用的WiFi网络"""
    try:
        # 在树莓派上扫描WiFi
        result = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'], 
                              capture_output=True, text=True, timeout=10)
        networks = []
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            current_network = {}
            for line in lines:
                if 'ESSID:' in line:
                    ssid = line.split('ESSID:')[1].strip().strip('"')
                    if ssid:
                        current_network['ssid'] = ssid
                elif 'Quality=' in line:
                    quality = line.split('Quality=')[1].split()[0]
                    current_network['quality'] = quality
                    if current_network.get('ssid'):
                        networks.append(current_network.copy())
                        current_network = {}
        return networks[:10]  # 返回前10个网络
    except:
        return []

def connect_wifi(ssid, password):
    """连接到WiFi网络"""
    try:
        # 创建wpa_supplicant配置
        wpa_config = f'''
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=CN

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
        # 写入配置文件
        with open('/tmp/wpa_supplicant.conf', 'w') as f:
            f.write(wpa_config)
        
        # 复制到系统目录（需要sudo权限）
        subprocess.run(['sudo', 'cp', '/tmp/wpa_supplicant.conf', 
                       '/etc/wpa_supplicant/wpa_supplicant.conf'])
        
        # 重启网络服务
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'])
        
        return True
    except Exception as e:
        print(f"WiFi连接错误: {e}")
        return False

# 路由：主页（HDMI展示页面）
@app.route('/')
def index():
    """HDMI展示主页"""
    return render_template('display.html')

# 路由：管理页面
@app.route('/admin')
def admin():
    """手机管理页面"""
    return render_template('admin.html')

# API：获取配置
@app.route('/api/config', methods=['GET'])
def get_config():
    """获取当前配置"""
    config = load_config()
    # 不返回WiFi密码
    if 'wifi' in config and 'password' in config['wifi']:
        config['wifi']['password'] = '******' if config['wifi']['password'] else ''
    return jsonify(config)

# API：更新配置
@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        new_config = request.json
        current_config = load_config()
        
        # 合并配置
        if 'shop_name' in new_config:
            current_config['shop_name'] = new_config['shop_name']
        if 'display' in new_config:
            current_config['display'] = new_config['display']
        if 'content' in new_config:
            current_config['content'] = new_config['content']
        
        save_config(current_config)
        return jsonify({'success': True, 'message': '配置已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# API：获取WiFi状态
@app.route('/api/wifi/status', methods=['GET'])
def wifi_status():
    """获取WiFi连接状态"""
    status = get_wifi_status()
    config = load_config()
    status['configured'] = config.get('wifi', {}).get('configured', False)
    status['ip'] = get_local_ip()
    return jsonify(status)

# API：扫描WiFi网络
@app.route('/api/wifi/scan', methods=['GET'])
def wifi_scan():
    """扫描可用的WiFi网络"""
    networks = scan_wifi_networks()
    return jsonify({'networks': networks})

# API：连接WiFi
@app.route('/api/wifi/connect', methods=['POST'])
def wifi_connect():
    """连接到WiFi网络"""
    try:
        data = request.json
        ssid = data.get('ssid')
        password = data.get('password')
        
        if not ssid:
            return jsonify({'success': False, 'message': 'SSID不能为空'}), 400
        
        # 尝试连接
        success = connect_wifi(ssid, password)
        
        if success:
            # 更新配置
            config = load_config()
            config['wifi'] = {
                'ssid': ssid,
                'password': password,
                'configured': True
            }
            save_config(config)
            return jsonify({'success': True, 'message': 'WiFi连接成功'})
        else:
            return jsonify({'success': False, 'message': 'WiFi连接失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# API：系统信息
@app.route('/api/system/info', methods=['GET'])
def system_info():
    """获取系统信息"""
    try:
        # 获取CPU温度
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read()) / 1000.0
        
        # 获取内存使用情况
        mem_info = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line or 'MemAvailable' in line:
                    parts = line.split()
                    mem_info[parts[0].rstrip(':')] = int(parts[1])
        
        mem_used = mem_info.get('MemTotal', 0) - mem_info.get('MemAvailable', 0)
        mem_percent = (mem_used / mem_info.get('MemTotal', 1)) * 100
        
        return jsonify({
            'cpu_temp': round(temp, 1),
            'memory_percent': round(mem_percent, 1),
            'ip': get_local_ip()
        })
    except:
        return jsonify({
            'cpu_temp': 0,
            'memory_percent': 0,
            'ip': get_local_ip()
        })

if __name__ == '__main__':
    print("=" * 50)
    print("奶茶店HDMI展示系统启动中...")
    print(f"本机IP地址: {get_local_ip()}")
    print(f"HDMI展示页面: http://{get_local_ip()}:5000")
    print(f"手机管理页面: http://{get_local_ip()}:5000/admin")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)