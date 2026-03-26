#!/usr/bin/env python3
"""
智能电能监测系统 - Web仪表盘
Smart Energy Monitor with Web Dashboard

功能：
- 电流监测（ACS712电流传感器 + MCP3008 ADC）
- 电压监测（分压电路 + MCP3008 ADC）
- 实时功率计算（P = U × I）
- 累计用电量统计（kWh）
- 电费估算
- 历史用电趋势图
- 多路负载监测（最多4路）

硬件连接：
- MCP3008 (SPI): CLK=GPIO11, MOSI=GPIO10, MISO=GPIO9, CS=GPIO8
  - CH0: ACS712电流传感器（负载1）
  - CH1: 分压电路电压检测
  - CH2: ACS712电流传感器（负载2）
  - CH3: ACS712电流传感器（负载3）

访问地址：http://<树莓派IP>:5004
"""

import time
import math
import threading
from datetime import datetime, timedelta
from collections import deque
from flask import Flask, render_template, jsonify

try:
    import RPi.GPIO as GPIO
    import spidev
    REAL_HARDWARE = True
    print("✓ 硬件模式")
except ImportError:
    REAL_HARDWARE = False
    import random
    print("⚠ 模拟模式")

# ==================== 配置 ====================
VOLTAGE_CHANNEL = 1     # MCP3008通道：电压检测
CURRENT_CHANNELS = [0, 2, 3]  # MCP3008通道：各路电流

# ACS712参数（ACS712-5A: 185mV/A, ACS712-20A: 100mV/A, ACS712-30A: 66mV/A）
ACS712_SENSITIVITY = 0.185  # V/A（5A版本）
ACS712_ZERO_VOLTAGE = 2.5   # 零电流时输出电压（V）

# 系统电压（V）
SYSTEM_VOLTAGE = 220.0

# 电费单价（元/kWh）
ELECTRICITY_PRICE = 0.6

# 负载名称
LOAD_NAMES = ['主回路', '照明回路', '插座回路', '空调回路']

SAMPLE_INTERVAL = 1.0   # 采集间隔（秒）
MAX_HISTORY = 120       # 历史数据点数

# ==================== 全局数据 ====================
energy_data = {
    'voltage': 0.0,
    'loads': [],
    'total_power': 0.0,
    'total_energy_kwh': 0.0,
    'cost': 0.0,
    'timestamp': '',
    'run_hours': 0.0,
}

power_history = deque(maxlen=MAX_HISTORY)
time_history = deque(maxlen=MAX_HISTORY)
hourly_energy = deque(maxlen=24)   # 24小时用电量
start_time = time.time()
sim_t = 0

# 初始化负载数据
for i, name in enumerate(LOAD_NAMES):
    energy_data['loads'].append({
        'name': name,
        'current': 0.0,
        'power': 0.0,
        'energy_kwh': 0.0,
        'status': 'off'
    })

# ==================== 硬件读取 ====================
if REAL_HARDWARE:
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1350000


def read_adc(channel):
    """读取MCP3008 ADC（0-1023）"""
    if REAL_HARDWARE:
        adc = spi.xfer2([1, (8 + channel) << 4, 0])
        return ((adc[1] & 3) << 8) + adc[2]
    else:
        return random.randint(0, 1023)


def adc_to_voltage(raw, vref=3.3):
    """ADC值转电压"""
    return raw / 1023.0 * vref


def read_current(channel):
    """读取ACS712电流（A）"""
    if REAL_HARDWARE:
        raw = read_adc(channel)
        v = adc_to_voltage(raw)
        current = (v - ACS712_ZERO_VOLTAGE) / ACS712_SENSITIVITY
        return max(0, abs(current))
    else:
        # 模拟不同负载的电流
        t = sim_t * 0.05
        base_currents = [2.5, 0.8, 1.2, 3.5]
        i = CURRENT_CHANNELS.index(channel) if channel in CURRENT_CHANNELS else 0
        base = base_currents[i] if i < len(base_currents) else 1.0
        # 模拟负载开关
        if random.random() < 0.02:  # 偶尔切换负载状态
            pass
        noise = random.uniform(-0.1, 0.1)
        variation = base * 0.2 * math.sin(t * (i + 1) * 0.3)
        return round(max(0, base + variation + noise), 3)


def read_voltage():
    """读取系统电压（V）"""
    if REAL_HARDWARE:
        raw = read_adc(VOLTAGE_CHANNEL)
        # 假设分压比为 220V -> 3.3V（需要根据实际电路调整）
        v_adc = adc_to_voltage(raw)
        voltage = v_adc * (220.0 / 3.3)
        return round(voltage, 1)
    else:
        t = sim_t * 0.02
        return round(220 + 5 * math.sin(t) + random.uniform(-1, 1), 1)


# ==================== 数据采集线程 ====================
def energy_monitor_thread():
    global sim_t
    last_hour = datetime.now().hour
    hourly_start_energy = 0.0

    while True:
        try:
            sim_t += 1
            voltage = read_voltage()
            ts = datetime.now().strftime('%H:%M:%S')
            total_power = 0.0

            for i, (ch, load) in enumerate(zip(CURRENT_CHANNELS, energy_data['loads'])):
                current = read_current(ch)
                power = round(voltage * current, 1)
                # 累计用电量（kWh）
                load['energy_kwh'] += power * SAMPLE_INTERVAL / 3600000
                load['current'] = current
                load['power'] = power
                load['status'] = 'on' if current > 0.1 else 'off'
                total_power += power

            energy_data['voltage'] = voltage
            energy_data['total_power'] = round(total_power, 1)
            energy_data['total_energy_kwh'] += total_power * SAMPLE_INTERVAL / 3600000
            energy_data['cost'] = round(energy_data['total_energy_kwh'] * ELECTRICITY_PRICE, 4)
            energy_data['timestamp'] = ts
            energy_data['run_hours'] = round((time.time() - start_time) / 3600, 2)

            # 记录历史
            time_history.append(ts)
            power_history.append(round(total_power, 1))

            # 每小时统计
            current_hour = datetime.now().hour
            if current_hour != last_hour:
                hour_energy = energy_data['total_energy_kwh'] - hourly_start_energy
                hourly_energy.append({
                    'hour': f'{last_hour:02d}:00',
                    'energy': round(hour_energy * 1000, 2),  # Wh
                    'cost': round(hour_energy * ELECTRICITY_PRICE, 4)
                })
                hourly_start_energy = energy_data['total_energy_kwh']
                last_hour = current_hour

            print(f"[{ts}] 电压:{voltage}V 总功率:{total_power:.1f}W "
                  f"累计:{energy_data['total_energy_kwh']*1000:.2f}Wh "
                  f"电费:¥{energy_data['cost']:.4f}")

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
    <title>⚡ 智能电能监测系统</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #0d1b2a 50%, #0a1628 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        header {
            background: rgba(255,193,7,0.08);
            padding: 15px 24px;
            text-align: center;
            border-bottom: 1px solid rgba(255,193,7,0.2);
        }
        header h1 { font-size: 1.8em; color: #ffd54f; }
        header p { color: #90a4ae; font-size: 0.9em; margin-top: 4px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }

        /* 主要指标 */
        .main-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .metric-card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 22px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.08);
            position: relative;
            overflow: hidden;
        }
        .metric-card::after {
            content: '';
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 3px;
        }
        .metric-card.voltage::after { background: linear-gradient(90deg, #ffd54f, #ff8f00); }
        .metric-card.power::after { background: linear-gradient(90deg, #ef5350, #b71c1c); }
        .metric-card.energy::after { background: linear-gradient(90deg, #42a5f5, #1565c0); }
        .metric-card.cost::after { background: linear-gradient(90deg, #66bb6a, #2e7d32); }
        .metric-icon { font-size: 2.2em; margin-bottom: 8px; }
        .metric-label { font-size: 0.8em; color: #78909c; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-value { font-size: 2.2em; font-weight: 700; }
        .metric-unit { font-size: 0.8em; color: #78909c; margin-top: 3px; }
        .metric-card.voltage .metric-value { color: #ffd54f; }
        .metric-card.power .metric-value { color: #ef5350; }
        .metric-card.energy .metric-value { color: #42a5f5; }
        .metric-card.cost .metric-value { color: #66bb6a; }

        /* 负载卡片 */
        .loads-section { margin-bottom: 20px; }
        .loads-section h3 { color: #90a4ae; margin-bottom: 12px; font-size: 1em; }
        .loads-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
        .load-card {
            background: rgba(255,255,255,0.05);
            border-radius: 14px;
            padding: 16px;
            border: 1px solid rgba(255,255,255,0.08);
            transition: border-color 0.3s;
        }
        .load-card.on { border-color: rgba(255,193,7,0.4); }
        .load-card.off { opacity: 0.6; }
        .load-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .load-name { font-weight: bold; color: #e0e0e0; }
        .load-badge {
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 0.75em;
            font-weight: bold;
        }
        .badge-on { background: rgba(76,175,80,0.2); color: #81c784; border: 1px solid #4caf50; }
        .badge-off { background: rgba(255,255,255,0.05); color: #546e7a; border: 1px solid #37474f; }
        .load-metrics { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
        .load-metric { text-align: center; }
        .load-metric .lm-val { font-size: 1.3em; font-weight: bold; color: #ffd54f; }
        .load-metric .lm-label { font-size: 0.7em; color: #546e7a; }
        .power-bar {
            height: 6px;
            background: rgba(255,255,255,0.08);
            border-radius: 3px;
            margin-top: 10px;
            overflow: hidden;
        }
        .power-bar-fill {
            height: 100%;
            border-radius: 3px;
            background: linear-gradient(90deg, #ffd54f, #ff8f00);
            transition: width 0.5s ease;
        }

        /* 图表 */
        .charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .chart-card {
            background: rgba(255,255,255,0.05);
            border-radius: 14px;
            padding: 18px;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .chart-card h3 { color: #78909c; margin-bottom: 14px; font-size: 0.9em; }
        .chart-card canvas { max-height: 200px; }

        /* 每小时统计 */
        .hourly-section {
            background: rgba(255,255,255,0.05);
            border-radius: 14px;
            padding: 18px;
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 20px;
        }
        .hourly-section h3 { color: #78909c; margin-bottom: 14px; font-size: 0.9em; }
        .hourly-table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
        .hourly-table th { color: #546e7a; padding: 8px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.08); }
        .hourly-table td { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .hourly-table tr:hover td { background: rgba(255,255,255,0.03); }
        .no-data { color: #37474f; font-style: italic; text-align: center; padding: 20px; }

        footer { text-align: center; color: #37474f; font-size: 0.8em; padding: 15px; }
    </style>
</head>
<body>
    <header>
        <h1>⚡ 智能电能监测系统</h1>
        <p>Raspberry Pi IoT 实时电能监测与分析 | 电价：¥{{ price }}/kWh</p>
    </header>
    <div class="container">
        <!-- 主要指标 -->
        <div class="main-metrics">
            <div class="metric-card voltage">
                <div class="metric-icon">🔌</div>
                <div class="metric-label">系统电压</div>
                <div class="metric-value" id="m-voltage">--</div>
                <div class="metric-unit">V (AC)</div>
            </div>
            <div class="metric-card power">
                <div class="metric-icon">⚡</div>
                <div class="metric-label">实时总功率</div>
                <div class="metric-value" id="m-power">--</div>
                <div class="metric-unit">W</div>
            </div>
            <div class="metric-card energy">
                <div class="metric-icon">📊</div>
                <div class="metric-label">累计用电量</div>
                <div class="metric-value" id="m-energy">--</div>
                <div class="metric-unit">Wh</div>
            </div>
            <div class="metric-card cost">
                <div class="metric-icon">💰</div>
                <div class="metric-label">累计电费</div>
                <div class="metric-value" id="m-cost">--</div>
                <div class="metric-unit">元</div>
            </div>
        </div>

        <!-- 各路负载 -->
        <div class="loads-section">
            <h3>🔌 各路负载监测</h3>
            <div class="loads-grid" id="loads-grid">
                <!-- 动态生成 -->
            </div>
        </div>

        <!-- 图表 -->
        <div class="charts">
            <div class="chart-card">
                <h3>⚡ 实时总功率趋势（W）</h3>
                <canvas id="chart-power"></canvas>
            </div>
            <div class="chart-card">
                <h3>🔌 各路负载功率对比（W）</h3>
                <canvas id="chart-loads"></canvas>
            </div>
        </div>

        <!-- 每小时统计 -->
        <div class="hourly-section">
            <h3>📅 每小时用电统计</h3>
            <div id="hourly-table-container">
                <p class="no-data">运行满1小时后显示统计数据</p>
            </div>
        </div>
    </div>

    <footer>
        运行时长：<span id="run-hours">--</span> 小时 |
        最后更新：<span id="last-ts">--</span> |
        智能电能监测系统 v1.0
    </footer>

    <script>
        const LOAD_COLORS = ['#ffd54f', '#42a5f5', '#66bb6a', '#ef5350'];

        // 功率趋势图
        const chartPower = new Chart(document.getElementById('chart-power'), {
            type: 'line',
            data: { labels: [], datasets: [{
                label: '总功率(W)', data: [],
                borderColor: '#ef5350', backgroundColor: '#ef535022',
                fill: true, tension: 0.4, pointRadius: 0
            }]},
            options: {
                responsive: true, animation: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#546e7a', maxTicksLimit: 10 }, grid: { color: 'rgba(255,255,255,0.04)' } },
                    y: { min: 0, ticks: { color: '#546e7a' }, grid: { color: 'rgba(255,255,255,0.04)' } }
                }
            }
        });

        // 各路负载图
        const chartLoads = new Chart(document.getElementById('chart-loads'), {
            type: 'bar',
            data: { labels: [], datasets: [] },
            options: {
                responsive: true, animation: false,
                plugins: { legend: { labels: { color: '#78909c', boxWidth: 12 } } },
                scales: {
                    x: { ticks: { color: '#546e7a' }, grid: { color: 'rgba(255,255,255,0.04)' } },
                    y: { min: 0, ticks: { color: '#546e7a' }, grid: { color: 'rgba(255,255,255,0.04)' } }
                }
            }
        });

        let loadsInitialized = false;

        async function fetchData() {
            const res = await fetch('/api/energy_data');
            const d = await res.json();

            document.getElementById('m-voltage').textContent = d.voltage.toFixed(1);
            document.getElementById('m-power').textContent = d.total_power.toFixed(1);
            document.getElementById('m-energy').textContent = (d.total_energy_kwh * 1000).toFixed(2);
            document.getElementById('m-cost').textContent = d.cost.toFixed(4);
            document.getElementById('last-ts').textContent = d.timestamp;
            document.getElementById('run-hours').textContent = d.run_hours.toFixed(2);

            // 渲染负载卡片
            const grid = document.getElementById('loads-grid');
            if (!loadsInitialized) {
                grid.innerHTML = d.loads.map((l, i) => `
                    <div class="load-card ${l.status}" id="load-${i}">
                        <div class="load-header">
                            <span class="load-name">${l.name}</span>
                            <span class="load-badge badge-${l.status}" id="badge-${i}">${l.status === 'on' ? '通电' : '断电'}</span>
                        </div>
                        <div class="load-metrics">
                            <div class="load-metric">
                                <div class="lm-val" id="lc-${i}">0.00</div>
                                <div class="lm-label">电流(A)</div>
                            </div>
                            <div class="load-metric">
                                <div class="lm-val" id="lp-${i}">0.0</div>
                                <div class="lm-label">功率(W)</div>
                            </div>
                            <div class="load-metric">
                                <div class="lm-val" id="le-${i}">0.00</div>
                                <div class="lm-label">用电(Wh)</div>
                            </div>
                        </div>
                        <div class="power-bar">
                            <div class="power-bar-fill" id="lb-${i}" style="width:0%"></div>
                        </div>
                    </div>`).join('');
                loadsInitialized = true;
            } else {
                d.loads.forEach((l, i) => {
                    const card = document.getElementById(`load-${i}`);
                    if (card) {
                        card.className = `load-card ${l.status}`;
                        document.getElementById(`badge-${i}`).textContent = l.status === 'on' ? '通电' : '断电';
                        document.getElementById(`badge-${i}`).className = `load-badge badge-${l.status}`;
                        document.getElementById(`lc-${i}`).textContent = l.current.toFixed(3);
                        document.getElementById(`lp-${i}`).textContent = l.power.toFixed(1);
                        document.getElementById(`le-${i}`).textContent = (l.energy_kwh * 1000).toFixed(2);
                        const maxPower = 1000;
                        document.getElementById(`lb-${i}`).style.width = Math.min(100, l.power / maxPower * 100) + '%';
                    }
                });
            }
        }

        async function fetchHistory() {
            const res = await fetch('/api/power_history');
            const h = await res.json();
            chartPower.data.labels = h.timestamps;
            chartPower.data.datasets[0].data = h.power;
            chartPower.update('none');

            // 更新负载对比图
            const res2 = await fetch('/api/energy_data');
            const d = await res2.json();
            chartLoads.data.labels = d.loads.map(l => l.name);
            chartLoads.data.datasets = [{
                label: '当前功率(W)',
                data: d.loads.map(l => l.power),
                backgroundColor: LOAD_COLORS.map(c => c + '88'),
                borderColor: LOAD_COLORS,
                borderWidth: 2,
                borderRadius: 6,
            }];
            chartLoads.update('none');
        }

        async function fetchHourly() {
            const res = await fetch('/api/hourly_energy');
            const data = await res.json();
            const container = document.getElementById('hourly-table-container');
            if (!data.length) {
                container.innerHTML = '<p class="no-data">运行满1小时后显示统计数据</p>';
                return;
            }
            container.innerHTML = `
                <table class="hourly-table">
                    <thead><tr><th>时段</th><th>用电量(Wh)</th><th>电费(元)</th></tr></thead>
                    <tbody>${data.map(r => `
                        <tr>
                            <td>${r.hour}</td>
                            <td>${r.energy.toFixed(2)} Wh</td>
                            <td>¥${r.cost.toFixed(4)}</td>
                        </tr>`).join('')}
                    </tbody>
                </table>`;
        }

        fetchData(); fetchHistory(); fetchHourly();
        setInterval(fetchData, 2000);
        setInterval(fetchHistory, 5000);
        setInterval(fetchHourly, 60000);
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template('energy_monitor_web.html', price=ELECTRICITY_PRICE)


@app.route('/api/energy_data')
def api_energy_data():
    return jsonify(energy_data)


@app.route('/api/power_history')
def api_power_history():
    return jsonify({
        'timestamps': list(time_history),
        'power': list(power_history),
    })


@app.route('/api/hourly_energy')
def api_hourly_energy():
    return jsonify(list(hourly_energy))


# ==================== 主程序 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("⚡ 智能电能监测系统")
    print("=" * 50)
    print(f"监测回路数: {len(CURRENT_CHANNELS)}")
    print(f"系统电压: {SYSTEM_VOLTAGE}V")
    print(f"电费单价: ¥{ELECTRICITY_PRICE}/kWh")
    print()

    t = threading.Thread(target=energy_monitor_thread, daemon=True)
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

    print(f"🌐 电能监测仪表盘：http://{ip}:5004")
    print("按 Ctrl+C 停止")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5004, debug=False)