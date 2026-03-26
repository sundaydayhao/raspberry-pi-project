#!/usr/bin/env python3
"""
智能安防监控系统 - Web报警中心
Smart Security Monitor with Web Alert Center

功能：
- PIR人体感应检测
- 超声波入侵检测（设定警戒距离）
- 摄像头抓拍（检测到入侵时自动拍照）
- 蜂鸣器报警
- Web报警中心：实时状态 + 报警日志 + 快照查看
- 布防/撤防控制
- 报警统计

硬件连接：
- PIR传感器: GPIO17
- 超声波: TRIG=GPIO23, ECHO=GPIO24
- 蜂鸣器: GPIO22（有源蜂鸣器）
- 摄像头: USB摄像头或Pi Camera

访问地址：http://<树莓派IP>:5003
"""

import time
import os
import math
import threading
import base64
from datetime import datetime
from collections import deque
from flask import Flask, render_template, jsonify, request, send_from_directory

try:
    import RPi.GPIO as GPIO
    REAL_HARDWARE = True
    print("✓ 硬件模式")
except ImportError:
    REAL_HARDWARE = False
    import random
    print("⚠ 模拟模式")

try:
    import cv2
    CAMERA_AVAILABLE = True
    print("✓ 摄像头可用")
except ImportError:
    CAMERA_AVAILABLE = False
    print("⚠ 摄像头不可用（pip3 install opencv-python）")

# ==================== 配置 ====================
PIR_PIN = 17
TRIG_PIN = 23
ECHO_PIN = 24
BUZZER_PIN = 22

ALERT_DISTANCE = 80     # 超声波警戒距离（cm），小于此值触发报警
ALARM_DURATION = 3      # 蜂鸣器报警时长（秒）
SNAPSHOT_DIR = 'snapshots'  # 快照保存目录
MAX_SNAPSHOTS = 20      # 最多保存快照数量
SAMPLE_INTERVAL = 0.5   # 采集间隔

# ==================== 全局状态 ====================
security_state = {
    'armed': True,          # 是否布防
    'alarm_active': False,  # 是否正在报警
    'pir_triggered': False,
    'distance': 999.0,
    'distance_alarm': False,
    'timestamp': '',
    'total_alarms': 0,
    'today_alarms': 0,
}

alarm_log = deque(maxlen=50)
snapshots = deque(maxlen=MAX_SNAPSHOTS)
distance_history = deque(maxlen=120)
time_history = deque(maxlen=120)
sim_t = 0
alarm_lock = threading.Lock()

# 创建快照目录
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# ==================== 硬件初始化 ====================
if REAL_HARDWARE:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)
    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)
    GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)


def read_pir():
    if REAL_HARDWARE:
        return GPIO.input(PIR_PIN) == GPIO.HIGH
    else:
        return random.random() < 0.08


def read_distance():
    if REAL_HARDWARE:
        GPIO.output(TRIG_PIN, False)
        time.sleep(0.05)
        GPIO.output(TRIG_PIN, True)
        time.sleep(0.00001)
        GPIO.output(TRIG_PIN, False)
        t0 = time.time()
        while GPIO.input(ECHO_PIN) == 0 and time.time() - t0 < 0.1:
            pass
        t1 = time.time()
        while GPIO.input(ECHO_PIN) == 1 and time.time() - t1 < 0.1:
            pass
        t2 = time.time()
        return round((t2 - t1) * 17150, 1)
    else:
        t = sim_t * 0.05
        base = 120 + 60 * math.sin(t * 0.3)
        # 偶尔模拟入侵（距离突然变近）
        if random.random() < 0.05:
            return round(random.uniform(20, 60), 1)
        return round(max(5, base + random.uniform(-10, 10)), 1)


def trigger_buzzer(duration=ALARM_DURATION):
    """触发蜂鸣器报警"""
    if REAL_HARDWARE:
        def beep():
            for _ in range(duration * 2):
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(0.25)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
                time.sleep(0.25)
        threading.Thread(target=beep, daemon=True).start()


def take_snapshot():
    """拍摄快照"""
    if not CAMERA_AVAILABLE:
        # 生成模拟快照（红色警告图片）
        try:
            import struct
            import zlib
            # 创建一个简单的红色PNG图片（1x1像素）作为占位符
            return None
        except Exception:
            return None

    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'alarm_{ts}.jpg'
                filepath = os.path.join(SNAPSHOT_DIR, filename)
                cv2.imwrite(filepath, frame)
                # 转为base64用于Web显示
                _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                b64 = base64.b64encode(buf).decode('utf-8')
                return {'filename': filename, 'data': b64, 'time': ts}
    except Exception as e:
        print(f"拍照失败: {e}")
    return None


def trigger_alarm(reason, source):
    """触发报警"""
    with alarm_lock:
        if security_state['alarm_active']:
            return  # 防止重复报警

        security_state['alarm_active'] = True
        security_state['total_alarms'] += 1
        security_state['today_alarms'] += 1

        now = datetime.now()
        log_entry = {
            'id': security_state['total_alarms'],
            'time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'reason': reason,
            'source': source,
            'snapshot': None
        }

        # 拍照
        snap = take_snapshot()
        if snap:
            log_entry['snapshot'] = snap['data']
            snapshots.appendleft({
                'time': snap['time'],
                'filename': snap['filename'],
                'data': snap['data'],
                'reason': reason
            })

        alarm_log.appendleft(log_entry)
        print(f"🚨 报警！{reason} [{source}]")

        # 触发蜂鸣器
        trigger_buzzer(ALARM_DURATION)

        # 3秒后解除报警状态
        def clear_alarm():
            time.sleep(ALARM_DURATION + 1)
            security_state['alarm_active'] = False
        threading.Thread(target=clear_alarm, daemon=True).start()


# ==================== 数据采集线程 ====================
def security_monitor_thread():
    global sim_t
    while True:
        try:
            sim_t += 1
            pir = read_pir()
            dist = read_distance()
            ts = datetime.now().strftime('%H:%M:%S')

            security_state['pir_triggered'] = pir
            security_state['distance'] = dist
            security_state['distance_alarm'] = dist < ALERT_DISTANCE
            security_state['timestamp'] = ts

            time_history.append(ts)
            distance_history.append(dist)

            # 报警逻辑（仅在布防状态下）
            if security_state['armed']:
                if pir:
                    trigger_alarm('PIR检测到人体活动', 'PIR传感器')
                elif dist < ALERT_DISTANCE:
                    trigger_alarm(f'超声波检测到入侵（距离 {dist}cm）', '超声波传感器')

        except Exception as e:
            print(f"监控错误: {e}")

        time.sleep(SAMPLE_INTERVAL)


# ==================== Flask Web服务器 ====================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔒 智能安防监控中心</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0a0a0f;
            color: #e0e0e0;
            min-height: 100vh;
        }
        header {
            background: #0d1117;
            padding: 15px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,0,0,0.2);
        }
        header h1 { color: #ff4444; font-size: 1.4em; }
        .arm-status {
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
            cursor: pointer;
            border: none;
            transition: all 0.3s;
        }
        .arm-status.armed { background: #c62828; color: white; animation: pulse-red 2s infinite; }
        .arm-status.disarmed { background: #1b5e20; color: #a5d6a7; }
        @keyframes pulse-red { 0%,100%{box-shadow:0 0 0 0 rgba(198,40,40,0.4)} 50%{box-shadow:0 0 0 8px rgba(198,40,40,0)} }

        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }

        /* 报警横幅 */
        .alarm-banner {
            display: none;
            background: linear-gradient(90deg, #b71c1c, #c62828);
            border-radius: 12px;
            padding: 15px 20px;
            margin-bottom: 20px;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
            color: white;
            animation: flash 0.5s infinite;
        }
        .alarm-banner.active { display: block; }
        @keyframes flash { 0%,100%{opacity:1} 50%{opacity:0.6} }

        /* 状态卡片 */
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .status-card {
            background: #0d1117;
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .status-card .icon { font-size: 2.5em; margin-bottom: 8px; }
        .status-card .label { font-size: 0.8em; color: #546e7a; margin-bottom: 6px; text-transform: uppercase; }
        .status-card .value { font-size: 1.8em; font-weight: bold; }
        .status-ok { color: #4caf50; }
        .status-warn { color: #ff9800; }
        .status-alarm { color: #f44336; animation: pulse-red 1s infinite; }

        /* 图表 */
        .chart-card {
            background: #0d1117;
            border-radius: 14px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 20px;
        }
        .chart-card h3 { color: #78909c; margin-bottom: 15px; font-size: 0.95em; }
        .chart-card canvas { max-height: 180px; }

        /* 报警日志 */
        .log-section {
            background: #0d1117;
            border-radius: 14px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 20px;
        }
        .log-section h3 { color: #78909c; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        .log-item {
            display: flex;
            gap: 12px;
            padding: 10px 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            background: rgba(244,67,54,0.08);
            border-left: 3px solid #f44336;
            align-items: flex-start;
        }
        .log-item .log-id { color: #546e7a; font-size: 0.8em; min-width: 30px; }
        .log-item .log-time { color: #ef9a9a; font-size: 0.85em; min-width: 140px; }
        .log-item .log-reason { flex: 1; }
        .log-item .log-source { color: #78909c; font-size: 0.8em; }
        .log-item .log-snap { width: 60px; height: 45px; object-fit: cover; border-radius: 4px; cursor: pointer; }
        .no-log { color: #37474f; font-style: italic; text-align: center; padding: 20px; }

        /* 快照画廊 */
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .gallery-item { position: relative; }
        .gallery-item img { width: 100%; border-radius: 8px; cursor: pointer; transition: transform 0.2s; }
        .gallery-item img:hover { transform: scale(1.05); }
        .gallery-item .gallery-time { font-size: 0.7em; color: #546e7a; text-align: center; margin-top: 3px; }

        /* 统计 */
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
        .stat-card {
            background: #0d1117;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .stat-card .stat-num { font-size: 2.5em; font-weight: bold; color: #ef5350; }
        .stat-card .stat-label { font-size: 0.8em; color: #546e7a; margin-top: 4px; }

        .btn-clear { background: #37474f; color: #90a4ae; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 0.85em; }
        .btn-clear:hover { background: #455a64; }

        footer { text-align: center; color: #37474f; font-size: 0.8em; padding: 15px; }
    </style>
</head>
<body>
    <header>
        <h1>🔒 智能安防监控中心</h1>
        <button class="arm-status armed" id="arm-btn" onclick="toggleArm()">🔴 已布防</button>
    </header>

    <div class="container">
        <!-- 报警横幅 -->
        <div class="alarm-banner" id="alarm-banner">
            🚨 警报！检测到入侵！请立即检查！🚨
        </div>

        <!-- 统计 -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-num" id="stat-total">0</div>
                <div class="stat-label">累计报警次数</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" id="stat-today">0</div>
                <div class="stat-label">今日报警次数</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" id="stat-dist" style="color:#ab47bc">--</div>
                <div class="stat-label">当前距离 (cm)</div>
            </div>
        </div>

        <!-- 传感器状态 -->
        <div class="status-grid">
            <div class="status-card">
                <div class="icon">👤</div>
                <div class="label">PIR 人体感应</div>
                <div class="value status-ok" id="pir-status">无活动</div>
            </div>
            <div class="status-card">
                <div class="icon">📏</div>
                <div class="label">超声波距离</div>
                <div class="value status-ok" id="dist-status">-- cm</div>
            </div>
            <div class="status-card">
                <div class="icon">🔒</div>
                <div class="label">系统状态</div>
                <div class="value status-ok" id="sys-status">布防中</div>
            </div>
            <div class="status-card">
                <div class="icon">🕐</div>
                <div class="label">最后更新</div>
                <div class="value" id="last-ts" style="font-size:1.1em;color:#78909c">--</div>
            </div>
        </div>

        <!-- 距离图表 -->
        <div class="chart-card">
            <h3>📏 超声波距离实时监测（警戒线：{{ alert_distance }}cm）</h3>
            <canvas id="chart-dist"></canvas>
        </div>

        <!-- 报警日志 -->
        <div class="log-section">
            <h3>
                🚨 报警日志（最近50条）
                <button class="btn-clear" onclick="clearLog()">清空日志</button>
            </h3>
            <div id="alarm-log"><p class="no-log">暂无报警记录</p></div>
        </div>

        <!-- 快照画廊 -->
        <div class="log-section">
            <h3>📷 入侵快照（最近{{ max_snapshots }}张）</h3>
            <div class="gallery" id="snapshot-gallery">
                <p class="no-log" style="grid-column:1/-1">暂无快照</p>
            </div>
        </div>
    </div>

    <footer>Raspberry Pi 智能安防监控系统 v1.0 | 刷新间隔：2秒</footer>

    <script>
        const ALERT_DIST = {{ alert_distance }};

        // 距离图表
        const chartDist = new Chart(document.getElementById('chart-dist'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: '距离(cm)', data: [], borderColor: '#ab47bc', backgroundColor: '#ab47bc22', fill: true, tension: 0.4, pointRadius: 0 },
                    { label: '警戒线', data: [], borderColor: '#f44336', borderDash: [5,5], pointRadius: 0, fill: false }
                ]
            },
            options: {
                responsive: true, animation: false,
                plugins: { legend: { labels: { color: '#78909c' } } },
                scales: {
                    x: { ticks: { color: '#546e7a', maxTicksLimit: 10 }, grid: { color: 'rgba(255,255,255,0.04)' } },
                    y: { min: 0, max: 250, ticks: { color: '#546e7a' }, grid: { color: 'rgba(255,255,255,0.04)' } }
                }
            }
        });

        async function fetchStatus() {
            const res = await fetch('/api/security_status');
            const d = await res.json();

            // 报警横幅
            document.getElementById('alarm-banner').className = d.alarm_active ? 'alarm-banner active' : 'alarm-banner';

            // 统计
            document.getElementById('stat-total').textContent = d.total_alarms;
            document.getElementById('stat-today').textContent = d.today_alarms;
            document.getElementById('stat-dist').textContent = d.distance.toFixed(1);
            document.getElementById('last-ts').textContent = d.timestamp;

            // PIR状态
            const pirEl = document.getElementById('pir-status');
            pirEl.textContent = d.pir_triggered ? '⚠ 检测到活动!' : '无活动';
            pirEl.className = 'value ' + (d.pir_triggered ? 'status-alarm' : 'status-ok');

            // 距离状态
            const distEl = document.getElementById('dist-status');
            distEl.textContent = d.distance.toFixed(1) + ' cm';
            distEl.className = 'value ' + (d.distance_alarm ? 'status-alarm' : 'status-ok');

            // 系统状态
            const sysEl = document.getElementById('sys-status');
            const armBtn = document.getElementById('arm-btn');
            if (d.armed) {
                sysEl.textContent = '布防中';
                sysEl.className = 'value status-ok';
                armBtn.textContent = '🔴 已布防';
                armBtn.className = 'arm-status armed';
            } else {
                sysEl.textContent = '已撤防';
                sysEl.className = 'value status-warn';
                armBtn.textContent = '🟢 已撤防';
                armBtn.className = 'arm-status disarmed';
            }
        }

        async function fetchHistory() {
            const res = await fetch('/api/distance_history');
            const h = await res.json();
            chartDist.data.labels = h.timestamps;
            chartDist.data.datasets[0].data = h.distances;
            chartDist.data.datasets[1].data = h.timestamps.map(() => ALERT_DIST);
            chartDist.update('none');
        }

        async function fetchLog() {
            const res = await fetch('/api/alarm_log');
            const logs = await res.json();
            const div = document.getElementById('alarm-log');
            if (!logs.length) { div.innerHTML = '<p class="no-log">暂无报警记录</p>'; return; }
            div.innerHTML = logs.map(l => `
                <div class="log-item">
                    <span class="log-id">#${l.id}</span>
                    <span class="log-time">${l.time}</span>
                    <span class="log-reason">${l.reason}</span>
                    <span class="log-source">${l.source}</span>
                    ${l.snapshot ? `<img class="log-snap" src="data:image/jpeg;base64,${l.snapshot}" onclick="viewSnap(this.src)">` : ''}
                </div>`).join('');
        }

        async function fetchSnapshots() {
            const res = await fetch('/api/snapshots');
            const snaps = await res.json();
            const div = document.getElementById('snapshot-gallery');
            if (!snaps.length) { div.innerHTML = '<p class="no-log" style="grid-column:1/-1">暂无快照</p>'; return; }
            div.innerHTML = snaps.map(s => `
                <div class="gallery-item">
                    <img src="data:image/jpeg;base64,${s.data}" onclick="viewSnap(this.src)" title="${s.reason}">
                    <div class="gallery-time">${s.time}</div>
                </div>`).join('');
        }

        function viewSnap(src) {
            const w = window.open('', '_blank');
            w.document.write(`<html><body style="margin:0;background:#000"><img src="${src}" style="max-width:100%;max-height:100vh"></body></html>`);
        }

        async function toggleArm() {
            const res = await fetch('/api/toggle_arm', { method: 'POST' });
            await fetchStatus();
        }

        async function clearLog() {
            if (confirm('确定清空报警日志？')) {
                await fetch('/api/clear_log', { method: 'POST' });
                await fetchLog();
            }
        }

        fetchStatus(); fetchHistory(); fetchLog(); fetchSnapshots();
        setInterval(fetchStatus, 2000);
        setInterval(fetchHistory, 3000);
        setInterval(fetchLog, 5000);
        setInterval(fetchSnapshots, 10000);
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template(
        'smart_security_web.html',
        alert_distance=ALERT_DISTANCE,
        max_snapshots=MAX_SNAPSHOTS
    )


@app.route('/api/security_status')
def api_security_status():
    return jsonify(security_state)


@app.route('/api/distance_history')
def api_distance_history():
    return jsonify({
        'timestamps': list(time_history),
        'distances': list(distance_history),
    })


@app.route('/api/alarm_log')
def api_alarm_log():
    logs = []
    for entry in alarm_log:
        log = dict(entry)
        # 不在列表中传输完整base64（太大），只在快照画廊中显示
        if log.get('snapshot'):
            log['snapshot'] = log['snapshot'][:100] + '...' if len(log['snapshot']) > 100 else log['snapshot']
        logs.append(log)
    # 重新获取完整数据
    return jsonify([{
        'id': e['id'],
        'time': e['time'],
        'reason': e['reason'],
        'source': e['source'],
        'snapshot': e.get('snapshot')
    } for e in alarm_log])


@app.route('/api/snapshots')
def api_snapshots():
    return jsonify([{
        'time': s['time'],
        'filename': s['filename'],
        'data': s['data'],
        'reason': s['reason']
    } for s in snapshots])


@app.route('/api/toggle_arm', methods=['POST'])
def api_toggle_arm():
    security_state['armed'] = not security_state['armed']
    state = '布防' if security_state['armed'] else '撤防'
    print(f"🔒 系统{state}")
    return jsonify({'armed': security_state['armed'], 'message': f'系统已{state}'})


@app.route('/api/clear_log', methods=['POST'])
def api_clear_log():
    alarm_log.clear()
    security_state['total_alarms'] = 0
    security_state['today_alarms'] = 0
    return jsonify({'message': '日志已清空'})


# ==================== 主程序 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("🔒 智能安防监控系统")
    print("=" * 50)
    print(f"PIR引脚: GPIO{PIR_PIN}")
    print(f"超声波警戒距离: {ALERT_DISTANCE}cm")
    print(f"快照目录: {SNAPSHOT_DIR}/")
    print()

    t = threading.Thread(target=security_monitor_thread, daemon=True)
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

    print(f"🌐 安防监控中心：http://{ip}:5003")
    print("按 Ctrl+C 停止")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5003, debug=False)
