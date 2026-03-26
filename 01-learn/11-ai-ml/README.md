# 🤖 11 - AI/ML 人工智能与机器学习

> 在树莓派上运行真实的 AI/ML 算法：异常检测、图像分类、手势识别、语音命令

---

## 📋 目录结构

```
11-ai-ml/
├── sensor_anomaly_detection.py  # 传感器异常检测（Isolation Forest / Z-Score）
├── image_classifier.py          # 图像分类（TFLite MobileNetV2 / OpenCV DNN）
├── gesture_recognition.py       # 手势识别（MediaPipe / 肤色分割）
├── voice_command.py             # 语音命令识别（Google API / Vosk 离线）
├── ai_dashboard_web/            # 🤖 AI/ML 智能仪表盘（端口5007）
│   ├── ai_dashboard_web.py
│   └── templates/
│       └── ai_dashboard_web.html
└── models/                      # 模型文件目录（需手动下载）
    ├── mobilenet_v2_1.0_224_quant.tflite
    └── vosk-model-small-cn-0.22/
```

---

## 🚀 快速开始

### 安装依赖

```bash
# 基础依赖（必须）
pip3 install numpy scikit-learn flask flask-socketio eventlet

# 摄像头相关
pip3 install opencv-python

# 手势识别
pip3 install mediapipe

# 图像分类（TFLite，推荐树莓派）
pip3 install tflite-runtime

# 语音识别
pip3 install SpeechRecognition pyaudio
sudo apt install portaudio19-dev python3-pyaudio

# 离线语音识别
pip3 install vosk
```

### 运行 AI 仪表盘（无需硬件，自动模拟数据）

```bash
cd 11-ai-ml/ai_dashboard_web
python3 ai_dashboard_web.py
# 访问 http://localhost:5007
```

---

## 🤖 项目一：传感器异常检测

**文件：** `sensor_anomaly_detection.py`

### 功能特性
- 🔍 **Isolation Forest**（无监督机器学习，自动学习正常模式）
- 📊 **Z-Score 统计检测**（无需 ML 库，滑动窗口统计）
- 🔄 **在线学习**（每 50 个样本自动重新训练）
- 🚨 **GPIO 报警联动**（异常时点亮 LED）
- 📈 **实时异常率统计**

### 算法原理

```
正常数据 → 训练 Isolation Forest → 学习正常分布
新数据   → 模型评分 → 分数低于阈值 → 判定为异常
```

### 运行

```bash
cd 11-ai-ml
python3 sensor_anomaly_detection.py
# 选择 1: Isolation Forest（需要 scikit-learn）
# 选择 2: Z-Score 统计检测
# 选择 3: 演示模式（查看原理）
```

### 硬件连接（可选）
```
DHT11 数据引脚 → GPIO4
BMP280 SDA     → GPIO2 (I2C)
BMP280 SCL     → GPIO3 (I2C)
报警 LED       → GPIO18
```

---

## 🖼️ 项目二：图像分类

**文件：** `image_classifier.py`

### 功能特性
- 🏆 **MobileNetV2 TFLite**（量化模型，树莓派 4B 约 50-100ms/帧）
- 🔄 **OpenCV DNN 备选**（无需 TensorFlow）
- 📷 **实时摄像头分类**（每 10 帧推理一次）
- 🏷️ **Top-5 结果展示**（含置信度）

### 下载模型

```bash
# 创建模型目录
mkdir -p 11-ai-ml/models

# 下载 MobileNetV2 TFLite 量化模型
wget -P 11-ai-ml/models \
  https://storage.googleapis.com/download.tensorflow.org/models/tflite/mobilenet_v2_1.0_224_quant_and_labels.zip
unzip 11-ai-ml/models/mobilenet_v2_1.0_224_quant_and_labels.zip -d 11-ai-ml/models/
```

### 运行

```bash
cd 11-ai-ml
python3 image_classifier.py
# 选择 1: 实时摄像头分类
# 选择 2: 分类图片文件
# 选择 3: 演示模式
```

### 性能参考

| 设备 | 模型 | 推理时间 |
|------|------|---------|
| 树莓派 4B | MobileNetV2 INT8 | ~50ms |
| 树莓派 4B | MobileNetV2 FP32 | ~150ms |
| 树莓派 3B+ | MobileNetV2 INT8 | ~200ms |

---

## ✋ 项目三：手势识别

**文件：** `gesture_recognition.py`

### 功能特性
- 🖐️ **MediaPipe Hands**（21 个手部关键点，实时检测）
- 🎯 **6 种手势识别**（握拳、张开、一指、剪刀、点赞、打电话）
- ⚡ **GPIO 动作映射**（手势→控制硬件）
- 🔄 **稳定性检测**（手势保持 1 秒才触发，防误触）
- 🎨 **备选方案**：肤色分割（无需 MediaPipe）

### 手势→GPIO 映射

| 手势 | GPIO | 动作 |
|------|------|------|
| ✊ 握拳 | GPIO17 | 关闭 LED |
| ✋ 张开 | GPIO17 | 打开 LED |
| ☝ 一指 | GPIO18 | LED 闪烁 |
| ✌ 剪刀 | GPIO27 | 蜂鸣器响 |
| 👍 点赞 | GPIO22 | 舵机转动 |
| 🤙 打电话 | GPIO23 | 拍照 |

### 运行

```bash
cd 11-ai-ml
python3 gesture_recognition.py
# 选择 1: MediaPipe 识别（推荐）
# 选择 2: 肤色分割识别
# 选择 3: 演示模式
```

---

## 🎤 项目四：语音命令识别

**文件：** `voice_command.py`

### 功能特性
- 🌐 **在线识别**（Google Speech API，中文，高精度）
- 📴 **离线识别**（Vosk，无需网络，树莓派友好）
- 🔑 **关键词唤醒**（"小派"唤醒，5 秒超时休眠）
- ⚡ **GPIO 联动**（语音→控制硬件）

### 支持命令

| 关键词 | GPIO | 动作 |
|--------|------|------|
| 开灯 / 打开灯 | GPIO17 | 打开 LED |
| 关灯 / 关闭灯 | GPIO17 | 关闭 LED |
| 闪烁 / 闪灯 | GPIO17 | LED 闪烁 |
| 报警 / 警报 | GPIO18 | 蜂鸣器报警 |
| 拍照 / 截图 | 摄像头 | 拍照 |
| 停止 / 退出 | — | 停止程序 |

### 下载 Vosk 中文模型（离线识别）

```bash
# 下载小型中文模型（约 40MB）
wget https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip
unzip vosk-model-small-cn-0.22.zip -d 11-ai-ml/models/
```

### 运行

```bash
cd 11-ai-ml
python3 voice_command.py
# 选择 1: 在线识别（需要网络）
# 选择 2: 离线识别（需要下载模型）
# 选择 3: 演示模式
```

---

## 🌐 项目五：AI/ML 智能仪表盘

**目录：** `ai_dashboard_web/`
**访问：** `http://<树莓派IP>:5007`

### 功能特性
- 📊 **实时传感器数据**（温度、湿度、气压）
- 🤖 **异常检测可视化**（Isolation Forest / Z-Score，实时分数图）
- 🖼️ **图像分类结果**（Top-5 置信度条形图）
- ✋ **手势识别状态**（实时手势 + 统计）
- 🎤 **语音命令模拟**（网页按钮触发）
- ⚙️ **ML 环境状态**（各库安装状态）
- 📈 **多维度图表**（Chart.js 实时折线图）
- 🚨 **异常报警横幅**（检测到异常时闪烁提示）

### 运行

```bash
cd 11-ai-ml/ai_dashboard_web
python3 ai_dashboard_web.py
# 访问 http://localhost:5007
```

---

## 📦 模型文件说明

```
11-ai-ml/models/
├── mobilenet_v2_1.0_224_quant.tflite    # MobileNetV2 量化模型（图像分类）
├── labels_mobilenet_quant_v1_224.txt    # ImageNet 标签文件
├── bvlc_googlenet.caffemodel            # GoogLeNet（OpenCV DNN 备选）
├── bvlc_googlenet.prototxt              # GoogLeNet 网络结构
└── vosk-model-small-cn-0.22/           # Vosk 中文语音模型（离线识别）
```

> 💡 所有脚本均有**模拟模式**，无需下载模型即可运行和学习

---

## 🔌 端口汇总

| 项目 | 目录 | 端口 |
|------|------|------|
| 🏠 智能家居监测 | `08-iot-projects/smart_home_monitor/` | 5000 |
| 🌱 植物养护 | `08-iot-projects/plant_care_web/` | 5001 |
| 📊 实时仪表盘 | `08-iot-projects/realtime_dashboard/` | 5002 |
| 🔒 安防监控 | `09-advanced-projects/smart_security_web/` | 5003 |
| ⚡ 电能监测 | `09-advanced-projects/energy_monitor_web/` | 5004 |
| 📷 摄像头直播 | `07-camera/camera_web_stream/` | 5005 |
| 🎵 音频控制 | `10-audio/audio_web_player/` | 5006 |
| 🤖 AI/ML 仪表盘 | `11-ai-ml/ai_dashboard_web/` | **5007** |

---

## 💡 学习路径建议

1. **先运行演示模式** — 无需任何硬件或模型，理解算法原理
2. **安装 scikit-learn** — 体验 Isolation Forest 异常检测
3. **安装 OpenCV** — 运行图像分类和手势识别
4. **下载 TFLite 模型** — 在树莓派上运行真实 AI 推理
5. **安装 MediaPipe** — 体验 21 点手部关键点检测
6. **安装 Vosk** — 实现完全离线的语音控制

---

## 📚 参考资料

- [TensorFlow Lite 树莓派部署](https://www.tensorflow.org/lite/guide/python)
- [MediaPipe 手势识别](https://mediapipe.dev/solutions/hands)
- [Vosk 离线语音识别](https://alphacephei.com/vosk/)
- [scikit-learn Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- [OpenCV DNN 模块](https://docs.opencv.org/4.x/d2/d58/tutorial_table_of_content_dnn.html)