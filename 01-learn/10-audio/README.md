# 10 - 音频处理 (Audio)

## 📋 目录结构

```
10-audio/
├── audio_web_player/            # 🎵 网页音频控制中心（端口5006）
│   ├── audio_web_player.py
│   └── templates/
│       └── audio_web_player.html
├── buzzer_music.py              # 蜂鸣器音乐（本地）
├── text_to_speech.py            # 文字转语音（本地）
├── record_audio.py              # 录音（本地）
├── play_audio.py                # 播放音频（本地）
└── README.md
```

---

## 🎵 网页音频控制中心（新增）

**目录：** `audio_web_player/`  
**访问：** `http://<树莓派IP>:5006`

### 功能特性
- 🎵 **远程播放音频**（MP3/WAV/OGG/FLAC，网页点击播放）
- 📁 **播放列表管理**（网页上传/删除音频文件）
- 🔊 **音量控制**（滑块实时调节）
- 🔊 **文字转语音 TTS**（网页输入文字，树莓派朗读，支持中英文）
- 🎵 **蜂鸣器音乐**（内置5首曲目：生日快乐/两只老虎/小星星/欢乐颂/哆来咪）
- 🎙 **远程录音**（网页触发，保存到服务器，可回放）
- 📊 **实时波形动画**（播放时显示动态均衡器效果）
- 📋 **操作日志**（记录所有播放/录音操作）

### 安装依赖
```bash
pip3 install flask
sudo apt install mpg123 espeak aplay arecord -y
# 或者安装 ffmpeg 作为备选播放器
sudo apt install ffmpeg -y
```

### 运行
```bash
cd 10-audio/audio_web_player
python3 audio_web_player.py
# 访问 http://<树莓派IP>:5006
```

### 使用说明
1. **播放音频**：先上传 MP3/WAV 文件，点击列表中的文件名播放
2. **TTS朗读**：在文本框输入文字，选择语言，点击"朗读"
3. **蜂鸣器**：点击曲目按钮，树莓派蜂鸣器演奏（需连接无源蜂鸣器到 GPIO18）
4. **录音**：选择录音时长，点击"开始录音"，完成后可在列表中回放

### 硬件连接
```
无源蜂鸣器 → GPIO18（PWM控制）
音频输出   → 3.5mm耳机口 或 HDMI
麦克风     → USB声卡 或 I2S麦克风模块
```

---

## 📻 其他音频脚本

| 文件 | 功能 |
|------|------|
| `buzzer_music.py` | 蜂鸣器演奏音乐（本地运行） |
| `text_to_speech.py` | 文字转语音（本地运行） |
| `record_audio.py` | 录音到文件（本地运行） |
| `play_audio.py` | 播放音频文件（本地运行） |

---

## 🔌 端口汇总（全项目）

| 项目 | 目录 | 端口 |
|------|------|------|
| 🏠 智能家居监测 | `08-iot-projects/smart_home_monitor/` | 5000 |
| 🌱 植物养护 | `08-iot-projects/plant_care_web/` | 5001 |
| 📊 实时仪表盘 | `08-iot-projects/realtime_dashboard/` | 5002 |
| 🔒 安防监控 | `09-advanced-projects/smart_security_web/` | 5003 |
| ⚡ 电能监测 | `09-advanced-projects/energy_monitor_web/` | 5004 |
| 📷 摄像头直播 | `07-camera/camera_web_stream/` | 5005 |
| 🎵 音频控制 | `10-audio/audio_web_player/` | 5006 |