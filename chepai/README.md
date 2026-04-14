# 树莓派 3B+ 车牌识别

这是一个适合树莓派 3B+ 的轻量级车牌识别项目，放在 [`chepai`](/home/hao/projects/raspberry-pi-project/chepai) 目录下即可直接部署。实现思路尽量避开重型深度学习模型，使用：

- `OpenCV` 传统图像处理做车牌候选区域检测
- `Tesseract OCR` 做字符识别
- 中国车牌格式清洗与纠错逻辑做结果后处理
- `Picamera2` / `OpenCV` 双后端摄像头输入，适配 CSI 摄像头和 USB 摄像头

这种方案在树莓派 3B+ 上更容易离线运行，也更方便自己后续继续优化。

## 目录结构

```text
chepai/
├── install.sh
├── main.py
├── README.md
├── requirements.txt
└── lpr/
    ├── __init__.py
    ├── camera.py
    ├── detector.py
    ├── ocr.py
    ├── pipeline.py
    └── postprocess.py
```

## 功能说明

- 单张图片识别
- 摄像头实时识别
- 自动在图像中框出车牌区域
- 输出识别文字、识别分数、OCR 置信度
- 可保存识别后的标注图片
- 实时模式下支持降帧识别，减轻树莓派 CPU 压力
- 内置 32 个省级简称识别与归一化规则，支持省份全称、繁体和部分常见 OCR 误写
- 对轻微倾斜和斜拍车牌会先做旋转/透视矫正，再送入 OCR

## 推荐硬件

- 树莓派 3B+
- 树莓派官方 CSI 摄像头，或 USB 摄像头
- 5V 2.5A 及以上电源
- Raspberry Pi OS Bookworm / Bullseye

## 安装

### 1. 进入项目目录

```bash
cd /home/hao/projects/raspberry-pi-project/chepai
```

### 2. 一键安装依赖

```bash
sudo bash install.sh
```

安装脚本会完成这些事情：

- 安装 `python3-opencv`
- 安装 `tesseract-ocr`
- 安装 `tesseract-ocr-chi-sim`
- 如果系统仓库存在，会顺带安装 `python3-picamera2` 和 `libcamera-apps`
- 安装中文字体 `fonts-noto-cjk`，用于在图片上正确绘制车牌汉字
- 创建 `venv`
- 安装 Python 依赖
- 清理 `venv` 里单独安装的 `NumPy`，避免和系统 `OpenCV` 产生 ABI 冲突

### 3. 如果用的是 CSI 摄像头

先确认摄像头已启用：

```bash
libcamera-hello
```

如果命令可正常预览，说明摄像头工作正常。

## 使用方法

### 识别单张图片

```bash
cd /home/hao/projects/raspberry-pi-project/chepai
venv/bin/python3 main.py --image ./test.jpg --show --output ./result.jpg
```

终端会输出类似结果：

```text
image: ./test.jpg
recognized plates: 1
[1] plate=粤B12345 score=0.88 ocr_conf=71.2 source=contour
```

### 摄像头实时识别

自动选择后端：

```bash
venv/bin/python3 main.py --camera --camera-engine auto --show
```

强制使用 USB 摄像头 / OpenCV：

```bash
venv/bin/python3 main.py --camera --camera-engine opencv --camera-index 0 --show
```

强制使用树莓派 CSI 摄像头 / Picamera2：

```bash
venv/bin/python3 main.py --camera --camera-engine picamera2 --show
```

只要识别到一次就退出：

```bash
venv/bin/python3 main.py --camera --once --output ./capture.jpg
```

输出 JSON：

```bash
venv/bin/python3 main.py --image ./test.jpg --json
```

## 参数建议

树莓派 3B+ 算力有限，推荐这样运行：

```bash
venv/bin/python3 main.py --camera --width 640 --height 480 --every-n-frames 3 --show
```

说明：

- `640x480` 对 Pi 3B+ 更稳
- `--every-n-frames 3` 表示每 3 帧做一次识别，减少 CPU 占用
- 如果识别较慢，可以把它改成 `4` 或 `5`

## 实现原理

### 1. 车牌检测

[`lpr/detector.py`](/home/hao/projects/raspberry-pi-project/chepai/lpr/detector.py) 使用两种方式找车牌候选框：

- 基于黑帽变换、Sobel 边缘和轮廓筛选
- 如果系统里存在 OpenCV 自带 Haar 车牌分类器，则额外启用级联检测

最后把重叠框合并，保留得分更高的候选区域。

### 2. OCR 识别

[`lpr/ocr.py`](/home/hao/projects/raspberry-pi-project/chepai/lpr/ocr.py) 会对候选车牌做多种预处理：

- 放大
- 双边滤波
- 全局二值化
- 自适应阈值
- 反色

然后调用 `Tesseract` 做多轮识别，挑选最优结果。

### 3. 结果纠错

[`lpr/postprocess.py`](/home/hao/projects/raspberry-pi-project/chepai/lpr/postprocess.py) 会做：

- 去掉空格和杂字符
- 修正 `0/O`、`1/I`、`5/S` 等常见 OCR 混淆
- 按中国车牌格式重新打分

## 已知限制

- 这是轻量级方案，不如专门训练的深度学习模型准确
- 夜间、强反光、运动模糊场景下准确率会明显下降
- 中国新能源车牌、双层车牌、遮挡车牌的识别稳定性有限
- `Tesseract` 对中文省份简称的鲁棒性一般，建议摄像头尽量正对车牌并保证清晰度

如果后续你想继续提升效果，下一步最值得做的是：

1. 增加一个拍照触发逻辑，只在车辆靠近时抓拍
2. 为识别前的图像做透视矫正
3. 用专门的轻量化车牌检测模型替换传统轮廓检测
4. 把 OCR 换成更适合车牌场景的 CRNN / PaddleOCR 轻量模型

## 常见问题

### 1. 找不到 `tesseract`

运行：

```bash
sudo apt install -y tesseract-ocr tesseract-ocr-chi-sim
```

### 2. `cv2` 导入时报 NumPy 2.x / `_ARRAY_API` 错误

这是因为 `venv` 里安装了 `NumPy 2.x`，但系统里的 `python3-opencv` 还是按 `NumPy 1.x` 编译的。

先尝试重新执行安装脚本：

```bash
sudo bash install.sh
```

如果你的旧 `venv` 目录是用 `sudo` 创建的，普通用户可能删不掉里面的 `numpy`。可以这样修复：

```bash
sudo chown -R $USER:$USER venv
mkdir -p .tmp
TMPDIR=$PWD/.tmp venv/bin/python3 -m pip uninstall -y numpy
```

修完后验证：

```bash
venv/bin/python3 -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"
```

### 3. 摄像头打不开

先试：

```bash
libcamera-hello
```

如果是 USB 摄像头，再试：

```bash
ls /dev/video*
```

然后改用：

```bash
venv/bin/python3 main.py --camera --camera-engine opencv --camera-index 0 --show
```

### 4. 图形窗口打不开

如果你是通过 SSH 运行，没有桌面环境时可以不加 `--show`：

```bash
venv/bin/python3 main.py --camera --once --output ./capture.jpg
```
