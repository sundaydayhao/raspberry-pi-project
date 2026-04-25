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

### 4.5 在树莓派 3B+ 上运行 NCNN 模型

如果你已经导出了 NCNN 模型目录，例如：

```text
yolo26n_ncnn_model/
├── model.bin
├── model.param
└── metadata.yaml
```

最推荐的运行方式，不是直接手写 `ncnn` 后处理，而是先用 `Ultralytics` 直接加载这个目录。  
官方 NCNN 文档明确支持这种方式，`YOLO("./yolo26n_ncnn_model")` 会自动处理前处理、后处理和画框逻辑。

#### 方案 A：最稳的摄像头实时识别

```python
from ultralytics import YOLO
import cv2

model = YOLO("/home/pi/yolo/yolo26n_ncnn_model")

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ok, frame = cap.read()
    if not ok:
        break

    results = model(frame, imgsz=320, verbose=False)
    annotated = results[0].plot()

    cv2.imshow("YOLO NCNN", annotated)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
```

这条路线更适合树莓派 3B+，因为：

- 不用自己解析 `output0`
- 不用自己写 NMS
- 不容易因为 blob 名称不一致而报错

如果你是通过 SSH 登录树莓派，没有桌面环境，`cv2.imshow()` 可能会失败。  
这种情况下可以把 `imshow` 改成定时保存图片，或者只打印检测结果。

#### 方案 B：原生 `ncnn` Python API 最小示例

你贴的代码整体方向是对的，但有几个点要改：

- Ultralytics 导出的默认文件名通常是 `model.param` 和 `model.bin`，不一定是 `yolov8n.ncnn.param`
- 模型通常期望 `RGB` 输入，建议从 OpenCV 的 `BGR` 转成 `RGB`
- `ex.extract("output0", out)` 只拿到了原始输出，还没有做框解码和 NMS
- 所以你当前代码只能证明“模型跑起来了”，还不能真正画检测框

下面这版可以作为“NCNN 推理链路自检”示例：

```python
import cv2
import ncnn

param_path = "/home/pi/yolo/yolo26n_ncnn_model/model.param"
bin_path = "/home/pi/yolo/yolo26n_ncnn_model/model.bin"

net = ncnn.Net()
net.opt.use_vulkan_compute = False
net.opt.num_threads = 4
net.load_param(param_path)
net.load_model(bin_path)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ok, frame = cap.read()
    if not ok:
        break

    h, w = frame.shape[:2]
    mat = ncnn.Mat.from_pixels_resize(
        frame,
        ncnn.Mat.PixelType.PIXEL_BGR2RGB,
        w,
        h,
        320,
        320,
    )
    mat.substract_mean_normalize([0.0, 0.0, 0.0], [1 / 255.0, 1 / 255.0, 1 / 255.0])

    ex = net.create_extractor()
    ex.input("in0", mat)   # 这里的输入名要以你自己的模型为准
    ret, out = ex.extract("out0")  # 输出名同样要按模型实际 blob 名称修改

    text = f"NCNN ok, ret={ret}, out=({out.w},{out.h},{out.c})"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.imshow("NCNN Smoke Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
```

这段代码的重点是确认：

- 摄像头能正常读帧
- NCNN 模型能正常加载
- 输入输出 blob 能对上

但它还不是完整检测程序。

#### 方案 C：为什么你当前代码还画不出真实框

你现在这段代码：

```python
ex.input("images", mat)
ex.extract("output0", out)
```

常见问题有三个：

1. `images` 和 `output0` 不一定是你导出模型里的真实 blob 名称。  
   不同导出方式里名字可能是 `in0`、`out0`，也可能是别的。最稳的办法是用 `Netron` 打开 `model.param` 检查。

2. `out` 只是原始张量，不是最终框。  
   要想真正画框，还需要：
   - 解析每个候选框
   - 按类别取最大分数
   - 换算回原图坐标
   - 执行 NMS 去重

3. 你的 `class_names` 只写了 7 个类。  
   如果你跑的是 COCO 模型，标准类别数是 80 个。

所以如果目标是“尽快在树莓派 3B+ 上跑起来”，更推荐先走方案 A。

#### 方案 D：树莓派 3B+ 上的实用参数

树莓派 3B+ 资源比较紧张，建议这样调：

- 模型：优先 `yolo11n`、`yolo26n`、`yolov8n`
- 输入尺寸：先试 `imgsz=320`
- 摄像头分辨率：先设成 `640x480`
- 推理频率：必要时隔帧推理
- 显示方式：无桌面时不要依赖 `cv2.imshow()`

如果你只想先验证速度，可以先每 2 到 3 帧推理一次。

```python
frame_id = 0

while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame_id += 1
    if frame_id % 3 != 0:
        continue
```

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
