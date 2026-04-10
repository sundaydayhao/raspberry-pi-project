#!/usr/bin/env python3
"""
录制音频
使用麦克风录制音频并保存

安装依赖:
  pip3 install pyaudio
  sudo apt install portaudio19-dev python3-pyaudio

学习要点:
  - 音频录制
  - WAV 文件格式
  - 音频参数设置
"""

import os
import sys
import time
import wave
import struct
import math

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("安装: pip3 install pyaudio")
    print("     sudo apt install portaudio19-dev")

# 录音参数
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
FORMAT_TYPE = 'int16'
OUTPUT_DIR = "recordings"

def ensure_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def record_audio(duration=5, filename=None):
    """录制音频"""
    if not PYAUDIO_AVAILABLE:
        print("pyaudio 未安装，使用系统命令录音")
        if filename is None:
            filename = os.path.join(OUTPUT_DIR, f"rec_{int(time.time())}.wav")
        ensure_dir()
        cmd = f"arecord -d {duration} -f cd -t wav {filename}"
        print(f"执行: {cmd}")
        os.system(cmd)
        return filename

    if filename is None:
        filename = os.path.join(OUTPUT_DIR, f"rec_{int(time.time())}.wav")
    ensure_dir()

    p = pyaudio.PyAudio()
    FORMAT = pyaudio.paInt16

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    print(f"录音中... ({duration}秒)")
    frames = []

    for i in range(0, int(SAMPLE_RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)
        remaining = duration - i * CHUNK / SAMPLE_RATE
        print(f"  剩余: {remaining:.1f}s", end='\r')

    print("\n录音完成!")
    stream.stop_stream()
    stream.close()
    p.terminate()

    # 保存 WAV 文件
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))

    size = os.path.getsize(filename)
    print(f"已保存: {filename} ({size/1024:.1f} KB)")
    return filename

def play_audio(filename):
    """播放音频文件"""
    if not os.path.exists(filename):
        print(f"文件不存在: {filename}")
        return

    print(f"播放: {filename}")

    # 尝试不同的播放方式
    if os.system('which aplay > /dev/null 2>&1') == 0:
        os.system(f'aplay {filename}')
    elif os.system('which sox > /dev/null 2>&1') == 0:
        os.system(f'play {filename}')
    else:
        print("未找到音频播放器")

def get_audio_info(filename):
    """获取音频文件信息"""
    try:
        with wave.open(filename, 'rb') as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frame_rate = wf.getframerate()
            n_frames = wf.getnframes()
            duration = n_frames / frame_rate

            print(f"\n音频信息: {filename}")
            print(f"  声道数: {channels}")
            print(f"  采样宽度: {sample_width * 8} bit")
            print(f"  采样率: {frame_rate} Hz")
            print(f"  时长: {duration:.2f} 秒")
            print(f"  帧数: {n_frames}")
    except Exception as e:
        print(f"读取失败: {e}")

def main():
    print("=" * 40)
    print("🎙️  音频录制")
    print("=" * 40)
    print(f"输出目录: {OUTPUT_DIR}/")
    print()

    print("选择模式:")
    print("1. 录制音频")
    print("2. 播放录音")
    print("3. 查看音频信息")

    choice = input("\n请选择 (1-3): ").strip()

    if choice == '1':
        duration = input("录制时长（秒，默认5）: ").strip()
        duration = int(duration) if duration.isdigit() else 5
        filename = record_audio(duration)
        play_back = input("\n是否立即播放? (y/n): ").strip().lower()
        if play_back == 'y':
            play_audio(filename)
    elif choice == '2':
        files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.wav')] if os.path.exists(OUTPUT_DIR) else []
        if files:
            print("\n可用录音:")
            for i, f in enumerate(files, 1):
                print(f"  {i}. {f}")
            idx = input("选择文件编号: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(files):
                play_audio(os.path.join(OUTPUT_DIR, files[int(idx)-1]))
        else:
            print("没有录音文件")
    elif choice == '3':
        path = input("音频文件路径: ").strip()
        get_audio_info(path)

if __name__ == "__main__":
    main()