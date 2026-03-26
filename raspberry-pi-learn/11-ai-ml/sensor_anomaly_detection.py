#!/usr/bin/env python3
"""
传感器数据异常检测
使用机器学习（IsolationForest）检测传感器数据中的异常值

安装依赖:
  pip3 install scikit-learn numpy

学习要点:
  - 无监督异常检测（Isolation Forest）
  - 传感器数据预处理
  - 实时流式检测
  - 异常报警联动
"""

import time
import random
import math
from collections import deque

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️  未找到 numpy，请安装: pip3 install numpy")

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️  未找到 scikit-learn，请安装: pip3 install scikit-learn")

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False

# ── 报警 LED 引脚（可选）──────────────────────────────────────────────────────
ALARM_LED_PIN = 18

# ── 数据窗口大小 ──────────────────────────────────────────────────────────────
WINDOW_SIZE = 100          # 训练窗口
DETECT_INTERVAL = 2.0      # 检测间隔（秒）


# ─────────────────────────────────────────────────────────────────────────────
# 传感器读取（真实 / 模拟）
# ─────────────────────────────────────────────────────────────────────────────

def read_dht11():
    """读取 DHT11 温湿度（模拟）"""
    try:
        import Adafruit_DHT
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4)
        return temperature or 25.0, humidity or 60.0
    except Exception:
        # 模拟正常数据，偶尔注入异常
        temp = 25.0 + random.gauss(0, 1.5)
        humi = 60.0 + random.gauss(0, 5.0)
        # 1% 概率注入异常
        if random.random() < 0.01:
            temp += random.choice([-15, 20])
            humi += random.choice([-40, 35])
        return round(temp, 1), round(humi, 1)


def read_bmp280():
    """读取 BMP280 气压（模拟）"""
    try:
        import board, busio, adafruit_bmp280
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
        return sensor.pressure
    except Exception:
        pressure = 1013.25 + random.gauss(0, 2.0)
        if random.random() < 0.01:
            pressure += random.choice([-30, 40])
        return round(pressure, 2)


def collect_sample():
    """采集一个多维传感器样本 [温度, 湿度, 气压]"""
    temp, humi = read_dht11()
    pressure = read_bmp280()
    return [temp, humi, pressure]


# ─────────────────────────────────────────────────────────────────────────────
# 异常检测器
# ─────────────────────────────────────────────────────────────────────────────

class SensorAnomalyDetector:
    """基于 Isolation Forest 的传感器异常检测器"""

    def __init__(self, window_size=WINDOW_SIZE, contamination=0.05):
        self.window_size = window_size
        self.contamination = contamination
        self.buffer = deque(maxlen=window_size)
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False
        self.anomaly_count = 0
        self.total_count = 0

    def add_sample(self, sample):
        """向缓冲区添加样本"""
        self.buffer.append(sample)

    def train(self):
        """用缓冲区数据训练模型"""
        if not SKLEARN_AVAILABLE or not NUMPY_AVAILABLE:
            return False
        if len(self.buffer) < self.window_size // 2:
            return False

        X = np.array(list(self.buffer))
        X_scaled = self.scaler.fit_transform(X)
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        self.model.fit(X_scaled)
        self.is_trained = True
        print(f"  ✅ 模型训练完成（{len(self.buffer)} 个样本）")
        return True

    def predict(self, sample):
        """
        预测样本是否异常
        返回: (is_anomaly: bool, score: float)
        """
        if not self.is_trained:
            return False, 0.0

        X = np.array([sample])
        X_scaled = self.scaler.transform(X)
        pred = self.model.predict(X_scaled)[0]          # 1=正常, -1=异常
        score = self.model.score_samples(X_scaled)[0]   # 越负越异常

        self.total_count += 1
        is_anomaly = (pred == -1)
        if is_anomaly:
            self.anomaly_count += 1
        return is_anomaly, round(score, 4)

    def anomaly_rate(self):
        if self.total_count == 0:
            return 0.0
        return round(self.anomaly_count / self.total_count * 100, 2)


# ─────────────────────────────────────────────────────────────────────────────
# 简单统计异常检测（无需 scikit-learn）
# ─────────────────────────────────────────────────────────────────────────────

class SimpleAnomalyDetector:
    """基于 Z-Score 的简单统计异常检测（无需 ML 库）"""

    def __init__(self, window_size=50, z_threshold=3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.buffers = {}   # {feature_name: deque}
        self.anomaly_count = 0
        self.total_count = 0

    def _get_buffer(self, name):
        if name not in self.buffers:
            self.buffers[name] = deque(maxlen=self.window_size)
        return self.buffers[name]

    def update_and_detect(self, name, value):
        """
        更新特征缓冲区并检测异常
        返回: (is_anomaly: bool, z_score: float)
        """
        buf = self._get_buffer(name)
        self.total_count += 1

        if len(buf) < 10:
            buf.append(value)
            return False, 0.0

        data = list(buf)
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        std = math.sqrt(variance) if variance > 0 else 1e-6

        z_score = abs(value - mean) / std
        is_anomaly = z_score > self.z_threshold

        if is_anomaly:
            self.anomaly_count += 1

        buf.append(value)
        return is_anomaly, round(z_score, 3)

    def anomaly_rate(self):
        if self.total_count == 0:
            return 0.0
        return round(self.anomaly_count / self.total_count * 100, 2)


# ─────────────────────────────────────────────────────────────────────────────
# GPIO 报警
# ─────────────────────────────────────────────────────────────────────────────

def setup_alarm():
    if RPI_AVAILABLE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ALARM_LED_PIN, GPIO.OUT)
        GPIO.output(ALARM_LED_PIN, GPIO.LOW)

def trigger_alarm(duration=0.5):
    if RPI_AVAILABLE:
        GPIO.output(ALARM_LED_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(ALARM_LED_PIN, GPIO.LOW)

def cleanup_alarm():
    if RPI_AVAILABLE:
        GPIO.cleanup()


# ─────────────────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────────────────

def run_ml_detection():
    """使用 Isolation Forest 进行异常检测"""
    print("\n🤖 Isolation Forest 异常检测")
    print("─" * 40)
    print(f"  训练窗口: {WINDOW_SIZE} 个样本")
    print(f"  检测间隔: {DETECT_INTERVAL} 秒")
    print("  按 Ctrl+C 退出\n")

    detector = SensorAnomalyDetector(window_size=WINDOW_SIZE)
    setup_alarm()

    phase = "collecting"
    sample_idx = 0

    try:
        while True:
            sample = collect_sample()
            temp, humi, pressure = sample
            sample_idx += 1

            detector.add_sample(sample)

            if phase == "collecting":
                progress = len(detector.buffer) / (WINDOW_SIZE // 2) * 100
                print(f"  [{sample_idx:4d}] 采集中... {progress:.0f}%  "
                      f"T={temp}°C  H={humi}%  P={pressure}hPa")

                if len(detector.buffer) >= WINDOW_SIZE // 2:
                    print("\n  开始训练模型...")
                    if detector.train():
                        phase = "detecting"
                        print("  🔍 进入检测模式\n")

            else:  # detecting
                is_anomaly, score = detector.predict(sample)
                status = "🚨 异常" if is_anomaly else "✅ 正常"

                print(f"  [{sample_idx:4d}] {status}  "
                      f"T={temp:5.1f}°C  H={humi:5.1f}%  P={pressure:7.2f}hPa  "
                      f"score={score:6.3f}  "
                      f"异常率={detector.anomaly_rate():.1f}%")

                if is_anomaly:
                    trigger_alarm()

                # 每 50 个样本重新训练一次（在线学习）
                if sample_idx % 50 == 0:
                    detector.train()

            time.sleep(DETECT_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n📊 统计结果:")
        print(f"  总样本数: {detector.total_count}")
        print(f"  异常数量: {detector.anomaly_count}")
        print(f"  异常率:   {detector.anomaly_rate():.2f}%")
    finally:
        cleanup_alarm()


def run_zscore_detection():
    """使用 Z-Score 进行简单异常检测（无需 ML 库）"""
    print("\n📊 Z-Score 统计异常检测")
    print("─" * 40)
    print("  无需 scikit-learn，基于滑动窗口统计")
    print("  按 Ctrl+C 退出\n")

    detector = SimpleAnomalyDetector(window_size=50, z_threshold=3.0)
    setup_alarm()
    sample_idx = 0

    try:
        while True:
            temp, humi = read_dht11()
            sample_idx += 1

            t_anomaly, t_z = detector.update_and_detect("temperature", temp)
            h_anomaly, h_z = detector.update_and_detect("humidity", humi)

            is_anomaly = t_anomaly or h_anomaly
            status = "🚨 异常" if is_anomaly else "✅ 正常"

            detail = ""
            if t_anomaly:
                detail += f" [温度异常 z={t_z}]"
            if h_anomaly:
                detail += f" [湿度异常 z={h_z}]"

            print(f"  [{sample_idx:4d}] {status}  "
                  f"T={temp:5.1f}°C(z={t_z:.2f})  "
                  f"H={humi:5.1f}%(z={h_z:.2f})"
                  f"{detail}")

            if is_anomaly:
                trigger_alarm()

            time.sleep(DETECT_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n📊 统计结果:")
        print(f"  总检测次数: {detector.total_count}")
        print(f"  异常次数:   {detector.anomaly_count}")
        print(f"  异常率:     {detector.anomaly_rate():.2f}%")
    finally:
        cleanup_alarm()


def demo_mode():
    """演示模式：展示异常检测原理"""
    print("\n📖 异常检测演示（模拟数据）")
    print("─" * 40)

    if not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
        print("  使用 Z-Score 方法（无需 ML 库）\n")
        detector = SimpleAnomalyDetector(window_size=30, z_threshold=2.5)

        # 生成演示数据
        data_points = []
        for i in range(60):
            temp = 25.0 + random.gauss(0, 1.0)
            # 在第 40、50 个点注入异常
            if i in (40, 50):
                temp += random.choice([-12, 15])
            data_points.append((i, temp))

        print("  序号  温度(°C)  Z-Score  状态")
        print("  " + "─" * 35)
        for idx, temp in data_points:
            is_anomaly, z = detector.update_and_detect("temp", temp)
            status = "🚨 异常" if is_anomaly else "  正常"
            marker = " ◄◄◄" if is_anomaly else ""
            print(f"  {idx:4d}  {temp:7.2f}   {z:6.3f}   {status}{marker}")
            time.sleep(0.05)
        return

    print("  使用 Isolation Forest 方法\n")
    # 生成训练数据（正常）
    np.random.seed(42)
    X_train = np.random.randn(200, 2) * np.array([2, 5]) + np.array([25, 60])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)

    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X_scaled)

    # 测试数据（含异常）
    test_normal = np.random.randn(10, 2) * np.array([2, 5]) + np.array([25, 60])
    test_anomaly = np.array([[45, 20], [5, 95], [50, 10]])
    X_test = np.vstack([test_normal, test_anomaly])
    labels = ["正常"] * 10 + ["注入异常"] * 3

    print("  温度(°C)  湿度(%)  预测结果  真实标签")
    print("  " + "─" * 45)
    for i, (sample, label) in enumerate(zip(X_test, labels)):
        x_s = scaler.transform([sample])
        pred = model.predict(x_s)[0]
        score = model.score_samples(x_s)[0]
        result = "🚨 异常" if pred == -1 else "✅ 正常"
        print(f"  {sample[0]:7.1f}   {sample[1]:6.1f}   {result}   [{label}]  score={score:.3f}")


def main():
    print("=" * 50)
    print("🤖 传感器数据异常检测（AI/ML）")
    print("=" * 50)

    print("\n选择模式:")
    print("1. Isolation Forest 检测（推荐，需要 scikit-learn）")
    print("2. Z-Score 统计检测（无需 ML 库）")
    print("3. 演示模式（查看原理）")

    choice = input("\n请选择 (1-3, 默认3): ").strip() or "3"

    if choice == "1":
        if not SKLEARN_AVAILABLE:
            print("❌ 需要安装 scikit-learn: pip3 install scikit-learn")
            return
        run_ml_detection()
    elif choice == "2":
        run_zscore_detection()
    else:
        demo_mode()


if __name__ == "__main__":
    main()