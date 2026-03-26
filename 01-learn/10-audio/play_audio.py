#!/usr/bin/env python3
"""
播放音频文件
支持 MP3、WAV 等格式

安装依赖:
  sudo apt install mpg123 sox
  pip3 install pygame

学习要点:
  - 音频文件播放
  - 音量控制
  - 播放列表管理
"""

import os
import sys
import time
import glob

# 尝试导入音频库
AUDIO_ENGINE = None

try:
    import pygame
    pygame.mixer.init()
    AUDIO_ENGINE = 'pygame'
except ImportError:
    pass

def play_with_pygame(filename, volume=0.8):
    """使用 pygame 播放"""
    pygame.mixer.music.load(filename)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play()
    print(f"播放: {os.path.basename(filename)}")

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

def play_with_system(filename):
    """使用系统命令播放"""
    ext = os.path.splitext(filename)[1].lower()

    if ext == '.mp3':
        if os.system('which mpg123 > /dev/null 2>&1') == 0:
            os.system(f'mpg123 -q "{filename}"')
        else:
            print("安装 mpg123: sudo apt install mpg123")
    elif ext == '.wav':
        if os.system('which aplay > /dev/null 2>&1') == 0:
            os.system(f'aplay -q "{filename}"')
        elif os.system('which sox > /dev/null 2>&1') == 0:
            os.system(f'play -q "{filename}"')
    else:
        print(f"不支持的格式: {ext}")

def play_file(filename, volume=0.8):
    """播放音频文件"""
    if not os.path.exists(filename):
        print(f"文件不存在: {filename}")
        return

    print(f"播放: {filename}")
    if AUDIO_ENGINE == 'pygame':
        play_with_pygame(filename, volume)
    else:
        play_with_system(filename)

def play_playlist(directory='.', pattern='*.mp3'):
    """播放目录中的所有音频"""
    files = sorted(glob.glob(os.path.join(directory, pattern)))
    if not files:
        files = sorted(glob.glob(os.path.join(directory, '*.wav')))

    if not files:
        print(f"在 {directory} 中未找到音频文件")
        return

    print(f"播放列表 ({len(files)} 首):")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {os.path.basename(f)}")

    print("\n开始播放 (Ctrl+C 跳过/停止)")
    for i, f in enumerate(files, 1):
        try:
            print(f"\n[{i}/{len(files)}] ", end='')
            play_file(f)
        except KeyboardInterrupt:
            print("\n跳过...")
            if AUDIO_ENGINE == 'pygame':
                pygame.mixer.music.stop()
            continue

def generate_test_wav(filename='test_tone.wav', freq=440, duration=2):
    """生成测试音频（440Hz 正弦波）"""
    import wave
    import struct
    import math

    sample_rate = 44100
    num_samples = sample_rate * duration

    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        for i in range(num_samples):
            value = int(32767 * math.sin(2 * math.pi * freq * i / sample_rate))
            wf.writeframes(struct.pack('<h', value))

    print(f"已生成测试音频: {filename} ({freq}Hz, {duration}秒)")
    return filename

def main():
    print("=" * 40)
    print("🎵 音频播放器")
    print("=" * 40)
    print(f"音频引擎: {AUDIO_ENGINE or '系统命令'}")
    print()

    print("选择模式:")
    print("1. 播放指定文件")
    print("2. 播放目录中所有音频")
    print("3. 生成并播放测试音频")

    choice = input("\n请选择 (1-3): ").strip()

    if choice == '1':
        path = input("音频文件路径: ").strip()
        play_file(path)
    elif choice == '2':
        directory = input("目录路径 (默认当前目录): ").strip() or '.'
        play_playlist(directory)
    elif choice == '3':
        filename = generate_test_wav()
        play_file(filename)
    else:
        filename = generate_test_wav()
        play_file(filename)

if __name__ == "__main__":
    main()