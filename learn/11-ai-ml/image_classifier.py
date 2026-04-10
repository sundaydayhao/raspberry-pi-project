#!/usr/bin/env python3
"""
图像分类（TensorFlow Lite / OpenCV DNN）
在树莓派上运行轻量级图像分类模型

安装依赖:
  # 方案一：TensorFlow Lite（推荐树莓派）
  pip3 install tflite-runtime
  # 或完整 TensorFlow（较慢）
  pip3 install tensorflow

  # 方案二：OpenCV DNN（无需 TF）
  pip3 install opencv-python

  # 下载 MobileNetV2 TFLite 模型
  wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/mobilenet_v2_1.0_224_quant_and_labels.zip

学习要点:
  - TensorFlow Lite 推理
  - MobileNetV2 轻量级模型
  - 图像预处理（resize、归一化）
  - 摄像头实时分类
"""

import os
import time
import urllib.request
import zipfile
import json

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️  未找到 numpy，请安装: pip3 install numpy")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# 尝试加载 TFLite
TFLITE_AVAILABLE = False
try:
    import tflite_runtime.interpreter as tflite
    TFLITE_AVAILABLE = True
    print("✅ 使用 tflite-runtime")
except ImportError:
    try:
        import tensorflow as tf
        tflite = tf.lite
        TFLITE_AVAILABLE = True
        print("✅ 使用 TensorFlow")
    except ImportError:
        pass

# ── 模型路径 ──────────────────────────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "mobilenet_v2_1.0_224_quant.tflite")
LABELS_PATH = os.path.join(MODEL_DIR, "labels_mobilenet_quant_v1_224.txt")

# ImageNet 标签下载地址
LABELS_URL = "https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt"

# ── 内置简化标签（离线演示用）────────────────────────────────────────────────
DEMO_LABELS = [
    "背景", "金鱼", "大白鲨", "虎鲨", "锤头鲨", "电鳐", "鳐鱼",
    "公鸡", "母鸡", "鸵鸟", "孔雀", "鹦鹉", "火烈鸟", "天鹅",
    "猫", "狗", "狼", "狐狸", "熊", "大熊猫", "猴子",
    "大象", "长颈鹿", "斑马", "狮子", "老虎", "豹子",
    "苹果", "香蕉", "橙子", "草莓", "西瓜",
    "汽车", "自行车", "摩托车", "飞机", "船",
    "椅子", "桌子", "电脑", "手机", "书本",
]


# ─────────────────────────────────────────────────────────────────────────────
# 标签加载
# ─────────────────────────────────────────────────────────────────────────────

def load_labels(path=None):
    """加载 ImageNet 标签"""
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    return DEMO_LABELS


# ─────────────────────────────────────────────────────────────────────────────
# TFLite 分类器
# ─────────────────────────────────────────────────────────────────────────────

class TFLiteClassifier:
    """TensorFlow Lite 图像分类器"""

    def __init__(self, model_path, labels, input_size=224):
        self.labels = labels
        self.input_size = input_size
        self.interpreter = None
        self._load_model(model_path)

    def _load_model(self, model_path):
        if not TFLITE_AVAILABLE:
            print("❌ TFLite 不可用")
            return
        if not os.path.exists(model_path):
            print(f"❌ 模型文件不存在: {model_path}")
            print("   请下载 MobileNetV2 TFLite 模型")
            return
        try:
            self.interpreter = tflite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            print(f"✅ 模型加载成功: {os.path.basename(model_path)}")
            print(f"   输入形状: {self.input_details[0]['shape']}")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")

    def preprocess(self, image):
        """图像预处理"""
        if not NUMPY_AVAILABLE or not CV2_AVAILABLE:
            return None
        img = cv2.resize(image, (self.input_size, self.input_size))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.expand_dims(img, axis=0).astype(np.uint8)
        return img

    def classify(self, image, top_k=5):
        """
        分类图像
        返回: [(label, confidence), ...]
        """
        if self.interpreter is None:
            return []

        input_data = self.preprocess(image)
        if input_data is None:
            return []

        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()

        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        # 量化模型输出为 uint8，转换为概率
        if output_data.dtype == np.uint8:
            output_data = output_data / 255.0

        top_indices = np.argsort(output_data)[::-1][:top_k]
        results = []
        for idx in top_indices:
            label = self.labels[idx] if idx < len(self.labels) else f"类别{idx}"
            confidence = float(output_data[idx])
            results.append((label, confidence))
        return results


# ─────────────────────────────────────────────────────────────────────────────
# OpenCV DNN 分类器（备选方案）
# ─────────────────────────────────────────────────────────────────────────────

class OpenCVDNNClassifier:
    """使用 OpenCV DNN 模块进行图像分类"""

    def __init__(self, labels):
        self.labels = labels
        self.net = None
        # 尝试加载 GoogLeNet（OpenCV 自带示例）
        self._try_load_googlenet()

    def _try_load_googlenet(self):
        """尝试加载 GoogLeNet 模型"""
        if not CV2_AVAILABLE:
            return
        # OpenCV 示例模型路径
        model_paths = [
            "/usr/share/opencv4/samples/data/bvlc_googlenet.caffemodel",
            os.path.join(MODEL_DIR, "bvlc_googlenet.caffemodel"),
        ]
        proto_paths = [
            "/usr/share/opencv4/samples/data/bvlc_googlenet.prototxt",
            os.path.join(MODEL_DIR, "bvlc_googlenet.prototxt"),
        ]
        for model, proto in zip(model_paths, proto_paths):
            if os.path.exists(model) and os.path.exists(proto):
                try:
                    self.net = cv2.dnn.readNetFromCaffe(proto, model)
                    print(f"✅ GoogLeNet 加载成功")
                    return
                except Exception as e:
                    print(f"  加载失败: {e}")

    def classify(self, image, top_k=5):
        if self.net is None or not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return []
        blob = cv2.dnn.blobFromImage(image, 1.0, (224, 224),
                                     (104, 117, 123))
        self.net.setInput(blob)
        preds = self.net.forward()[0]
        top_indices = np.argsort(preds)[::-1][:top_k]
        return [(self.labels[i] if i < len(self.labels) else f"类别{i}",
                 float(preds[i])) for i in top_indices]


# ─────────────────────────────────────────────────────────────────────────────
# 模拟分类器（无需任何 ML 库）
# ─────────────────────────────────────────────────────────────────────────────

class SimulatedClassifier:
    """模拟分类器，用于演示和测试"""

    def __init__(self, labels):
        self.labels = labels
        import random
        self._random = random

    def classify(self, image=None, top_k=5):
        """返回模拟的分类结果"""
        import random
        # 随机选取 top_k 个标签，生成递减的置信度
        chosen = random.sample(self.labels[:min(40, len(self.labels))], top_k)
        scores = sorted([random.uniform(0.1, 0.9) for _ in range(top_k)], reverse=True)
        # 归一化
        total = sum(scores)
        scores = [s / total for s in scores]
        return list(zip(chosen, scores))


# ─────────────────────────────────────────────────────────────────────────────
# 主功能
# ─────────────────────────────────────────────────────────────────────────────

def classify_image_file(image_path, classifier, top_k=5):
    """对图片文件进行分类"""
    if not CV2_AVAILABLE:
        print("❌ 需要 OpenCV: pip3 install opencv-python")
        return

    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ 无法读取图片: {image_path}")
        return

    print(f"\n📷 分类图片: {image_path}")
    print(f"   尺寸: {img.shape[1]}×{img.shape[0]}")

    start = time.time()
    results = classifier.classify(img, top_k=top_k)
    elapsed = (time.time() - start) * 1000

    print(f"\n🏆 Top-{top_k} 分类结果（推理耗时 {elapsed:.1f}ms）:")
    print("  " + "─" * 35)
    for i, (label, conf) in enumerate(results):
        bar = "█" * int(conf * 20)
        print(f"  {i+1}. {label:<20s} {conf*100:5.1f}%  {bar}")


def realtime_classify(classifier, camera_id=0):
    """实时摄像头分类"""
    if not CV2_AVAILABLE:
        print("❌ 需要 OpenCV")
        return

    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"❌ 无法打开摄像头 {camera_id}")
        return

    print("\n📷 实时图像分类（按 q 退出，按 s 截图分类）")
    labels = load_labels()
    frame_count = 0
    classify_every = 10  # 每 10 帧分类一次

    last_results = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % classify_every == 0:
            start = time.time()
            last_results = classifier.classify(frame, top_k=3)
            elapsed = (time.time() - start) * 1000

            # 在画面上显示结果
            y_offset = 30
            for i, (label, conf) in enumerate(last_results):
                text = f"{i+1}. {label}: {conf*100:.1f}%"
                cv2.putText(frame, text, (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_offset += 30

            cv2.putText(frame, f"推理: {elapsed:.0f}ms", (10, y_offset + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        # 显示上次结果
        if last_results:
            y_offset = 30
            for i, (label, conf) in enumerate(last_results):
                text = f"{i+1}. {label}: {conf*100:.1f}%"
                cv2.putText(frame, text, (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_offset += 30

        cv2.imshow("图像分类 (q退出)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            fname = f"classify_{int(time.time())}.jpg"
            cv2.imwrite(fname, frame)
            print(f"截图已保存: {fname}")

    cap.release()
    cv2.destroyAllWindows()


def demo_mode():
    """演示模式"""
    print("\n📖 图像分类演示（模拟模式）")
    print("─" * 40)
    print("  在实际使用中，此功能会对摄像头画面进行实时分类")
    print("\n  支持的模型:")
    print("  • MobileNetV2 (TFLite) - 推荐树莓派使用，速度快")
    print("  • GoogLeNet (OpenCV DNN) - 无需 TensorFlow")
    print("  • EfficientNet-Lite - 精度更高")
    print("\n  模拟分类结果:")

    labels = load_labels()
    classifier = SimulatedClassifier(labels)
    results = classifier.classify(top_k=5)

    print("\n  🏆 Top-5 分类结果（模拟）:")
    print("  " + "─" * 35)
    for i, (label, conf) in enumerate(results):
        bar = "█" * int(conf * 20)
        print(f"  {i+1}. {label:<20s} {conf*100:5.1f}%  {bar}")

    print("\n  💡 提示:")
    print("  • 树莓派 4B 运行 MobileNetV2 约 50-100ms/帧")
    print("  • 量化模型（INT8）比浮点模型快 2-4 倍")
    print("  • 可结合 GPIO 实现物体识别自动控制")


def main():
    print("=" * 50)
    print("🖼️  图像分类（AI/ML）")
    print("=" * 50)

    labels = load_labels(LABELS_PATH)
    print(f"  标签数量: {len(labels)}")

    # 选择分类器
    if TFLITE_AVAILABLE and os.path.exists(MODEL_PATH):
        classifier = TFLiteClassifier(MODEL_PATH, labels)
        print("  分类器: TFLite MobileNetV2")
    elif CV2_AVAILABLE:
        classifier = OpenCVDNNClassifier(labels)
        if classifier.net:
            print("  分类器: OpenCV DNN GoogLeNet")
        else:
            print("  分类器: 模拟模式（未找到模型文件）")
            classifier = SimulatedClassifier(labels)
    else:
        print("  分类器: 模拟模式")
        classifier = SimulatedClassifier(labels)

    print("\n选择模式:")
    print("1. 实时摄像头分类")
    print("2. 分类图片文件")
    print("3. 演示模式")

    choice = input("\n请选择 (1-3, 默认3): ").strip() or "3"

    if choice == "1":
        realtime_classify(classifier)
    elif choice == "2":
        path = input("图片路径: ").strip()
        if os.path.exists(path):
            classify_image_file(path, classifier)
        else:
            print(f"❌ 文件不存在: {path}")
    else:
        demo_mode()


if __name__ == "__main__":
    main()