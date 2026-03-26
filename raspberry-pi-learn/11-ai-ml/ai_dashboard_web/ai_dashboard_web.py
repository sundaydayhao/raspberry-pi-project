#!/usr/bin/env python3
"""
AI/ML 智能仪表盘 Web 服务
集成传感器异常检测、图像分类、手势识别结果的实时展示

运行:
  cd 11-ai-ml/ai_dashboard_web
  python3 ai_dashboard_web.py
  访问: http://<树莓派IP>:5007

安装依赖:
  pip3 install flask flask-socketio eventlet scikit-learn numpy opencv-python
"""

import os
import sys
import time
import random
import math
import threading
import base64
from collections import deque
from datetime import datetime

# 将父目录加入路径，复用异常检测模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

# ── 尝试导入 ML 库 ────────────────────────────────────────────────────────────
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False

# ── Flask 应用 ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "ai-ml-dashboard-2024"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── 全局状态 ──────────────────────────────────────────────────────────────────
MAX_HISTORY = 60   # 保留最近 60 个数据点

state = {
    # 传感器数据
    "sensor_history": deque(maxlen=MAX_HISTORY),
    "anomaly_history": deque(maxlen=MAX_HISTORY),
    "anomaly_count": 0,
    "total_count": 0,

    # 图像分类
    "last_classification": [],
    "classification_count": 0,

    # 手势识别
    "last_gesture": "无",
    "gesture_history": deque(maxlen=20),
    "gesture_counts": {},

    # 系统状态
    "ml_libs": {
        "numpy": NUMPY_AVAILABLE,
        "scikit-learn": SKLEARN_AVAILABLE,
        "opencv": CV2_AVAILABLE,
        "raspberry-pi": RPI_AVAILABLE,
    },
    "start_time": time.time(),
    "running": True,
}

# ── 异常检测器（复用 sensor_anomaly_detection.py 的逻辑）────────────────────

class SimpleAnomalyDetector:
    def __init__(self, window_size=50, z_threshold=3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.buffers = {}

    def _get_buffer(self, name):
        if name not in self.buffers:
            self.buffers[name] = deque(maxlen=self.window_size)
        return self.buffers[name]

    def update_and_detect(self, name, value):
        buf = self._get_buffer(name)
        if len(buf) < 10:
            buf.append(value)
            return False, 0.0
        data = list(buf)
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        std = math.sqrt(variance) if variance > 0 else 1e-6
        z_score = abs(value - mean) / std
        buf.append(value)
        return z_score > self.z_threshold, round(z_score, 3)


class IFAnomalyDetector:
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.buffer = deque(maxlen=window_size)
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False

    def add_and_detect(self, sample):
        self.buffer.append(sample)
        if len(self.buffer) >= 30 and not self.is_trained:
            self._train()
        if not self.is_trained:
            return False, 0.0
        X = np.array([sample])
        X_s = self.scaler.transform(X)
        pred = self.model.predict(X_s)[0]
        score = float(self.model.score_samples(X_s)[0])
        return pred == -1, round(score, 4)

    def _train(self):
        if not SKLEARN_AVAILABLE or not NUMPY_AVAILABLE:
            return
        X = np.array(list(self.buffer))
        X_s = self.scaler.fit_transform(X)
        self.model = IsolationForest(contamination=0.05, random_state=42, n_estimators=50)
        self.model.fit(X_s)
        self.is_trained = True


# 选择检测器
if SKLEARN_AVAILABLE and NUMPY_AVAILABLE:
    anomaly_detector = IFAnomalyDetector(window_size=100)
    detector_name = "Isolation Forest"
else:
    anomaly_detector = SimpleAnomalyDetector(window_size=50)
    detector_name = "Z-Score"

# ── 模拟传感器读取 ────────────────────────────────────────────────────────────

_inject_anomaly_counter = 0

def read_sensors():
    """读取传感器数据（真实或模拟）"""
    global _inject_anomaly_counter
    _inject_anomaly_counter += 1

    try:
        import Adafruit_DHT
        humi, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4)
        temp = temp or 25.0
        humi = humi or 60.0
    except Exception:
        temp = 25.0 + random.gauss(0, 1.5)
        humi = 60.0 + random.gauss(0, 5.0)
        # 每 30 个样本注入一次异常
        if _inject_anomaly_counter % 30 == 0:
            temp += random.choice([-12, 18])
            humi += random.choice([-35, 30])

    try:
        import board, busio, adafruit_bmp280
        i2c = busio.I2C(board.SCL, board.SDA)
        bmp = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
        pressure = bmp.pressure
    except Exception:
        pressure = 1013.25 + random.gauss(0, 2.0)
        if _inject_anomaly_counter % 30 == 0:
            pressure += random.choice([-25, 35])

    return round(temp, 1), round(humi, 1), round(pressure, 2)


# ── 模拟图像分类 ──────────────────────────────────────────────────────────────

DEMO_LABELS = ["猫", "狗", "苹果", "香蕉", "汽车", "自行车",
               "椅子", "桌子", "手机", "书本", "花朵", "树木"]

def simulate_classification():
    """模拟图像分类结果"""
    chosen = random.sample(DEMO_LABELS, 5)
    scores = sorted([random.uniform(0.05, 0.85) for _ in range(5)], reverse=True)
    total = sum(scores)
    scores = [s / total for s in scores]
    return [{"label": l, "confidence": round(c * 100, 1)} for l, c in zip(chosen, scores)]


# ── 模拟手势识别 ──────────────────────────────────────────────────────────────

DEMO_GESTURES = ["✊ 握拳", "✋ 张开", "☝ 一指", "✌ 剪刀", "👍 点赞", "无"]
GESTURE_WEIGHTS = [0.15, 0.15, 0.15, 0.15, 0.1, 0.3]

def simulate_gesture():
    """模拟手势识别结果"""
    return random.choices(DEMO_GESTURES, weights=GESTURE_WEIGHTS, k=1)[0]


# ─────────────────────────────────────────────────────────────────────────────
# 后台数据采集线程
# ─────────────────────────────────────────────────────────────────────────────

def data_collection_thread():
    """后台线程：持续采集数据并通过 WebSocket 推送"""
    while state["running"]:
        try:
            now = datetime.now().strftime("%H:%M:%S")
            temp, humi, pressure = read_sensors()

            # 异常检测
            if isinstance(anomaly_detector, IFAnomalyDetector):
                is_anomaly, score = anomaly_detector.add_and_detect([temp, humi, pressure])
            else:
                t_anom, _ = anomaly_detector.update_and_detect("temp", temp)
                h_anom, _ = anomaly_detector.update_and_detect("humi", humi)
                is_anomaly = t_anom or h_anom
                score = 0.0

            state["total_count"] += 1
            if is_anomaly:
                state["anomaly_count"] += 1

            sensor_point = {
                "time": now,
                "temperature": temp,
                "humidity": humi,
                "pressure": pressure,
                "is_anomaly": is_anomaly,
                "score": score,
            }
            state["sensor_history"].append(sensor_point)
            state["anomaly_history"].append(1 if is_anomaly else 0)

            # 图像分类（每 5 秒更新一次）
            if state["total_count"] % 5 == 0:
                state["last_classification"] = simulate_classification()
                state["classification_count"] += 1

            # 手势识别（每 2 秒更新一次）
            if state["total_count"] % 2 == 0:
                gesture = simulate_gesture()
                state["last_gesture"] = gesture
                state["gesture_history"].append({"time": now, "gesture": gesture})
                state["gesture_counts"][gesture] = state["gesture_counts"].get(gesture, 0) + 1

            # 推送数据到前端
            anomaly_rate = (state["anomaly_count"] / state["total_count"] * 100
                            if state["total_count"] > 0 else 0)

            socketio.emit("update", {
                "sensor": sensor_point,
                "anomaly_rate": round(anomaly_rate, 2),
                "anomaly_count": state["anomaly_count"],
                "total_count": state["total_count"],
                "classification": state["last_classification"],
                "gesture": state["last_gesture"],
                "gesture_counts": state["gesture_counts"],
                "detector": detector_name,
            })

        except Exception as e:
            print(f"数据采集错误: {e}")

        time.sleep(1.0)


# ─────────────────────────────────────────────────────────────────────────────
# Flask 路由
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("ai_dashboard_web.html",
                           detector_name=detector_name,
                           ml_libs=state["ml_libs"])


@app.route("/api/status")
def api_status():
    uptime = int(time.time() - state["start_time"])
    anomaly_rate = (state["anomaly_count"] / state["total_count"] * 100
                    if state["total_count"] > 0 else 0)
    return jsonify({
        "uptime": uptime,
        "total_count": state["total_count"],
        "anomaly_count": state["anomaly_count"],
        "anomaly_rate": round(anomaly_rate, 2),
        "detector": detector_name,
        "ml_libs": state["ml_libs"],
        "last_gesture": state["last_gesture"],
        "classification": state["last_classification"],
    })


@app.route("/api/history")
def api_history():
    return jsonify({
        "sensor_history": list(state["sensor_history"]),
        "anomaly_history": list(state["anomaly_history"]),
        "gesture_history": list(state["gesture_history"]),
    })


@app.route("/api/reset", methods=["POST"])
def api_reset():
    state["anomaly_count"] = 0
    state["total_count"] = 0
    state["sensor_history"].clear()
    state["anomaly_history"].clear()
    state["gesture_history"].clear()
    state["gesture_counts"].clear()
    return jsonify({"status": "ok"})


@socketio.on("connect")
def on_connect():
    emit("init", {
        "history": list(state["sensor_history"]),
        "detector": detector_name,
        "ml_libs": state["ml_libs"],
    })


# ─────────────────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("🤖 AI/ML 智能仪表盘")
    print("=" * 55)
    print(f"  异常检测算法: {detector_name}")
    print(f"  numpy:        {'✅' if NUMPY_AVAILABLE else '❌'}")
    print(f"  scikit-learn: {'✅' if SKLEARN_AVAILABLE else '❌'}")
    print(f"  OpenCV:       {'✅' if CV2_AVAILABLE else '❌'}")
    print(f"  树莓派 GPIO:  {'✅' if RPI_AVAILABLE else '❌ (模拟模式)'}")
    print()
    print("  访问地址: http://localhost:5007")
    print("  手机访问: http://<树莓派IP>:5007")
    print("  按 Ctrl+C 退出")
    print("=" * 55)

    # 启动后台数据采集线程
    t = threading.Thread(target=data_collection_thread, daemon=True)
    t.start()

    try:
        socketio.run(app, host="0.0.0.0", port=5007, debug=False)
    finally:
        state["running"] = False