#!/usr/bin/env python3
"""
摄像头拍照
使用 Pi Camera 或 USB 摄像头拍照

支持:
  - Raspberry Pi Camera Module (picamera2)
  - USB 摄像头 (OpenCV)

学习要点:
  - 摄像头初始化
  - 图像捕获和保存
  - 图像参数调整
"""

import os
import time
import sys
from datetime import datetime

# 尝试导入摄像头库
CAMERA_TYPE = None

try:
    from picamera2 import Picamera2
    CAMERA_TYPE = 'picamera2'
    print("✅ 使用 picamera2")
except ImportError:
    pass

if CAMERA_TYPE is None:
    try:
        import cv2
        CAMERA_TYPE = 'opencv'
        print("✅ 使用 OpenCV")
    except ImportError:
        pass

if CAMERA_TYPE is None:
    print("⚠️  未找到摄像头库，使用模拟模式")
    print("   安装 picamera2: pip3 install picamera2")
    print("   安装 OpenCV: pip3 install opencv-python")

OUTPUT_DIR = "photos"

def ensure_output_dir():
    """确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_filename(prefix="photo", ext="jpg"):
    """生成带时间戳的文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUTPUT_DIR, f"{prefix}_{timestamp}.{ext}")

class PiCamera2Capture:
    """使用 picamera2 拍照"""

    def __init__(self):
        self.camera = Picamera2()
        config = self.camera.create_still_configuration(
            main={"size": (1920, 1080)},
            lores={"size": (640, 480)},
            display="lores"
        )
        self.camera.configure(config)
        self.camera.start()
        time.sleep(2)  # 等待自动曝光稳定
        print("✅ Pi Camera 初始化完成")

    def capture(self, filename=None):
        if filename is None:
            filename = generate_filename()
        self.camera.capture_file(filename)
        return filename

    def set_resolution(self, width, height):
        self.camera.stop()
        config = self.camera.create_still_configuration(
            main={"size": (width, height)}
        )
        self.camera.configure(config)
        self.camera.start()
        time.sleep(1)

    def close(self):
        self.camera.stop()
        self.camera.close()

class OpenCVCapture:
    """使用 OpenCV 拍照"""

    def __init__(self, device=0):
        self.cap = cv2.VideoCapture(device)
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开摄像头 {device}")

        # 设置分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # 预热
        for _ in range(5):
            self.cap.read()
        print(f"✅ USB 摄像头初始化完成 (设备 {device})")

    def capture(self, filename=None):
        if filename is None:
            filename = generate_filename()

        ret, frame = self.cap.read()
        if ret:
            cv2.imwrite(filename, frame)
            return filename
        return None

    def capture_with_preview(self, filename=None):
        """带预览窗口拍照"""
        if filename is None:
            filename = generate_filename()

        print("按 空格键 拍照，按 q 退出")
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            cv2.imshow('预览 (空格拍照, q退出)', frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord(' '):
                cv2.imwrite(filename, frame)
                print(f"  📸 已拍照: {filename}")
                break
            elif key == ord('q'):
                filename = None
                break

        cv2.destroyAllWindows()
        return filename

    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()

class MockCapture:
    """模拟摄像头"""

    def capture(self, filename=None):
        if filename is None:
            filename = generate_filename()
        # 创建一个简单的测试图像
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (640, 480), color=(100, 150, 200))
            draw = ImageDraw.Draw(img)
            draw.text((200, 220), "Mock Camera", fill=(255, 255, 255))
            draw.text((220, 250), datetime.now().strftime("%H:%M:%S"), fill=(255, 255, 0))
            img.save(filename)
            print(f"  [模拟] 已保存: {filename}")
        except ImportError:
            print(f"  [模拟] 拍照: {filename}")
        return filename

    def close(self):
        pass

def create_camera():
    """创建摄像头实例"""
    ensure_output_dir()

    if CAMERA_TYPE == 'picamera2':
        try:
            return PiCamera2Capture()
        except Exception as e:
            print(f"Pi Camera 初始化失败: {e}")

    if CAMERA_TYPE == 'opencv':
        try:
            return OpenCVCapture()
        except Exception as e:
            print(f"USB 摄像头初始化失败: {e}")

    return MockCapture()

def take_single_photo():
    """拍单张照片"""
    camera = create_camera()
    try:
        filename = camera.capture()
        if filename:
            size = os.path.getsize(filename) if os.path.exists(filename) else 0
            print(f"\n📸 照片已保存:")
            print(f"  文件: {filename}")
            print(f"  大小: {size / 1024:.1f} KB")
    finally:
        camera.close()

def take_burst_photos(count=5, interval=1):
    """连拍"""
    camera = create_camera()
    print(f"\n连拍 {count} 张，间隔 {interval} 秒")

    try:
        for i in range(count):
            filename = generate_filename(f"burst_{i+1:03d}")
            camera.capture(filename)
            print(f"  [{i+1}/{count}] 📸 {filename}")
            if i < count - 1:
                time.sleep(interval)
        print(f"\n✅ 连拍完成，共 {count} 张")
    finally:
        camera.close()

def timelapse(count=10, interval=5):
    """延时摄影"""
    camera = create_camera()
    print(f"\n延时摄影: {count} 张，间隔 {interval} 秒")
    print(f"总时长: {count * interval} 秒")
    print("按 Ctrl+C 停止\n")

    try:
        for i in range(count):
            filename = generate_filename(f"timelapse_{i+1:04d}")
            camera.capture(filename)
            print(f"  [{i+1}/{count}] {time.strftime('%H:%M:%S')} 📸 {filename}")
            if i < count - 1:
                time.sleep(interval)
        print(f"\n✅ 延时摄影完成")
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        camera.close()

def main():
    print("=" * 40)
    print("📷 摄像头拍照")
    print("=" * 40)
    print(f"输出目录: {OUTPUT_DIR}/")
    print()

    print("选择模式:")
    print("1. 单张拍照")
    print("2. 连拍 (5张)")
    print("3. 延时摄影")

    choice = input("\n请选择 (1-3): ").strip()

    if choice == '1':
        take_single_photo()
    elif choice == '2':
        count = input("连拍张数 (默认5): ").strip()
        count = int(count) if count.isdigit() else 5
        take_burst_photos(count)
    elif choice == '3':
        count = input("拍摄张数 (默认10): ").strip()
        interval = input("间隔秒数 (默认5): ").strip()
        count = int(count) if count.isdigit() else 10
        interval = int(interval) if interval.isdigit() else 5
        timelapse(count, interval)
    else:
        take_single_photo()

if __name__ == "__main__":
    main()