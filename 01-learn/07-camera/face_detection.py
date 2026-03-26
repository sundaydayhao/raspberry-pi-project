#!/usr/bin/env python3
"""
人脸检测
使用 OpenCV Haar 级联分类器检测人脸

安装依赖:
  pip3 install opencv-python

学习要点:
  - Haar 级联分类器
  - 实时视频处理
  - 图像标注
"""

import os
import time
import sys

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️  未找到 OpenCV")
    print("   安装: pip3 install opencv-python")

def get_face_cascade():
    """获取人脸检测分类器"""
    # OpenCV 内置的 Haar 级联文件
    cascade_paths = [
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml',
        '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
        '/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
    ]

    for path in cascade_paths:
        if os.path.exists(path):
            return cv2.CascadeClassifier(path)

    print("❌ 未找到人脸分类器文件")
    return None

def detect_faces_in_image(image_path, output_path=None):
    """检测图片中的人脸"""
    if not CV2_AVAILABLE:
        print("需要 OpenCV")
        return

    img = cv2.imread(image_path)
    if img is None:
        print(f"无法读取图片: {image_path}")
        return

    face_cascade = get_face_cascade()
    if face_cascade is None:
        return

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    print(f"检测到 {len(faces)} 张人脸")

    for i, (x, y, w, h) in enumerate(faces):
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(img, f"Face {i+1}", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    if output_path is None:
        output_path = image_path.replace('.', '_detected.')

    cv2.imwrite(output_path, img)
    print(f"结果已保存: {output_path}")
    return len(faces)

def realtime_face_detection(camera_id=0):
    """实时人脸检测"""
    if not CV2_AVAILABLE:
        print("需要 OpenCV")
        return

    face_cascade = get_face_cascade()
    eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
    eye_cascade = cv2.CascadeClassifier(eye_cascade_path) if os.path.exists(eye_cascade_path) else None

    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"无法打开摄像头 {camera_id}")
        return

    print("实时人脸检测 (按 q 退出, 按 s 截图)")
    frame_count = 0
    face_count_total = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 检测人脸
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        face_count_total += len(faces)

        for (x, y, w, h) in faces:
            # 绘制人脸框
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # 检测眼睛
            if eye_cascade:
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = frame[y:y+h, x:x+w]
                eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3)
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (255, 0, 0), 2)

        # 显示信息
        fps = frame_count / (time.time() - start_time)
        cv2.putText(frame, f"人脸: {len(faces)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.imshow('人脸检测 (q退出)', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"face_detect_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            print(f"截图已保存: {filename}")

    cap.release()
    cv2.destroyAllWindows()

    elapsed = time.time() - start_time
    print(f"\n统计: {frame_count} 帧, {elapsed:.1f}秒, 平均 {frame_count/elapsed:.1f} FPS")

def count_faces_demo():
    """人脸计数演示（无需摄像头）"""
    print("\n人脸检测演示（模拟模式）")
    print("在实际使用中，此功能会实时检测摄像头画面中的人脸")
    print("\n功能说明:")
    print("  - 使用 Haar 级联分类器")
    print("  - 可检测正面人脸")
    print("  - 可同时检测眼睛")
    print("  - 实时显示 FPS")
    print("  - 支持截图保存")

def main():
    print("=" * 40)
    print("👤 人脸检测")
    print("=" * 40)

    if not CV2_AVAILABLE:
        print("\n需要安装 OpenCV:")
        print("  pip3 install opencv-python")
        return

    print("\n选择模式:")
    print("1. 实时人脸检测（摄像头）")
    print("2. 检测图片中的人脸")
    print("3. 功能说明")

    choice = input("\n请选择 (1-3): ").strip()

    if choice == '1':
        realtime_face_detection()
    elif choice == '2':
        path = input("图片路径: ").strip()
        if os.path.exists(path):
            detect_faces_in_image(path)
        else:
            print(f"文件不存在: {path}")
    elif choice == '3':
        count_faces_demo()
    else:
        realtime_face_detection()

if __name__ == "__main__":
    main()