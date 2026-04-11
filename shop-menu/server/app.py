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

DEFAULT_PRODUCTS = [
    {
        'id': 'classic-boba',
        'name': '经典珍珠奶茶',
        'category': '经典奶茶',
        'price': '16',
        'description': '锡兰红茶搭配Q弹黑糖珍珠',
        'image': '',
        'badge': '门店热销',
        'enabled': True
    },
    {
        'id': 'matcha-milk',
        'name': '抹茶鲜奶',
        'category': '鲜奶系列',
        'price': '18',
        'description': '现打抹茶与冰博克牛乳融合',
        'image': '',
        'badge': '清新推荐',
        'enabled': True
    },
    {
        'id': 'grape-yogurt',
        'name': '多肉葡萄酸奶',
        'category': '果茶系列',
        'price': '22',
        'description': '葡萄果肉加酸奶，口感轻盈',
        'image': '',
        'badge': '新品',
        'enabled': True
    },
    {
        'id': 'cheese-oolong',
        'name': '芝士乌龙奶盖',
        'category': '奶盖系列',
        'price': '20',
        'description': '乌龙茶香上覆盖咸甜芝士奶盖',
        'image': '',
        'badge': '招牌',
        'enabled': True
    }
]


def build_default_content():
    """构造默认展示内容"""
    return {
        'slides': [
            {
                'id': 1,
                'title': '欢迎光临',
                'subtitle': '精选好茶 用心制作',
                'content': '现煮茶底 · 鲜奶现调 · 每日现做',
                'image': '',
                'backgroundColor': '#B85C38',
                'duration': 5
            },
            {
                'id': 2,
                'title': '本周特惠',
                'subtitle': '第二杯半价',
                'content': '指定奶茶第二杯半价\n活动时间：周一至周五 14:00-18:00',
                'image': '',
                'backgroundColor': '#4F6F52',
                'duration': 5
            },
            {
                'id': 3,
                'title': '新品推荐',
                'subtitle': '轻乳果茶系列',
                'content': '鲜果现切 · 茶香清爽\n适合春夏的轻负担选择',
                'image': '',
                'backgroundColor': '#D4A373',
                'duration': 5
            }
        ],
        'products': [product.copy() for product in DEFAULT_PRODUCTS],
        'settings': {
            'defaultDuration': 5,
            'transition': 'fade',
            'autoPlay': True,
            'menuTitle': '本店热卖奶茶',
            'menuSubtitle': '支持少糖 / 去冰 / 加料定制',
            'productsPerPage': 6
        }
    }


def safe_positive_int(value, default_value):
    """将输入转换为正整数，失败时返回默认值"""
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default_value
    except (TypeError, ValueError):
        return default_value


def normalize_content(content_data):
    """兼容旧格式并补齐默认字段"""
    default_content = build_default_content()
    if not isinstance(content_data, dict):
        return default_content

    normalized = {
        'slides': [],
        'products': [],
        'settings': default_content['settings'].copy()
    }

    has_slide_list = 'slides' in content_data and isinstance(content_data.get('slides'), list)
    slides = content_data.get('slides')
    if has_slide_list:
        for index, slide in enumerate(slides):
            if not isinstance(slide, dict):
                continue
            normalized['slides'].append({
                'id': slide.get('id', index + 1),
                'title': str(slide.get('title', '')).strip(),
                'subtitle': str(slide.get('subtitle', '')).strip(),
                'content': str(slide.get('content', '')).strip(),
                'image': str(slide.get('image', '')).strip(),
                'backgroundColor': str(
                    slide.get(
                        'backgroundColor',
                        default_content['slides'][index % len(default_content['slides'])]['backgroundColor']
                    )
                ).strip() or default_content['slides'][index % len(default_content['slides'])]['backgroundColor'],
                'duration': safe_positive_int(
                    slide.get('duration'),
                    default_content['settings']['defaultDuration']
                )
            })

    if not has_slide_list:
        normalized['slides'] = default_content['slides']

    has_product_list = 'products' in content_data and isinstance(content_data.get('products'), list)
    has_legacy_product_list = 'menu_items' in content_data and isinstance(content_data.get('menu_items'), list)
    products = content_data.get('products')
    if not has_product_list and has_legacy_product_list:
        products = content_data.get('menu_items')

    if has_product_list or has_legacy_product_list:
        for index, product in enumerate(products):
            if not isinstance(product, dict):
                continue

            name = str(product.get('name') or product.get('title') or '').strip()
            if not name:
                continue

            normalized['products'].append({
                'id': product.get('id', f'product-{index + 1}'),
                'name': name,
                'category': str(product.get('category', '')).strip(),
                'price': str(product.get('price', '')).strip(),
                'description': str(product.get('description', '')).strip(),
                'image': str(product.get('image', '')).strip(),
                'badge': str(product.get('badge', '')).strip(),
                'enabled': bool(product.get('enabled', True))
            })

    if not (has_product_list or has_legacy_product_list):
        normalized['products'] = [product.copy() for product in default_content['products']]

    settings = content_data.get('settings', {})
    if isinstance(settings, dict):
        normalized['settings'].update(settings)

    normalized['settings']['defaultDuration'] = safe_positive_int(
        normalized['settings'].get('defaultDuration'),
        default_content['settings']['defaultDuration']
    )
    normalized['settings']['productsPerPage'] = safe_positive_int(
        normalized['settings'].get('productsPerPage'),
        default_content['settings']['productsPerPage']
    )
    normalized['settings']['autoPlay'] = normalized['settings'].get('autoPlay', True) is not False
    normalized['settings']['transition'] = str(
        normalized['settings'].get('transition', default_content['settings']['transition'])
    ).strip() or default_content['settings']['transition']
    normalized['settings']['menuTitle'] = str(
        normalized['settings'].get('menuTitle', default_content['settings']['menuTitle'])
    ).strip() or default_content['settings']['menuTitle']
    normalized['settings']['menuSubtitle'] = str(
        normalized['settings'].get('menuSubtitle', default_content['settings']['menuSubtitle'])
    ).strip() or default_content['settings']['menuSubtitle']

    return normalized

def load_content():
    """加载展示内容"""
    try:
        if os.path.exists(config.CONTENT_FILE):
            with open(config.CONTENT_FILE, 'r', encoding='utf-8') as f:
                return normalize_content(json.load(f))
    except Exception as e:
        print(f"加载内容失败: {e}")

    return build_default_content()

def save_content(content_data):
    """保存展示内容"""
    try:
        normalized_content = normalize_content(content_data)
        with open(config.CONTENT_FILE, 'w', encoding='utf-8') as f:
            json.dump(normalized_content, f, ensure_ascii=False, indent=2)
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
