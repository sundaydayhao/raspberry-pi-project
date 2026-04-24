# 树莓派 3B+ 移植 YOLO 实战笔记

这份文档整理了前面讨论过的几个核心问题：

- 树莓派 3B+ 上怎么部署 YOLO
- `best.pt` 去哪里下载
- `python3 -m pip install ultralytics` 为什么会报 `externally-managed-environment`
- 已经配置了清华源，为什么安装时又从 `piwheels` 下载

适用场景：

- 设备：Raspberry Pi 3B+
- 系统：Raspberry Pi OS Bookworm/Trixie 一类新版本
- 目标：在树莓派上运行 YOLO 推理，而不是在树莓派上训练模型

## 1. 先说结论

树莓派 3B+ 能跑 YOLO，但更适合做推理端，不适合训练端。

推荐路线：

1. 在电脑上训练或下载模型
2. 在电脑上把模型导出成适合树莓派的格式
3. 把导出的模型拷到树莓派
4. 在树莓派上只做图片或摄像头推理

对于树莓派 3B+，优先推荐：

- 首选：`NCNN`
- 备选：`TFLite`

实际建议：

- 尽量使用小模型，如 `yolo11n.pt`、`yolo26n.pt`
- 输入尺寸先从 `imgsz=320` 开始
- 不要一上来就跑 `s/m/l/x` 这种更大的模型

## 2. 为什么不建议在树莓派 3B+ 上直接训练

树莓派 3B+ 的资源比较有限：

- 1GB 内存
- Cortex-A53 CPU
- 没有适合 YOLO 训练的高性能 GPU

所以更合理的做法是：

- 训练：在电脑或云端完成
- 导出：在电脑完成
- 推理：放到树莓派上运行

## 3. 在哪里下载开源的 `best.pt`

这里要先区分两类文件。

### 3.1 官方预训练模型

如果你只是想先跑通 YOLO，不一定非要文件名叫 `best.pt`。  
官方常用的是这些预训练权重：

- `yolo11n.pt`
- `yolo26n.pt`
- `yolov8n.pt`

最简单的下载方式，是让 `ultralytics` 自动拉取：

```bash
pip install -U ultralytics
python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
```

或者：

```bash
python -c "from ultralytics import YOLO; YOLO('yolo26n.pt')"
```

### 3.2 别人项目里的 `best.pt`

`best.pt` 一般是某个具体数据集训练出来的最佳权重，不是统一官方文件名。

常见来源：

- Ultralytics 官方模型
- Hugging Face 上的 YOLO 社区模型
- Roboflow Universe 上的数据集和模型项目

注意：

- 社区 `.pt` 文件只建议从可信作者下载
- 不要随便运行来源不明的 `.pt` 文件
- Roboflow 上很多项目并不能直接免费下载原始 `.pt` 权重

如果只是为了在树莓派 3B+ 上先验证流程，推荐直接从官方小模型开始，而不是先找陌生人的 `best.pt`。

## 4. 推荐的树莓派 YOLO 部署流程

### 4.1 在电脑上安装 Ultralytics

```bash
pip install -U ultralytics
```

### 4.2 在电脑上导出模型

推荐导出为 `NCNN`：

```bash
yolo export model=best.pt format=ncnn imgsz=320
```

如果需要备选方案，也可以导出 `TFLite`：

```bash
yolo export model=best.pt format=tflite imgsz=320 int8=True data=data.yaml
```

说明：

- `best.pt` 可以换成你自己的权重
- `imgsz=320` 更适合树莓派 3B+ 这种性能有限的板子
- `int8=True` 会进一步压缩模型，适合弱性能设备

### 4.3 把模型传到树莓派

```bash
scp -r best_ncnn_model pi@<树莓派IP>:/home/pi/yolo/
```

### 4.4 在树莓派上做推理

```python
from ultralytics import YOLO

model = YOLO("/home/pi/yolo/best_ncnn_model")
results = model("/home/pi/test.jpg")
print(results[0])
```

如果你接的是树莓派摄像头，可以先确认相机正常：

```bash
rpicam-hello
sudo apt install -y python3-picamera2
```

后面用 `Picamera2` 抓帧，再把图像帧喂给 YOLO 即可。

## 5. 为什么 `pip install ultralytics` 会报 `externally-managed-environment`

在 Raspberry Pi OS Bookworm 之后，系统 Python 默认受到 PEP 668 保护。

你看到的这类报错：

```text
error: externally-managed-environment
```

意思不是命令写错了，而是系统不希望你直接把第三方包装进系统 Python。

正确做法是使用虚拟环境。

### 5.1 推荐安装方式

```bash
sudo apt update
sudo apt install -y python3-full python3-venv

mkdir -p ~/yolo
cd ~/yolo

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip setuptools wheel
python -m pip install ultralytics
```

### 5.2 验证是否安装成功

```bash
python -c "from ultralytics import YOLO; print('ultralytics ok')"
```

### 5.3 每次使用前先激活环境

```bash
cd ~/yolo
source .venv/bin/activate
```

退出虚拟环境：

```bash
deactivate
```

### 5.4 如果还要访问系统里的相机或 GPIO 包

可以这样创建虚拟环境：

```bash
python3 -m venv --system-site-packages .venv
```

这样虚拟环境能同时看到系统安装的一部分 Python 包，更适合树莓派上的硬件开发场景。

### 5.5 为什么不推荐 `--break-system-packages`

虽然下面这个命令能强行安装：

```bash
python3 -m pip install ultralytics --break-system-packages
```

但它可能破坏系统 Python 环境，不建议作为常规方案。

## 6. 我明明配了清华源，为什么又从 `piwheels` 下载

如果你看到类似输出：

```text
Looking in indexes: https://pypi.tuna.tsinghua.edu.cn/simple, https://www.piwheels.org/simple
```

说明当前 `pip` 并不是只使用清华源，而是同时使用：

- 清华源
- `piwheels`

### 6.1 这不是异常，而是 `pip` 的正常行为

`pip` 在存在多个索引源时，并不是简单地“前面的源优先”。  
它会把多个索引里的候选包综合起来，再选择当前最合适的安装候选。

所以即使你配置了清华源，只要：

- `piwheels` 里也有这个包
- 而且版本更新或 wheel 更适合树莓派

那么 `pip` 就可能从 `piwheels` 下载。

### 6.2 为什么树莓派上经常会走 `piwheels`

`piwheels` 是专门给 Raspberry Pi/ARM 平台准备的 wheel 仓库。  
很多包在这里会有更适合树莓派的预编译版本，安装更顺，速度也更快。

对树莓派来说，保留 `piwheels` 往往是有好处的。

### 6.3 怎么查看是谁把 `piwheels` 配进去的

```bash
python -m pip config debug
python -m pip config list -v
```

通常配置可能出现在这些地方：

- `~/.config/pip/pip.conf`
- `/etc/pip.conf`
- 虚拟环境自己的 `pip.conf`

### 6.4 如果想临时只用清华源

```bash
PIP_CONFIG_FILE=/dev/null python -m pip install ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir
```

### 6.5 如果想长期不使用 `piwheels`

把配置文件中的这行删掉或注释掉：

```ini
extra-index-url = https://www.piwheels.org/simple
```

不过从树莓派的实际使用体验来看，通常不建议移除 `piwheels`。

## 7. 树莓派 3B+ 上的实用建议

- 优先用 `n` 级别小模型
- 先用图片推理把流程跑通，再接摄像头
- 输入尺寸优先从 `320` 开始
- 系统尽量精简，优先使用 `Raspberry Pi OS Lite`
- 真正要做长期项目，建议记录模型版本、导出格式和安装命令

## 8. 一个可操作的最小流程

### 电脑端

```bash
pip install -U ultralytics
yolo export model=yolo11n.pt format=ncnn imgsz=320
scp -r yolo11n_ncnn_model pi@<树莓派IP>:/home/pi/yolo/
```

### 树莓派端

```bash
sudo apt update
sudo apt install -y python3-full python3-venv

mkdir -p ~/yolo
cd ~/yolo

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip setuptools wheel
python -m pip install ultralytics
```

测试：

```bash
python -c "from ultralytics import YOLO; model = YOLO('/home/pi/yolo/yolo11n_ncnn_model'); print('model loaded')"
```

## 9. 参考资料

- Ultralytics 文档: https://docs.ultralytics.com/
- Ultralytics Export: https://docs.ultralytics.com/modes/export/
- Ultralytics Raspberry Pi 指南: https://docs.ultralytics.com/guides/raspberry-pi/
- Ultralytics NCNN: https://docs.ultralytics.com/integrations/ncnn/
- Ultralytics TFLite: https://docs.ultralytics.com/integrations/tflite/
- Raspberry Pi OS 文档: https://www.raspberrypi.com/documentation/computers/os.html
- Raspberry Pi 关于虚拟环境的说明: https://www.raspberrypi.com/news/using-python-with-virtual-environments-the-magpi-148/
- Python `venv` 文档: https://docs.python.org/3/library/venv.html
- PEP 668: https://peps.python.org/pep-0668/
- pip 配置文档: https://pip.pypa.io/en/stable/topics/configuration/
- pip install 行为: https://pip.pypa.io/en/stable/cli/pip_install/
- piwheels: https://www.piwheels.org/

