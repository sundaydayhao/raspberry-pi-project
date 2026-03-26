#!/usr/bin/env python3
"""
摄像头网页直播系统
Camera Web Streaming System

功能：
- 实时视频流（MJPEG）通过浏览器查看
- 远程拍照（网页按钮触发）
- 照片画廊（最近20张）
- 运动检测（帧差法，网页显示报警）
- 人脸检测（OpenCV Haar级联）
- 画面参数调节（亮度/对比度）
- PC/手机均可访问

依赖安装：
  pip3 install flask opencv-python

访问地址：http://<树莓派IP>:5005
"""

import cv2
import time
import base64
import threading
import numpy as np
from datetime import datetime
from collections import deque
from flask import Flask, render_template, Response, jsonify, request

# ==================== 配置 ====================
CAMERA_INDEX = 0        # 摄像头索引（0=默认摄像头）
STREAM_WIDTH = 640
STREAM_HEIGHT = 480
STREAM_FPS = 20
JPEG_QUALITY = 75       # MJPEG压缩质量（1-100）

MAX_PHOTOS = 20         # 画廊最多保存照片数
MOTION_THRESHOLD = 3000 # 运动检测灵敏度（像素差异面积）

# ==================== 全局状态 ====================
camera_state = {
    'streaming': False,
    'motion_detect': True,
    'face_detect': False,
    'motion_alarm': False,
    'brightness': 0,      # -100 ~ 100
    'contrast': 1.0,      # 0.5 ~ 2.0
    'fps': 0,
    'resolution': f'{STREAM_WIDTH}x{STREAM_HEIGHT}',
    'photo_count': 0,
    'motion_count': 0,
}

photo_gallery = deque(maxlen=MAX_PHOTOS)
motion_log = deque(maxlen=30)
frame_lock = threading.Lock()
latest_frame = None

# ==================== 摄像头初始化 ====================
try:
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    OPENCV_AVAILABLE = True
except Exception:
    OPENCV_AVAILABLE = False

def open_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, STREAM_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, STREAM_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, STREAM_FPS)
    return cap

# ==================== 帧处理 ====================
def apply_adjustments(frame):
    """应用亮度/对比度调整"""
    b = camera_state['brightness']
    c = camera_state['contrast']
    if b != 0 or c != 1.0:
        frame = cv2.convertScaleAbs(frame, alpha=c, beta=b)
    return frame

def detect_faces(frame):
    """人脸检测，返回带标注的帧"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
    count = 0
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, 'Face', (x, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        count += 1
    if count > 0:
        cv2.putText(frame, f'Faces: {count}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    return frame

prev_gray = None
def detect_motion(frame):
    """运动检测（帧差法）"""
    global prev_gray
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    motion_detected = False
    if prev_gray is not None:
        diff = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            if cv2.contourArea(c) > MOTION_THRESHOLD:
                motion_detected = True
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        if motion_detected:
            cv2.putText(frame, '⚠ MOTION', (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    prev_gray = gray
    return frame, motion_detected

def add_overlay(frame):
    """添加时间戳水印"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    h, w = frame.shape[:2]
    cv2.putText(frame, ts, (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    return frame

# ==================== 视频采集线程 ====================
def camera_thread():
    global latest_frame
    cap = open_camera()
    if not cap.isOpened():
        print("⚠ 摄像头未找到，使用测试画面")
        cap = None

    fps_counter = 0
    fps_timer = time.time()
    camera_state['streaming'] = True

    while True:
        if cap and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
        else:
            # 生成测试画面
            frame = np.zeros((STREAM_HEIGHT, STREAM_WIDTH, 3), dtype=np.uint8)
            frame[:] = (30, 30, 50)
            ts = datetime.now().strftime('%H:%M:%S')
            cv2.putText(frame, 'No Camera - Test Mode', (120, 220),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (100, 200, 255), 2)
            cv2.putText(frame, ts, (220, 270),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 1)
            time.sleep(1.0 / STREAM_FPS)

        frame = apply_adjustments(frame)

        if camera_state['motion_detect']:
            frame, motion = detect_motion(frame)
            if motion and not camera_state['motion_alarm']:
                camera_state['motion_alarm'] = True
                camera_state['motion_count'] += 1
                motion_log.appendleft({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'msg': '检测到运动'
                })
                # 自动拍照
                _save_photo(frame.copy(), trigger='自动（运动触发）')
            elif not motion:
                camera_state['motion_alarm'] = False

        if camera_state['face_detect']:
            frame = detect_faces(frame)

        frame = add_overlay(frame)

        with frame_lock:
            latest_frame = frame.copy()

        fps_counter += 1
        if time.time() - fps_timer >= 1.0:
            camera_state['fps'] = fps_counter
            fps_counter = 0
            fps_timer = time.time()

    if cap:
        cap.release()

def _save_photo(frame, trigger='手动'):
    """保存照片到画廊"""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    b64 = base64.b64encode(buf).decode('utf-8')
    photo_gallery.appendleft({
        'id': camera_state['photo_count'] + 1,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'filename': f'photo_{ts}.jpg',
        'data': b64,
        'trigger': trigger,
    })
    camera_state['photo_count'] += 1
    print(f"📷 拍照：photo_{ts}.jpg [{trigger}]")

# ==================== MJPEG 流生成器 ====================
def generate_stream():
    while True:
        with frame_lock:
            frame = latest_frame
        if frame is None:
            time.sleep(0.05)
            continue
        _, buf = cv2.imencode('.jpg', frame,
                              [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buf.tobytes() + b'\r\n')
        time.sleep(1.0 / STREAM_FPS)

# ==================== Flask Web服务器 ====================
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('camera_web_stream.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def api_status():
    return jsonify(camera_state)

@app.route('/api/capture', methods=['POST'])
def api_capture():
    with frame_lock:
        frame = latest_frame
    if frame is None:
        return jsonify({'success': False, 'message': '无画面'})
    _save_photo(frame.copy(), trigger='手动拍照')
    return jsonify({'success': True, 'message': f'已拍照，共{camera_state["photo_count"]}张'})

@app.route('/api/gallery')
def api_gallery():
    return jsonify([{
        'id': p['id'], 'time': p['time'],
        'data': p['data'], 'trigger': p['trigger']
    } for p in photo_gallery])

@app.route('/api/motion_log')
def api_motion_log():
    return jsonify(list(motion_log))

@app.route('/api/toggle_motion', methods=['POST'])
def api_toggle_motion():
    camera_state['motion_detect'] = not camera_state['motion_detect']
    return jsonify({'motion_detect': camera_state['motion_detect']})

@app.route('/api/toggle_face', methods=['POST'])
def api_toggle_face():
    camera_state['face_detect'] = not camera_state['face_detect']
    return jsonify({'face_detect': camera_state['face_detect']})

@app.route('/api/adjust', methods=['POST'])
def api_adjust():
    data = request.get_json()
    if 'brightness' in data:
        camera_state['brightness'] = max(-100, min(100, int(data['brightness'])))
    if 'contrast' in data:
        camera_state['contrast'] = max(0.5, min(2.0, float(data['contrast'])))
    return jsonify({'success': True})

@app.route('/api/clear_gallery', methods=['POST'])
def api_clear_gallery():
    photo_gallery.clear()
    camera_state['photo_count'] = 0
    return jsonify({'message': '画廊已清空'})

# ==================== 主程序 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("📷 摄像头网页直播系统")
    print("=" * 50)

    t = threading.Thread(target=camera_thread, daemon=True)
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

    print(f"🌐 直播地址：http://{ip}:5005")
    print(f"   手机访问：确保与树莓派在同一WiFi")
    print("按 Ctrl+C 停止")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5005, debug=False, threaded=True)