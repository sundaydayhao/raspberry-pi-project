# -*- coding: utf-8 -*-
"""
WiFi管理模块
用于处理WiFi配网和AP模式切换
"""
import os
import json
import subprocess
import time
from . import config

class WiFiManager:
    def __init__(self):
        self.wifi_config_file = config.WIFI_CONFIG_FILE
        self.ap_mode = False
        
    def get_wifi_status(self):
        """获取当前WiFi连接状态"""
        try:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.startswith('yes:'):
                    ssid = line.split(':', 1)[1]
                    return {'connected': True, 'ssid': ssid}
            
            return {'connected': False, 'ssid': None}
        except Exception as e:
            print(f"获取WiFi状态失败: {e}")
            return {'connected': False, 'ssid': None}
    
    def scan_wifi(self):
        """扫描可用WiFi网络"""
        try:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            networks = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if not line:
                    continue
                parts = line.split(':')
                if len(parts) >= 3:
                    ssid = parts[0]
                    signal = parts[1]
                    security = parts[2]
                    
                    if ssid and ssid not in [n['ssid'] for n in networks]:
                        networks.append({
                            'ssid': ssid,
                            'signal': int(signal) if signal.isdigit() else 0,
                            'security': security if security else 'Open'
                        })
            
            # 按信号强度排序
            networks.sort(key=lambda x: x['signal'], reverse=True)
            return networks
        except Exception as e:
            print(f"扫描WiFi失败: {e}")
            return []
    
    def connect_wifi(self, ssid, password=None):
        """连接到指定WiFi"""
        try:
            # 先删除已存在的连接
            subprocess.run(
                ['nmcli', 'connection', 'delete', ssid],
                capture_output=True,
                timeout=5
            )
            
            # 创建新连接
            if password:
                cmd = [
                    'nmcli', 'dev', 'wifi', 'connect', ssid,
                    'password', password
                ]
            else:
                cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # 保存配置
                self.save_wifi_config(ssid, password)
                return {'success': True, 'message': '连接成功'}
            else:
                return {'success': False, 'message': f'连接失败: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'message': f'连接异常: {str(e)}'}
    
    def save_wifi_config(self, ssid, password):
        """保存WiFi配置"""
        try:
            config_data = {
                'ssid': ssid,
                'password': password,
                'timestamp': time.time()
            }
            with open(self.wifi_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存WiFi配置失败: {e}")
    
    def load_wifi_config(self):
        """加载WiFi配置"""
        try:
            if os.path.exists(self.wifi_config_file):
                with open(self.wifi_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载WiFi配置失败: {e}")
        return None
    
    def start_ap_mode(self):
        """启动AP模式"""
        try:
            # 停止现有连接
            subprocess.run(
                ['nmcli', 'radio', 'wifi', 'off'],
                timeout=5
            )
            time.sleep(1)
            subprocess.run(
                ['nmcli', 'radio', 'wifi', 'on'],
                timeout=5
            )
            time.sleep(2)
            
            # 创建热点
            result = subprocess.run([
                'nmcli', 'dev', 'wifi', 'hotspot',
                'ssid', config.AP_SSID,
                'password', config.AP_PASSWORD
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.ap_mode = True
                print(f"AP模式已启动: {config.AP_SSID}")
                return True
            else:
                print(f"启动AP模式失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"启动AP模式异常: {e}")
            return False
    
    def stop_ap_mode(self):
        """停止AP模式"""
        try:
            subprocess.run(
                ['nmcli', 'connection', 'down', 'Hotspot'],
                timeout=5
            )
            self.ap_mode = False
            print("AP模式已停止")
            return True
        except Exception as e:
            print(f"停止AP模式失败: {e}")
            return False
    
    def auto_connect(self):
        """自动连接WiFi"""
        # 检查当前连接状态
        status = self.get_wifi_status()
        if status['connected']:
            print(f"已连接到WiFi: {status['ssid']}")
            return True
        
        # 尝试连接保存的WiFi
        saved_config = self.load_wifi_config()
        if saved_config:
            print(f"尝试连接到保存的WiFi: {saved_config['ssid']}")
            result = self.connect_wifi(
                saved_config['ssid'],
                saved_config.get('password')
            )
            if result['success']:
                return True
        
        # 连接失败，启动AP模式
        print("无法连接WiFi，启动AP模式")
        return self.start_ap_mode()