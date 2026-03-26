# 01 - 入门基础 (Getting Started)

## 📋 本章内容

| 文件 | 说明 |
|------|------|
| `setup_guide.md` | 系统安装与配置指南 |
| `hello_world.py` | 第一个 Python 程序 |
| `system_info.py` | 获取系统信息 |
| `gpio_test.py` | GPIO 基础测试 |
| `network_config.py` | 网络配置工具 |

## 🛠️ 环境准备

### 1. 安装 Raspberry Pi OS
1. 下载 [Raspberry Pi Imager](https://www.raspberrypi.org/software/)
2. 选择 Raspberry Pi OS (64-bit) 推荐
3. 烧录到 MicroSD 卡
4. 首次启动完成初始化设置

### 2. 启用必要接口
```bash
sudo raspi-config
```
- Interface Options → SSH → Enable
- Interface Options → I2C → Enable  
- Interface Options → SPI → Enable
- Interface Options → Camera → Enable
- Interface Options → Serial Port → Enable

### 3. 安装必要软件
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-dev git
sudo apt install -y python3-rpi.gpio python3-smbus
pip3 install RPi.GPIO gpiozero
```

## 🔌 硬件连接

本章无需额外硬件，仅需 Raspberry Pi 主板和电源。

## 📝 学习目标

- [ ] 成功启动 Raspberry Pi
- [ ] 通过 SSH 远程连接
- [ ] 运行第一个 Python 程序
- [ ] 了解系统基本信息