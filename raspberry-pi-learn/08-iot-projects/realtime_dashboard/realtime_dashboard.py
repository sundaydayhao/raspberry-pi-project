#!/usr/bin/env python3
"""
实时多传感器综合仪表盘（WebSocket版）
Real-time Multi-Sensor Dashboard with WebSocket

功能：
- 整合多路传感器数据（温湿度、超声波、光照、加速度）
- 使用 Flask-SocketIO 实现 WebSocket 实时推送（无需轮询）
- 精美的仪表盘界面，支持PC和手机
- 实时折线图（Chart.js）
- 数据导出为CSV

硬件连接：
- DHT11: GPIO4（温湿度）
- HC-SR04: TRIG=GPIO23, ECHO=GPIO24（超声波测距）
- 光敏电阻: MCP3008 CH0（光照）
- MPU6050: I2C（加速度/陀螺仪）

安装依赖：
  pip3 install flask flask-socketio eventlet

访问地址：http://<树莓派IP>:5002
"""

import time
import math
import threading
from datetime import datetime
from collections import deque

try:
    from flask import Flask, render_template
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("请安装: pip3 install flask flask-socketio eventlet")
    exit(1)

try:
    import RPi.GPIO as GPIO
    import Adafruit_DHT
    REAL_HARDWARE = True
    print("✓ 硬件模式")
except ImportError:
    REAL_HARDWARE = False
    import random
    print("⚠ 模拟模式")

# ==================== 配置 ====================
DHT_PIN = 4
TRIG_PIN = 23
ECHO_PIN = 24
SAMPLE_INTERVAL = 1.0   # 采集间隔（秒）
MAX_HISTORY = 60        # 图表显示最近60个点

# ==================== 全局数据 ====================
latest_data = {}
history = {
    'time': deque(maxlen=MAX_HISTORY),
    'temperature': deque(maxlen=MAX_HISTORY),
    'humidity': deque(maxlen=MAX_HISTORY),
    'distance': deque(maxlen=MAX_HISTORY),
    'light': deque(maxlen=MAX_HISTORY),
    'accel_x': deque(maxlen=MAX_HISTORY),
    'accel_y': deque(maxlen=MAX_HISTORY),
    'accel_z': deque(maxlen=MAX_HISTORY),
}
sim_t = 0

# ==================== 传感器读取 ====================
def read_all_sensors():
    """读取所有传感器"""
    global sim_t
    sim_t += 1
    t = sim_t * 0.1

    if REAL_HARDWARE:
        # DHT11
        humi, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, DHT_PIN)
        temp = temp or 0.0
        humi = humi or 0.0

        # 超声波
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIG_PIN, GPIO.OUT)
        GPIO.setup(ECHO_PIN, GPIO.IN)
        GPIO.output(TRIG_PIN, False)
        time.sleep(0.05)
        GPIO.output(TRIG_PIN, True)
        time.sleep(0.00001)
        GPIO.output(TRIG_PIN, False)
        pulse_start = time.time()
        while GPIO.input(ECHO_PIN) == 0:
            pulse_start = time.time()
        pulse_end = time.time()
        while GPIO.input(ECHO_PIN) == 1:
            pulse_end = time.time()
        distance = round((pulse_end - pulse_start) * 17150, 1)

        light = 50.0  # 需要ADC
        ax, ay, az = 0.0, 0.0, 1.0  # 需要MPU6050
    else:
        # 模拟数据
        temp = round(25 + 5 * math.sin(t * 0.3) + random.uniform(-0.3, 0.3), 1)
        humi = round(60 + 15 * math.cos(t * 0.2) + random.uniform(-1, 1), 1)
        distance = round(max(2, 50 + 30 * math.sin(t * 0.5) + random.uniform(-2, 2)), 1)
        light = round(max(0, min(100, 60 + 35 * math.sin(t * 0.08) + random.uniform(-3, 3))), 1)
        ax = round(math.sin(t * 0.4) * 0.3 + random.uniform(-0.05, 0.05), 3)
        ay = round(math.cos(t * 0.3) * 0.2 + random.uniform(-0.05, 0.05), 3)
        az = round(1.0 + math.sin(t * 0.1) * 0.05 + random.uniform(-0.02, 0.02), 3)

    ts = datetime.now().strftime('%H:%M:%S')
    return {
        'time': ts,
        'temperature': temp,
        'humidity': humi,
        'distance': distance,
        'light': light,
        'accel_x': ax,
        'accel_y': ay,
        'accel_z': az,
        'heat_index': round(temp + (humi - 40) * 0.1, 1) if temp > 27 else temp,
        'comfort': get_comfort(temp, humi),
    }


def get_comfort(temp, humi):
    if 20 <= temp <= 26 and 40 <= humi <= 65:
        return {'text': '😊 舒适', 'color': '#4caf50'}
    elif temp > 30 and humi > 70:
        return {'text': '🥵 闷热', 'color': '#f44336'}
    elif temp < 15:
        return {'text': '🥶 寒冷', 'color': '#2196f3'}
    elif humi < 30:
        return {'text': '🏜️ 干燥', 'color': '#ff9800'}
    else:
        return {'text': '😐 一般', 'color': '#9e9e9e'}


# ==================== Flask + SocketIO ====================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'rpi-dashboard-2024'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 实时传感器仪表盘</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        :root {
            --bg: #0a0e1a;
            --card: #111827;
            --border: rgba(255,255,255,0.08);
            --text: #e2e8f0;
            --muted: #64748b;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

        /* 顶部导航 */
        nav {
            background: rgba(17,24,39,0.95);
            backdrop-filter: blur(12px);
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            position: sticky; top: 0; z-index: 100;
        }
        nav h1 { font-size: 1.2em; color: #60a5fa; display: flex; align-items: center; gap: 8px; }
        .conn-status { display: flex; align-items: center; gap: 6px; font-size: 0.85em; }
        .conn-dot { width: 8px; height: 8px; border-radius: 50%; background: #ef4444; }
        .conn-dot.connected { background: #22c55e; animation: blink 2s infinite; }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }

        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }

        /* 主要指标卡片 */
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .metric-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
        }
        .metric-card.temp::before { background: linear-gradient(90deg, #f97316, #ef4444); }
        .metric-card.humi::before { background: linear-gradient(90deg, #38bdf8, #3b82f6); }
        .metric-card.dist::before { background: linear-gradient(90deg, #a78bfa, #8b5cf6); }
        .metric-card.light::before { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
        .metric-card.accel::before { background: linear-gradient(90deg, #34d399, #10b981); }
        .metric-card.comfort::before { background: linear-gradient(90deg, #f472b6, #ec4899); }

        .metric-icon { font-size: 1.8em; margin-bottom: 6px; }
        .metric-label { font-size: 0.75em; color: var(--muted); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-value { font-size: 1.9em; font-weight: 700; line-height: 1; }
        .metric-unit { font-size: 0.75em; color: var(--muted); margin-top: 3px; }
        .metric-card.temp .metric-value { color: #fb923c; }
        .metric-card.humi .metric-value { color: #60a5fa; }
        .metric-card.dist .metric-value { color: #a78bfa; }
        .metric-card.light .metric-value { color: #fbbf24; }
        .metric-card.accel .metric-value { font-size: 1.1em; color: #34d399; }
        .metric-card.comfort .metric-value { font-size: 1.1em; }

        /* 图表网格 */
        .charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 20px; }
        .chart-panel {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 18px;
        }
        .chart-panel h3 { font-size: 0.9em; color: #94a3b8; margin-bottom: 14px; display: flex; align-items: center; gap: 6px; }
        .chart-panel canvas { max-height: 200px; }

        /* 加速度仪表 */
        .accel-panel {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 20px;
        }
        .accel-panel h3 { font-size: 0.9em; color: #94a3b8; margin-bottom: 14px; }
        .accel-bars { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        .accel-bar-item { text-align: center; }
        .accel-bar-label { font-size: 0.8em; color: var(--muted); margin-bottom: 6px; }
        .accel-bar-track {
            height: 120px;
            background: rgba(255,255,255,0.05);
            border-radius: 6px;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: flex-end;
        }
        .accel-bar-fill {
            width: 100%;
            border-radius: 6px;
            transition: height 0.3s ease;
        }
        .ax-fill { background: linear-gradient(0deg, #ef4444, #f97316); }
        .ay-fill { background: linear-gradient(0deg, #3b82f6, #38bdf8); }
        .az-fill { background: linear-gradient(0deg, #22c55e, #84cc16); }
        .accel-bar-val { font-size: 0.85em; color: var(--text); margin-top: 4px; font-weight: bold; }

        /* 数据导出 */
        .toolbar {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 8px 18px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9em;
            font-weight: 600;
            transition: all 0.2s;
        }
        .btn-export { background: #1d4ed8; color: white; }
        .btn-export:hover { background: #2563eb; }
        .btn-clear { background: #374151; color: #d1d5db; }
        .btn-clear:hover { background: #4b5563; }
        #data-count { color: var(--muted); font-size: 0.85em; align-self: center; }

        /* 状态栏 */
        footer { text-align: center; color: var(--muted); font-size: 0.8em; padding: 15px; border-top: 1px solid var(--border); margin-top: 10px; }

        @media (max-width: 600px) {
            .charts-grid { grid-template-columns: 1fr; }
            .metric-value { font-size: 1.5em; }
        }
    </style>
</head>
<body>
    <nav>
        <h1>📊 实时传感器仪表盘</h1>
        <div class="conn-status">
            <div class="conn-dot" id="conn-dot"></div>
            <span id="conn-text">连接中...</span>
        </div>
    </nav>

    <div class="container">
        <!-- 工具栏 -->
        <div class="toolbar">
            <button class="btn btn-export" onclick="exportCSV()">📥 导出CSV</button>
            <button class="btn btn-clear" onclick="clearHistory()">🗑 清空历史</button>
            <span id="data-count">已采集: 0 条</span>
        </div>

        <!-- 指标卡片 -->
        <div class="metrics">
            <div class="metric-card temp">
                <div class="metric-icon">🌡️</div>
                <div class="metric-label">温度</div>
                <div class="metric-value" id="m-temp">--</div>
                <div class="metric-unit">°C</div>
            </div>
            <div class="metric-card humi">
                <div class="metric-icon">💧</div>
                <div class="metric-label">湿度</div>
                <div class="metric-value" id="m-humi">--</div>
                <div class="metric-unit">%RH</div>
            </div>
            <div class="metric-card dist">
                <div class="metric-icon">📏</div>
                <div class="metric-label">距离</div>
                <div class="metric-value" id="m-dist">--</div>
                <div class="metric-unit">cm</div>
            </div>
            <div class="metric-card light">
                <div class="metric-icon">☀️</div>
                <div class="metric-label">光照</div>
                <div class="metric-value" id="m-light">--</div>
                <div class="metric-unit">%</div>
            </div>
            <div class="metric-card accel">
                <div class="metric-icon">📐</div>
                <div class="metric-label">加速度 (g)</div>
                <div class="metric-value" id="m-accel">--</div>
                <div class="metric-unit">X / Y / Z</div>
            </div>
            <div class="metric-card comfort">
                <div class="metric-icon">🌈</div>
                <div class="metric-label">舒适度</div>
                <div class="metric-value" id="m-comfort" style="font-size:1em">--</div>
                <div class="metric-unit">综合评估</div>
            </div>
        </div>

        <!-- 图表 -->
        <div class="charts-grid">
            <div class="chart-panel">
                <h3>🌡️ 温度 & 湿度实时曲线</h3>
                <canvas id="chart-th"></canvas>
            </div>
            <div class="chart-panel">
                <h3>📏 超声波距离实时曲线</h3>
                <canvas id="chart-dist"></canvas>
            </div>
            <div class="chart-panel">
                <h3>☀️ 光照强度实时曲线</h3>
                <canvas id="chart-light"></canvas>
            </div>
            <div class="chart-panel">
                <h3>📐 加速度三轴实时曲线</h3>
                <canvas id="chart-accel"></canvas>
            </div>
        </div>

        <!-- 加速度可视化 -->
        <div class="accel-panel">
            <h3>📐 加速度实时可视化（单位：g）</h3>
            <div class="accel-bars">
                <div class="accel-bar-item">
                    <div class="accel-bar-label">X 轴</div>
                    <div class="accel-bar-track">
                        <div class="accel-bar-fill ax-fill" id="bar-ax" style="height:50%"></div>
                    </div>
                    <div class="accel-bar-val" id="val-ax">0.000</div>
                </div>
                <div class="accel-bar-item">
                    <div class="accel-bar-label">Y 轴</div>
                    <div class="accel-bar-track">
                        <div class="accel-bar-fill ay-fill" id="bar-ay" style="height:50%"></div>
                    </div>
                    <div class="accel-bar-val" id="val-ay">0.000</div>
                </div>
                <div class="accel-bar-item">
                    <div class="accel-bar-label">Z 轴</div>
                    <div class="accel-bar-track">
                        <div class="accel-bar-fill az-fill" id="bar-az" style="height:50%"></div>
                    </div>
                    <div class="accel-bar-val" id="val-az">1.000</div>
                </div>
            </div>
        </div>
    </div>

    <footer>Raspberry Pi 实时传感器仪表盘 v1.0 | WebSocket 实时推送 | 采集间隔: 1秒</footer>

    <script>
        // ===== 图表初始化 =====
        const chartOpts = (yLabel, min, max) => ({
            type: 'line',
            options: {
                responsive: true, animation: false,
                plugins: { legend: { labels: { color: '#94a3b8', boxWidth: 12 } } },
                scales: {
                    x: { ticks: { color: '#64748b', maxTicksLimit: 10 }, grid: { color: 'rgba(255,255,255,0.04)' } },
                    y: { min, max, ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' }, title: { display: true, text: yLabel, color: '#64748b' } }
                }
            }
        });

        const chartTH = new Chart(document.getElementById('chart-th'), {
            ...chartOpts('值', 0, 100),
            data: { labels: [], datasets: [
                { label: '温度(°C)', data: [], borderColor: '#f97316', backgroundColor: '#f9731622', fill: true, tension: 0.4, pointRadius: 0 },
                { label: '湿度(%)', data: [], borderColor: '#60a5fa', backgroundColor: '#60a5fa22', fill: true, tension: 0.4, pointRadius: 0 }
            ]}
        });

        const chartDist = new Chart(document.getElementById('chart-dist'), {
            ...chartOpts('cm', 0, 200),
            data: { labels: [], datasets: [
                { label: '距离(cm)', data: [], borderColor: '#a78bfa', backgroundColor: '#a78bfa22', fill: true, tension: 0.4, pointRadius: 0 }
            ]}
        });

        const chartLight = new Chart(document.getElementById('chart-light'), {
            ...chartOpts('%', 0, 100),
            data: { labels: [], datasets: [
                { label: '光照(%)', data: [], borderColor: '#fbbf24', backgroundColor: '#fbbf2422', fill: true, tension: 0.4, pointRadius: 0 }
            ]}
        });

        const chartAccel = new Chart(document.getElementById('chart-accel'), {
            ...chartOpts('g', -2, 2),
            data: { labels: [], datasets: [
                { label: 'X轴', data: [], borderColor: '#ef4444', tension: 0.4, pointRadius: 0 },
                { label: 'Y轴', data: [], borderColor: '#3b82f6', tension: 0.4, pointRadius: 0 },
                { label: 'Z轴', data: [], borderColor: '#22c55e', tension: 0.4, pointRadius: 0 }
            ]}
        });

        // ===== 数据存储（用于CSV导出）=====
        const csvData = [];
        let dataCount = 0;

        // ===== WebSocket 连接 =====
        const socket = io();

        socket.on('connect', () => {
            document.getElementById('conn-dot').className = 'conn-dot connected';
            document.getElementById('conn-text').textContent = '已连接 (WebSocket)';
        });

        socket.on('disconnect', () => {
            document.getElementById('conn-dot').className = 'conn-dot';
            document.getElementById('conn-text').textContent = '已断开';
        });

        socket.on('sensor_data', (d) => {
            dataCount++;
            document.getElementById('data-count').textContent = `已采集: ${dataCount} 条`;

            // 更新指标卡片
            document.getElementById('m-temp').textContent = d.temperature.toFixed(1);
            document.getElementById('m-humi').textContent = d.humidity.toFixed(1);
            document.getElementById('m-dist').textContent = d.distance.toFixed(1);
            document.getElementById('m-light').textContent = d.light.toFixed(1);
            document.getElementById('m-accel').textContent = `${d.accel_x.toFixed(2)} / ${d.accel_y.toFixed(2)} / ${d.accel_z.toFixed(2)}`;
            const comfortEl = document.getElementById('m-comfort');
            comfortEl.textContent = d.comfort.text;
            comfortEl.style.color = d.comfort.color;

            // 更新图表
            const MAX_POINTS = 60;
            function addPoint(chart, label, ...values) {
                chart.data.labels.push(label);
                values.forEach((v, i) => chart.data.datasets[i].data.push(v));
                if (chart.data.labels.length > MAX_POINTS) {
                    chart.data.labels.shift();
                    chart.data.datasets.forEach(ds => ds.data.shift());
                }
                chart.update('none');
            }

            addPoint(chartTH, d.time, d.temperature, d.humidity);
            addPoint(chartDist, d.time, d.distance);
            addPoint(chartLight, d.time, d.light);
            addPoint(chartAccel, d.time, d.accel_x, d.accel_y, d.accel_z);

            // 更新加速度条
            const toBarH = v => Math.max(5, Math.min(95, (v + 2) / 4 * 100));
            document.getElementById('bar-ax').style.height = toBarH(d.accel_x) + '%';
            document.getElementById('bar-ay').style.height = toBarH(d.accel_y) + '%';
            document.getElementById('bar-az').style.height = toBarH(d.accel_z) + '%';
            document.getElementById('val-ax').textContent = d.accel_x.toFixed(3);
            document.getElementById('val-ay').textContent = d.accel_y.toFixed(3);
            document.getElementById('val-az').textContent = d.accel_z.toFixed(3);

            // 存储CSV数据
            csvData.push([d.time, d.temperature, d.humidity, d.distance, d.light, d.accel_x, d.accel_y, d.accel_z]);
            if (csvData.length > 1000) csvData.shift();
        });

        // ===== CSV导出 =====
        function exportCSV() {
            if (!csvData.length) { alert('暂无数据'); return; }
            const header = '时间,温度(°C),湿度(%),距离(cm),光照(%),加速度X,加速度Y,加速度Z';
            const rows = csvData.map(r => r.join(','));
            const blob = new Blob([header + '\\n' + rows.join('\\n')], { type: 'text/csv;charset=utf-8;' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `sensor_data_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.csv`;
            a.click();
        }

        function clearHistory() {
            [chartTH, chartDist, chartLight, chartAccel].forEach(c => {
                c.data.labels = [];
                c.data.datasets.forEach(ds => ds.data = []);
                c.update();
            });
            csvData.length = 0;
            dataCount = 0;
            document.getElementById('data-count').textContent = '已采集: 0 条';
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template('realtime_dashboard.html')


@socketio.on('connect')
def on_connect():
    print(f"客户端连接: {threading.current_thread().name}")


def sensor_broadcast_thread():
    """传感器数据广播线程"""
    while True:
        try:
            data = read_all_sensors()
            latest_data.update(data)
            socketio.emit('sensor_data', data)
        except Exception as e:
            print(f"广播错误: {e}")
        time.sleep(SAMPLE_INTERVAL)


# ==================== 主程序 ====================
if __name__ == '__main__':
    print("=" * 55)
    print("📊 实时多传感器综合仪表盘（WebSocket版）")
    print("=" * 55)
    print(f"采集间隔: {SAMPLE_INTERVAL}秒")
    print(f"图表显示: 最近{MAX_HISTORY}个数据点")
    print()

    # 启动广播线程
    t = threading.Thread(target=sensor_broadcast_thread, daemon=True)
    t.start()

    import socket as sock
    try:
        s = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = '127.0.0.1'

    print(f"🌐 仪表盘地址：http://{ip}:5002")
    print(f"   手机访问：确保与树莓派在同一WiFi")
    print("按 Ctrl+C 停止")
    print("=" * 55)

    socketio.run(app, host='0.0.0.0', port=5002, debug=False)