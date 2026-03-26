#!/usr/bin/env python3
"""
Flask Web 服务器
在树莓派上运行 Web 服务器，通过浏览器控制 GPIO

功能:
  - 网页控制 LED
  - 实时显示传感器数据
  - REST API 接口
  - WebSocket 实时推送

安装依赖:
  pip3 install flask flask-socketio

访问:
  http://树莓派IP:5000

学习要点:
  - Flask Web 框架
  - REST API 设计
  - 前后端交互
"""

import time
import threading
import json
import sys
import os

try:
    from flask import Flask, render_template_string, jsonify, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️  未找到 Flask")
    print("   安装: pip3 install flask")

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
except ImportError:
    GPIO_AVAILABLE = False

# GPIO 配置
LED_PINS = {
    'led1': 17,
    'led2': 18,
    'led3': 27,
}

if GPIO_AVAILABLE:
    for name, pin in LED_PINS.items():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

# 模拟传感器数据
sensor_data = {
    'temperature': 25.0,
    'humidity': 60.0,
    'light': 500,
}

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍓 Raspberry Pi 控制面板</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; }
        .header { background: #16213e; padding: 20px; text-align: center; }
        .header h1 { color: #e94560; font-size: 2em; }
        .container { max-width: 900px; margin: 20px auto; padding: 0 20px; }
        .card { background: #16213e; border-radius: 10px; padding: 20px; margin: 15px 0; }
        .card h2 { color: #0f3460; color: #e94560; margin-bottom: 15px; }
        .led-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .led-btn { padding: 15px; border: none; border-radius: 8px; cursor: pointer;
                   font-size: 1em; transition: all 0.3s; }
        .led-btn.off { background: #333; color: #999; }
        .led-btn.on { background: #e94560; color: white; box-shadow: 0 0 15px #e94560; }
        .sensor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
        .sensor-item { text-align: center; padding: 15px; background: #0f3460; border-radius: 8px; }
        .sensor-value { font-size: 2em; font-weight: bold; color: #e94560; }
        .sensor-label { color: #aaa; margin-top: 5px; }
        .api-section code { background: #0f3460; padding: 5px 10px; border-radius: 4px;
                            display: block; margin: 5px 0; font-family: monospace; }
        .status { padding: 5px 10px; border-radius: 4px; display: inline-block; margin-top: 10px; }
        .status.ok { background: #2d6a4f; color: #95d5b2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🍓 Raspberry Pi 控制面板</h1>
        <p>通过浏览器控制你的树莓派</p>
    </div>

    <div class="container">
        <div class="card">
            <h2>💡 LED 控制</h2>
            <div class="led-grid" id="led-grid">
                <button class="led-btn off" id="led1" onclick="toggleLED('led1')">LED 1 (GPIO17)</button>
                <button class="led-btn off" id="led2" onclick="toggleLED('led2')">LED 2 (GPIO18)</button>
                <button class="led-btn off" id="led3" onclick="toggleLED('led3')">LED 3 (GPIO27)</button>
            </div>
        </div>

        <div class="card">
            <h2>📊 传感器数据</h2>
            <div class="sensor-grid">
                <div class="sensor-item">
                    <div class="sensor-value" id="temperature">--</div>
                    <div class="sensor-label">🌡️ 温度 (°C)</div>
                </div>
                <div class="sensor-item">
                    <div class="sensor-value" id="humidity">--</div>
                    <div class="sensor-label">💧 湿度 (%)</div>
                </div>
                <div class="sensor-item">
                    <div class="sensor-value" id="light">--</div>
                    <div class="sensor-label">☀️ 光照</div>
                </div>
            </div>
            <span class="status ok">每2秒自动刷新</span>
        </div>

        <div class="card api-section">
            <h2>🔌 API 接口</h2>
            <code>GET  /api/status          - 获取所有状态</code>
            <code>POST /api/led/&lt;name&gt;/on   - 打开 LED</code>
            <code>POST /api/led/&lt;name&gt;/off  - 关闭 LED</code>
            <code>GET  /api/sensors         - 获取传感器数据</code>
        </div>
    </div>

    <script>
        const ledStates = {led1: false, led2: false, led3: false};

        function toggleLED(name) {
            const action = ledStates[name] ? 'off' : 'on';
            fetch(`/api/led/${name}/${action}`, {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    ledStates[name] = data.state;
                    const btn = document.getElementById(name);
                    btn.className = `led-btn ${data.state ? 'on' : 'off'}`;
                    btn.textContent = `${name.toUpperCase()} ${data.state ? '✓ 开' : '关'}`;
                });
        }

        function updateSensors() {
            fetch('/api/sensors')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('temperature').textContent = data.temperature.toFixed(1);
                    document.getElementById('humidity').textContent = data.humidity.toFixed(1);
                    document.getElementById('light').textContent = data.light;
                });
        }

        // 初始化状态
        fetch('/api/status').then(r => r.json()).then(data => {
            Object.keys(data.leds).forEach(name => {
                ledStates[name] = data.leds[name];
                const btn = document.getElementById(name);
                if (btn) {
                    btn.className = `led-btn ${data.leds[name] ? 'on' : 'off'}`;
                }
            });
        });

        updateSensors();
        setInterval(updateSensors, 2000);
    </script>
</body>
</html>
"""

if FLASK_AVAILABLE:
    app = Flask(__name__)

    led_states = {name: False for name in LED_PINS}

    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)

    @app.route('/api/status')
    def api_status():
        return jsonify({
            'leds': led_states,
            'sensors': sensor_data,
            'timestamp': time.time()
        })

    @app.route('/api/led/<name>/<action>', methods=['POST'])
    def api_led(name, action):
        if name not in LED_PINS:
            return jsonify({'error': 'LED not found'}), 404

        state = action == 'on'
        led_states[name] = state

        if GPIO_AVAILABLE:
            GPIO.output(LED_PINS[name], GPIO.HIGH if state else GPIO.LOW)

        return jsonify({'name': name, 'state': state})

    @app.route('/api/sensors')
    def api_sensors():
        # 模拟传感器数据更新
        import random
        sensor_data['temperature'] = round(25 + random.uniform(-2, 2), 1)
        sensor_data['humidity'] = round(60 + random.uniform(-5, 5), 1)
        sensor_data['light'] = random.randint(400, 800)
        return jsonify(sensor_data)

    @app.route('/api/gpio/<int:pin>/<action>', methods=['POST'])
    def api_gpio(pin, action):
        if not GPIO_AVAILABLE:
            return jsonify({'error': 'GPIO not available'}), 503
        try:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH if action == 'on' else GPIO.LOW)
            return jsonify({'pin': pin, 'state': action == 'on'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

def run_server(host='0.0.0.0', port=5000, debug=False):
    """启动 Web 服务器"""
    if not FLASK_AVAILABLE:
        print("Flask 未安装，无法启动服务器")
        return

    import socket
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except Exception:
        ip = '127.0.0.1'

    print(f"\n🌐 Web 服务器启动中...")
    print(f"   本地访问: http://localhost:{port}")
    print(f"   局域网访问: http://{ip}:{port}")
    print(f"   按 Ctrl+C 停止\n")

    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    finally:
        if GPIO_AVAILABLE:
            GPIO.cleanup()

def main():
    print("=" * 40)
    print("🌐 Flask Web 控制服务器")
    print("=" * 40)

    port = input("端口号 (默认 5000): ").strip()
    port = int(port) if port.isdigit() else 5000

    run_server(port=port)

if __name__ == "__main__":
    main()