# -*- coding: utf-8 -*-
"""
奶茶店展示系统配置文件
"""
import os

# 基础配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_DIR = os.path.join(STATIC_DIR, 'images')

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Flask配置
SECRET_KEY = 'tea-shop-display-secret-key-2026'
HOST = '0.0.0.0'
PORT = 5000
DEBUG = False

# 内容配置
CONTENT_FILE = os.path.join(DATA_DIR, 'content.json')
DEFAULT_SLIDE_DURATION = 5  # 默认轮播时间(秒)

# WiFi配置
WIFI_CONFIG_FILE = os.path.join(DATA_DIR, 'wifi_config.json')
AP_SSID = 'TeaShop-Display'
AP_PASSWORD = '12345678'
AP_IP = '192.168.4.1'

# 上传文件配置
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# 显示配置
DISPLAY_WIDTH = 1920
DISPLAY_HEIGHT = 1080
FULLSCREEN = True

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS