#!/usr/bin/env python3
"""
蜂鸣器演奏音乐
使用无源蜂鸣器通过 PWM 演奏音乐

硬件连接:
  GPIO18 ──[蜂鸣器+]──[蜂鸣器-]── GND
  (使用无源蜂鸣器，有源蜂鸣器只能发出固定音调)

学习要点:
  - 音频频率与音符对应关系
  - PWM 产生不同频率
  - 音乐节拍控制
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("模拟模式（无 GPIO）")

BUZZER_PIN = 18

# 音符频率表 (Hz)
NOTES = {
    'C4': 261, 'D4': 294, 'E4': 330, 'F4': 349,
    'G4': 392, 'A4': 440, 'B4': 494,
    'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698,
    'G5': 784, 'A5': 880, 'B5': 988,
    'C6': 1047, 'REST': 0
}

# 音符简写
NOTE_MAP = {
    '1': 'C4', '2': 'D4', '3': 'E4', '4': 'F4',
    '5': 'G4', '6': 'A4', '7': 'B4',
    '1h': 'C5', '2h': 'D5', '3h': 'E5',
    '0': 'REST'
}

def setup():
    if GPIO_AVAILABLE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)

def play_tone(frequency, duration, volume=50):
    """播放指定频率的音调"""
    if frequency == 0:
        time.sleep(duration)
        return

    if GPIO_AVAILABLE:
        pwm = GPIO.PWM(BUZZER_PIN, frequency)
        pwm.start(volume)
        time.sleep(duration)
        pwm.stop()
    else:
        note_name = next((k for k, v in NOTES.items() if v == frequency), str(frequency))
        print(f"  ♪ {note_name} ({frequency}Hz, {duration:.2f}s)")
        time.sleep(duration * 0.3)  # 模拟模式加速

def play_song(melody, bpm=120):
    """
    演奏歌曲
    melody: [(音符, 拍数), ...]
    bpm: 每分钟拍数
    """
    beat_duration = 60 / bpm  # 一拍的时长（秒）

    for note, beats in melody:
        freq = NOTES.get(note, 0)
        duration = beat_duration * beats
        play_tone(freq, duration * 0.9)  # 留10%间隔
        time.sleep(duration * 0.1)

# 预设歌曲
SONGS = {
    '小星星': [
        ('C4', 1), ('C4', 1), ('G4', 1), ('G4', 1),
        ('A4', 1), ('A4', 1), ('G4', 2),
        ('F4', 1), ('F4', 1), ('E4', 1), ('E4', 1),
        ('D4', 1), ('D4', 1), ('C4', 2),
        ('G4', 1), ('G4', 1), ('F4', 1), ('F4', 1),
        ('E4', 1), ('E4', 1), ('D4', 2),
        ('G4', 1), ('G4', 1), ('F4', 1), ('F4', 1),
        ('E4', 1), ('E4', 1), ('D4', 2),
        ('C4', 1), ('C4', 1), ('G4', 1), ('G4', 1),
        ('A4', 1), ('A4', 1), ('G4', 2),
        ('F4', 1), ('F4', 1), ('E4', 1), ('E4', 1),
        ('D4', 1), ('D4', 1), ('C4', 2),
    ],
    '生日快乐': [
        ('C4', 0.75), ('C4', 0.25), ('D4', 1), ('C4', 1), ('F4', 1), ('E4', 2),
        ('C4', 0.75), ('C4', 0.25), ('D4', 1), ('C4', 1), ('G4', 1), ('F4', 2),
        ('C4', 0.75), ('C4', 0.25), ('C5', 1), ('A4', 1), ('F4', 1), ('E4', 1), ('D4', 2),
        ('B4', 0.75), ('B4', 0.25), ('A4', 1), ('F4', 1), ('G4', 1), ('F4', 2),
    ],
    '两只老虎': [
        ('C4', 1), ('D4', 1), ('E4', 1), ('C4', 1),
        ('C4', 1), ('D4', 1), ('E4', 1), ('C4', 1),
        ('E4', 1), ('F4', 1), ('G4', 2),
        ('E4', 1), ('F4', 1), ('G4', 2),
        ('G4', 0.5), ('A4', 0.5), ('G4', 0.5), ('F4', 0.5), ('E4', 1), ('C4', 1),
        ('G4', 0.5), ('A4', 0.5), ('G4', 0.5), ('F4', 0.5), ('E4', 1), ('C4', 1),
        ('D4', 1), ('G3', 1), ('C4', 2),
        ('D4', 1), ('G3', 1), ('C4', 2),
    ],
    '哆来咪': [
        ('C4', 1), ('D4', 1), ('E4', 1), ('C4', 1),
        ('E4', 1), ('C4', 1), ('E4', 2),
        ('D4', 1), ('E4', 1), ('F4', 0.5), ('F4', 0.5),
        ('E4', 1), ('D4', 1), ('F4', 2),
    ],
}

def play_scale():
    """演奏音阶"""
    print("演奏 C 大调音阶...")
    scale = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
    for note in scale:
        print(f"  {note}: {NOTES[note]} Hz")
        play_tone(NOTES[note], 0.4)
        time.sleep(0.1)

def main():
    print("=" * 40)
    print("🎵 蜂鸣器音乐演奏")
    print("=" * 40)
    print(f"蜂鸣器引脚: GPIO{BUZZER_PIN}")
    print()

    setup()

    print("选择歌曲:")
    song_list = list(SONGS.keys())
    for i, name in enumerate(song_list, 1):
        print(f"  {i}. {name}")
    print(f"  {len(song_list)+1}. 音阶测试")

    choice = input("\n请选择: ").strip()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(song_list):
            name = song_list[idx]
            print(f"\n演奏: {name}")
            play_song(SONGS[name], bpm=120)
            print("演奏完成!")
        elif idx == len(song_list):
            play_scale()
        else:
            print("无效选项")
    except (ValueError, KeyboardInterrupt):
        print("\n已停止")
    finally:
        if GPIO_AVAILABLE:
            GPIO.cleanup()

if __name__ == "__main__":
    main()