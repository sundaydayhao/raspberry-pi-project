#!/usr/bin/env python3
"""
智能植物养护系统 - Web控制台
Smart Plant Care System with Web Dashboard

功能：
- 土壤湿度监测（电容式土壤湿度传感器 + MCP3008 ADC）
- 温湿度监测（DHT11）
- 光照强度监测（光敏电阻 + MCP3008 ADC）
- 自动/手动浇水控制（继电器控制水泵）
- 浇水历史记录
- Web控制台：实时数据 + 远程控制

硬件连接：
- DHT11: GPIO4
- MCP3008 (SPI): CLK=GPIO11, MOSI=GPIO10, MISO=GPIO9, CS=GPIO8
  - CH0: 土壤湿度传感器
  - CH1: 光敏电阻（分压电路）
- 继电器（水泵）: GPIO18

访问地址：http://<树莓派IP>:5001
"""

import time
import json
import threading
from datetime import datetime
from collections import deque
from flask import Flask, render_template, jsonify, request

try:
    import RPi.GPIO as GPIO
    import Adafruit_DHT
    import spidev
    REAL_HARDWARE = True
    print("✓ 硬件模式：使用真实传感器")
except ImportError:
    REAL_HARDWARE = False
    import random
    import math
    print("⚠ 模拟模式：使用虚拟传感器数据")

# ==================== 配置 ====================
DHT_PIN = 4
PUMP_PIN = 18        # 继电器控制引脚（LOW触发）
SOIL_CHANNEL = 0     # MCP3008通道0：土壤湿度
LIGHT_CHANNEL = 1    # MCP3008通道1：光照

# 土壤湿度阈值（0-1023，值越小越湿）
SOIL_DRY_THRESHOLD = 600    # 低于此值认为干燥，需要浇水
SOIL_WET_THRESHOLD = 300    # 高于此值认为足够湿润

# 自动浇水配置
AUTO_WATER = True           # 是否开启自动浇水
WATER_DURATION = 5          # 每次浇水时长（秒）
WATER_COOLDOWN = 300        # 浇水冷却时间（秒），防止过度浇水

SAMPLE_INTERVAL = 5

# ==================== 全局状态 ====================
plant_data = {
    'soil_moisture': 0,      # 0-100%
    'soil_raw': 0,           # ADC原始值
    'temperature': 0.0,
    'humidity': 0.0,
    'light_level': 0,        # 0-100%
    'pump_running': False,
    'auto_water': AUTO_WATER,
    'timestamp': '',
    'status': '正常',
    'status_color': 'green'
}

water_history = deque(maxlen=30)
soil_history = deque(maxlen=100)
temp_history = deque(maxlen=100)
time_history = deque(maxlen=100)
last_water_time = 0
sim_time = 0

# ==================== 硬件控制 ====================
if REAL_HARDWARE:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_PIN, GPIO.OUT, initial=GPIO.HIGH)  # HIGH=关闭（低电平触发继电器）
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1350000


def read_mcp3008(channel):
    """读取MCP3008 ADC值（0-1023）"""
    if REAL_HARDWARE:
        adc = spi.xfer2([1, (8 + channel) << 4, 0])
        return ((adc[1] & 3) << 8) + adc[2]
    else:
        t = sim_time * 0.03
        if channel == SOIL_CHANNEL:
            # 模拟土壤湿度：随时间缓慢变干，浇水后变湿
            base = 400 + 200 * math.sin(t * 0.1)
            return int(base + random.uniform(-20, 20))
        else:
            # 模拟光照：白天亮夜晚暗
            base = 500 + 400 * math.sin(t * 0.05)
            return int(max(0, min(1023, base + random.uniform(-30, 30))))


def soil_raw_to_percent(raw):
    """将ADC原始值转换为湿度百分比（值越小越湿）"""
    # 假设：0=完全浸水(100%), 1023=完全干燥(0%)
    percent = (1023 - raw) / 1023 * 100
    return round(max(0, min(100, percent)), 1)


def light_raw_to_percent(raw):
    """将ADC原始值转换为光照百分比"""
    return round(raw / 1023 * 100, 1)


def start_pump(duration=WATER_DURATION):
    """启动水泵"""
    global last_water_time
    if plant_data['pump_running']:
        return False, "水泵已在运行中"

    plant_data['pump_running'] = True
    last_water_time = time.time()

    if REAL_HARDWARE:
        GPIO.output(PUMP_PIN, GPIO.LOW)  # 低电平触发继电器

    # 记录浇水历史
    water_history.appendleft({
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'duration': duration,
        'trigger': '手动' if not plant_data['auto_water'] else '自动',
        'soil_before': plant_data['soil_moisture']
    })

    print(f"💧 水泵启动，持续 {duration} 秒")

    def stop_after():
        time.sleep(duration)
        if REAL_HARDWARE:
            GPIO.output(PUMP_PIN, GPIO.HIGH)
        plant_data['pump_running'] = False
        print("💧 水泵停止")

    threading.Thread(target=stop_after, daemon=True).start()
    return True, f"水泵已启动，将运行 {duration} 秒"


def stop_pump():
    """停止水泵"""
    if REAL_HARDWARE:
        GPIO.output(PUMP_PIN, GPIO.HIGH)
    plant_data['pump_running'] = False
    return True, "水泵已停止"


# ==================== 数据采集线程 ====================
def data_collection_thread():
    global sim_time
    while True:
        try:
            sim_time += 1
            soil_raw = read_mcp3008(SOIL_CHANNEL)
            light_raw = read_mcp3008(LIGHT_CHANNEL)
            temp, humi = None, None

            if REAL_HARDWARE:
                sensor = Adafruit_DHT.DHT11
                humi, temp = Adafruit_DHT.read_retry(sensor, DHT_PIN)
            else:
                t = sim_time * 0.05
                temp = round(22 + 3 * math.sin(t) + random.uniform(-0.3, 0.3), 1)
                humi = round(60 + 10 * math.cos(t * 0.7) + random.uniform(-1, 1), 1)

            soil_pct = soil_raw_to_percent(soil_raw)
            light_pct = light_raw_to_percent(light_raw)

            plant_data['soil_moisture'] = soil_pct
            plant_data['soil_raw'] = soil_raw
            plant_data['temperature'] = temp or 0
            plant_data['humidity'] = humi or 0
            plant_data['light_level'] = light_pct
            plant_data['timestamp'] = datetime.now().strftime('%H:%M:%S')

            # 判断植物状态
            if soil_pct < 20:
                plant_data['status'] = '⚠ 严重缺水！'
                plant_data['status_color'] = 'red'
            elif soil_pct < 40:
                plant_data['status'] = '💧 需要浇水'
                plant_data['status_color'] = 'orange'
            elif soil_pct > 85:
                plant_data['status'] = '🌊 水分过多'
                plant_data['status_color'] = 'blue'
            else:
                plant_data['status'] = '✅ 状态良好'
                plant_data['status_color'] = 'green'

            # 自动浇水逻辑
            now = time.time()
            if (plant_data['auto_water'] and
                    soil_pct < (soil_raw_to_percent(SOIL_DRY_THRESHOLD)) and
                    not plant_data['pump_running'] and
                    (now - last_water_time) > WATER_COOLDOWN):
                print(f"🤖 自动浇水触发：土壤湿度 {soil_pct}%")
                start_pump(WATER_DURATION)

            # 记录历史
            ts = datetime.now().strftime('%H:%M:%S')
            time_history.append(ts)
            soil_history.append(soil_pct)
            temp_history.append(temp or 0)

            print(f"[{ts}] 土壤:{soil_pct}% 温度:{temp}°C 湿度:{humi}% 光照:{light_pct}%")

        except Exception as e:
            print(f"采集错误: {e}")

        time.sleep(SAMPLE_INTERVAL)


# ==================== Flask Web服务器 ====================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌱 智能植物养护系统</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0d2b0d 0%, #1a3a1a 50%, #0d3320 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        header {
            background: rgba(0,0,0,0.3);
            padding: 15px 20px;
            text-align: center;
            border-bottom: 1px solid rgba(76,175,80,0.3);
        }
        header h1 { font-size: 1.8em; color: #81c784; }
        header p { color: #a5d6a7; font-size: 0.9em; margin-top: 4px; }
        .container { max-width: 1100px; margin: 0 auto; padding: 20px; }

        /* 植物状态大卡片 */
        .plant-status {
            background: rgba(0,0,0,0.3);
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            margin-bottom: 20px;
            border: 2px solid rgba(76,175,80,0.3);
        }
        .plant-emoji { font-size: 5em; margin-bottom: 10px; }
        .plant-status-text { font-size: 1.5em; font-weight: bold; margin-bottom: 5px; }
        .plant-status-text.green { color: #81c784; }
        .plant-status-text.orange { color: #ffb74d; }
        .plant-status-text.red { color: #ef9a9a; animation: pulse 1s infinite; }
        .plant-status-text.blue { color: #90caf9; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }

        /* 数据卡片 */
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .card {
            background: rgba(0,0,0,0.3);
            border-radius: 14px;
            padding: 18px;
            text-align: center;
            border: 1px solid rgba(76,175,80,0.2);
        }
        .card .icon { font-size: 2em; margin-bottom: 6px; }
        .card .label { font-size: 0.8em; color: #a5d6a7; margin-bottom: 4px; }
        .card .value { font-size: 1.8em; font-weight: bold; color: #c8e6c9; }
        .card .unit { font-size: 0.85em; color: #81c784; }

        /* 进度条 */
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            margin-top: 8px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        .soil-fill { background: linear-gradient(90deg, #8d6e63, #4caf50); }
        .light-fill { background: linear-gradient(90deg, #ffd54f, #ff8f00); }
        .humi-fill { background: linear-gradient(90deg, #42a5f5, #1565c0); }

        /* 控制面板 */
        .control-panel {
            background: rgba(0,0,0,0.3);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(76,175,80,0.2);
        }
        .control-panel h3 { color: #81c784; margin-bottom: 15px; }
        .controls { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.2s;
        }
        .btn:hover { transform: scale(1.05); }
        .btn-water { background: #1565c0; color: white; }
        .btn-water:hover { background: #1976d2; }
        .btn-stop { background: #c62828; color: white; }
        .btn-stop:hover { background: #d32f2f; }
        .btn-auto { background: #2e7d32; color: white; }
        .btn-auto.off { background: #4a4a4a; }
        .pump-status {
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: bold;
        }
        .pump-on { background: rgba(33,150,243,0.3); color: #90caf9; border: 1px solid #1565c0; }
        .pump-off { background: rgba(255,255,255,0.05); color: #78909c; border: 1px solid #37474f; }

        /* 图表 */
        .charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .chart-card {
            background: rgba(0,0,0,0.3);
            border-radius: 14px;
            padding: 18px;
            border: 1px solid rgba(76,175,80,0.2);
        }
        .chart-card h3 { color: #a5d6a7; margin-bottom: 12px; font-size: 0.95em; }
        .chart-card canvas { max-height: 180px; }

        /* 浇水历史 */
        .history-card {
            background: rgba(0,0,0,0.3);
            border-radius: 14px;
            padding: 18px;
            border: 1px solid rgba(76,175,80,0.2);
            margin-bottom: 20px;
        }
        .history-card h3 { color: #a5d6a7; margin-bottom: 12px; }
        .history-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 6px;
            background: rgba(76,175,80,0.1);
            border-left: 3px solid #4caf50;
            font-size: 0.9em;
        }
        .history-item .trigger { color: #a5d6a7; }
        .no-history { color: #546e7a; font-style: italic; }

        .status-bar { text-align: center; color: #546e7a; font-size: 0.85em; padding: 10px; }
    </style>
</head>
<body>
    <header>
        <h1>🌱 智能植物养护系统</h1>
        <p>Raspberry Pi IoT 植物监测与自动浇水控制台</p>
    </header>
    <div class="container">
        <!-- 植物状态 -->
        <div class="plant-status">
            <div class="plant-emoji" id="plant-emoji">🌿</div>
            <div class="plant-status-text green" id="plant-status-text">加载中...</div>
            <div style="color:#78909c;font-size:0.9em;margin-top:5px" id="plant-ts">--</div>
        </div>

        <!-- 数据卡片 -->
        <div class="cards">
            <div class="card">
                <div class="icon">🌱</div>
                <div class="label">土壤湿度</div>
                <div class="value" id="val-soil">--</div>
                <div class="unit">%</div>
                <div class="progress-bar"><div class="progress-fill soil-fill" id="bar-soil" style="width:0%"></div></div>
            </div>
            <div class="card">
                <div class="icon">🌡️</div>
                <div class="label">环境温度</div>
                <div class="value" id="val-temp">--</div>
                <div class="unit">°C</div>
            </div>
            <div class="card">
                <div class="icon">💧</div>
                <div class="label">空气湿度</div>
                <div class="value" id="val-humi">--</div>
                <div class="unit">%</div>
                <div class="progress-bar"><div class="progress-fill humi-fill" id="bar-humi" style="width:0%"></div></div>
            </div>
            <div class="card">
                <div class="icon">☀️</div>
                <div class="label">光照强度</div>
                <div class="value" id="val-light">--</div>
                <div class="unit">%</div>
                <div class="progress-bar"><div class="progress-fill light-fill" id="bar-light" style="width:0%"></div></div>
            </div>
        </div>

        <!-- 控制面板 -->
        <div class="control-panel">
            <h3>🎮 浇水控制</h3>
            <div class="controls">
                <button class="btn btn-water" onclick="manualWater()">💧 手动浇水 (5秒)</button>
                <button class="btn btn-stop" onclick="stopWater()">⏹ 停止水泵</button>
                <button class="btn btn-auto" id="btn-auto" onclick="toggleAuto()">🤖 自动浇水：开启</button>
                <div class="pump-status pump-off" id="pump-status">水泵：待机</div>
            </div>
        </div>

        <!-- 图表 -->
        <div class="charts">
            <div class="chart-card">
                <h3>🌱 土壤湿度趋势</h3>
                <canvas id="chart-soil"></canvas>
            </div>
            <div class="chart-card">
                <h3>🌡️ 温度趋势</h3>
                <canvas id="chart-temp"></canvas>
            </div>
        </div>

        <!-- 浇水历史 -->
        <div class="history-card">
            <h3>💧 浇水历史记录</h3>
            <div id="water-history"><p class="no-history">暂无浇水记录</p></div>
        </div>

        <div class="status-bar">最后更新：<span id="last-update">--</span> | 智能植物养护系统 v1.0</div>
    </div>

    <script>
        const plantEmojis = { green: '🌿', orange: '🥀', red: '🏜️', blue: '🌊' };

        const chartOpts = {
            type: 'line',
            options: {
                responsive: true, animation: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#78909c', maxTicksLimit: 8 }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#78909c' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        };

        const chartSoil = new Chart(document.getElementById('chart-soil'), {
            ...chartOpts,
            data: { labels: [], datasets: [{ label: '土壤湿度(%)', data: [], borderColor: '#4caf50', backgroundColor: '#4caf5022', fill: true, tension: 0.4, pointRadius: 2 }] }
        });
        const chartTemp = new Chart(document.getElementById('chart-temp'), {
            ...chartOpts,
            data: { labels: [], datasets: [{ label: '温度(°C)', data: [], borderColor: '#ff7043', backgroundColor: '#ff704322', fill: true, tension: 0.4, pointRadius: 2 }] }
        });

        async function fetchData() {
            const res = await fetch('/api/plant_data');
            const d = await res.json();

            document.getElementById('val-soil').textContent = d.soil_moisture.toFixed(1);
            document.getElementById('val-temp').textContent = d.temperature.toFixed(1);
            document.getElementById('val-humi').textContent = d.humidity.toFixed(1);
            document.getElementById('val-light').textContent = d.light_level.toFixed(1);
            document.getElementById('bar-soil').style.width = d.soil_moisture + '%';
            document.getElementById('bar-humi').style.width = d.humidity + '%';
            document.getElementById('bar-light').style.width = d.light_level + '%';
            document.getElementById('plant-ts').textContent = '更新时间：' + d.timestamp;

            const statusEl = document.getElementById('plant-status-text');
            statusEl.textContent = d.status;
            statusEl.className = 'plant-status-text ' + d.status_color;
            document.getElementById('plant-emoji').textContent = plantEmojis[d.status_color] || '🌿';

            const pumpEl = document.getElementById('pump-status');
            if (d.pump_running) {
                pumpEl.textContent = '水泵：运行中 💧';
                pumpEl.className = 'pump-status pump-on';
            } else {
                pumpEl.textContent = '水泵：待机';
                pumpEl.className = 'pump-status pump-off';
            }

            const autoBtn = document.getElementById('btn-auto');
            if (d.auto_water) {
                autoBtn.textContent = '🤖 自动浇水：开启';
                autoBtn.className = 'btn btn-auto';
            } else {
                autoBtn.textContent = '🤖 自动浇水：关闭';
                autoBtn.className = 'btn btn-auto off';
            }

            document.getElementById('last-update').textContent = d.timestamp;
        }

        async function fetchHistory() {
            const res = await fetch('/api/plant_history');
            const h = await res.json();
            chartSoil.data.labels = h.timestamps;
            chartSoil.data.datasets[0].data = h.soil;
            chartTemp.data.labels = h.timestamps;
            chartTemp.data.datasets[0].data = h.temperature;
            chartSoil.update(); chartTemp.update();
        }

        async function fetchWaterLog() {
            const res = await fetch('/api/water_history');
            const logs = await res.json();
            const div = document.getElementById('water-history');
            if (!logs.length) { div.innerHTML = '<p class="no-history">暂无浇水记录</p>'; return; }
            div.innerHTML = logs.map(l =>
                `<div class="history-item">
                    <span>${l.time}</span>
                    <span>持续 ${l.duration}秒</span>
                    <span>浇水前湿度 ${l.soil_before}%</span>
                    <span class="trigger">${l.trigger}</span>
                </div>`
            ).join('');
        }

        async function manualWater() {
            const res = await fetch('/api/water/start', { method: 'POST' });
            const d = await res.json();
            alert(d.message);
        }

        async function stopWater() {
            const res = await fetch('/api/water/stop', { method: 'POST' });
            const d = await res.json();
            alert(d.message);
        }

        async function toggleAuto() {
            const res = await fetch('/api/auto_water/toggle', { method: 'POST' });
            await fetchData();
        }

        fetchData(); fetchHistory(); fetchWaterLog();
        setInterval(fetchData, 5000);
        setInterval(fetchHistory, 10000);
        setInterval(fetchWaterLog, 15000);
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template('plant_care_web.html')


@app.route('/api/plant_data')
def api_plant_data():
    return jsonify(plant_data)


@app.route('/api/plant_history')
def api_plant_history():
    return jsonify({
        'timestamps': list(time_history),
        'soil': list(soil_history),
        'temperature': list(temp_history),
    })


@app.route('/api/water_history')
def api_water_history():
    return jsonify(list(water_history))


@app.route('/api/water/start', methods=['POST'])
def api_water_start():
    ok, msg = start_pump(WATER_DURATION)
    return jsonify({'success': ok, 'message': msg})


@app.route('/api/water/stop', methods=['POST'])
def api_water_stop():
    ok, msg = stop_pump()
    return jsonify({'success': ok, 'message': msg})


@app.route('/api/auto_water/toggle', methods=['POST'])
def api_auto_toggle():
    plant_data['auto_water'] = not plant_data['auto_water']
    state = '开启' if plant_data['auto_water'] else '关闭'
    return jsonify({'auto_water': plant_data['auto_water'], 'message': f'自动浇水已{state}'})


# ==================== 主程序 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("🌱 智能植物养护系统")
    print("=" * 50)

    t = threading.Thread(target=data_collection_thread, daemon=True)
    t.start()
    time.sleep(1)

    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = '127.0.0.1'

    print(f"🌐 Web控制台：http://{ip}:5001")
    print("按 Ctrl+C 停止")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5001, debug=False)
