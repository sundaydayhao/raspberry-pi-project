# -*- coding: utf-8 -*-
"""
奶茶店展示系统Flask应用
"""
import os
import json
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from . import config
from .wifi_manager import WiFiManager

app = Flask(__name__, 
            template_folder=os.path.join(config.BASE_DIR, 'templates'),
            static_folder=config.STATIC_DIR)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
CORS(app)

# 初始化WiFi管理器
wifi_manager = WiFiManager()

def load_content():
    """加载展示内容"""
    try:
        if os.path.exists(config.CONTENT_FILE):
            with open(config.CONTENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载内容失败: {e}")
    
    # 返回默认内容
    return {
        'slides': [
            {
                'id': 1,
                'title': '欢迎光临',
                'subtitle': '精选好茶 用心制作',
                'content': '新鲜水果 · 优质茶叶 · 健康饮品',
                'image': '',
                'backgroundColor': '#FF6B9D',
                'duration': 5
            },
            {
                'id': 2,
                'title': '本周特惠',
                'subtitle': '第二杯半价',
                'content': '全场饮品第二杯半价\n活动时间：周一至周五',
                'image': '',
                'backgroundColor': '#4ECDC4',
                'duration': 5
            },
            {
                'id': 3,
                'title': '新品推荐',
                'subtitle': '芝士奶盖系列',
                'content': '浓郁芝士 · 香滑奶盖\n多种口味任你选择',
                'image': '',
                'backgroundColor': '#FFD93D',
                'duration': 5
            }
        ],
        'settings': {
            'defaultDuration': 5,
            'transition': 'fade',
            'autoPlay': True
        }
    }

def save_content(content_data):
    """保存展示内容"""
    try:
        with open(config.CONTENT_FILE, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存内容失败: {e}")
        return False

# ==================== 展示页面路由 ====================

@app.route('/')
@app.route('/display')
def display():
    """展示页面"""
    return render_template('display.html')

@app.route('/api/content')
def get_content():
    """获取展示内容API"""
    content = load_content()
    return jsonify(content)

# ==================== 管理后台路由 ====================

@app.route('/admin')
def admin():
    """管理后台页面"""
    return render_template('admin.html')

@app.route('/api/admin/content', methods=['GET'])
def admin_get_content():
    """获取内容（管理端）"""
    content = load_content()
    return jsonify({'success': True, 'data': content})

@app.route('/api/admin/content', methods=['POST'])
def admin_save_content():
    """保存内容"""
    try:
        content_data = request.json
        if save_content(content_data):
            return jsonify({'success': True, 'message': '保存成功'})
        else:
            return jsonify({'success': False, 'message': '保存失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/upload', methods=['POST'])
def upload_image():
    """上传图片"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'})
        
        if file and config.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 添加时间戳避免重名
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(time.time())}{ext}"
            
            filepath = os.path.join(config.UPLOAD_DIR, filename)
            file.save(filepath)
            
            # 返回相对URL
            url = f"/static/images/{filename}"
            return jsonify({'success': True, 'url': url})
        else:
            return jsonify({'success': False, 'message': '不支持的文件类型'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ==================== WiFi配网路由 ====================

@app.route('/wifi')
def wifi_config():
    """WiFi配置页面"""
    return render_template('wifi.html')

@app.route('/api/wifi/status')
def wifi_status():
    """获取WiFi状态"""
    status = wifi_manager.get_wifi_status()
    return jsonify({
        'success': True,
        'data': {
            'connected': status['connected'],
            'ssid': status['ssid'],
            'ap_mode': wifi_manager.ap_mode
        }
    })

@app.route('/api/wifi/scan')
def wifi_scan():
    """扫描WiFi"""
    networks = wifi_manager.scan_wifi()
    return jsonify({'success': True, 'data': networks})

@app.route('/api/wifi/connect', methods=['POST'])
def wifi_connect():
    """连接WiFi"""
    try:
        data = request.json
        ssid = data.get('ssid')
        password = data.get('password')
        
        if not ssid:
            return jsonify({'success': False, 'message': 'SSID不能为空'})
        
        result = wifi_manager.connect_wifi(ssid, password)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ==================== 静态文件路由 ====================

@app.route('/static/<path:filename>')
def static_files(filename):
    """静态文件服务"""
    return send_from_directory(config.STATIC_DIR, filename)

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def run_server():
    """运行服务器"""
    # 启动时尝试自动连接WiFi
    print("正在检查WiFi连接...")
    wifi_manager.auto_connect()
    
    # 启动Flask服务
    print(f"启动服务器: http://{config.HOST}:{config.PORT}")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )

if __name__ == '__main__':
    run_server()