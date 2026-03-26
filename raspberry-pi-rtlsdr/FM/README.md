# FM RTL-SDR HDMI 频谱监视器

## 方案说明

该目录实现了一个基于树莓派和 RTL-SDR 的 FM 广播监视器，用于在 HDMI 屏上显示 FM 频段的实时信息和瀑布图。

### 功能
- 使用 RTL-SDR 采集 FM 广播 IQ 数据
- 对采样数据执行 FFT 频谱分析
- 在 HDMI 屏上显示：
  - 当前中心频率
  - 采样率
  - 增益
  - 峰值频点
  - 实时频谱曲线
  - 瀑布图
- 支持全屏显示
- 支持 `Q` / `ESC` 退出

### 显示方案
本方案不再使用 SPI LCD，而是直接输出到树莓派连接的 HDMI 屏。  
程序内部使用 `pygame` 创建显示窗口，适合同样硬件配置下的 HDMI 显示器、小尺寸 HDMI LCD、便携显示屏等。

### 核心实现思路
1. 使用 `pyrtlsdr` 调用 RTL-SDR 设备采样
2. 对采样结果进行窗函数处理和 FFT 运算
3. 提取功率谱并计算峰值频点
4. 将每一帧频谱压缩为一行，持续写入瀑布图缓存
5. 使用 `Pillow` 绘制频谱、文字信息、瀑布图
6. 使用 `pygame` 将图像显示到 HDMI 屏

---

## 文件说明

- `main.py`  
  主程序，负责 RTL-SDR 采样、频谱分析、瀑布图生成和 HDMI 输出

- `requirements.txt`  
  Python 依赖列表

- `run.sh`  
  启动脚本，包含默认运行参数

---

## 依赖安装

在树莓派上安装 Python 依赖：

```bash
pip install -r requirements.txt
```

如果系统还没有安装 RTL-SDR 底层驱动和库，请先安装系统依赖。

---

## 使用方法

进入当前目录后运行：

```bash
bash run.sh
```

或者直接运行：

```bash
python3 main.py --freq 98.0 --sample-rate 2400000 --gain auto --fft-size 1024 --frame-rate 20 --width 800 --height 480
```

---

## 参数说明

### 常用参数
- `--freq`  
  中心频率，单位 MHz，例如 `98.0`

- `--sample-rate`  
  采样率，例如 `2400000`

- `--gain`  
  增益，支持 `auto` 或具体数值

- `--fft-size`  
  FFT 点数，默认 `1024`

- `--frame-rate`  
  HDMI 刷新帧率

- `--width`  
  HDMI 显示宽度

- `--height`  
  HDMI 显示高度

- `--ppm`  
  RTL-SDR 频偏校正

- `--device-index`  
  RTL-SDR 设备索引

- `--windowed`  
  使用窗口模式，而不是全屏模式

- `--save-frames`  
  保存当前显示帧到本地目录

---

## 默认配置

`run.sh` 当前默认配置为：

- 中心频率：`98.0 MHz`
- 采样率：`2400000`
- 增益：`auto`
- FFT：`1024`
- 帧率：`20`
- 分辨率：`800 x 480`

---

## 适用场景

- 树莓派 + RTL-SDR + HDMI 小屏
- FM 广播频段现场频谱观察
- 简单 SDR 频谱可视化
- 便携式无线电频谱显示终端

---

## 注意事项

1. 该程序当前重点是 **FM 信号监视和可视化显示**，不是完整的 FM 音频播放器
2. 如果需要播放 FM 音频，需要进一步增加 FM 解调和音频输出模块
3. 请确保 RTL-SDR 已正确连接，并且系统能够识别设备
4. 若 HDMI 分辨率不同，可修改 `run.sh` 或命令行参数中的 `--width` 和 `--height`

---

## 退出方式

运行过程中按以下按键可退出：

- `Q`
- `ESC`