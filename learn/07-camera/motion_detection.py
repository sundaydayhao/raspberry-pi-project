#!/usr/bin/env python3
"""
摄像头运动检测
通过比较帧差异检测画面中的运动

安装依赖:
  pip3 install opencv-python

学习要点:
  - 帧差法运动检测
  - 背景减除算法
  - 轮廓检测
  - 运动区域标注
"""

import os
import time
import sys
from datetime import datetime

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("安装: pip3 install opencv-python")

OUTPUT_DIR = "motion_captures"

def ensure_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def frame_diff_detection(camera_id=0, sensitivity=25, min_area=500):
    """
    帧差法运动检测
    sensitivity: 像素差异阈值 (越小越灵敏)
    min_area: 最小运动区域面积
    """
    if not CV2_AVAILABLE:
        print("需要 OpenCV")
        return

    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"无法打开摄像头 {camera_id}")
        return

    ensure_dir()
    print("帧差法运动检测 (按 q 退出, 按 s 截图)")
    print(f"灵敏度: {sensitivity}, 最小区域: {min_area}px²\n")

    prev_frame = None
    motion_count = 0
    frame_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if prev_frame is None:
            prev_frame = gray
            continue

        # 计算帧差
        frame_delta = cv2.absdiff(prev_frame, gray)
        thresh = cv2.threshold(frame_delta, sensitivity, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # 查找轮廓
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) < min_area:
                continue

            motion_detected = True
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if motion_detected:
            motion_count += 1
            cv2.putText(frame, "运动检测!", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # 显示统计
        fps = frame_count / (time.time() - start_time)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(frame, f"运动次数: {motion_count}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # 显示差异图
        cv2.imshow('运动检测 (q退出)', frame)
        cv2.imshow('差异图', frame_delta)

        prev_frame = gray

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s') and motion_detected:
            filename = os.path.join(OUTPUT_DIR, f"motion_{int(time.time())}.jpg")
            cv2.imwrite(filename, frame)
            print(f"截图: {filename}")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n共检测到 {motion_count} 次运动")

def background_subtraction(camera_id=0):
    """
    背景减除法（更精确）
    使用 MOG2 算法
    """
    if not CV2_AVAILABLE:
        print("需要 OpenCV")
        return

    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"无法打开摄像头 {camera_id}")
        return

    # 创建背景减除器
    backSub = cv2.createBackgroundSubtractorMOG2(
        history=500, varThreshold=50, detectShadows=True
    )

    ensure_dir()
    print("背景减除法运动检测 (按 q 退出)")
    print("等待背景学习 (约3秒)...\n")

    motion_count = 0
    frame_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # 应用背景减除
        fg_mask = backSub.apply(frame)

        # 去除阴影（灰色区域）
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # 形态学处理
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)

        # 查找轮廓
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) < 1000:
                continue
            motion_detected = True
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if motion_detected:
            motion_count += 1
            cv2.putText(frame, "运动!", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        fps = frame_count / (time.time() - start_time)
        cv2.putText(frame, f"FPS:{fps:.1f} 运动:{motion_count}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow('背景减除运动检测 (q退出)', frame)
        cv2.imshow('前景掩码', fg_mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def motion_triggered_capture(camera_id=0, sensitivity=30, cooldown=5):
    """
    运动触发自动拍照
    检测到运动时自动保存图片
    """
    if not CV2_AVAILABLE:
        print("需要 OpenCV")
        return

    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"无法打开摄像头 {camera_id}")
        return

    ensure_dir()
    print(f"运动触发拍照模式 (冷却: {cooldown}秒, Ctrl+C 停止)")

    prev_frame = None
    last_capture = 0
    capture_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if prev_frame is None:
                prev_frame = gray
                continue

            delta = cv2.absdiff(prev_frame, gray)
            thresh = cv2.threshold(delta, sensitivity, 255, cv2.THRESH_BINARY)[1]
            motion_pixels = cv2.countNonZero(thresh)

            now = time.time()
            if motion_pixels > 5000 and (now - last_capture) > cooldown:
                last_capture = now
                capture_count += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(OUTPUT_DIR, f"motion_{timestamp}.jpg")
                cv2.imwrite(filename, frame)
                print(f"  [{timestamp}] 检测到运动! 已保存: {filename} (第{capture_count}张)")

            prev_frame = gray
            time.sleep(0.1)

    except KeyboardInterrupt:
        print(f"\n已停止，共拍摄 {capture_count} 张")
    finally:
        cap.release()

def main():
    print("=" * 40)
    print("🎥 摄像头运动检测")
    print("=" * 40)

    if not CV2_AVAILABLE:
        print("需要安装 OpenCV: pip3 install opencv-python")
        return

    print("\n选择模式:")
    print("1. 帧差法检测（实时显示）")
    print("2. 背景减除法（更精确）")
    print("3. 运动触发自动拍照")

    choice = input("\n请选择 (1-3): ").strip()

    if choice == '1':
        frame_diff_detection()
    elif choice == '2':
        background_subtraction()
    elif choice == '3':
        motion_triggered_capture()
    else:
        frame_diff_detection()

if __name__ == "__main__":
    main()