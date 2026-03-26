#!/usr/bin/env python3
"""
手势识别与控制
使用 MediaPipe 或 OpenCV 识别手势，联动 GPIO 控制硬件

安装依赖:
  pip3 install mediapipe opencv-python

学习要点:
  - MediaPipe Hands 关键点检测
  - 手势特征提取（手指状态）
  - 手势→GPIO 动作映射
  - 实时视频处理
"""

import time
import math

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️  未找到 OpenCV，请安装: pip3 install opencv-python")

try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False
    print("⚠️  未找到 MediaPipe，请安装: pip3 install mediapipe")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False

# ── GPIO 引脚映射（手势→动作）────────────────────────────────────────────────
GESTURE_GPIO_MAP = {
    "✊ 握拳":    {"pin": 17, "action": "关闭 LED"},
    "✋ 张开":    {"pin": 17, "action": "打开 LED"},
    "☝ 一指":    {"pin": 18, "action": "LED 闪烁"},
    "✌ 剪刀":    {"pin": 27, "action": "蜂鸣器响"},
    "👍 点赞":   {"pin": 22, "action": "舵机转动"},
    "🤙 打电话": {"pin": 23, "action": "拍照"},
}

# ── 手指关键点索引（MediaPipe）────────────────────────────────────────────────
# 每根手指的指尖和第二关节索引
FINGER_TIPS = [4, 8, 12, 16, 20]    # 拇指、食指、中指、无名指、小指指尖
FINGER_PIP  = [3, 6, 10, 14, 18]    # 第二关节


# ─────────────────────────────────────────────────────────────────────────────
# GPIO 控制
# ─────────────────────────────────────────────────────────────────────────────

_gpio_initialized = False

def setup_gpio():
    global _gpio_initialized
    if RPI_AVAILABLE and not _gpio_initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for gesture_info in GESTURE_GPIO_MAP.values():
            GPIO.setup(gesture_info["pin"], GPIO.OUT, initial=GPIO.LOW)
        _gpio_initialized = True

def execute_gpio_action(gesture_name):
    """根据手势执行 GPIO 动作"""
    if gesture_name not in GESTURE_GPIO_MAP:
        return
    info = GESTURE_GPIO_MAP[gesture_name]
    pin = info["pin"]
    action = info["action"]

    if not RPI_AVAILABLE:
        print(f"  [模拟] GPIO{pin} → {action}")
        return

    if "打开" in action:
        GPIO.output(pin, GPIO.HIGH)
    elif "关闭" in action:
        GPIO.output(pin, GPIO.LOW)
    elif "闪烁" in action:
        for _ in range(3):
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.1)
    elif "蜂鸣" in action:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(pin, GPIO.LOW)

def cleanup_gpio():
    if RPI_AVAILABLE and _gpio_initialized:
        GPIO.cleanup()


# ─────────────────────────────────────────────────────────────────────────────
# 手势识别（MediaPipe）
# ─────────────────────────────────────────────────────────────────────────────

class MediaPipeGestureRecognizer:
    """基于 MediaPipe Hands 的手势识别器"""

    def __init__(self):
        if not MP_AVAILABLE:
            raise RuntimeError("需要安装 mediapipe: pip3 install mediapipe")
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )

    def get_finger_states(self, landmarks):
        """
        获取每根手指的伸展状态
        返回: [拇指, 食指, 中指, 无名指, 小指]  True=伸展, False=弯曲
        """
        states = []

        # 拇指：比较指尖 x 坐标与第二关节（左右手方向不同，简化处理）
        thumb_tip = landmarks[FINGER_TIPS[0]]
        thumb_ip  = landmarks[FINGER_PIP[0]]
        states.append(thumb_tip.x < thumb_ip.x)  # 假设右手

        # 其余四指：指尖 y 坐标小于第二关节 y 坐标（屏幕坐标向下为正）
        for i in range(1, 5):
            tip = landmarks[FINGER_TIPS[i]]
            pip = landmarks[FINGER_PIP[i]]
            states.append(tip.y < pip.y)

        return states  # [thumb, index, middle, ring, pinky]

    def classify_gesture(self, finger_states):
        """根据手指状态分类手势"""
        thumb, index, middle, ring, pinky = finger_states
        fingers_up = sum([index, middle, ring, pinky])

        if not any(finger_states):
            return "✊ 握拳"
        if all([index, middle, ring, pinky]) and thumb:
            return "✋ 张开"
        if all([index, middle, ring, pinky]) and not thumb:
            return "✋ 张开"
        if index and not middle and not ring and not pinky:
            return "☝ 一指"
        if index and middle and not ring and not pinky:
            return "✌ 剪刀"
        if thumb and not index and not middle and not ring and not pinky:
            return "👍 点赞"
        if thumb and not index and not middle and not ring and pinky:
            return "🤙 打电话"
        if fingers_up == 3 and index and middle and ring:
            return "三指"
        if fingers_up == 4:
            return "四指"
        return "未知手势"

    def process_frame(self, frame):
        """
        处理一帧图像
        返回: (gesture_name, annotated_frame)
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        gesture = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 绘制关键点
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )
                # 识别手势
                finger_states = self.get_finger_states(hand_landmarks.landmark)
                gesture = self.classify_gesture(finger_states)

                # 在画面上显示手势
                h, w, _ = frame.shape
                cv2.putText(frame, gesture, (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

                # 显示手指状态
                labels = ["拇", "食", "中", "无", "小"]
                for i, (state, label) in enumerate(zip(finger_states, labels)):
                    color = (0, 255, 0) if state else (0, 0, 255)
                    cv2.putText(frame, label, (10 + i * 30, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        return gesture, frame

    def close(self):
        self.hands.close()


# ─────────────────────────────────────────────────────────────────────────────
# 简单手势识别（仅用 OpenCV，无需 MediaPipe）
# ─────────────────────────────────────────────────────────────────────────────

class SimpleGestureRecognizer:
    """
    基于肤色分割和轮廓分析的简单手势识别
    无需 MediaPipe，但精度较低
    """

    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=False
        ) if CV2_AVAILABLE else None

    def _skin_mask(self, frame):
        """提取肤色区域"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = (0, 20, 70)
        upper = (20, 255, 255)
        mask = cv2.inRange(hsv, lower, upper)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    def count_fingers(self, frame):
        """
        通过凸包缺陷计算伸出手指数量
        返回: (finger_count, annotated_frame)
        """
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return 0, frame

        mask = self._skin_mask(frame)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0, frame

        # 取最大轮廓
        max_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(max_contour) < 5000:
            return 0, frame

        # 凸包和凸包缺陷
        hull = cv2.convexHull(max_contour, returnPoints=False)
        try:
            defects = cv2.convexityDefects(max_contour, hull)
        except Exception:
            return 0, frame

        finger_count = 0
        if defects is not None:
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(max_contour[s][0])
                end   = tuple(max_contour[e][0])
                far   = tuple(max_contour[f][0])

                # 计算夹角（余弦定理）
                a = math.dist(start, end)
                b = math.dist(far, start)
                c = math.dist(far, end)
                if b * c == 0:
                    continue
                angle = math.acos((b**2 + c**2 - a**2) / (2 * b * c))

                # 夹角小于 90° 且缺陷深度足够，认为是手指间隙
                if angle < math.pi / 2 and d > 10000:
                    finger_count += 1
                    cv2.circle(frame, far, 5, (0, 0, 255), -1)

        finger_count = min(finger_count + 1, 5)  # 缺陷数+1 = 手指数

        # 绘制轮廓
        cv2.drawContours(frame, [max_contour], -1, (0, 255, 0), 2)
        cv2.putText(frame, f"手指数: {finger_count}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        return finger_count, frame

    def classify_gesture(self, finger_count):
        """根据手指数量分类手势"""
        mapping = {
            0: "✊ 握拳",
            1: "☝ 一指",
            2: "✌ 剪刀",
            3: "三指",
            4: "四指",
            5: "✋ 张开",
        }
        return mapping.get(finger_count, "未知")


# ─────────────────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────────────────

def run_mediapipe_recognition():
    """使用 MediaPipe 进行手势识别"""
    if not CV2_AVAILABLE or not MP_AVAILABLE:
        print("❌ 需要安装: pip3 install opencv-python mediapipe")
        return

    recognizer = MediaPipeGestureRecognizer()
    setup_gpio()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return

    print("\n✋ MediaPipe 手势识别（按 q 退出）")
    print("  支持手势: 握拳、张开、一指、剪刀、点赞、打电话")

    last_gesture = None
    gesture_hold_time = 0
    HOLD_THRESHOLD = 1.0  # 手势保持 1 秒才触发动作

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)  # 镜像翻转
            gesture, frame = recognizer.process_frame(frame)

            # 手势稳定检测
            if gesture:
                if gesture == last_gesture:
                    hold_duration = time.time() - gesture_hold_time
                    if hold_duration >= HOLD_THRESHOLD:
                        execute_gpio_action(gesture)
                        # 显示触发状态
                        cv2.putText(frame, "触发!", (200, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                else:
                    last_gesture = gesture
                    gesture_hold_time = time.time()

            cv2.imshow("手势识别 (q退出)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        recognizer.close()
        cleanup_gpio()


def run_simple_recognition():
    """使用 OpenCV 肤色分割进行手势识别"""
    if not CV2_AVAILABLE:
        print("❌ 需要安装: pip3 install opencv-python")
        return

    recognizer = SimpleGestureRecognizer()
    setup_gpio()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return

    print("\n✋ 简单手势识别（肤色分割，按 q 退出）")
    print("  将手放在摄像头前，背景尽量简单")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            finger_count, frame = recognizer.count_fingers(frame)
            gesture = recognizer.classify_gesture(finger_count)

            execute_gpio_action(gesture)

            cv2.imshow("简单手势识别 (q退出)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        cleanup_gpio()


def demo_mode():
    """演示模式（无需摄像头）"""
    print("\n📖 手势识别演示")
    print("─" * 40)
    print("  手势识别原理：")
    print("  1. 摄像头捕获手部图像")
    print("  2. MediaPipe 检测 21 个手部关键点")
    print("  3. 根据关键点位置判断手指伸展状态")
    print("  4. 匹配预定义手势规则")
    print("  5. 触发对应 GPIO 动作")
    print()
    print("  支持的手势及对应动作:")
    print("  " + "─" * 35)
    for gesture, info in GESTURE_GPIO_MAP.items():
        print(f"  {gesture:<15s} → GPIO{info['pin']} {info['action']}")

    print()
    print("  模拟手势序列:")
    import random
    gestures = list(GESTURE_GPIO_MAP.keys())
    for i in range(8):
        g = random.choice(gestures)
        print(f"  [{i+1}] 检测到: {g}")
        execute_gpio_action(g)
        time.sleep(0.5)

    print()
    print("  💡 MediaPipe 手部关键点（21个）:")
    print("  拇指: 1-4  食指: 5-8  中指: 9-12")
    print("  无名指: 13-16  小指: 17-20  手腕: 0")


def main():
    print("=" * 50)
    print("✋ 手势识别与 GPIO 控制（AI/ML）")
    print("=" * 50)

    print("\n选择模式:")
    print("1. MediaPipe 手势识别（推荐，需要 mediapipe）")
    print("2. 简单肤色分割识别（仅需 OpenCV）")
    print("3. 演示模式（无需摄像头）")

    choice = input("\n请选择 (1-3, 默认3): ").strip() or "3"

    if choice == "1":
        run_mediapipe_recognition()
    elif choice == "2":
        run_simple_recognition()
    else:
        demo_mode()


if __name__ == "__main__":
    main()