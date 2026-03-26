# 07 - 摄像头应用 (Camera)

## 📋 目录结构

```
07-camera/
├── camera_web_stream/           # 📷 摄像头网页直播系统（端口5005）
│   ├── camera_web_stream.py
│   └── templates/
│       └── camera_web_stream.html
├── capture_photo.py             # 基础拍照
├── face_detection.py            # 人脸检测（本地显示）
├── motion_detection.py          # 运动检测（本地显示）
└── README.md
```

---

## 📷 摄像头网页直播系统（新增）

**目录：** `camera_web_stream/`  
**访问：** `http://<树莓派IP>:5005`

### 功能特性
- 🎥 **MJPEG实时视频流**（浏览器直接播放，无需插件）
- 📷 远程拍照（网页按钮一键拍照）
- 🖼 照片画廊（最近20张，支持全屏预览）
- 👁 运动检测（帧差法，自动标注运动区域 + 自动拍照）
- 😊 人脸检测（OpenCV Haar级联，实时框选）
- 🎛 画面调节（亮度/对比度滑块）
- 📱 手机/PC自适应界面

### 安装依赖
```bash
pip3 install flask opencv-python
```

### 运行
```bash
cd 07-camera/camera_web_stream
python3 camera_web_stream.py
# 访问 http://<树莓派IP>:5005
```

### 技术说明
- 视频流使用 **MJPEG over HTTP**（`multipart/x-mixed-replace`），兼容所有现代浏览器
- 运动检测使用**帧差法**（Gaussian模糊 + 二值化 + 轮廓检测）
- 人脸检测使用 **OpenCV Haar级联分类器**
- 后端多线程：采集线程 + Flask服务线程分离，保证流畅度

---

## 📸 其他摄像头脚本

### capture_photo.py
基础拍照脚本，支持 Pi Camera 和 USB 摄像头。

### face_detection.py
实时人脸检测，在本地窗口显示（需要显示器）。

### motion_detection.py
运动检测，在本地窗口显示（需要显示器）。

---

## 🔌 硬件连接

### Pi Camera（推荐）
```
树莓派 CSI 接口 → Pi Camera 排线
sudo raspi-config → Interface Options → Camera → Enable
```

### USB 摄像头
```
直接插入 USB 口，自动识别为 /dev/video0
```

---

## 📡 手机访问

1. 手机与树莓派连接同一 WiFi
2. 查看树莓派 IP：`hostname -I`
3. 手机浏览器访问：`http://<IP>:5005`
4. 即可在手机上实时查看摄像头画面