#!/usr/bin/env python3
"""
智能家居环境监测站
Smart Home Environment Monitor

功能：
- 采集温度、湿度（DHT11/DHT22）
- 采集气压（BMP280）
- 采集烟雾/气体浓度（MQ-2）
- 检测人体运动（PIR）
- 通过Flask Web服务器展示实时数据
- 支持PC和手机访问
- 数据历史记录和图表展示
- 超限报警提示

硬件连接：
- DHT11: GPIO4
- BMP280: I2C (SDA=GPIO2, SCL=GPIO3)
- MQ-2: GPIO17 (数字输出)
- PIR: GPIO27

访问地址：http://<树莓派IP>:5000
"""

import time
import json
import threading
from datetime import datetime, timedelta
from collections import deque
from flask import Flask, render_template, jsonify, Response

# 尝试导入传感器库，失败则使用模拟数据
try:
    import RPi.GPIO as GPIO
    import Adafruit_DHT
    import smbus2
    REAL_HARDWARE = True
    print("✓ 硬件模式：使用真实传感器")
except ImportError:
    REAL_HARDWARE = False
    import random
    import math
    print("⚠ 模拟模式：使用虚拟传感器数据（用于测试）")

# ==================== 配置 ====================
DHT_PIN = 4          # DHT11数据引脚
DHT_TYPE = 11        # 11=DHT11, 22=DHT22
MQ2_PIN = 17         # MQ-2数字输出引脚
PIR_PIN = 27         # PIR运动传感器引脚
BMP280_ADDR = 0x76   # BMP280 I2C地址

# 报警阈值
TEMP_MAX = 35.0      # 最高温度报警 °C
TEMP_MIN = 5.0       # 最低温度报警 °C
HUMIDITY_MAX = 80.0  # 最高湿度报警 %
CO2_ALARM = True     # MQ-2触发报警

# 数据采集间隔（秒）
SAMPLE_INTERVAL = 3

# 历史数据保存条数
MAX_HISTORY = 100

# ==================== 全局数据 ====================
sensor_data = {
    'temperature': 0.0,
    'humidity': 0.0,
    'pressure': 0.0,
    'gas_alarm': False,
    'motion': False,
    'timestamp': '',
    'alerts': []
}

# 历史数据队列
history = {
    'timestamps': deque(maxlen=MAX_HISTORY),
    'temperature': deque(maxlen=MAX_HISTORY),
    'humidity': deque(maxlen=MAX_HISTORY),
    'pressure': deque(maxlen=MAX_HISTORY),
}

motion_log = deque(maxlen=20)  # 运动事件日志
sim_time = 0  # 模拟时间计数器

# ==================== 传感器读取 ====================
def read_dht():
    """读取DHT11/DHT22温湿度"""
    if REAL_HARDWARE:
        sensor = Adafruit_DHT.DHT11 if DHT_TYPE == 11 else Adafruit_DHT.DHT22
        humidity, temperature = Adafruit_DHT.read_retry(sensor, DHT_PIN)
        return temperature, humidity
    else:
        # 模拟数据：温度在20-30°C波动，湿度在40-70%波动
        t = sim_time * 0.05
        temp = 25 + 5 * math.sin(t) + random.uniform(-0.5, 0.5)
        humi = 55 + 15 * math.cos(t * 0.7) + random.uniform(-1, 1)
        return round(temp, 1), round(max(0, min(100, humi)), 1)


def read_bmp280():
    """读取BMP280气压"""
    if REAL_HARDWARE:
        try:
            bus = smbus2.SMBus(1)
            # 简化读取，实际项目建议使用 adafruit-circuitpython-bmp280 库
            # 这里返回标准大气压作为示例
            return 1013.25
        except Exception:
            return None
    else:
        t = sim_time * 0.02
        return round(1013 + 5 * math.sin(t) + random.uniform(-0.5, 0.5), 1)


def read_mq2():
    """读取MQ-2气体传感器（数字输出：LOW=报警）"""
    if REAL_HARDWARE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MQ2_PIN, GPIO.IN)
        return GPIO.input(MQ2_PIN) == GPIO.LOW  # LOW表示检测到气体
    else:
        # 模拟：偶尔触发报警
        return random.random() < 0.05


def read_pir():
    """读取PIR运动传感器"""
    if REAL_HARDWARE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIR_PIN, GPIO.IN)
        return GPIO.input(PIR_PIN) == GPIO.HIGH
    else:
        return random.random() < 0.1


def check_alerts(temp, humi, gas_alarm):
    """检查报警条件"""
    alerts = []
    if temp is not None:
        if temp > TEMP_MAX:
            alerts.append({'type': 'danger', 'msg': f'⚠ 温度过高！当前 {temp}°C（阈值 {TEMP_MAX}°C）'})
        elif temp < TEMP_MIN:
            alerts.append({'type': 'warning', 'msg': f'⚠ 温度过低！当前 {temp}°C（阈值 {TEMP_MIN}°C）'})
    if humi is not None and humi > HUMIDITY_MAX:
        alerts.append({'type': 'warning', 'msg': f'💧 湿度过高！当前 {humi}%（阈值 {HUMIDITY_MAX}%）'})
    if gas_alarm:
        alerts.append({'type': 'danger', 'msg': '🔥 检测到烟雾/可燃气体！请立即检查！'})
    return alerts


# ==================== 数据采集线程 ====================
def data_collection_thread():
    """后台数据采集线程"""
    global sim_time
    if REAL_HARDWARE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MQ2_PIN, GPIO.IN)
        GPIO.setup(PIR_PIN, GPIO.IN)

    while True:
        try:
            sim_time += 1
            temp, humi = read_dht()
            pressure = read_bmp280()
            gas_alarm = read_mq2()
            motion = read_pir()
            now = datetime.now()
            ts = now.strftime('%H:%M:%S')

            # 更新全局数据
            sensor_data['temperature'] = temp if temp else 0.0
            sensor_data['humidity'] = humi if humi else 0.0
            sensor_data['pressure'] = pressure if pressure else 0.0
            sensor_data['gas_alarm'] = gas_alarm
            sensor_data['motion'] = motion
            sensor_data['timestamp'] = ts
            sensor_data['alerts'] = check_alerts(temp, humi, gas_alarm)

            # 记录历史
            history['timestamps'].append(ts)
            history['temperature'].append(temp if temp else 0)
            history['humidity'].append(humi if humi else 0)
            history['pressure'].append(pressure if pressure else 0)

            # 记录运动事件
            if motion:
                motion_log.appendleft({
                    'time': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'msg': '检测到人体活动'
                })

            print(f"[{ts}] 温度:{temp}°C 湿度:{humi}% 气压:{pressure}hPa "
                  f"气体报警:{'是' if gas_alarm else '否'} 运动:{'是' if motion else '否'}")

        except Exception as e:
            print(f"传感器读取错误: {e}")

        time.sleep(SAMPLE_INTERVAL)


# ==================== Flask Web服务器 ====================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏠 智能家居环境监测站</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        header {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        header h1 { font-size: 1.8em; color: #64b5f6; }
        header p { color: #90a4ae; font-size: 0.9em; margin-top: 4px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }

        /* 报警横幅 */
        .alerts { margin-bottom: 15px; }
        .alert {
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 8px;
            font-weight: bold;
            animation: pulse 1s infinite;
        }
        .alert.danger { background: rgba(244,67,54,0.3); border: 1px solid #f44336; color: #ff8a80; }
        .alert.warning { background: rgba(255,152,0,0.3); border: 1px solid #ff9800; color: #ffcc80; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.7} }

        /* 数据卡片 */
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .card {
            background: rgba(255,255,255,0.07);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.2s;
        }
        .card:hover { transform: translateY(-3px); }
        .card .icon { font-size: 2.5em; margin-bottom: 8px; }
        .card .label { font-size: 0.85em; color: #90a4ae; margin-bottom: 5px; }
        .card .value { font-size: 2em; font-weight: bold; }
        .card .unit { font-size: 0.9em; color: #90a4ae; }
        .card.temp .value { color: #ff7043; }
        .card.humi .value { color: #42a5f5; }
        .card.pres .value { color: #66bb6a; }
        .card.gas .value { color: #ef5350; }
        .card.motion .value { color: #ab47bc; }
        .card.status-ok { border-color: rgba(76,175,80,0.4); }
        .card.status-alarm { border-color: rgba(244,67,54,0.6); animation: pulse 1s infinite; }

        /* 图表区域 */
        .charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .chart-card {
            background: rgba(255,255,255,0.07);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .chart-card h3 { margin-bottom: 15px; color: #90caf9; font-size: 1em; }
        .chart-card canvas { max-height: 200px; }

        /* 运动日志 */
        .log-card {
            background: rgba(255,255,255,0.07);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 20px;
        }
        .log-card h3 { margin-bottom: 12px; color: #90caf9; }
        .log-item {
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 6px;
            background: rgba(171,71,188,0.15);
            border-left: 3px solid #ab47bc;
            font-size: 0.9em;
        }
        .log-item .time { color: #ce93d8; font-size: 0.85em; }
        .no-log { color: #546e7a; font-style: italic; }

        /* 状态栏 */
        .status-bar {
            text-align: center;
            color: #546e7a;
            font-size: 0.85em;
            padding: 10px;
        }
        #last-update { color: #78909c; }

        /* 响应式 */
        @media (max-width: 600px) {
            header h1 { font-size: 1.3em; }
            .card .value { font-size: 1.6em; }
        }
    </style>
</head>
<body>
    <header>
        <h1>🏠 智能家居环境监测站</h1>
        <p>Raspberry Pi IoT 实时环境监测 | 自动刷新间隔：3秒</p>
    </header>
    <div class="container">
        <!-- 报警区域 -->
        <div class="alerts" id="alerts"></div>

        <!-- 数据卡片 -->
        <div class="cards">
            <div class="card temp" id="card-temp">
                <div class="icon">🌡️</div>
                <div class="label">室内温度</div>
                <div class="value" id="val-temp">--</div>
                <div class="unit">°C</div>
            </div>
            <div class="card humi" id="card-humi">
                <div class="icon">💧</div>
                <div class="label">相对湿度</div>
                <div class="value" id="val-humi">--</div>
                <div class="unit">%RH</div>
            </div>
            <div class="card pres" id="card-pres">
                <div class="icon">🌬️</div>
                <div class="label">大气压强</div>
                <div class="value" id="val-pres">--</div>
                <div class="unit">hPa</div>
            </div>
            <div class="card gas status-ok" id="card-gas">
                <div class="icon">🔥</div>
                <div class="label">烟雾/气体</div>
                <div class="value" id="val-gas">正常</div>
                <div class="unit">MQ-2</div>
            </div>
            <div class="card motion" id="card-motion">
                <div class="icon">👤</div>
                <div class="label">人体感应</div>
                <div class="value" id="val-motion">无</div>
                <div class="unit">PIR</div>
            </div>
        </div>

        <!-- 图表 -->
        <div class="charts">
            <div class="chart-card">
                <h3>📈 温度趋势（近100次采样）</h3>
                <canvas id="chart-temp"></canvas>
            </div>
            <div class="chart-card">
                <h3>📈 湿度趋势（近100次采样）</h3>
                <canvas id="chart-humi"></canvas>
            </div>
            <div class="chart-card">
                <h3>📈 气压趋势（近100次采样）</h3>
                <canvas id="chart-pres"></canvas>
            </div>
        </div>

        <!-- 运动日志 -->
        <div class="log-card">
            <h3>👤 运动检测日志（最近20条）</h3>
            <div id="motion-log"><p class="no-log">暂无运动记录</p></div>
        </div>

        <div class="status-bar">
            最后更新：<span id="last-update">--</span> |
            树莓派 IoT 环境监测系统 v1.0
        </div>
    </div>

    <script>
        // 图表配置
        const chartDefaults = {
            type: 'line',
            options: {
                responsive: true,
                animation: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#78909c', maxTicksLimit: 8 }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#78909c' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        };

        function makeChart(id, color, label) {
            return new Chart(document.getElementById(id), {
                ...chartDefaults,
                data: {
                    labels: [],
                    datasets: [{
                        label: label,
                        data: [],
                        borderColor: color,
                        backgroundColor: color + '22',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 2
                    }]
                }
            });
        }

        const chartTemp = makeChart('chart-temp', '#ff7043', '温度(°C)');
        const chartHumi = makeChart('chart-humi', '#42a5f5', '湿度(%)');
        const chartPres = makeChart('chart-pres', '#66bb6a', '气压(hPa)');

        function updateCharts(history) {
            [chartTemp, chartHumi, chartPres].forEach(c => {
                c.data.labels = history.timestamps;
            });
            chartTemp.data.datasets[0].data = history.temperature;
            chartHumi.data.datasets[0].data = history.humidity;
            chartPres.data.datasets[0].data = history.pressure;
            [chartTemp, chartHumi, chartPres].forEach(c => c.update());
        }

        async function fetchData() {
            try {
                const res = await fetch('/api/data');
                const d = await res.json();

                // 更新卡片
                document.getElementById('val-temp').textContent = d.temperature.toFixed(1);
                document.getElementById('val-humi').textContent = d.humidity.toFixed(1);
                document.getElementById('val-pres').textContent = d.pressure.toFixed(1);

                const gasCard = document.getElementById('card-gas');
                const gasVal = document.getElementById('val-gas');
                if (d.gas_alarm) {
                    gasVal.textContent = '报警!';
                    gasCard.className = 'card gas status-alarm';
                } else {
                    gasVal.textContent = '正常';
                    gasCard.className = 'card gas status-ok';
                }

                const motionVal = document.getElementById('val-motion');
                motionVal.textContent = d.motion ? '检测到!' : '无';

                // 报警横幅
                const alertsDiv = document.getElementById('alerts');
                alertsDiv.innerHTML = d.alerts.map(a =>
                    `<div class="alert ${a.type}">${a.msg}</div>`
                ).join('');

                document.getElementById('last-update').textContent = d.timestamp;
            } catch(e) { console.error('数据获取失败:', e); }
        }

        async function fetchHistory() {
            try {
                const res = await fetch('/api/history');
                const h = await res.json();
                updateCharts(h);
            } catch(e) { console.error('历史数据获取失败:', e); }
        }

        async function fetchMotionLog() {
            try {
                const res = await fetch('/api/motion_log');
                const logs = await res.json();
                const div = document.getElementById('motion-log');
                if (logs.length === 0) {
                    div.innerHTML = '<p class="no-log">暂无运动记录</p>';
                } else {
                    div.innerHTML = logs.map(l =>
                        `<div class="log-item"><span class="time">${l.time}</span> — ${l.msg}</div>`
                    ).join('');
                }
            } catch(e) {}
        }

        // 定时刷新
        fetchData();
        fetchHistory();
        fetchMotionLog();
        setInterval(fetchData, 3000);
        setInterval(fetchHistory, 5000);
        setInterval(fetchMotionLog, 10000);
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template('smart_home_monitor.html')


@app.route('/api/data')
def api_data():
    return jsonify(sensor_data)


@app.route('/api/history')
def api_history():
    return jsonify({
        'timestamps': list(history['timestamps']),
        'temperature': list(history['temperature']),
        'humidity': list(history['humidity']),
        'pressure': list(history['pressure']),
    })


@app.route('/api/motion_log')
def api_motion_log():
    return jsonify(list(motion_log))


# ==================== 主程序 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("🏠 智能家居环境监测站")
    print("=" * 50)
    print(f"采集间隔: {SAMPLE_INTERVAL}秒")
    print(f"温度报警: >{TEMP_MAX}°C 或 <{TEMP_MIN}°C")
    print(f"湿度报警: >{HUMIDITY_MAX}%")
    print()

    # 启动数据采集线程
    t = threading.Thread(target=data_collection_thread, daemon=True)
    t.start()

    # 等待首次数据采集
    time.sleep(1)

    # 获取本机IP
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = '127.0.0.1'

    print(f"🌐 Web服务器启动中...")
    print(f"   本机访问: http://localhost:5000")
    print(f"   局域网访问: http://{ip}:5000")
    print(f"   手机访问: 确保手机与树莓派在同一WiFi网络")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=False)